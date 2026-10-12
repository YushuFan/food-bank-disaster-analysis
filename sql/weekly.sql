-- Monday-start weeks; one order cannot appear in multiple weeks.
-- Missing dates stay outside the aggregation and are reported by the audit.
SELECT date(accepted_date, '-' || ((CAST(strftime('%w', accepted_date) AS INTEGER) + 6) % 7) || ' days') AS week,
       COUNT(*) AS dated_orders,
       SUM(CASE WHEN positive_lines > 0 AND date_anomaly = 0 THEN 1 ELSE 0 END) AS positive_orders,
       SUM(CASE WHEN positive_lines > 0 THEN 1 ELSE 0 END) AS positive_orders_including_date_anomalies,
       SUM(CASE WHEN date_anomaly = 0 THEN positive_lines ELSE 0 END) AS positive_lines,
       SUM(dated_lines) AS dated_lines,
       COUNT(DISTINCT CASE WHEN positive_lines > 0 AND date_anomaly = 0 THEN sourceorg END) AS active_organizations,
       SUM(date_anomaly) AS anomalous_orders
FROM analytical_orders
WHERE accepted_date IS NOT NULL
GROUP BY week ORDER BY week;
