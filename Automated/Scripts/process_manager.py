import time
import schedule
from update_registry import UpdateRegistry
from datetime import datetime, timedelta, timezone

def run_updates():
    """
    Function to execute updates for all registered tables.
    """
    try:
        print("run_updates has been called")
        registry = UpdateRegistry()
        registry.execute_updates()
    except Exception as e:
        print(f"Error in run_updates: {e}")

def get_utc_midnight_local():
    """
    Calculate the local time equivalent of midnight UTC.
    """
    now = datetime.now(timezone.utc)
    utc_midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    local_midnight = utc_midnight.astimezone().replace(tzinfo=None)  # Convert to local time without timezone
    return local_midnight.strftime("%H:%M")  # Format as HH:MM

def start_process_manager():
    """
    Run updates immediately and keep the process running for testing.
    """

    # Get the local time equivalent of midnight UTC
    midnight_utc_local = get_utc_midnight_local()
    print(f"Scheduling updates for midnight UTC (local time: {midnight_utc_local})")
    
    # Schedule the update
    schedule.every().day.at(midnight_utc_local).do(run_updates)

    while True:
        schedule.run_pending()
        time.sleep(300)  # Wait to prevent high CPU usage

if __name__ == "__main__":
    start_process_manager()
