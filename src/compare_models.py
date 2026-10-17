
"""Compare four fraud classifiers on consistent data partitions.

The validation set is used to select a threshold for each model.
The final test set is evaluated only after thresholds are selected.
"""

from pathlib import Path
import gc

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "docs"

TRAIN_PATH = DATA_DIR / "train_model_data.csv"
VALIDATION_PATH = DATA_DIR / "validation_model_data.csv"
TEST_PATH = DATA_DIR / "test_model_data.csv"

TARGET = "is_fraud"
CHUNK_SIZE = 100_000
TARGET_RECALL = 0.95
RANDOM_SEED = 42

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


def build_preprocessor(scale_numeric=False):
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]

    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    numeric_pipeline = Pipeline(numeric_steps)

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])


def build_models():
    return {
        "Logistic Regression": Pipeline([
            ("preprocessing", build_preprocessor(scale_numeric=True)),
            ("classifier", LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            )),
        ]),
        "Decision Tree": Pipeline([
            ("preprocessing", build_preprocessor()),
            ("classifier", DecisionTreeClassifier(
                max_depth=16,
                min_samples_leaf=10,
                class_weight="balanced",
                random_state=RANDOM_SEED,
            )),
        ]),
        "Random Forest": Pipeline([
            ("preprocessing", build_preprocessor()),
            ("classifier", RandomForestClassifier(
                n_estimators=100,
                max_depth=16,
                min_samples_leaf=10,
                max_features="sqrt",
                class_weight="balanced_subsample",
                random_state=RANDOM_SEED,
                n_jobs=2,
            )),
        ]),
        "XGBoost": Pipeline([
            ("preprocessing", build_preprocessor()),
            ("classifier", XGBClassifier(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="binary:logistic",
                eval_metric="logloss",
                tree_method="hist",
                random_state=RANDOM_SEED,
                n_jobs=2,
                verbosity=0,
            )),
        ]),
    }


def load_partition(path):
    frame = pd.read_csv(path)
    X = frame[FEATURES]
    y = frame[TARGET].astype(bool).to_numpy()
    return X, y


def score_partition(model, path):
    actual_parts = []
    probability_parts = []
    total_rows = 0

    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE):
        probabilities = model.predict_proba(chunk[FEATURES])[:, 1]
        actual_parts.append(chunk[TARGET].astype(bool).to_numpy())
        probability_parts.append(probabilities)
        total_rows += len(chunk)

    return (
        np.concatenate(actual_parts),
        np.concatenate(probability_parts),
        total_rows,
    )


def choose_threshold(y_true, probabilities):
    # Select the highest-precision threshold that achieves
    # at least the target recall on validation data.
    from sklearn.metrics import precision_recall_curve

    precisions, recalls, thresholds = precision_recall_curve(
        y_true, probabilities
    )

    eligible = np.flatnonzero(recalls[:-1] >= TARGET_RECALL)

    if len(eligible) == 0:
        return 0.5

    best_index = eligible[np.argmax(precisions[eligible])]
    return float(thresholds[best_index])


