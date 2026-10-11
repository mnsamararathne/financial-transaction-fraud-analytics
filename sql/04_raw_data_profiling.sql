-- ============================================================
-- Financial Transaction Fraud Analytics
-- 04 - Raw Data Profiling
-- ============================================================
-- Purpose:
-- Assess the structure, completeness, validity and basic
-- characteristics of the PaySim dataset after ingestion
-- into PostgreSQL.
--
-- IMPORTANT:
-- This script performs profiling only.
-- It does not modify or delete raw data.
-- ============================================================


-- ============================================================
-- 1. TOTAL RECORD COUNT
-- ============================================================

SELECT
    COUNT(*) AS total_transactions
FROM raw.transactions;


-- ============================================================
-- 2. SAMPLE RECORDS
-- ============================================================

SELECT *
FROM raw.transactions
LIMIT 10;


-- ============================================================
-- 3. TRANSACTION TYPE DISTRIBUTION
-- ============================================================

SELECT
    type,
    COUNT(*) AS transaction_count,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage

FROM raw.transactions

GROUP BY type

ORDER BY transaction_count DESC;


-- ============================================================
-- 4. FRAUD CLASS DISTRIBUTION
-- ============================================================

SELECT
    isfraud,
    COUNT(*) AS transaction_count,

    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        4
    ) AS percentage

FROM raw.transactions

GROUP BY isfraud

ORDER BY isfraud;


-- ============================================================
-- 5. NULL VALUE ANALYSIS
-- ============================================================

SELECT
    COUNT(*) AS total_rows,

    COUNT(*) FILTER (
        WHERE step IS NULL
    ) AS null_step,

    COUNT(*) FILTER (
        WHERE type IS NULL
    ) AS null_type,

    COUNT(*) FILTER (
        WHERE amount IS NULL
    ) AS null_amount,

    COUNT(*) FILTER (
        WHERE nameorig IS NULL
    ) AS null_nameorig,

    COUNT(*) FILTER (
        WHERE oldbalanceorg IS NULL
    ) AS null_oldbalanceorg,

    COUNT(*) FILTER (
        WHERE newbalanceorig IS NULL
    ) AS null_newbalanceorig,

    COUNT(*) FILTER (
        WHERE namedest IS NULL
    ) AS null_namedest,

    COUNT(*) FILTER (
        WHERE oldbalancedest IS NULL
    ) AS null_oldbalancedest,

    COUNT(*) FILTER (
        WHERE newbalancedest IS NULL
    ) AS null_newbalancedest,

    COUNT(*) FILTER (
        WHERE isfraud IS NULL
    ) AS null_isfraud,

    COUNT(*) FILTER (
        WHERE isflaggedfraud IS NULL
    ) AS null_isflaggedfraud

FROM raw.transactions;


-- ============================================================
-- 6. COMPLETE DUPLICATE ROW ANALYSIS
-- ============================================================

SELECT
    COUNT(*) - COUNT(
        DISTINCT (
            step,
            type,
            amount,
            nameorig,
            oldbalanceorg,
            newbalanceorig,
            namedest,
            oldbalancedest,
            newbalancedest,
            isfraud,
            isflaggedfraud
        )
    ) AS duplicate_rows

FROM raw.transactions;


-- ============================================================
-- 7. CARDINALITY ANALYSIS
-- ============================================================

SELECT
    COUNT(DISTINCT step)
        AS unique_steps,

    COUNT(DISTINCT type)
        AS unique_transaction_types,

    COUNT(DISTINCT nameorig)
        AS unique_origin_accounts,

    COUNT(DISTINCT namedest)
        AS unique_destination_accounts

FROM raw.transactions;


-- ============================================================
-- 8. STEP / TIME RANGE
-- ============================================================

SELECT
    MIN(step) AS minimum_step,
    MAX(step) AS maximum_step,
    COUNT(DISTINCT step) AS unique_steps

FROM raw.transactions;


-- ============================================================
-- 9. TRANSACTION AMOUNT STATISTICS
-- ============================================================

SELECT
    MIN(amount) AS minimum_amount,

    MAX(amount) AS maximum_amount,

    ROUND(
        AVG(amount),
        2
    ) AS average_amount,

    ROUND(
        PERCENTILE_CONT(0.5)
        WITHIN GROUP (ORDER BY amount)::NUMERIC,
        2
    ) AS median_amount

