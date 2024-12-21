from table_manager import TableManager
from update_registry import UpdateRegistry
from input_handler import InputHandler

def main():
    print("Welcome to the Data Manager!")

    registry = UpdateRegistry()
    table_manager = TableManager(registry)
    input_handler = InputHandler(table_manager)

    while True:
        print("\nChoose an operation:")
        print("1. Manage Raw Tables")
        print("2. Manage Materialized Views")
        print("3. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            input_handler.raw_table_workflow()
        elif choice == "2":
            input_handler.materialized_view_workflow()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
