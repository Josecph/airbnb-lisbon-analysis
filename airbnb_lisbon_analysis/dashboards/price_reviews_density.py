import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the datasets
listings_detailed = pd.read_csv("data/listings.csv.gz", compression="gzip")
reviews = pd.read_csv("data/reviews.csv.gz", compression="gzip")

# Clean and prepare the data
# 1. Calculate average price per listing
listings_detailed['price'] = listings_detailed['price'].str.replace('$', '').str.replace(',', '').astype(float)
avg_price = listings_detailed.groupby('id')['price'].mean().reset_index()
avg_price.rename(columns={'id': 'listing_id', 'price': 'avg_price'}, inplace=True)

# 2. Calculate the number of reviews per listing
review_counts = reviews['listing_id'].value_counts().reset_index()
#review_counts.rename(columns={'index': 'listing_id', 'listing_id': 'review_count'}, inplace=True)

# 3. Merge the dataframes
merged_data = pd.merge(listings_detailed, avg_price, left_on='id', right_on='listing_id', how='left')
merged_data = pd.merge(merged_data, review_counts, left_on='id', right_on='listing_id', how='left')

# Fill NaN review counts with 0
merged_data['review_count'] = merged_data['count'].fillna(0)

# Create the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H1("AirBnB Listings in Lisbon"),
    dcc.Graph(id='airbnb-map'),
    html.Div([
        html.Label("Review Count Threshold:"),
        dcc.Slider(
            id='review-slider',
            min=0,
            max=merged_data['review_count'].max(),
            value=0,
            step=1,
            marks={i: str(i) for i in range(0, int(merged_data['review_count'].max()) + 1, max(1, int(merged_data['review_count'].max() / 10)))}
        ),
    ], style={'width': '80%', 'margin': 'auto'})
])

# Callback to update the map based on the review count threshold
@app.callback(
    Output('airbnb-map', 'figure'),
    [Input('review-slider', 'value')]
)
def update_map(review_threshold):
    filtered_data = merged_data[merged_data['review_count'] >= review_threshold]

    fig = px.scatter_map(
        filtered_data,
        lat="latitude",
        lon="longitude",
        color="avg_price",
        size="review_count",
        hover_name="name",
        hover_data=["avg_price", "review_count"],
        color_continuous_scale=px.colors.sequential.Plasma,
        zoom=11,
        title="AirBnB Listings in Lisbon (Price vs. Reviews)",
    )
    fig.update_layout(mapbox_bounds={"west": filtered_data['longitude'].min()-0.05, "east": filtered_data['longitude'].max()+0.05, "south": filtered_data['latitude'].min()-0.05, "north": filtered_data['latitude'].max()+0.05})
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
