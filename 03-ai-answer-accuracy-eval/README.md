# AI Answer Accuracy Evaluation: Ontario Employment Law

**Problem:** People increasingly ask AI assistants about their rights at work. A wrong answer about overtime, sick days or severance can cost someone real money. How do you measure, repeatably, whether an assistant gets these answers right?

**What I built:** a small evaluation framework:
- a **test set** of 15 Ontario *Employment Standards Act* (ESA) questions, each with the facts a correct answer must contain and the common wrong answers to watch for
- a **scorer** that grades each answer as Correct, Partial or Incorrect and explains why
- a **report** that summarizes accuracy, error rate and weak topics for a non-technical reader

## Tools
Python (pandas, regular expressions) · JSON test sets · rubric-based scoring

## How to run
```bash
python evaluate.py      # writes outputs/report.md, summary.csv, results_by_question.csv
```

## How the scoring works

Each question in `data/questions.json` looks like this:

```json
{
  "id": "ot-01",
  "question": "In Ontario, after how many hours a week does an employee earn overtime, and at what rate?",
  "required_facts": [
    {"fact": "Overtime starts after 44 hours in a work week", "any_of": ["44 hours", "forty-four hours"]},
    {"fact": "Rate is 1.5 times the regular rate", "any_of": ["1.5 times", "time and a half"]}
  ],
  "forbidden_claims": [
    {"claim": "Overtime starts after 40 hours", "any_of": ["after 40 hours", "over 40 hours"]}
  ]
}
```

| Verdict | Rule |
|---|---|
| **Correct** | All required facts present, no forbidden claim |
| **Partial** | Some required facts missing, no forbidden claim |
| **Incorrect** | Contains a forbidden claim, or none of the required facts |

The forbidden claims matter as much as the required facts. An answer that says "overtime after 40 hours" is worse than one that leaves the number out, because people act on it.

## Sample results

`data/sample_answers.json` contains **two illustrative sets of answers I wrote to test the scorer**. They are not output from any real AI product. Assistant A is written to be accurate; assistant B makes the kinds of mistakes AI tools commonly make (US rules, outdated numbers, missing caveats).

| Assistant | Fully correct | Partial | Incorrect | Avg. fact recall |
|---|---|---|---|---|
| assistant_a | 100% | 0% | 0% | 100% |
| assistant_b | 20% | 27% | 53% | 41% |

The scorer caught all 8 planted errors in assistant B, including:
- **US rule applied to Ontario:** overtime after 40 hours (Ontario is 44)
- **Outdated law:** parental leave of 35 weeks (now up to 61 or 63)
- **Wrong benefit:** "3 paid sick days" (ESA sick leave is unpaid)
- **Dangerous scope error:** telling someone fired after 10 years that ESA severance is "the most you can receive" (ESA amounts are minimums; common law can give more)

## To evaluate a real assistant
1. Ask it each question in `data/questions.json` in a fresh chat.
2. Paste its answers into `sample_answers.json` under a new name (for example `"chatbot_x"`).
3. Run `python evaluate.py`. The report compares it against the others.

## Limitations (and what I'd do next)
- **Phrase matching is simple on purpose.** It's transparent, but it can miss a correct answer phrased unusually, or be fooled by negation ("it is *not* 44 hours"). Every Incorrect verdict should be spot-checked by a person. A next step is adding an LLM-as-judge grader and measuring how often it agrees with human review.
- **The law changes.** Facts are based on Ontario's *Your guide to the Employment Standards Act* (the sources below were checked in November 2026). Amounts that change yearly, like the minimum wage, were left out on purpose. The test set should be re-checked at least once a year.
- **15 questions is a pilot.** A production eval would need hundreds of questions, including edge cases (exemptions for specific industries, managers, students).

## Sources checked
- [Domestic or sexual violence leave](https://www.ontario.ca/document/your-guide-employment-standards-act-0/domestic-or-sexual-violence-leave) — 10 days and 15 weeks per calendar year; first 5 days paid
- [Severance pay](https://www.ontario.ca/document/your-guide-employment-standards-act/severance-pay) — 5+ years and $2.5M payroll; up to 26 weeks
- [Record keeping](https://ontario.ca/document/your-guide-employment-standards-act-0/record-keeping) — most records kept for 3 years
- Other facts: [Your guide to the Employment Standards Act](https://www.ontario.ca/document/your-guide-employment-standards-act-0)

*This project measures AI accuracy. It is not legal advice.*
