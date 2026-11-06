"""The reconciliation must find every planted defect and raise nothing else."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import reconcile  # noqa: E402


@pytest.fixture(scope="module")
def result():
    subprocess.run([sys.executable, str(ROOT / "src" / "generate_sample.py")], check=True, capture_output=True)
    fg, ec, sn, cases = reconcile.load()
    exc = reconcile.reconcile(fg, ec, sn, cases, pd.Timestamp("2026-10-31"))
    key = pd.read_csv(ROOT / "data" / "sample" / "answer_key.csv")
    found = set(zip(exc.worker_id.str.replace("(none) cw", "FGW", regex=False), exc.check))
    return found, set(zip(key.worker_id, key.defect))


def test_finds_every_planted_defect(result):
    found, planted = result
    assert planted - found == set()


def test_no_false_alarms(result):
    found, planted = result
    assert found - planted == set()


def test_every_check_has_owner_and_severity():
    for check, (desc, sev, owner) in reconcile.CHECKS.items():
        assert sev in {"Critical", "High", "Medium", "Low"} and owner and desc
