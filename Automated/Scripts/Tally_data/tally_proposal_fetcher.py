import requests
import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime, timedelta
from psycopg2 import extras
import time 

class TallyProposalFetcher: 

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

        self.space_keys = [{'space': 'Uniswap', 'governor_id': 'eip155:1:0x408ED6354d4973f66138C91495F2f2FCbd8724C3'}, 
                           {'space': 'Arbitrum', 'governor_id': 'eip155:42161:0xf07DeD9dC292157749B6Fd268E37DF6EA38395B9'},
                           {'space': 'Compound', 'governor_id': 'eip155:1:0xc0Da02939E1441F497fd74F78cE7Decb17B66529'},
                           {'space': 'Dope Wars', 'governor_id': 'eip155:1:0xDBd38F7e739709fe5bFaE6cc8eF67C3820830E0C'},
                           {'space': 'Lil Nouns', 'governor_id': 'eip155:1:0x5d2C31ce16924C2a71D317e5BbFd5ce387854039'},
                           {'space': 'Nouns Dao', 'governor_id': 'eip155:1:0x6f3E6272A167e8AcCb32072d08E0957F9c79223d'},
                           {'space': 'PoolTogether', 'governor_id': 'eip155:1:0x8a907De47E00830a2b742db65e938a3ea1070A2E'},
                           {'space': 'Rari Dao', 'governor_id': 'eip155:1:0x6552C8fb228f7776Fc0e4056AA217c139D4baDa1'},
                           {'space': 'Unlock Dao', 'governor_id': 'eip155:8453:0x65bA0624403Fc5Ca2b20479e9F626eD4D78E0aD9'},
                           {'space': 'InstaDapp', 'governor_id': 'eip155:1:0x0204Cd037B2ec03605CFdFe482D8e257C765fA1B'},
                           {'space': 'Idle Dao', 'governor_id': 'eip155:1:0x3D5Fc645320be0A085A32885F078F7121e5E5375'},
                           {'space': 'Cryptex', 'governor_id': 'eip155:1:0x874C5D592AfC6803c3DD60d6442357879F196d5b'},
                           {'space': 'Optimism', 'governor_id': 'eip155:10:0xcDF27F107725988f2261Ce2256bDfCdE8B382B10'},
                           {'space': 'ZKsync', 'governor_id': 'eip155:324:0x76705327e682F2d96943280D99464Ab61219e34f'},
                           {'space': 'Aave', 'governor_id': 'eip155:1:0xEC568fffba86c094cf06b22134B23074DFE2252c'},
                           {'space': 'ENS', 'governor_id': 'eip155:1:0x323A76393544d5ecca80cd6ef2A560C6a395b7E3'},
                            {'space': 'Gitcoin', 'governor_id': 'eip155:1:0x9D4C63565D5618310271bF3F3c01b2954C1D1639'},
                            {'space': 'Hop', 'governor_id': 'eip155:1:0xed8Bdb5895B8B7f9Fdb3C087628FD8410E853D48'},
                            {'space': 'GMX', 'governor_id': 'eip155:42161:0x03e8f708e9C85EDCEaa6AD7Cd06824CeB82A7E68'},
                            {'space': 'Realtoken', 'governor_id': 'eip155:100:0x4A5327347f077E72d2AaB19F68Ba8A7F12ec5d63'},
                           {'space': 'Lisk', 'governor_id': 'eip155:1135:0x58a61b1807a7bDA541855DaAEAEe89b1DDA48568'},
                            {'space': 'Diva Staking', 'governor_id': 'eip155:1:0xFb6B7C11a55C57767643F1FF65c34C8693a11A70'},
                            {'space': 'Open Dollar', 'governor_id': 'eip155:42161:0xf704735CE81165261156b41D33AB18a08803B86F'},
                           {'space': 'Fei', 'governor_id': 'eip155:1:0x0BEF27FEB58e857046d630B2c03dFb7bae567494'},
                           {'space': 'SpellsDao', 'governor_id': 'eip155:1:0x2f8da73e52Ec56FeB0aE63FBDD50c01dd04E8CC9'},
                           {'space': 'Moonwell', 'governor_id': 'eip155:1284:0xfc4DFB17101A12C5CEc5eeDd8E92B5b16557666d'},
                           {'space': 'HAI', 'governor_id': 'eip155:10:0xe807f3282f3391d237BA8B9bECb0d8Ea3ba23777'},
                           {'space': 'Ondo Dao', 'governor_id': 'eip155:1:0x336505EC1BcC1A020EeDe459f57581725D23465A'},
                           {'space': 'Seamless', 'governor_id': 'eip155:8453:0x8768c789C6df8AF1a92d96dE823b4F80010Db294'}
                           ]


    def fetch_proposals(self):

        final_result = []
        
        for space in self.space_keys: 
            time.sleep(1) 
            space_name = space['space']
            governor_id = space['governor_id']

            url = "https://api.tally.xyz/query"

            # GraphQL query to fetch proposals with BlocklessTimestamp only
            query = """
            query ($input: ProposalsInput!) {
                proposals(input: $input) {
                    nodes {
                        ... on Proposal {
                            id
                            metadata {
                                title
                                description 
                            }
                            status
                            start {
                                ... on Block {
                                    timestamp
                                }
                            }
                            end {
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
                        firstCursor
                        lastCursor
                        count
                    }
                }
            }
            """
            
            headers = {"Api-Key": self.tally_api_key}
            after_cursor = None
            proposals = []

            while True:
                variables = {
                    "input": {
                        "filters": {
                            "governorId": f"{governor_id}"  # Filter by governor ID
                        },
                        "page": {
                            "limit": 10,  # Maximum items per page
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
                        proposals.extend(nodes)

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
            
            final_result.append({'proposals': proposals, 'space_name': space_name})


        return final_result


    def insert_proposals(self):
            try:
                data = self.fetch_proposals() 

                # Connect to the PostgreSQL database
                with psycopg2.connect(**self.db_config) as conn:
                    with conn.cursor() as cursor:
                        for item in data:
                            space_name = item['space_name'] 
                            for proposal in item['proposals']:
                                if proposal['status'] == 'active': 
                                    # Extract fields from the proposal
                                    proposal_id = proposal['id']
                                    proposal_title = proposal['metadata'].get('title', '')
                                    proposal_description = proposal['metadata'].get('description', '')
                                    status = proposal['status']
                                    start_time = proposal['start']['timestamp']
                                    end_time = proposal['end']['timestamp']
                                    vote_stats = proposal.get('voteStats', [])

                                    # Insert into the database
                                    sql_insert = """
                                    INSERT INTO tally_gov_proposals (
                                        proposal_id,
                                        proposal_title,
                                        proposal_description,
                                        status,
                                        start_time,
                                        end_time,
                                        voteStats, 
                                        space_name
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (proposal_id) DO NOTHING
                                    """
                                    cursor.execute(
                                        sql_insert,
                                        (
                                            proposal_id,
                                            proposal_title,
                                            proposal_description,
                                            status,
                                            start_time,
                                            end_time,
                                            psycopg2.extras.Json(vote_stats),  # Store voteStats as JSONB
                                            space_name
                                        )
                                    )
                    conn.commit()
                    print(f"Inserted proposals into the database.")
            except Exception as db_error:
                print(f"Database error: {db_error}")

if __name__ == "__main__": 
    tally_client = TallyProposalFetcher()
    tally_client.insert_proposals()
