# Hira (Harley) Hasan — Product & Data Analyst Portfolio

Four projects that show how I work across **data analysis**, **product management** and **technical delivery**. Each one is modelled on a real kind of problem I've worked on, rebuilt with **synthetic data** so no employer data is exposed.

| # | Project | What it shows | Tools |
|---|---------|---------------|-------|
| 01 | [Contingent Workforce Compliance Analytics](01-workforce-compliance-analytics/) | Cleaning messy HR/vendor data, flagging compliance risk, building a reporting model for leadership | Python (pandas), SQL (SQLite), Power BI / DAX, matplotlib |
| 02 | [Dealership Inventory & A/B Test Analysis](02-dealership-inventory-ab-test/) | Finding what slows inventory turnover and testing whether a website change really worked | Python, SciPy (statistical testing), matplotlib |
| 03 | [AI Answer Accuracy Evaluation](03-ai-answer-accuracy-eval/) | Building a repeatable way to score whether AI answers to Ontario employment law questions are correct | Python, JSONL test sets, rubric-based scoring |
| 04 | [Appraisal Tool Product Case Study](04-appraisal-tool-product-case-study/) | Taking a product from problem to launch plan: PRD, user stories, RICE roadmap, UAT test plan | Product docs, Python (RICE scoring) |

## Run everything

```bash
pip install -r requirements.txt
python 01-workforce-compliance-analytics/generate_data.py
python 01-workforce-compliance-analytics/pipeline.py
python 02-dealership-inventory-ab-test/generate_data.py
python 02-dealership-inventory-ab-test/analysis.py
python 03-ai-answer-accuracy-eval/evaluate.py
python 04-appraisal-tool-product-case-study/rice_score.py
```

Every script uses a fixed random seed, so the outputs match the numbers in each README.

## About me

Former Senior Program Analyst (Contingent Workforce Management) at Scotiabank, Product Manager Intern at Jones Autos, and current NPower Canada Data Analytics & AI participant. Based in Mississauga, ON.

[LinkedIn](https://www.linkedin.com/in/hirahasanq/) · hasanhira10@gmail.com
