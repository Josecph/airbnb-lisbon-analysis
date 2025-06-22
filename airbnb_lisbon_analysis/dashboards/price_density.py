import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html

# 1. Load the data
listings_df = pd.read_csv('data/listings.csv.gz', compression='gzip')  # Use the summary listings for simplicity

# 2. Clean and prepare the data
# Handle missing prices and convert to numeric
listings_df['price'] = listings_df['price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)
listings_df = listings_df.dropna(subset=['latitude', 'longitude', 'price'])

# 3. Create the scatter map using Plotly Express
fig = px.scatter_map(
    listings_df,
    lat='latitude',
    lon='longitude',
    color='price',
    size_max=15,  # Adjust size as needed
    zoom=12,  # Adjust zoom level for Lisbon
    title='Airbnb Listings in Lisbon - Price Distribution',
    hover_name='name',  # Display listing name on hover
    hover_data=['room_type', 'neighbourhood'] #Display room type and neighborhood on hover
)

fig.update_layout(
    margin={'r': 0, 't': 40, 'l': 0, 'b': 0}
)

# 4. Create the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Airbnb Listings in Lisbon'),

    dcc.Graph(
        id='airbnb-map',
        figure=fig
    )
])

# 5. Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
