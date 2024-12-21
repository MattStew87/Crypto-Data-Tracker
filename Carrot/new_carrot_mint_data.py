import os
from dotenv import load_dotenv
import psycopg2
from flipside import Flipside
import time

def main():
    start_time = time.time()

    # Load the .env file
    load_dotenv()   

    # Initialize `Flipside` with your API Key and API URL
    flipside = Flipside(
        os.getenv("FLIPSIDE_API_KEY"), 
        "https://api-v2.flipsidecrypto.xyz"
    )

    # New Flipside SQL query for burn and mint actions
    sql = """
    With tab1 as (
        SELECT 
            block_timestamp, 
            tx_id, 
            event_type, 
            burn_amount / POWER(10, decimal) AS amount
        FROM solana.defi.fact_token_burn_actions
        WHERE succeeded
            AND mint LIKE 'CRTx1JouZhzSU6XytsE42UQraoGqiHgxabocVfARTy2s'
            AND block_timestamp >= GETDATE() - interval '2 days'
            AND block_timestamp > '2024-08-01'
            AND succeeded = TRUE

        UNION ALL

        SELECT 
            block_timestamp, 
            tx_id, 
            event_type, 
            mint_amount / POWER(10, decimal) AS amount
        FROM solana.defi.fact_token_mint_actions
        WHERE succeeded
            AND mint LIKE 'CRTx1JouZhzSU6XytsE42UQraoGqiHgxabocVfARTy2s'
            AND block_timestamp >= GETDATE() - interval '2 days'
            AND block_timestamp > '2024-08-01'
            AND succeeded = TRUE
    )
    SELECT
        * 
    FROM tab1 
    """

    # Run the query against Flipside's query engine and set initial page
    query_result_set = flipside.query(sql, page_number=1, page_size=1)

    # Pagination setup
    current_page_number = 1
    page_size = 1000  # Adjust as necessary
    total_pages = 2  # Start with 2 until we know the real number

    # List to store all rows
    all_rows = []
   
    print("Before Flipside")
    # Paginate through all available pages
    while current_page_number <= total_pages:
        results = flipside.get_query_results(
            query_result_set.query_id,
            page_number=current_page_number,
            page_size=page_size
        )

        # Update total pages based on response
        total_pages = results.page.totalPages

        # Add records from this page to the list
        if results.records:
            all_rows.extend(results.records)

        # Increment page number to move to the next page
        current_page_number += 1
    print("After Flipside")

    # Connect to your PostgreSQL database using environment variables from .env
    try:
        conn = psycopg2.connect(
            host=os.getenv("DATABASE_HOST"),
            database="CARROT_DB",
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"), 
            port="5432" 
        )
        cur = conn.cursor()

        # Insert data into `carrot_burn_mint_actions` table
        insert_sql = """
        INSERT INTO carrot_burn_mint_actions (
            block_timestamp,
            tx_id,
            event_type,
            amount
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (tx_id) DO NOTHING;
        """

        # Iterate through all collected records and insert into the database
        for row in all_rows:
            cur.execute(insert_sql, (
                row['block_timestamp'],   # TIMESTAMP
                row['tx_id'],             # TEXT
                row['event_type'],        # TEXT
                row['amount']             # NUMERIC
            ))

        # Commit changes and close connection
        conn.commit()
        print("Data inserted successfully!")

        print("Refreshing carrot_supply materialized view...")
        cur.execute("REFRESH MATERIALIZED VIEW carrot_supply;")
        conn.commit()
        print("carrot_supply materialized view refreshed successfully!")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

    end_time = time.time()
    print(f"Execution time: {end_time - start_time} seconds")

# Entry point for the script
if __name__ == "__main__":
    main()
