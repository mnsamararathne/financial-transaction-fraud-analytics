
"""Train a Random Forest and tune its threshold on validation data."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "docs"

TARGET = "is_fraud"
CHUNK_SIZE = 100_000
TARGET_RECALL = 0.95

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


def evaluate_threshold(y_true, probabilities, threshold):
    predictions = probabilities >= threshold

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[False, True],
    ).ravel()

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0

    return {
        "threshold": float(threshold),
        "precision": precision,
        "recall": recall,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "alerts": int(tp + fp),
    }


def main():
    train_path = DATA / "train_model_data.csv"
    validation_path = DATA / "validation_model_data.csv"

    print("Loading the current training sample...")
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

    print("Scoring validation data in chunks...")

    actual_parts = []
    probability_parts = []
    processed_rows = 0

    for chunk in pd.read_csv(
        validation_path,
        chunksize=CHUNK_SIZE,
    ):
        X_chunk = chunk[FEATURES]
        y_chunk = chunk[TARGET].astype(bool).to_numpy()

        probabilities = model.predict_proba(X_chunk)[:, 1]

        actual_parts.append(y_chunk)
        probability_parts.append(probabilities)
        processed_rows += len(chunk)

        print(f"Scored {processed_rows:,} validation rows...")

    y_validation = np.concatenate(actual_parts)
    probabilities = np.concatenate(probability_parts)

    roc_auc = roc_auc_score(y_validation, probabilities)
    avg_precision = average_precision_score(
        y_validation,
        probabilities,
    )

    # Find the threshold with the highest validation precision
    # while keeping recall at or above the specified target.
    precision_values, recall_values, thresholds = (
        precision_recall_curve(y_validation, probabilities)
    )

    eligible = np.flatnonzero(
        recall_values[:-1] >= TARGET_RECALL
    )

    if len(eligible) == 0:
        raise RuntimeError(
            "No threshold achieved the required validation recall."
        )

    best_index = eligible[
        np.argmax(precision_values[eligible])
    ]
    selected_threshold = float(thresholds[best_index])

    baseline = evaluate_threshold(
        y_validation,
        probabilities,
        0.5,
    )
    selected = evaluate_threshold(
        y_validation,
        probabilities,
        selected_threshold,
    )

    print("\nVALIDATION RESULTS")
    print("=" * 45)
    print(f"Validation rows: {len(y_validation):,}")
    print(f"Fraud cases: {int(y_validation.sum()):,}")
    print(f"Fraud prevalence: {y_validation.mean() * 100:.4f}%")
    print(f"ROC-AUC: {roc_auc:.4f}")
    print(f"Average precision: {avg_precision:.4f}")

    print("\nThreshold comparison")
    print("-" * 75)
    print(
        f"{'Threshold':>12} {'Precision':>12} {'Recall':>10} "
        f"{'TP':>8} {'FP':>9} {'FN':>7} {'Alerts':>9}"
    )

    for result in (baseline, selected):
        print(
            f"{result['threshold']:>12.6f} "
            f"{result['precision']:>12.4f} "
            f"{result['recall']:>10.4f} "
            f"{result['tp']:>8,} "
            f"{result['fp']:>9,} "
            f"{result['fn']:>7,} "
            f"{result['alerts']:>9,}"
        )

    selected_predictions = probabilities >= selected_threshold

    report = classification_report(
        y_validation,
        selected_predictions,
        labels=[False, True],
        target_names=["Non-fraud", "Fraud"],
        digits=4,
        zero_division=0,
    )

    selected_matrix = confusion_matrix(
        y_validation,
        selected_predictions,
        labels=[False, True],
    )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = MODEL_DIR / "random_forest_threshold_tuned.joblib"
    report_path = REPORT_DIR / "random_forest_threshold_tuning.txt"

    joblib.dump(model, model_path)

    with report_path.open("w", encoding="utf-8") as file:
        file.write("Random Forest Validation Threshold Tuning\n")
        file.write("=" * 45 + "\n")
        file.write(f"Validation rows: {len(y_validation):,}\n")
        file.write(f"Fraud cases: {int(y_validation.sum()):,}\n")
        file.write(f"Fraud prevalence: {y_validation.mean() * 100:.4f}%\n")
        file.write(f"ROC-AUC: {roc_auc:.4f}\n")
        file.write(f"Average precision: {avg_precision:.4f}\n\n")
        file.write(f"Target recall: {TARGET_RECALL:.2%}\n")
        file.write(f"Selected threshold: {selected_threshold:.8f}\n\n")
        file.write("Threshold 0.5 results:\n")
        file.write(f"{baseline}\n\n")
        file.write("Selected threshold results:\n")
        file.write(f"{selected}\n\n")
        file.write("Classification report at selected threshold:\n")
        file.write(report)
        file.write("\nConfusion matrix (rows=actual, columns=predicted):\n")
        file.write(str(selected_matrix))
        file.write(
            "\n\nThe threshold was selected using validation data only. "
            "The final test set was not used for threshold selection.\n"
            "The training data uses sampled non-fraud cases, so predicted "
            "probabilities may not be calibrated to natural prevalence.\n"
        )

    print(f"\nModel saved to {model_path.relative_to(ROOT)}")
    print(f"Report saved to {report_path.relative_to(ROOT)}")
    print("\nThe final test set has not been evaluated or used for tuning.")


if __name__ == "__main__":
    main()

