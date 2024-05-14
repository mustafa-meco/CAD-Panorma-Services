import json
import matplotlib.pyplot as plt

# Load data from data.json
with open('data.json', 'r') as file:
    data = json.load(file)

# Find the minimum row and column values to determine the origin
min_row = min(entry['row'] for entry in data)
min_column = min(entry['column'] for entry in data)

# Map points to the origin
mapped_data = [{'row': entry['row'] - min_row, 'column': entry['column'] - min_column} for entry in data]

# Extract mapped x and y coordinates from the data
mapped_x_values = [entry['row'] for entry in mapped_data]
mapped_y_values = [entry['column'] for entry in mapped_data]

# Create a scatter plot of mapped data
plt.scatter(mapped_x_values, mapped_y_values, marker='o', color='blue')
plt.xlabel('Mapped Row')
plt.ylabel('Mapped Column')
plt.title('Scatter Plot of Mapped Data')
plt.grid(True)
plt.show()
