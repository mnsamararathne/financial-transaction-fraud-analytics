# XGBoost Fraud Detection — SHAP Explainability

## 1. Objective

SHAP (SHapley Additive exPlanations) was used to examine how the trained XGBoost model uses transaction characteristics when predicting potential fraud. The objective is to improve model transparency and support interpretation of the model's behaviour.

## 2. Methodology

- **Model:** Previously trained XGBoost classification pipeline.
- **Explainer:** SHAP TreeExplainer.
- **Feature representation:** Preprocessed numerical and one-hot-encoded categorical features.
- **Explanation sample:** 1,000 training records.
- **SHAP background:** Tree-path-dependent approach.
- **Global importance:** Mean absolute SHAP value across the explanation sample.
- **Visualisation:** SHAP summary beeswarm plot.

SHAP values explain contributions to the model's raw output (log-odds) rather than direct causal effects.

## 3. Key Findings

The highest mean absolute SHAP values in the current explanation sample were:

| Feature | Mean absolute SHAP |
|---|---:|
| Origin old balance | 1.712031 |
| Transaction amount | 1.606910 |
| Transaction type: PAYMENT | 1.334196 |
| Transaction type: CASH_IN | 0.871870 |
| Transaction type: CASH_OUT | 0.652873 |
| Destination old balance | 0.624560 |
| Simulated day | 0.403940 |
| Simulated hour | 0.332492 |
| Transaction type: TRANSFER | 0.329139 |
| Destination account: CUSTOMER | 0.161046 |

Origin balance and transaction amount had the largest average absolute contributions in this sample. Transaction type indicators also influenced model predictions.

The origin account type indicator had zero importance because all origin accounts in this dataset are classified as customers, leaving no variation for the model to use.

## 4. Interpretation

In the summary plot, positive SHAP values increase the model's raw output, moving it towards a fraud prediction. Negative values decrease that output. For numerical features, colour represents the feature value; for one-hot-encoded categorical features, it represents whether the category is present or absent.

A feature's global importance indicates the magnitude of its contributions, not whether it consistently increases fraud risk. Individual predictions can be influenced differently depending on other feature values.

## 5. Limitations

- PaySim is a synthetic financial transaction dataset. Results do not establish that the same relationships will occur in real banking systems.
- SHAP values describe model behaviour, not causal relationships.
- The explanation is based on a sample of 1,000 training records rather than every transaction.
- Correlated features and the chosen SHAP reference approach can affect the allocation of feature contributions.
- The model's performance should be assessed further using temporal validation and realistic operational assumptions before any real-world deployment.

## 6. Outputs

- `docs/images/xgboost_shap_summary.png` — SHAP summary beeswarm plot.
- `docs/xgboost_shap_feature_importance.csv` — numerical feature-importance results.
- `docs/xgboost_shap_feature_importance.txt` — text report of feature rankings.
- `src/explain_xgboost_shap.py` — reproducible analysis script.

## 7. Conclusion

SHAP provides a global view of how the XGBoost model uses transaction amounts, account balances, transaction types, and simulated time features. This improves interpretability, but the results should be treated as explanations of a model trained on synthetic data, not evidence of causal fraud indicators or proven real-world effectiveness.
