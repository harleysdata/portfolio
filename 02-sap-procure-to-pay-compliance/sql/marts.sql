-- Reporting layer for the purchase-to-pay analysis. Reads fct_po_line (one row per PO line item).

-- Control exceptions: how often each control fails, and how much PO value is involved
DROP VIEW IF EXISTS mart_control_exceptions;
CREATE VIEW mart_control_exceptions AS
WITH base AS (
    SELECT 'After-the-fact PO (invoice dated before PO)'  AS control, ctl_after_the_fact_po          AS hit, po_value_eur, flow FROM fct_po_line UNION ALL
    SELECT 'Paid with no goods receipt first',             ctl_paid_without_gr,            po_value_eur, flow FROM fct_po_line UNION ALL
    SELECT 'Same person raised PO and received goods',     ctl_sod_conflict,               po_value_eur, flow FROM fct_po_line UNION ALL
    SELECT 'Price changed after invoice recorded',         ctl_price_change_after_invoice, po_value_eur, flow FROM fct_po_line UNION ALL
    SELECT 'Invoice posted before goods receipt (allowed in this flow)', ctl_invoice_before_gr,          po_value_eur, flow FROM fct_po_line UNION ALL
    SELECT 'Invoice hit a payment block',                  ctl_payment_block,              po_value_eur, flow FROM fct_po_line
)
SELECT control,
       SUM(hit)                                         AS po_lines,
       ROUND(100.0 * AVG(hit), 2)                       AS pct_of_lines,
       ROUND(SUM(CASE WHEN hit = 1 THEN po_value_eur END) / 1e6, 1) AS po_value_eur_m
FROM base
GROUP BY control
ORDER BY po_lines DESC;

-- Volume and control profile of each matching flow (how SAP is configured to check the invoice)
DROP VIEW IF EXISTS mart_flow_profile;
CREATE VIEW mart_flow_profile AS
SELECT flow,
       COUNT(*)                                        AS po_lines,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_lines,
       ROUND(SUM(po_value_eur) / 1e6, 1)               AS po_value_eur_m,
       ROUND(100.0 * AVG(cleared_at IS NOT NULL), 1)   AS pct_paid,
       ROUND(100.0 * AVG(ctl_payment_block), 1)        AS pct_payment_block,
       ROUND(AVG(rework_events), 2)                    AS rework_per_line
FROM fct_po_line
GROUP BY flow
ORDER BY po_lines DESC;

-- Monthly trend of the two highest-risk controls
DROP VIEW IF EXISTS mart_monthly_controls;
CREATE VIEW mart_monthly_controls AS
SELECT po_month,
       COUNT(*)                                       AS po_lines,
       ROUND(100.0 * AVG(ctl_after_the_fact_po), 2)   AS pct_after_the_fact,
       ROUND(100.0 * AVG(ctl_payment_block), 2)       AS pct_payment_block
FROM fct_po_line
WHERE po_month BETWEEN '2018-01' AND '2018-12'
GROUP BY po_month
ORDER BY po_month;

-- Vendor risk scorecard. Each rate is turned into a percentile against peer vendors,
-- then weighted: controls that can lose money directly count three times as much as rework.
DROP VIEW IF EXISTS mart_vendor_risk;
CREATE VIEW mart_vendor_risk AS
WITH v AS (
    SELECT vendor,
           COUNT(*)                                AS po_lines,
           SUM(po_value_eur)                       AS spend_eur,
           AVG(ctl_after_the_fact_po)              AS r_after_the_fact,
           AVG(ctl_paid_without_gr)                AS r_paid_without_gr,
           AVG(ctl_price_change_after_invoice)     AS r_price_change,
           AVG(ctl_payment_block)                  AS r_payment_block,
           AVG(ctl_sod_conflict)                   AS r_sod,
           AVG(rework_events)                      AS r_rework
    FROM fct_po_line
    GROUP BY vendor
    HAVING COUNT(*) >= 100
), ranked AS (
    SELECT v.*,
           PERCENT_RANK() OVER (ORDER BY r_after_the_fact)  AS p_after_the_fact,
           PERCENT_RANK() OVER (ORDER BY r_paid_without_gr) AS p_paid_without_gr,
           PERCENT_RANK() OVER (ORDER BY r_price_change)    AS p_price_change,
           PERCENT_RANK() OVER (ORDER BY r_payment_block)   AS p_payment_block,
           PERCENT_RANK() OVER (ORDER BY r_sod)             AS p_sod,
           PERCENT_RANK() OVER (ORDER BY r_rework)          AS p_rework
    FROM v
), scored AS (
    SELECT *,
           ROUND(100 * (3 * p_after_the_fact + 3 * p_paid_without_gr + 2 * p_price_change
                        + 2 * p_sod + 1 * p_payment_block + 1 * p_rework) / 12, 1) AS risk_score
    FROM ranked
)
SELECT vendor, po_lines,
       ROUND(spend_eur / 1e6, 2)                AS spend_eur_m,
       ROUND(100 * r_after_the_fact, 1)         AS pct_after_the_fact,
       ROUND(100 * r_paid_without_gr, 2)        AS pct_paid_without_gr,
       ROUND(100 * r_price_change, 1)           AS pct_price_change,
       ROUND(100 * r_payment_block, 1)          AS pct_payment_block,
       ROUND(100 * r_sod, 1)                    AS pct_sod,
       ROUND(r_rework, 2)                       AS rework_per_line,
       risk_score,
       CASE WHEN risk_score >= 70 THEN 'High'
            WHEN risk_score >= 45 THEN 'Medium'
            ELSE 'Low' END                      AS risk_tier
FROM scored
ORDER BY risk_score DESC;

DROP VIEW IF EXISTS mart_risk_tier_summary;
CREATE VIEW mart_risk_tier_summary AS
SELECT risk_tier,
       COUNT(*)                         AS vendors,
       SUM(po_lines)                    AS po_lines,
       ROUND(SUM(spend_eur_m), 1)       AS spend_eur_m,
       ROUND(100.0 * SUM(spend_eur_m) / SUM(SUM(spend_eur_m)) OVER (), 1) AS pct_of_scored_spend
FROM mart_vendor_risk
GROUP BY risk_tier
ORDER BY MIN(-risk_score);
