from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from twitter_handler import TwitterHandler
from tally_data import TallyData
from openai import OpenAI
import time 
from comment_handler import CommentHandler


class TallyHandler: 
    
    def __init__(self): 
        load_dotenv() 

        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": os.getenv("DATABASE_NAME"), 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }

        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        spaces_json_path = os.path.join(script_dir, "Image_bank", "spaces.json")
        with open(spaces_json_path, "r") as file:
            self.spaces_data = json.load(file)
        
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))      

        self.twitter_client = TwitterHandler() 

        self.tally_gov_data = TallyData() 

        self.comment_handler = CommentHandler() 


    def proposal_announcement_messages(self, proposal): 
        
        # Extract proposal data
        proposal_title = proposal['proposal_title']
        proposal_text = proposal['proposal_description']
        proposal_start_time = proposal['start_time']
        proposal_end_time = proposal['end_time']
        space_id = proposal['space_name']
        twitter_handle = self.spaces_data[space_id]["twitter"]

        messages = []

        # Tweet 1
        ################################################################

        part_1_prompt = (
            f"Write a professional and concise tweet to announce a new governance proposal. This must start with 1/"
            f"The tweet must highlight the proposal's title ({proposal_title}) In quotes, from {twitter_handle}, "
            f"and display the proposal's live period in a short date range format, like 'Jan 2nd - 7th'. "
            f"Use the actual date/time from {proposal_start_time} to {proposal_end_time} for context, but do not show hours, minutes, seconds, or the year in the final tweet. "
            f"DO NOT include hashtags or emojis. "
            f"This should not call to action, just inform."
            f"have tweet lead with proposal name after 1/"
            f"DO NOT include this char anywhere *"
        )
        part_1_message = self._generate_chatGPT_response(part_1_prompt)
        messages.append(part_1_message)

        # Tweet 2
        ################################################################

        part_2_prompt =f"""
            ### **Prompt Template for Shortened Second Tweet of a Thread**

            ---

            ### **Required Inputs:**

            - {{ proposal_title }} = {proposal_title}
            - {{ proposal_description }} = {proposal_text}

            ---

            ### **Structure for the Second Tweet:**

            Start with **2/** to indicate the second tweet in the thread.

            1. Highlight **why the proposal matters** or **how it will be implemented**.
            2. Emphasize **unique elements or decisions** related to the proposal.

            ---

            ### **Output Format:**

            2/ This proposal addresses {{ key issue or challenge }}.
            It’s expected to {{ key impact or outcome }}, supporting {{ mission or objective }}.
            
            ---

            ### **Example Second Tweets:**

            2/ This proposal strengthens Stargate’s alignment with Abstract, a zk-powered chain focused on culture-driven communities.

            It’s expected to boost cross-chain liquidity and solidify Stargate’s zk ecosystem presence.
            
            ---

            2/ The Retroactive Public Goods Funding proposal addresses the need to reward contributors for prior work.

            The proposal is expected to drive future contributions by funding successful projects retroactively.

            **Output should have a max of one short sentence and one long one.**

            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline character
        """

        part_2_message = self._generate_chatGPT_response(part_2_prompt)
        messages.append(part_2_message)

        # Tweet 3
        ################################################################

        part_3_message = (
            f"3/ To be a part of the decision-making process cast your vote on the latest proposal by visiting the following link: \n\n"
            f"https://www.tally.xyz/explore"
        )
        messages.append(part_3_message)

        # Append space_id and messages to the result list
        result = {"space_id": space_id, "messages": messages, 'proposal_title': proposal_title}

        return result
    

    def proposal_halftime_messages(self, proposal): 

        # Extract proposal data
        proposal_id = proposal['proposal_id']
        proposal_title = proposal['proposal_title']
        proposal_text = proposal['proposal_description']
        space_id = proposal['space_name']
        governor_id = proposal['governor_id']
        decimals = proposal['decimals']
        twitter_handle = self.spaces_data[space_id]["twitter"]
    
        prompt_data = self.tally_gov_data.prompt_stats(proposal_id, decimals, governor_id)

        # Messages for the current proposal
        messages = []

        # Tweet 1
        ################################################################
        prompt_for_first_tweet = f"""
        ### **Prompt Template for First Tweet of a Thread**
            ---

            ### **Required Inputs:**

            - `proposal_title` = {proposal_title}
            - `space_twitter_id` = {twitter_handle}
            - `proposal_text` = {proposal_text}
            ---

            ### **Intro**

            Start the first tweet of the thread with **`1/`**. Mention that the governance proposal with the title  **`{{ proposal_title }}`** In quotes from **`{{ space_twitter_id }}`** is halfway through.

            Ensure the tweet is under 245 characters. Do not include emojis. keep brief and informative put a pagebreak between sentences.

            ---

            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters
            - Have the seccond setence mension the dolar figure of the proposal or if there is non just a few word suummary of it keep it short
             
        """

        part_1_message = self._generate_chatGPT_response(prompt_for_first_tweet)
        messages.append(part_1_message)

        # Tweet 2
        ################################################################
        prompt_for_second_tweet = f"""
            ### **Prompt Template for Second Tweet of a Thread (Hourly Voter and Activity Breakdown)**

            ---

            ### **Required Inputs:**

            - `total_voters` = {prompt_data["total_voters"]}
            - `choice_1_name` = {prompt_data["1st_choice_name"]}
            - `choice_1_votes` = {prompt_data["1st_choice_voting_power"]}
            - `choice_2_name` = {prompt_data["2nd_choice_name"]}
            - `choice_2_votes` = {prompt_data["2nd_choice_voting_power"]}
            - `space_twitter_id` = {twitter_handle}

            ---

            ### **Intro**

            Begin the tweet with **`2/`**.  Mention the total number of voters and votes for each choice of top 2 using placeholders. 
            
            ensure the tweet is under 245 characters. Keep the tone neutral and professional. Do not include emojis. keep brief and informative put a pagebreak between sentences.

            ---

            ### **Dynamic Comments Based on Voting Activity**

            Add a comment based on the most relevant dynamic from the graph. Only include one (most relevant) do not mension dynamic title:

            - **Choice Dominance** If one choice received significantly more votes than the other, mention this dominance.
            - **Choice Winning** If one choice received more votes than the other it is not very close but also not a domination.
            - **Close Race** If the final votes between choices are close, note the competitive nature of the proposal.

            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters 
            - DO **NOT** add an additional comment at the end with direction to more infomation or twitter @ (eg. Follow @GMX_IO for updates.)
            - Every time a voting choice is talked about surround it with " on both sides

        """

        part_2_message = self._generate_chatGPT_response(prompt_for_second_tweet)
        messages.append(part_2_message)

        # Tweet 3
        ################################################################

        prompt_for_third_tweet = f"""
            ### **Prompt Template for Third Tweet of a Thread (Voting Power Distribution)**

            ---

            ### **Required Inputs:**

            - `{{ total_voters }}` = {prompt_data["total_voters"]}
            - `{{ top_10_percent_voting_power_wallets }}` = {prompt_data["top_10%_voting_power_wallets"] }
            - `{{ top_50_percent_voting_power_wallets }}`= {prompt_data["top_50%_voting_power_wallets"] }
            - `{{ space_twitter_id }}` = {twitter_handle}

            ---

            ### **Intro**

            Begin the tweet with **`3/`**. Mention relevant data points about how voting power is distributed among participants using placeholders. 
            
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional. Keep brief and informative put a pagebreak between sentences.

            ---

            ### **Dynamic Comments Based on Voting Power Distribution**

            Add a comment based on the most relevant dynamic from the voting power breakdown. Only include one (most relevant):

            - Extreme Concentration Among a Handful: If only a under 10 wallets or below 0.1% make up the top 50% of voting power, note the concentration of power among a select few.
            Example: "The top 50% of voting power is controlled by just 8 wallets, highlighting a significant concentration of influence."
            
            - Distributed Power Among Many Wallets: If the top 50% of voting power is shared among a large number of wallets (e.g., >50 wallets), emphasize that power is more evenly distributed.
            Example: "Voting power is distributed, with the top 50% shared across 120 wallets, showing balanced governance participation."
            
            - Single Wallet Dominance: If a single wallet accounts for the top 25% or 50% of voting power, highlight this extreme dominance.
            Example: "One wallet alone controls 50% of the voting power, signaling an unusual concentration of influence."
            
            - Balanced Mid-Tier Influence: If the top 25%-50% includes a moderate to large number of wallets (e.g., 25-70 wallets), note their significant collective impact.
            Example: "The top 25%-50% of voting power is distributed among 60 wallets, showcasing strong mid-tier influence in governance
            
            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters 
            - DO **NOT** add an additional comment at the end with direction to more infomation or twitter @ (eg. Follow @GMX_IO for updates.) 

        """

        part_3_message = self._generate_chatGPT_response(prompt_for_third_tweet)
        messages.append(part_3_message)

        # Message Cleanup 
        ################################################################
        final_messages = []
        for message in messages:
            validation_prompt = f"""
            Please carefully review the following tweet that is a part of a twitter thread and remove any incomplete phrases at the end 
            that seem to occasionally get left at the end when we generate the tweets with gpt.
            if the last sentence seems to be cut off remove it from the output (eg. doesn't end with a period) 
            do not use this - execpt as a bulletpoint. If the whole tweet is wrapped in quotes remove them and just leave the text. 
            Tweet: "{message}"

            Return fixed tweet
            """
            refined_message = self._generate_chatGPT_response(validation_prompt)
            final_messages.append(refined_message)

        # Tweet 4
        ################################################################

        part_4_message = (
             f"4/ To be a part of the decision-making process. Cast your vote on the latest proposal by visiting the following link: \n\n"
             f"https://www.tally.xyz/explore"
        )

        final_messages.append(part_4_message)

        # Append space_id and messages to the result list
        result = {
            "space_id": space_id,
            "messages": final_messages,
            "proposal_id": proposal_id,
            "decimals": decimals,
            'proposal_title': proposal_title
        }        

        return result 
    
    def proposal_final_messages(self, proposal): 

        # Extract proposal data
        proposal_id = proposal['proposal_id']
        proposal_title = proposal['proposal_title']
        space_id = proposal['space_name']
        governor_id = proposal['governor_id']
        decimals = proposal['decimals']
        twitter_handle = self.spaces_data[space_id]["twitter"]
    
        prompt_data = self.tally_gov_data.prompt_stats(proposal_id, decimals, governor_id)
        
        # Messages for the current proposal
        messages = []

        # Tweet 1
        ################################################################

        prompt_for_first_tweet = f"""
            **Prompt Template for First Tweet of a Thread (Proposal Concluded)**

            ---

            ### **Required Inputs:**

            - `{{ proposal_title }}` = {proposal_title}
            - `{{ space_twitter_id }}` = {twitter_handle}
            - `{{ 1st choice votes }}` = {prompt_data["1st_choice_voting_power"]}
            - `{{ 1st choice name }}` = {prompt_data["1st_choice_name"]}
            - `{{ winning_option }}` = {prompt_data["1st_choice_name"]}
            - `{{ winning_percent }}` = {prompt_data["leading_percent"]}

            ### **Intro**

            Start the first tweet of the thread with **`1/`**. Mention that the governance proposal with the title **`{{ proposal_title }}` In quotes ** from **`{{ space_twitter_id }}`** has concluded and mension the results.

            Ensure the tweet is under 245 characters. Do not include emojis. keep breif and infomative put a pagebreak between sentences.

            ---

            
            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters
            - DO NOT include this char anywhere *
            - have tweet lead with proposal name after 1/

            """

        part_1_message = self._generate_chatGPT_response(prompt_for_first_tweet)
        messages.append(part_1_message)

        # Tweet 2
        ################################################################

        prompt_for_second_tweet = f"""
            **Prompt Template for Second Tweet of a Thread (Final Voter and Activity Breakdown)**

            ---

            ### **Required Inputs:**

            - `{{ total_voters }}` = {prompt_data["total_voters"]}
            - `{{ choice_1_name }}` = {prompt_data["1st_choice_name"]}
            - `{{ choice_1_votes }}` = {prompt_data["1st_choice_voting_power"]}
            - `{{ choice_2_name }}` =  {prompt_data["2nd_choice_name"]}
            - `{{ choice_2_votes }}` = {prompt_data["2nd_choice_voting_power"]}
            - `{{ space_twitter_id }}` = {twitter_handle}

            ---

            ### **Intro**

            Begin the tweet with **`2/`**. Mention the total number of voters and votes for each choice of top 2 using placeholders. 
            
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional. Do not include emojis. keep breif and infomative put a pagebreak between sentences.


            ---

            ### **Dynamic Comments Based on Voting Activity**

            Add a comment based on the most relevant dynamic from the graph. Only include one (most relevant) do not mension dynamic title:

            - **Choice Dominance** If one choice received significantly more votes than the other, mention this dominance.
            - **Choice Winning** If one choice received more votes than the other it is not very close but also not a domination.
            - **Close Race** If the final votes between choices are close, note the competitive nature of the proposal.

            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters 
            - DO **NOT** add an additional comment at the end with direction to more infomation or twitter @ (eg. Follow @GMX_IO for updates.)
            - Every time a voting choice is talked about surround it with " on both sides
        """

        part_2_message = self._generate_chatGPT_response(prompt_for_second_tweet)
        messages.append(part_2_message)

        # Tweet 3
        ################################################################

        prompt_for_third_tweet = f"""
            **Prompt Template for Third Tweet of a Thread (Final Voting Power Distribution)**
            ---

            ### **Required Inputs:**

            - `{{ total_voters }}` = {prompt_data["total_voters"]}
            - `{{ top_10_percent_voting_power_wallets }}` = {prompt_data["top_10%_voting_power_wallets"] }
            - `{{ top_50_percent_voting_power_wallets }}`= {prompt_data["top_50%_voting_power_wallets"] }
            - `{{ space_twitter_id }}` = {twitter_handle}

            ---

            ### **Intro**

            Begin the tweet with **`3/`**.  Mention relevant data points about how voting power is distributed among participants using placeholders. 
            
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional. Keep brief and informative put a pagebreak between sentences.

            ---

            ### **Dynamic Comments Based on Voting Power Distribution**

            Add a comment based on the most relevant dynamic from the voting power breakdown. Only include one (most relevant):

            - Extreme Concentration Among a Handful: If only a under 10 wallets or below 0.1% make up the top 50% of voting power, note the concentration of power among a select few.
            Example: "The top 50% of voting power is controlled by just 8 wallets, highlighting a significant concentration of influence."
            
            - Distributed Power Among Many Wallets: If the top 50% of voting power is shared among a large number of wallets (e.g., >50 wallets), emphasize that power is more evenly distributed.
            Example: "Voting power is distributed, with the top 50% shared across 120 wallets, showing balanced governance participation."
            
            - Single Wallet Dominance: If a single wallet accounts for the top 25% or 50% of voting power, highlight this extreme dominance.
            Example: "One wallet alone controls 50% of the voting power, signaling an unusual concentration of influence."
            
            - Balanced Mid-Tier Influence: If the top 25%-50% includes a moderate to large number of wallets (e.g., 25-70 wallets), note their significant collective impact.
            Example: "The top 25%-50% of voting power is distributed among 60 wallets, showcasing strong mid-tier influence in governance
            
            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters 
            - DO **NOT** add an additional comment at the end with direction to more infomation or twitter @ (eg. Follow @GMX_IO for updates.)
        """

        part_3_message = self._generate_chatGPT_response(prompt_for_third_tweet)
        messages.append(part_3_message)

        # Tweet 4
        ################################################################


        prompt_for_fourth_tweet = f"""
            **Prompt Template for Fourth Tweet of a Thread (Final Voting Activity Comparison)**

            ---

            ### **Required Inputs:**

            - `{{ voting_power_rank }}` = {prompt_data["voting_power_rank"]}
            - `{{ voter_turnout_rank }}`= {prompt_data["voter_turnout_rank"]}
            - `{{ voting_power_percentile }}` = {prompt_data["voting_power_percentile"]}
            - `{{ voter_percentile }}` = {prompt_data["voter_percentile"]}
            - `{{ space_twitter_id }}` = {twitter_handle}

            ---

            ### **Intro**

            Begin the tweet with **`4/`**. Compare the concluded proposal’s voting activity to previous proposals within the same space.

            Mention relevant data points using placeholders. Ensure the tweet is under 245 characters. Keep the tone neutral and professional.

            ---

            ### **Dynamic Comments Based on Voting Activity Comparison**

            Add a comment based on the most relevant insight from the comparison of turnout data. Only include one (most relevant):

            - **High Turnout (Above 75th Percentile):** If both voter participation and voting power turnout were high, emphasize strong engagement. 
            - **High-Mid Turnout (Between 50th-75th Percentile):  If both voter participation and voting power turnout were low-mid, highlight above average engagement.** 
            - **Low-Mid Turnout (Between 25th-50th Percentile):** If both voter participation and voting power turnout were low-mid, highlight below average engagement.
            - **Low Turnout (Below 25th Percentile):** If both voter participation and voting power turnout were low, highlight the lack of engagement.
            - **Discrepancy Between Voters and Voting Power:** If voter turnout rank is significantly higher or lower than voting power rank, nly use this if the discrpency is very large.
            - **Top Performer (Rank 1-3):** If the proposal ranks in the top 1-3 spots for turnout, emphasize its leading position.
            - **Middle of the Pack (25th-75th Percentile):** If turnout falls between the 25th and 75th percentile, focus on balanced engagement.

            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            - Format the tweet so that each sentence **after the first sentence** is separated by **two** newline characters
            - DO **NOT** add an additional comment at the end with direction to more infomation or twitter @ (eg. Follow @GMX_IO for updates.)
        """

        part_4_message = self._generate_chatGPT_response(prompt_for_fourth_tweet)
        messages.append(part_4_message)

        # Message Cleanup 
        ################################################################
        final_messages = []
        for message in messages:
            validation_prompt = f"""
            Please carefully review the following tweet that is a part of a twitter thread and remove any incomplete phrases at the end 
            that seem to occasionally get left at the end when we generate the tweets with gpt.
            if the last sentence seems to be cut off remove it from the output (eg. doesn't end with a period) 
            do not use this - execpt as a bulletpoint. If the whole tweet is wrapped in quotes remove them and just leave the text. 
            Tweet: "{message}"

            Return fixed tweet
            """
            refined_message = self._generate_chatGPT_response(validation_prompt)
            final_messages.append(refined_message)


        # Tweet 5
        ################################################################

        part_5_message = (
            f"5/ To be a part of the decision-making process. Cast your vote on the latest proposal by visiting the following link: \n\n"
            f"https://www.tally.xyz/explore"
        )

        final_messages.append(part_5_message)

        # Append space_id and messages to the result list
        result = {
            "space_id": space_id,
            "messages": final_messages,
            "proposal_id": proposal_id, 
            "governor_id": governor_id, 
            "decimals": decimals,
            'proposal_title': proposal_title
        } 
    
        return result
    
    
    def create_proposal_announcement(self, proposal):
        
        proposal_message = self.proposal_announcement_messages(proposal)

        space_id = proposal_message.get("space_id", "")
        messages = proposal_message.get("messages", "")
        proposal_title = proposal_message.get("proposal_title", "")
                    
        cover_image = self.generate_space_image(space_id, 1)

        orginal_post_id = self.twitter_client.post_with_media(messages[0], cover_image)
        thread1_id = self.twitter_client.post_thread_reply(messages[1], orginal_post_id)
        self.twitter_client.post_thread_reply(messages[2], thread1_id)

        self.comment_handler.set_tweet_id(orginal_post_id, proposal_title, space_id)

    
    def create_proposal_halftime(self, proposal):

        halftime_message =  self.proposal_halftime_messages(proposal) 

        space_id = halftime_message.get("space_id", "")
        messages = halftime_message.get("messages", "")
        proposal_id = halftime_message.get("proposal_id", "")
        decimals = halftime_message.get("decimals", "") 
        proposal_title = halftime_message.get("proposal_title", "")
                    
        cover_image = self.generate_space_image(space_id, 2)
        Tweet2_media = self.tally_gov_data.tally_daily_total_voting_power_by_choice(proposal_id, decimals)
        Tweet3_media = self.tally_gov_data.tally_voting_power_by_wallet(proposal_id, decimals)

        orginal_post_id = self.twitter_client.post_with_media(messages[0], cover_image)
        thread1_id = self.twitter_client.post_thread_reply_with_media(messages[1], Tweet2_media, orginal_post_id)
        thread2_id = self.twitter_client.post_thread_reply_with_media(messages[2], Tweet3_media, thread1_id)
        self.twitter_client.post_thread_reply(messages[3], thread2_id)

        self.comment_handler.set_tweet_id(orginal_post_id, proposal_title, space_id)
    
    def create_proposal_final(self, proposal):

        final_message =  self.proposal_final_messages(proposal) 

        space_id = final_message.get("space_id", "")
        messages = final_message.get("messages", "")
        proposal_id = final_message.get("proposal_id", "")
        governor_id = final_message.get("governor_id", "")
        decimals = final_message.get("decimals", "") 
        proposal_title = final_message.get("proposal_title", "")
                    
        cover_image = self.generate_space_image(space_id, 3)
        Tweet2_media = self.tally_gov_data.tally_daily_total_voting_power_by_choice(proposal_id, decimals)
        Tweet3_media = self.tally_gov_data.tally_voting_power_by_wallet(proposal_id, decimals)
        Tweet4_media = self.tally_gov_data.tally_space_proposals_by_voting_power(proposal_id, decimals, governor_id)

        orginal_post_id = self.twitter_client.post_with_media(messages[0], cover_image)
        thread1_id = self.twitter_client.post_thread_reply_with_media(messages[1], Tweet2_media, orginal_post_id)
        thread2_id = self.twitter_client.post_thread_reply_with_media(messages[2], Tweet3_media, thread1_id)
        thread3_id = self.twitter_client.post_thread_reply_with_media(messages[3], Tweet4_media, thread2_id)
        self.twitter_client.post_thread_reply(messages[4], thread3_id)

        self.comment_handler.set_tweet_id(orginal_post_id, proposal_title, space_id)
    
    
    
    def _generate_chatGPT_response(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[ {"role": "system", "content": "Keep Tweet brief under 240 char and informative put TWO NEWLINES CHARACTERS between sentences. If any numbers are mentioned in the thousands, millions, billions, or trillions mention them shorthand with two decimals (eg. 1.85B). Also do not Include Emoji's"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=75
            )
            # Extract and return the content from the response
            return response.choices[0].message.content.strip()
        except Exception  as chatgpt_error:
            # Handle any errors
            return f"An error occurred: {str(chatgpt_error)}"


    def generate_space_image(self, space_id, part):
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Paths relative to the script directory
        output_image_path = os.path.join(script_dir, "Image_bank", "final_output_image.png")

        # Validate space_id
        if space_id not in self.spaces_data:
            raise ValueError(...)
        space_data = self.spaces_data[space_id]

        base_image_path = os.path.join(script_dir, "Image_bank", os.path.basename(space_data["base_image"]))
        logo_image_path = os.path.join(script_dir, "Image_bank", os.path.basename(space_data["space_image"]))
        title_text = (space_data["part1_text"] if part == 1 else space_data["part2_text"] if part == 2  else space_data["part3_text"] if part == 3 else "Invalid part")

        # Open the base and logo images
        base_image = Image.open(base_image_path)
        logo_image = Image.open(logo_image_path)

        # Resize the logo to be bigger
        logo_size = (300, 300)  # Adjust size as needed
        logo_image = logo_image.resize(logo_size)

        # Calculate logo position (move more to the right, center vertically)
        logo_position = (300 + 140, (base_image.height // 2) - (logo_image.height // 2))

        # Paste the logo onto the base image
        base_image.paste(logo_image, logo_position, logo_image)

        # Add text (title and date)
        draw = ImageDraw.Draw(base_image)

        # Set fonts (adjust to available fonts on your system)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

        # Title text with bounding box
        bounding_box_width = 600  # Set the maximum width for the text
        wrapped_title = textwrap.fill(title_text, width=15)  # Wrap text to fit within the bounding box

        # Calculate position for wrapped text
        title_x = logo_position[0] + logo_size[0] + 50
        title_y = logo_position[1] + (logo_image.height // 4) - 67
        current_y = title_y

        # Draw each line of the wrapped text
        for line in wrapped_title.split('\n'):
            text_bbox = draw.textbbox((0, 0), line, font=title_font)  # Get the bounding box of the text
            text_height = text_bbox[3] - text_bbox[1]  # Calculate text height
            draw.text((title_x, current_y), line, fill="black", font=title_font)
            current_y += text_height + 10  # Move to the next line with spacing

        # Generate current date in required format
        current_date = datetime.now().strftime("%d %b, %Y").upper()

        # Date text (move into the pill-shaped element, adjust left and up slightly)
        pill_x1, pill_y1, pill_x2, pill_y2 = base_image.width - 440, base_image.height - 195, base_image.width - 50, base_image.height - 95
        date_position = (pill_x1 + (pill_x2 - pill_x1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[2] // 2,
                        pill_y1 + (pill_y2 - pill_y1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[3] // 2)
        draw.text(date_position, current_date, fill="black", font=date_font)


        # Save the final output
        base_image.save(output_image_path)
        return output_image_path  
              




if __name__ == "__main__": 
    tally_hanlder = TallyHandler() 
    tally_hanlder.generate_space_image('Cryptex', 2) 

