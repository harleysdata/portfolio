"""Generate synthetic data for a used-car dealership:

1. inventory.csv  - every vehicle acquired over 18 months, with how it was
   acquired, how it was priced, and how many days it took to sell
2. ab_test.csv    - website sessions split between the current lead form (A)
   and a shorter lead form with the call-to-action moved up the page (B)

All records are fictional.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
rng = np.random.default_rng(SEED)
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

# ----------------------------------------------------------------- inventory
N = 1_400
makes = {"Toyota": 0.22, "Honda": 0.18, "Ford": 0.15, "Hyundai": 0.12, "Nissan": 0.1,
         "Chevrolet": 0.09, "BMW": 0.06, "Mercedes-Benz": 0.05, "Kia": 0.03}
body = ["SUV", "Sedan", "Truck", "Hatchback", "Minivan"]

acquired = pd.to_datetime("2025-01-01") + pd.to_timedelta(rng.integers(0, 540, N), unit="D")
inv = pd.DataFrame({
    "stock_id": [f"JA{20000 + i}" for i in range(N)],
    "acquired_date": acquired,
    "make": rng.choice(list(makes), N, p=list(makes.values())),
    "body_type": rng.choice(body, N, p=[0.38, 0.27, 0.15, 0.12, 0.08]),
    "model_year": rng.integers(2013, 2025, N),
    "mileage_km": rng.normal(95_000, 40_000, N).clip(8_000, 260_000).round(-2),
    "source": rng.choice(["Trade-in", "Auction", "Private purchase"], N, p=[0.45, 0.4, 0.15]),
})
# The digital appraisal tool went live on 2025-09-01; trade-ins after that date
# were priced with market data instead of a manual estimate.
inv["appraisal_method"] = np.where(
    (inv.source == "Trade-in") & (inv.acquired_date >= "2025-09-01"), "Digital tool", "Manual"
)
# Price vs. market: manual appraisals overpay more often, so cars are listed above market.
base_gap = rng.normal(2.0, 4.0, N)
inv["price_vs_market_pct"] = np.where(inv.appraisal_method == "Digital tool",
                                      base_gap - 2.5, base_gap).round(1)

age = 2026 - inv.model_year
days = (
    28
    + 2.2 * inv.price_vs_market_pct.clip(lower=0)  # overpriced cars sit longer
    + 0.6 * age
    + 0.00008 * inv.mileage_km
    + np.where(inv.body_type.isin(["SUV", "Truck"]), -6, 0)
    + np.where(inv.make.isin(["BMW", "Mercedes-Benz"]), 9, 0)
    + np.where(inv.source == "Auction", 4, 0)
    + rng.gamma(2, 6, N)
)
inv["days_to_turn"] = days.round().astype(int)
inv.to_csv(DATA / "inventory.csv", index=False)

# ----------------------------------------------------------------- A/B test
SESSIONS = 9_000
variant = rng.choice(["A", "B"], SESSIONS)
device = rng.choice(["Mobile", "Desktop"], SESSIONS, p=[0.68, 0.32])
base_rate = np.where(device == "Mobile", 0.031, 0.047)
lift = np.where((variant == "B") & (device == "Mobile"), 1.24,
                np.where(variant == "B", 1.04, 1.0))
ab = pd.DataFrame({
    "session_id": np.arange(SESSIONS),
    "variant": variant,
    "device": device,
    "submitted_lead": (rng.random(SESSIONS) < base_rate * lift).astype(int),
})
ab.to_csv(DATA / "ab_test.csv", index=False)
print(f"Wrote {len(inv):,} vehicles and {len(ab):,} A/B sessions to {DATA}")
