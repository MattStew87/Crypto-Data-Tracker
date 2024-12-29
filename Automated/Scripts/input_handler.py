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
        print("\n" + "=" * 40)
        print("📊 Raw Table Creation Workflow")
        print("=" * 40 + "\n")

        # Step 1: Table name
        print("Step 1: Enter the Table Name")
        table_name = input("🔹 Table Name: ").strip()

        # Step 2: Columns
        print("\nStep 2: Define Table Columns")
        print("💡 Enter columns in dictionary format:")
        print("   Example: {'item1': 'TIMESTAMP', 'item2': 'int'}")
        print("-" * 40)
        columns_input = input("🔹 Columns: ").strip()
        
        try:
            columns = eval(columns_input)  # Converts string input into dictionary
        except Exception:
            print("❌ Invalid column format. Please use a dictionary format.")
            return

        # Step 3: Primary key
        print("\nStep 3: Specify Primary Key")
        primary_key = input("🔹 Primary Key: ").strip()
        
        if primary_key not in columns:
            print(f"❌ Primary key '{primary_key}' not found in columns.")
            return

        # Step 4: Create the table
        print("\n" + "=" * 40)
        print("📝 Creating Table...")
        self.table_manager.create_raw_table(table_name, columns, primary_key)
        
        # Step 5: Display table information
        print("\n📋 Table Structure Summary")
        print(f"Table Name: {table_name}")
        print("Columns:")
        for col, dtype in columns.items():
            print(f"  ▪️ {col}: {dtype}")
        
        # Step 6: Input SQL Query
        print("\nStep 6: Enter Data Insertion Query")
        print("💡 Enter your SQL query for fetching data from Flipside")
        print("   Type 'END' on a new line when finished")
        print("-" * 40)
        
        sql_query_lines = []
        while True:
            line = input()
            if line.upper().strip() == "END":
                break
            sql_query_lines.append(line)
        
        sql_query = f"""{' '.join(sql_query_lines).strip()}"""
        
        # Step 7: Insert data
        print("\n" + "=" * 40)
        print("📥 Inserting Data...")
        self.table_manager.insert_data_from_flipside(sql_query)
        
        # Step 8: Update query
        print("\nStep 8: Define Update Query")
        print("💡 Enter the SQL query for updates")
        print("   Type 'END' on a new line when finished")
        print("-" * 40)
        
        sql_update_query_lines = []
        while True:
            line = input()
            if line.upper().strip() == "END":
                break
            sql_update_query_lines.append(line)
        
        sql_update_query = f"""{' '.join(sql_update_query_lines).strip()}"""
        
        # Step 9: Register update query
        print("\n" + "=" * 40)
        print("📝 Registering Update Query...")
        self.table_manager.add_update_query(sql_update_query)
        print("✅ Workflow completed successfully!")
        print("=" * 40)

    def materialized_view_workflow(self):
        """
        Handles workflow for materialized view creation with a user-friendly interface.
        """
        print("\n" + "=" * 40)
        print("📊 Welcome to the Materialized View Workflow 📊")
        print("=" * 40 + "\n")

        # Step 1: Enter Table Name
        print("Step 1: Enter the Name of the Table for the Materialized View")
        table_name = input("🔹 Table Name: ").strip()

        # Step 2: Enter SQL Query
        print("\nStep 2: Define the SQL Query for the Materialized View")
        print("💡 Use a valid SQL query to create aggregate tables or views.")
        print("   Type your query line by line, and type 'END' to finish.")
        print("   Example:\n")
        print("   WITH tab1 AS (")
        print("       SELECT ...")
        print("   )")
        print("   SELECT ...")
        print("-" * 40)

        sql_query_lines = []
        while True:
            line = input() 
            if line.upper().strip() == "END":
                break
            sql_query_lines.append(line)

        sql_query = ' '.join(sql_query_lines).strip()

        # Step 3: Create the Materialized View
        print("\n" + "=" * 40)
        print(f"📋 Creating the Materialized View for Table: {table_name}")
        self.mv_manager.create_materialized_view(table_name, sql_query)
        self.mv_manager.add_mv_refresh()
        print(f"✅ Materialized View '{table_name}' created successfully!")
        print("=" * 40)


    def alerts_workflow(self):
        """
        Handles the workflow for creating alerts with a user-friendly interface.
        """
        print("\n" + "=" * 40)
        print("🚨 Welcome to the Alerts Workflow 🚨")
        print("=" * 40 + "\n")

        # Step 1: Alert name
        print("Step 1: Enter the Name of Your Alert")
        alert_name = input("🔹 Alert Name: ").strip()

        # Step 2: Alert SQL
        print("\nStep 2: Define the Alert Condition (SQL Query)")
        print("💡 The SQL query must evaluate to TRUE or FALSE.")
        print("   Type your query line by line, and type 'END' to finish.")
        print("-" * 40)

        sql_query_lines = []
        while True:
            line = input()
            if line.upper().strip() == "END":
                break
            sql_query_lines.append(line)

        alert_sql = ' '.join(sql_query_lines).strip()

        # Step 3: AI Prompt Info
        print("\nStep 3: (Optional) Add an AI Prompt")
        print("💡 If this alert involves AI processing, provide a prompt.")
        print("   Leave blank if not applicable.")
        ai_prompt_info = input("🔹 AI Prompt: ").strip()

        # Step 3: Twitter Prompt Info
        print("\nStep 4: (Optional) Add an Twitter Prompt")
        print("💡 If this alert involves Twitter processing, provide a prompt.")
        print("   Leave blank if not applicable.")
        twitter_prompt_info = input("🔹 Twitter Prompt: ").strip()

        # Step 4: Additional SQL Queries
        print("\nStep 5: (Optional) Add Additional SQL Queries")
        print("💡 Enter queries to fetch more data for this alert.")
        print("   Type each query one at a time, and type 'END' to finish.")
        print("-" * 40)

        additional_queries = []
        while True:
            query = input("SQL Query> ").strip()
            if query.upper() == "END":
                break
            additional_queries.append(query)

        # Step 5: Register the Alert
        print("\n" + "=" * 40)
        print("📋 Registering Your Alert...")
        self.alert_manager.create_alert(alert_name, alert_sql, ai_prompt_info, additional_queries, twitter_prompt_info)
        print(f"✅ Alert '{alert_name}' registered successfully!")
        print("=" * 40)

