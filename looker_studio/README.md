# Google Looker Studio Dashboard

## Overview

This dashboard presents key findings from the financial transaction analytics and fraud detection project. It uses analytical datasets exported from PostgreSQL and connected through Google Sheets.

## Dashboard Components

### KPI Scorecards

- Total transactions
- Fraudulent transactions
- Fraud rate
- Fraudulent transaction value

### Charts

- Fraud transactions by transaction type
- Daily transaction and fraud trends
- Fraud transactions by simulated hour
- Fraud rate by transaction amount band

## Data Sources

The dashboard uses five analytical datasets generated from PostgreSQL views:

| Dataset | Purpose |
|---|---|
| `fraud_overview` | Overall transaction and fraud KPIs |
| `fraud_by_type` | Fraud patterns across transaction types |
| `fraud_by_day` | Daily transaction and fraud trends |
| `fraud_by_hour` | Fraud patterns by simulated hour |
| `fraud_by_amount_band` | Fraud rates across transaction amount bands |

## Data Preparation

The source data is processed through the project's PostgreSQL analytics pipeline. The resulting analytical views are exported as CSV files and connected to Google Sheets for use in Looker Studio.

The exported CSV files are excluded from Git version control because they are generated data files.

## Dashboard Preview

See the dashboard screenshot in [`docs/images/fraud_dashboard.png.png`](../images/fraud_dashboard.png.png) in the main repository.

## Interpretation Notes

- The underlying PaySim dataset is synthetic.
- Observed fraud patterns may reflect the dataset's simulation process rather than real financial behaviour.
- Fraud rates should be interpreted alongside transaction volumes.
- Transaction values are presented in the dataset's units; no real-world currency is assumed.

