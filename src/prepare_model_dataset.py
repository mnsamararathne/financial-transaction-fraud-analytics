
import csv
from pathlib import Path

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "fraud_model_dataset.csv"
BATCH_SIZE = 10_000


QUERY = """
SELECT
    dt.step,
    dt.simulated_day,
    dt.simulated_hour,
    dtt.transaction_type,
    f.amount,

    f.origin_old_balance,
    f.origin_new_balance,
    f.destination_old_balance,
    f.destination_new_balance,

    da_origin.account_type AS origin_account_type,
    da_destination.account_type AS destination_account_type,

    f.origin_old_balance - f.origin_new_balance
        AS origin_balance_change,

    f.destination_new_balance - f.destination_old_balance
        AS destination_balance_change,

    f.origin_old_balance - f.amount - f.origin_new_balance
        AS origin_balance_error,

    f.destination_old_balance + f.amount
        - f.destination_new_balance
        AS destination_balance_error,

    f.is_fraud

FROM warehouse.fact_transactions AS f

JOIN warehouse.dim_time AS dt
    ON f.time_key = dt.time_key

JOIN warehouse.dim_transaction_type AS dtt
    ON f.transaction_type_key = dtt.transaction_type_key

JOIN warehouse.dim_account AS da_origin
    ON f.origin_account_key = da_origin.account_key

JOIN warehouse.dim_account AS da_destination
    ON f.destination_account_key = da_destination.account_key
"""


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    total_rows = 0

    print("Connecting to PostgreSQL...")
    print("Preparing the modelling dataset.")
    print(f"Output: {OUTPUT_FILE}")

    with psycopg.connect(
        dbname="financial_fraud_analytics",
        user="manesh",
        host="/tmp",
        port=5432,
    ) as conn:

        with conn.cursor(name="model_dataset_cursor") as cursor:
            cursor.itersize = BATCH_SIZE
            cursor.execute(QUERY)

            column_names = [column.name for column in cursor.description]

            with OUTPUT_FILE.open(
                "w", newline="", encoding="utf-8"
            ) as output:
                writer = csv.writer(output)
                writer.writerow(column_names)

                while True:
                    rows = cursor.fetchmany(BATCH_SIZE)

                    if not rows:
                        break

                    writer.writerows(rows)
                    total_rows += len(rows)

                    if total_rows % 500_000 < BATCH_SIZE:
                        print(f"Exported {total_rows:,} rows...")

    print("\nDataset extraction completed.")
    print(f"Total rows exported: {total_rows:,}")
    print(f"Output file: {OUTPUT_FILE}")

    if total_rows != 6_362_620:
        print(
            "WARNING: The exported row count differs from "
            "the expected warehouse count. Please investigate."
        )


if __name__ == "__main__":
    main()

