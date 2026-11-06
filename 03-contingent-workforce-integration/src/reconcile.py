"""Three-way reconciliation of contingent workers: Fieldglass (source of truth for the
engagement) vs. Employee Central (worker record) vs. ServiceNow (access and onboarding).

    python src/reconcile.py [as_of=2026-10-31]

Writes reports/exceptions.csv (one row per issue, with severity and owner) and
reports/reconciliation_summary.csv.
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data" / "sample", ROOT / "reports"

# check id -> (description, severity, owner). Severity follows the risk: access after
# an engagement ends is a security issue; a cost-centre mismatch is a reporting issue.
CHECKS = {
    "ended_account_active": ("Work order ended but ServiceNow account still active", "Critical", "IAM / Service desk"),
    "orphan_account": ("Active ServiceNow contractor account with no Fieldglass work order", "Critical", "IAM"),
    "ended_still_active_ec": ("Work order ended but Employee Central record still active", "High", "HR Operations"),
    "missing_in_ec": ("Active work order with no Employee Central record", "High", "HR Operations"),
    "end_date_mismatch": ("End date in EC differs from Fieldglass (extension not synced)", "Medium", "HR Operations"),
    "cost_center_mismatch": ("Cost centre in EC differs from Fieldglass", "Medium", "Finance / HR Operations"),
    "late_onboarding": ("Onboarding case closed after the worker's start date", "Low", "HR Service Delivery"),
}


def load():
    d = lambda f, cols: pd.read_csv(DATA / f, parse_dates=cols)  # noqa: E731
    return (d("fieldglass_work_orders.csv", ["start_date", "end_date"]),
            d("ec_contingent_workers.csv", ["startDate", "endDate"]),
            d("servicenow_sys_user.csv", ["sys_created_on"]),
            d("servicenow_onboarding_cases.csv", ["opened_at", "closed_at", "worker_start_date"]))


def reconcile(fg, ec, sn, cases, as_of: pd.Timestamp) -> pd.DataFrame:
    issues = []

    def add(rows, check, detail):
        for wid, det in zip(rows.worker_id, detail):
            issues.append({"worker_id": wid, "check": check, "detail": det})

    fg = fg.assign(active=fg.end_date >= as_of)
    m = fg.merge(ec, how="left", left_on="worker_id", right_on="customString_fieldglassWorkerId")
    m = m.merge(sn[["u_fieldglass_worker_id", "user_name", "active"]].rename(columns={"active": "sn_active"}),
                how="left", left_on="worker_id", right_on="u_fieldglass_worker_id")

    r = m[m.active & m.userId.isna()]
    add(r, "missing_in_ec", [f"work order {w} active since {s:%Y-%m-%d}" for w, s in zip(r.work_order_id, r.start_date)])

    r = m[~m.active & (m.emplStatus == "A")]
    add(r, "ended_still_active_ec", [f"ended {e:%Y-%m-%d}, {(as_of - e).days} days ago" for e in r.end_date])

    r = m[~m.active & (m.sn_active == True)]  # noqa: E712
    add(r, "ended_account_active", [f"{u} active {(as_of - e).days} days after end" for u, e in zip(r.user_name, r.end_date)])

    r = m[m.userId.notna() & (m.endDate != m.end_date)]
    add(r, "end_date_mismatch", [f"FG {a:%Y-%m-%d} vs EC {b:%Y-%m-%d}" for a, b in zip(r.end_date, r.endDate)])

    r = m[m.userId.notna() & (m.costCenter != m.cost_center)]
    add(r, "cost_center_mismatch", [f"FG {a} vs EC {b}" for a, b in zip(r.cost_center, r.costCenter)])

    orphans = sn[sn.active & sn.u_fieldglass_worker_id.isna() & sn.user_name.str.startswith("cw")]
    orphans = orphans.assign(worker_id="(none) " + orphans.user_name)
    add(orphans, "orphan_account", [f"{u} created {c:%Y-%m-%d}" for u, c in zip(orphans.user_name, orphans.sys_created_on)])

    c = cases.merge(sn[["user_name", "u_fieldglass_worker_id"]], left_on="subject_person", right_on="user_name")
    late = c[c.closed_at > c.worker_start_date].rename(columns={"u_fieldglass_worker_id": "worker_id"})
    add(late, "late_onboarding", [f"{(a - b).days} days after start" for a, b in zip(late.closed_at, late.worker_start_date)])

    out = pd.DataFrame(issues)
    meta = pd.DataFrame.from_dict(CHECKS, orient="index", columns=["description", "severity", "owner"])
    return out.join(meta, on="check")


def summarise(exc: pd.DataFrame, fg, cases) -> pd.DataFrame:
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    s = (exc.groupby(["check", "description", "severity", "owner"]).size().rename("workers").reset_index()
         .sort_values("severity", key=lambda x: x.map(order)))
    s["pct_of_work_orders"] = (100 * s.workers / len(fg)).round(2)
    return s


def main():
    as_of = pd.Timestamp(sys.argv[1] if len(sys.argv) > 1 else "2026-10-31")
    fg, ec, sn, cases = load()
    exc = reconcile(fg, ec, sn, cases, as_of)
    OUT.mkdir(exist_ok=True)
    exc.to_csv(OUT / "exceptions.csv", index=False)
    s = summarise(exc, fg, cases)
    s.to_csv(OUT / "reconciliation_summary.csv", index=False)
    on_time = (cases.closed_at <= cases.worker_start_date).mean()
    print(s.to_string(index=False))
    print(f"\nOnboarding ready by start date: {on_time:.1%} of {len(cases):,} cases")


if __name__ == "__main__":
    main()
