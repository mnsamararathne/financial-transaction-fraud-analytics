
"""Create training, validation and final test datasets."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "processed" / "fraud_model_dataset.csv"
OUTPUT = ROOT / "data" / "processed"

CHUNK_SIZE = 100_000
TEST_FRACTION = 0.20
VALIDATION_FRACTION = 0.10
NEGATIVE_SAMPLE_RATE = 0.026
RANDOM_SEED = 42
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

COLUMNS = FEATURES + [TARGET]


def main():
    rng = np.random.default_rng(RANDOM_SEED)

    train_path = OUTPUT / "train_model_data.csv"
    validation_path = OUTPUT / "validation_model_data.csv"
    test_path = OUTPUT / "test_model_data.csv"

    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Recreate the datasets from scratch on every run.
    for path in (train_path, validation_path, test_path):
        if path.exists():
            path.unlink()

    total_rows = 0
    train_rows = 0
    validation_rows = 0
    test_rows = 0
    train_fraud = 0
    validation_fraud = 0
    test_fraud = 0

    print("Creating training, validation and test datasets...")

    for chunk in pd.read_csv(
        SOURCE,
        usecols=COLUMNS,
        chunksize=CHUNK_SIZE,
        dtype={"is_fraud": "bool"},
    ):
        total_rows += len(chunk)

        # Assign each row to exactly one partition.
        random_values = rng.random(len(chunk))
        is_test = random_values < TEST_FRACTION
        is_validation = (
            (random_values >= TEST_FRACTION)
            & (random_values < TEST_FRACTION + VALIDATION_FRACTION)
        )
        is_training = ~(is_test | is_validation)

        test = chunk.loc[is_test]
        validation = chunk.loc[is_validation]
        training_pool = chunk.loc[is_training]

        # Keep every fraud case in the training pool.
        # Sample non-fraud cases to keep training manageable.
        fraud = training_pool.loc[training_pool[TARGET]]
        non_fraud = training_pool.loc[~training_pool[TARGET]]

        keep_negative = (
            rng.random(len(non_fraud)) < NEGATIVE_SAMPLE_RATE
        )

        train = pd.concat(
            [fraud, non_fraud.loc[keep_negative]],
            ignore_index=True,
        )

        for data, path in (
            (train, train_path),
            (validation, validation_path),
            (test, test_path),
        ):
            data.to_csv(
                path,
                mode="a",
                header=not path.exists(),
                index=False,
            )

        train_rows += len(train)
        validation_rows += len(validation)
        test_rows += len(test)

        train_fraud += int(train[TARGET].sum())
        validation_fraud += int(validation[TARGET].sum())
        test_fraud += int(test[TARGET].sum())

        if total_rows % 1_000_000 < CHUNK_SIZE:
            print(f"Processed {total_rows:,} source rows...")

    print("\nDATA SPLIT SUMMARY")
    print("=" * 45)
    print(f"Source rows: {total_rows:,}")

    for name, rows, fraud_count, path in (
        ("Training sample", train_rows, train_fraud, train_path),
        ("Validation set", validation_rows, validation_fraud, validation_path),
        ("Final test set", test_rows, test_fraud, test_path),
    ):
        rate = fraud_count / rows * 100 if rows else 0
        print(f"\n{name}")
        print(f"  Rows: {rows:,}")
        print(f"  Fraud cases: {fraud_count:,}")
        print(f"  Fraud rate: {rate:.4f}%")
        print(f"  File: {path.relative_to(ROOT)}")

    print("\nTraining negatives are sampled.")
    print("Validation and test sets retain natural prevalence.")


if __name__ == "__main__":
    main()

