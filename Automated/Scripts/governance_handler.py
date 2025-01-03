from PIL import Image, ImageDraw, ImageFont
import textwrap
import json
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import psycopg2
import os

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
    
    def get_new_proposals(self): 
        proposals = []
        try:
            # Connect to the PostgreSQL database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    sql_query = """SELECT * FROM new_proposals LIMIT 1"""
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
        messages = []
        for proposal in self.new_proposals:
            # Extract proposal data
            proposal_id = proposal['proposal_id']
            proposal_title = proposal['proposal_title']
            proposal_text = proposal['proposal_text']
            choices = proposal['choices']
            proposal_start_time = proposal['proposal_start_time']
            proposal_end_time = proposal['proposal_end_time']
            space_id = proposal['space_id']
            network = proposal['network'] 
            link_to_vote = f"https://snapshot.box/#/s:{space_id}/proposal/{proposal_id}"

            # Generate first part
            part_1_prompt = (
                f"Write a professional and concise tweet to announce a new governance proposal. "
                f"The tweet must highlight the proposal's title ({proposal_title}), the space ID ({space_id}), "
                f"and the proposal's live period (from {proposal_start_time} to {proposal_end_time}). "
                f"Do not include hashtags or emojis."
                f"this should start with 1/"
                f"this should not call to action just infom"
            )
            part_1_message = self._generate_claude_response(part_1_prompt)
            messages.append(part_1_message)

            # Generate second part
            part_2_prompt = (
                f"Write a professional and concise tweet summarizing the details of the proposal. Use the following text to explain "
                f"what the proposal is about: {proposal_text}. Briefly mention the choices available: {choices}. "
                f"Do not include hashtags or emojis."
                f"this should start with 2/"
            )
            part_2_message = self._generate_claude_response(part_2_prompt)
            messages.append(part_2_message)

            # Generate third part
            part_3_prompt = (
                f"Write a professional and concise tweet to provide readers a link to vote if the want to participate. Include the link to vote: {link_to_vote}. "
                f"Do not include hashtags or emojis."
                f"this should start with 3/"
            )
            part_3_message = self._generate_claude_response(part_3_prompt)
            messages.append(part_3_message)

        return messages
    
    def create_proposal_announcement(self):
        
        messages = self.proposal_announcement_messages()




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
        spaces_json_path = os.path.join(script_dir, "Image_bank", "spaces.json")
        output_image_path = os.path.join(script_dir, "Image_bank", "final_output_image.png")

        # Load the spaces.json file
        with open(spaces_json_path, "r") as file:
            spaces_data = json.load(file)

        # Validate space_id
        if space_id not in spaces_data:
            raise ValueError(f"Space ID '{space_id}' not found in spaces.json")

        # Get space details
        space_data = spaces_data[space_id]
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
        title_y = logo_position[1] + (logo_image.height // 4) - 50
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
        pill_x1, pill_y1, pill_x2, pill_y2 = base_image.width - 440, base_image.height - 190, base_image.width - 50, base_image.height - 100
        date_position = (pill_x1 + (pill_x2 - pill_x1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[2] // 2,
                        pill_y1 + (pill_y2 - pill_y1) // 2 - draw.textbbox((0, 0), current_date, font=date_font)[3] // 2)
        draw.text(date_position, current_date, fill="black", font=date_font)

        # Save the final output
        base_image.save(output_image_path)
        return output_image_path

if __name__ == "__main__": 
    governance_data = GovernanceHandler() 
    
    path = governance_data.generate_space_image("arbitrumfoundation.eth", 1)
    print(path) 

    
    #announcement_messages = governance_data.proposal_announcement_messages()
    #print(announcement_messages)
