from datetime import datetime, timedelta, timezone
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv


class DAOTwitterResponder:
    """Class to generate Twitter responses using DAO governance discussions stored in Qdrant."""

    def __init__(self, qdrant_host="http://localhost:6333", collection_name="dao_forum_collection"):
        """Initialize the responder with OpenAI API and Qdrant database settings."""
        
        load_dotenv() 
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.qdrant_host = qdrant_host
        self.collection_name = collection_name
        self.current_date = datetime.now(timezone.utc)

    def iso_to_epoch_milliseconds(self, iso_timestamp):
        """Convert ISO 8601 timestamp to Unix epoch time in milliseconds."""
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        return int((dt - epoch).total_seconds() * 1000)

    def get_embedding(self, text):
        """Generate an embedding for the input text using OpenAI."""
        response = self.client.embeddings.create(model="text-embedding-ada-002", input=text)
        return response.data[0].embedding

    def query_similar_context(self, input_text, dao_name, top_k=4, extra_context=""):
        """Query Qdrant for the most similar governance discussions based on input text."""
        # Combine input text and extra context
        combined_text = f"{input_text}\n\nAdditional context: {extra_context}"
        query_vector = self.get_embedding(combined_text)

        # Time filtering (limit to discussions from the past `days_past` days)
        time_threshold = self.iso_to_epoch_milliseconds(
            (self.current_date - timedelta(days=30)).isoformat()
        )

        filter_condition = {
            "must": [
                {"key": "dao_name", "match": {"value": dao_name}},
                {"key": "timestamp", "range": {"gte": time_threshold}}
            ]
        }

        # Query payload
        url = f"{self.qdrant_host}/collections/{self.collection_name}/points/search"
        payload = {
            "vector": query_vector,
            "filter": filter_condition,
            "top": top_k,
            "with_payload": True
        }

        # Request to Qdrant
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            results = response.json().get("result", [])
            return [
                {
                    "content": match["payload"].get("content", ""),
                    "source_url": match["payload"].get("source_url", "No link available"),
                    "author": match["payload"].get("author", "Unknown"),
                    "timestamp": match["payload"].get("timestamp", "Unknown"),
                    "dao_name": match["payload"].get("dao_name", "Unknown"),
                    "topic_title": match["payload"].get("topic_title", "No topic available"),
                }
                for match in results
            ]
        else:
            print(f"Error querying Qdrant: {response.status_code}, {response.text}")
            return []

    def generate_response(self, input_text, dao_name, extra_context=""):
        """Generate a concise response based on similar governance discussions."""
        try:
            # Retrieve similar discussions
            similar_comments = self.query_similar_context(input_text, dao_name, extra_context=extra_context)

            # Format the context for GPT
            context = "\n\n".join(
                f"Comment {i+1} by {comment['author']} on {comment['timestamp']} (DAO: {comment['dao_name']}): {comment['content']}"
                for i, comment in enumerate(similar_comments)
            )

            # Source links
            links = "\n".join(f"{i+1}. {comment['source_url']}" for i, comment in enumerate(similar_comments))

            # Define the chat prompt
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a DAO governance intern on Twitter. Your context comes from governance forums. "
                        "Respond concisely in under 200 characters, and use references sparingly."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Today's date is {self.current_date.strftime('%Y-%m-%d')}.\n\n"
                        f"Extra context: {extra_context}\n\n"
                        f"Using the context below, respond concisely:\n\nContext:\n{context}\n\nQuery: {input_text}"
                    )
                }
            ]

            # Query GPT for a response
            completion = self.client.chat.completions.create(
                model="gpt-4o", messages=messages
            )

            # Extract response text
            gpt_response = completion.choices[0].message.content

            return f"{gpt_response}{f'\n\nSources:\n{links}' if links else ''}"

        except Exception as e:
            return f"An error occurred: {e}"


# **Usage Example**
if __name__ == "__main__":
    responder = DAOTwitterResponder()

    # Collect user input
    user_query = input("Enter your query: ")  # Tweet comment
    #extra_context = input("Enter extra context (e.g., 'response to PropXYZ from XYZDAO'): ")  # Extra metadata
    dao_name = input("Enter dao name:")

    # Generate and print response
    response = responder.query_similar_context(user_query, dao_name)
    print(response)

