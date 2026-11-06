# UAT Test Plan: Release 1 (Online Estimate)

## Scope
User stories US-01, US-02 and US-03: vehicle entry, estimate range from the pricing API, and CRM lead creation. Tested by the sales manager, one appraiser and the product manager, on desktop and mobile (iOS Safari, Android Chrome), in the staging environment with test data.

## Entry criteria
- All Release 1 stories are code-complete and passed developer QA
- Staging connected to the pricing and vehicle-history **sandbox** APIs and a test CRM
- Test VINs and test customer data prepared (no real customer data)

## Exit criteria (go / no-go)
- 100% of test cases executed
- **No open Critical or High defects**
- Medium defects have an agreed fix date or an accepted workaround
- Sales manager signs off

## Defect severity
| Severity | Definition | Example |
|---|---|---|
| Critical | Blocks the flow or loses data | Lead not created in CRM |
| High | Wrong result with no workaround | Estimate range shown for the wrong trim |
| Medium | Wrong but has a workaround | VIN auto-fill fails, but drop-downs work |
| Low | Cosmetic | Button misaligned on small screens |

## Test cases
| ID | Story | Scenario | Steps | Expected result |
|---|---|---|---|---|
| TC-01 | US-01 | Valid VIN | Enter a valid 17-character test VIN | Year, make, model and trim auto-fill correctly |
| TC-02 | US-01 | Invalid VIN | Enter a 16-character VIN and submit | Error message shown; no API call made |
| TC-03 | US-01 | No VIN | Use the drop-downs to select year → make → model → trim | Each list filters correctly by the previous choice |
| TC-04 | US-02 | Estimate returned | Submit valid vehicle, mileage and condition | A low–high range appears within 5 seconds |
| TC-05 | US-02 | Disclaimer shown | Look at the result page | Text states the final offer depends on inspection |
| TC-06 | US-02 | Pricing API down | Set the sandbox API to return an error, then submit | Friendly fallback message; details still saved |
| TC-07 | US-02 | Very high mileage | Submit a vehicle with 400,000 km | Estimate is returned or routed to manual appraisal; no crash |
| TC-08 | US-03 | Lead created | Submit an estimate | CRM lead created with all fields, assigned to the on-shift salesperson within 1 minute |
| TC-09 | US-03 | Duplicate submission | Submit the same vehicle twice within 10 minutes | One lead, updated; no duplicate |
| TC-10 | US-03 | API down still creates lead | Repeat TC-06 | Lead is created and flagged "estimate pending" |
| TC-11 | All | Mobile | Run TC-01, TC-04, TC-08 on iOS Safari and Android Chrome | Same results as desktop; layout usable on a 375px screen |
| TC-12 | All | Privacy | Check the CRM lead and logs | Only required personal data stored; nothing in URL parameters |

## Defect log template
| Defect ID | Test case | Severity | Description | Steps to reproduce | Owner | Status |
|---|---|---|---|---|---|---|
| D-001 | | | | | | Open |
