# User Stories

Format: *As a [user], I want [action] so that [outcome].* Acceptance criteria use Given / When / Then.

## Epic 1: Online estimate (Release 1)

### US-01 Enter my vehicle
As a **trade-in customer**, I want to enter my VIN or choose my vehicle from a list so that I don't have to know technical details.
- **Given** I'm on the trade-in page, **when** I enter a valid 17-character VIN, **then** year, make, model and trim fill in automatically.
- **Given** I don't have my VIN, **when** I choose "Select my vehicle", **then** I can pick year → make → model → trim from drop-downs.
- **Given** I enter an invalid VIN, **when** I submit, **then** I see "That VIN doesn't look right. Check it or select your vehicle instead."

### US-02 See an estimate range
As a **trade-in customer**, I want to see an estimated value range so that I know whether it's worth coming in.
- **Given** valid vehicle details, mileage and condition, **when** I submit, **then** I see a low–high range within 5 seconds.
- **Then** the page states the final offer depends on an in-person inspection.
- **Given** the pricing API is unavailable, **when** I submit, **then** I see "We'll email your estimate within 1 business hour" and my details are still saved.

### US-03 Lead reaches sales
As a **sales manager**, I want every estimate to create a CRM lead so that no trade-in customer is missed.
- **Given** a customer submits an estimate, **when** it completes, **then** a CRM lead is created with contact details, vehicle, mileage, condition and the estimate range.
- **Then** the lead is assigned to the on-shift salesperson and appears in their queue within 1 minute.

## Epic 2: Appraiser workflow (Release 2)

### US-04 Standard inspection checklist
As an **appraiser**, I want a standard inspection checklist on a tablet so that every car is assessed the same way.
- **Given** a booked appraisal, **when** I open it, **then** I see the online estimate, vehicle history summary and market comparables.
- **When** I complete the checklist, **then** each section (exterior, interior, mechanical, tires, history flags) must be marked before I can submit.

### US-05 Record the final offer
As an **owner**, I want the final offer and the reason for any change from the estimate recorded so that I can see how accurate our estimates are.
- **Given** a completed inspection, **when** the appraiser enters a final offer more than 8% away from the estimate range, **then** an adjustment reason is required.
- **Then** the final offer is saved to the CRM lead.

## Epic 3: Reporting and notifications (Release 3)

### US-06 Trade-in dashboard
As an **owner**, I want a dashboard of trade-in leads, conversion and estimate-vs-offer variance so that I can see whether the tool is working.
- **Then** the dashboard shows weekly leads, % booked, % purchased, median estimate-vs-offer gap and median days-to-turn for trade-ins.

### US-07 Customer confirmation
As a **trade-in customer**, I want a text or email with my estimate so that I can come back to it.
- **Given** I opted in, **when** my estimate is generated, **then** I receive it by my chosen channel within 5 minutes, with a link to book an appraisal.
