import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html

# Load the datasets
listings = pd.read_csv('data/listings.csv.gz', compression='gzip')
reviews = pd.read_csv('data/reviews.csv.gz', compression='gzip')
review_languages = pd.read_csv('data/review_languages.csv.gz', compression='gzip')

# Merge reviews and review_languages to get language for each review
merged_reviews = pd.merge(reviews, review_languages, on='id', how='left')

# Group by listing_id and language, count the number of reviews
language_counts = merged_reviews.groupby(['listing_id', 'language']).size().reset_index(name='count')

# Find the most frequent language for each listing
most_frequent_languages = language_counts.sort_values(by='count', ascending=False).groupby('listing_id').first().reset_index()

# Merge with listings to get latitude and longitude
listings_with_languages = pd.merge(listings, most_frequent_languages, left_on='id', right_on='listing_id', how='left')

# Handle missing language values (fill with 'Unknown' or similar)
listings_with_languages['language'] = listings_with_languages['language'].fillna('Unknown')
listings_with_languages = listings_with_languages.dropna(subset=['count'])

# Create the map using Plotly Express
fig = px.scatter_map(
    listings_with_languages,
    lat='latitude',
    lon='longitude',
    color='language',
    size='count',
    hover_name='name',
    hover_data=['room_type', 'price', 'count'],
    zoom=11,
    title='Airbnb Listings in Lisbon by Most Frequent Review Language'
)

fig.update_layout(
    margin={'r': 0, 't': 40, 'l': 0, 'b': 0}
)

# Create a Dash app
app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Airbnb Listings in Lisbon'),
    dcc.Graph(id='airbnb-map', figure=fig)
])

if __name__ == '__main__':
    app.run_server(debug=True)