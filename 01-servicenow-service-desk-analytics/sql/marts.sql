-- Reporting views on top of the fact tables. These are what the dashboard and the
-- write-up read from, so every number in the README traces back to one of them.

CREATE INDEX IF NOT EXISTS ix_inc_number ON fct_incident(number);
CREATE INDEX IF NOT EXISTS ix_state_number ON fct_state_interval(number);

-- Headline KPIs
DROP VIEW IF EXISTS mart_kpis;
CREATE VIEW mart_kpis AS
SELECT
    COUNT(*)                                             AS incidents,
    ROUND(AVG(made_sla), 4)                              AS sla_attainment,
    SUM(1 - made_sla)                                    AS sla_breaches,
    ROUND(AVG(reassignment_count > 0), 4)                AS reassigned_share,
    ROUND(AVG(reopen_count > 0), 4)                      AS reopen_rate,
    SUM(hours_to_resolve IS NULL)                        AS missing_resolution_time
FROM fct_incident;

-- SLA and resolution time by priority: checks whether priority actually changes how fast work moves
DROP VIEW IF EXISTS mart_sla_by_priority;
CREATE VIEW mart_sla_by_priority AS
SELECT priority,
       COUNT(*)                         AS incidents,
       ROUND(AVG(made_sla), 4)          AS sla_attainment,
       ROUND(AVG(reassignment_count), 2) AS avg_reassignments
FROM fct_incident
GROUP BY priority, priority_code
ORDER BY priority_code;

-- The core finding: SLA attainment falls with every reassignment
DROP VIEW IF EXISTS mart_reassignment_impact;
CREATE VIEW mart_reassignment_impact AS
SELECT reassign_band,
       COUNT(*)                                          AS incidents,
       ROUND(AVG(made_sla), 4)                           AS sla_attainment,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_incidents
FROM fct_incident
GROUP BY reassign_band
ORDER BY MIN(reassignment_count);

-- Same view held within one priority, so the pattern can't be explained by priority mix
DROP VIEW IF EXISTS mart_reassignment_within_priority;
CREATE VIEW mart_reassignment_within_priority AS
SELECT priority, reassign_band,
       COUNT(*)                 AS incidents,
       ROUND(AVG(made_sla), 4)  AS sla_attainment
FROM fct_incident
GROUP BY priority, priority_code, reassign_band
HAVING COUNT(*) >= 30
ORDER BY priority_code, MIN(reassignment_count);

-- Where open time goes. Elapsed calendar hours, not business hours.
DROP VIEW IF EXISTS mart_time_in_state;
CREATE VIEW mart_time_in_state AS
SELECT incident_state,
       COUNT(DISTINCT number)          AS incidents,
       ROUND(SUM(hours_in_state), 0)   AS total_hours,
       ROUND(100.0 * SUM(hours_in_state) / SUM(SUM(hours_in_state)) OVER (), 1) AS pct_of_open_hours
FROM fct_state_interval
WHERE incident_state NOT IN ('Resolved', 'Closed')
GROUP BY incident_state
ORDER BY total_hours DESC;

-- Assignment group scorecard, by the group that first received the ticket
DROP VIEW IF EXISTS mart_group_scorecard;
CREATE VIEW mart_group_scorecard AS
SELECT first_group,
       COUNT(*)                              AS incidents_received,
       ROUND(AVG(made_sla), 4)               AS sla_attainment,
       ROUND(AVG(first_group = resolving_group), 4) AS resolved_by_first_group,
       ROUND(AVG(reassignment_count), 2)     AS avg_reassignments
FROM fct_incident
WHERE first_group IS NOT NULL
GROUP BY first_group
HAVING COUNT(*) >= 200
ORDER BY incidents_received DESC;

-- The most common handoffs between groups
DROP VIEW IF EXISTS mart_top_handoffs;
CREATE VIEW mart_top_handoffs AS
SELECT from_group, to_group, COUNT(*) AS handoffs, SUM(is_bounce_back) AS bounce_backs
FROM fct_group_handoff
GROUP BY from_group, to_group
ORDER BY handoffs DESC
LIMIT 10;
