import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import uuid
import os
from dotenv import load_dotenv
import time


class DAOForumScraper:
    def __init__(self, qdrant_host="http://localhost:6333", collection_name="dao_forum_collection"):
        """Initialize the DAO scraper with OpenAI and Qdrant configurations."""
        load_dotenv() 

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_host = qdrant_host
        self.collection_name = collection_name
        self.chunk_size = 3000
        self.max_threads = 5

        # Ensure the Qdrant collection exists
        self.create_qdrant_collection()

    def safe_request(self, method, url, retries=3, **kwargs):
        """Wrapper for requests with retries and timeout handling."""
        for attempt in range(retries):
            try:
                response = requests.request(method, url, timeout=10, **kwargs)
                response.raise_for_status()
                return response  # Return response if successful
            except requests.Timeout:
                print(f"Timeout error on attempt {attempt+1}/{retries} for {url}")
            except requests.RequestException as e:
                print(f"Request error on attempt {attempt+1}/{retries}: {e}")
            time.sleep(1)  # Wait before retrying
        return None  # Return None after all retries fail


    def create_qdrant_collection(self):
        """Ensure the collection exists in Qdrant."""
        url = f"{self.qdrant_host}/collections/{self.collection_name}"
        payload = {"vectors": {"size": 1536, "distance": "Cosine"}}
        response = requests.put(url, json=payload)
        if response.status_code in [200, 201]:
            print(f"Collection '{self.collection_name}' is ready.")
        else:
            print(f"Failed to create or access the collection: {response.text}")

    def get_embedding(self, text):
        """Get OpenAI embeddings for a given text."""
        embeddings = []
        parts = [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]
        
        for part in parts:
            try:
                response = self.client.embeddings.create(model="text-embedding-ada-002", input=part)
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                print(f"Error embedding text: {e}")
                return None
        return embeddings

    def fetch_json(self, url):
        """Fetch JSON data from a given URL with error handling."""
        response = self.safe_request("GET", url)
        if response:
            return response.json()  # Return valid JSON response
        return None  # Return None if request failed


    def fetch_all_categories(self, base_url):
        """Fetch all categories from the DAO forum."""
        url = f"{base_url}/categories.json"
        data = self.fetch_json(url)
        return [cat.get("id") for cat in data.get("category_list", {}).get("categories", [])] if data else []

    def fetch_category_topics(self, base_url, category_id):
        """Fetch topics from a specific category."""
        url = f"{base_url}/c/{category_id}.json"
        topics = []
        while url:
            data = self.fetch_json(url)
            if data:
                topics.extend(data.get("topic_list", {}).get("topics", []))
                url = data.get("topic_list", {}).get("more_topics_url")
                if url:
                    url = f"{base_url}{url}"
            else:
                break
        return topics

    def fetch_topic_posts(self, base_url, topic_id):
        """Fetch all posts from a topic."""
        url = f"{base_url}/t/{topic_id}.json"
        data = self.fetch_json(url)
        return data.get("post_stream", {}).get("posts", []) if data else []

    def iso_to_epoch_milliseconds(self, iso_timestamp):
        """Convert ISO 8601 timestamp to epoch time in milliseconds."""
        try:
            dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
            epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
            return int((dt - epoch).total_seconds() * 1000)
        except Exception as e:
            print(f"Error converting timestamp: {iso_timestamp}, error: {e}")
            return None

    def record_exists(self, dao_name, topic_id, comment_id):
        """Check if a record with the same metadata exists in Qdrant."""
        url = f"{self.qdrant_host}/collections/{self.collection_name}/points/scroll"
        query = {
            "filter": {
                "must": [
                    {"key": "dao_name", "match": {"value": dao_name}},
                    {"key": "topic_id", "match": {"value": topic_id}},
                    {"key": "comment_id", "match": {"value": comment_id}},
                ]
            },
            "limit": 1
        }
        response = self.safe_request("POST", url, json=query)
        if response:
            points = response.json().get("result", {}).get("points", [])
            return len(points) > 0
        return False

    def upload_to_qdrant(self, post, topic, dao, base_url):
        """Upload a post's metadata and embedding to Qdrant."""
        content = post.get("cooked", "").replace("\n", " ")
        combined_text = f"Topic: {topic['title']}\nAuthor: {post['username']}\nComment: {content}"
        embeddings = self.get_embedding(combined_text)
        
        if embeddings is None:
            print(f"Skipping upload for {topic['title']} due to embedding error.")
            return

        epoch_timestamp = self.iso_to_epoch_milliseconds(post.get("created_at", ""))
        vector_id = str(uuid.uuid4())

        if self.record_exists(dao, topic["id"], post["id"]):
            print(f"Record already exists for DAO: {dao}, Topic ID: {topic['id']}, Comment ID: {post['id']}. Skipping...")
            return  # Skip duplicate

        for idx, embedding in enumerate(embeddings):
            payload = {
                "points": [{
                    "id": vector_id,
                    "vector": embedding,
                    "payload": {
                        "dao_name": dao,
                        "comment_id": post["id"],
                        "content": content,
                        "part_index": idx,
                        "author": post["username"],
                        "topic_id": topic["id"],
                        "topic_title": topic["title"],
                        "timestamp": epoch_timestamp,
                        "source_url": f"{base_url}/t/{topic['id']}",
                    },
                }]
            }
            self.safe_request("PUT", f"{self.qdrant_host}/collections/{self.collection_name}/points", json=payload)
            

    def process_topic(self, dao_name, base_url, topic):
        """Process a single topic."""
        topic_id = topic.get("id")
        topic_title = topic.get("title", "Unknown Title")
        print(f"Processing topic: {topic_title} (ID: {topic_id})")
        posts = self.fetch_topic_posts(base_url, topic_id)

        for post in posts:
            self.upload_to_qdrant(post, topic, dao_name, base_url)

    def process_dao(self, dao_name, base_url):
        """Process a DAO forum."""
        print(f"Processing DAO: {dao_name}")
        categories = self.fetch_all_categories(base_url)
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for category_id in categories:
                topics = self.fetch_category_topics(base_url, category_id)
                for topic in topics:
                    executor.submit(self.process_topic, dao_name, base_url, topic)

    def run(self):
        """Start processing DAOs in parallel."""

        dao_list = [
            {"name": "Gitcoin", "base_url": "https://gov.gitcoin.co/"},
            {"name": "Compound", "base_url": "https://www.comp.xyz/"},
            {"name": "Across", "base_url": "https://forum.across.to/"},
            {"name": "Lido", "base_url": "https://research.lido.fi/"},
            {"name": "Jito", "base_url": "https://forum.jito.network"},
            {"name": "Uniswap", "base_url": "https://gov.uniswap.org/"},
            {"name": "Aave", "base_url": "https://governance.aave.com/"},
            {"name": "Arbitrum", "base_url": "https://forum.arbitrum.foundation/"},
            {"name": "ENS", "base_url": "https://discuss.ens.domains/"},
            {"name": "Apecoin", "base_url": "https://forum.apecoin.com/"},
            {"name": "Balancer", "base_url": "https://forum.balancer.fi/"},
            {"name": "Starknet", "base_url": "https://community.starknet.io/"},
            {"name": "Stargate", "base_url": "https://stargate.discourse.group/"},
            {"name": "Optimism", "base_url": "https://gov.optimism.io/"},
            {"name": "GMX", "base_url": "https://gov.gmx.io/"},
            {"name": "Decentraland", "base_url": "https://forum.decentraland.org/"},
            {"name": "Radiant", "base_url": "https://community.radiant.capital/"},
            {"name": "Gnosis", "base_url": "https://forum.gnosis.io/"},
            {"name": "coW DAO", "base_url": "https://forum.cow.fi/"},
            {"name": "Hop", "base_url": "https://forum.hop.exchange/"},
            {"name": "Curve", "base_url": "https://gov.curve.fi/"},
            {"name": "Shapeshift", "base_url": "https://forum.shapeshift.com/"},
            {"name": "Gyroscope", "base_url": "https://forum.gyro.finance/"},
            {"name": "Frax", "base_url": "https://gov.frax.finance/"},
            {"name": "Moonwell", "base_url": "https://forum.moonwell.fi/"},
            {"name": "Rocketpool", "base_url": "https://dao.rocketpool.net/"},
            {"name": "VitaDAO", "base_url": "https://gov.vitadao.com/"},
            {"name": "Goldfinch", "base_url": "https://gov.goldfinch.finance/"},
            {"name": "Cabin", "base_url": "https://forum.cabin.city/"},
            {"name": "Stakewise", "base_url": "https://forum.stakewise.io/"},
            {"name": "Rari", "base_url": "https://forum.rari.foundation/"},
            {"name": "Sanctum", "base_url": "https://research.sanctum.so/"},
            {"name": "Jupiter", "base_url": "https://www.jupresear.ch/"},
            {"name": "Drift", "base_url": "https://driftgov.discourse.group/"},
            {"name": "Orca", "base_url": "https://forums.orca.so/"},
            {"name": "Marinade", "base_url": "https://forum.marinade.finance/"},
            {"name": "Sky", "base_url": "https://forum.sky.money/"},
            {"name": "Kamino", "base_url": "https://gov.kamino.finance/"},
            {"name": "Parcl", "base_url": "https://parcl.discourse.group/"},
            {"name": "Pyth", "base_url": "https://forum.pyth.network/"},
            {"name": "Debridge", "base_url": "https://gov.debridge.foundation/"},
            {"name": "Morpho", "base_url": "https://forum.morpho.org/"},
            {"name": "Marinade", "base_url": "https://forum.marinade.finance/"},
            {"name": "Sky", "base_url": "https://forum.sky.money/"},
            {"name": "Wormhole", "base_url": "https://forum.wormhole.com/"},
            {"name": "Pancakeswap", "base_url": "https://forum.pancakeswap.finance/"},
            {"name": "Etherfi", "base_url": "https://governance.ether.fi/"},
            {"name": "Abracadabra", "base_url": "https://forum.abracadabra.money/"},
            {"name": "Osmosis", "base_url": "https://forum.osmosis.zone/"},
            {"name": "Dxdy", "base_url": "https://dydx.forum/"},
            {"name": "Blast", "base_url": "https://forum.blast.io/latest"},
            
        ]

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(self.process_dao, dao["name"], dao["base_url"]): dao for dao in dao_list}

            for future in as_completed(futures):  # Process completed threads first
                dao = futures[future]
                try:
                    future.result()  # Raises exceptions inside the thread
                except Exception as e:
                    print(f"Error processing {dao['name']}: {e}")  # Error is logged, but execution continues


# **Usage**
if __name__ == "__main__": 
    scraper = DAOForumScraper()
    scraper.run()

