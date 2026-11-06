# Interview notes (keep or delete before publishing)

Use these to practise explaining each project out loud. For each one, be ready to answer: *What was the problem? What did you do? What did you find? What would you do next?*

## 01 Workforce compliance
- **Why synthetic data?** "I can't share bank data, so I generated a dataset that reproduces the same problems: messy vendor exports, missing fields, duplicates."
- **Hardest part:** deciding what to do with bad records. Duplicates were dropped; missing bill rates were filled with the role median, because dropping them would bias the cost analysis; rows with no start date were dropped, because tenure can't be checked without one.
- **SQL to be ready to explain:** `HAVING` vs. `WHERE`; why `RANK() OVER` is a window function; why there's a 50-worker minimum in the vendor scorecard.
- **Best insight:** two vendors rated Low risk were among the worst performers, so the risk tiers needed to be based on actual compliance data.

## 02 Dealership inventory & A/B test
- **Why Mann-Whitney instead of a t-test?** Days-to-turn is skewed by a few cars that sit for a long time.
- **What does p = 0.004 mean?** If variant B made no difference, a gap this large would happen by chance only 0.4% of the time.
- **Why not trust the 48% mobile lift?** The confidence interval is wide; the true lift could be much smaller.
- **Honest finding:** the appraisal tool helped by about 2 days; pricing closer to market matters more.

## 03 AI answer accuracy eval
- **Why forbidden claims?** A confidently wrong answer is worse than an incomplete one, because people act on it.
- **Limitation to mention first:** phrase matching can be fooled by negation, so a human reviews every Incorrect verdict. Next step: an LLM grader, measured against human review.
- **Link to the role:** "My past jobs came down to 'is this answer right?' — compliance at Scotiabank, UAT on SAP. This applies the same thinking to AI."

## 04 Product case study
- **Why show a range, not a single price?** It sets honest expectations and protects trust when the in-person offer differs.
- **Where you overruled RICE:** the dashboard scored lowest but stayed in Release 2, because without it none of the success metrics can be measured.
- **Guardrail metric:** gross margin per trade-in, so speed isn't bought by overpaying.

## If asked how you built these
Be straightforward: "I built them with an AI coding assistant, then worked through every script until I could explain and change it myself." Only say this once it's true, so run each script, change a number, and see what happens before your interviews.
