import os
from dotenv import load_dotenv
from twitter_handler import TwitterHandler
import psycopg2
from openai import OpenAI
import json
from dao_twitter_responder import DAOTwitterResponder

class CommentHandler: 

    def __init__(self): 
        load_dotenv() 
        
        self.twitter_handler = TwitterHandler() 

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB", 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }

        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_file_path = os.path.join(script_dir, "../config/current_tweet.json")

        self.dao_twitter_responder = DAOTwitterResponder() 


    def add_comments_to_db(self): 
        
        try: 
            tweet_id = self.get_tweet_id()["tweet_id"]
            comments = self.twitter_handler.get_comments_on_post(tweet_id) 
            if not comments: 
                 print("There are no comments to add")
                 return 
            
            with psycopg2.connect(**self.db_config) as conn: 
                with conn.cursor() as cursor: 

                    query = """
                    INSERT INTO twitter_comments (id, text, responded)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                    """

                    cursor.executemany(query, comments) 

                    conn.commit()
                    print(f"Inserted {cursor.rowcount} comments into the database.")
                    
                         
        except Exception as e:
            print(f"Error in store_comments(): {e}")

    

    def respond_to_comments(self): 
        """
        Fetches all comments with the responded field set to FALSE.
        :return: List of unresponded comments as tuples (id, text, responded).
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    # SQL query to select comments where responded is FALSE
                    query = """
                    SELECT id, text, responded
                    FROM twitter_comments
                    WHERE responded = FALSE;
                    """

                    cursor.execute(query)
                    comments = cursor.fetchall()

                    # SQL query to update already selected 
                    update_query = """
                        UPDATE twitter_comments
                        SET responded = TRUE
                        WHERE responded = FALSE;
                    """

                    cursor.execute(update_query)
            
            # returns information about the orignal post
            post_data = self.get_tweet_id() 
            
            for comment in comments:
                reply = self.dao_twitter_responder.generate_response(comment[1], f"Response to {post_data['proposal_title']} from {post_data['dao_name']}")
            
                #self.twitter_handler.post_thread_reply(reply, comment[0])
                
                print(reply) 
                    
                    

        except Exception as e:
            print(f"Error fetching unresponded comments: {e}")


    def set_tweet_id(self, tweet_id, proposal_title, dao_name):
        """
        Overwrites the JSON file with the given tweet data.
        
        :param tweet_id: The tweet ID to save.
        :param text: The content of the tweet.
        :param proposal_title: The title of the DAO proposal.
        :param dao_name: The name of the DAO.
        """
        data = {
            "tweet_id": tweet_id,
            "proposal_title": proposal_title,
            "dao_name": dao_name
        }

        try:
            with open(self.json_file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Tweet data saved successfully: {data}")
        except Exception as e:
            print(f"Error writing to {self.json_file_path}: {e}") 


    def get_tweet_id(self):
        """
        Retrieves the tweet_id from the JSON file.
        :return: The tweet ID if it exists, otherwise None.
        """
        try:
            with open(self.json_file_path, 'r') as json_file:
                data = json.load(json_file)
            return data
        except FileNotFoundError:
            print(f"File {self.json_file_path} not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {self.json_file_path}.")
            return None
        except Exception as e:
            print(f"Error reading from {self.json_file_path}: {e}")
            return None
            





if __name__ == "__main__": 
    client = CommentHandler()
    client.respond_to_comments() 
    



'''
client.add_comments_to_db("1882522791687209138") 

1. Add set_tweet_id() at the end of every create Tweet

'''