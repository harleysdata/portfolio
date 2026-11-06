"""Clean the raw contingent workforce export, load it into SQLite, run the
compliance queries and produce the charts and CSVs a Power BI report would use.

Steps:
  1. Clean   - standardize text, fix Y/N flags, parse dates, drop duplicates
  2. Validate - log what was fixed or dropped (a data-quality report)
  3. Derive  - count failed checks per worker and set an is_compliant flag
  4. Load    - write a small star schema into SQLite
  5. Report  - run sql/compliance_queries.sql and save results + charts
"""
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
DATA, SQL, OUT = ROOT / "data", ROOT / "sql", ROOT / "outputs"
OUT.mkdir(exist_ok=True)

YES = {"y": 1, "yes": 1, "n": 0, "no": 0}


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {"raw_rows": len(raw)}
    df = raw.copy()

    df = df.drop_duplicates()
    log["duplicates_removed"] = log["raw_rows"] - len(df)

    df["business_unit"] = df.business_unit.str.strip().str.title()
    for col in ["nda_signed", "training_completed", "tenure_review_done"]:
        df[col] = df[col].str.strip().str.lower().map(YES)

    df["start_date"] = pd.to_datetime(df.start_date, errors="coerce")
    df["end_date"] = pd.to_datetime(df.end_date, errors="coerce")
    bad_dates = df.start_date.isna()
    log["rows_dropped_bad_start_date"] = int(bad_dates.sum())
    df = df[~bad_dates]

    missing_rate = df.bill_rate_cad.isna()
    log["bill_rates_imputed"] = int(missing_rate.sum())
    # Fill missing bill rates with the median for that role (a common, defensible choice).
    df["bill_rate_cad"] = df.bill_rate_cad.fillna(df.groupby("role").bill_rate_cad.transform("median"))

    log["clean_rows"] = len(df)
    return df, log


def derive(df: pd.DataFrame) -> pd.DataFrame:
    checks = pd.DataFrame({
        "bg": df.background_check_status.eq("Pending"),
        "nda": df.nda_signed.eq(0),
        "training": df.training_completed.eq(0),
        "tenure": df.tenure_review_done.eq(0),
    })
    df = df.assign(issue_count=checks.sum(axis=1), is_compliant=(checks.sum(axis=1) == 0).astype(int))
    return df


def load(df: pd.DataFrame, vendors: pd.DataFrame) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript((SQL / "schema.sql").read_text())
    vendors.assign(contract_end_date=vendors.contract_end_date.astype(str)).to_sql(
        "vendors", con, if_exists="append", index=False)
    out = df.assign(start_date=df.start_date.dt.date.astype(str), end_date=df.end_date.dt.date.astype(str))
    out.to_sql("contingent_workers", con, if_exists="append", index=False)
    return con


def run_queries(con: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    results = {}
    for block in (SQL / "compliance_queries.sql").read_text().split("-- name: ")[1:]:
        name, _, query = block.partition("\n")
        results[name.strip()] = pd.read_sql_query(query, con)
    return results


def charts(results: dict[str, pd.DataFrame]) -> None:
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    issues = results["issues_by_type"].sort_values("workers")
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(issues.issue, issues.workers, color="#4C5B8C")
    ax.set_title("Contractors failing each compliance check")
    ax.set_xlabel("Workers")
    for y, v in enumerate(issues.workers):
        ax.text(v + 5, y, f"{v:,}", va="center")
    fig.tight_layout()
    fig.savefig(OUT / "issues_by_type.png", dpi=150)

    vs = results["vendor_scorecard"].sort_values("compliance_rate_pct")
    colors = vs.risk_tier.map({"High": "#B5443A", "Medium": "#D99A3A", "Low": "#4C8C6A"})
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(vs.vendor_name, vs.compliance_rate_pct, color=colors)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=f"{t} risk tier") for t, c in
                       [("High", "#B5443A"), ("Medium", "#D99A3A"), ("Low", "#4C8C6A")]],
              frameon=False, loc="lower right")
    ax.set_title("10 lowest-compliance vendors")
    ax.set_xlabel("Compliance rate (%)")
    ax.set_xlim(0, 100)
    fig.tight_layout()
    fig.savefig(OUT / "vendor_scorecard.png", dpi=150)


def main() -> None:
    raw = pd.read_csv(DATA / "contingent_workers_raw.csv")
    vendors = pd.read_csv(DATA / "vendors.csv", parse_dates=["contract_end_date"])

    df, log = clean(raw)
    df = derive(df)
    con = load(df, vendors)
    results = run_queries(con)
    charts(results)

    df.to_csv(OUT / "contingent_workers_clean.csv", index=False)  # Power BI source
    for name, table in results.items():
        table.to_csv(OUT / f"{name}.csv", index=False)
    pd.Series(log).to_csv(OUT / "data_quality_log.csv", header=["value"])

    print("Data quality log:")
    for k, v in log.items():
        print(f"  {k:30} {v:,}")
    for name, table in results.items():
        print(f"\n== {name} ==\n{table.to_string(index=False)}")


if __name__ == "__main__":
    main()
