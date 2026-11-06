# PRD: Contractor Onboarding Hub

**Status:** Draft for review · **Owner:** Hira Hasan (product) · **Platform:** ServiceNow Employee Center + HR Service Delivery, fed by Fieldglass and Employee Central

## Problem

A contractor's first day depends on work done in three systems by at least four teams (hiring manager, supplier, HR Ops, IT). Nobody sees the whole picture. Requests arrive incomplete, tasks wait for information, and access sometimes outlives the contract.

**Evidence**

| Signal | Number | Source |
|---|---|---|
| Service desk tickets that stalled waiting on the requester | 22% of tickets; median wait 96 h; 30% of all open hours | Project 1, real ServiceNow data |
| Tickets reassigned at least once | 46%; SLA falls from 78% to 14% as handoffs rise | Project 1 |
| Onboarding cases not ready by the start date | 7.9% | Project 3 sample (planted rate, not measured) |
| Contractor accounts active after the work order ended | 1.8% of work orders | Project 3 sample (planted rate, not measured) |

The Project 1 numbers are real but come from general IT tickets, not onboarding specifically. The first job of discovery is to confirm they hold for onboarding requests (see *Open questions*).

## Users

| User | Job to be done | Pain today |
|---|---|---|
| Hiring manager | "Get my contractor productive on day one" | Doesn't know what's needed or what's late; chases by email |
| HR Operations | "Create a correct worker record once" | Re-keys data; fixes bad cost centres and managers after the fact |
| IT / IAM | "Give the right access on the right day, and remove it on time" | Requests arrive without the app list; offboarding depends on someone remembering |
| Supplier contact | "Get my worker started so billing can begin" | Can't see what the worker still owes |

## Goals and metrics

**North Star:** % of contractors **day-one ready** (every onboarding task closed before the start date).

| Type | Metric | Baseline | Target (2 quarters) |
|---|---|---|---|
| North Star | Day-one ready | measure in discovery | +10 pts |
| Driver | Requests needing a follow-up question | 22% (P1 proxy) | 15% |
| Driver | Median days, work order approved → EC record | measure | ≤ 1 business day |
| Driver | Reassignments per onboarding request | measure | −30% |
| Guardrail | Hiring-manager time to complete intake | measure | ≤ 10 minutes |
| Guardrail | Contractor accounts active after end date | 1.8% (sample) | 0 within 1 day |

The intake-time guardrail matters because the obvious way to cut follow-up questions is a longer form. If the form takes 30 minutes, managers will work around it.

## Scope

**Release 1: stop the bleeding (6 weeks)**
- OB-11 Daily three-way reconciliation
- OB-10 Disable access on work order end
- OB-4 Validate cost centre and manager at submission
- OB-14 Experiment flag on intake

**Release 2: smart intake (6 weeks)**
- OB-3 Required fields by role type
- OB-2 Pre-fill from Fieldglass
- OB-8 Start-date risk alert
- OB-13 Onboarding funnel dashboard

**Later:** OB-6 Hiring-manager readiness view, OB-7 Supplier portal view

**Out of scope:** changing the Fieldglass requisition process; employee (non-contractor) onboarding, which could reuse the same design later.

## Prioritisation

Scored with RICE ([`../reports/rice_ranking.csv`](../reports/rice_ranking.csv)), then adjusted where the score misses something:

- **OB-10 (disable access) scores 162, in the bottom half, but ships in Release 1.** Its reach is small (only contractors who end each quarter), but an active account after a contract ends is an audit finding and a security risk. RICE doesn't weigh risk, so I overrode it.
- **OB-13 (dashboard) scores lowest but ships in Release 2.** Without it, none of the metrics above can be measured, so the team couldn't tell if Release 2 worked.
- **OB-7 (supplier portal) is deferred.** Low confidence (0.5): we don't yet know how many delays are actually waiting on the worker, and external access needs a security review that would hold up the release.

## Experiment

**Hypothesis:** required, role-specific intake fields (OB-3) reduce requests that need a follow-up question from 22% to 17%.

| | |
|---|---|
| Unit of randomisation | Hiring manager (not request), so one manager doesn't see both forms |
| Primary metric | % of onboarding requests that enter *Awaiting info* at least once |
| Guardrail | Median minutes to complete the intake |
| Sample size | 985 requests per arm at α = 0.05, power 0.8; **1,133 per arm** after a design effect of 1.15 (ICC 0.05, ~4 requests per manager) |
| Duration | At ~300 requests a month, about 7.6 months. That's too long |

**The trade-off.** Testing for a 5-point drop takes most of a year. Options:
1. Test for a 7-point drop instead (555 per arm, about 4 months). Risk: a real 5-point improvement could be missed.
2. Include employee onboarding requests to double volume. Risk: different users, so the result may not transfer.
3. Ship to everyone and compare before vs. after with a holdout of 10% of managers.

**Recommendation:** option 1. A change smaller than 7 points wouldn't justify the extra form fields anyway, and four months fits the roadmap. If the result is borderline, extend the test rather than calling it.

## Launch plan

1. Pilot with two business units that hire the most contractors.
2. Train HR Ops on the exception worklist before the reconciliation goes live; it will find a backlog on day one.
3. Clear the backlog of Critical exceptions (active accounts after end date) before announcing anything.
4. Roll out by business unit, two weeks apart, watching the guardrails.

## Risks and dependencies

| Risk | Mitigation |
|---|---|
| Fieldglass → EC integration isn't real-time, so pre-fill shows stale data | Show "last synced" on the form; edits go back through Fieldglass |
| Hiring managers bypass the form by emailing HR | HR Ops redirects to the form; track bypass rate |
| Automatic disable cuts off a contractor whose extension is late | Disable runs at 23:59 on the end date; managers get a 5-day warning; IAM can re-enable within 1 hour |
| Reconciliation floods teams with exceptions | Start with Critical and High only |

## Open questions

- What share of onboarding requests stall today, and on what? (Pull 3 months of onboarding cases from ServiceNow and repeat the Project 1 analysis on them.)
- Is the SLA clock paused during *Awaiting info*? This changes whether the problem shows up in current reports.
- Who signs off the automatic disable: IAM, or the business?
