
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "data" / "processed" / "fraud_model_dataset.csv"
REPORT_FILE = PROJECT_ROOT / "docs" / "model_dataset_validation.txt"

CHUNK_SIZE = 250_000

expected_columns = [
    "step",
    "simulated_day",
    "simulated_hour",
    "transaction_type",
    "amount",
    "origin_old_balance",
    "origin_new_balance",
    "destination_old_balance",
    "destination_new_balance",
    "origin_account_type",
    "destination_account_type",
    "origin_balance_change",
    "destination_balance_change",
    "origin_balance_error",
    "destination_balance_error",
    "is_fraud",
]

total_rows = 0
missing_counts = pd.Series(dtype="int64")
fraud_counts = {}
type_counts = {}
origin_type_counts = {}
destination_type_counts = {}
negative_amounts = 0
min_amount = float("inf")
max_amount = float("-inf")
min_step = float("inf")
max_step = float("-inf")
min_hour = float("inf")
max_hour = float("-inf")

print("Validating the modelling dataset in chunks...")

for chunk in pd.read_csv(DATA_FILE, chunksize=CHUNK_SIZE):
    total_rows += len(chunk)

    if list(chunk.columns) != expected_columns:
        raise ValueError("The CSV columns do not match the expected schema.")

    missing = chunk.isna().sum()
    missing_counts = missing_counts.add(missing, fill_value=0)

    fraud = chunk["is_fraud"].value_counts()
    for label, count in fraud.items():
        fraud_counts[str(label)] = (
            fraud_counts.get(str(label), 0) + int(count)
        )

    for column, counts in [
        ("transaction_type", type_counts),
        ("origin_account_type", origin_type_counts),
        ("destination_account_type", destination_type_counts),
    ]:
        for label, count in chunk[column].value_counts().items():
            counts[str(label)] = counts.get(str(label), 0) + int(count)

    negative_amounts += int((chunk["amount"] < 0).sum())

    min_amount = min(min_amount, float(chunk["amount"].min()))
    max_amount = max(max_amount, float(chunk["amount"].max()))
    min_step = min(min_step, int(chunk["step"].min()))
    max_step = max(max_step, int(chunk["step"].max()))
    min_hour = min(min_hour, int(chunk["simulated_hour"].min()))
    max_hour = max(max_hour, int(chunk["simulated_hour"].max()))

    if total_rows % 1_000_000 < CHUNK_SIZE:
        print(f"Checked {total_rows:,} rows...")


lines = [
    "MODELLING DATASET VALIDATION",
    "=" * 35,
    f"Dataset: {DATA_FILE}",
    f"Total rows: {total_rows:,}",
    f"Expected rows: 6,362,620",
    f"Row count matches expected: {total_rows == 6_362_620}",
    "",
    "Fraud target counts:",
]

for label, count in sorted(fraud_counts.items()):
    lines.append(f"  {label}: {count:,}")

fraud_rate = fraud_counts.get("True", 0) / total_rows * 100
lines.extend([
    f"Fraud rate: {fraud_rate:.4f}%",
    "",
    "Missing values by column:",
])

for column, count in missing_counts.items():
    lines.append(f"  {column}: {int(count):,}")

lines.extend([
    "",
    f"Negative amount rows: {negative_amounts:,}",
    f"Amount range: {min_amount:,.2f} to {max_amount:,.2f}",
    f"Step range: {min_step:.0f} to {max_step:.0f}",
    f"Simulated hour range: {min_hour:.0f} to {max_hour:.0f}",
    "",
    "Transaction type counts:",
])

for label, count in sorted(type_counts.items()):
    lines.append(f"  {label}: {count:,}")

lines.extend([
    "",
    "Origin account type counts:",
])

for label, count in sorted(origin_type_counts.items()):
    lines.append(f"  {label}: {count:,}")

lines.extend([
    "",
    "Destination account type counts:",
])

for label, count in sorted(destination_type_counts.items()):
    lines.append(f"  {label}: {count:,}")

report = "\n".join(lines)
print("\n" + report)

REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
REPORT_FILE.write_text(report + "\n", encoding="utf-8")

print(f"\nValidation report saved to: {REPORT_FILE}")

if total_rows != 6_362_620:
    raise ValueError("Unexpected row count.")

if missing_counts.sum() > 0:
    raise ValueError("Missing values were found. Investigate before modelling.")

if negative_amounts > 0:
    raise ValueError("Negative transaction amounts were found.")

