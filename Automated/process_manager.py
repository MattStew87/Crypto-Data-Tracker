import time
import schedule
from update_registry import UpdateRegistry

def run_updates():
    """
    Function to execute updates for all registered tables.
    """
    print("run_updates has been called")
    registry = UpdateRegistry()
    registry.execute_updates()

def start_process_manager():
    """
    Schedule the updates to run daily and keep the process running.
    """
    # Schedule the update function to run every day at midnight
    schedule.every().day.at("00:00").do(run_updates)

    print("\nProcess Manager started. Updates will run daily at midnight.")
    
    # Keep the script running to check for scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(300)  # Wait to prevent high CPU usage

if __name__ == "__main__":
    start_process_manager()
