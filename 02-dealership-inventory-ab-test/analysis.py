"""Two analyses for a used-car dealership.

Part 1 - Inventory turnover: what makes cars sit on the lot, and did the
         digital appraisal tool change days-to-turn for trade-ins?
Part 2 - A/B test: did the new lead form (B) increase lead submissions,
         and is the difference statistically significant?
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent
DATA, OUT = ROOT / "data", ROOT / "outputs"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


# ------------------------------------------------------------- Part 1
def inventory() -> None:
    inv = pd.read_csv(DATA / "inventory.csv", parse_dates=["acquired_date"])
    print(f"Vehicles: {len(inv):,} | median days-to-turn: {inv.days_to_turn.median():.0f}")

    inv["pricing_band"] = pd.cut(inv.price_vs_market_pct, [-np.inf, -2, 2, 6, np.inf],
                                 labels=["Under market (<-2%)", "At market (±2%)",
                                         "Above market (2-6%)", "Well above (>6%)"])
    by_band = inv.groupby("pricing_band", observed=True).days_to_turn.agg(["count", "median"])
    by_body = inv.groupby("body_type").days_to_turn.median().sort_values()
    print("\nMedian days-to-turn by pricing band:\n", by_band, sep="")
    print("\nMedian days-to-turn by body type:\n", by_body, sep="")

    # Correlation of each numeric driver with days-to-turn
    inv["vehicle_age"] = 2026 - inv.model_year
    corr = inv[["price_vs_market_pct", "vehicle_age", "mileage_km", "days_to_turn"]].corr()["days_to_turn"]
    print("\nCorrelation with days-to-turn:\n", corr.drop("days_to_turn").round(2), sep="")

    # Did the digital appraisal tool help? Compare trade-ins only.
    trade = inv[inv.source == "Trade-in"]
    manual = trade[trade.appraisal_method == "Manual"].days_to_turn
    digital = trade[trade.appraisal_method == "Digital tool"].days_to_turn
    u = stats.mannwhitneyu(manual, digital, alternative="greater")
    diff = manual.mean() - digital.mean()
    print(f"\nTrade-ins: manual mean {manual.mean():.1f} days (n={len(manual)}), "
          f"digital tool mean {digital.mean():.1f} days (n={len(digital)})")
    print(f"Difference: {diff:.1f} days | Mann-Whitney U p-value: {u.pvalue:.2g}")

    summary = pd.DataFrame({
        "metric": ["manual_mean_days", "digital_mean_days", "difference_days", "p_value"],
        "value": [manual.mean(), digital.mean(), diff, u.pvalue],
    })
    summary.to_csv(OUT / "appraisal_tool_impact.csv", index=False)
    by_band.to_csv(OUT / "days_to_turn_by_pricing.csv")

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].bar(by_band.index.astype(str), by_band["median"], color="#4C5B8C")
    axes[0].set_title("Overpriced cars sit longer")
    axes[0].set_ylabel("Median days-to-turn")
    axes[0].tick_params(axis="x", rotation=20)
    axes[1].boxplot([manual, digital], tick_labels=["Manual appraisal", "Digital tool"], showfliers=False)
    axes[1].set_title(f"Trade-ins: digital tool cut {diff:.0f} days on average")
    axes[1].set_ylabel("Days-to-turn")
    fig.tight_layout()
    fig.savefig(OUT / "inventory_turnover.png", dpi=150)


# ------------------------------------------------------------- Part 2
def two_proportion_test(conv_a, n_a, conv_b, n_b):
    """Two-sided z-test for the difference between two conversion rates."""
    p_a, p_b = conv_a / n_a, conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (p_b - p_a) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    # 95% confidence interval for the difference (unpooled standard error)
    se_diff = np.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
    ci = (p_b - p_a - 1.96 * se_diff, p_b - p_a + 1.96 * se_diff)
    return p_a, p_b, z, p_value, ci


def ab_test() -> None:
    ab = pd.read_csv(DATA / "ab_test.csv")
    rows = []
    for segment, df in [("All", ab), *ab.groupby("device")]:
        g = df.groupby("variant").submitted_lead.agg(["sum", "count"])
        p_a, p_b, z, p, ci = two_proportion_test(g.loc["A", "sum"], g.loc["A", "count"],
                                                 g.loc["B", "sum"], g.loc["B", "count"])
        rows.append({"segment": segment, "sessions": len(df), "rate_A": p_a, "rate_B": p_b,
                     "relative_lift": p_b / p_a - 1, "z": z, "p_value": p,
                     "ci_low": ci[0], "ci_high": ci[1], "significant": p < 0.05})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "ab_test_results.csv", index=False)
    show = res.copy()
    for c in ["rate_A", "rate_B", "relative_lift", "ci_low", "ci_high"]:
        show[c] = (show[c] * 100).round(2).astype(str) + "%"
    show["p_value"] = show.p_value.round(4)
    print("\nA/B test results:\n", show.drop(columns="z").to_string(index=False), sep="")

    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    x = np.arange(len(res))
    ax.bar(x - 0.18, res.rate_A * 100, 0.36, label="A: current form", color="#9AA3BF")
    ax.bar(x + 0.18, res.rate_B * 100, 0.36, label="B: short form, CTA higher", color="#4C5B8C")
    ax.set_xticks(x, res.segment)
    ax.set_ylabel("Lead submission rate (%)")
    ax.set_title("Variant B wins on mobile")
    ax.set_ylim(0, max(res.rate_B.max(), res.rate_A.max()) * 100 * 1.35)
    ax.legend(frameon=False, loc="upper left", ncols=2)
    fig.tight_layout()
    fig.savefig(OUT / "ab_test.png", dpi=150)


if __name__ == "__main__":
    inventory()
    ab_test()
