"""Score AI assistant answers to Ontario employment law questions.

Each question in data/questions.json has:
  - required_facts:   facts a correct answer must state (any listed phrasing counts)
  - forbidden_claims: common wrong answers; stating one is a factual error

Verdict per answer:
  Correct    - every required fact present, no forbidden claim
  Partial    - some required facts missing, no forbidden claim
  Incorrect  - states a forbidden claim, or covers none of the required facts

Phrase matching is deliberately simple and transparent so a reviewer can see
exactly why an answer passed or failed. Every "Incorrect" verdict should still
be spot-checked by a person (see README, "Limitations").
"""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def contains(text: str, phrase: str) -> bool:
    """Case-insensitive phrase match that won't match inside a longer number
    or word (so '7 years' does not match '17 years')."""
    pattern = r"(?<![\w.])" + re.escape(phrase.lower()) + r"(?![\w])"
    return re.search(pattern, text.lower()) is not None


def score_answer(question: dict, answer: str) -> dict:
    hits = [f["fact"] for f in question["required_facts"] if any(contains(answer, p) for p in f["any_of"])]
    missed = [f["fact"] for f in question["required_facts"] if f["fact"] not in hits]
    errors = [c["claim"] for c in question["forbidden_claims"] if any(contains(answer, p) for p in c["any_of"])]

    recall = len(hits) / len(question["required_facts"])
    if errors or recall == 0:
        verdict = "Incorrect"
    elif recall == 1:
        verdict = "Correct"
    else:
        verdict = "Partial"
    return {"fact_recall": recall, "verdict": verdict,
            "missed_facts": "; ".join(missed), "errors": "; ".join(errors)}


def main() -> None:
    questions = json.loads((ROOT / "data" / "questions.json").read_text())
    answers = json.loads((ROOT / "data" / "sample_answers.json").read_text())

    rows = []
    for assistant, by_id in answers.items():
        if assistant.startswith("_"):
            continue
        for q in questions:
            answer = by_id.get(q["id"], "")
            rows.append({"assistant": assistant, "id": q["id"], "topic": q["topic"],
                         **score_answer(q, answer)})
    results = pd.DataFrame(rows)
    results.to_csv(OUT / "results_by_question.csv", index=False)

    summary = results.groupby("assistant").agg(
        questions=("id", "count"),
        accuracy=("verdict", lambda v: (v == "Correct").mean()),
        partial=("verdict", lambda v: (v == "Partial").mean()),
        error_rate=("verdict", lambda v: (v == "Incorrect").mean()),
        avg_fact_recall=("fact_recall", "mean"),
    )
    by_topic = results.pivot_table(index="topic", columns="assistant",
                                   values="fact_recall", aggfunc="mean")
    summary.to_csv(OUT / "summary.csv")

    # Markdown report a non-technical stakeholder can read
    pct = lambda x: f"{x:.0%}"
    lines = ["# Evaluation report", "",
             "| Assistant | Questions | Fully correct | Partial | Incorrect | Avg. fact recall |",
             "|---|---|---|---|---|---|"]
    for name, r in summary.iterrows():
        lines.append(f"| {name} | {r.questions} | {pct(r.accuracy)} | {pct(r.partial)} | "
                     f"{pct(r.error_rate)} | {pct(r.avg_fact_recall)} |")
    lines += ["", "## Fact recall by topic", "", "| Topic | " + " | ".join(by_topic.columns) + " |",
              "|---" * (len(by_topic.columns) + 1) + "|"]
    for topic, r in by_topic.iterrows():
        lines.append(f"| {topic} | " + " | ".join(pct(v) for v in r) + " |")
    lines += ["", "## Factual errors found", ""]
    errs = results[results.errors != ""]
    for _, r in errs.iterrows():
        lines.append(f"- **{r.assistant} / {r.id}:** {r.errors}")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")

    print(summary.to_string(float_format=lambda x: f"{x:.0%}"))
    print("\nFact recall by topic:\n", by_topic.to_string(float_format=lambda x: f"{x:.0%}"), sep="")
    print(f"\n{len(errs)} factual errors flagged. Full report: {OUT / 'report.md'}")


if __name__ == "__main__":
    main()
