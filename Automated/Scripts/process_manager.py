import time
import schedule
from update_registry import UpdateRegistry
from governance_handler import GovernanceHandler
from comment_handler import CommentHandler
from datetime import datetime

def run_updates():
    """
    Function to execute updates for all registered tables.
    """
    try:
        print('--------------------------------------------------------------------')
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"run_updates called at {current_time} \n")
        registry = UpdateRegistry()
        registry.execute_updates()
        print('--------------------------------------------------------------------\n\n')
    except Exception as e:
        print(f"Error in run_updates: {e}")

def run_tweet():
    """
    Function to execute the governance proposal handling.
    """
    try:
        print('#######################################################################################################################')
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"run_tweet called at {current_time} \n")
        governance_handler = GovernanceHandler()
        governance_handler.execute_proposal()
        print('#######################################################################################################################\n\n')
    except Exception as e:
        print(f"Error in run_tweet: {e}")

def process_comments():
    """
    Function to fetch comments from Twitter and respond to them.
    Runs every 15 minutes.
    """
    try:
        print('===========================================================================================================')
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"process_comments called at {current_time} \n")
        comment_handler = CommentHandler()
        comment_handler.add_comments_to_db()
        comment_handler.respond_to_comments()
        print('===========================================================================================================\n\n')
    except Exception as e:
        print(f"Error in process_comments: {e}")

def start_process_manager():
    """
    Run updates immediately and keep the process running for testing.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Process Manager started at: {current_time}")

    # Schedule the updates to run every day at 6:00 PM local time
    schedule.every().day.at("18:00").do(run_updates)

    # Schedule tweets to run every 2 hours
    schedule.every(2).hours.do(run_tweet)

    # Schedule comment processing every 15 minutes
    schedule.every(15).minutes.do(process_comments)

    while True:
        schedule.run_pending()
        time.sleep(300)  # Wait to prevent high CPU usage

if __name__ == "__main__":
    start_process_manager()
