import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv
import psycopg2
import random

class GraphGenerator:
    def __init__(self, output_dir="graphs", logo_path="Image_bank/pine_watermark.png"):
        """
        Initialize the GraphGenerator.
        :param output_dir: Directory to save generated graph images.
        """

        load_dotenv() 

        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.logo_path = logo_path
        self.calmColors = ["#2A503A", "#8BC9A3", "#3E9F73", "#3AB0AA", "#EEDC82", "#F4A261", "#F4D3D6", "#6D8AA7"]

        # Set default font to Times New Roman
        plt.rcParams['font.family'] = 'Times New Roman'
        # Set the default background color to off-white
        plt.rcParams['figure.facecolor'] = '#f2efe9'

        self.db_config = {
            "host": os.getenv("DATABASE_HOST"),
            "database": "CARROT_DB", 
            "user": os.getenv("DATABASE_USER"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "port": 5432
        }
    
    def execute_and_prepare_queries(self, additional_queries):
        """
        Executes SQL queries from additional_queries, cleans data, and returns results.
        :param additional_queries: List of dictionaries containing SQL queries, graph types, and final columns.
        :return: List of tuples (cleaned_data, graph_type, final_columns).
        """
        query_results = []

        try:
            # Connect to the PostgreSQL database
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    for query_info in additional_queries:
                        try:
                            sql_query = query_info["sql_query"]
                            graph_type = query_info["graph_type"]
                            final_columns = query_info["final_columns"]
                            graph_title = query_info["graph_title"]

                            formatted_sql = f"""{sql_query}"""
                            cursor.execute(formatted_sql)
                            raw_data = cursor.fetchall()
                            
                            # Append results as a tuple (cleaned_data, graph_type, final_columns)
                            query_results.append((raw_data, graph_type, final_columns, graph_title))
                            
                        except Exception as query_error:
                            print(f"Error executing query: {sql_query}. Error: {query_error}")
        except Exception as db_error:
            print(f"Database connection error: {db_error}")

        return query_results


    def save_graph(self, fig, filename):
        """
        Save the graph as an image file.
        :param fig: Matplotlib figure object.
        :param filename: Name of the output file (without extension).
        """
        filepath = os.path.join(self.output_dir, f"{filename}.png")
        filepath = os.path.normpath(filepath)
        fig.savefig(filepath, format="png", bbox_inches="tight")
        plt.close(fig)
        return filepath

    def add_logo_to_figure(self, fig):
        """
        Add a logo to the top-left corner of the figure with sufficient spacing.
        :param fig: Matplotlib figure object.
        """

        try:
            #fig.subplots_adjust(top=0.95, left=0.15, right=0.97, bottom=0.15)
            fig.subplots_adjust(top=0.85)
            # Load the logo image
            logo_img = Image.open(self.logo_path)
            imagebox = OffsetImage(logo_img, zoom=0.12)  # Adjust zoom for appropriate size

            # Create an AnnotationBbox to place the logo in the figure
            ab = AnnotationBbox(
                imagebox,
                (0.01, 0.95),  # Adjusted to the top-left corner of the figure
                xycoords='figure fraction',  # Relative to the whole figure
                frameon=False,  # No border around the logo
                box_alignment=(0, 1)  # Align the logo to the top-left corner
            )
            fig.add_artist(ab)
            
        except Exception as e:
            print(f"Error adding logo: {e}")


    def create_line_graph(self, data, x_label, y_label, title, filename):
        """
        Create a simple line graph with one X and one Y axis.
        :param data: List of tuples, where the first element is X (e.g., date) and the second element is Y (e.g., value).
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        x = [point[0] for point in data]  # Assuming first column is X (date).
        y = [float(point[1]) for point in data]  # Assuming second column is Y (metric).

        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')

        ax.plot(x, y, marker="o", color=self.calmColors[0])
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(True)
        fig.autofmt_xdate()

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)

    def create_multi_line_graph(self, data, x_label, y_labels, title, filename):
        """
        Create a multi-line graph with one X-axis and multiple Y-axes.
        :param data: List of tuples, where the first element is X (e.g., date) and subsequent elements are Y (e.g., metrics).
        :param x_label: Label for the X-axis.
        :param y_labels: List of labels for each Y series.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        x = [point[0] for point in data]  # Assuming first column is X (date).
        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')

        # Iterate through each Y series in the data (from index 1 onward).
        for i in range(1, len(data[0])):
            y = [float(point[i]) for point in data]  # Extract Y values for this series.
            label = y_labels[i - 1]  # Use the corresponding label from y_labels.
            ax.plot(x, y, label=label, marker="o", color=self.calmColors[i - 1 % len(self.calmColors)])

        ax.set_xlabel(x_label)
        
        ax.set_ylabel(" / ".join(y_labels))  # Combined Y labels for the legend.
        ax.set_title(title)
        ax.legend()
        ax.grid(True)
        fig.autofmt_xdate()

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)

    def create_grouped_line_graph(self, data, x_label, y_label, title, filename):
        """
        Create a grouped line graph where the Y-axis is grouped by a key.
        :param data: List of tuples, where the first element is X (e.g., date),
                     the second element is a group/category, and the third element is Y (metric).
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        grouped_data = {}
        for point in data:
            x, group, y = point[0], point[1], point[2]
            if group not in grouped_data:
                grouped_data[group] = []
            grouped_data[group].append((x, y))

        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')


        # Create a line for each group.
        for idx, (group, points) in enumerate(grouped_data.items()):
            x = [point[0] for point in points]  # Extract X values (dates).
            y = [float(point[1]) for point in points]  # Extract Y values (metrics).
            ax.plot(x, y, label=group, marker="o", color=self.calmColors[idx % len(self.calmColors)])

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.legend()
        ax.grid(True)
        fig.autofmt_xdate()

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)

    def create_pie_chart(self, data, title, filename):
        """
        Create a pie chart.
        :param data: List of tuples, where the first element is a category, and the second element is a value.
        :param title: Title of the pie chart.
        :param filename: Name of the output file.
        """
        labels = [point[0] for point in data]  # Categories
        sizes = [float(point[1]) for point in data]  # Values

        fig, ax = plt.subplots(figsize=(8, 6))  # Adjust size as needed
        ax.set_facecolor('#f2efe9')

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.calmColors[:len(sizes)])
        ax.set_title(title)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Adjust figure margins to prevent cropping
        fig.subplots_adjust(top=0.85, left=0.1, right=0.9, bottom=0.1)

        # Add logo to the figure
        try:
            logo_img = Image.open(self.logo_path)
            imagebox = OffsetImage(logo_img, zoom=0.12)
            ab = AnnotationBbox(
                imagebox,
                (0.01, 0.8),  # Position in the top-left corner of the figure
                xycoords='figure fraction',
                frameon=False,
                box_alignment=(0, 1)
            )
            fig.add_artist(ab)
        except Exception as e:
            print(f"Error adding logo: {e}")

        return self.save_graph(fig, filename)
    

    def create_bar_chart(self, data, x_label, y_label, title, filename):
        """
        Create a simple bar chart.
        :param data: List of tuples, where the first element is X (e.g., category or date) 
                    and the second element is Y (e.g., value).
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        x = [point[0] for point in data]  # Assuming first column is X (category or date).
        y = [float(point[1]) for point in data]  # Assuming second column is Y (value).

        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')

        ax.bar(x, y, color=self.calmColors[0], zorder=3)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.grid(axis='y', zorder=1)  # Add horizontal grid lines for readability
        fig.autofmt_xdate()

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)
    

    def create_stacked_bar_chart(self, data, x_label, y_label, title, filename):
        """
        Create a stacked bar chart.
        :param data: List of tuples, where the first element is X (e.g., category or date),
                    the second element is a group/category, and the third element is Y (metric).
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        grouped_data = {}
        for point in data:
            x, group, y = point[0], point[1], point[2]
            if group not in grouped_data:
                grouped_data[group] = []
            grouped_data[group].append((x, y))

        x_labels = sorted(set(point[0] for point in data))  # Unique X labels in order
        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')

        bottom_values = [0] * len(x_labels)  # To keep track of the cumulative Y values for stacking
        for idx, (group, points) in enumerate(grouped_data.items()):
            group_y = [float(dict(points).get(x, 0)) for x in x_labels]  # Get Y values for the group
            ax.bar(x_labels, group_y, bottom=bottom_values, label=group, color=self.calmColors[idx % len(self.calmColors)], edgecolor='black', zorder=3)
            bottom_values = [sum(x) for x in zip(bottom_values, group_y)]  # Update bottom for next group

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.legend()
        ax.grid(axis='y', zorder=1)
        fig.autofmt_xdate()

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)
    

    def create_grouped_scatter_graph(self, data, x_label, y_label, title, filename):
        """
        Create a grouped scatter plot where the Y-axis is grouped by a key.
        :param data: List of tuples, where the first element is X (e.g., date),
                    the second element is a group/category, and the third element is Y (metric).
        :param x_label: Label for the X-axis.
        :param y_label: Label for the Y-axis.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        # Group data by 'group'
        grouped_data = {}
        for point in data:
            x, group, y = point[0], point[1], point[2]
            if group not in grouped_data:
                grouped_data[group] = []
            grouped_data[group].append((x, y))

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_facecolor('#f2efe9')

        # Create a scatter plot for each group
        for idx, (group, points) in enumerate(grouped_data.items()):
            x_vals = [pt[0] for pt in points]  # Extract X values
            y_vals = [float(pt[1]) for pt in points]  # Extract Y values
            ax.scatter(x_vals, y_vals, label=group, color=self.calmColors[idx % len(self.calmColors)], marker="o", zorder=3)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, zorder=1)
        fig.autofmt_xdate()

        fig.subplots_adjust(top=0.9)
        logo_img = Image.open(self.logo_path)
        imagebox = OffsetImage(logo_img, zoom=0.12)  # Adjust zoom to resize

        # 2) Adjust 'xy' and 'xycoords' to move the logo
        #    - (0.01, 0.95) means x=0.01, y=0.95 in figure fraction coordinates.
        #    - Increase x to move logo to the right, decrease x to move logo left.
        #    - Increase y to move logo higher, decrease y to move it lower.
        ab = AnnotationBbox(
            imagebox,
            (0.005, 0.87),           # <--- Change these numbers to move logo around
            xycoords='figure fraction',
            frameon=False,
            box_alignment=(0, 1)    # (0,1) aligns left edge & top edge of the image
        )
        fig.add_artist(ab)


        return self.save_graph(fig, filename)


    def generate_graphs(self, additional_queries):
        """
        Executes queries via `execute_and_prepare_queries` and generates graphs based on graph types.
        :param additional_queries: List of dictionaries containing SQL queries, graph types, and final columns.
        :return: List of file paths to the generated graphs.
        """
        # Step 1: Fetch query results
        query_results = self.execute_and_prepare_queries(additional_queries)

        # Step 2: Initialize a list to store file paths of generated graphs
        graph_file_paths = []

        # Step 3: Process the results and generate graphs
        for query_result in query_results:
            data, graph_type, final_columns, graph_title = query_result

            rand = random.randint(100000, 999999)

            # Generate the appropriate graph and store the file path
            if graph_type == "BASIC_LINE":
                graph_path = self.create_line_graph(
                    data=data,
                    x_label=final_columns[0],
                    y_label=final_columns[1],
                    title=graph_title,
                    filename=f"basic_line_{rand}"
                )
            elif graph_type == "MULTI_LINE":
                graph_path = self.create_multi_line_graph(
                    data=data,
                    x_label=final_columns[0],
                    y_labels=final_columns[1:],
                    title=graph_title,
                    filename=f"multi_line_{rand}"
                )
            elif graph_type == "GROUPED_LINE":
                graph_path = self.create_grouped_line_graph(
                    data=data,
                    x_label=final_columns[0],
                    y_label=final_columns[2],
                    title=graph_title,
                    filename=f"grouped_line_{rand}"
                )
            elif graph_type == "GROUPED_SCATTER":
                graph_path = self.create_grouped_scatter_graph(
                    data=data,
                    x_label=final_columns[0],
                    y_label=final_columns[2],
                    title=graph_title,
                    filename=f"grouped_scatter_1"
                )
            elif graph_type == "PIECHART":
                graph_path = self.create_pie_chart(
                    data=data,
                    title=graph_title,
                    filename=f"pie_chart_{rand}"
                )
            elif graph_type == "BASIC_BAR":
                graph_path = self.create_bar_chart(
                    data=data,
                    x_label=final_columns[0],
                    y_label=final_columns[1],
                    title=graph_title,
                    filename=f"basic_bar_{rand}"
                )
            elif graph_type == "STACKED_BAR":
                graph_path = self.create_stacked_bar_chart(
                    data=data,
                    x_label=final_columns[0],
                    y_label=final_columns[2],
                    title=graph_title,
                    filename=f"stacked_bar_{rand}"
                )
            else:
                print(f"Unsupported graph type: {graph_type}")
                graph_path = None

            if graph_path:
                graph_file_paths.append(graph_path)

        # Step 4: Return the list of file paths
        return graph_file_paths



