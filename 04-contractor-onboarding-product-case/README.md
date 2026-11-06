# Contractor Onboarding Hub: Product case study

**Type:** product discovery, PRD, prioritised backlog and experiment design.
**Tools:** Jira (importable backlog CSV) · RICE scoring in Python · power analysis (scipy) · ServiceNow Employee Center as the delivery platform.
**Question:** Projects 1–3 found the problems. What should a product team build first, and how would it know it worked?

---

## From analysis to product

| Earlier finding | Product response |
|---|---|
| 22% of service-desk tickets stalled waiting on the requester; 30% of open hours (Project 1, real data) | **Smart intake:** collect everything at the start, with required fields by role |
| SLA drops from 78% to 14% as tickets bounce between teams (Project 1) | **Validation at submission** so requests don't need to be sent back |
| Accounts still active after contracts end; extensions not synced (Project 3) | **Automatic offboarding** and a daily reconciliation |
| Nobody can see if a contractor will be ready on day one | **Readiness tracker** for hiring managers and HR Ops |

## What's here

| File | What it is |
|---|---|
| [`product/prd.md`](product/prd.md) | The PRD: problem and evidence, users, North Star and guardrails, scope, prioritisation decisions, experiment, launch plan, risks |
| [`product/backlog.csv`](product/backlog.csv) | 4 epics, 10 user stories with acceptance criteria, ready to import into Jira (*Issues → Import from CSV*) |
| [`src/prioritise.py`](src/prioritise.py) | RICE scoring and the experiment sample-size calculation |
| [`reports/rice_ranking.csv`](reports/rice_ranking.csv) | Ranked backlog |

## Metrics

```
North Star: % of contractors day-one ready (every onboarding task closed before start)
│
├── Driver: requests needing a follow-up question        (baseline proxy 22%, target 15%)
├── Driver: days from work order approval to HR record   (target ≤ 1 business day)
├── Driver: reassignments per onboarding request         (target −30%)
│
└── Guardrails: intake time ≤ 10 min · accounts active after end date → 0
```

The guardrail on intake time is there because the easy way to reduce follow-up questions is a longer form, and managers will work around a form that takes 30 minutes.

## Decisions where I didn't follow the score

| Story | RICE | Decision | Why |
|---|---|---|---|
| Daily three-way reconciliation | 1,800 (1st) | Release 1 | Highest score, and it measures the problem |
| Disable access on work order end | 162 (8th) | **Release 1** | Small reach, but it's a security and audit risk. RICE doesn't score risk |
| Onboarding funnel dashboard | 30 (last) | **Release 2** | Without it, no other metric can be measured |
| Supplier portal view | 38 | **Deferred** | Low confidence, and external access needs a security review |

## Experiment design

Hypothesis: role-specific required fields cut requests needing a follow-up from 22% to 17%. Randomised by hiring manager, so one manager never sees both forms.

| Effect to detect | Requests per arm (with clustering) | At ~300/month |
|---|---|---|
| 22% → 17% (5 pts) | 1,133 | ~7.6 months |
| 22% → 16% (6 pts) | 771 | ~5 months |
| 22% → 15% (7 pts) | 555 | ~4 months |

Five points takes too long to test. I recommend testing for seven points: a smaller gain wouldn't justify the extra form fields anyway, and four months fits the roadmap. The PRD covers the other options and why I didn't choose them.

## Honest limits

- The 22% baseline is from general IT tickets (Project 1), not onboarding requests. The PRD's first open question is to measure it on onboarding cases.
- Project 3's rates come from planted sample data, so they show the method, not a real defect rate.
- Reach and effort in the RICE scores are my estimates. In a real team, engineering sets effort and the scores get revisited each quarter.

## Reproduce

```bash
python src/prioritise.py
```
