"""Load the raw ServiceNow audit export and produce a clean event table.

Every rule here is recorded in the data-quality log so a reviewer can see
exactly what changed between the raw export and the analysis tables.
"""
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_ZIP = ROOT / "data" / "raw" / "incident_event_log.zip"

TS_COLS = ["opened_at", "sys_created_at", "sys_updated_at", "resolved_at", "closed_at"]
VALID_STATES = {"New", "Active", "Awaiting User Info", "Awaiting Vendor", "Awaiting Problem",
                "Awaiting Evidence", "Resolved", "Closed"}
# Columns that are >98% empty in the export (CMDB item, vendor, problem, change, caused_by)
SPARSE_COLS = ["caused_by", "vendor", "cmdb_ci", "rfc", "problem_id"]


def load_raw() -> pd.DataFrame:
    with zipfile.ZipFile(RAW_ZIP) as z, z.open("incident_event_log.csv") as f:
        # ServiceNow exports write unknown values as "?"
        return pd.read_csv(f, na_values=["?"], low_memory=False)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    log: list[dict] = []

    def note(rule, rows, detail):
        log.append({"rule": rule, "rows_affected": int(rows), "detail": detail})

    df = raw.copy()
    note("raw rows", len(df), f"{df.number.nunique():,} incidents, {df.shape[1]} columns")

    for c in TS_COLS:
        parsed = pd.to_datetime(df[c], format="%d/%m/%Y %H:%M", errors="coerce")
        bad = parsed.isna() & df[c].notna()
        if bad.any():
            note(f"unparseable {c}", bad.sum(), "set to null")
        df[c] = parsed

    bad_state = ~df.incident_state.isin(VALID_STATES)
    note("invalid incident_state", bad_state.sum(), "state '-100' is not a ServiceNow state; rows dropped")
    df = df[~bad_state]

    missing_resolved = df.groupby("number").resolved_at.transform(lambda s: s.isna().all())
    note("incidents with no resolved_at", df.loc[missing_resolved, "number"].nunique(),
         "kept for SLA counts, excluded from resolution-time metrics")

    note("dropped sparse columns", 0, ", ".join(SPARSE_COLS) + " are >98% empty")
    df = df.drop(columns=SPARSE_COLS)

    # Ordinal fields arrive as "2 - Medium"; keep the label and add a sortable number.
    for c in ["priority", "impact", "urgency"]:
        df[f"{c}_code"] = df[c].str.slice(0, 1).astype(int)

    # Order events the way ServiceNow wrote them: modification counter, then update time.
    df = df.sort_values(["number", "sys_mod_count", "sys_updated_at"]).reset_index(drop=True)
    note("clean event rows", len(df), f"{df.number.nunique():,} incidents")
    return df, log
