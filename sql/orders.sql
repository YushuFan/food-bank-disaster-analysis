-- Exactly one row per source order; fail validation before executing if keys
-- are duplicated or lines within an order have inconsistent acceptance dates.
-- Quantity is a selection criterion, NOT a comparable physical-volume measure.
DROP TABLE IF EXISTS analytical_orders;
CREATE TABLE analytical_orders AS
WITH per_order AS (
    SELECT headerid,
           MIN(ISO_DATE(accepteddate)) AS accepted_date,
           SUM(CASE WHEN ISO_DATE(accepteddate) IS NOT NULL THEN 1 ELSE 0 END) AS dated_lines,
           SUM(CASE WHEN ISO_DATE(accepteddate) IS NOT NULL
                     AND SAFE_NUMBER(acceptedquantity) > 0 THEN 1 ELSE 0 END) AS positive_lines
    FROM lines
    GROUP BY headerid
)
SELECT p.*, h.sourceorg,
       ISO_DATE(h.createddate) AS created_date,
       CASE WHEN p.accepted_date < ISO_DATE(h.createddate) THEN 1 ELSE 0 END AS date_anomaly
FROM per_order p
JOIN headers h ON p.headerid = h.documentid;
CREATE INDEX analytical_order_date ON analytical_orders(accepted_date);
