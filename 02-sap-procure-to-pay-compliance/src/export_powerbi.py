"""Write the CSVs that the Power BI report loads (powerbi/data/).

    python src/export_powerbi.py

FactPOLine has 251,734 rows, so it ships zipped (unzip before loading).
"""
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi" / "data"
COLS = ["case_id", "po_number", "vendor", "company", "flow", "item_type", "spend_area", "sub_spend_area",
        "po_at", "gr_at", "ir_at", "vendor_inv_at", "cleared_at", "po_value_eur",
        "ctl_after_the_fact_po", "ctl_paid_without_gr", "ctl_sod_conflict", "ctl_price_change_after_invoice",
        "ctl_invoice_before_gr", "ctl_payment_block", "rework_events", "days_invoice_to_paid", "days_blocked"]


def main():
    con = sqlite3.connect(ROOT / "data" / "p2p.db")
    OUT.mkdir(parents=True, exist_ok=True)
    lines = pd.read_sql("SELECT " + ", ".join(COLS) + " FROM fct_po_line", con)
    lines["spend_area"] = lines.spend_area.fillna("Unclassified")
    csv = lines.to_csv(index=False)
    with zipfile.ZipFile(OUT / "FactPOLine.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("FactPOLine.csv", csv)
    pd.read_sql("SELECT * FROM mart_vendor_risk", con).to_csv(OUT / "DimVendorRisk.csv", index=False)
    pd.read_csv(ROOT / "reports" / "top_variants.csv").to_csv(OUT / "ProcessVariants.csv", index=False)
    for f in sorted(OUT.glob("*")):
        print(f.name, round(f.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
