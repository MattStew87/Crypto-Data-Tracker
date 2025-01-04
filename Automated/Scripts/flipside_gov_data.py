import os
from dotenv import load_dotenv
import psycopg2
from flipside import Flipside
from graph_generator import GraphGenerator
from datetime import datetime
import time


class FlipsideGovData:

    def __init__(self): 
        # Load the .env file
        load_dotenv()   

        # Initialize `Flipside` with your API Key and API URL
        self.flipside = Flipside(
            os.getenv("FLIPSIDE_API_KEY"), 
            "https://api-v2.flipsidecrypto.xyz"
        )

        self.graph_generator = GraphGenerator() 

    
    def hourly_total_voting_power_by_choice(self, proposal_id):
        sql = f"""
        WITH tab1 AS (
            SELECT 
                VOTER,
                TO_NUMBER(
                REPLACE(
                    REPLACE(
                    REPLACE(ARRAY_TO_STRING(vote_option, ''), '[', ''), 
                    ']', ''), 
                    '"', ''
                )
                ) AS numeric_vote_option,
                PARSE_JSON(ARRAY_TO_STRING(CHOICES, ',')) AS c,
                c[(TO_NUMBER(
                REPLACE(
                    REPLACE(
                    REPLACE(ARRAY_TO_STRING(vote_option, ''), '[', ''), 
                    ']', ''), 
                    '"', ''
                )
                ) - 1)] AS selected_choice,
                VOTING_POWER,
                DATE_TRUNC('hour', VOTE_TIMESTAMP) AS hour,
                VOTE_TIMESTAMP,
                ROW_NUMBER() OVER (PARTITION BY VOTER ORDER BY VOTE_TIMESTAMP DESC) AS rn
            FROM external.snapshot.ez_snapshot
            WHERE PROPOSAL_ID LIKE '{proposal_id}'
                AND VOTING_POWER > 0
        ), 
        Final_tab as (
            SELECT
            hour,
            selected_choice,
            count(DISTINCT voter) as voters,
            sum(voters) over (partition by selected_choice order by hour) as total_voters,
            sum(vp) as voting_power,
            sum(voting_power) over (partition by selected_choice order by hour) as total_voting_power
            from(
                SELECT 
                VOTER,
                numeric_vote_option,
                c,
                selected_choice,
                VOTING_POWER as vp,
                hour,
                VOTE_TIMESTAMP
                FROM tab1
                WHERE rn = 1
            )
            GROUP by 1,2
        ) 
        Select 
            hour,
            selected_choice,
            total_voters, 
            total_voting_power
        from Final_tab
        order by hour
        """
        query_result_set = self.flipside.query(sql, page_number=1, page_size=1)

        # Pagination setup
        current_page_number = 1
        page_size = 1000  # Adjust as necessary
        total_pages = 2   # Start with 2 until we know the real number

        # List to store all rows
        all_rows = []

        # Paginate through all available pages
        while current_page_number <= total_pages:
            results = self.flipside.get_query_results(
                query_result_set.query_id,
                page_number=current_page_number,
                page_size=page_size
            )

            # Update total pages based on response
            total_pages = results.page.totalPages

            # Add records from this page to the list
            if results.records:
                all_rows.extend(results.records)

            # Increment page number to move to the next page
            current_page_number += 1

        # Now 'all_rows' contains every record for our query in dictionary form.
        # Build two separate lists of lists:
        #
        #   1) [hour, selected_choice, total_voters]
        #   2) [hour, selected_choice, total_voting_power]

        voters_data = []
        voting_power_data = []

        for row in all_rows:
            # Each 'row' is a dict with keys: "HOUR", "SELECTED_CHOICE", "TOTAL_VOTERS", "TOTAL_VOTING_POWER"
            hour_str = row["hour"]
            hour_val = datetime.strptime(hour_str, "%Y-%m-%dT%H:%M:%S.%fZ")

            choice_val = row["selected_choice"]
            total_voters_val = row["total_voters"]
            total_power_val = row["total_voting_power"]

            # Append to separate lists
            voters_data.append([hour_val, choice_val, total_voters_val])
            voting_power_data.append([hour_val, choice_val, total_power_val])

        #create_grouped_line_graph(self, data, x_label, y_label, title, filename):

        voter_columns = ["Hour", "Selected Choice", "Total Voters"]
        voter_power_columns = ["Hour", "Selected Choice", "Total Voting Power"]
        

        self.graph_generator.create_grouped_line_graph(voters_data, voter_columns[0], voter_columns[2], 'Hourly Total Voters by Choice', 'test')
        self.graph_generator.create_grouped_line_graph(voting_power_data, voter_power_columns[0], voter_power_columns[2], 'Hourly Total Voting Power by Choice', 'test2')
        # Return or process them further as you like
       
        Tweet2_data = {"voter" : {"data": voters_data, "x_label": "Hour", "y_label" : "Total Voters", "title" : "Hourly Total Voters by Choice"}, 
                 "voting_power" : {"data": voting_power_data, "x_label": "Hour", "y_label" : "Total Voting Power", "title" : "Hourly Total Voting Power by Choice"} }
        
        return Tweet2_data
    
    

    def voting_power_by_wallet(self, proposal_id):
        sql = f"""
        WITH tab1 AS (
            SELECT 
                VOTER,
                TO_NUMBER(
                REPLACE(
                    REPLACE(
                    REPLACE(ARRAY_TO_STRING(vote_option, ''), '[', ''), 
                    ']', ''), 
                    '"', ''
                )
                ) AS numeric_vote_option,
                PARSE_JSON(ARRAY_TO_STRING(CHOICES, ',')) AS c,
                c[(TO_NUMBER(
                REPLACE(
                    REPLACE(
                    REPLACE(ARRAY_TO_STRING(vote_option, ''), '[', ''), 
                    ']', ''), 
                    '"', ''
                )
                ) - 1)] AS selected_choice,
                VOTING_POWER,
                DATE_TRUNC('hour', VOTE_TIMESTAMP) AS hour,
                VOTE_TIMESTAMP,
                ROW_NUMBER() OVER (PARTITION BY VOTER ORDER BY VOTE_TIMESTAMP DESC) AS rn
            FROM external.snapshot.ez_snapshot
            WHERE PROPOSAL_ID LIKE '{proposal_id}'
                AND VOTING_POWER > 0
        )

        SELECT
        case when Voting_power < 10 then 'a/ below 10'
        when Voting_power < 100 then 'b/ 10-100'
        when Voting_power < 1000 then 'c/ 100-1K'
        when Voting_power < 10000 then 'd/ 1K-10K'
        when Voting_power < 100000 then 'e/ 10K-100K'
        when Voting_power < 1000000 then 'f/ 100K-1M'
        when Voting_power < 10000000 then 'g/ 1M-10M'
        else 'h/ 10M+' end as voting_power_group,
        count(*) as wallets,
        sum(Voting_power) as voting_power
        from (
            SELECT 
            VOTER,
            numeric_vote_option,
            c,
            selected_choice,
            VOTING_POWER,
            hour,
            VOTE_TIMESTAMP
            FROM tab1
            WHERE rn = 1
        )
        GROUP by 1
        order by voting_power_group 
        """
        query_result_set = self.flipside.query(sql, page_number=1, page_size=1)

        # Pagination setup
        current_page_number = 1
        page_size = 1000  # Adjust as necessary
        total_pages = 2   # Start with 2 until we know the real number

        # List to store all rows
        all_rows = []

        # Paginate through all available pages
        while current_page_number <= total_pages:
            results = self.flipside.get_query_results(
                query_result_set.query_id,
                page_number=current_page_number,
                page_size=page_size
            )

            # Update total pages based on response
            total_pages = results.page.totalPages

            # Add records from this page to the list
            if results.records:
                all_rows.extend(results.records)

            # Increment page number to move to the next page
            current_page_number += 1


        voters_data = []
        voting_power_data = []

        for row in all_rows:
            voting_power_group = row["voting_power_group"]
            wallets = row["wallets"]
            voting_power = row["voting_power"]

            # Append to separate lists
            voters_data.append([voting_power_group, wallets])
            voting_power_data.append([voting_power_group, voting_power])

        #    def create_bar_chart(self, data, x_label, y_label, title, filename):
        

        self.graph_generator.create_bar_chart(voters_data, "Voting Power Group", "Wallets", 'Voters by Wallet Voting Power Group', 'test')
        self.graph_generator.create_bar_chart(voting_power_data, "Voting Power Group", "Voting Power", 'Voting Power by Wallet Voting Power Group', 'test2')
        # Return or process them further as you like
    
        Tweet3_data = {"voter" : {"data": voters_data, "x_label": "Voting Power Group", "y_label" : "Wallets", "title" : "Voters by Wallet Voting Power Group"}, 
                    "voting_power" : {"data": voters_data, "x_label": "Voting Power Group", "y_label" : "Voting Power", "title" : "Voting Power by Wallet Voting Power Group"} }
        
        return Tweet3_data
    
    def space_proposals_by_voting_power(self, proposal_id):
        sql = f"""
            WITH tab1 AS (
                SELECT 
                    space_id
                FROM external.snapshot.fact_proposals
                WHERE proposal_id LIKE '{proposal_id}'
            ), 
            tab2 as (
                SELECT 
                    proposal_id,
                    proposal_start_time,
                    proposal_end_time
                FROM external.snapshot.fact_proposals
                where space_id in (SELECT space_id from tab1)
            ), 
            halfway_time AS (
                SELECT 
                    proposal_id,
                    proposal_start_time,
                    proposal_end_time,
                    TIMESTAMPADD(
                    SECOND, 
                    DATEDIFF(SECOND, proposal_start_time, proposal_end_time) / 2, 
                    proposal_start_time
                    ) AS halfway_point
                FROM tab2
            )

            SELECT 
            ez.proposal_id,
            CASE 
                WHEN ez.proposal_id LIKE '{proposal_id}' THEN 'Selected Proposal' 
                ELSE 'Other Proposal' 
            END AS proposal_type,
            MIN(ez.vote_timestamp) AS start_time,
            COUNT(DISTINCT ez.voter) AS voters,
            SUM(ez.voting_power) AS total_voting_power
            FROM external.snapshot.ez_snapshot AS ez
            JOIN halfway_time AS ht
                on ht.proposal_id = ez.proposal_id
            WHERE ez.vote_timestamp < ht.halfway_point
            GROUP BY 1, 2;
            Order by start_time  
        """
        query_result_set = self.flipside.query(sql, page_number=1, page_size=1)

        # Pagination setup
        current_page_number = 1
        page_size = 1000  # Adjust as necessary
        total_pages = 2   # Start with 2 until we know the real number

        # List to store all rows
        all_rows = []

        # Paginate through all available pages
        while current_page_number <= total_pages:
            results = self.flipside.get_query_results(
                query_result_set.query_id,
                page_number=current_page_number,
                page_size=page_size
            )

            # Update total pages based on response
            total_pages = results.page.totalPages

            # Add records from this page to the list
            if results.records:
                all_rows.extend(results.records)

            # Increment page number to move to the next page
            current_page_number += 1


        voters_data = []
        voting_power_data = []

        for row in all_rows:
            
            start_time_str = row["start_time"]
            start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")

            proposal_type = row["proposal_type"]
            total_voters = row["voters"]
            total_voting_power = row["total_voting_power"]

            # Append to separate lists
            voters_data.append([start_time, proposal_type, total_voters])
            voting_power_data.append([start_time, proposal_type, total_voting_power])

        #    def create_bar_chart(self, data, x_label, y_label, title, filename):
        

        self.graph_generator.create_grouped_scatter_graph(voters_data, "Start Time", "Total Voters", 'Space Proposals by Voters', 'test')
        self.graph_generator.create_grouped_scatter_graph(voting_power_data, "Start Time", "Total Voting Power", 'Space Proposals by Voting Power', 'test2')
        # Return or process them further as you like

        Tweet4_data = {"voter" : {"data": voters_data, "x_label": "Start Time", "y_label" : "Total Voters", "title" : "Space Proposals by Voters"}, 
                    "voting_power" : {"data": voters_data, "x_label": "Start Time", "y_label" : "Total Voting Power", "title" : "Space Proposals by Voting Power"} }
        
        return Tweet4_data

       
if __name__ == "__main__":
    flipside = FlipsideGovData()
    flipside.space_proposals_by_voting_power("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
