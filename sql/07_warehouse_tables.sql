-- ============================================================
-- Financial Transaction Fraud Analytics
-- 07 - Warehouse Table Creation
-- ============================================================
-- Purpose:
-- Create the dimensional data warehouse structure used for
-- analytical querying, fraud analysis, Power BI, and downstream
-- machine-learning feature engineering.
-- ============================================================


-- ============================================================
-- 1. TRANSACTION TYPE DIMENSION
-- ============================================================

DROP TABLE IF EXISTS warehouse.fact_transactions;
DROP TABLE IF EXISTS warehouse.dim_transaction_type;
DROP TABLE IF EXISTS warehouse.dim_time;
DROP TABLE IF EXISTS warehouse.dim_account;


CREATE TABLE warehouse.dim_transaction_type (

    transaction_type_key SMALLSERIAL PRIMARY KEY,

    transaction_type VARCHAR(20) NOT NULL UNIQUE,

    CONSTRAINT chk_dim_transaction_type
        CHECK (
            transaction_type IN (
                'CASH_IN',
                'CASH_OUT',
                'DEBIT',
                'PAYMENT',
                'TRANSFER'
            )
        )
);


-- ============================================================
-- 2. TIME DIMENSION
-- ============================================================

CREATE TABLE warehouse.dim_time (

    time_key SMALLSERIAL PRIMARY KEY,

    step INTEGER NOT NULL UNIQUE,

    simulated_day INTEGER NOT NULL,

    simulated_hour INTEGER NOT NULL,

    CONSTRAINT chk_time_step
        CHECK (step > 0),

    CONSTRAINT chk_simulated_day
        CHECK (simulated_day > 0),

    CONSTRAINT chk_simulated_hour
        CHECK (simulated_hour BETWEEN 0 AND 23)
);


-- ============================================================
-- 3. ACCOUNT DIMENSION
-- ============================================================

CREATE TABLE warehouse.dim_account (

    account_key BIGSERIAL PRIMARY KEY,

    account_id VARCHAR(20) NOT NULL UNIQUE,

    account_type VARCHAR(20) NOT NULL,

    CONSTRAINT chk_account_type
        CHECK (
            account_type IN (
                'CUSTOMER',
                'MERCHANT'
            )
        )
);


-- ============================================================
-- 4. TRANSACTION FACT TABLE
-- ============================================================

CREATE TABLE warehouse.fact_transactions (

    transaction_id BIGINT PRIMARY KEY,

    time_key SMALLINT NOT NULL,

    transaction_type_key SMALLINT NOT NULL,

    origin_account_key BIGINT NOT NULL,

    destination_account_key BIGINT NOT NULL,

    amount NUMERIC(20,2) NOT NULL,

    origin_old_balance NUMERIC(20,2) NOT NULL,

    origin_new_balance NUMERIC(20,2) NOT NULL,

    destination_old_balance NUMERIC(20,2) NOT NULL,

    destination_new_balance NUMERIC(20,2) NOT NULL,

    is_fraud BOOLEAN NOT NULL,

    is_flagged_fraud BOOLEAN NOT NULL,

    CONSTRAINT fk_fact_time
        FOREIGN KEY (time_key)
        REFERENCES warehouse.dim_time(time_key),

    CONSTRAINT fk_fact_transaction_type
        FOREIGN KEY (transaction_type_key)
        REFERENCES warehouse.dim_transaction_type(transaction_type_key),

    CONSTRAINT fk_fact_origin_account
        FOREIGN KEY (origin_account_key)
        REFERENCES warehouse.dim_account(account_key),

    CONSTRAINT fk_fact_destination_account
        FOREIGN KEY (destination_account_key)
        REFERENCES warehouse.dim_account(account_key),

    CONSTRAINT chk_fact_amount
        CHECK (amount >= 0),

    CONSTRAINT chk_origin_old_balance
        CHECK (origin_old_balance >= 0),

    CONSTRAINT chk_origin_new_balance
        CHECK (origin_new_balance >= 0),

    CONSTRAINT chk_destination_old_balance
        CHECK (destination_old_balance >= 0),

    CONSTRAINT chk_destination_new_balance
        CHECK (destination_new_balance >= 0)
);


-- ============================================================
-- END OF WAREHOUSE TABLE CREATION
-- ============================================================
