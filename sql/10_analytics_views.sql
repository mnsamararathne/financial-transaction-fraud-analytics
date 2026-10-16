
-- 10_analytics_views.sql
-- Business-focused analytics views for fraud investigation.

-- 1. Overall fraud and transaction summary
CREATE OR REPLACE VIEW analytics.v_fraud_overview AS
SELECT
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE is_fraud) AS fraud_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_fraud)
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate_percentage,
    COUNT(*) FILTER (WHERE is_flagged_fraud)
        AS flagged_transactions,
    COUNT(*) FILTER (
        WHERE is_fraud AND is_flagged_fraud
    ) AS fraud_transactions_flagged,
    COUNT(*) FILTER (
        WHERE is_fraud AND NOT is_flagged_fraud
    ) AS fraud_transactions_not_flagged,
    SUM(amount) AS total_transaction_value,
    SUM(amount) FILTER (WHERE is_fraud)
        AS fraudulent_transaction_value
FROM warehouse.fact_transactions;


-- 2. Fraud analysis by transaction type
CREATE OR REPLACE VIEW analytics.v_fraud_by_type AS
SELECT
    dtt.transaction_type,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE f.is_fraud)
        AS fraud_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE f.is_fraud)
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate_percentage,
    SUM(f.amount) AS total_transaction_value,
    SUM(f.amount) FILTER (WHERE f.is_fraud)
        AS fraudulent_transaction_value
FROM warehouse.fact_transactions AS f
JOIN warehouse.dim_transaction_type AS dtt
    ON f.transaction_type_key = dtt.transaction_type_key
GROUP BY dtt.transaction_type;


-- 3. Fraud analysis by simulated day
CREATE OR REPLACE VIEW analytics.v_fraud_by_day AS
SELECT
    dt.simulated_day,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE f.is_fraud)
        AS fraud_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE f.is_fraud)
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate_percentage,
    SUM(f.amount) AS total_transaction_value,
    SUM(f.amount) FILTER (WHERE f.is_fraud)
        AS fraudulent_transaction_value
FROM warehouse.fact_transactions AS f
JOIN warehouse.dim_time AS dt
    ON f.time_key = dt.time_key
GROUP BY dt.simulated_day;


-- 4. Fraud analysis by simulated hour
CREATE OR REPLACE VIEW analytics.v_fraud_by_hour AS
SELECT
    dt.simulated_hour,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE f.is_fraud)
        AS fraud_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE f.is_fraud)
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate_percentage,
    SUM(f.amount) FILTER (WHERE f.is_fraud)
        AS fraudulent_transaction_value
FROM warehouse.fact_transactions AS f
JOIN warehouse.dim_time AS dt
    ON f.time_key = dt.time_key
GROUP BY dt.simulated_hour;


-- 5. Fraud analysis by transaction amount band
CREATE OR REPLACE VIEW analytics.v_fraud_by_amount_band AS
SELECT
    amount_band,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (WHERE is_fraud)
        AS fraud_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_fraud)
        / NULLIF(COUNT(*), 0),
        4
    ) AS fraud_rate_percentage,
    SUM(amount) AS total_transaction_value,
    SUM(amount) FILTER (WHERE is_fraud)
        AS fraudulent_transaction_value
FROM (
    SELECT
        amount,
        is_fraud,
        CASE
            WHEN amount < 1000 THEN 'Under 1,000'
            WHEN amount < 10000 THEN '1,000–9,999.99'
            WHEN amount < 100000 THEN '10,000–99,999.99'
            WHEN amount < 1000000 THEN '100,000–999,999.99'
            ELSE '1,000,000 and above'
        END AS amount_band,
        CASE
            WHEN amount < 1000 THEN 1
            WHEN amount < 10000 THEN 2
            WHEN amount < 100000 THEN 3
            WHEN amount < 1000000 THEN 4
            ELSE 5
        END AS band_order
    FROM warehouse.fact_transactions
) AS transactions
GROUP BY amount_band, band_order;

