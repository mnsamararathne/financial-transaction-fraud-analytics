
"""Train and evaluate a Random Forest fraud detection model."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "docs"

TARGET = "is_fraud"
TEST_CHUNK_SIZE = 100_000

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


def main():
    train_path = DATA / "train_model_data.csv"
    test_path = DATA / "test_model_data.csv"

    print("Loading training sample...")
    train_data = pd.read_csv(train_path)

    X_train = train_data[FEATURES]
    y_train = train_data[TARGET].astype(bool)

    del train_data

    preprocessing = ColumnTransformer([
        (
            "numeric",
            SimpleImputer(strategy="median"),
            NUMERIC_FEATURES,
        ),
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]),
            CATEGORICAL_FEATURES,
        ),
    ])

    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=16,
        min_samples_leaf=10,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=2,
    )

    model = Pipeline([
        ("preprocessing", preprocessing),
        ("classifier", classifier),
    ])

    print("Training Random Forest...")
    model.fit(X_train, y_train)

    print("Evaluating the full test set in chunks...")

    actual_parts = []
    probability_parts = []
    prediction_parts = []

    processed_rows = 0

    for chunk in pd.read_csv(
        test_path,
        chunksize=TEST_CHUNK_SIZE,
    ):
        X_chunk = chunk[FEATURES]
        y_chunk = chunk[TARGET].astype(bool).to_numpy()

        probabilities = model.predict_proba(X_chunk)[:, 1]
        predictions = probabilities >= 0.5

        actual_parts.append(y_chunk)
        probability_parts.append(probabilities)
        prediction_parts.append(predictions)

        processed_rows += len(chunk)

        print(f"Evaluated {processed_rows:,} test rows...")

    y_test = np.concatenate(actual_parts)
    probabilities = np.concatenate(probability_parts)
    predictions = np.concatenate(prediction_parts)

    roc_auc = roc_auc_score(y_test, probabilities)
    avg_precision = average_precision_score(y_test, probabilities)

    report = classification_report(
        y_test,
        predictions,
        target_names=["Non-fraud", "Fraud"],
        digits=4,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=[False, True],
    )

    fraud_rate = y_test.mean() * 100

    print("\nRANDOM FOREST — NATURAL-PREVALENCE TEST RESULTS")
    print("=" * 50)
    print(f"Test rows: {len(y_test):,}")
    print(f"Actual fraud cases: {int(y_test.sum()):,}")
    print(f"Actual fraud rate: {fraud_rate:.4f}%")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Average precision (PR-AUC summary): {avg_precision:.4f}")
    print("\nClassification report at threshold 0.5:")
    print(report)
    print("Confusion matrix (rows=actual, columns=predicted):")
    print(matrix)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "random_forest_final_split.joblib"
    report_path = REPORT_DIR / "random_forest_final_split.txt"

    joblib.dump(model, model_path)

    with report_path.open("w", encoding="utf-8") as file:
        file.write("Random Forest — Natural-Prevalence Test Results\n")
        file.write("=" * 50 + "\n")
        file.write(f"Test rows: {len(y_test):,}\n")
        file.write(f"Actual fraud cases: {int(y_test.sum()):,}\n")
        file.write(f"Actual fraud rate: {fraud_rate:.4f}%\n")
        file.write(f"ROC-AUC: {roc_auc:.4f}\n")
        file.write(f"Average precision: {avg_precision:.4f}\n\n")
        file.write("Classification report at threshold 0.5:\n")
        file.write(report)
        file.write("\nConfusion matrix (rows=actual, columns=predicted):\n")
        file.write(str(matrix))
        file.write(
            "\n\nMethodology notes:\n"
            "- The test set retains the natural class distribution.\n"
            "- Non-fraud training cases were sampled to reduce training cost.\n"
            "- Post-transaction balance features and is_flagged_fraud "
            "were excluded from predictors.\n"
            "- Threshold 0.5 is a baseline, not necessarily the optimal "
            "fraud detection threshold.\n"
            "- Predicted probabilities may require calibration because "
            "the training data was sampled.\n"
        )

    print(f"\nModel saved to {model_path.relative_to(ROOT)}")
    print(f"Report saved to {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

