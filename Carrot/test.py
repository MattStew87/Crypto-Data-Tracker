import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()   

conn = psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        database="CARROT_DB",
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"), 
        port="5432" 
)
cur = conn.cursor()

insert_sql = """
INSERT INTO carrot_price_holders (
    block_timestamp,
    net_holders,
    price
) VALUES (%s, %s, %s)
ON CONFLICT (block_timestamp) DO NOTHING;
"""

try:
    cur.execute(insert_sql, (
        datetime(2024, 12, 20, 0, 0, 0),  # Example timestamp
        280,  # Example net_holders
        104.73  # Example price
    ))
    conn.commit()
    print("Data inserted successfully!")
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
