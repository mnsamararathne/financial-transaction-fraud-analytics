# Data Warehouse Design

## Financial Transaction Fraud Analytics

## 1. Warehouse Objective

The warehouse layer transforms validated staging data into a
dimensional model designed for analytical querying, fraud analysis,
machine learning feature engineering, and business intelligence.

The model follows a star-schema-oriented design with transaction
records stored in a central fact table and descriptive entities stored
in dimension tables.

---

## 2. Grain

The grain of the fact table is:

> One row represents one financial transaction.

Each transaction contains an origin account, destination account,
transaction type, simulation time step, monetary values, and fraud
indicators.

---

## 3. Fact Table

### warehouse.fact_transactions

The central fact table stores transaction-level measures and foreign
keys to analytical dimensions.

Fields:

- transaction_id
- time_key
- transaction_type_key
- origin_account_key
- destination_account_key
- amount
- origin_old_balance
- origin_new_balance
- destination_old_balance
- destination_new_balance
- is_fraud
- is_flagged_fraud

---

## 4. Account Dimension

### warehouse.dim_account

Stores unique financial accounts appearing as either origin or
destination accounts.

Fields:

- account_key
- account_id
- account_type

Account type is derived from the identifier prefix:

- C = Customer
- M = Merchant

The account dimension acts as a role-playing dimension in the fact
table through:

- origin_account_key
- destination_account_key

---

## 5. Transaction Type Dimension

### warehouse.dim_transaction_type

Stores the five transaction categories represented in the dataset:

- CASH_IN
- CASH_OUT
- DEBIT
- PAYMENT
- TRANSFER

Fields:

- transaction_type_key
- transaction_type

---

## 6. Time Dimension

### warehouse.dim_time

The PaySim dataset represents time using sequential simulation steps.

Fields:

- time_key
- step
- simulated_day
- simulated_hour

The derived time attributes will support temporal transaction and
fraud analysis.

---

## 7. Relationships

dim_time
    1 → many fact_transactions

dim_transaction_type
    1 → many fact_transactions

dim_account
    1 → many fact_transactions (origin)

dim_account
    1 → many fact_transactions (destination)

---

## 8. Analytical Purpose

The warehouse supports:

- Transaction volume analysis
- Transaction value analysis
- Fraud rate analysis
- Fraud analysis by transaction type
- Account-level transaction behaviour
- Origin and destination account analysis
- Temporal fraud analysis
- Transaction velocity analysis
- Feature engineering for machine learning
- Power BI reporting and dashboard development
