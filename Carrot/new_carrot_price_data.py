import os
from dotenv import load_dotenv
import psycopg2
from flipside import Flipside
import time
from datetime import datetime


def main():
    start_time = time.time()

    # Load the .env file
    load_dotenv()   

    # Initialize `Flipside` with your API Key and API URL
    flipside = Flipside(
        os.getenv("FLIPSIDE_API_KEY"), 
        "https://api-v2.flipsidecrypto.xyz"
    )

    # New Flipside SQL query
    sql = """
    WITH tab1 AS (
        SELECT 
            tx_id,
            mint_amount / POWER(10, 9) AS amt
        FROM solana.defi.fact_token_mint_actions
        WHERE mint LIKE 'CRTx1JouZhzSU6XytsE42UQraoGqiHgxabocVfARTy2s'
        AND block_timestamp > '2024-05-01'
    ),

    Carrot_Price AS ( 
        SELECT 
            DATE(block_timestamp) AS day,
            MEDIAN(amount / amt) AS median_price
        FROM solana.core.fact_transfers AS a
        LEFT OUTER JOIN tab1
            ON a.tx_id = tab1.tx_id  
        WHERE tx_to LIKE 'FfCRL34rkJiMiX5emNDrYp3MdWH2mES3FvDQyFppqgpJ'
        AND mint LIKE 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
        AND block_timestamp >= GETDATE() - interval '2 days' 
        AND block_timestamp > '2024-05-01'
        GROUP BY 1 
        HAVING NOT median_price = 0
        ORDER BY 1 
    ), 

    Carrot_Holders AS (
        SELECT
            DATE(block_timestamp) AS day,
            SUM(
                CASE WHEN bal = 0 THEN -1 
                WHEN change = bal THEN 1 
                ELSE 0 END
            ) AS net_holders
        FROM (
            SELECT
                block_timestamp,
                owner,
                balance - pre_balance AS change,
                SUM(balance - pre_balance) OVER (PARTITION BY owner ORDER BY block_id) AS bal
            FROM solana.core.fact_token_balances
            WHERE mint = 'CRTx1JouZhzSU6XytsE42UQraoGqiHgxabocVfARTy2s'
            AND succeeded = TRUE
            AND block_timestamp::date >= '2024-08-01'
        )
        WHERE block_timestamp >= GETDATE() - interval '2 days' 
        GROUP BY 1 
        ORDER BY 1 
    ) 

    SELECT
        Carrot_Price.day AS block_timestamp, 
        net_holders,
        median_price AS price
    FROM Carrot_Price
    LEFT OUTER JOIN Carrot_Holders ON Carrot_Price.day = Carrot_Holders.day 
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

        # Insert data into `carrot_price_holders` table
        insert_sql = """
        INSERT INTO carrot_price_holders (
            block_timestamp,
            net_holders,
            price
        ) VALUES (%s, %s, %s)
        ON CONFLICT (block_timestamp) DO NOTHING;
        """
        print("SQL Setup")
        # Iterate through all collected records and insert into the database
        for row in all_rows:
            cur.execute(insert_sql, (
                row['block_timestamp'],   # TIMESTAMP
                row['net_holders'],       # INTEGER
                row['price']              # NUMERIC
        ))

        
        conn.commit()
        print("Data inserted successfully!")

        print("Refreshing carrot_tvl materialized view...")
        cur.execute("REFRESH MATERIALIZED VIEW carrot_tvl;")
        conn.commit()
        print("carrot_tvl materialized view refreshed successfully!")

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
