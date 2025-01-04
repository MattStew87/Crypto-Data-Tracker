import tweepy
import os
from dotenv import load_dotenv


class TwitterHandler:
    def __init__(self):
        """
        Initializes TwitterHandler with authentication for both API v1.1 and v2.
        """
        # Load environment variables
        load_dotenv()

        # API keys and tokens
        consumer_key = os.getenv("X_API_KEY")
        consumer_secret = os.getenv("X_API_SECRET")
        access_token = os.getenv("X_ACCESS_TOKEN")
        access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

        # Authenticate to API v1.1 (for media uploads)
        auth = tweepy.OAuth1UserHandler(
            consumer_key, consumer_secret, access_token, access_token_secret
        )
        self.api_v1 = tweepy.API(auth)

        # Authenticate to API v2 (for tweet creation)
        self.api_v2 = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

    def upload_media(self, media_path):
        """
        Uploads media to Twitter (API v1.1) and returns the media ID.
        :param media_path: Path to the media file.
        :return: media_id (str)
        """
        try:
            print(f"Uploading media: {media_path}")
            response = self.api_v1.media_upload(media_path)
            print(f"Media uploaded successfully: {response.media_id_string}")
            return response.media_id_string
        except Exception as e:
            print(f"Error uploading media: {e}")
            return None
        
    
    def post_with_media(self, text, media_path):
        """
        Creates a tweet with media and tags users on the media.
        :param text: Text of the tweet.
        :param media_path: Path to the media file.
        :return: Tweet ID (str) if successful, None otherwise.
        """
        media_id = self.upload_media(media_path)
        if not media_id:
            print("Failed to upload media. Aborting post.")
            return None

        try:
            print(f"Creating tweet with media: {text}")
            response = self.api_v2.create_tweet(
                text=text,
                media_ids=[media_id],
                user_auth=True
            )
            tweet_id = response.data["id"]
            print(f"Tweet created successfully: {tweet_id}")
            return tweet_id
        except Exception as e:
            print(f"Error creating tweet: {e}")
            return None
    
    def post_thread_reply(self, text, reply_to_tweet_id):
        """
        Creates a reply in a thread 
        :param text: Text of the tweet.
        :param reply_to_tweet_id: Tweet ID of the tweet being replied to.
        :return: Tweet ID (str) if successful, None otherwise.
        """

        try:
            print(f"Creating thread reply to {reply_to_tweet_id}: {text}")
            response = self.api_v2.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to_tweet_id,
                user_auth=True
            )
            tweet_id = response.data["id"]
            print(f"Thread reply created successfully: {tweet_id}")
            return tweet_id
        except Exception as e:
            print(f"Error creating thread reply: {e}")
            return None


    def post_thread_reply_with_media(self, text, media_paths, reply_to_tweet_id):
        """
        Creates a reply in a thread with one or more media attachments.
        :param text: Text of the tweet.
        :param media_paths: A list of file paths (strings) to the media you want to attach.
        :param reply_to_tweet_id: Tweet ID of the tweet being replied to.
        :return: Tweet ID (str) if successful, None otherwise.
        """
        media_ids = []

        # Upload each media file and collect media_ids
        for path in media_paths:
            m_id = self.upload_media(path)
            if m_id:
                media_ids.append(m_id)
            else:
                print(f"Failed to upload media: {path}. Aborting thread reply.")
                return None

        try:
            print(f"Creating thread reply to {reply_to_tweet_id} with text: {text}")
            response = self.api_v2.create_tweet(
                text=text,
                media_ids=media_ids,  # pass the entire list
                in_reply_to_tweet_id=reply_to_tweet_id,
                user_auth=True
            )
            tweet_id = response.data["id"]
            print(f"Thread reply created successfully: {tweet_id}")
            return tweet_id
        except Exception as e:
            print(f"Error creating thread reply: {e}")
            return None

