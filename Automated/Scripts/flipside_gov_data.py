import os
from dotenv import load_dotenv
from flipside import Flipside
from graph_generator import GraphGenerator
from datetime import datetime


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
        

        voter_file_path = self.graph_generator.create_grouped_line_graph(voters_data, voter_columns[0], voter_columns[2], 'Hourly Total Voters by Choice', 'hourly_total_voters_by_choice')
        voting_power_file_path = self.graph_generator.create_grouped_line_graph(voting_power_data, voter_power_columns[0], voter_power_columns[2], 'Hourly Total Voting Power by Choice', 'hourly_total_voting_power_by_choice')
        # Return or process them further as you like
       
        Tweet2_data = [voter_file_path, voting_power_file_path] 
        
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
        

        
        voter_file_path = self.graph_generator.create_bar_chart(voters_data, "Voting Power Group", "Wallets", 'Voters by Wallet Voting Power Group', 'voters_by_wallet_voting_power_group')
        voting_power_file_path = self.graph_generator.create_bar_chart(voting_power_data, "Voting Power Group", "Voting Power", 'Voting Power by Wallet Voting Power Group', 'voting_power_by_wallet_voting_power_group')
        # Return or process them further as you like
    
        Tweet3_data = [voter_file_path, voting_power_file_path] 
        
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


        voter_file_path = self.graph_generator.create_grouped_scatter_graph(voters_data, "Start Time", "Total Voters", 'Space Proposals by Voters', 'space_proposals_by_voters')
        voting_power_file_path = self.graph_generator.create_grouped_scatter_graph(voting_power_data, "Start Time", "Total Voting Power", 'Space Proposals by Voting Power', 'space_proposals_by_voting_power')

        Tweet4_data = [voter_file_path, voting_power_file_path] 
        
        return Tweet4_data

    def prompt_stats(self, proposal_id): 
        prompt_data = {}

        # Part1
        ###########################################################

        sql1 = f"""
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
                selected_choice,
                COUNT(DISTINCT voter) AS voters,
                SUM(vp) AS voting_power
            FROM (
                SELECT 
                    VOTER,
                    numeric_vote_option,
                    c,
                    selected_choice,
                    VOTING_POWER AS vp,
                    hour,
                    VOTE_TIMESTAMP
                FROM tab1
                WHERE rn = 1
            )
            GROUP BY 1
            ORDER BY voting_power DESC
        """

        # Submit the query and await the results in one step.
        result1 = self.flipside.query(sql1)

        records1 = result1.records
        if not records1:
            return prompt_data  # No data returned

        # Calculate totals across *all* choices
        total_voting_power = sum(row["voting_power"] for row in records1)
        total_voters = sum(row["voters"] for row in records1)

        # Because we ORDER BY voting_power DESC, the first row is the #1 choice
        first_choice  = records1[0]
        second_choice = records1[1] if len(records1) > 1 else None

        # Compute leading_percent based on the first choice’s voting power
        leading_percent = 0
        if total_voting_power > 0:
            leading_percent = (first_choice["voting_power"] / total_voting_power) * 100

        # Populate prompt_data
        prompt_data["1st_choice_voting_power"] = first_choice["voting_power"]
        prompt_data["1st_choice_name"] = first_choice["selected_choice"]

        if second_choice:
            prompt_data["2nd_choice_voting_power"] = second_choice["voting_power"]
            prompt_data["2nd_choice_name"] = second_choice["selected_choice"]
        else:
            prompt_data["2nd_choice_voting_power"] = 0
            prompt_data["2nd_choice_name"] = "N/A"

        prompt_data["leading_percent"] = leading_percent
        prompt_data["total_voting_power"] = total_voting_power
        prompt_data["total_voters"] = total_voters

        # Part2
        ###########################################################

        sql2 = f"""
            WITH tab1 AS (
                SELECT space_id
                FROM external.snapshot.fact_proposals
                WHERE proposal_id LIKE '{proposal_id}'
            ),
            tab2 AS (
                SELECT 
                    proposal_id,
                    proposal_start_time,
                    proposal_end_time,
                    PROPOSAL_TITLE
                FROM external.snapshot.fact_proposals
                WHERE space_id IN (SELECT space_id FROM tab1)
            ),
            halfway_time AS (
                SELECT 
                    proposal_id,
                    PROPOSAL_TITLE,
                    proposal_start_time,
                    proposal_end_time,
                    TIMESTAMPADD(
                    SECOND, 
                    DATEDIFF(SECOND, proposal_start_time, proposal_end_time) / 2, 
                    proposal_start_time
                    ) AS halfway_point
                FROM tab2
            ),
            proposal_data AS (
                SELECT 
                    ez.proposal_id,
                    ht.PROPOSAL_TITLE,
                    CASE WHEN ez.proposal_id LIKE '{proposal_id}' THEN 'Selected Proposal' ELSE 'Other Proposal' END AS proposal_type,
                    MIN(ez.vote_timestamp) AS start_time,
                    COUNT(DISTINCT ez.voter) AS voters,
                    SUM(ez.voting_power) AS total_voting_power
                FROM external.snapshot.ez_snapshot AS ez
                JOIN halfway_time AS ht
                    ON ez.proposal_id = ht.proposal_id
                WHERE ez.vote_timestamp <= ht.halfway_point
                GROUP BY 1, 2, 3
            ),
            ranked_proposals AS (
            SELECT 
                proposal_id,
                proposal_type,
                PROPOSAL_TITLE,
                voters,
                start_time,
                total_voting_power,
                RANK() OVER (ORDER BY total_voting_power DESC) AS voting_power_rank,
                RANK() OVER (ORDER BY voters DESC) AS voters_rank,
                COUNT(*) OVER () AS total_proposals,
                PERCENT_RANK() OVER (ORDER BY voters DESC) AS voters_percentile,
                PERCENT_RANK() OVER (ORDER BY total_voting_power DESC) AS voting_power_percentile
            FROM proposal_data
            )

            SELECT
            voting_power_rank,
            100 - ROUND(voting_power_percentile * 100, 2) AS voting_power_percentile_rank,
            voters_rank,
            100 - ROUND(voters_percentile * 100, 2) AS voters_percentile_rank
            FROM ranked_proposals
            Where PROPOSAL_ID LIKE '{proposal_id}'
        """

        result2 = self.flipside.query(sql2)
        records2 = result2.records

        # We expect exactly one row from this query.
        if records2:
            row = records2[0]
            # row2 keys will be lowercase, e.g. "voting_power_rank", etc.
            prompt_data["voting_power_rank"] = row["voting_power_rank"]
            prompt_data["voter_turnout_rank"] = row["voters_rank"]
            prompt_data["voting_power_percentile"] = row["voting_power_percentile_rank"]
            prompt_data["voter_percentile"] = row["voters_percentile_rank"]

        # Part3
        ###########################################################


        sql3 = f"""
            WITH tab1 AS (
            SELECT space_id
            FROM external.snapshot.fact_proposals
            WHERE proposal_id LIKE '{proposal_id}'
            ),
            proposal_data AS (
            SELECT 
                proposal_id,
                PROPOSAL_TITLE,
                CASE WHEN proposal_id LIKE '{proposal_id}' THEN 'Selected Proposal' ELSE 'Other Proposal' END AS proposal_type,
                MIN(vote_timestamp) AS start_time,
                COUNT(DISTINCT voter) AS voters,
                SUM(voting_power) AS total_voting_power
            FROM external.snapshot.ez_snapshot
            WHERE space_id IN (SELECT * FROM tab1)
            GROUP BY 1, 2, 3
            ),
            ranked_proposals AS (
            SELECT 
                proposal_id,
                proposal_type,
                PROPOSAL_TITLE,
                voters,
                start_time,
                total_voting_power,
                RANK() OVER (ORDER BY total_voting_power DESC) AS voting_power_rank,
                RANK() OVER (ORDER BY voters DESC) AS voters_rank,
                COUNT(*) OVER () AS total_proposals,
                PERCENT_RANK() OVER (ORDER BY voters DESC) AS voters_percentile,
                PERCENT_RANK() OVER (ORDER BY total_voting_power DESC) AS voting_power_percentile
            FROM proposal_data
            )

            SELECT
            voting_power_rank,
            100 - ROUND(voting_power_percentile * 100, 2) AS voting_power_percentile_rank,
            voters_rank,
            100 - ROUND(voters_percentile * 100, 2) AS voters_percentile_rank
            FROM ranked_proposals
            WHERE Proposal_ID LIKE '{proposal_id}'
        """

        result3 = self.flipside.query(sql3)
        records3 = result3.records

        # We expect exactly one row from this query.
        if records3:
            row = records3[0]
            # row2 keys will be lowercase, e.g. "voting_power_rank", etc.
            prompt_data["final_voting_power_rank"] = row["voting_power_rank"]
            prompt_data["final_voter_turnout_rank"] = row["voters_rank"]
            prompt_data["final_voting_power_percentile"] = row["voting_power_percentile_rank"]
            prompt_data["final_voter_percentile"] = row["voters_percentile_rank"]
    
        # Part4
        ###########################################################

        sql4 = f""" 
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
                ranked_wallets AS (
                SELECT 
                    VOTER,
                    VOTING_POWER,
                    ROW_NUMBER() OVER (ORDER BY VOTING_POWER DESC) AS rank,
                    SUM(VOTING_POWER) OVER () AS total_voting_power,
                    SUM(VOTING_POWER) OVER (ORDER BY VOTING_POWER DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_voting_power
                FROM (
                    SELECT 
                    VOTER,
                    VOTING_POWER
                    FROM tab1
                    WHERE rn = 1
                )
                ),
                percentile_calculations AS (
                SELECT 
                    rank,
                    VOTER,
                    VOTING_POWER,
                    cumulative_voting_power,
                    total_voting_power,
                    cumulative_voting_power / total_voting_power AS voting_power_percentage
                FROM ranked_wallets
                )

                SELECT 
                CASE 
                    WHEN voting_power_percentage <= 0.10 THEN 'Top 10%'
                    WHEN voting_power_percentage <= 0.25 THEN 'Top 25%'
                    WHEN voting_power_percentage <= 0.50 THEN 'Top 50%'
                    ELSE 'Others'
                END AS voting_power_group,
                COUNT(*) AS wallet_count,
                SUM(VOTING_POWER) AS total_voting_power
                FROM percentile_calculations
                GROUP BY 1
                ORDER BY CASE 
                WHEN voting_power_group = 'Top 10%' THEN 1
                WHEN voting_power_group = 'Top 25%' THEN 2
                WHEN voting_power_group = 'Top 50%' THEN 3
                ELSE 4
                END;
        """
        
        result4 = self.flipside.query(sql4)
        records4 = result4.records

        # Initialize defaults in case some groups are missing:
        prompt_data["top_10%_voting_power_wallets"] = 1
        prompt_data["top_25%_voting_power_wallets"] = 1
        prompt_data["top_50%_voting_power_wallets"] = 1
        prompt_data["top_10%_voting_power_power"]   = 1
        prompt_data["top_25%_voting_power_power"]   = 1
        prompt_data["top_50%_voting_power_power"]   = 1

        # Populate based on query results
        for row in records4:
            group_name = row["voting_power_group"]          # e.g. "Top 25%"
            wallet_count = row["wallet_count"]              # e.g. 2
            total_vp = row["total_voting_power"]            # e.g. 9107017

            if group_name == "Top 10%":
                prompt_data["top_10%_voting_power_wallets"] = wallet_count + 1 
                prompt_data["top_10%_voting_power_power"]   = total_vp
            elif group_name == "Top 25%":
                prompt_data["top_25%_voting_power_wallets"] = wallet_count + 1 
                prompt_data["top_25%_voting_power_power"]   = total_vp 
            elif group_name == "Top 50%":
                prompt_data["top_50%_voting_power_wallets"] = wallet_count + 1 
                prompt_data["top_50%_voting_power_power"]   = total_vp  


        return prompt_data



       
if __name__ == "__main__":
    flipside = FlipsideGovData()
    
    
    tweet2_path = flipside.hourly_total_voting_power_by_choice("0xe4ea71ad1e49384952cf6bfd8c02e3a0669fe8f2d3fe39f88d614bba358d0263")
    #print(tweet2_path) 
    tweet3_path = flipside.voting_power_by_wallet("0xe4ea71ad1e49384952cf6bfd8c02e3a0669fe8f2d3fe39f88d614bba358d0263")
    #print(tweet3_path) 
    tweet4_path = flipside.space_proposals_by_voting_power("0xe4ea71ad1e49384952cf6bfd8c02e3a0669fe8f2d3fe39f88d614bba358d0263")
    #print(tweet4_path)
    

    #data = flipside.prompt_stats("0x11953281aac686d41e57bfe4a1f341b1343f591096c583d738ebb9f317fa8a85")
    #print(data) 


    #results = flipside.space_proposals_by_voting_power("0x90fab9ab51bb8ca09bab7d76e7ccacaf7dad184e697c870c30957770211cc95d")
    #print(results)
