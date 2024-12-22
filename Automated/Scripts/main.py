from table_manager import TableManager
from mv_manager import MvManager
from alert_manager import AlertManager
from update_registry import UpdateRegistry
from input_handler import InputHandler

def main():
    print("Welcome to the Data Manager!")

    registry = UpdateRegistry()
    table_manager = TableManager(registry)
    mv_manager = MvManager(registry)
    alert_manager = AlertManager(registry)
    input_handler = InputHandler(table_manager, mv_manager, alert_manager)

    while True:
        print("\nChoose an operation:")
        print("1. Manage Raw Tables")
        print("2. Manage Materialized Views")
        print("3. Manage Alerts")
        print("4. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            input_handler.raw_table_workflow()
        elif choice == "2":
            input_handler.materialized_view_workflow()
        elif choice == "3":
            input_handler.alerts_workflow()
        elif choice == "4":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
