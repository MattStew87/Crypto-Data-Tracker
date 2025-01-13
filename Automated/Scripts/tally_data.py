import requests
import os
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from graph_generator import GraphGenerator
import time 


class TallyData: 
    def __init__(self): 

        load_dotenv()
        self.tally_api_key = os.getenv("TALLY_API_KEY")

        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB",
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": "5432"
        }

        self.graph_generator = GraphGenerator() 

    def tally_daily_total_voting_power_by_choice(self, proposal_id, decimals):
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

        headers = {"Api-Key": self.tally_api_key}
        after_cursor = None
        daily_votes_by_amount = []  # List of tuples (date, type, total_amount)
        daily_votes_by_count = []  # List of tuples (date, type, voter_count)
        aggregated_amounts = defaultdict(lambda: defaultdict(int))  # {date: {type: total_amount}}
        aggregated_counts = defaultdict(lambda: defaultdict(int))  # {date: {type: voter_count}}

        while True:
            time.sleep(1) 
            variables = {
                "input": {
                    "filters": {
                        "proposalId": proposal_id,
                        "includePendingVotes": False  # Filter by proposal ID
                    },
                    "page": {
                        "limit": 100,  # Adjust as needed for batch size
                        "afterCursor": after_cursor  # Pagination cursor
                    },
                    "sort": {
                        "isDescending": True,
                        "sortBy": "id"  # Sort by proposal ID
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
                            # Normalize to the date and aggregate
                            date = datetime.fromisoformat(timestamp).date()
                            aggregated_amounts[date][decision] += amount / (10**decimals)
                            aggregated_counts[date][decision] += 1

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

        # Convert aggregated data to tuples
        for date, decisions in aggregated_amounts.items():
            for decision, total_amount in decisions.items():
                daily_votes_by_amount.append((date, decision, total_amount))

        for date, decisions in aggregated_counts.items():
            for decision, voter_count in decisions.items():
                daily_votes_by_count.append((date, decision, voter_count))
        
        daily_votes_by_amount = sorted(daily_votes_by_amount, key=lambda x: x[0])
        daily_votes_by_count = sorted(daily_votes_by_count, key=lambda x: x[0])

        # Makes the data cumulative
        def make_cumulative(data):
            cumulative_data = []
            cumulative_totals = defaultdict(int)

            for date, decision, value in data:
                cumulative_totals[decision] += value
                cumulative_data.append((date, decision, cumulative_totals[decision]))

            return cumulative_data

        daily_votes_by_amount = make_cumulative(daily_votes_by_amount) 
        daily_votes_by_count = make_cumulative(daily_votes_by_count) 

        voter_file_path = self.graph_generator.create_grouped_line_graph(daily_votes_by_count, 'Date', 'Total Voters', 'Daily Total Voters by Choice', 'tally_daily_total_voters_by_choice')
        voting_power_file_path = self.graph_generator.create_grouped_line_graph(daily_votes_by_amount, 'Date', 'Total Voting Power', 'Daily Total Voting Power by Choice', 'tally_daily_total_voting_power_by_choice')

        return voter_file_path, voting_power_file_path
    


    def tally_voting_power_by_wallet(self, proposal_id, decimals):
        """
        Categorizes wallets into voting power groups, counts wallets in each group,
        and calculates the total voting power per group.
        """
        url = "https://api.tally.xyz/query"
        query = """
        query ($input: VotesInput!) {
            votes(input: $input) {
                nodes {
                    ... on Vote {
                        amount
                    }
                }
                pageInfo {
                    lastCursor
                }
            }
        }
        """
        headers = {"Api-Key": self.tally_api_key}
        after_cursor = None

        # Define the groups
        voting_power_groups = defaultdict(lambda: {"wallets": 0, "voting_power": 0})

        def get_voting_power_group(amount):
            """
            Returns the group name based on the voting power.
            """
            if amount < 1:
                return "a/ below 1"
            elif amount < 10:
                return "b/ 1-10"
            elif amount < 100:
                return "c/ 10-100"
            elif amount < 1_000:
                return "d/ 100-1K"
            elif amount < 10_000:
                return "e/ 1K-10K"
            elif amount < 100_000:
                return "f/ 10K-100K"
            elif amount < 1_000_000:
                return "g/ 100K-1M"
            elif amount < 10_000_000:
                return "h/ 1M-10M"
            else:
                return "i/ 10M+"

        while True:
            time.sleep(1) 
            variables = {
                "input": {
                    "filters": {
                        "proposalId": proposal_id,
                        "includePendingVotes": False  # Filter by proposal ID
                    },
                    "page": {
                        "limit": 100,  # Adjust as needed for batch size
                        "afterCursor": after_cursor  # Pagination cursor
                    },
                    "sort": {
                        "isDescending": True,
                        "sortBy": "id"  # Sort by proposal ID
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
                        amount = int(vote.get("amount", 0)) / (10**decimals)
                        group = get_voting_power_group(amount)

                        voting_power_groups[group]["wallets"] += 1
                        voting_power_groups[group]["voting_power"] += amount

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

        # Prepare the results as lists of tuples
        wallets_list = [(group, data["wallets"]) for group, data in voting_power_groups.items()]
        voting_power_list = [(group, data["voting_power"]) for group, data in voting_power_groups.items()]

        # Sort results by group name
        wallets_list = sorted(wallets_list, key=lambda x: x[0])
        voting_power_list = sorted(voting_power_list, key=lambda x: x[0])

        voter_file_path = self.graph_generator.create_bar_chart(wallets_list, "Voting Power Group", "Wallets", 'Voters by Wallet Voting Power Group', 'tally_voters_by_wallet_voting_power_group')
        voting_power_file_path = self.graph_generator.create_bar_chart(voting_power_list, "Voting Power Group", "Voting Power", 'Voting Power by Wallet Voting Power Group', 'tally_voting_power_by_wallet_voting_power_group')

        return voter_file_path, voting_power_file_path




    
    def tally_space_proposals_by_voting_power(self, proposal_id, decimals, governor_id): 
        print("chciken")

    

if __name__ == "__main__": 
    tally_data_client = TallyData() 
    votes_count, votes_amount = tally_data_client.tally_voting_power_by_wallet(2499208639684806584, 18)
    print(f"Voting power: {votes_amount}")
    print(f"Voters: {votes_count}")