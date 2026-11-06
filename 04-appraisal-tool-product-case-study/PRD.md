# PRD: Digital Trade-In Appraisal Tool

| | |
|---|---|
| **Owner** | Hira Hasan, Product Manager |
| **Stakeholders** | Dealership owner, Sales manager, Appraisers, Finance, Web developer team |
| **Status** | Approved for build |

## 1. Problem
- **Customers wait too long.** Getting a trade-in value means booking an in-person appraisal. Customers who are shopping around get offers elsewhere first.
- **Pricing is inconsistent.** Each appraiser uses their own judgement and sources. Overpaid trade-ins have to be listed above market, and above-market cars take longer to sell.
- **No data trail.** Appraisals are on paper, so the business can't see conversion rates or how accurate estimates were.

## 2. Users
| User | Need |
|---|---|
| **Trade-in customer** | A fast, believable estimate without visiting the lot |
| **Appraiser** | A standard checklist and market data in one place, so the final offer is quick and defensible |
| **Sales manager** | Visibility into trade-in leads and follow-up status |
| **Owner** | Fewer overpaid trade-ins and faster inventory turnover |

## 3. Goals and success metrics
| Goal | Metric | Baseline | Target (90 days after launch) |
|---|---|---|---|
| Capture more trade-in leads | Trade-in lead → appraisal booked conversion | Measure in first 2 weeks | +10% relative |
| Price consistently | Avg. gap between online estimate and final offer | Not tracked today | Within ±8% |
| Sell trade-ins faster | Median days-to-turn, trade-ins only | Current median | −5 days |
| Respond faster | Time from estimate to appraiser contact | ~2 days | < 4 business hours |

**Guardrail metric:** gross margin per trade-in must not fall. Faster sales at a loss are not a win.

## 4. Scope
**In scope (MVP):** online estimate form (VIN or year/make/model + mileage + condition), vehicle history and market price lookups via API, estimate range shown to the customer, lead sent to the CRM, appraiser inspection checklist, final-offer capture.

**Out of scope (later):** instant binding offers, photo-based damage detection, financing pre-approval in the same flow.

## 5. Requirements
| ID | Requirement | Priority |
|---|---|---|
| R1 | Customer can enter a VIN or pick year/make/model/trim | Must |
| R2 | System calls vehicle history and market pricing APIs and returns an estimate **range** within 5 seconds | Must |
| R3 | If an API fails, show a friendly message and still capture the lead | Must |
| R4 | Every submitted estimate creates a CRM lead with the vehicle details and estimate | Must |
| R5 | Appraiser sees the online estimate, checklist and market comparables on a tablet | Must |
| R6 | Final offer and any adjustment reason are recorded | Must |
| R7 | Dashboard of leads, conversion and estimate-vs-offer variance | Should |
| R8 | SMS/email confirmation to the customer | Should |

## 6. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Customers treat the estimate as a promise and feel misled | Show a **range**, state that the final offer depends on inspection, and track the estimate-vs-offer gap |
| Third-party API outage or cost increases | Cache recent valuations, degrade gracefully (R3), review API cost monthly |
| Appraisers don't adopt the checklist | Involve them in designing it; make it faster than paper |
| Personal data in leads | Collect only what's needed; follow the CRM's access controls and Canadian privacy law (PIPEDA) |

## 7. Launch plan
The release order comes from RICE scoring plus dependencies (`rice_score.py`, output in `roadmap.md`), with 8 person-weeks of capacity per release.

1. **Release 1 (MVP):** estimate form, API integrations, CRM lead (R1–R4)
2. **Release 2:** appraiser workflow, final-offer capture, customer notifications and dashboard (R5–R8)
3. **Later:** the out-of-scope ideas (financing pre-approval, photo damage detection, binding offers), revisited once Release 1 data shows whether customers trust the estimates

**A judgement call RICE doesn't make:** the dashboard (US-06) scores lowest of all MVP items (32) because only a few internal people use it. I kept it in Release 2 anyway, because without it we can't measure any of the success metrics in section 3.

Each release goes through UAT (see `uat_test_plan.md`) before go-live.
