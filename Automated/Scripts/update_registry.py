import psycopg2
from flipside import Flipside
from dotenv import load_dotenv
import os
import json
from alert_processor import AlertProcessor


class UpdateRegistry:
    """
    Manages the registration and execution of update queries for tables and materialized views.
    """

    def __init__(self, registry_file="../config/update_registry.json", mv_registry_file="../config/materialized_views.json", alert_registry_file="../config/alerts.json"):
        """
        Initializes the registries and loads existing updates from JSON files if available.
        :param registry_file: Path to the JSON file storing the update registry.
        :param mv_registry_file: Path to the JSON file storing materialized view names.
        """
        load_dotenv()
        self.registry_file = registry_file
        self.mv_registry_file = mv_registry_file
        self.alert_registry_file = alert_registry_file
        self.registry = self.load_json(self.registry_file)  # Registry for table updates
        self.materialized_views = self.load_json(self.mv_registry_file)  # List of materialized views
        self.alerts = self.load_json(self.alert_registry_file)

    def load_json(self, file_path):
        """
        Load a JSON file and return its contents.
        :param file_path: Path to the JSON file.
        :return: Dictionary containing the loaded data or empty list/dict if not found.
        """
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    return json.load(file)
            except Exception as e:
                print(f"Error loading JSON file {file_path}: {e}")
        return [] if "mv_registry_file" in file_path else {}

    def save_json(self, file_path, data):
        """
        Save a dictionary or list to a JSON file.
        :param file_path: Path to the JSON file.
        :param data: Data to save.
        """
        try:
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {e}")

    def register_table_update(self, table_name, update_query, columns, primary_key):
        """
        Register a table and its update query, then save it to the JSON file.
        :param table_name: Name of the table to update.
        :param update_query: SQL query for updating the table.
        :param columns: Dictionary of column names and their data types.
        :param primary_key: Primary key of the table.
        """

        self.registry[table_name] = {
            "update_query": update_query,
            "columns": columns,
            "primary_key": primary_key
        }
        self.save_json(self.registry_file, self.registry)
        print(f"Table '{table_name}' update query registered.")

    def register_materialized_view(self, mv_name):
        """
        Register a materialized view name and save it to the JSON file.
        :param mv_name: Name of the materialized view.
        """
        if mv_name not in self.materialized_views:
            self.materialized_views.append(mv_name)
            self.save_json(self.mv_registry_file, self.materialized_views)
            print(f"Materialized view '{mv_name}' registered.")

    def register_alert(self, alert_name, alert_sql, metadata):
        """
        Registers an alert in the registry.
        :param alert_name: Name of the alert.
        :param alert_sql: SQL query that evaluates to TRUE or FALSE.
        :param metadata: Metadata containing AI prompt and additional SQL queries.
        """
        if alert_name not in self.alerts:
            self.alerts[alert_name] = {
                "alert_sql": alert_sql,
                "metadata": metadata
            }
        else:
            print(f"Alert '{alert_name}' already exists. Updating existing alert.")
            self.alerts[alert_name].update({
                "alert_sql": alert_sql,
                "metadata": metadata
            })

        # Save the updated registry to the JSON file
        self.save_json(self.alert_registry_file, self.alerts)


    def execute_updates(self):
        """
        Execute the update query for each registered table and refresh all materialized views.
        """
        # Load database configuration from .env once
        load_dotenv()
        db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB",
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": "5432"
        }

        try:
            # Establish a single database connection
            with psycopg2.connect(**db_config) as conn:
                with conn.cursor() as cur:
                    # Loop through all registered tables and execute updates
                    for table_name, details in self.registry.items():
                        update_query = f"""{details["update_query"]}"""
                        columns = details["columns"]
                        primary_key = details["primary_key"]

                        flipside = Flipside(
                            os.getenv("FLIPSIDE_API_KEY"), 
                            "https://api-v2.flipsidecrypto.xyz"
                        )
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

                    # Refresh all registered materialized views
                    for mv_name in self.materialized_views:
                        cur.execute(f"REFRESH MATERIALIZED VIEW {mv_name};")
                        conn.commit()
                        print(f"Materialized view '{mv_name}' refreshed successfully!")
                    

                    # Evaluate alerts
                    for alert_name, alert_data in self.alerts.items():
                        try:
                            # Extract alert SQL and metadata
                            alert_sql = alert_data.get("alert_sql", "")
                            metadata = alert_data.get("metadata", {})

                            # Dynamically wrap the SQL in triple quotes for consistency
                            formatted_sql = f"""{alert_sql}"""
                            cur.execute(formatted_sql)
                            result = cur.fetchone()

                            if result and result[0]:  # Check if the alert condition is TRUE
                                # Prepare the triggered alert as a dictionary
                                triggered_alert = {alert_name: metadata}

                                # Pass the triggered alert to the AlertProcessor
                                processor = AlertProcessor()
                                processor.process_alert(triggered_alert)

                        except Exception as e:
                            print(f"Error checking alert '{alert_name}': {e}")

        except Exception as e:
            print(f"Error executing updates: {e}")


