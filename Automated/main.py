from table_manager import TableManager

def main():
    print("Welcome to the Table Manager!")

    # Initialize TableManager
    table_manager = TableManager()

    # Step 1: Table name
    table_name = input("Table name: ").strip()

    # Step 2: Columns
    print("Enter columns in dictionary format (e.g., {'item1': 'TIMESTAMP', 'item2': 'int'}):")
    columns_input = input("Columns: ").strip()
    try:
        columns = eval(columns_input)  # Converts string input into dictionary
    except Exception as e:
        print("Invalid column format. Please use a dictionary format.")
        return

    # Step 3: Primary key
    primary_key = input("Primary key: ").strip()
    if primary_key not in columns:
        print(f"Primary key '{primary_key}' not found in columns.")
        return

    # Step 4: Create the table
    table_manager.create_raw_table(table_name, columns, primary_key)

    # Step 5: Notify the user about the next step
    print("\nMoving on to data insertion.")
    print(f"Table '{table_name}' has the following columns:")
    for col, dtype in columns.items():
        print(f"  - {col}: {dtype}")

    # Step 6: Input SQL Query
    print("\nEnter your SQL query for fetching data from Flipside (type 'END' to finish):")
    print("For example:")
    print("WITH tab1 AS (\n    SELECT ...\n)\nSELECT ...")
    print("End your query with 'END'.")

    sql_query_lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        sql_query_lines.append(line)

    # Combine the query lines and wrap them in triple quotes
    sql_query = f"""{' '.join(sql_query_lines).strip()}"""

    # Step 7: Insert data into the table
    table_manager.insert_data_from_flipside(sql_query)

if __name__ == "__main__":
    main()
