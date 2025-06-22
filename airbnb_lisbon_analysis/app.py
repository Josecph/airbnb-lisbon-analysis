import plotly.express as px
from dash import Dash, html, dcc, Output, Input
import geopandas as gpd
import pandas as pd

# Load the GeoJSON and CSV data
gdf = gpd.read_file("./data/lisbon_parishes.geojson")
quarterly_language_data = pd.read_csv("data/parish_data_quarterly.csv")

def mode(x):
    return x.mode()[0] if not x.empty else None  # Handle empty groups

aggregated_df = quarterly_language_data.groupby('parish_id').agg(
    total_reviews=('num_reviews', 'sum'),
    language=('language', mode)
).reset_index()

# Merge the dataframes based on the common 'id' column
merged_df = gdf.merge(aggregated_df, left_on="id", right_on='parish_id')

app = Dash()

# Initial choropleth map

# Create the initial choropleth map
unique_languages = merged_df['language'].unique().tolist()
color_discrete_map = {lang: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] for i, lang in enumerate(unique_languages)}

fig_map = px.choropleth_map(
    merged_df, 
    geojson=merged_df.geometry, 
    locations=merged_df.index,
    color="language",
    color_discrete_map=color_discrete_map,
    center={"lat": 38.8, "lon": -9.1500},  # Lisbon's coordinates,
    hover_name="name",
    zoom=10,
    map_style="carto-positron",
    hover_data=["language"]
)

fig_map.update_layout(
    margin={'r': 0, 'l': 0, 'b': 0, 't': 10},
    paper_bgcolor="#fbfbfa"
)

# Initial bar chart for total reviews per quarter

quarterly_reviews = quarterly_language_data.groupby('quarter')['num_reviews'].sum().reset_index()
fig_bar = px.bar(quarterly_reviews, x='quarter', y='num_reviews')

app.layout = html.Div(
    [
        html.H1(
            "AirBnB occupancy",
        ), # Large, centered, caps title
        html.P(
            "By nationality and parish (Region of Lisbon)"
        ),
        dcc.Graph(id='map-graph', figure=fig_map, style={
            'width': '100%', 
            'height': '60vh',
        }),
        dcc.Graph(id='bar-graph', figure=fig_bar, style={
            'width': '100%', 'height': '40vh'
        }),
    ]
)

@app.callback(
    Output('map-graph', 'figure'),
    Input('bar-graph', 'selectedData')
)
def update_map(selectedData):
    if selectedData and selectedData['points']:
        selected_quarters = [point['x'] for point in selectedData['points']]

        filtered_data = quarterly_language_data[quarterly_language_data['quarter'].isin(selected_quarters)]

        if filtered_data.empty:
            updated_merged_df = merged_df.copy()
            updated_merged_df['language'] = None # or set to other default value
        else:

            aggregated_filtered_df = filtered_data.groupby('parish_id').agg(
                language=('language', mode)
            ).reset_index()

            updated_merged_df = gdf.merge(aggregated_filtered_df, left_on="id", right_on='parish_id', how='left')
            updated_merged_df = merged_df[['id', 'name', 'geometry', 'parish_id']].merge(updated_merged_df[['parish_id','language']], on='parish_id', how='left')

        fig_updated_map = px.choropleth_map(
            updated_merged_df, 
            geojson=updated_merged_df.geometry, 
            locations=updated_merged_df.index,
            color="language",
            color_discrete_map=color_discrete_map,
            center={"lat": 38.8, "lon": -9.1500},
            hover_name="name",
            zoom=10,
            map_style="carto-positron",
            hover_data=["language"],
        )

        fig_updated_map.update_layout(
            margin={'r': 0, 'l': 0, 'b': 0, 't': 10},
            paper_bgcolor="#fbfbfa"
        )

        return fig_updated_map
    else:
        # Return the original map if no selection has been made
        return fig_map


if __name__ == '__main__':
    app.run(debug=True)