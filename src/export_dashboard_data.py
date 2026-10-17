
"""Export PostgreSQL analytics views for the fraud dashboard."""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "dashboard"

# Local PostgreSQL connection using the current macOS account.
DATABASE_URL = (
    "postgresql+psycopg://manesh@/financial_fraud_analytics"
    "?host=/tmp"
)

VIEWS = {
    "fraud_overview": """
        SELECT *
        FROM analytics.v_fraud_overview
    """,
    "fraud_by_type": """
        SELECT *
        FROM analytics.v_fraud_by_type
        ORDER BY fraud_rate_percentage DESC
    """,
    "fraud_by_day": """
        SELECT *
        FROM analytics.v_fraud_by_day
        ORDER BY simulated_day
    """,
    "fraud_by_hour": """
        SELECT *
        FROM analytics.v_fraud_by_hour
        ORDER BY simulated_hour
    """,
    "fraud_by_amount_band": """
        SELECT *
        FROM analytics.v_fraud_by_amount_band
    """,
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            for filename, query in VIEWS.items():
                print(f"Exporting {filename}...")

                dataframe = pd.read_sql(
                    text(query),
                    connection,
                )

                output_path = OUTPUT_DIR / f"{filename}.csv"
                dataframe.to_csv(output_path, index=False)

                print(
                    f"  Rows: {len(dataframe):,} | "
                    f"Columns: {len(dataframe.columns)}"
                )
                print(f"  Saved: {output_path}")

        print("\nDashboard exports completed.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

