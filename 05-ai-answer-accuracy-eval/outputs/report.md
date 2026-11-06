# Evaluation report

| Assistant | Questions | Fully correct | Partial | Incorrect | Avg. fact recall |
|---|---|---|---|---|---|
| assistant_a | 15.0 | 100% | 0% | 0% | 100% |
| assistant_b | 15.0 | 20% | 27% | 53% | 41% |

## Fact recall by topic

| Topic | assistant_a | assistant_b |
|---|---|---|
| Breaks | 100% | 100% |
| Hours & overtime | 100% | 39% |
| Leaves | 100% | 42% |
| Public holidays | 100% | 0% |
| Records | 100% | 100% |
| Scope | 100% | 0% |
| Severance | 100% | 25% |
| Termination | 100% | 25% |
| Vacation | 100% | 50% |

## Factual errors found

- **assistant_b / ot-01:** Overtime starts after 40 hours
- **assistant_b / hol-01:** Says there are 10 or more public holidays
- **assistant_b / term-02:** Says one week of notice is required
- **assistant_b / sev-01:** 2 weeks per year of service
- **assistant_b / sick-01:** Says ESA sick days are paid
- **assistant_b / par-01:** Parental leave is 35 weeks (outdated)
- **assistant_b / rest-01:** 8 hours between shifts
- **assistant_b / out-01:** Says ESA is the most you can receive
