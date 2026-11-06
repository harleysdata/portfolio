"""Export the aggregated data behind the live web dashboard.

    python src/export_dashboard.py <out_dir>

251,734 PO lines are too many to ship to a browser, so lines are pre-aggregated into a
cube (month x spend area x flow x company) with every measure the dashboard needs.
Filtering the cube in the browser gives the same totals as filtering the lines.
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CTLS = ["ctl_after_the_fact_po", "ctl_paid_without_gr", "ctl_sod_conflict",
        "ctl_price_change_after_invoice", "ctl_invoice_before_gr", "ctl_payment_block"]
BINS = list(range(0, 190, 10))  # days invoice -> paid, 10-day bins, last bin = 180+


def main(out: Path):
    con = sqlite3.connect(ROOT / "data" / "p2p.db")
    df = pd.read_sql("SELECT po_month, spend_area, flow, company, vendor, po_value_eur, cleared_at, "
                     "days_invoice_to_paid, days_blocked, " + ", ".join(CTLS) + " FROM fct_po_line", con)
    df["spend_area"] = df.spend_area.fillna("Unclassified")
    counts = df.spend_area.value_counts()
    areas = counts[counts >= 400].index.tolist()          # every area big enough to read a rate from
    df["area"] = df.spend_area.where(df.spend_area.isin(areas), "Smaller areas (< 400 lines)")
    months = [f"2018-{m:02d}" for m in range(1, 13)]
    df["m"] = df.po_month.where(df.po_month.isin(months), "Other")
    paid = df.days_invoice_to_paid.between(0, 400)
    df["bin"] = np.where(paid, np.minimum(df.days_invoice_to_paid.fillna(0) // 10, 18), -1).astype(int)

    for c in CTLS:
        df[c + "_v"] = df.po_value_eur * df[c]
    g = df.groupby(["m", "area", "flow", "company"])
    cube = g.agg(lines=("flow", "size"), value=("po_value_eur", "sum"),
                 paid=("cleared_at", "count"), **{c: (c, "sum") for c in CTLS},
                 **{c + "_v": (c + "_v", "sum") for c in CTLS}).reset_index()
    hist = df[df.bin >= 0].groupby(["m", "area", "flow", "company", "bin"]).size().unstack(fill_value=0)
    hist = hist.reindex(columns=range(19), fill_value=0)
    cube = cube.join(hist, on=["m", "area", "flow", "company"]).fillna(0)

    dims = {k: sorted(cube[k].unique().tolist()) for k in ["m", "area", "flow", "company"]}
    rows = [[dims[k].index(r[k]) for k in dims] + [int(r.lines), round(r.value), int(r.paid)]
            + [int(r[c]) for c in CTLS] + [round(r[c + "_v"]) for c in CTLS] + [int(r[b]) for b in range(19)] for _, r in cube.iterrows()]

    vendors = pd.read_sql("SELECT * FROM mart_vendor_risk", con)
    variants = pd.read_csv(ROOT / "reports" / "top_variants.csv").head(8)
    d = {"dims": dims, "controls": CTLS, "bins": BINS, "rows": rows, "row_layout": "m,area,flow,company,lines,value,paid,ctl x6,ctl_value x6,hist x19",
         "vendors": vendors.to_dict(orient="split")["data"], "vendor_cols": vendors.columns.tolist(),
         "variants": variants[["variant", "po_lines", "share"]].values.tolist()}
    out.mkdir(parents=True, exist_ok=True)
    (out / "p2p.json").write_text(json.dumps(d, separators=(",", ":"), default=float))
    print(len(rows), "cube cells;", round((out / "p2p.json").stat().st_size / 1e6, 2), "MB")
    # sanity: cube totals equal line totals
    assert cube.lines.sum() == len(df) and all(cube[c].sum() == df[c].sum() for c in CTLS)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
