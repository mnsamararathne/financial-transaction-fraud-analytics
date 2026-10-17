
"""Train a Decision Tree baseline for fraud detection."""

from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "docs"

TARGET = "is_fraud"

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


def main():
    print("Loading the same training and test sets...")

    X_train = pd.read_csv(DATA / "X_train_sample.csv")
    X_test = pd.read_csv(DATA / "X_test_sample.csv")
    y_train = pd.read_csv(DATA / "y_train_sample.csv")[TARGET]
    y_test = pd.read_csv(DATA / "y_test_sample.csv")[TARGET]

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

    model = Pipeline([
        ("preprocessing", preprocessing),
        (
            "classifier",
            DecisionTreeClassifier(
                max_depth=10,
                min_samples_leaf=20,
                class_weight="balanced",
                random_state=42,
            ),
        ),
    ])

    print("Training Decision Tree...")
    model.fit(X_train, y_train)

    print("Evaluating the model...")
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, probabilities)
    avg_precision = average_precision_score(y_test, probabilities)
    report = classification_report(
        y_test,
        predictions,
        target_names=["Non-fraud", "Fraud"],
        digits=4,
        zero_division=0,
    )
    matrix = confusion_matrix(y_test, predictions)

    print("\nDECISION TREE RESULTS")
    print("=" * 40)
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Average precision: {avg_precision:.4f}")
    print("\nClassification report:")
    print(report)
    print("Confusion matrix (rows=actual, columns=predicted):")
    print(matrix)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_DIR / "decision_tree_baseline.joblib")

    with (REPORT_DIR / "decision_tree_baseline.txt").open(
        "w", encoding="utf-8"
    ) as file:
        file.write("Decision Tree Baseline\n")
        file.write("=" * 30 + "\n")
        file.write(f"ROC-AUC: {roc_auc:.4f}\n")
        file.write(f"Average precision: {avg_precision:.4f}\n\n")
        file.write(report)
        file.write("\nConfusion matrix:\n")
        file.write(str(matrix))
        file.write(
            "\n\nThe test set uses a sampled class distribution. "
            "Precision and other prevalence-sensitive metrics "
            "must be reassessed on a test set with the original "
            "fraud prevalence.\n"
        )

    print("\nModel saved to models/decision_tree_baseline.joblib")
    print("Report saved to docs/decision_tree_baseline.txt")


if __name__ == "__main__":
    main()

