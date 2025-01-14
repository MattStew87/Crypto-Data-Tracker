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

        return [voter_file_path, voting_power_file_path]
    


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

        return [voter_file_path, voting_power_file_path]


    def tally_space_proposals_by_voting_power(self, proposal_id, decimals, governor_id):
        url = "https://api.tally.xyz/query"

        # GraphQL query to fetch proposals
        query = """
        query ($input: ProposalsInput!) {
            proposals(input: $input) {
                nodes {
                    ... on Proposal {
                        id
                        block {
                            timestamp
                        }
                        start {
                            ... on Block {
                                timestamp
                            }
                        }
                        voteStats {
                            type
                            votesCount
                            votersCount
                            percent
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
        proposal_tuples_by_voting_power = []
        proposal_tuples_by_voters = []

        while True:
            time.sleep(1)
            variables = {
                "input": {
                    "filters": {
                        "governorId": f"{governor_id}"  # Filter by governor ID
                    },
                    "page": {
                        "limit": 100,  # Maximum items per page
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
                    page = data.get("data", {}).get("proposals", {})
                    nodes = page.get("nodes", [])

                    # Process each proposal
                    for proposal in nodes:
                        # Extract relevant data
                        prop_id = proposal.get("id")
                        block = proposal.get("block", {}).get("timestamp")
                        start_time = proposal.get("start", {}).get("timestamp", block) 

                        # Default to block timestamp if start time is missing
                        start_time = datetime.fromisoformat(start_time).date()

                        # Process voteStats
                        vote_stats = proposal.get("voteStats", [])
                        total_voting_power = sum(int(vote.get("votesCount", 0)) / (10**decimals) for vote in vote_stats if vote["type"] in ["for", "against", "abstain"])
                        total_voters_count = sum(int(vote.get("votersCount", 0)) for vote in vote_stats if vote["type"] in ["for", "against", "abstain"])

                        # Determine proposal type
                        proposal_type = "Selected Proposal" if prop_id == proposal_id else "Other Proposal"

                        # Add to tuples
                        proposal_tuples_by_voting_power.append((start_time, proposal_type, total_voting_power))
                        proposal_tuples_by_voters.append((start_time, proposal_type, total_voters_count))

                    # Handle pagination
                    after_cursor = page.get("pageInfo", {}).get("lastCursor")
                    if not after_cursor:
                        break  # Exit loop if no more pages
                else:
                    print(f"Query failed with status {response.status_code}: {response.text}")
                    break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        voter_file_path = self.graph_generator.create_grouped_scatter_graph(proposal_tuples_by_voters, "Start Time", "Total Voters", 'Space Proposals by Voters', 'tally_space_proposals_by_voters')
        voting_power_file_path = self.graph_generator.create_grouped_scatter_graph(proposal_tuples_by_voting_power, "Start Time", "Total Voting Power", 'Space Proposals by Voting Power', 'tally_space_proposals_by_voting_power')

        return [voter_file_path, voting_power_file_path]
    
    
    def get_top_voters_info(self, proposal_id, decimals):
        """
        Calculate the number of wallets needed to make up the top 10% and 50% of total voting power.
        :param proposal_id: ID of the proposal.
        :param decimals: Number of decimals for normalization.
        :return: A dictionary with top 10% and 50% wallet counts.
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

        wallet_voting_powers = []

        while True:
            time.sleep(1)
            variables = {
                "input": {
                    "filters": {
                        "proposalId": proposal_id,
                        "includePendingVotes": False
                    },
                    "page": {
                        "limit": 200,
                        "afterCursor": after_cursor
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
                        amount = int(vote.get("amount", 0)) / (10 ** decimals)
                        wallet_voting_powers.append(amount)

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

        # Sort voting powers in descending order
        wallet_voting_powers.sort(reverse=True)

        total_power = sum(wallet_voting_powers)

        def calculate_top_percent(percent):
            threshold = percent * total_power
            cumulative = 0
            for i, power in enumerate(wallet_voting_powers, start=1):
                cumulative += power
                if cumulative >= threshold:
                    return i
            return len(wallet_voting_powers)

        return {
            "top_10%_voting_power_wallets": calculate_top_percent(0.1),
            "top_50%_voting_power_wallets": calculate_top_percent(0.5)
        }

    

    def prompt_stats(self, proposal_id, decimals, governor_id):
        url = "https://api.tally.xyz/query"

        # GraphQL query to fetch proposals
        query = """
        query ($input: ProposalsInput!) {
            proposals(input: $input) {
                nodes {
                    ... on Proposal {
                        id    
                        voteStats {
                            type
                            votesCount
                            votersCount
                            percent
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

        # Variables for rank calculation
        proposals_voting_power = []
        proposals_voter_turnout = []

        # Final data for the specific proposal
        proposal_data = {}

        while True:
            time.sleep(1)
            variables = {
                "input": {
                    "filters": {
                        "governorId": f"{governor_id}"  # Filter by governor ID
                    },
                    "page": {
                        "limit": 100,  # Maximum items per page
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
                    page = data.get("data", {}).get("proposals", {})
                    nodes = page.get("nodes", [])

                    for proposal in nodes:
                        prop_id = proposal.get("id")
                        vote_stats = proposal.get("voteStats", [])
                        total_voting_power = sum(
                            int(vote.get("votesCount", 0)) / (10 ** decimals)
                            for vote in vote_stats
                            if vote["type"] in ["for", "against", "abstain"]
                        )
                        total_voters_count = sum(
                            int(vote.get("votersCount", 0))
                            for vote in vote_stats
                            if vote["type"] in ["for", "against", "abstain"]
                        )

                        proposals_voting_power.append((prop_id, total_voting_power))
                        proposals_voter_turnout.append((prop_id, total_voters_count))

                        if prop_id == proposal_id:
                            # Identify the top choices and their stats
                            valid_votes = [vote for vote in vote_stats if vote["type"] in ["for", "against", "abstain"]]
                            sorted_votes = sorted(valid_votes, key=lambda x: int(x.get("votesCount", 0)), reverse=True)

                            if sorted_votes:
                                winning_option = sorted_votes[0]
                                second_choice = sorted_votes[1] if len(sorted_votes) > 1 else None

                                proposal_data = {
                                    "1st_choice_voting_power": int(winning_option.get("votesCount", 0)) / (10 ** decimals),
                                    "1st_choice_name": winning_option["type"],
                                    "leading_percent": winning_option.get("percent", 0),
                                    "total_voters": total_voters_count,
                                    "2nd_choice_name": second_choice["type"] if second_choice else None,
                                    "2nd_choice_voting_power": int(second_choice.get("votesCount", 0)) / (10 ** decimals) if second_choice else None
                                }

                                # Call the helper method to add top voter metrics
                                top_voters_info = self.get_top_voters_info(proposal_id, decimals)
                                proposal_data.update(top_voters_info)

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

        # Calculate rank and percentile
        proposals_voting_power.sort(key=lambda x: x[1], reverse=True)
        proposals_voter_turnout.sort(key=lambda x: x[1], reverse=True)

        voting_power_rank = next((i + 1 for i, (pid, _) in enumerate(proposals_voting_power) if pid == proposal_id), None)
        voter_turnout_rank = next((i + 1 for i, (pid, _) in enumerate(proposals_voter_turnout) if pid == proposal_id), None)

        if voting_power_rank is not None:
            proposal_data["voting_power_rank"] = voting_power_rank
            proposal_data["voting_power_percentile"] = 100 - (voting_power_rank - 1) / len(proposals_voting_power) * 100

        if voter_turnout_rank is not None:
            proposal_data["voter_turnout_rank"] = voter_turnout_rank
            proposal_data["voter_percentile"] = 100 - (voter_turnout_rank - 1) / len(proposals_voter_turnout) * 100

        return proposal_data





    

if __name__ == "__main__": 
    tally_data_client = TallyData() 
    result = tally_data_client.prompt_stats('2499208639684806584', 18, 'eip155:42161:0xf07DeD9dC292157749B6Fd268E37DF6EA38395B9')
    print(f"Result: {result}")


