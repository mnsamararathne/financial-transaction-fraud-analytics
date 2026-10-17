
"""Evaluate the threshold-tuned Random Forest on the untouched test set."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
MODEL_PATH = ROOT / "models" / "random_forest_threshold_tuned.joblib"
TEST_PATH = DATA_DIR / "test_model_data.csv"
REPORT_PATH = ROOT / "docs" / "random_forest_final_evaluation.txt"

CHUNK_SIZE = 100_000
TUNED_THRESHOLD = 0.581039

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


def calculate_metrics(y_true, probabilities, threshold):
    predictions = probabilities >= threshold

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[False, True],
    ).ravel()

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "alerts": int(tp + fp),
    }


def main():
    print("Loading the trained Random Forest...")
    model = joblib.load(MODEL_PATH)

    actual_parts = []
    probability_parts = []
    processed_rows = 0

    print("Evaluating the final test set in chunks...")

    for chunk in pd.read_csv(TEST_PATH, chunksize=CHUNK_SIZE):
        X_chunk = chunk[FEATURES]
        y_chunk = chunk[TARGET].astype(bool).to_numpy()

        probabilities = model.predict_proba(X_chunk)[:, 1]

        actual_parts.append(y_chunk)
        probability_parts.append(probabilities)

        processed_rows += len(chunk)
        print(f"Evaluated {processed_rows:,} test rows...")

    y_test = np.concatenate(actual_parts)
    probabilities = np.concatenate(probability_parts)

    roc_auc = roc_auc_score(y_test, probabilities)
    average_precision = average_precision_score(y_test, probabilities)

    baseline = calculate_metrics(y_test, probabilities, 0.5)
    tuned = calculate_metrics(
        y_test, probabilities, TUNED_THRESHOLD
    )

    report = []
    report.append("FINAL RANDOM FOREST TEST EVALUATION")
    report.append("=" * 45)
    report.append(f"Test rows: {len(y_test):,}")
    report.append(f"Fraud cases: {int(y_test.sum()):,}")
    report.append(
        f"Fraud prevalence: {y_test.mean() * 100:.4f}%"
    )
    report.append(f"ROC-AUC: {roc_auc:.4f}")
    report.append(f"Average precision (AP): {average_precision:.4f}")
    report.append("")
    report.append("THRESHOLD COMPARISON")
    report.append("-" * 45)

    for name, result in [
        ("Default threshold (0.50)", baseline),
        ("Validation-tuned threshold", tuned),
    ]:
        report.append(f"\n{name}")
        report.append(f"Threshold: {result['threshold']:.6f}")
        report.append(f"Precision: {result['precision']:.4f}")
        report.append(f"Recall: {result['recall']:.4f}")
        report.append(f"F1-score: {result['f1']:.4f}")
        report.append(f"True positives: {result['tp']:,}")
        report.append(f"False positives: {result['fp']:,}")
        report.append(f"False negatives: {result['fn']:,}")
        report.append(f"True negatives: {result['tn']:,}")
        report.append(f"Total alerts: {result['alerts']:,}")

    report.append("")
    report.append("CLASSIFICATION REPORT AT TUNED THRESHOLD")
    report.append("-" * 45)
    report.append(
        classification_report(
            y_test,
            probabilities >= TUNED_THRESHOLD,
            labels=[False, True],
            target_names=["Non-fraud", "Fraud"],
            digits=4,
            zero_division=0,
        )
    )
    report.append(
        "The threshold was selected using validation data, "
        "not the final test set."
    )

    output = "\n".join(report)

    print("\n" + output)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(output + "\n", encoding="utf-8")

    print(f"\nReport saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()


