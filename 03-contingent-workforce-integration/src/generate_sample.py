"""Generate sample extracts from Fieldglass, Employee Central and ServiceNow, with known defects planted.

There is no public dataset of HR system records (and there shouldn't be), so the
reconciliation is tested on generated extracts. The field names follow each system's
standard objects. Every planted defect is written to an answer key, so the tests can
prove the reconciliation finds all of them and nothing else.

    python src/generate_sample.py
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED, N_WORKERS, AS_OF = 7, 3000, date(2026, 10, 31)
OUT = Path(__file__).resolve().parents[1] / "data" / "sample"

# Share of workers that get each defect. Rates are set to be plausible, not measured.
DEFECTS = {
    "missing_in_ec": 0.015,           # active work order, never created in Employee Central
    "ended_still_active_ec": 0.02,    # work order ended, EC record still active
    "ended_account_active": 0.025,    # work order ended, ServiceNow account still active
    "end_date_mismatch": 0.04,        # extension in Fieldglass not carried to EC
    "cost_center_mismatch": 0.03,
    "orphan_account": 0.01,           # ServiceNow account with no Fieldglass work order at all
    "late_onboarding": 0.08,          # equipment/access task closed after the start date
}
SUPPLIERS = ["Supplier A", "Supplier B", "Supplier C", "Supplier D", "Supplier E", "Supplier F"]
COST_CENTERS = [f"CC{n}" for n in range(4100, 4140)]
ROLES = ["Business Analyst", "Developer", "QA Analyst", "Project Coordinator", "Data Analyst",
         "Change Manager", "Scrum Master", "Infrastructure Analyst"]


def main():
    rng = random.Random(SEED)
    fg, ec, sn_user, sn_case, key = [], [], [], [], []

    for i in range(N_WORKERS):
        worker_id = f"FGW{100000 + i}"
        wo_id = f"WO{500000 + i}"
        start = AS_OF - timedelta(days=rng.randint(10, 900))
        end = start + timedelta(days=rng.choice([90, 180, 182, 270, 365, 365, 548, 730]))
        cc, mgr = rng.choice(COST_CENTERS), f"E{rng.randint(10000, 10400)}"
        email = f"{worker_id.lower()}@contractor.example.com"
        active = end >= AS_OF
        defects = {d for d, p in DEFECTS.items() if rng.random() < p}
        # Some defects only make sense for workers who have / haven't ended
        if active:
            defects -= {"ended_still_active_ec", "ended_account_active"}
        else:
            defects -= {"missing_in_ec"}
        if "missing_in_ec" in defects:
            defects -= {"end_date_mismatch", "cost_center_mismatch"}
        if "orphan_account" in defects:
            defects = {"orphan_account"}

        for d in sorted(defects):
            key.append({"worker_id": worker_id, "defect": d})

        if "orphan_account" not in defects:
            fg.append({"work_order_id": wo_id, "worker_id": worker_id, "supplier": rng.choice(SUPPLIERS),
                       "job_title": rng.choice(ROLES), "start_date": start, "end_date": end,
                       "cost_center": cc, "site": rng.choice(["Toronto", "Toronto", "Halifax", "Remote"]),
                       "hiring_manager_id": mgr, "bill_rate_cad": rng.choice(range(55, 140, 5)),
                       "work_order_status": "Active" if active else "Closed", "email": email})

        if "missing_in_ec" not in defects and "orphan_account" not in defects:
            ec_end = end + timedelta(days=rng.choice([30, 60, 90])) if "end_date_mismatch" in defects else end
            ec_status = "A" if (active or "ended_still_active_ec" in defects) else "T"
            ec.append({"personIdExternal": f"CW{100000 + i}", "userId": f"CW{100000 + i}",
                       "isContingentWorker": True, "startDate": start, "endDate": ec_end,
                       "emplStatus": ec_status,
                       "costCenter": rng.choice([c for c in COST_CENTERS if c != cc])
                       if "cost_center_mismatch" in defects else cc,
                       "managerId": mgr, "customString_fieldglassWorkerId": worker_id, "email": email})

        acct_active = active or "ended_account_active" in defects or "orphan_account" in defects
        sn_user.append({"user_name": f"cw{100000 + i}", "email": email,
                        "employee_number": f"CW{100000 + i}",
                        "u_fieldglass_worker_id": worker_id if "orphan_account" not in defects else "",
                        "active": acct_active, "sys_created_on": start - timedelta(days=rng.randint(1, 7))})

        if "orphan_account" not in defects:
            late = "late_onboarding" in defects
            closed = start + timedelta(days=rng.randint(1, 15)) if late else start - timedelta(days=rng.randint(0, 5))
            sn_case.append({"number": f"HRC{700000 + i}", "subject_person": f"cw{100000 + i}",
                            "hr_service": "Contingent Worker Onboarding", "opened_at": start - timedelta(days=10),
                            "closed_at": closed, "worker_start_date": start})

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(fg).to_csv(OUT / "fieldglass_work_orders.csv", index=False)
    pd.DataFrame(ec).to_csv(OUT / "ec_contingent_workers.csv", index=False)
    pd.DataFrame(sn_user).to_csv(OUT / "servicenow_sys_user.csv", index=False)
    pd.DataFrame(sn_case).to_csv(OUT / "servicenow_onboarding_cases.csv", index=False)
    pd.DataFrame(key).to_csv(OUT / "answer_key.csv", index=False)
    print(f"{len(fg)} work orders, {len(ec)} EC records, {len(sn_user)} accounts, {len(key)} planted defects")


if __name__ == "__main__":
    main()
