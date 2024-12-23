class InputHandler:
    def __init__(self, table_manager, mv_manager, alert_manager):
        """
        Initialize the InputHandler with a reference to the TableManager instance.
        :param table_manager: An instance of the TableManager.
        """
        self.table_manager = table_manager
        self.mv_manager = mv_manager
        self.alert_manager = alert_manager

    def raw_table_workflow(self):
        """
        Handles the workflow for creating raw tables and managing update queries.
        """
        # Step 1: Table name
        table_name = input("Table name: ").strip()

        # Step 2: Columns
        print("Enter columns in dictionary format (e.g., {'item1': 'TIMESTAMP', 'item2': 'int'}):")
        columns_input = input("Columns: ").strip()
        try:
            columns = eval(columns_input)  # Converts string input into dictionary
        except Exception:
            print("Invalid column format. Please use a dictionary format.")
            return

        # Step 3: Primary key
        primary_key = input("Primary key: ").strip()
        if primary_key not in columns:
            print(f"Primary key '{primary_key}' not found in columns.")
            return

        # Step 4: Create the table
        self.table_manager.create_raw_table(table_name, columns, primary_key)
        print("------------------------------------------------------------")
        print("------------------------------------------------------------")

        # Step 5: Notify the user about the next step
        print("Moving on to data insertion.")
        print(f"Table '{table_name}' has the following columns:")
        for col, dtype in columns.items():
            print(f"  - {col}: {dtype}")

        # Step 6: Input SQL Query
        print("\nEnter your SQL query for fetching data from Flipside (type 'END' to finish):")
        print("For example:")
        print("WITH tab1 AS (\n    SELECT ...\n)\nSELECT ...")
        print("END")
        print("\nSQL:")

        sql_query_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            sql_query_lines.append(line)

        sql_query = f"""{' '.join(sql_query_lines).strip()}"""

        # Step 7: Insert data into the table
        self.table_manager.insert_data_from_flipside(sql_query)
        print("------------------------------------------------------------")
        print("------------------------------------------------------------")

        # Step 8: Prompt user for update query
        print("Moving on to the update query.")
        print("Same format as data insertion query.")
        print("\nUpdate Query SQL:")

        sql_update_query_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            sql_update_query_lines.append(line)

        sql_update_query = f"""{' '.join(sql_update_query_lines).strip()}"""

        # Step 9: Register the update query
        self.table_manager.add_update_query(sql_update_query)

    def materialized_view_workflow(self):
        """
        Handles workflow for materialized view creation logic.
        """

        # Step 1: Enter table name
        table_name = input("Table name: ").strip()

        # Step 2: Enter SQL Query for materialized view
        print("Enter your SQL query for creating aggregate tables:")
        print("For example:")
        print("WITH tab1 AS (\n    SELECT ...\n)\nSELECT ...")
        print("END")
        print("\nSQL:")

        sql_query_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            sql_query_lines.append(line)

        sql_query = ' '.join(sql_query_lines).strip()

        # Step 3: Create the materialized view and add it to a list to be refreshed
        self.mv_manager.create_materialized_view(table_name, sql_query)
        self.mv_manager.add_mv_refresh() 

    def alerts_workflow(self):
        """
        Handles the workflow for creating alerts.
        """
        print("Managing Alerts")

        # Step 1: Alert name
        alert_name = input("Enter the name of the alert: ").strip()

        # Step 2: Alert SQL
        print("Enter the SQL query for the alert (must evaluate to TRUE or FALSE):")
        print("END your query with the word 'END'.")
        print("\nSQL:")

        sql_query_lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            sql_query_lines.append(line)

        alert_sql = ' '.join(sql_query_lines).strip()

        # Step 3: Twitter Info
        twitter_info = input("Enter Twitter script (optional, leave blank if not applicable): ").strip()

        # Step 4: AI Prompt Info
        ai_prompt_info = input("Enter AI prompt (optional, leave blank if not applicable): ").strip()

        # Step 5: SQL Queries List
        print("Enter additional SQL queries for the alert (one at a time, END to finish):")
        additional_queries = []
        while True:
            query = input("SQL Query: ").strip()
            if query.upper() == "END":
                break
            additional_queries.append(query)

        # Step 6: Register the alert with all parameters
        self.alert_manager.create_alert(alert_name, alert_sql, twitter_info, ai_prompt_info, additional_queries)
