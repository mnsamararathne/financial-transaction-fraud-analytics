# PaySim Dataset – Data Dictionary

## Dataset Overview

- Dataset: PaySim Synthetic Financial Dataset
- Domain: Financial Transactions / Fraud Detection
- Grain: One row represents one financial transaction
- Target Variable: isFraud
- Source Format: CSV

## Data Dictionary

| Column | Description | Expected Type | Analytical Role |
|---|---|---|---|
| step | Unit of simulated time | Integer | Time |
| type | Transaction type | Categorical | Dimension |
| amount | Transaction amount | Numeric | Measure |
| nameOrig | Originating customer/account | Text | Identifier |
| oldbalanceOrg | Origin balance before transaction | Numeric | Measure |
| newbalanceOrig | Origin balance after transaction | Numeric | Measure |
| nameDest | Destination customer/account | Text | Identifier |
| oldbalanceDest | Destination balance before transaction | Numeric | Measure |
| newbalanceDest | Destination balance after transaction | Numeric | Measure |
| isFraud | Indicates fraudulent transaction | Integer/Boolean | Target |
| isFlaggedFraud | Indicates transaction flagged by system | Integer/Boolean | Risk Indicator |
