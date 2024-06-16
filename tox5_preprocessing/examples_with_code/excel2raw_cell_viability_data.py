import pandas as pd
import re
import os

# file = 'D:\\PhD\\projects\\ToxPi\\tox_data\\calibrate\\from_patrols\\nanodata-patrols\\misvik\\Patrols_HepG2_A549_Beas2b_HTS_data_Misvik.xlsx'
#
# sheet_name = 'Apoptosis data'
# # sheet_name = 'Cell viability data '
#
# raw_data_df = pd.read_excel(file, skiprows=2, usecols="A, D:AM", engine='openpyxl', sheet_name=sheet_name)
# print(raw_data_df)
#
# raw_data_df['row'] = raw_data_df['well'].apply(lambda x: re.match(r"([A-Za-z]+)([0-9]+)", x).groups()[0])
# raw_data_df['column'] = raw_data_df['well'].apply(lambda x: re.match(r"([A-Za-z]+)([0-9]+)", x).groups()[1])
# save_dir = 'D:\\PhD\\projects\\ToxPi\\tox_data\\patrols\\cell_viability_custom'
# for col in raw_data_df.columns[1:-2]:
#     matrix_df = raw_data_df.pivot(index='row', columns='column', values=col)
#     file_path = os.path.join(save_dir, f'{col}.csv')
#     matrix_df.to_csv(file_path)

# import matplotlib.pyplot as plt
# import mpld3
# import os
#
# # Sample data for the plot
# labels = ['Frogs', 'Hogs', 'Dogs', 'Logs']
# sizes = [15, 30, 45, 10]
#
# # Create a matplotlib Pie Chart
# fig, ax = plt.subplots()
# ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
# ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
#
# # Directory to save the output file
# output_directory = "output_directory"  # Replace with your desired directory
# os.makedirs(output_directory, exist_ok=True)  # Create directory if it doesn't exist
#
# # Save the figure as an interactive HTML file using mpld3
# figure_file_name_html = os.path.join(output_directory, 'tox_rank_pie_mpld3.html')
# mpld3.save_html(fig, figure_file_name_html)
#
# print(f"Saved interactive plot to {figure_file_name_html}")
#
# # Show the interactive plot immediately in the browser
# mpld3.show(fig)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(rows=2, cols=2, specs=[[{'type': 'polar'}]*2]*2)

fig.add_trace(go.Scatterpolar(
      name = "angular categories",
      r = [5, 4, 2, 4, 5],
      theta = ["a", "b", "c", "d", "a"],
    ), 1, 1)
fig.add_trace(go.Scatterpolar(
      name = "radial categories",
      r = ["a", "b", "c", "d", "b", "f", "a"],
      theta = [1, 4, 2, 1.5, 1.5, 6, 5],
      thetaunit = "radians",
    ), 1, 1)
fig.add_trace(go.Scatterpolar(
      name = "angular categories (w/ categoryarray)",
      r = [5, 4, 2, 4, 5],
      theta = ["a", "b", "c", "d", "a"],
    ), 2, 1)
fig.add_trace(go.Scatterpolar(
      name = "radial categories (w/ category descending)",
      r = ["a", "b", "c", "d", "b", "f", "a", "a"],
      theta = [45, 90, 180, 200, 300, 15, 20, 45],
    ), 2, 2)

fig.update_traces(fill='toself')
fig.update_layout(
    polar = dict(
      radialaxis_angle = -45,
      angularaxis = dict(
        direction = "clockwise",
        period = 6)
    ),
    polar2 = dict(
      radialaxis = dict(
        angle = 180,
        tickangle = -180 # so that tick labels are not upside down
      )
    ),
    polar3 = dict(
      sector = [80, 400],
      radialaxis_angle = -45,
      angularaxis_categoryarray = ["d", "a", "c", "b"]
    ),
    polar4 = dict(
      radialaxis_categoryorder = "category descending",
      angularaxis = dict(
        thetaunit = "radians",
        dtick = 0.3141592653589793
      ))
)

fig.show()
