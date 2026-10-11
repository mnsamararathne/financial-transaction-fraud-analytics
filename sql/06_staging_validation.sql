-- ============================================================
-- Financial Transaction Fraud Analytics
-- 06 - Staging Validation & Reconciliation
-- ============================================================
-- Purpose:
-- Validate that the staging transformation preserved the
-- source data correctly and investigate known anomalies.
-- ============================================================


-- ============================================================
-- 1. RAW VS STAGING ROW COUNT
-- ============================================================

SELECT
    (SELECT COUNT(*) FROM raw.transactions) AS raw_count,
    (SELECT COUNT(*) FROM staging.transactions) AS staging_count,
    (SELECT COUNT(*) FROM raw.transactions)
        - (SELECT COUNT(*) FROM staging.transactions) AS difference;


-- ============================================================
-- 2. RAW VS STAGING FRAUD COUNT
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM raw.transactions
     WHERE isfraud = 1) AS raw_fraud_count,

    (SELECT COUNT(*)
     FROM staging.transactions
     WHERE is_fraud = TRUE) AS staging_fraud_count;


-- ============================================================
-- 3. RAW VS STAGING FLAGGED FRAUD COUNT
-- ============================================================

SELECT
    (SELECT COUNT(*)
     FROM raw.transactions
     WHERE isflaggedfraud = 1) AS raw_flagged_count,

    (SELECT COUNT(*)
     FROM staging.transactions
     WHERE is_flagged_fraud = TRUE) AS staging_flagged_count;


-- ============================================================
-- 4. TRANSACTION TYPE RECONCILIATION
-- ============================================================

SELECT
    r.type,
    r.raw_count,
    s.staging_count,
    r.raw_count - s.staging_count AS difference

FROM (
    SELECT
        type,
        COUNT(*) AS raw_count
    FROM raw.transactions
    GROUP BY type
) r

JOIN (
    SELECT
        transaction_type,
        COUNT(*) AS staging_count
    FROM staging.transactions
    GROUP BY transaction_type
) s

ON r.type = s.transaction_type

ORDER BY r.type;


-- ============================================================
-- 5. NULL VALIDATION
-- ============================================================

SELECT
    COUNT(*) FILTER (WHERE step IS NULL) AS null_step,
    COUNT(*) FILTER (WHERE transaction_type IS NULL) AS null_type,
    COUNT(*) FILTER (WHERE amount IS NULL) AS null_amount,
    COUNT(*) FILTER (WHERE origin_account IS NULL) AS null_origin,
    COUNT(*) FILTER (WHERE destination_account IS NULL) AS null_destination,
    COUNT(*) FILTER (WHERE is_fraud IS NULL) AS null_fraud

FROM staging.transactions;


-- ============================================================
-- 6. ZERO-AMOUNT TRANSACTIONS
-- ============================================================

SELECT
    transaction_id,
    step,
    transaction_type,
    amount,
    origin_account,
    origin_old_balance,
    origin_new_balance,
    destination_account,
    destination_old_balance,
    destination_new_balance,
    is_fraud,
    is_flagged_fraud

FROM staging.transactions

WHERE amount = 0

ORDER BY transaction_id;


-- ============================================================
-- 7. ZERO-AMOUNT SUMMARY
-- ============================================================

SELECT
    transaction_type,
    is_fraud,
    COUNT(*) AS zero_amount_transactions

FROM staging.transactions

WHERE amount = 0

GROUP BY
    transaction_type,
    is_fraud

ORDER BY
    transaction_type,
    is_fraud;


-- ============================================================
-- 8. BALANCE DIFFERENCE FEATURES - DIAGNOSTIC ONLY
-- ============================================================

SELECT
    transaction_id,
    transaction_type,
    amount,

    origin_old_balance,
    origin_new_balance,

    origin_old_balance - origin_new_balance
        AS origin_balance_change,

    destination_old_balance,
    destination_new_balance,

    destination_new_balance - destination_old_balance
        AS destination_balance_change,

    is_fraud

FROM staging.transactions

LIMIT 20;


-- ============================================================
-- 9. BASIC STAGING INTEGRITY SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS total_transactions,

    COUNT(DISTINCT transaction_id)
        AS unique_transaction_ids,

    COUNT(DISTINCT origin_account)
        AS unique_origin_accounts,

    COUNT(DISTINCT destination_account)
        AS unique_destination_accounts,

    COUNT(*) FILTER (
        WHERE is_fraud
    ) AS fraud_transactions,

    COUNT(*) FILTER (
        WHERE is_flagged_fraud
    ) AS flagged_transactions

FROM staging.transactions;


-- ============================================================
-- END OF STAGING VALIDATION
-- ============================================================