def calculate_metrics(y_true, probabilities, threshold):
    predictions = probabilities >= threshold

    tn, fp, fn, tp = confusion_matrix(
        y_true, predictions, labels=[False, True]
    ).ravel()

    return {
        "threshold": threshold,
        "precision": precision_score(
            y_true, predictions, zero_division=0
        ),
        "recall": recall_score(
            y_true, predictions, zero_division=0
        ),
        "f1": f1_score(y_true, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_true, probabilities),
        "average_precision": average_precision_score(
            y_true, probabilities
        ),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "alerts": int(tp + fp),
    }


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading training sample...")
    X_train, y_train = load_partition(TRAIN_PATH)

    print(f"Training rows: {len(y_train):,}")
    print(f"Training fraud cases: {int(y_train.sum()):,}")

    print("\nLoading validation set...")
    X_validation, y_validation = load_partition(VALIDATION_PATH)
    print(f"Validation rows: {len(y_validation):,}")
    print(f"Validation fraud cases: {int(y_validation.sum()):,}")

    results = []
    models = build_models()

    for name, model in models.items():
        print("\n" + "=" * 60)
        print(f"Training {name}...")
        model.fit(X_train, y_train)

        print(f"Scoring validation set for {name}...")
        validation_probabilities = model.predict_proba(
            X_validation
        )[:, 1]

        threshold = choose_threshold(
            y_validation, validation_probabilities
        )

        validation_metrics = calculate_metrics(
            y_validation, validation_probabilities, threshold
        )

        print(f"Validation ROC-AUC: {validation_metrics['roc_auc']:.4f}")
        print(
            "Validation average precision: "
            f"{validation_metrics['average_precision']:.4f}"
        )
        print(f"Selected threshold: {threshold:.6f}")
        print(
            "Validation precision / recall: "
            f"{validation_metrics['precision']:.4f} / "
            f"{validation_metrics['recall']:.4f}"
        )

        model_path = MODEL_DIR / (
            name.lower().replace(" ", "_") + "_comparison.joblib"
        )
        joblib.dump(model, model_path)

        # Keep only one fitted model in memory at a time.
        del model
        gc.collect()

        results.append({
            "model": name,
            "threshold": threshold,
            "validation_roc_auc": validation_metrics["roc_auc"],
            "validation_average_precision":
                validation_metrics["average_precision"],
            "validation_precision": validation_metrics["precision"],
            "validation_recall": validation_metrics["recall"],
            "validation_f1": validation_metrics["f1"],
        })

    del models, X_train, y_train, X_validation, y_validation
    gc.collect()

    print("\nAll four models trained and saved.")
    print("Validation summary:")
    print(pd.DataFrame(results).to_string(index=False))

    print("\nEvaluating the saved models on the final test set...")
    final_results = []

    for result in results:
        name = result["model"]
        model_path = MODEL_DIR / (
            name.lower().replace(" ", "_") + "_comparison.joblib"
        )

        print(f"\nEvaluating {name}...")
        model = joblib.load(model_path)

        y_test, probabilities, total_rows = score_partition(
            model, TEST_PATH
        )

        test_metrics = calculate_metrics(
            y_test, probabilities, result["threshold"]
        )

        final_results.append({
            "model": name,
            "threshold": result["threshold"],
            "test_roc_auc": test_metrics["roc_auc"],
            "test_average_precision": test_metrics["average_precision"],
            "test_precision": test_metrics["precision"],
            "test_recall": test_metrics["recall"],
            "test_f1": test_metrics["f1"],
            "true_positives": test_metrics["tp"],
            "false_positives": test_metrics["fp"],
            "false_negatives": test_metrics["fn"],
            "total_alerts": test_metrics["alerts"],
        })

        print(f"Test rows: {total_rows:,}")
        print(f"ROC-AUC: {test_metrics['roc_auc']:.4f}")
        print(
            "Average precision: "
            f"{test_metrics['average_precision']:.4f}"
        )
        print(f"Precision: {test_metrics['precision']:.4f}")
        print(f"Recall: {test_metrics['recall']:.4f}")
        print(f"F1-score: {test_metrics['f1']:.4f}")
        print(f"False positives: {test_metrics['fp']:,}")
        print(f"False negatives: {test_metrics['fn']:,}")
        print(f"Total alerts: {test_metrics['alerts']:,}")

        del model, y_test, probabilities
        gc.collect()

    comparison = pd.DataFrame(final_results)
    comparison.to_csv(
        DATA_DIR / "model_comparison_results.csv", index=False
    )

    report_path = REPORT_DIR / "model_comparison_results.txt"
    report_path.write_text(
        "FINAL TEST MODEL COMPARISON\n"
        "===========================\n\n"
        "Thresholds were selected using validation data. "
        "Final test data was not used for threshold selection.\n\n"
        + comparison.to_string(index=False)
        + "\n",
        encoding="utf-8",
    )

    print("\nFINAL TEST COMPARISON")
    print("=" * 60)
    print(comparison.to_string(index=False))
    print(f"\nComparison CSV saved to {DATA_DIR / 'model_comparison_results.csv'}")
    print(f"Comparison report saved to {report_path}")


if __name__ == "__main__":
    main()

