-- ============================================================
-- Financial Transaction Fraud Analytics
-- Raw Transaction Table
-- ============================================================

CREATE TABLE IF NOT EXISTS raw.transactions (

    step INTEGER,

    type VARCHAR(20),

    amount NUMERIC(20, 2),

    nameOrig VARCHAR(20),

    oldbalanceOrg NUMERIC(20, 2),

    newbalanceOrig NUMERIC(20, 2),

    nameDest VARCHAR(20),

    oldbalanceDest NUMERIC(20, 2),

    newbalanceDest NUMERIC(20, 2),

    isFraud INTEGER,

    isFlaggedFraud INTEGER
);
