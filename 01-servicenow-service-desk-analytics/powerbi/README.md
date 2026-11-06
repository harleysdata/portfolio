# Power BI model: Service Desk Performance

The Power BI version of the [live web dashboard](https://harleysdata.github.io/dashboards/service-desk.html). The data is in [`data/`](data/), exported by `src/export_powerbi.py`. The theme is [`../../powerbi-theme/hira-dark.json`](../../powerbi-theme/hira-dark.json). The measures below give the same numbers as the web dashboard and the write-up.

Every DAX measure below has a SQL equivalent in `sql/marts.sql`, which produced the numbers in the write-up. Build steps are at the end of this page.

## Star schema

```
                 DimDate (opened_at)
                        │ 1
                        │
DimGroup ──1───*  FactIncident  *───1── DimCategory (category, subcategory)
 (first_group,          │ 1                    
  resolving_group:      │
  one active, one       *
  inactive relationship)
              FactStateHours        FactGroupHandoff
              (number → FactIncident)  (number → FactIncident)
```

| Table | Grain | Key columns |
|---|---|---|
| FactIncident | one row per incident | number, opened_at, priority, first_group, resolving_group, reassignment_count, made_sla, hours_to_resolve |
| FactStateHours | one row per incident and state | number, incident_state, hours |
| FactGroupHandoff | one row per change of group | number, from_group, to_group, is_bounce_back |
| DimDate | one row per day | Date, Week, Month; marked as the date table |
| DimGroup | one row per assignment group | group name |

Choices worth explaining:
- **Two relationships to DimGroup.** First-touch group is active, resolving group is inactive and turned on in measures with `USERELATIONSHIP`. This lets one slicer answer "how do tickets *received by* Group 20 perform?" and "how do tickets *resolved by* Group 20 perform?"
- **Single-direction filters** from dimensions to facts. Bi-directional filtering between the facts would make handoff counts depend on slicer order.
- **Final-record grain for SLA.** `made_sla` changes during a ticket's life, so FactIncident keeps only the last audit record per ticket.

## Measures (DAX)

```dax
Incidents = COUNTROWS ( FactIncident )

SLA Attainment % =
DIVIDE ( CALCULATE ( [Incidents], FactIncident[made_sla] = 1 ), [Incidents] )

SLA Breaches = CALCULATE ( [Incidents], FactIncident[made_sla] = 0 )

Median Hours to Resolve =
MEDIANX ( FILTER ( FactIncident, NOT ISBLANK ( FactIncident[hours_to_resolve] ) ),
          FactIncident[hours_to_resolve] )

P90 Hours to Resolve =
PERCENTILEX.INC ( FILTER ( FactIncident, NOT ISBLANK ( FactIncident[hours_to_resolve] ) ),
                  FactIncident[hours_to_resolve], 0.9 )

Reassigned % =
DIVIDE ( CALCULATE ( [Incidents], FactIncident[reassignment_count] > 0 ), [Incidents] )

First-Touch Resolution % =
DIVIDE (
    CALCULATE ( [Incidents],
        FILTER ( FactIncident, FactIncident[first_group] = FactIncident[resolving_group] ) ),
    [Incidents] )

Breaches from Reassigned Tickets % =
DIVIDE (
    CALCULATE ( [SLA Breaches], FactIncident[reassignment_count] > 0 ),
    [SLA Breaches] )

-- Bounce-backs: ticket returned to a group it had already left (A → B → A)
Bounce-Back Incidents =
CALCULATE ( DISTINCTCOUNT ( FactGroupHandoff[number] ), FactGroupHandoff[is_bounce_back] = 1 )

-- Share of open time in each state (put incident_state on rows)
Open Hours = CALCULATE ( SUM ( FactStateHours[hours] ),
                         NOT FactStateHours[incident_state] IN { "Resolved", "Closed" } )
% of Open Hours =
DIVIDE ( [Open Hours], CALCULATE ( [Open Hours], REMOVEFILTERS ( FactStateHours[incident_state] ) ) )

-- Same group slicer, but scored by the group that resolved the ticket
SLA Attainment % (Resolving Group) =
CALCULATE ( [SLA Attainment %],
            USERELATIONSHIP ( FactIncident[resolving_group], DimGroup[group] ) )

-- Gap to the best band: how far each reassignment band is from zero-touch tickets
SLA Gap vs. No Reassignment (pts) =
[SLA Attainment %]
  - CALCULATE ( [SLA Attainment %], FactIncident[reassignment_count] = 0,
                REMOVEFILTERS ( FactIncident[reassign_band] ) )
```

## Report pages

1. **Overview.** KPI cards (Incidents, SLA Attainment %, Median Hours to Resolve, Reassigned %), monthly SLA trend, SLA by priority.
2. **Routing.** SLA by reassignment band, top handoff pairs (matrix with conditional formatting on bounce-backs), group scorecard with First-Touch Resolution %.
3. **Where time goes.** % of Open Hours by state, distribution of hours waiting on the user.
4. **Group drill-through.** Right-click any group to see its tickets, handoffs in and out, and SLA as first vs. resolving group.

Row-level security for a real deployment: a `DimGroup[manager_email] = USERPRINCIPALNAME()` role so team leads see only their own queues. The open dataset has no manager column, so this is documented but not built.

## Build it (about 45 minutes)

Power BI Desktop is free but only runs on Windows. On a Mac, use any Windows PC (a library, school or NPower lab machine), or a Windows virtual machine.

1. **Get data → Text/CSV** and load the four files in `data/`. In Power Query, set `opened_at` and `resolved_at` to *Date/Time*; `made_sla`, `priority_confirmed` and `knowledge_used` to *Whole number*.
2. **Add a date table:** *Modeling → New table* `DimDate = CALENDAR ( DATE ( 2016, 2, 1 ), DATE ( 2017, 3, 31 ) )`, then *Mark as date table*.
3. **Relationships** (Model view, all single-direction, one-to-many):
   `DimDate[Date]` → `FactIncident[opened_at]` (via a date column) · `DimGroup[group]` → `FactIncident[first_group]` (active) · `DimGroup[group]` → `FactIncident[resolving_group]` (inactive) · `FactIncident[number]` → `FactStateHours[number]` · `FactIncident[number]` → `FactGroupHandoff[number]`.
4. **Measures:** create a blank *_Measures* table and paste the DAX above.
5. **Theme:** *View → Themes → Browse for themes* → `hira-dark.json`.
6. **Pages** (16:9). Each mirrors a chapter of the web story:
   - *Overview:* 5 cards (Incidents, SLA Attainment %, Median Hours to Resolve, Reassigned %, % of Open Hours for *Awaiting User Info*). Clustered column of `SLA Attainment %` by `reassign_band`. Slicers for priority and category.
   - *Routing:* matrix of `first_group` × `resolving_group` with `Incidents`, conditional-format background scale. Table of groups with `First-Touch Resolution %` and data bars.
   - *Where time goes:* bar of `% of Open Hours` by `incident_state`; histogram of `hours_to_resolve` using a grouped column (bins of 24 h).
   - *Group drill-through:* drill-through on `DimGroup[group]` showing SLA as first vs. resolving group (`SLA Attainment % (Resolving Group)`).
7. **Check the numbers:** with no filters, *SLA Attainment %* must read **63.4%** and *Reassigned %* **45.6%**. If not, check that `made_sla` loaded as a number.
8. **Share:** *File → Export → PDF*, and save `ServiceDesk.pbix` into this folder. Add screenshots of each page to `powerbi/screenshots/`.

**Why the live version is a web page, not Power BI:** *Publish to web* (a public Power BI link) needs a work or school Microsoft account with a Pro licence, which a personal Gmail can't get for free. The web dashboard is free to host and anyone can open it. The `.pbix`, PDF and screenshots show the same analysis in Power BI.
