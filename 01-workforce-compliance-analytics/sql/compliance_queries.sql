-- name: overall_compliance
-- Headline KPI: how many active contractors are fully compliant?
SELECT
    COUNT(*)                                   AS total_workers,
    SUM(is_compliant)                          AS compliant_workers,
    ROUND(100.0 * SUM(is_compliant) / COUNT(*), 1) AS compliance_rate_pct
FROM contingent_workers;

-- name: vendor_scorecard
-- Vendor scorecard: compliance rate per vendor, worst first.
-- Only vendors with 50+ workers, so small vendors don't distort the ranking.
SELECT
    v.vendor_name,
    v.risk_tier,
    COUNT(*)                                        AS workers,
    ROUND(100.0 * SUM(w.is_compliant) / COUNT(*), 1) AS compliance_rate_pct,
    SUM(w.issue_count)                              AS open_issues
FROM contingent_workers w
JOIN vendors v ON v.vendor_id = w.vendor_id
GROUP BY v.vendor_name, v.risk_tier
HAVING COUNT(*) >= 50
ORDER BY compliance_rate_pct ASC
LIMIT 10;

-- name: issues_by_type
-- Which check fails most often? Tells the program where to focus.
SELECT 'Background check pending' AS issue, SUM(background_check_status = 'Pending') AS workers FROM contingent_workers
UNION ALL SELECT 'NDA not signed',        SUM(nda_signed = 0)          FROM contingent_workers
UNION ALL SELECT 'Training incomplete',   SUM(training_completed = 0)  FROM contingent_workers
UNION ALL SELECT 'Tenure review overdue', SUM(tenure_review_done = 0)  FROM contingent_workers
ORDER BY workers DESC;

-- name: business_unit_risk
-- Compliance by business unit, with a window function ranking each unit.
SELECT
    business_unit,
    COUNT(*) AS workers,
    ROUND(100.0 * SUM(is_compliant) / COUNT(*), 1) AS compliance_rate_pct,
    RANK() OVER (ORDER BY 1.0 * SUM(is_compliant) / COUNT(*)) AS risk_rank
FROM contingent_workers
GROUP BY business_unit
ORDER BY risk_rank;

-- name: contracts_expiring
-- Vendor contracts ending in the next 90 days that still have non-compliant workers.
-- Report date is fixed so results are reproducible.
SELECT
    v.vendor_name,
    v.contract_end_date,
    SUM(1 - w.is_compliant) AS non_compliant_workers
FROM vendors v
JOIN contingent_workers w ON w.vendor_id = v.vendor_id
WHERE v.contract_end_date BETWEEN '2026-01-01' AND DATE('2026-01-01', '+90 days')
GROUP BY v.vendor_name, v.contract_end_date
HAVING SUM(1 - w.is_compliant) > 0
ORDER BY v.contract_end_date;
