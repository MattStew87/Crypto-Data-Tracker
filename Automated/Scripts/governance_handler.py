
import json
import psycopg2
import os
from dotenv import load_dotenv
from openai import OpenAI
from snapshot_handler import SnapshotHandler
from tally_handler import TallyHandler

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
        self.tally_handler = TallyHandler() 

        # Resolve the path to snapshot_proposals.json dynamically
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_file_path = os.path.join(script_dir, "../config/snapshot_proposals.json")  


    def get_new_proposals(self): 
            proposals = []
            try:
                # Connect to the PostgreSQL database
                with psycopg2.connect(**self.db_config) as conn:
                    with conn.cursor() as cursor:
                        sql_query = """
                            WITH snapshot_proposals as (
                                SELECT 
                                    proposal_id, 
                                    proposal_title, 
                                    CASE 
                                        WHEN NOW() BETWEEN proposal_start_time AND proposal_start_time + INTERVAL '1 DAY' THEN 'Announcement'
                                        WHEN NOW() BETWEEN proposal_start_time + (proposal_end_time - proposal_start_time) / 2 
                                                    AND proposal_start_time + (proposal_end_time - proposal_start_time) / 2 + INTERVAL '1 DAY' THEN 'Halftime'
                                        WHEN NOW() BETWEEN proposal_end_time AND proposal_end_time + INTERVAL '1 DAY' THEN 'Final'
                                        ELSE NULL
                                    END AS stage, 
                                    'SNAPSHOT' as Platform
                                FROM snapshot_gov_proposals
                                WHERE space_id IN (
                                    'arbitrumfoundation.eth', 'aave.eth', 'ens.eth', 'apecoin.eth', 'balancer.eth',
                                    'lido-snapshot.eth', 'cvx.eth', 'starknet.eth', 'safe.eth', 'stgdao.eth',
                                    'uniswapgovernance.eth', 'gitcoindao.eth', 'gmx.eth', 'speraxdao.eth', 'shellprotocol.eth',
                                    'sushigov.eth', 'radiantcapital.eth', 'beets.eth', 'hop.eth', 'frax.eth',
                                    'shapeshiftdao.eth', 'acrossprotocol.eth', 'rocketpool-dao.eth', 'comp-vote.eth', 'devdao.eth',
                                    'abracadabrabymerlinthemagician.eth', 'morpho.eth', 'symbiosisdao.eth', 'vote.vitadao.eth', 'stakewise.eth',
                                    'prismafinance.eth', 'metislayer2.eth', 'g-dao.eth', 'equilibriafi.eth', 'beaverbuilder.eth',
                                    'aavegotchi.eth', 'moonwell-governance.eth', 'worldlibertyfinancial.com', 'etherfi-dao.eth',
                                    'moxie.eth', 'snapshot.dcl.eth', 'sandboxdao.eth', 'magicappstore.eth', 'metfi.io',
                                    'the-arena.eth', 'dfkvote.eth', 'polyhedragovernance.eth', 'rdatadao.eth',
                                    'mendifinance.eth', 'gracy.eth', 'toshibase.eth', 'magpiexyz.eth',
                                    'gyrodao.eth', 'cow.eth', 'beefydao.eth', 'latticegov.eth',
                                    'thegurudao.eth', 'mocana.eth', 'gameswiftdao.eth', 'bioxyz.eth',
                                    'dao.spaceid.eth', 'gauges.aurafinance.eth', 'wayfinderfoundation.eth', 'degen-defi.eth', 'madebyapesvote.eth',
                                    'hyperlockfi.eth', '1inch.eth', 'extradao.eth', 'octantapp.eth', 'xborg.eth',
                                    'somonowo.eth', 'gearbox.eth', 'eventhorizongitcoin.eth', 'airdaofoundation.eth', 'jadeprotocol.eth',
                                    'gnosis.eth'
                                )  
                            ), 

                            tally_proposals as (
                            Select 
                                proposal_id, 
                                proposal_title, 
                                CASE 
                                    WHEN NOW() BETWEEN start_time AND start_time + INTERVAL '1 DAY' THEN 'Announcement'
                                    WHEN NOW() BETWEEN start_time + (end_time - start_time) / 2 
                                                AND start_time + (end_time - start_time) / 2 + INTERVAL '1 DAY' THEN 'Halftime'
                                    WHEN NOW() BETWEEN end_time AND end_time + INTERVAL '1 DAY' THEN 'Final'
                                    ELSE NULL
                                END AS stage, 
                                'TALLY' as Platform
                            from tally_gov_proposals 
                            ) 

                            SELECT 
                            * 
                            FROM snapshot_proposals 
                            WHERE stage IS NOT NULL 

                            UNION ALL 
                                
                            SELECT 
                            * 
                            FROM tally_proposals 
                            WHERE stage IS NOT NULL 
                        """
                        cursor.execute(sql_query)
                        raw_data = cursor.fetchall()

                        # Column names in lower case and in order
                        columns = [
                            "proposal_id", 
                            "proposal_title",
                            "stage", 
                            "platform"
                        ]
                        
                        # Convert each row into a dictionary
                        for row in raw_data:
                            proposals.append(dict(zip(columns, row)))

            except Exception as db_error:
                print(f"Database connection error: {db_error}")

            return proposals
    

    def select_best_proposal(self):
        """
        Sends a list of proposals to ChatGPT, selects the most interesting one based on the title,
        fetches full details from the appropriate database, updates the JSON file, and returns the selected proposal.
        """

        proposals = self.get_new_proposals()  # Get the proposals

        try:
            # Load existing data or initialize an empty structure
            if os.path.exists(self.json_file_path) and os.path.getsize(self.json_file_path) > 0:
                with open(self.json_file_path, "r") as file:
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
                "Here is a list of governance proposals:\n\n"
                f"{filtered_proposals}\n\n"
                "Each dictionary represents a proposal. Based on the title, "
                "return the index (0-based) of the most interesting proposal as a single number."
            )

            # Call ChatGPT to get the index
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Return the index of the most interesting proposal as a single number."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10  # Small token limit since we only need the index
            )

            # Extract the response content
            selected_index = response.choices[0].message.content.strip()

            # Validate the selected index
            if not selected_index.isdigit():
                print(f"Invalid index returned by ChatGPT: {selected_index}")
                return None

            selected_index = int(selected_index)  # Convert to integer

            if not (0 <= selected_index < len(filtered_proposals)):
                print(f"Index out of range: {selected_index}")
                return None

            # Retrieve the selected proposal using the index
            selected_proposal = filtered_proposals[selected_index]
            selected_proposal_id = selected_proposal["proposal_id"]

            # Fetch full details of the selected proposal based on the platform
            platform = selected_proposal["platform"]
            if platform == "SNAPSHOT":
                query = f"""
                    SELECT 
                        proposal_id,
                        proposal_title,
                        proposal_text,
                        choices,
                        created_at,
                        proposal_start_time,
                        proposal_end_time,
                        network,
                        space_id,
                        date_added
                    FROM snapshot_gov_proposals
                    WHERE proposal_id = %s
                """
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
                    "date_added"
                ]
            elif platform == "TALLY":
                query = f"""
                    SELECT 
                        proposal_id,
                        proposal_title,
                        proposal_description,
                        start_time, 
                        end_time,
                        space_name,
                        governor_id,
                        decimals
                    FROM tally_gov_proposals
                    WHERE proposal_id = %s
                """
                columns = [
                    "proposal_id",
                    "proposal_title",
                    "proposal_description",
                    "start_time",
                    "end_time",
                    "space_name",
                    "governor_id",
                    "decimals"
                ]
            else:
                print(f"Unknown platform: {platform}")
                return None

            # Execute the query and fetch data
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (selected_proposal_id,))
                    result = cursor.fetchone()

            if not result:
                print(f"No data found for proposal_id: {selected_proposal_id}")
                return None

            # Convert result to a dictionary
            full_proposal_details = dict(zip(columns, result))

            # Update the JSON file
            stage = selected_proposal["stage"]
            data[stage].append(selected_proposal_id)

            with open(self.json_file_path, "w") as file:
                json.dump(data, file, indent=4)

            return {"proposal": full_proposal_details, "stage": stage, "platform": platform}

        except Exception as e:
            print(f"An error occurred during proposal selection: {e}")
            return {} 


    
    def execute_proposal(self): 
        selected_proposal = self.select_best_proposal() 
        if not selected_proposal:
            print("No proposal selected for execution.")
            return
        
        proposal = selected_proposal["proposal"]
        platform = selected_proposal["platform"]
        stage = selected_proposal["stage"]
        if platform == 'SNAPSHOT': 
            if stage == 'Announcement': 
                self.snapshot_handler.create_proposal_announcement(proposal)
            elif stage == 'Halftime':
                self.snapshot_handler.create_proposal_halftime(proposal)
            elif stage == 'Final':
                self.snapshot_handler.create_proposal_final(proposal)  
        elif platform == 'TALLY': 
            if stage == 'Announcement': 
                self.tally_handler.create_proposal_announcement(proposal)
            elif stage == 'Halftime':
                self.tally_handler.create_proposal_halftime(proposal)
            elif stage == 'Final':
                self.tally_handler.create_proposal_final(proposal) 
        else:
            print("Stage was not on of the following stages ['SNAPSHOT', 'TALLY']")        
    


if __name__ == "__main__": 
    gov_hanlder = GovernanceHandler() 
    gov_hanlder.execute_proposal() 
   
    
 
