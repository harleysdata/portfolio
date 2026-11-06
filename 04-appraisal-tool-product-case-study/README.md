# Product Case Study: Digital Trade-In Appraisal Tool

How I'd take a product from a business problem to a launch-ready plan, using a used-car dealership's trade-in process as the example.

> A case study based on the kind of product work I did at Jones Autos. Names, numbers and specifics are illustrative, not confidential company data.

| Document | What it shows |
|---|---|
| [PRD.md](PRD.md) | Problem, users, goals and success metrics, scope, requirements, risks |
| [user_stories.md](user_stories.md) | Epics and user stories with acceptance criteria (Given / When / Then) |
| [rice_roadmap.csv](rice_roadmap.csv) + [rice_score.py](rice_score.py) | Backlog scored with RICE, turned into a 3-release roadmap |
| [uat_test_plan.md](uat_test_plan.md) | UAT scope, entry/exit criteria, test cases and defect severity rules |

## Run the RICE scoring
```bash
python rice_score.py   # prints the ranked backlog and writes roadmap.md
```

## The story in one paragraph
Trade-in customers waited up to two days for a manual appraisal, and many bought elsewhere in the meantime. Appraisers also priced inconsistently, so some trade-ins were bought above market and then sat on the lot. The tool gives customers an instant online estimate using vehicle history and market pricing data, and gives appraisers a standard workflow to confirm it in person. Success is measured by trade-in lead conversion, estimate-to-final-offer variance and days-to-turn on trade-ins.
