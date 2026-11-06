"""RICE scores for the backlog, and the sample size for the intake experiment.

    python src/prioritise.py

RICE = Reach x Impact x Confidence / Effort
  Reach       contractors (or requests) affected per quarter
  Impact      3 = removes a blocker, 2 = large, 1 = medium, 0.5 = small
  Confidence  how sure I am of reach and impact (evidence from Projects 1-3 raises it)
  Effort      story points
"""
import math
from pathlib import Path

import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]


def rice():
    b = pd.read_csv(ROOT / "product" / "backlog.csv")
    s = b[b["Issue Type"] == "Story"].copy()
    s["RICE"] = (s.Reach * s.Impact * s.Confidence / s.Effort).round(0).astype(int)
    s = s.sort_values("RICE", ascending=False)
    s[["Issue Key", "Summary", "Epic Name", "Reach", "Impact", "Confidence", "Effort", "RICE"]].to_csv(
        ROOT / "reports" / "rice_ranking.csv", index=False)
    return s


def sample_size(p_control, p_treatment, alpha=0.05, power=0.8, icc=0.05, requests_per_manager=4):
    """Requests per arm for a two-sided two-proportion test, then inflated for clustering.

    Hiring managers are randomised, not requests, so requests from one manager are
    correlated. Design effect = 1 + (m - 1) x ICC.
    """
    za, zb = norm.ppf(1 - alpha / 2), norm.ppf(power)
    pbar = (p_control + p_treatment) / 2
    n = ((za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(
        p_control * (1 - p_control) + p_treatment * (1 - p_treatment))) ** 2) / (p_control - p_treatment) ** 2
    deff = 1 + (requests_per_manager - 1) * icc
    return math.ceil(n), math.ceil(n * deff), deff


if __name__ == "__main__":
    (ROOT / "reports").mkdir(exist_ok=True)
    print(rice()[["Issue Key", "Summary", "RICE"]].to_string(index=False))
    # Baseline: 22% of service-desk tickets needed a follow-up question (Project 1, real data).
    n, n_adj, deff = sample_size(0.22, 0.17)
    print(f"\nIntake experiment: {n} requests per arm unclustered; {n_adj} per arm with design effect {deff:.2f}")
