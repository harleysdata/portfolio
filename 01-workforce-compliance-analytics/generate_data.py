"""Generate a synthetic contingent workforce dataset.

The data imitates what a bank's contingent workforce program tracks: vendors
(staffing agencies), the contractors they supply, and the compliance checks each
contractor must pass. It deliberately includes the messy records real exports
contain (inconsistent casing, blank fields, duplicate rows, bad dates) so the
cleaning pipeline has real work to do.

All names and records are fictional.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_WORKERS = 5_000
DATA_DIR = Path(__file__).parent / "data"

rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- vendors
vendor_names = [
    "Northbridge Staffing", "Maple Talent Group", "Lakeshore IT Partners",
    "Summit Contract Solutions", "Bayview Consulting", "Harbourfront Resourcing",
    "Ridgeline Tech Staffing", "Clearwater Workforce", "Granite Professional Services",
    "Evergreen Talent", "Pinecrest Contractors", "Riverside Digital",
    "Highland Staffing Co", "Union Station Talent", "Trillium Resourcing",
    "Kingsway Consulting", "Oakridge Partners", "Crescent IT Group",
    "Westend Staffing", "Lighthouse Talent", "Ironwood Solutions",
    "Bluewater Consulting", "Cedar Point Staffing", "Meridian Resourcing",
    "Silverline Talent", "Northstar Contract Group", "Elmwood Partners",
    "Queensway Staffing", "Parkdale Digital", "Harbour Talent Solutions",
    "Danforth Consulting", "Junction IT Staffing",
]
vendors = pd.DataFrame({
    "vendor_id": [f"V{100 + i}" for i in range(len(vendor_names))],
    "vendor_name": vendor_names,
    "risk_tier": rng.choice(["Low", "Medium", "High"], len(vendor_names), p=[0.5, 0.35, 0.15]),
    "contract_end_date": pd.to_datetime("2026-01-01")
    + pd.to_timedelta(rng.integers(-60, 540, len(vendor_names)), unit="D"),
})

# ---------------------------------------------------------------- workers
business_units = ["Global Banking", "Retail Banking", "Technology", "Risk", "Wealth", "Operations"]
roles = ["Developer", "Business Analyst", "Project Manager", "QA Tester", "Data Analyst",
         "Call Centre Agent", "Admin Support", "Security Analyst"]

# Some vendors are worse at paperwork than others: give each a "sloppiness" score.
sloppiness = dict(zip(vendors.vendor_id, rng.beta(2, 8, len(vendors))))
vendor_weights = rng.dirichlet(np.ones(len(vendors)) * 2)

start = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 700, N_WORKERS), unit="D")
tenure_days = rng.integers(60, 900, N_WORKERS)
workers = pd.DataFrame({
    "worker_id": [f"CW{10000 + i}" for i in range(N_WORKERS)],
    "vendor_id": rng.choice(vendors.vendor_id, N_WORKERS, p=vendor_weights),
    "business_unit": rng.choice(business_units, N_WORKERS),
    "role": rng.choice(roles, N_WORKERS),
    "start_date": start,
    "end_date": start + pd.to_timedelta(tenure_days, unit="D"),
    "bill_rate_cad": rng.normal(85, 22, N_WORKERS).clip(30, 180).round(2),
})

s = workers.vendor_id.map(sloppiness).to_numpy()
workers["background_check_status"] = np.where(rng.random(N_WORKERS) < s * 0.5, "Pending", "Cleared")
workers["nda_signed"] = np.where(rng.random(N_WORKERS) < s * 0.4, "N", "Y")
workers["training_completed"] = np.where(rng.random(N_WORKERS) < s * 0.7, "N", "Y")
# Policy: a contractor may not stay more than 24 months without a review.
workers["tenure_review_done"] = np.where(
    (tenure_days > 730) & (rng.random(N_WORKERS) < 0.6), "N", "Y"
)

# ---------------------------------------------------------------- make it messy
messy = workers.copy()
idx = rng.choice(N_WORKERS, 300, replace=False)
messy.loc[idx[:100], "business_unit"] = messy.loc[idx[:100], "business_unit"].str.upper()
messy.loc[idx[100:150], "business_unit"] = " " + messy.loc[idx[100:150], "business_unit"] + " "
messy.loc[idx[150:200], "nda_signed"] = messy.loc[idx[150:200], "nda_signed"].map({"Y": "yes", "N": "no"})
messy.loc[idx[200:240], "bill_rate_cad"] = np.nan
messy["start_date"] = messy.start_date.dt.strftime("%Y-%m-%d")
messy["end_date"] = messy.end_date.dt.strftime("%Y-%m-%d")
messy.loc[idx[240:260], "start_date"] = "not provided"
messy = pd.concat([messy, messy.sample(120, random_state=SEED)], ignore_index=True)  # duplicates
messy = messy.sample(frac=1, random_state=SEED).reset_index(drop=True)

DATA_DIR.mkdir(exist_ok=True)
vendors.to_csv(DATA_DIR / "vendors.csv", index=False)
messy.to_csv(DATA_DIR / "contingent_workers_raw.csv", index=False)
print(f"Wrote {len(vendors)} vendors and {len(messy):,} raw worker rows to {DATA_DIR}")
