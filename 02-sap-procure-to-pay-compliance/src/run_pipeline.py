"""End-to-end run: SAP event log (XES) -> clean events -> PO-line facts -> SQLite marts -> figures.

    python src/run_pipeline.py
"""
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import parse_xes, transform  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "BPI_Challenge_2019.xes.gz"
INTERIM = ROOT / "data" / "interim"
DB = ROOT / "data" / "p2p.db"
OUT, FIG = ROOT / "reports", ROOT / "reports" / "figures"
INK, MUTED, ACCENT = "#1f2328", "#8b949e", "#c4314b"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9)


def figures(con, lines):
    FIG.mkdir(parents=True, exist_ok=True)
    c = pd.read_sql("SELECT * FROM mart_control_exceptions", con)
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    bars = ax.barh(c.control, c.po_lines, color=[ACCENT if v in (
        "After-the-fact PO (invoice dated before PO)", "Same person raised PO and received goods",
        "Paid with no goods receipt first") else MUTED for v in c.control])
    ax.bar_label(bars, labels=[f"{n:,}  (€{m:.0f}M)" for n, m in zip(c.po_lines, c.po_value_eur_m)],
                 fontsize=8.5, padding=3)
    ax.invert_yaxis(); ax.set_xlabel("PO lines"); ax.set_xlim(0, c.po_lines.max() * 1.35)
    style(ax, "Control exceptions across 251,734 PO lines")
    fig.tight_layout(); fig.savefig(FIG / "control_exceptions.png", dpi=160); plt.close(fig)

    v = pd.read_sql("SELECT * FROM mart_vendor_risk", con)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    colors = v.risk_tier.map({"High": ACCENT, "Medium": "#d29922", "Low": MUTED})
    ax.scatter(v.spend_eur_m, v.risk_score, s=12 + v.po_lines / 60, c=colors, alpha=0.75, edgecolors="none")
    ax.set_xscale("log"); ax.set_xlabel("Spend, € millions (log scale)"); ax.set_ylabel("Risk score (0–100)")
    style(ax, f"Vendor risk vs. spend ({len(v)} vendors with 100+ PO lines)")
    fig.tight_layout(); fig.savefig(FIG / "vendor_risk.png", dpi=160); plt.close(fig)

    paid = lines.dropna(subset=["days_invoice_to_paid"])
    paid = paid[paid.days_invoice_to_paid.between(0, 365)]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.hist(paid.days_invoice_to_paid, bins=73, color=MUTED)
    for d in (30, 60, 90):
        ax.axvline(d, color=ACCENT, lw=0.8, ls="--")
    ax.set_xlabel("Days from vendor invoice date to payment"); ax.set_ylabel("PO lines")
    style(ax, "Time to pay: most invoices clear between 30 and 90 days")
    fig.tight_layout(); fig.savefig(FIG / "days_to_pay.png", dpi=160); plt.close(fig)


def main():
    if not (INTERIM / "events.csv").exists():
        print("parsing XES (about 2 minutes)…", parse_xes.parse(RAW, INTERIM))
    ev, cases = transform.load(INTERIM)
    ev, dq = transform.clean(ev)
    lines = transform.build_po_lines(ev, cases)
    var = transform.variants(ev)

    DB.unlink(missing_ok=True)
    con = sqlite3.connect(DB)
    out = lines.copy()
    for c in out.select_dtypes("datetime").columns:
        out[c] = out[c].dt.strftime("%Y-%m-%d %H:%M")
    out.to_sql("fct_po_line", con, index=False)
    con.executescript((ROOT / "sql" / "marts.sql").read_text())

    OUT.mkdir(exist_ok=True)
    pd.DataFrame(dq).to_csv(OUT / "data_quality_log.csv", index=False)
    var.head(15).to_csv(OUT / "top_variants.csv", index=False)
    pd.read_sql("SELECT * FROM mart_vendor_risk", con).to_csv(OUT / "vendor_risk_scorecard.csv", index=False)

    marts = {m: pd.read_sql(f"SELECT * FROM {m}", con).to_dict(orient="records") for m in [
        "mart_control_exceptions", "mart_flow_profile", "mart_monthly_controls", "mart_risk_tier_summary"]}
    paid = lines.dropna(subset=["days_invoice_to_paid"])
    blocked = lines.dropna(subset=["days_blocked"])
    derived = {
        "po_lines": len(lines), "purchase_orders": lines.po_number.nunique(),
        "vendors": lines.vendor.nunique(), "companies": lines.company.nunique(),
        "events": len(ev), "po_value_eur_m": round(lines.po_value_eur.sum() / 1e6, 1),
        "variants": var.attrs["n_variants"],
        "top10_variant_share": round(var.head(10).share.sum(), 4),
        "median_days_po_to_paid": float(lines.days_po_to_paid.median()),
        "median_days_invoice_to_paid": float(paid.days_invoice_to_paid.median()),
        "pct_paid_over_90_days": round((paid.days_invoice_to_paid > 90).mean(), 4),
        "median_days_blocked": float(blocked[blocked.days_blocked >= 0].days_blocked.median()),
        "batch_share_of_events": round(ev.is_batch.mean(), 4),
        "vendors_scored": int(pd.read_sql("SELECT COUNT(*) n FROM mart_vendor_risk", con).n[0]),
    }
    figures(con, lines)
    (OUT / "summary.json").write_text(json.dumps(marts | {"derived": derived}, indent=2, default=str))
    print(json.dumps(marts | {"derived": derived}, indent=1, default=str))


if __name__ == "__main__":
    main()
