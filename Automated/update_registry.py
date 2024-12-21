import psycopg2
from flipside import Flipside
from dotenv import load_dotenv
import os
import json

class UpdateRegistry:
    """
    Manages the registration and execution of update queries for tables.
    """

    def __init__(self, registry_file="update_registry.json"):
        """
        Initializes the registry and loads existing updates from a JSON file if available.
        :param registry_file: Path to the JSON file storing the registry.
        """
        load_dotenv()
        self.registry_file = registry_file
        self.registry = self.load_updates()

    def load_updates(self):
        """
        Load the update registry from the JSON file.
        :return: A dictionary containing the loaded registry data.
        """
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r") as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error loading registry file: {e}")
                return {}
        return {}

    def save_updates(self):
        """
        Save the current registry to the JSON file.
        """
        try:
            with open(self.registry_file, "w") as file:
                json.dump(self.registry, file, indent=4)
        except Exception as e:
            print(f"Error saving registry file: {e}")

    def register_table_update(self, table_name, update_query, db_config, columns, primary_key):
        """
        Register a table and its update query and save it to the JSON file.
        :param table_name: Name of the table to update.
        :param update_query: SQL query for updating the table.
        :param db_config: Database configuration.
        :param columns: Dictionary of column names and their data types.
        :param primary_key: Primary key of the table.
        """
        self.registry[table_name] = {
            "update_query": update_query,
            "db_config": db_config,
            "columns": columns,
            "primary_key": primary_key
        }
        self.save_updates()
        print(f"Table '{table_name}' update query registered.")

    def execute_updates(self):
        """
        Execute the update query for each registered table.
        """
        for table_name, details in self.registry.items():
            update_query = f"""{details["update_query"]}"""
            db_config = details["db_config"]
            columns = details["columns"]
            primary_key = details["primary_key"]

            flipside = Flipside(os.getenv("FLIPSIDE_API_KEY"), "https://api-v2.flipsidecrypto.xyz")
            try:
                query_result_set = flipside.query(update_query, page_number=1, page_size=1)
                all_rows = []
                current_page_number = 1
                total_pages = 2

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

                conn = psycopg2.connect(**db_config)
                if conn:
                    with conn.cursor() as cur:
                        col_names = ", ".join(columns.keys())
                        placeholders = ", ".join(["%s"] * len(columns))
                        insert_sql = f"""
                        INSERT INTO {table_name} ({col_names})
                        VALUES ({placeholders})
                        ON CONFLICT ({primary_key}) DO NOTHING;
                        """
                        for row in all_rows:
                            cur.execute(insert_sql, tuple(row[col] for col in columns.keys()))
                        conn.commit()
                        print(f"Update for table '{table_name}' executed successfully!")
            except Exception as e:
                print(f"Error updating table '{table_name}': {e}")
            finally:
                if conn:
                    conn.close()
