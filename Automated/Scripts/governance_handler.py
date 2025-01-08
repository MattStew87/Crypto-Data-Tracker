
import json
import psycopg2
import os
from dotenv import load_dotenv
from openai import OpenAI
from snapshot_handler import SnapshotHandler

class GovernanceHandler: 
    def __init__(self): 
        load_dotenv() 

        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB", 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.snapshot_handler = SnapshotHandler() 

        self.selected_proposal = self.select_best_proposal() 



    def get_new_proposals(self): 
            proposals = []
            try:
                # Connect to the PostgreSQL database
                with psycopg2.connect(**self.db_config) as conn:
                    with conn.cursor() as cursor:
                        sql_query = """
                        WITH relevant_proposals as (
                            SELECT 
                            *, 
                            'Announcement' as stage
                            FROM snapshot_new_proposals 

                            UNION ALL 
                                
                            SELECT 
                            *, 
                            'Halftime' as stage
                            FROM snapshot_gov_proposals
                            WHERE NOW() BETWEEN 
                            proposal_start_time + (proposal_end_time - proposal_start_time) / 2
                            AND 
                            proposal_start_time + (proposal_end_time - proposal_start_time) / 2 + INTERVAL '1 DAY'
                            
                            UNION ALL 

                            SELECT 
                            *, 
                            'Final' as stage
                            FROM snapshot_gov_proposals
                            WHERE NOW() BETWEEN  proposal_end_time AND proposal_end_time + INTERVAL '1 DAY'
                            ) 

                            SELECT * 

                            FROM relevant_proposals 
                            WHERE space_id IN (
                                'arbitrumfoundation.eth', 'aave.eth', 'ens.eth', 'apecoin.eth', 'balancer.eth',
                                'lido-snapshot.eth', 'cvx.eth', 'starknet.eth', 'safe.eth', 'stgdao.eth',
                                'uniswapgovernance.eth', 'gitcoindao.eth', 'gmx.eth', 'speraxdao.eth', 'shellprotocol.eth',
                                'sushigov.eth', 'radiantcapital.eth', 'beets.eth', 'hop.eth', 'frax.eth',
                                'shapeshiftdao.eth', 'acrossprotocol.eth', 'rocketpool-dao.eth', 'comp-vote.eth', 'devdao.eth',
                                'abracadabrabymerlinthemagician.eth', 'morpho.eth', 'symbiosisdao.eth', 'vote.vitadao.eth', 'stakewise.eth',
                                'prismafinance.eth', 'metislayer2.eth', 'g-dao.eth', 'equilibriafi.eth', 'beaverbuilder.eth',
                                'aavegotchi.eth', 'evergrow-lucro-governance.eth', 'moonwell-governance.eth', 'worldlibertyfinancial.com', 'etherfi-dao.eth',
                                'moxie.eth', 'snapshot.dcl.eth', 'sandboxdao.eth', 'magicappstore.eth', 'metfi.io',
                                'the-arena.eth', 'dfkvote.eth', 'polyhedragovernance.eth', 'hvax.eth', 'rdatadao.eth',
                                'mendifinance.eth', 'gracy.eth', 'toshibase.eth', 'magpiexyz.eth', 'mutantcatsvote.eth',
                                'gyrodao.eth', 'cow.eth', 'beefydao.eth', 'latticegov.eth', 'selfkey.eth',
                                'thegurudao.eth', 'mocana.eth', 'gameswiftdao.eth', 'bioxyz.eth', 'sdao.eth',
                                'dao.spaceid.eth', 'gauges.aurafinance.eth', 'wayfinderfoundation.eth', 'degen-defi.eth', 'madebyapesvote.eth',
                                'hyperlockfi.eth', '1inch.eth', 'extradao.eth', 'octantapp.eth', 'xborg.eth',
                                'somonowo.eth', 'gearbox.eth', 'eventhorizongitcoin.eth', 'airdaofoundation.eth', 'jadeprotocol.eth',
                                'gnosis.eth'
                            ) 
                        """
                        cursor.execute(sql_query)
                        raw_data = cursor.fetchall()

                        # Column names in lower case and in order
                        columns = [
                            "proposal_id", 
                            "proposal_title",
                            "proposal_text",
                            "choices",
                            "created_at",
                            "proposal_start_time",
                            "proposal_end_time",
                            "network",
                            "space_id",
                            "date_added",
                            "stage"
                        ]
                        
                        # Convert each row into a dictionary
                        for row in raw_data:
                            proposals.append(dict(zip(columns, row)))

            except Exception as db_error:
                print(f"Database connection error: {db_error}")

            return proposals

    def select_best_proposal(self):
            """
            Sends the list of proposals to ChatGPT, dynamically excludes proposals based on their stage and proposal_id,
            validates the index, updates the JSON file, and returns the corresponding proposal.
            """

            proposals = self.get_new_proposals()

            # Load the existing JSON file to get previously selected proposals
            json_file_path = "../config/snapshot_proposals.json"

            try:
                # Load existing data or initialize an empty structure
                if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
                    with open(json_file_path, "r") as file:
                        data = json.load(file)
                else:
                    # If the file is missing or empty, initialize the structure
                    data = {
                        "Announcement": [],
                        "Halftime": [],
                        "Final": []
                    }

                # Filter out proposals already selected for their respective stage
                filtered_proposals = [
                    proposal for proposal in proposals
                    if proposal["proposal_id"] not in data.get(proposal["stage"], [])
                ]

                if not filtered_proposals:
                    print("No new proposals available for selection.")
                    return None

                # Prompt for ChatGPT
                prompt = (
                    "Here is a list of governance proposals as dictionaries:\n\n"
                    f"{filtered_proposals}\n\n"
                    "Each dictionary represents a proposal. Based on the details provided, "
                    f"select the index (0-based) of the proposal you think is the best / most interesting."
                    "Only return the index as an integer (e.g., 0, 1, 2)."
                )

                # Call ChatGPT to get the index
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Return the best proposal's index as an integer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=10  # Small token limit since we only need the index
                )

                # Extract the response content
                selected_index = response.choices[0].message.content.strip()

                # Validate and process the index
                if selected_index.isdigit():
                    selected_index = int(selected_index)  # Convert to integer
                    if 0 <= selected_index < len(filtered_proposals):  # Check if index is valid
                        selected_proposal = filtered_proposals[selected_index]
                        proposal_id = selected_proposal["proposal_id"]
                        stage = selected_proposal["stage"]
            
                        data[stage].append(proposal_id)

                        # Write the updated data back to the JSON file
                        with open(json_file_path, "w") as file:
                            json.dump(data, file, indent=4)

                        return selected_proposal  # Return the selected proposal
                    else:
                        print(f"Index out of range: {selected_index}")
                else:
                    print(f"Invalid index format returned by ChatGPT: {selected_index}")

            except Exception as e:
                print(f"An error occurred during proposal selection: {e}")

            return None  # Return None if selection failed
    
    def execute_proposal(self): 

        stage = self.selected_proposal["stage"]
        if stage == 'Announcement': 
            self.snapshot_handler.create_proposal_announcement(self.selected_proposal)
        elif stage == 'Halftime':
            self.snapshot_handler.create_proposal_halftime(self.selected_proposal)
        elif stage == 'Final':
            self.snapshot_handler.create_proposal_final(self.selected_proposal)  


if __name__ == "__main__": 
    gov_hanlder = GovernanceHandler() 
    gov_hanlder.execute_proposal() 