FROM raw.transactions;


-- ============================================================
-- 10. ZERO AND NEGATIVE VALUE CHECKS
-- ============================================================

SELECT

    COUNT(*) FILTER (
        WHERE amount < 0
    ) AS negative_amounts,

    COUNT(*) FILTER (
        WHERE amount = 0
    ) AS zero_amounts,

    COUNT(*) FILTER (
        WHERE oldbalanceorg < 0
    ) AS negative_origin_old_balance,

    COUNT(*) FILTER (
        WHERE newbalanceorig < 0
    ) AS negative_origin_new_balance,

    COUNT(*) FILTER (
        WHERE oldbalancedest < 0
    ) AS negative_destination_old_balance,

    COUNT(*) FILTER (
        WHERE newbalancedest < 0
    ) AS negative_destination_new_balance

FROM raw.transactions;


-- ============================================================
-- 11. TRANSACTION TYPE DOMAIN
-- ============================================================

SELECT DISTINCT
    type

FROM raw.transactions

ORDER BY type;


-- ============================================================
-- 12. INVALID TRANSACTION TYPE CHECK
-- ============================================================

SELECT
    COUNT(*) AS invalid_transaction_types

FROM raw.transactions

WHERE
    type NOT IN (
        'CASH_IN',
        'CASH_OUT',
        'DEBIT',
        'PAYMENT',
        'TRANSFER'
    )
    OR type IS NULL;


-- ============================================================
-- 13. FRAUD FLAG DOMAIN
-- ============================================================

SELECT DISTINCT
    isfraud

FROM raw.transactions

ORDER BY isfraud;


-- ============================================================
-- 14. FLAGGED FRAUD DOMAIN
-- ============================================================

SELECT DISTINCT
    isflaggedfraud

FROM raw.transactions

ORDER BY isflaggedfraud;


-- ============================================================
-- 15. INVALID FRAUD FLAG CHECK
-- ============================================================

SELECT

    COUNT(*) FILTER (
        WHERE isfraud NOT IN (0, 1)
        OR isfraud IS NULL
    ) AS invalid_isfraud,

    COUNT(*) FILTER (
        WHERE isflaggedfraud NOT IN (0, 1)
        OR isflaggedfraud IS NULL
    ) AS invalid_isflaggedfraud

FROM raw.transactions;


-- ============================================================
-- 16. FRAUD BY TRANSACTION TYPE
-- ============================================================

SELECT
    type,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (
        WHERE isfraud = 1
    ) AS fraudulent_transactions,

    ROUND(
        COUNT(*) FILTER (
            WHERE isfraud = 1
        ) * 100.0 / COUNT(*),
        4
    ) AS fraud_rate_percentage

FROM raw.transactions

GROUP BY type

ORDER BY fraud_rate_percentage DESC;


-- ============================================================
-- 17. SYSTEM-FLAGGED FRAUD ANALYSIS
-- ============================================================

SELECT
    isflaggedfraud,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (
        WHERE isfraud = 1
    ) AS actual_fraud_transactions

FROM raw.transactions

GROUP BY isflaggedfraud

ORDER BY isflaggedfraud;


-- ============================================================
-- 18. FRAUD VS SYSTEM FLAG CROSS-TABULATION
-- ============================================================

SELECT
    isfraud,
    isflaggedfraud,
    COUNT(*) AS transaction_count

FROM raw.transactions

GROUP BY
    isfraud,
    isflaggedfraud

ORDER BY
    isfraud,
    isflaggedfraud;


-- ============================================================
-- 19. ACCOUNT IDENTIFIER PREFIX ANALYSIS
-- ============================================================

SELECT
    LEFT(nameorig, 1) AS origin_prefix,
    COUNT(*) AS transaction_count

FROM raw.transactions

GROUP BY LEFT(nameorig, 1)

ORDER BY transaction_count DESC;


SELECT
    LEFT(namedest, 1) AS destination_prefix,
    COUNT(*) AS transaction_count

FROM raw.transactions

GROUP BY LEFT(namedest, 1)

ORDER BY transaction_count DESC;


-- ============================================================
-- END OF RAW DATA PROFILING
-- ============================================================
