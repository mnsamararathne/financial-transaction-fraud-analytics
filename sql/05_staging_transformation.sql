-- ============================================================
-- Financial Transaction Fraud Analytics
-- 05 - Staging Transformation
-- ============================================================
-- Purpose:
-- Transform the raw PaySim data into a standardized,
-- validated analytical staging table.
-- ============================================================


-- ============================================================
-- 1. DROP EXISTING STAGING TABLE
-- ============================================================

DROP TABLE IF EXISTS staging.transactions;


-- ============================================================
-- 2. CREATE STAGING TABLE
-- ============================================================

CREATE TABLE staging.transactions (

    transaction_id BIGSERIAL PRIMARY KEY,

    step INTEGER NOT NULL,

    transaction_type VARCHAR(20) NOT NULL,

    amount NUMERIC(20,2) NOT NULL,

    origin_account VARCHAR(20) NOT NULL,

    origin_old_balance NUMERIC(20,2) NOT NULL,

    origin_new_balance NUMERIC(20,2) NOT NULL,

    destination_account VARCHAR(20) NOT NULL,

    destination_old_balance NUMERIC(20,2) NOT NULL,

    destination_new_balance NUMERIC(20,2) NOT NULL,

    is_fraud BOOLEAN NOT NULL,

    is_flagged_fraud BOOLEAN NOT NULL,

    CONSTRAINT chk_transaction_type
        CHECK (
            transaction_type IN (
                'CASH_IN',
                'CASH_OUT',
                'DEBIT',
                'PAYMENT',
                'TRANSFER'
            )
        ),

    CONSTRAINT chk_amount_nonnegative
        CHECK (amount >= 0),

    CONSTRAINT chk_step_positive
        CHECK (step > 0)
);


-- ============================================================
-- 3. LOAD AND TRANSFORM RAW DATA
-- ============================================================

INSERT INTO staging.transactions (

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
)

SELECT

    step,

    UPPER(TRIM(type)),

    amount,

    TRIM(nameorig),

    oldbalanceorg,

    newbalanceorig,

    TRIM(namedest),

    oldbalancedest,

    newbalancedest,

    CASE
        WHEN isfraud = 1 THEN TRUE
        ELSE FALSE
    END,

    CASE
        WHEN isflaggedfraud = 1 THEN TRUE
        ELSE FALSE
    END

FROM raw.transactions;


-- ============================================================
-- 4. VALIDATE ROW COUNT
-- ============================================================

SELECT
    COUNT(*) AS staging_row_count
FROM staging.transactions;


-- ============================================================
-- 5. VALIDATE BOOLEAN TRANSFORMATION
-- ============================================================

SELECT
    is_fraud,
    COUNT(*) AS transaction_count
FROM staging.transactions
GROUP BY is_fraud
ORDER BY is_fraud;


SELECT
    is_flagged_fraud,
    COUNT(*) AS transaction_count
FROM staging.transactions
GROUP BY is_flagged_fraud
ORDER BY is_flagged_fraud;


-- ============================================================
-- 6. SAMPLE STAGING DATA
-- ============================================================

SELECT *
FROM staging.transactions
LIMIT 10;
