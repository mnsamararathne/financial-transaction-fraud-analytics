-- ============================================================
-- Financial Transaction Fraud Analytics
-- 08 - Warehouse Data Load
-- ============================================================
-- Purpose:
-- Populate warehouse dimensions and transaction fact table
-- from the validated staging layer.
-- ============================================================


-- ============================================================
-- 1. LOAD TRANSACTION TYPE DIMENSION
-- ============================================================

INSERT INTO warehouse.dim_transaction_type (
    transaction_type
)
SELECT DISTINCT
    transaction_type
FROM staging.transactions
ORDER BY transaction_type;


-- ============================================================
-- 2. LOAD TIME DIMENSION
-- ============================================================
-- PaySim step represents an hourly simulation step.
-- simulated_day starts at Day 1.
-- simulated_hour ranges from 0 to 23.
-- ============================================================

INSERT INTO warehouse.dim_time (
    step,
    simulated_day,
    simulated_hour
)
SELECT DISTINCT
    step,
    ((step - 1) / 24) + 1 AS simulated_day,
    (step - 1) % 24 AS simulated_hour
FROM staging.transactions
ORDER BY step;


-- ============================================================
-- 3. LOAD ACCOUNT DIMENSION
-- ============================================================
-- Accounts may appear as origin accounts, destination accounts,
-- or both. UNION removes duplicate account IDs.
--
-- Prefix classification:
-- C = CUSTOMER
-- M = MERCHANT
-- ============================================================

INSERT INTO warehouse.dim_account (
    account_id,
    account_type
)
SELECT
    account_id,

    CASE
        WHEN LEFT(account_id, 1) = 'C' THEN 'CUSTOMER'
        WHEN LEFT(account_id, 1) = 'M' THEN 'MERCHANT'
    END AS account_type

FROM (

    SELECT origin_account AS account_id
    FROM staging.transactions

    UNION

    SELECT destination_account AS account_id
    FROM staging.transactions

) accounts

WHERE LEFT(account_id, 1) IN ('C', 'M')

ORDER BY account_id;


-- ============================================================
-- 4. LOAD TRANSACTION FACT TABLE
-- ============================================================

INSERT INTO warehouse.fact_transactions (
    transaction_id,
    time_key,
    transaction_type_key,
    origin_account_key,
    destination_account_key,
    amount,
    origin_old_balance,
    origin_new_balance,
    destination_old_balance,
    destination_new_balance,
    is_fraud,
    is_flagged_fraud
)

SELECT
    s.transaction_id,

    dt.time_key,

    dtt.transaction_type_key,

    origin_acc.account_key,

    destination_acc.account_key,

    s.amount,
    s.origin_old_balance,
    s.origin_new_balance,
    s.destination_old_balance,
    s.destination_new_balance,
    s.is_fraud,
    s.is_flagged_fraud

FROM staging.transactions s

JOIN warehouse.dim_time dt
    ON s.step = dt.step

JOIN warehouse.dim_transaction_type dtt
    ON s.transaction_type = dtt.transaction_type

JOIN warehouse.dim_account origin_acc
    ON s.origin_account = origin_acc.account_id

JOIN warehouse.dim_account destination_acc
    ON s.destination_account = destination_acc.account_id;


-- ============================================================
-- 5. LOAD SUMMARY
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
        AS accounts,

    (SELECT COUNT(*)
     FROM warehouse.fact_transactions)
        AS transactions;


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
-- END OF WAREHOUSE LOAD
-- ============================================================
