import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import gzip
import io
import numpy as np

listings = pd.read_csv('data/listings.csv.gz', compression='gzip')
calendar = pd.read_csv('data/calendar.csv.gz', compression='gzip')

# Data Preprocessing
# Convert price to numeric
calendar['price'] = calendar['price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

# Calculate price standard deviation per listing
price_std = calendar.groupby('listing_id')['price'].std().reset_index()
price_std.rename(columns={'price': 'price_std'}, inplace=True)

# Merge with listings data
listings = pd.merge(listings, price_std, left_on='id', right_on='listing_id', how='left')

# Drop NaN price_std values, if any.
listings = listings.dropna(subset=['price_std'])

# Dash App
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("AirBnB Listings in Lisbon with Price Deviation"),
    dcc.Graph(id='airbnb-map')
])

@app.callback(
    Output('airbnb-map', 'figure'),
    Input('airbnb-map', 'relayoutData')
)
def update_map(relayoutData):
    fig = px.scatter_map(
        listings,
        lat="latitude",
        lon="longitude",
        color="price_std",
        size_max=15,
        zoom=11,
        hover_name="name",
        hover_data=["price_std", "room_type", "neighbourhood_cleansed"],
        color_continuous_scale=px.colors.sequential.Plasma
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
