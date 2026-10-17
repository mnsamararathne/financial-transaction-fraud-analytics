
"""Explain the trained XGBoost fraud model using SHAP."""

from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = PROJECT_ROOT / "models" / "xgboost_comparison.joblib"
TRAIN_PATH = PROJECT_ROOT / "data" / "processed" / "train_model_data.csv"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "images"

# Keep the sample small to limit memory use.
BACKGROUND_SIZE = 200
EXPLANATION_SIZE = 1000
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "amount",
    "origin_old_balance",
    "destination_old_balance",
    "simulated_day",
    "simulated_hour",
]

CATEGORICAL_FEATURES = [
    "transaction_type",
    "origin_account_type",
    "destination_account_type",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "is_fraud"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading saved XGBoost pipeline...")
    pipeline = joblib.load(MODEL_PATH)
    preprocessor = pipeline.named_steps["preprocessing"]
    classifier = pipeline.named_steps["classifier"]

    print("Loading a sample of training data...")
    data = pd.read_csv(TRAIN_PATH)

    missing = set(FEATURES + [TARGET]) - set(data.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")

    rng = np.random.default_rng(RANDOM_STATE)

    background_size = min(BACKGROUND_SIZE, len(data))
    explanation_size = min(EXPLANATION_SIZE, len(data))

    background_data = data.sample(
        n=background_size,
        random_state=RANDOM_STATE,
    )
    explanation_data = data.sample(
        n=explanation_size,
        random_state=RANDOM_STATE + 1,
    )

    X_background = background_data[FEATURES]
    X_explanation = explanation_data[FEATURES]

    print("Transforming features...")
    background_transformed = preprocessor.transform(X_background)
    explanation_transformed = preprocessor.transform(X_explanation)

    if hasattr(background_transformed, "toarray"):
        background_transformed = background_transformed.toarray()

    if hasattr(explanation_transformed, "toarray"):
        explanation_transformed = explanation_transformed.toarray()

    feature_names = preprocessor.get_feature_names_out()

    X_explanation_transformed = pd.DataFrame(
        explanation_transformed,
        columns=feature_names,
    )

    print("Calculating SHAP values...")
    explainer = shap.TreeExplainer(
    classifier,
    feature_perturbation="tree_path_dependent",
    )

    shap_values = explainer.shap_values(
        X_explanation_transformed,
        check_additivity=False,
    )

    # Handle different SHAP output formats for binary classification.
    if isinstance(shap_values, list):
        shap_values = shap_values[-1]
    elif getattr(shap_values, "ndim", 0) == 3:
        shap_values = shap_values[:, :, 1]

    print("Creating SHAP summary plot...")
    summary_path = OUTPUT_DIR / "xgboost_shap_summary.png"

    shap.summary_plot(
        shap_values,
        X_explanation_transformed,
        show=False,
        max_display=13,
    )
    plt.tight_layout()
    plt.savefig(summary_path, dpi=200, bbox_inches="tight")
    plt.close()

    print("Calculating mean absolute SHAP importance...")
    importance = pd.DataFrame({
        "feature": feature_names,
        "mean_absolute_shap": np.abs(shap_values).mean(axis=0),
    }).sort_values("mean_absolute_shap", ascending=False)

    importance_path = (
        PROJECT_ROOT / "docs" / "xgboost_shap_feature_importance.csv"
    )
    report_path = (
        PROJECT_ROOT / "docs" / "xgboost_shap_feature_importance.txt"
    )

    importance.to_csv(importance_path, index=False)

    with open(report_path, "w", encoding="utf-8") as report:
        report.write("XGBoost SHAP Feature Importance\n")
        report.write("=" * 38 + "\n\n")
        report.write(
            "Importance is the mean absolute SHAP value across the "
            "explanation sample.\n"
        )
        report.write(
            "Values explain contributions to the model's raw output "
            "(log-odds), not direct causal effects.\n\n"
        )
        report.write(importance.to_string(index=False))
        report.write("\n")

    print("\nTop SHAP features:")
    print(importance.head(10).to_string(index=False))

    print("\nSHAP analysis completed.")
    print(f"Summary plot: {summary_path}")
    print(f"Importance table: {importance_path}")
    print(f"Text report: {report_path}")


if __name__ == "__main__":
    main()