if __name__ == "__main__":
    graph_gen = GraphGenerator()

    # Mock additional queries input
    additional_queries = [
          {
            "sql_query": "SELECT date_trunc('day', block_timestamp) as date, event_type, sum(amount) as Amount from carrot_burn_mint_actions where amount is not null and block_timestamp > current_date - 16 group by date, event_type order by date desc",
            "final_columns": ["Date", "event_type", "Amount"],
            "graph_type": "GROUPED_SCATTER",
            "graph_title" : "Daily Carrot minted and Burned" 
         }
    ]
 

    # Run the function and print results
    results = graph_gen.generate_graphs(additional_queries)
    print(results) 
 
    
"""
additional_queries = [
          {
            "sql_query": "SELECT date_trunc('day', block_timestamp) as date, event_type, sum(amount) as Amount from carrot_burn_mint_actions where amount is not null and block_timestamp > current_date - 16 group by date, event_type order by date desc",
            "final_columns": ["Date", "event_type", "Amount"],
            "graph_type": "STACKED_BAR",
            "graph_title" : "Daily Carrot minted and Burned" 
         },
         {
            "sql_query": "select block_timestamp, net_holders from tab1 where block_timestamp > current_date - 50 order by block_timestamp desc",
            "final_columns": ["Date", "Net Holders"],
            "graph_type": "BASIC_BAR",
            "graph_title" : "Daily Carrot Net Holders" 
        },
        {
            "sql_query": "select * from tab1 order by block_timestamp desc",
            "final_columns": ["Date", "Net Holders", "Carrot Price (USD)"],
            "graph_type": "MULTI_LINE",
            "graph_title" : "Daily Carrot Price and Net Holders" 
        }
    ]
"""