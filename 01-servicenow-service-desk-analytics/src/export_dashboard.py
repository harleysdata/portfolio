"""Export the compact incident-level dataset behind the live web dashboard.

    python src/export_dashboard.py <out_dir>

One row per incident with only the fields the dashboard filters and aggregates on,
as column arrays (smaller than row objects). ~25k incidents -> ~1 MB of JSON.
"""
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STATES = ["New", "Active", "Awaiting User Info", "Awaiting Vendor", "Awaiting Problem", "Awaiting Evidence"]


def main(out: Path):
    con = sqlite3.connect(ROOT / "data" / "service_desk.db")
    inc = pd.read_sql("SELECT * FROM fct_incident", con, parse_dates=["opened_at"])
    st = pd.read_sql("SELECT number, incident_state, SUM(hours_in_state) h FROM fct_state_interval "
                     "GROUP BY number, incident_state", con).pivot(index="number", columns="incident_state", values="h")
    inc = inc.join(st.reindex(columns=STATES).fillna(0), on="number")

    top_groups = inc.first_group.value_counts().head(12).index.tolist()
    top_cats = inc.category.value_counts().head(10).index.tolist()
    def code(s, keep):  # index into a lookup list; last slot = "Other"
        return [keep.index(v) if v in keep else len(keep) for v in s]

    month0 = pd.Timestamp("2016-02-01")
    d = {
        "lookups": {"group": top_groups + ["Other"], "category": top_cats + ["Other"], "states": STATES,
                    "priority": ["Critical", "High", "Moderate", "Low"], "month0": "2016-02"},
        "month": ((inc.opened_at.dt.year - 2016) * 12 + inc.opened_at.dt.month - 2).clip(0, 12).tolist(),
        "pri": (inc.priority_code - 1).tolist(),
        "reas": inc.reassignment_count.clip(upper=9).tolist(),
        "sla": inc.made_sla.tolist(),
        "ttr": [None if pd.isna(v) else round(v, 1) for v in inc.hours_to_resolve],
        "fg": code(inc.first_group, top_groups),
        # -1 = no resolving group recorded (2,157 incidents); excluded from "resolved by first group"
        "rg": [-1 if pd.isna(g) else c for g, c in zip(inc.resolving_group, code(inc.resolving_group, top_groups))],
        "cat": code(inc.category, top_cats),
        "hrs": [inc[s].round(0).astype(int).tolist() for s in STATES],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "service_desk.json").write_text(json.dumps(d, separators=(",", ":")))
    print(len(inc), round((out / "service_desk.json").stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
