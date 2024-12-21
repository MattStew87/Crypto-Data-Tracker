import psycopg2
from dotenv import load_dotenv
import os
from flipside import Flipside

class TableManager:
    def __init__(self):
        """
        Initialize the TableManager and load database credentials.
        """
        load_dotenv()
        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB",
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": "5432"
        }
        # Initialize metadata for the table
        self.table_name = None
        self.columns = None
        self.primary_key = None

    def connect(self):
        """
        Create a connection to the PostgreSQL database.
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            return None

    def create_raw_table(self, table_name, columns, primary_key):
        """
        Create a raw table in PostgreSQL.
        """
        # Update table metadata
        self.table_name = table_name
        self.columns = columns
        self.primary_key = primary_key

        # Build the CREATE TABLE SQL command
        column_definitions = ", ".join([f"{col} {dtype}" for col, dtype in self.columns.items()])
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            {column_definitions},
            PRIMARY KEY ({self.primary_key})
        );
        """
        try:
            conn = self.connect()
            if conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
                    conn.commit()
                    print(f"Table {self.table_name} created successfully!")
        except Exception as e:
            print(f"Error creating table: {e}")
        finally:
            if conn:
                conn.close()

    def insert_data_from_flipside(self, sql_query):
        """
        Fetch data from Flipside's API and insert it into the table.
        :param sql_query: SQL query to execute on Flipside.
        """
        if not self.table_name or not self.columns or not self.primary_key:
            print("Table metadata is not set. Create the table first.")
            return

        flipside = Flipside(os.getenv("FLIPSIDE_API_KEY"), "https://api-v2.flipsidecrypto.xyz")

        try:
            # Run the query against Flipside's query engine
            query_result_set = flipside.query(sql_query, page_number=1, page_size=1)

            all_rows = []
            current_page_number = 1
            total_pages = 2

            # Fetch data page by page
            while current_page_number <= total_pages:
                results = flipside.get_query_results(
                    query_result_set.query_id,
                    page_number=current_page_number,
                    page_size=1000
                )
                total_pages = results.page.totalPages
                if results.records:
                    all_rows.extend(results.records)
                current_page_number += 1

            # Insert data into the database
            conn = self.connect()
            if conn:
                with conn.cursor() as cur:
                    columns = ", ".join(self.columns.keys())
                    placeholders = ", ".join(["%s"] * len(self.columns))
                    insert_sql = f"""
                    INSERT INTO {self.table_name} ({columns})
                    VALUES ({placeholders})
                    ON CONFLICT ({self.primary_key}) DO NOTHING;
                    """
                    for row in all_rows:
                        cur.execute(insert_sql, tuple(row[col] for col in self.columns.keys()))
                    conn.commit()
                    print(f"Data inserted successfully into {self.table_name}!")
        except Exception as e:
            print(f"Error fetching or inserting data: {e}")
        finally:
            if conn:
                conn.close()
