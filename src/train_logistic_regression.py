
"""Train an interpretable baseline model for fraud detection."""

from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "docs"

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

TARGET = "is_fraud"


def main():
    print("Loading the prepared training and test sets...")

    X_train = pd.read_csv(DATA / "X_train_sample.csv")
    X_test = pd.read_csv(DATA / "X_test_sample.csv")
    y_train = pd.read_csv(DATA / "y_train_sample.csv")[TARGET]
    y_test = pd.read_csv(DATA / "y_test_sample.csv")[TARGET]

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ])

    preprocessing = ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])

    model = Pipeline([
        ("preprocessing", preprocessing),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=42,
                solver="liblinear",
            ),
        ),
    ])

    print("Training Logistic Regression...")
    model.fit(X_train, y_train)

    print("Generating test predictions...")
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    print("\nBASELINE MODEL RESULTS")
    print("=" * 45)
    print(f"ROC-AUC: {roc_auc_score(y_test, probabilities):.4f}")
    print(
        "Average precision (PR-AUC summary): "
        f"{average_precision_score(y_test, probabilities):.4f}"
    )

    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        target_names=["Non-fraud", "Fraud"],
        digits=4,
        zero_division=0,
    ))

    print("Confusion matrix (rows=actual, columns=predicted):")
    print(confusion_matrix(y_test, predictions))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "logistic_regression_baseline.joblib"
    joblib.dump(model, model_path)

    report_path = REPORT_DIR / "logistic_regression_baseline.txt"
    with report_path.open("w", encoding="utf-8") as report:
        report.write("Logistic Regression Baseline\n")
        report.write("=" * 35 + "\n")
        report.write(
            f"ROC-AUC: {roc_auc_score(y_test, probabilities):.4f}\n"
        )
        report.write(
            "Average precision: "
            f"{average_precision_score(y_test, probabilities):.4f}\n\n"
        )
        report.write(classification_report(
            y_test,
            predictions,
            target_names=["Non-fraud", "Fraud"],
            digits=4,
            zero_division=0,
        ))
        report.write("\nConfusion matrix:\n")
        report.write(str(confusion_matrix(y_test, predictions)))
        report.write(
            "\n\nEvaluation note: the test set uses a sampled "
            "class distribution and does not represent the original "
            "fraud prevalence.\n"
        )

    print(f"\nSaved model: {model_path}")
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()

