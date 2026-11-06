# Power BI model: Service Desk Performance

This is the semantic model I would publish on top of the warehouse in `data/service_desk.db`. The web dashboard on my portfolio site reads the same marts, so the numbers match.

To build it in Power BI Desktop (Windows), connect through the SQLite ODBC driver, or export the three fact tables to CSV with `sqlite3 -csv`. Power BI Desktop doesn't run on macOS, so I designed the model here and tested the measure logic in SQL (`sql/marts.sql`). Every DAX measure below has a SQL equivalent that produced the numbers in the write-up.

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
              FactStateInterval     FactGroupHandoff
              (number → FactIncident)  (number → FactIncident)
```

| Table | Grain | Key columns |
|---|---|---|
| FactIncident | one row per incident | number, opened_at, priority, first_group, resolving_group, reassignment_count, made_sla, hours_to_resolve |
| FactStateInterval | one row per audit event | number, incident_state, hours_in_state |
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
Open Hours = CALCULATE ( SUM ( FactStateInterval[hours_in_state] ),
                         NOT FactStateInterval[incident_state] IN { "Resolved", "Closed" } )
% of Open Hours =
DIVIDE ( [Open Hours], CALCULATE ( [Open Hours], REMOVEFILTERS ( FactStateInterval[incident_state] ) ) )

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
