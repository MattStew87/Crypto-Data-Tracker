import psycopg2
from dotenv import load_dotenv
import os
import anthropic
import tweepy
from graph_generator import GraphGenerator

class AlertProcessor:
    def __init__(self):
        """
        Initializes the AlertProcessor.
        """

        # Load environment variables
        load_dotenv()  

        # Anthropics (Claude) API setup
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))    
    

    def process_ai_prompt(self, ai_prompt, query_results):
        """
        Processes the AI prompt with the relevant query results using the Claude API.
        :param ai_prompt: AI prompt string.
        :param query_results: Dictionary of labeled query results.
        :return: Claude's response to the AI prompt.
        """
        try:
            # Prepare results as a formatted string
            formatted_results = "\n".join(
                [f"{key}:\n{result}" for key, result in query_results.items()]
            )
            prompt = f"{ai_prompt}\n\nRelevant Data:\n{formatted_results}"

            # Send the prompt to Claude
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content
        except Exception as e:
            print(f"Error communicating with the Claude API: {e}")
            return None
        

    def process_alert(self, triggered_alert):
        """
        Processes a single alert.
        :param triggered_alert: Dictionary with alert name and metadata.
        """
        # Extract the alert name and metadata
        alert_name, metadata = next(iter(triggered_alert.items()))

        # Step 1: Execute SQL queries
        additional_queries = metadata.get("additional_queries", [])
        graph_handler = GraphGenerator() 
        results = graph_handler.generate_graphs(additional_queries)
        print(results) 


        # Step 2: Process AI prompt
        ai_prompt = metadata.get("ai_prompt_info", "")
        if ai_prompt:
            # Process AI prompt
            #ai_response = self.process_ai_prompt(ai_prompt, query_results)
            #print(f"AI Response for {alert_name}: {ai_response}")

            print(f"Dummy result for {alert_name}")
        


