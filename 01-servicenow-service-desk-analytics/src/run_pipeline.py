"""End-to-end run: raw export -> clean events -> warehouse -> marts -> figures -> dashboard data.

    python src/run_pipeline.py
"""
import json
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import ingest, model, routing  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
FIG = OUT / "figures"
DB = ROOT / "data" / "service_desk.db"

INK, MUTED, ACCENT, GOOD = "#1f2328", "#8b949e", "#c4314b", "#2f6f4f"


def style(ax, title):
    ax.set_title(title, loc="left", fontsize=12, color=INK, pad=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK, labelsize=9)


def figures(con):
    FIG.mkdir(parents=True, exist_ok=True)

    r = pd.read_sql("SELECT * FROM mart_reassignment_impact", con)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.bar(r.reassign_band, r.sla_attainment * 100,
                  color=[GOOD] + [ACCENT] * (len(r) - 1))
    ax.bar_label(bars, labels=[f"{v:.0%}" for v in r.sla_attainment], fontsize=9, padding=3)
    ax.set_ylim(0, 100); ax.set_ylabel("SLA met (%)"); ax.set_xlabel("Times reassigned")
    style(ax, "SLA attainment falls with every reassignment")
    fig.tight_layout(); fig.savefig(FIG / "sla_by_reassignment.png", dpi=160); plt.close(fig)

    p = pd.read_sql("SELECT * FROM mart_sla_by_priority", con)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(p.priority, p.sla_attainment * 100, color=MUTED)
    ax.bar_label(bars, labels=[f"{v:.1%}  (n={n:,})" for v, n in zip(p.sla_attainment, p.incidents)],
                 fontsize=9, padding=3)
    ax.invert_yaxis(); ax.set_xlim(0, 110); ax.set_xlabel("SLA met (%)")
    style(ax, "Critical and High tickets almost never meet SLA")
    fig.tight_layout(); fig.savefig(FIG / "sla_by_priority.png", dpi=160); plt.close(fig)

    t = pd.read_sql("SELECT * FROM mart_time_in_state", con)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(t.incident_state, t.pct_of_open_hours, color=MUTED)
    ax.bar_label(bars, labels=[f"{v:.0f}%" for v in t.pct_of_open_hours], fontsize=9, padding=3)
    ax.invert_yaxis(); ax.set_xlabel("Share of open hours (%)")
    style(ax, "Almost a third of open time is spent waiting on the user")
    fig.tight_layout(); fig.savefig(FIG / "time_in_state.png", dpi=160); plt.close(fig)


def main():
    raw = ingest.load_raw()
    events, dq_log = ingest.clean(raw)

    inc = model.build_incident(events)
    tables = {
        "fct_incident": inc,
        "fct_state_interval": model.build_state_intervals(events),
        "fct_group_handoff": model.build_handoffs(events),
    }
    con = model.load_warehouse(DB, tables)

    OUT.mkdir(exist_ok=True)
    pd.DataFrame(dq_log).to_csv(OUT / "data_quality_log.csv", index=False)

    marts = {v: pd.read_sql(f"SELECT * FROM {v}", con) for v in [
        "mart_kpis", "mart_sla_by_priority", "mart_reassignment_impact",
        "mart_reassignment_within_priority", "mart_time_in_state",
        "mart_group_scorecard", "mart_top_handoffs"]}

    resolved = inc.dropna(subset=["hours_to_resolve"])
    reassigned = inc.reassignment_count > 0
    extra = {
        "median_hours_to_resolve": round(resolved.hours_to_resolve.median(), 1),
        "p90_hours_to_resolve": round(resolved.hours_to_resolve.quantile(0.9), 1),
        "breaches_from_reassigned_share": round(((inc.made_sla == 0) & reassigned).sum()
                                                / (inc.made_sla == 0).sum(), 4),
        "median_ttr_not_reassigned": round(resolved[resolved.reassignment_count == 0].hours_to_resolve.median(), 2),
        "median_ttr_reassigned": round(resolved[resolved.reassignment_count > 0].hours_to_resolve.median(), 1),
        "bounce_back_incidents": int(tables["fct_group_handoff"].groupby("number").is_bounce_back.max().sum()),
        "sla_priority_confirmed": round(inc[inc.priority_confirmed == 1].made_sla.mean(), 4),
        "sla_priority_unconfirmed": round(inc[inc.priority_confirmed == 0].made_sla.mean(), 4),
    }
    wait = pd.read_sql("""SELECT number, SUM(hours_in_state) h FROM fct_state_interval
                          WHERE incident_state='Awaiting User Info' GROUP BY number HAVING h > 0""", con)
    extra["incidents_waiting_on_user"] = len(wait)
    extra["median_wait_on_user_hours"] = round(wait.h.median(), 1)

    rt = routing.evaluate(inc)
    rt["rules"].to_csv(OUT / "routing_rules.csv", index=False)
    extra["routing"] = {k: (round(v, 4) if isinstance(v, float) else v)
                        for k, v in rt.items() if k != "rules"}
    extra["routing"]["rule_count"] = len(rt["rules"])

    figures(con)

    summary = {k: v.to_dict(orient="records") for k, v in marts.items()} | {"derived": extra}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary["mart_kpis"], indent=2))
    print(json.dumps(extra, indent=2, default=str))


if __name__ == "__main__":
    main()
