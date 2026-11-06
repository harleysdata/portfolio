"""Build the analysis tables and load them into a SQLite warehouse.

Grain of each table:
  fct_incident        one row per incident (its final audit record + derived fields)
  fct_state_interval  one row per audit event: how long the incident stayed in that state
  fct_group_handoff   one row per change of assignment group
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"


def build_incident(events: pd.DataFrame) -> pd.DataFrame:
    last = events.groupby("number").tail(1).set_index("number")
    first_group = events.dropna(subset=["assignment_group"]).groupby("number").assignment_group.first()
    n_groups = events.dropna(subset=["assignment_group"]).groupby("number").assignment_group.nunique()

    inc = pd.DataFrame({
        "opened_at": last.opened_at,
        "resolved_at": last.resolved_at,
        "closed_at": last.closed_at,
        "priority": last.priority, "priority_code": last.priority_code,
        "impact": last.impact, "urgency": last.urgency,
        "contact_type": last.contact_type,
        "category": last.category, "subcategory": last.subcategory,
        "location": last.location,
        "first_group": first_group,
        "resolving_group": last.assignment_group,
        "distinct_groups": n_groups,
        "reassignment_count": last.reassignment_count,
        "reopen_count": last.reopen_count,
        "knowledge_used": last.knowledge.astype(int),
        "priority_confirmed": last.u_priority_confirmation.astype(int),
        # made_sla flips from True to False when the SLA clock runs out, so the final record is the truth.
        "made_sla": last.made_sla.astype(int),
    })
    inc["hours_to_resolve"] = (inc.resolved_at - inc.opened_at).dt.total_seconds() / 3600
    inc["reassign_band"] = pd.cut(inc.reassignment_count, [-1, 0, 1, 2, 4, 1000],
                                  labels=["0", "1", "2", "3-4", "5+"]).astype(str)
    return inc.reset_index()


def build_state_intervals(events: pd.DataFrame) -> pd.DataFrame:
    e = events[["number", "sys_mod_count", "incident_state", "assignment_group", "sys_updated_at"]].copy()
    e["next_update"] = e.groupby("number").sys_updated_at.shift(-1)
    e["hours_in_state"] = (e.next_update - e.sys_updated_at).dt.total_seconds() / 3600
    # The final event has no successor; a handful of out-of-order timestamps give negatives.
    return e[e.hours_in_state >= 0].drop(columns="next_update")


def build_handoffs(events: pd.DataFrame) -> pd.DataFrame:
    g = events.dropna(subset=["assignment_group"])[["number", "sys_updated_at", "assignment_group"]]
    g = g[g.assignment_group != g.groupby("number").assignment_group.shift(1)].copy()
    g["from_group"] = g.groupby("number").assignment_group.shift(1)
    g["step"] = g.groupby("number").cumcount()
    g["is_bounce_back"] = (g.assignment_group == g.groupby("number").assignment_group.shift(2)).astype(int)
    return g.dropna(subset=["from_group"]).rename(columns={"assignment_group": "to_group"})


def load_warehouse(path: Path, tables: dict[str, pd.DataFrame]) -> sqlite3.Connection:
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    for name, df in tables.items():
        out = df.copy()
        for c in out.select_dtypes("datetime").columns:
            out[c] = out[c].dt.strftime("%Y-%m-%d %H:%M")
        out.to_sql(name, con, index=False)
    con.executescript((SQL_DIR / "marts.sql").read_text())
    return con
