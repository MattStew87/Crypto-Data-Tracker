import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import os
from dotenv import load_dotenv
import numpy as np
from collections import defaultdict
import matplotlib.dates as mdates


class GraphGenerator:
    def __init__(self, output_dir="graphs", watermark_path="Image_bank/pine_watermark_gov.png"):
        """
        Initialize the GraphGenerator.
        :param output_dir: Directory to save generated graph images.
        """
        load_dotenv() 

        script_dir = os.path.dirname(os.path.abspath(__file__))

        self.output_dir = os.path.join(script_dir, output_dir)
        self.watermark_path = os.path.join(script_dir, watermark_path)
        os.makedirs(self.output_dir, exist_ok=True)

        self.calmColors = ["#2A503A", "#8BC9A3", "#3E9F73", "#3AB0AA", "#EEDC82", "#F4A261", "#F4D3D6", "#6D8AA7"]
        plt.rcParams['font.family'] = 'Liberation Serif' 
        plt.rcParams['figure.facecolor'] = '#f2efe9' # Set the default background color to off-white


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
    
    
    def add_watermark_to_figure(self, fig, ax):
        """
        Add a semi-transparent watermark at the center of the figure.
        :param fig: Matplotlib figure object.
        :param ax: Matplotlib axis object.
        """
        try:
            watermark_img = Image.open(self.watermark_path).convert("RGBA")

            # Resize watermark to 25% of its current size
            fig_width, fig_height = fig.get_size_inches()
            watermark_size = (int(fig_width * 80), int(fig_height * 80))  # Reduced size by 50%
            watermark_img = watermark_img.resize(watermark_size, Image.LANCZOS)

            # Reduce transparency (increase visibility slightly)
            alpha = 0.6  # Adjusted from 0.2 to 0.3
            watermark_array = np.array(watermark_img)
            watermark_array[..., 3] = (watermark_array[..., 3] * alpha).astype(np.uint8)
            watermark_img = Image.fromarray(watermark_array)

            # Overlay watermark on the figure
            imagebox = OffsetImage(watermark_img, zoom=0.25, alpha=alpha)  # Reduced zoom
            ab = AnnotationBbox(
                imagebox, (0.5, 0.5),  
                xycoords='axes fraction',  
                frameon=False  
            )
            ax.add_artist(ab)

        except Exception as e:
            print(f"Error adding watermark: {e}")



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

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax)

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

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax)

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

         # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax) 

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

        fig, ax = plt.subplots()  # Adjust size as needed
        ax.set_facecolor('#f2efe9')

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.calmColors[:len(sizes)])
        ax.set_title(title)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

         # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax) 

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

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax) 

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

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax)

        return self.save_graph(fig, filename)


    
    def create_bar_line_graph(self, data, x_label, y_labels, title, filename):
        """
        Create a bar and line graph with one X-axis and two Y-series.
        The first Y-series will be displayed as a bar, and the second as a line.
        
        :param data: List of tuples, where the first element is X (e.g., date),
                    the second element is Y1 (e.g., hourly total, shown as bars),
                    and the third element is Y2 (e.g., cumulative total, shown as a line).
        :param x_label: Label for the X-axis.
        :param y_labels: List with two labels, where the first is for the bar and the second is for the line.
        :param title: Title of the graph.
        :param filename: Name of the output file.
        """
        if len(y_labels) != 2:
            raise ValueError("y_labels must contain exactly two elements: one for the bar and one for the line.")

        x = [point[0] for point in data]  # Extract X-axis (dates)
        y1 = [float(point[1]) for point in data]  # Extract first Y-axis (bars)
        y2 = [float(point[2]) for point in data]  # Extract second Y-axis (line)

        fig, ax1 = plt.subplots()
        ax1.set_facecolor('#f2efe9')

        # Create bars for the first Y-axis
        ax1.bar(x, y1, color=self.calmColors[0], label=y_labels[0], zorder=3)  # Removed alpha
        ax1.set_xlabel(x_label, color="black")  # Set label color to black
        ax1.set_ylabel(y_labels[0], color="black")  # Set label color to black
        ax1.tick_params(axis='y', colors="black")  # Ensure tick labels are black
        ax1.tick_params(axis='x', colors="black")  # Ensure X-axis labels are black

        # Create a secondary Y-axis for the line graph
        ax2 = ax1.twinx()
        ax2.plot(x, y2, marker="o", color=self.calmColors[1], label=y_labels[1], linestyle='-', linewidth=2, zorder=4)
        ax2.set_ylabel(y_labels[1], color="black")  # Set label color to black
        ax2.tick_params(axis='y', colors="black")  # Ensure Y-axis labels are black

        # Formatting
        ax1.grid(axis='y', zorder=1) 
        fig.autofmt_xdate()
        ax1.set_title(title, color="black")  # Set title color to black

        # Add legends
        ax1.legend(loc="upper left", facecolor='#f2efe9', edgecolor="black")
        ax2.legend(loc="upper right", facecolor='#f2efe9', edgecolor="black")

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax1)

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

        fig, ax = plt.subplots()
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

        # Add watermark [DONE]
        self.add_watermark_to_figure(fig, ax) 


        return self.save_graph(fig, filename)




