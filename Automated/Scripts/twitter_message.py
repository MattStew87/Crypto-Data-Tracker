import psycopg2
from dotenv import load_dotenv
import os
import anthropic


class TwitterMessage:
    def __init__(self):

        load_dotenv()
        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB", 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }

        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))   

    def create_data_summary(self, additional_queries):
        """
        Executes SQL queries, prepares summary messages, sends them to Claude, and returns processed results.
        :param additional_queries: List of dictionaries containing SQL queries, graph types, final columns, and graph titles.
        :return: List of processed message strings from Claude.
        """
        messages = []

        try:
            # Connect to the PostgreSQL database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    for query_info in additional_queries:
                        try:
                            # Extract query information
                            sql_query = query_info["sql_query"]
                            graph_title = query_info["graph_title"]
                            final_columns = query_info["final_columns"]

                            # Execute the SQL query
                            cursor.execute(sql_query)
                            raw_data = cursor.fetchall()

                            # Build the message string
                            column_descriptions = ", ".join(final_columns)
                            prompt = (
                                f"Here is a dataset showing '{graph_title}'.\n\n"
                                f"The columns in this dataset are: {column_descriptions}.\n\n"
                                f"Could you provide a concise one paragraph summary highlighting the main trends, "
                                f"patterns, and any significant outliers in the data (DO NOT VISUALIZE JUST INTERPRET)?\n\n"
                                f"Data: {raw_data if raw_data else 'No data available.'}"
                            )

                            # Connect to Claude API and send the prompt
                            try:
                                response = self.client.messages.create(
                                    model="claude-3-5-sonnet-20241022",
                                    max_tokens=1024,
                                    messages=[{"role": "user", "content": prompt}]
                                )
                                # Extract the text directly from Claude's response format
                                if response and hasattr(response, 'content'):
                                    text_block = response.content[0]
                                    messages.append(text_block.text if hasattr(text_block, 'text') else "Error: No text found in response.")
                                else:
                                    messages.append("Error: Invalid response format from Claude API.")
                            except Exception as claude_error:
                                print(f"Error communicating with the Claude API: {claude_error}")
                                messages.append("Error processing AI prompt.")

                        except Exception as query_error:
                            print(f"Error executing query: {sql_query}. Error: {query_error}")
                            messages.append(f"Error executing query: {sql_query}.")
        except Exception as db_error:
            print(f"Database connection error: {db_error}")
            messages.append("Database connection error.")

        return messages
    
    
    def generate_final_twitter_messages(self, additional_queries):
        """
        Calls execute_and_prepare_queries to get initial messages, prompts Claude with additional context,
        and formats the responses as a Twitter thread.
        :param additional_queries: List of dictionaries containing SQL queries, graph types, final columns, and graph titles.
        :return: List of formatted Twitter messages.
        """
        # Step 1: Get initial messages from execute_and_prepare_queries
        initial_messages = self.create_data_summary(additional_queries)

        final_twitter_messages = []
        counter = 2 
        for message in initial_messages:
            # Step 2: Create a new prompt for Claude
            additional_prompt = (
                f"Here is the summary based on the dataset provided:\n\n"
                f"{message}\n\n"
                f"Using this summary, generate a concise Twitter-style message following these detailed guidelines:\n\n"
                f"Understand the Metric:\n"
                f"1. Identify the key metric(s) from the dataset (e.g., user activity, market trends, governance).\n"
                f"2. Briefly explain why this metric matters (e.g., adoption, liquidity, community health).\n\n"
                f"Focus on Trends, Not Just Outliers:\n"
                f"3. Emphasize changes over time or across categories rather than single spikes/dips unless clearly significant.\n"
                f"4. Include aggregate comparisons (e.g., 'over the past week,' 'comparing Q1 to Q2,' 'cumulative totals').\n\n"
                f"Maintain a Professional, Neutral Tone:\n"
                f"5. Use concise and direct language understandable to both newcomers and industry experts.\n"
                f"6. Avoid emojis, hashtags, or unsupported speculation.\n"
                f"7. When suggesting possible reasons for trends, use moderate wording like 'could indicate,' 'may reflect,' or 'suggests.'\n\n"
                f"Formatting & Style:\n"
                f"8. Present the insight as part of a numbered thread. For this message, format it as: {counter}/.\n"
                f"9. Deliver one main insight supported by relevant numbers or comparisons.\n"
                f"10. Keep it under 280 characters to ensure tweet-friendly length.\n\n"
                f"Example:\n"
                f"2/ From mid-Aug to late Dec, net holders hovered in single-to-double digits before surging to +460 around Dec 19. Meanwhile, price rose steadily from ~100 to 104.83. This combined uptick could suggest growing adoption and confidence in the platform."
            )
            counter += 1 

            # Step 3: Send the new prompt to Claude
            try:
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=280,
                    messages=[{"role": "user", "content": additional_prompt}]
                )
                if response and hasattr(response, 'content'):
                    text_block = response.content[0]
                    final_message = text_block.text if hasattr(text_block, 'text') else "Error: No text found in response."
                    final_twitter_messages.append(final_message)
                else:
                    final_twitter_messages.append("Error: Invalid response format from Claude API.")
            except Exception as claude_error:
                print(f"Error communicating with the Claude API: {claude_error}")
                final_twitter_messages.append("Error processing AI prompt.")

        return final_twitter_messages



if __name__ == "__main__": 
    twitter_message = TwitterMessage()

    additional_queries = [
        {
            "sql_query": "select * from tab1 order by block_timestamp desc",
            "final_columns": ["Date", "Net Holders", "Carrot Price (USD)"],
            "graph_type": "MULTI_LINE",
            "graph_title" : "Daily Carrot Price and Net Holders" 
        }
    ]

    results = twitter_message.generate_final_twitter_messages(additional_queries) 
    print(results) 