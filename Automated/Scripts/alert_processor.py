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
        


