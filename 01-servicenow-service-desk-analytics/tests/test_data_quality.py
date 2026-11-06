"""Data-quality and logic checks. Run after the pipeline: pytest -q"""
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "service_desk.db"


@pytest.fixture(scope="module")
def con():
    if not DB.exists():
        pytest.skip("run src/run_pipeline.py first")
    return sqlite3.connect(DB)


def one(con, sql):
    return con.execute(sql).fetchone()[0]


def test_one_row_per_incident(con):
    assert one(con, "SELECT COUNT(*) - COUNT(DISTINCT number) FROM fct_incident") == 0


def test_all_incidents_kept(con):
    # 24,918 incidents in the source; cleaning drops 5 bad rows, never a whole incident
    assert one(con, "SELECT COUNT(*) FROM fct_incident") == 24918


def test_no_negative_durations(con):
    assert one(con, "SELECT COUNT(*) FROM fct_state_interval WHERE hours_in_state < 0") == 0
    assert one(con, "SELECT COUNT(*) FROM fct_incident WHERE hours_to_resolve < 0") == 0


def test_resolved_after_opened(con):
    assert one(con, "SELECT COUNT(*) FROM fct_incident WHERE resolved_at < opened_at") == 0


def test_made_sla_is_binary(con):
    assert one(con, "SELECT COUNT(*) FROM fct_incident WHERE made_sla NOT IN (0, 1)") == 0


def test_bands_cover_every_incident(con):
    assert one(con, "SELECT SUM(incidents) FROM mart_reassignment_impact") == 24918


def test_handoffs_are_real_changes(con):
    assert one(con, "SELECT COUNT(*) FROM fct_group_handoff WHERE from_group = to_group") == 0


def test_time_in_state_shares_sum_to_100(con):
    total = one(con, "SELECT SUM(pct_of_open_hours) FROM mart_time_in_state")
    assert abs(total - 100) < 0.5


def test_routing_rules_were_not_fit_on_test_data():
    s = json.loads((ROOT / "reports" / "summary.json").read_text())["derived"]["routing"]
    assert s["covered"] <= s["test_incidents"]
    assert s["fixed"] > s["broken"]
