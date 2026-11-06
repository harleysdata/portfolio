"""Clean the purchase-to-pay event log and build one row per purchase-order line with control flags.

A "case" in this log is one purchase-order line item (PO number + item number).
"""
import pandas as pd

WINDOW = ("2018-01-01", "2019-02-01")   # the log covers POs created in 2018; payments run into Jan 2019
MILESTONES = {
    "Create Purchase Requisition Item": "req_at",
    "Create Purchase Order Item": "po_at",
    "Record Goods Receipt": "gr_at",
    "Vendor creates invoice": "vendor_inv_at",
    "Record Invoice Receipt": "ir_at",
    "Remove Payment Block": "block_removed_at",
    "Change Price": "price_change_at",
    "Clear Invoice": "cleared_at",
}
REWORK = ["Change Quantity", "Change Price", "Cancel Invoice Receipt", "Cancel Goods Receipt",
          "Delete Purchase Order Item", "Change Approval for Purchase Order", "Change Delivery Indicator"]


def load(interim) -> tuple[pd.DataFrame, pd.DataFrame]:
    ev = pd.read_csv(interim / "events.csv", dtype={"case_id": str})
    ev.columns = ["case_id", "activity", "ts", "resource", "user", "cum_value_eur"]
    ev["ts"] = pd.to_datetime(ev.ts, utc=True).dt.tz_localize(None)
    cases = pd.read_csv(interim / "cases.csv", dtype=str).rename(columns={
        "concept:name": "case_id", "Purchasing Document": "po_number", "Item": "item",
        "Item Type": "item_type", "Item Category": "flow", "Document Type": "doc_type",
        "GR-Based Inv. Verif.": "gr_based_iv", "Goods Receipt": "gr_required",
        "Company": "company", "Vendor": "vendor", "Spend area text": "spend_area",
        "Sub spend area text": "sub_spend_area", "Spend classification text": "spend_class"})
    return ev, cases


def clean(ev: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    log = [{"rule": "raw events", "rows_affected": len(ev), "detail": f"{ev.case_id.nunique():,} PO lines"}]
    out = ~ev.ts.between(*WINDOW)
    log.append({"rule": "timestamp outside 2018-01 to 2019-01", "rows_affected": int(out.sum()),
                "detail": f"earliest {ev.ts.min():%Y-%m-%d}, latest {ev.ts.max():%Y-%m-%d}; "
                          "excluded from timing metrics, kept for counts"})
    ev = ev.assign(ts_valid=~out, is_batch=ev.user.str.startswith("batch"))
    dup = ev.duplicated(["case_id", "activity", "ts", "user"])
    log.append({"rule": "same step, same minute, same user", "rows_affected": int(dup.sum()),
                "detail": "kept: timestamps are to the minute, so these are usually split deliveries "
                          "or invoices posted together, not duplicates"})
    ev = ev.sort_values(["case_id", "ts"], kind="stable").reset_index(drop=True)
    return ev, log


def build_po_lines(ev: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    valid = ev[ev.ts_valid]
    first = (valid[valid.activity.isin(MILESTONES)]
             .groupby(["case_id", "activity"]).ts.min().unstack().rename(columns=MILESTONES))
    value = ev[ev.activity == "Create Purchase Order Item"].groupby("case_id").cum_value_eur.first()
    counts = ev.pivot_table(index="case_id", columns="activity", values="ts", aggfunc="size", fill_value=0)

    df = cases.set_index("case_id").join(first).join(value.rename("po_value_eur"))
    df["n_events"] = counts.sum(axis=1)
    df["n_goods_receipts"] = counts.get("Record Goods Receipt", 0)
    df["n_invoices"] = counts.get("Record Invoice Receipt", 0)
    df["rework_events"] = counts.reindex(columns=REWORK, fill_value=0).sum(axis=1)

    # Segregation of duties: the same named person raised the PO and confirmed the goods arrived.
    human = ev[~ev.is_batch]
    po_users = human[human.activity == "Create Purchase Order Item"].groupby("case_id").user.agg(set)
    gr_users = human[human.activity == "Record Goods Receipt"].groupby("case_id").user.agg(set)
    both = po_users.to_frame("po").join(gr_users.rename("gr"), how="inner")
    df["sod_po_and_gr_same_user"] = 0
    df.loc[both.index[[bool(a & b) for a, b in zip(both.po, both.gr)]], "sod_po_and_gr_same_user"] = 1

    three_way = df.flow.str.startswith("3-way")
    df["ctl_after_the_fact_po"] = (df.vendor_inv_at < df.po_at).astype(int)
    df["ctl_invoice_before_gr"] = (three_way & (df.ir_at < df.gr_at)).astype(int)
    df["ctl_paid_without_gr"] = (three_way & df.cleared_at.notna() &
                                 (df.gr_at.isna() | (df.cleared_at < df.gr_at))).astype(int)
    df["ctl_price_change_after_invoice"] = (df.price_change_at > df.ir_at).astype(int)
    df["ctl_payment_block"] = df.block_removed_at.notna().astype(int)
    df["ctl_sod_conflict"] = df.sod_po_and_gr_same_user

    df["days_po_to_paid"] = (df.cleared_at - df.po_at).dt.days
    df["days_invoice_to_paid"] = (df.cleared_at - df.vendor_inv_at).dt.days
    df["days_blocked"] = (df.block_removed_at - df.ir_at).dt.days
    df["po_month"] = df.po_at.dt.to_period("M").astype(str)
    return df.reset_index()


def variants(ev: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Process variants: the ordered list of distinct steps each line went through."""
    collapsed = ev[ev.activity != ev.groupby("case_id").activity.shift()]
    seq = collapsed.groupby("case_id").activity.agg(" → ".join)
    v = seq.value_counts().rename_axis("variant").reset_index(name="po_lines")
    v["share"] = v.po_lines / v.po_lines.sum()
    v["cumulative_share"] = v.share.cumsum()
    v.attrs["n_variants"] = len(v)
    return v
