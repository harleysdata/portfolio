"""Write the star-schema CSVs that the Power BI report loads (powerbi/data/).

    python src/export_powerbi.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi" / "data"


def main():
    con = sqlite3.connect(ROOT / "data" / "service_desk.db")
    OUT.mkdir(parents=True, exist_ok=True)
    inc = pd.read_sql("SELECT number, opened_at, resolved_at, priority, category, subcategory, first_group, "
                      "resolving_group, reassignment_count, reassign_band, reopen_count, priority_confirmed, "
                      "knowledge_used, made_sla, hours_to_resolve FROM fct_incident", con)
    inc.to_csv(OUT / "FactIncident.csv", index=False)
    st = pd.read_sql("SELECT number, incident_state, ROUND(SUM(hours_in_state), 2) AS hours "
                     "FROM fct_state_interval GROUP BY number, incident_state", con)
    st.to_csv(OUT / "FactStateHours.csv", index=False)
    pd.read_sql("SELECT number, step, sys_updated_at AS handoff_at, from_group, to_group, is_bounce_back "
                "FROM fct_group_handoff", con).to_csv(OUT / "FactGroupHandoff.csv", index=False)
    groups = pd.unique(pd.concat([inc.first_group, inc.resolving_group]).dropna())
    pd.DataFrame({"group": sorted(groups, key=lambda g: int(g.split()[-1]))}).to_csv(OUT / "DimGroup.csv", index=False)
    for f in sorted(OUT.glob("*.csv")):
        print(f.name, round(f.stat().st_size / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
