
import psycopg


def main():
    try:
        with psycopg.connect(
            dbname="financial_fraud_analytics",
            user="manesh",
            host="/tmp",
            port=5432,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        current_database(),
                        current_user,
                        COUNT(*)
                    FROM warehouse.fact_transactions;
                """)

                database, username, transaction_count = cur.fetchone()

                print("PostgreSQL connection successful.")
                print(f"Database: {database}")
                print(f"User: {username}")
                print(f"Warehouse transactions: {transaction_count:,}")

    except Exception as error:
        print(f"Connection test failed: {error}")
        raise


if __name__ == "__main__":
    main()

