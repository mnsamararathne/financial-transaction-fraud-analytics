

RANDOM_STATE = 42
TEST_SIZE = 0.20

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

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def main():
    print("Loading the modelling dataset...")

    # Read only the columns needed for the initial model.
    # This avoids loading unnecessary post-transaction fields.
    df = pd.read_csv(
        INPUT_FILE,
        usecols=FEATURES + [TARGET],
        dtype={
            "transaction_type": "category",
            "origin_account_type": "category",
            "destination_account_type": "category",
            TARGET: "bool",
        },
    )

    print(f"Dataset shape: {df.shape}")
    print(f"Fraudulent transactions: {int(df[TARGET].sum()):,}")
    print(
        f"Fraud rate: {df[TARGET].mean() * 100:.4f}%"
    )

    X = df[FEATURES]
    y = df[TARGET].astype("int8")

    # Keep the original fraud prevalence in both partitions.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Store feature matrices and targets separately.
    # The test set retains the natural class distribution.
    X_train.to_csv(
        OUTPUT_DIR / "X_train.csv",
        index=False,
    )
    X_test.to_csv(
        OUTPUT_DIR / "X_test.csv",
        index=False,
    )
    y_train.to_frame(TARGET).to_csv(
        OUTPUT_DIR / "y_train.csv",
        index=False,
    )
    y_test.to_frame(TARGET).to_csv(
        OUTPUT_DIR / "y_test.csv",
        index=False,
    )

    print("\nTRAINING AND TEST SPLIT")
    print("=" * 35)
    print(f"Training rows: {len(X_train):,}")
  
"""Create a reproducible, leakage-aware dataset for initial fraud modelling."""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "fraud_model_dataset.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

RANDOM_STATE = 42
TEST_SIZE = 0.20

TARGET = "is_fraud"

FEATURES = [
    "amount",
    "origin_old_balance",
    "destination_old_balance",
    "simulated_day",
    "simulated_hour",
    "transaction_type",
    "origin_account_type",
    "destination_account_type",
]

CATEGORICAL_FEATURES = [
    "transaction_type",
    "origin_account_type",
    "destination_account_type",
]


def main():
    print("Reading only the columns required for initial modelling...")

    # Load only the selected columns and use compact data types.
    df = pd.read_csv(
        INPUT_FILE,
        usecols=FEATURES + [TARGET],
        dtype={
            "amount": "float32",
            "origin_old_balance": "float32",
            "destination_old_balance": "float32",
            "simulated_day": "int16",
            "simulated_hour": "int8",
            "transaction_type": "category",
            "origin_account_type": "category",
            "destination_account_type": "category",
            TARGET: "bool",
        },
    )

    print(f"Rows loaded: {len(df):,}")
    print(f"Fraud cases: {int(df[TARGET].sum()):,}")
    print(f"Fraud rate: {df[TARGET].mean() * 100:.4f}%")

    # Retain every fraud case and sample non-fraud cases for the
    # initial experiment. This reduces memory use and training time.
    fraud = df.loc[df[TARGET]]
    non_fraud = df.loc[~df[TARGET]]

    negative_sample_size = min(
        len(non_fraud),
        len(fraud) * 20,
    )

    non_fraud_sample = non_fraud.sample(
        n=negative_sample_size,
        random_state=RANDOM_STATE,
    )

    sampled = pd.concat(
        [fraud, non_fraud_sample],
        ignore_index=True,
    )

    # Shuffle reproducibly before splitting.
    sampled = sampled.sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    X = sampled[FEATURES]
    y = sampled[TARGET].astype("int8")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save the sample's split files; these are not the full dataset.
    X_train.to_csv(OUTPUT_DIR / "X_train_sample.csv", index=False)
    X_test.to_csv(OUTPUT_DIR / "X_test_sample.csv", index=False)
    y_train.to_frame(TARGET).to_csv(
        OUTPUT_DIR / "y_train_sample.csv", index=False
    )
    y_test.to_frame(TARGET).to_csv(
        OUTPUT_DIR / "y_test_sample.csv", index=False
    )

    print("\nINITIAL SAMPLE SUMMARY")
    print("=" * 35)
    print(f"Sample rows: {len(sampled):,}")
    print(f"Fraud cases: {int(y.sum()):,}")
    print(f"Non-fraud cases: {int((y == 0).sum()):,}")
    print(f"Training rows: {len(X_train):,}")
    print(f"Testing rows: {len(X_test):,}")
    print(f"Training fraud cases: {int(y_train.sum()):,}")
    print(f"Testing fraud cases: {int(y_test.sum()):,}")
    print(f"Training fraud rate: {y_train.mean() * 100:.4f}%")
    print(f"Testing fraud rate: {y_test.mean() * 100:.4f}%")

    print("\nFeatures used:")
    for feature in FEATURES:
        print(f"- {feature}")

    print("\nExcluded from the primary model:")
    print("- Post-transaction balances and derived balance changes")
    print("- Balance-error features")
    print("- is_flagged_fraud")

    print("\nWARNING: This sample has a higher fraud prevalence than")
    print("the original data. Its test metrics are not final")
    print("performance estimates at the original prevalence.")
    print(f"\nFiles saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

