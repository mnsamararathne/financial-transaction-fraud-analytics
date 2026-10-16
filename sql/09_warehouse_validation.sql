-- ============================================================
-- Financial Transaction Fraud Analytics
-- 09 - Warehouse Validation
-- ============================================================
-- Purpose:
-- Validate warehouse completeness, dimensional relationships,
-- referential integrity, and reconciliation with staging.
-- ============================================================


-- ============================================================
-- 1. STAGING VS FACT ROW COUNT
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM staging.transactions) AS staging_count,
    (SELECT COUNT(*) FROM warehouse.fact_transactions) AS fact_count,
    (SELECT COUNT(*) FROM staging.transactions)
        - (SELECT COUNT(*) FROM warehouse.fact_transactions)
        AS difference;


-- ============================================================
-- 2. TRANSACTION ID VALIDATION
-- ============================================================

SELECT
    COUNT(*) AS total_fact_rows,
    COUNT(DISTINCT transaction_id) AS unique_transaction_ids,
    COUNT(*) - COUNT(DISTINCT transaction_id)
        AS duplicate_transaction_ids
FROM warehouse.fact_transactions;


-- ============================================================
-- 3. DIMENSION COUNTS
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM warehouse.dim_transaction_type)
        AS transaction_types,

    (SELECT COUNT(*)
     FROM warehouse.dim_time)
        AS time_records,

    (SELECT COUNT(*)
     FROM warehouse.dim_account)
        AS accounts;


-- ============================================================
-- 4. ACCOUNT TYPE DISTRIBUTION
-- ============================================================

SELECT
    account_type,
    COUNT(*) AS account_count
FROM warehouse.dim_account
GROUP BY account_type
ORDER BY account_type;


-- ============================================================
-- 5. TRANSACTION TYPE RECONCILIATION
-- ============================================================

SELECT
    dtt.transaction_type,
    COUNT(*) AS warehouse_count
FROM warehouse.fact_transactions f
JOIN warehouse.dim_transaction_type dtt
    ON f.transaction_type_key = dtt.transaction_type_key
GROUP BY dtt.transaction_type
ORDER BY warehouse_count DESC;


-- ============================================================
-- 6. FRAUD RECONCILIATION
-- ============================================================

SELECT
    is_fraud,
    COUNT(*) AS transaction_count
FROM warehouse.fact_transactions
GROUP BY is_fraud
ORDER BY is_fraud;


-- ============================================================
-- 7. FLAGGED FRAUD RECONCILIATION
-- ============================================================

SELECT
    is_flagged_fraud,
    COUNT(*) AS transaction_count
FROM warehouse.fact_transactions
GROUP BY is_flagged_fraud
ORDER BY is_flagged_fraud;


-- ============================================================
-- 8. TIME DIMENSION VALIDATION
-- ============================================================

SELECT
    MIN(step) AS minimum_step,
    MAX(step) AS maximum_step,
    COUNT(*) AS time_records,
    MIN(simulated_day) AS minimum_day,
    MAX(simulated_day) AS maximum_day,
    MIN(simulated_hour) AS minimum_hour,
    MAX(simulated_hour) AS maximum_hour
FROM warehouse.dim_time;


-- ============================================================
-- 9. CHECK FOR ORPHANED DIMENSION KEYS
-- ============================================================

SELECT
    COUNT(*) FILTER (
        WHERE dt.time_key IS NULL
    ) AS missing_time_dimension,

    COUNT(*) FILTER (
        WHERE dtt.transaction_type_key IS NULL
    ) AS missing_transaction_type_dimension,

    COUNT(*) FILTER (
        WHERE oa.account_key IS NULL
    ) AS missing_origin_account,

    COUNT(*) FILTER (
        WHERE da.account_key IS NULL
    ) AS missing_destination_account

FROM warehouse.fact_transactions f

LEFT JOIN warehouse.dim_time dt
    ON f.time_key = dt.time_key

LEFT JOIN warehouse.dim_transaction_type dtt
    ON f.transaction_type_key = dtt.transaction_type_key

LEFT JOIN warehouse.dim_account oa
    ON f.origin_account_key = oa.account_key

LEFT JOIN warehouse.dim_account da
    ON f.destination_account_key = da.account_key;


-- ============================================================
-- 10. AMOUNT RECONCILIATION
-- ============================================================

SELECT
    (SELECT SUM(amount)
     FROM staging.transactions) AS staging_total_amount,

    (SELECT SUM(amount)
     FROM warehouse.fact_transactions) AS warehouse_total_amount,

    (SELECT SUM(amount)
     FROM staging.transactions)
        -
    (SELECT SUM(amount)
     FROM warehouse.fact_transactions) AS difference;


-- ============================================================
-- 11. SAMPLE RECONSTRUCTED TRANSACTIONS
-- ============================================================

SELECT
    f.transaction_id,
    dt.step,
    dt.simulated_day,
    dt.simulated_hour,
    dtt.transaction_type,
    oa.account_id AS origin_account,
    da.account_id AS destination_account,
    f.amount,
    f.is_fraud,
    f.is_flagged_fraud

FROM warehouse.fact_transactions f

JOIN warehouse.dim_time dt
    ON f.time_key = dt.time_key

JOIN warehouse.dim_transaction_type dtt
    ON f.transaction_type_key = dtt.transaction_type_key

JOIN warehouse.dim_account oa
    ON f.origin_account_key = oa.account_key

JOIN warehouse.dim_account da
    ON f.destination_account_key = da.account_key

ORDER BY f.transaction_id

LIMIT 10;


-- ============================================================
-- END OF WAREHOUSE VALIDATION
-- ============================================================
