import json
import psycopg2
from dotenv import load_dotenv
import os
import anthropic

class AlertProcessor:
    def __init__(self, json_file_path="../config/triggered_alerts.json"):
        """
        Initializes the AlertProcessor.
        :param json_file_path: Path to the triggered_alerts.json file.
        """
        load_dotenv()  # Load environment variables
        self.json_file_path = json_file_path
        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB", 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def read_alerts(self):
        """
        Reads and returns the raw alerts from the JSON file.
        :return: Dictionary of raw alert data.
        """
        try:
            with open(self.json_file_path, "r") as json_file:
                alerts = json.load(json_file)
            return alerts
        except Exception as e:
            print(f"Error reading JSON file: {e}")
            return {}

    def execute_queries(self, queries):
        """
        Executes a list of SQL queries and returns the results labeled as query1, query2, etc.
        :param queries: List of SQL queries to execute.
        :return: Dictionary with labeled query results.
        """
        results = {}
        try:
            # Connect to the PostgreSQL database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    for idx, query in enumerate(queries, start=1):
                        try:
                            # Wrap the query in triple quotes for consistency
                            formatted_sql = f"""{query}"""
                            cursor.execute(formatted_sql)
                            query_results = cursor.fetchall()
                            results[f"query{idx}"] = query_results
                        except Exception as query_error:
                            print(f"Error executing query {idx}: {query_error}")
        except Exception as e:
            print(f"Database connection error: {e}")
        return results

    def process_ai_prompt(self, ai_prompt, query_results):
        """
        Processes the AI prompt with the relevant query results using the Claude API.
        :param ai_prompt: AI prompt string.
        :param query_results: Dictionary of labeled query results.
        :return: Claude's response to the AI prompt.
        """
        try:
            # Prepare results as a formatted string
            formatted_results = "\n".join(
                [f"{key}:\n{result}" for key, result in query_results.items()]
            )
            prompt = f"{ai_prompt}\n\nRelevant Data:\n{formatted_results}"

            # Send the prompt to Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content
        except Exception as e:
            print(f"Error communicating with the Claude API: {e}")
            return None

    def process_alerts(self):
        """
        Main method to process alerts from the JSON file.
        """
        alerts = self.read_alerts()
        for alert_name, metadata in alerts.items():
            print(f"Processing {alert_name}...")

            # Access the actual metadata dictionary
            metadata = metadata["metadata"]

            # Step 1: Execute SQL queries
            additional_queries = metadata.get("additional_queries", [])
            query_results = self.execute_queries(additional_queries)

            if not query_results:
                print(f"No data returned for {alert_name}, skipping AI prompt processing.")
                continue

            # Step 2: Process AI prompt
            ai_prompt = metadata.get("ai_prompt_info", "")
            if ai_prompt:
                # Prepare and debug AI prompt
                formatted_results = "\n".join(
                    [f"{key}:\n{result}" for key, result in query_results.items()]
                )

                # Process AI prompt
                ai_response = self.process_ai_prompt(ai_prompt, query_results)
                print(f"AI Response for {alert_name}: {ai_response}")



# Example usage
if __name__ == "__main__":
    processor = AlertProcessor()
    processor.process_alerts()
