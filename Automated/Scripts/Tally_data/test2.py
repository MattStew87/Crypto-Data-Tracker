import requests
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

def fetch_votes(api_key, proposal_id):
    url = "https://api.tally.xyz/query"
    query = """
    query ($input: VotesInput!) {
        votes(input: $input) {
            nodes {
                ... on Vote {
                    amount
                    type
                    block {
                        timestamp
                    }
                }
            }
            pageInfo {
                lastCursor
            }
        }
    }
    """

    headers = {"Api-Key": api_key}
    after_cursor = None
    daily_vote_summary = defaultdict(lambda: defaultdict(int))  # {date: {decision: total_voting_power}}

    while True:
        variables = {
            "input": {
                "filters": {
                    "proposalId": proposal_id  # Filter by proposal ID
                },
                "page": {
                    "limit": 50,  # Adjust as needed for batch size
                    "afterCursor": after_cursor  # Pagination cursor
                }
            }
        }

        try:
            response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
            if response.status_code == 200:
                data = response.json()
                page = data.get("data", {}).get("votes", {})
                nodes = page.get("nodes", [])
                if not nodes:
                    break

                for vote in nodes:
                    amount = int(vote.get("amount", 0))
                    decision = vote.get("type", "UNKNOWN")
                    timestamp = vote.get("block", {}).get("timestamp")
                    
                    if timestamp:
                        # Parse the timestamp and extract the date
                        date = datetime.fromisoformat(timestamp).date()
                        daily_vote_summary[date][decision] += amount

                # Handle pagination
                after_cursor = page.get("pageInfo", {}).get("lastCursor")
                if not after_cursor:
                    break
            else:
                print(f"Query failed with status {response.status_code}: {response.text}")
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    return daily_vote_summary

# Load API key from .env file
load_dotenv()
api_key = os.getenv("TALLY_API_KEY")

# Fetch and process votes for the given proposal ID
proposal_id = 2496846462550280093
daily_vote_summary = fetch_votes(api_key, proposal_id)

# Print daily vote summary
if daily_vote_summary:
    print("Daily Vote Summary:")
    for date, decisions in sorted(daily_vote_summary.items()):
        print(f"Date: {date}")
        for decision, total_voting_power in decisions.items():
            print(f"  Decision: {decision}, Total Voting Power: {total_voting_power}")
        print("-" * 50)
else:
    print("No votes found.")
