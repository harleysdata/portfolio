"""Checks on the PO-line table and the control logic. Run after the pipeline: pytest -q"""
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "p2p.db"


@pytest.fixture(scope="module")
def lines():
    if not DB.exists():
        pytest.skip("run src/run_pipeline.py first")
    return pd.read_sql("SELECT * FROM fct_po_line", sqlite3.connect(DB),
                       parse_dates=["po_at", "gr_at", "ir_at", "vendor_inv_at", "cleared_at"])


def test_one_row_per_po_line(lines):
    assert lines.case_id.is_unique
    assert len(lines) == 251_734          # published size of the BPI Challenge 2019 log


def test_every_line_has_a_po_event(lines):
    assert lines.po_at.notna().mean() > 0.999


def test_after_the_fact_flag_matches_dates(lines):
    flagged = lines[lines.ctl_after_the_fact_po == 1]
    assert (flagged.vendor_inv_at < flagged.po_at).all()


def test_paid_without_gr_only_in_three_way_flows(lines):
    assert lines.loc[~lines.flow.str.startswith("3-way"), "ctl_paid_without_gr"].sum() == 0


def test_consignment_is_never_invoiced_per_line(lines):
    # Consignment stock is settled periodically, not invoiced line by line
    assert lines.loc[lines.flow == "Consignment", "n_invoices"].sum() == 0


def test_invoice_after_gr_flow_is_enforced(lines):
    # SAP blocks invoice posting before GR when GR-based invoice verification is on
    sub = lines[lines.flow == "3-way match, invoice after GR"]
    assert sub.ctl_invoice_before_gr.sum() == 0


def test_flags_are_binary(lines):
    for c in [c for c in lines.columns if c.startswith("ctl_")]:
        assert set(lines[c].unique()) <= {0, 1}, c


def test_risk_scores_bounded():
    v = pd.read_sql("SELECT * FROM mart_vendor_risk", sqlite3.connect(DB))
    assert v.risk_score.between(0, 100).all()
    assert (v.po_lines >= 100).all()
