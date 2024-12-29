import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
from decimal import Decimal
from datetime import datetime
import os


class GraphGenerator:
    def __init__(self, output_dir="graphs", logo_path="pine_watermark.png"):
        """
        Initialize the GraphGenerator.
        :param output_dir: Directory to save generated graph images.
        """
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        self.logo_path = logo_path
        self.calmColors = ["#115f9a", "#1984c5", "#22a7f0", "#48b5c4", "#76c68f", "#a6d75b", "#c9e52f", "#d0ee11", "#d0f400"]

        # Set default font to Times New Roman
        plt.rcParams['font.family'] = 'Times New Roman'
        # Set the default background color to off-white
        plt.rcParams['figure.facecolor'] = '#f2efe9'

    def save_graph(self, fig, filename):
        """
        Save the graph as an image file.
        :param fig: Matplotlib figure object.
        :param filename: Name of the output file (without extension).
        """
        filepath = os.path.join(self.output_dir, f"{filename}.png")
        fig.savefig(filepath, format="png", bbox_inches="tight")
        plt.close(fig)
        return filepath

    def add_logo_to_figure(self, fig):
        """
        Add a logo to the top-left corner of the figure without a circular border.
        :param fig: Matplotlib figure object.
        """
        try:
            # Load the logo image
            logo_img = Image.open(self.logo_path)
            imagebox = OffsetImage(logo_img, zoom=0.11)  # Adjust zoom for appropriate size

            # Create an AnnotationBbox to place the logo in the figure
            ab = AnnotationBbox(
                imagebox,
                (0.01, 0.77),  # Adjusted to fit entirely on the image
                xycoords='figure fraction',  # Position relative to the whole figure
                frameon=False,  # No border around the logo
                box_alignment=(0, 1)  # Align the logo box to the top-left corner
            )
            fig.add_artist(ab)

            # Adjust the figure's layout to ensure the logo doesn't get cropped
            fig.subplots_adjust(top=0.75)
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
        labels = [point[0] for point in data]  # Categories.
        sizes = [float(point[1]) for point in data]  # Values.

        fig, ax = plt.subplots()
        ax.set_facecolor('#f2efe9')

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=self.calmColors[:len(sizes)])
        ax.set_title(title)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Add logo
        self.add_logo_to_figure(fig)

        return self.save_graph(fig, filename)


if __name__ == "__main__":
    graph_gen = GraphGenerator()

    data = [
        (datetime(2024, 8, 15, 0, 0), 2, Decimal('100.163265722')),
        (datetime(2024, 8, 16, 0, 0), 5, Decimal('100.1623662')),
        (datetime(2024, 8, 17, 0, 0), 8, Decimal('100.289026958')),
        (datetime(2024, 8, 18, 0, 0), 4, Decimal('100.357780737')),
        (datetime(2024, 8, 19, 0, 0), 10, Decimal('100.1623662')),
        (datetime(2024, 8, 20, 0, 0), 47, Decimal('100.289026958')),
        (datetime(2024, 8, 21, 0, 0), 60, Decimal('100.357780737')),
    ]

    file_path = graph_gen.create_multi_line_graph(
        data=data,
        x_label="Date",
        y_labels=["Net Holders", "Price"],
        title="Net Holders and Price Over Time",
        filename="test_multi_line_graph"
    )

    print(f"Graph saved at: {file_path}")
