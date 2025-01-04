from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import psycopg2
import os
from twitter_handler import TwitterHandler
from flipside_gov_data import FlipsideGovData

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
        
        self.new_proposals = self.get_new_proposals()  

        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY")) 

        self.twitter_client = TwitterHandler() 

        self.flipside_gov_data = FlipsideGovData() 

        script_dir = os.path.dirname(os.path.abspath(__file__))
        spaces_json_path = os.path.join(script_dir, "Image_bank", "spaces.json")

        with open(spaces_json_path, "r") as file:
            self.spaces_data = json.load(file)
    
    def get_new_proposals(self): 
        proposals = []
        try:
            # Connect to the PostgreSQL database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    #sql_query = """SELECT * FROM new_proposals WHERE space_id IN ( 'arbitrumfoundation.eth', 'aave.eth', 'ens.eth', 'apecoin.eth', 'balancer.eth', 'lido-snapshot.eth', 'cvx.eth', 'starknet.eth', 'safe.eth', 'stgdao.eth', 'uniswapgovernance.eth', 'gitcoindao.eth', 'gmx.eth', 'speraxdao.eth', 'shellprotocol.eth', 'sushigov.eth', 'radiantcapital.eth', 'beets.eth', 'hop.eth', 'frax.eth', 'shapeshiftdao.eth', 'acrossprotocol.eth', 'rocketpool-dao.eth', 'comp-vote.eth', 'devdao.eth', 'abracadabrabymerlinthemagician.eth', 'morpho.eth', 'ymbiosisdao.eth', 'vote.vitadao.eth', 'stakewise.eth', 'prismafinance.eth' ) LIMIT 1"""
                    sql_query = """ SELECT * FROM governance_proposals WHERE PROPOSAL_ID like '0x6cc9d7377b027de1a8b66a592a3ce55f2201b75d256e8626514f1ead768fd316'"""
                    cursor.execute(sql_query)
                    raw_data = cursor.fetchall()

                    # Column names in lower case and in order
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
                    
                    # Convert each row into a dictionary
                    for row in raw_data:
                        proposals.append(dict(zip(columns, row)))

        except Exception as db_error:
            print(f"Database connection error: {db_error}")
        
        return proposals

    def proposal_announcement_messages(self): 
        all_messages = []
        
        for proposal in self.new_proposals:
            # Extract proposal data
            proposal_id = proposal['proposal_id']
            proposal_title = proposal['proposal_title']
            proposal_text = proposal['proposal_text']
            choices = proposal['choices']
            proposal_start_time = proposal['proposal_start_time']
            proposal_end_time = proposal['proposal_end_time']
            space_id = proposal['space_id']
            link_to_vote = f"https://snapshot.box/#/s:{space_id}/proposal/{proposal_id}"
            twitter_handle = self.spaces_data[space_id]["twitter"]

            
           
            # Messages for the current proposal
            messages = []

            # Generate first part
            part_1_prompt = (
                f"Write a professional and concise tweet to announce a new governance proposal. This should start with 1/"
                f"The tweet must highlight the proposal's title ({proposal_title}), the twitter handle ({twitter_handle}), "
                f"and display the proposal's live period in a short date range format, like 'Jan 2nd - 7th'. "
                f"Use the actual date/time from {proposal_start_time} to {proposal_end_time} for context, but do not show hours, minutes, seconds, or the year in the final tweet. "
                f"DO NOT include hashtags or emojis. "
                f"This should not call to action, just inform."
            )
            part_1_message = self._generate_claude_response(part_1_prompt)
            messages.append(part_1_message)

            # Generate second part
            part_2_prompt = (
                f"Write a professional and concise tweet summarizing the details of the proposal. Use the following text to explain "
                f"what the proposal is about: {proposal_text}"
                f"Please split the following text into exactly two lines. Do **not** include any numbering or extra labels like 1/2 or 2/2. Output only the text in two lines, separated by **two** newline characters. No other characters, punctuation, or headers"
                f"Do not include hashtags or emojis. "
                f"The post should start with 2/."
            )
            part_2_message = self._generate_claude_response(part_2_prompt)
            messages.append(part_2_message)

            # Generate third part
            part_3_prompt = (
                f"Write a professional and concise tweet to provide readers a link to vote if they want to participate. Include the link to vote: {link_to_vote}. "
                f"Do not include hashtags or emojis. "
                f"This should start with 3/."
            )
            part_3_message = self._generate_claude_response(part_3_prompt)
            messages.append(part_3_message)

            # Append space_id and messages to the result list
            all_messages.append({
                "space_id": space_id,
                "messages": messages
            })

        return all_messages
    
    def proposal_halftime_messages(self): 
        all_messages = []
        
        for proposal in self.new_proposals:
            # Extract proposal data
            proposal_id = proposal['proposal_id']
            proposal_title = proposal['proposal_title']
            proposal_text = proposal['proposal_text']
            choices = proposal['choices']
            proposal_start_time = proposal['proposal_start_time']
            proposal_end_time = proposal['proposal_end_time']
            space_id = proposal['space_id']
            link_to_vote = f"https://snapshot.box/#/s:{space_id}/proposal/{proposal_id}"
            twitter_handle = self.spaces_data[space_id]["twitter"]
            
            # proposal_id_str = f"{proposal_id}" MIGHT NOT NEED

            prompt_data = self.flipside_gov_data.prompt_stats("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
           
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
                - `proposal_description` = {proposal_text}
                - `1st choice votes` = {prompt_data["1st_choice_voting_power"]}
                - `2nd choice votes` = {prompt_data["2nd_choice_voting_power"]}
                - `1st choice name` = {prompt_data["1st_choice_name"]}
                - `2nd choice name` = {prompt_data["2nd_choice_name"]}
                - `leading_percent` = {prompt_data["leading_percent"]}
                - `voting_power_percentile` = {prompt_data["voting_power_percentile"]}
                - `voter_percentile` = {prompt_data["voter_percentile"]}

                ---

                ### **Intro**

                Start the first tweet of the thread with **`1/`**. Mention that the governance proposal with the title **`{{ proposal_title }}`** from **`{{ space_twitter_id }}`** is halfway through, and we are going to look at the activity so far.

                Ensure the tweet is under 245 characters. Do not include emojis.

                ---

                ### **Dynamic Conditions**

                Add context or comments based on specific voting or proposal dynamics. Only include one (most relevant):

                - **Close Vote:** If the top choice and the second choice voting power percentages are close, add a comment noting that it is a contentious vote.
                - **Overwhelming Lead:** If one choice is significantly ahead of the others, add a comment naming the choice and its dominance.
                - **Option Winning Without Majority:** If the leading option has less than 50% of the total voting power, add a comment noting the lack of a majority and the divided community.
                - **Discrepancy Between Popular Vote and Voting Power:** If the winner of the vote differs between the popular vote and voting power, note this discrepancy.
                - **High or Low Turnout Compared to Space Average:** If the halftime voter or voting power turnout percentile is unusually high or low for the voting space, add a comment on this.
                
                ### **Additional Instructions**

                - DO **NOT** include hashtags or emojis.
                - DO **NOT** add any additional text besides the tweet itself. 
            """

            part_1_message = self._generate_claude_response(prompt_for_first_tweet)
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
            - `proposal_title` = {proposal_title}
            - `space_twitter_id` = {twitter_handle}
            - `proposal_description` = {proposal_text}

            ---

            ### **Intro**

            Begin the tweet with **`2/`**. Reference the attached graph showing hourly voting activity and total votes by choice.

            Mention the total number of voters and votes for each choice using placeholders.
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional. Do not include emojis.

            ---

            ### **Dynamic Comments Based on Voting Activity**

            Add a comment based on the most relevant dynamic from the graph:

            - **Steady Voting Activity:** If the voting activity shows a consistent trend over time, highlight the steady engagement.
            - **Spikes in Voting Activity:** If there are noticeable spikes in voting at specific hours, comment on these trends.
            - **Choice Dominance:** If one choice is receiving significantly more votes than others, mention this dominance.
            - **Close Race:** If the votes between choices are close, note the competitive nature of the proposal.

             ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 
            """

            part_2_message = self._generate_claude_response(prompt_for_second_tweet)
            messages.append(part_2_message)

            # Tweet 3
            ################################################################

            prompt_for_third_tweet = f"""
            ### **Prompt Template for Third Tweet of a Thread (Voting Power Distribution)**

            ---

            ### **Required Inputs:**

            - `total_voters` = {prompt_data["total_voters"]}
            - `top_10%_voting_power_wallets` = {prompt_data["top_10%_voting_power_wallets"]}
            - `top_25%_voting_power_wallets` = {prompt_data["top_25%_voting_power_wallets"]}
            - `top_50%_voting_power_wallets` = {prompt_data["top_50%_voting_power_wallets"]}
            - `top_10%_voting_power_power` = {prompt_data["top_10%_voting_power_power"]}
            - `top_25%_voting_power_power` = {prompt_data["top_25%_voting_power_power"]}
            - `top_50%_voting_power_power` = {prompt_data["top_50%_voting_power_power"]}
            - `proposal_title` = {proposal_title}
            - `space_twitter_id` = {twitter_handle}
            - `proposal_description` = {proposal_text}

            ---

            ### **Intro**

            Begin the tweet with **`3/`**. Highlight the key insights about how voting power is distributed among participants in the proposal.

            Mention relevant data points using placeholders.
            Choose to emphasize concentration at the top, mid-tier wallet influence, or balanced distribution, depending on the data.
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional.

            ---

            ### **Dynamic Comments Based on Voting Power Distribution**

            Add a comment based on the most relevant dynamic from the voting power breakdown:

            - **Typical Pareto Distribution:** If the distribution follows a common pattern where a small group holds a large share of voting power, note this expected outcome.
            - **Extreme Concentration at the Top:** If a very small number of wallets control a significant portion of the voting power, highlight this notable concentration.
            - **Mid-Tier Wallet Influence:** If the top 25%-50% of wallets hold a significant share of voting power, emphasize their impact.
            - **Balanced Distribution:** If voting power is more evenly distributed than usual, highlight this as a positive sign for governance health.
            
            ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 

            """

            part_3_message = self._generate_claude_response(prompt_for_third_tweet)
            messages.append(part_3_message)

            # Tweet 4
            ################################################################

            prompt_for_fourth_tweet = f"""
            ### **Prompt Template for Fourth Tweet of a Thread (Voting Activity Comparison)**

            ---

            ### **Required Inputs:**

            - `voting_power_rank` = {prompt_data["voting_power_rank"]}
            - `voter_turnout_rank` = {prompt_data["voter_turnout_rank"]}
            - `voting_power_percentile` = {prompt_data["voting_power_percentile"]}
            - `voter_percentile` = {prompt_data["voter_percentile"]}
            - `proposal_title` = {[proposal_title]}
            - `space_twitter_id` = {twitter_handle}
            - `proposal_description` = {proposal_text}

            ---

            ### **Intro**

            Begin the tweet with **`4/`**. Compare the current proposal’s voting activity to other proposals within the same space at a similar stage.

            Mention relevant data points using placeholders.
            Ensure the tweet is under 245 characters. Keep the tone neutral and professional.

            ---

            ### **Dynamic Comments Based on Voting Activity Comparison**

            Add a comment based on the most relevant insight from the comparison of turnout data:

            - **High Turnout (Above 75th Percentile):** If both voter participation and voting power turnout are high, emphasize strong engagement.
            - **Low Turnout (Below 25th Percentile):** If both voter participation and voting power turnout are low, highlight the lack of engagement.
            - **Discrepancy Between Voters and Voting Power:** If voter turnout rank is significantly higher or lower than voting power rank, note this discrepancy.
            - **Top Performer (Rank 1-3):** If the proposal ranks in the top 1-3 spots for turnout so far, emphasize its leading position.
            - **Middle of the Pack (25th-75th Percentile):** If turnout falls between the 25th and 75th percentile, focus on balanced engagement.

             ### **Additional Instructions**

            - DO **NOT** include hashtags or emojis.
            - DO **NOT** add any additional text besides the tweet itself. 

            """

            part_4_message = self._generate_claude_response(prompt_for_fourth_tweet)
            messages.append(part_4_message)

            # Tweet 5
            ################################################################

            part_5_message = f"""
            5/ If you want to learn more about this {twitter_handle} proposal check out our @flipsidecrypto Dashboard:
            
            https://flipsidecrypto.xyz/pine/snapshot-proposal-lookup-nFH10H 
            
            To participate in the vote go here: {link_to_vote}
            """

            messages.append(part_5_message)

            # Append space_id and messages to the result list
            all_messages.append({
                "space_id": space_id,
                "messages": messages
            })
        
        # Output the messages to a file
        '''
        output_filename = "proposal_messages.txt"
        with open(output_filename, "w", encoding="utf-8") as file:
            for proposal_data in all_messages:
                space_id = proposal_data["space_id"]
                msgs = proposal_data["messages"]
                
                file.write(f"Space ID: {space_id}\n\n")  
                for msg in msgs:
                    file.write(msg + "\n\n")            
                file.write("-----\n\n")
        '''

        return all_messages
    
    def create_proposal_halftime(self):

        halftime_messages =  self.proposal_halftime_messages() 

        for proposal in halftime_messages: 
            space_id = proposal.get("space_id", "")
            messages = proposal.get("messages", "")
                        
            cover_image = self.generate_space_image(space_id, 2)
            orginal_post_id = self.twitter_client.post_with_media(messages[0], cover_image)

            Tweet2_media = self.flipside_gov_data.hourly_total_voting_power_by_choice("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
            thread1_id = self.twitter_client.post_thread_reply_with_media(messages[1], Tweet2_media, orginal_post_id)

            Tweet3_media = self.flipside_gov_data.voting_power_by_wallet("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
            thread2_id = self.twitter_client.post_thread_reply_with_media(messages[2], Tweet3_media, thread1_id)

            Tweet4_media = self.flipside_gov_data.space_proposals_by_voting_power("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
            thread3_id = self.twitter_client.post_thread_reply_with_media(messages[3], Tweet4_media, thread2_id)

            self.twitter_client.post_thread_reply(messages[4], thread3_id)

    
    def create_proposal_announcement(self):
        
        proposal_messages = self.proposal_announcement_messages()
        for proposal in proposal_messages: 
            space_id = proposal.get("space_id", "")
            messages = proposal.get("messages", "")
                        
            cover_image = self.generate_space_image(space_id, 1)

            orginal_post_id = self.twitter_client.post_with_media(messages[0], cover_image)
            thread1_id = self.twitter_client.post_thread_reply(messages[1], orginal_post_id)
            self.twitter_client.post_thread_reply(messages[2], thread1_id)


    def _generate_claude_response(self, prompt):
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=280,
                messages=[{"role": "user", "content": prompt}]
            )
            if response and hasattr(response, 'content'):
                text_block = response.content[0]
                final_message = text_block.text if hasattr(text_block, 'text') else "Error: No text found in response."
                return final_message
            else:
                return "Error: Invalid response format from Claude API."
        except Exception as claude_error:
            print(f"Error communicating with the Claude API: {claude_error}")
            return "Error: Unable to generate response."
        


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
        title_text = space_data["part1_text"] if part == 1 else space_data["part2_text"]

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
        title_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 125)  # Bold Segoe UI
        date_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 35)

        # Title text with bounding box
        bounding_box_width = 600  # Set the maximum width for the text
        wrapped_title = textwrap.fill(title_text, width=15)  # Wrap text to fit within the bounding box

        # Calculate position for wrapped text
        title_x = logo_position[0] + logo_size[0] + 50
        title_y = logo_position[1] + (logo_image.height // 4) - 85
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
        pill_x1, pill_y1, pill_x2, pill_y2 = base_image.width - 440, base_image.height - 200, base_image.width - 50, base_image.height - 100
        date_position = (pill_x1 + (pill_x2 - pill_x1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[2] // 2,
                        pill_y1 + (pill_y2 - pill_y1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[3] // 2)
        draw.text(date_position, current_date, fill="black", font=date_font)


        # Save the final output
        base_image.save(output_image_path)
        return output_image_path

if __name__ == "__main__": 
    governance_data = GovernanceHandler() 

    governance_data.create_proposal_halftime() 
    #print(result) 
    
    #governance_data.create_proposal_announcement()
     
    #path = governance_data.generate_space_image("arbitrumfoundation.eth", 1)
    #print(path) 

    #announcement_messages = governance_data.proposal_announcement_messages()
    #print(announcement_messages)


