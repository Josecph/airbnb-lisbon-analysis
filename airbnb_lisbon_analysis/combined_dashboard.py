import pandas as pd
import geopandas as gpd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

COLORS = {
    'background': '#f8f9fa',
    'text': '#2c3e50',
    'primary': '#3498db',
    'secondary': '#e74c3c'
}

app = Dash(__name__, external_stylesheets=[
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
    "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap",
], suppress_callback_exceptions=True)

# --- Dashboard 1: Nationality & Parish ---
gdf = gpd.read_file("./data/lisbon_parishes.geojson")
quarterly_language_data = pd.read_csv("data/parish_data_quarterly.csv")


def mode(x):
    return x.mode()[0] if not x.empty else None


aggregated_df = quarterly_language_data.groupby('parish_id').agg(
    total_reviews=('num_reviews', 'sum'),
    language=('language', mode)
).reset_index()

merged_df = gdf.merge(aggregated_df, left_on="id", right_on='parish_id')
unique_languages = merged_df['language'].unique().tolist()
color_discrete_map = {
    lang: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
    for i, lang in enumerate(unique_languages)
}

fig_map = px.choropleth_map(
    merged_df,
    geojson=merged_df.geometry,
    locations=merged_df.index,
    color="language",
    color_discrete_map=color_discrete_map,
    center={"lat": 38.8, "lon": -9.1500},
    hover_name="name",
    zoom=10,
    map_style="carto-positron",
    hover_data=["language"]
)
fig_map.update_layout(
    margin={'r': 0, 'l': 0, 'b': 0, 't': 10},
    paper_bgcolor=COLORS['background'],
    plot_bgcolor=COLORS['background'],
    font={'family': 'Roboto'},
    hoverlabel={'font_size': 14, 'font_family': 'Roboto'}
)


quarterly_reviews = quarterly_language_data.groupby('quarter')['num_reviews'].sum().reset_index()
fig_bar = px.bar(quarterly_reviews, x='quarter', y='num_reviews')
fig_bar.update_layout(
    margin={'r': 20, 'l': 20, 'b': 20, 't': 30},
    paper_bgcolor=COLORS['background'],
    plot_bgcolor=COLORS['background'],
    font={'family': 'Roboto'},
    hoverlabel={'font_size': 14, 'font_family': 'Roboto'},
    xaxis={'gridcolor': '#eee'},
    yaxis={'gridcolor': '#eee'}
)


# --- Dashboard 2: Price Map ---
listings_df = pd.read_csv('data/listings.csv.gz', compression='gzip')
listings_df['price'] = listings_df['price'].str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(
    float)
listings_df = listings_df.dropna(subset=['latitude', 'longitude', 'price'])

fig_price = px.scatter_map(
    listings_df,
    lat='latitude',
    lon='longitude',
    color='price',
    size_max=15,
    zoom=12,
    title='Airbnb Listings in Lisbon - Price Distribution',
    hover_name='name',
    hover_data=['room_type', 'neighbourhood'],
    map_style="carto-positron"
)
fig_price.update_layout(
    margin={'r': 0, 't': 40, 'l': 0, 'b': 0},
    paper_bgcolor=COLORS['background'],
    font={'family': 'Roboto'},
    title={'font': {'size': 24, 'family': 'Roboto', 'color': COLORS['text']}}
)

# --- Dashboard 3: Price vs Reviews Map com Slider ---
reviews = pd.read_csv("data/reviews.csv.gz", compression="gzip")

listings_detailed = pd.read_csv("data/listings.csv.gz", compression="gzip")
listings_detailed['price'] = listings_detailed['price'].str.replace('$', '').str.replace(',', '').astype(float)
avg_price = listings_detailed.groupby('id')['price'].mean().reset_index()
avg_price.rename(columns={'id': 'listing_id', 'price': 'avg_price'}, inplace=True)

review_counts = reviews['listing_id'].value_counts().reset_index()
review_counts.columns = ['listing_id', 'review_count']

merged_data = pd.merge(listings_detailed, avg_price, left_on='id', right_on='listing_id', how='left')
merged_data = pd.merge(merged_data, review_counts, left_on='id', right_on='listing_id', how='left')
merged_data['review_count'] = merged_data['review_count'].fillna(0)

# --- Layout com abas ---
app.layout = html.Div([
    html.Div([
        html.H1("Lisbon Airbnb Analytics",
                className="text-center mt-4 mb-4",
                style={'color': COLORS['text'],
                       'font-family': 'Roboto',
                       'font-weight': '500'}),
        dcc.Tabs(
            id="tabs",
            value='tab1',
            className="mb-4",
            style={'font-family': 'Roboto'},
            colors={
                "border": COLORS['primary'],
                "primary": COLORS['primary'],
                "background": COLORS['background']
            },
            children=[
                dcc.Tab(label='Occupancy by Nationality & Parish', value='tab1'),
                dcc.Tab(label='Price Distribution Map', value='tab2'),
                dcc.Tab(label='Price vs Reviews Map', value='tab3'),
            ]
        )
    ], className="container"),
    html.Div(id='tabs-content',
             className="container",
             style={'background': COLORS['background'],
                    'padding': '20px',
                    'border-radius': '8px',
                    'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'})
])


# --- Callback para renderizar abas ---
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab(tab):
    if tab == 'tab1':
        return html.Div([
            html.P("By nationality and parish (Region of Lisbon)"),
            dcc.Graph(figure=fig_map, style={'height': '60vh'}),
            dcc.Graph(figure=fig_bar, style={'height': '35vh'})
        ])
    elif tab == 'tab2':
        return html.Div([
            html.P("Airbnb Price Distribution"),
            dcc.Graph(figure=fig_price)
        ])
    elif tab == 'tab3':
        return html.Div([
            html.P("Airbnb Listings (Filtered by Review Count)"),
            dcc.Graph(id='airbnb-map'),
            html.Div([
                html.Label("Review Count Threshold:"),
                dcc.Slider(
                    id='review-slider',
                    min=0,
                    max=int(merged_data['review_count'].max()),
                    value=0,
                    step=1,
                    marks={i: str(i) for i in range(
                        0, int(merged_data['review_count'].max()) + 1,
                        max(1, int(merged_data['review_count'].max() / 10))
                    )}
                ),
            ], style={'width': '80%', 'margin': 'auto'})
        ])


# --- Callback da aba 3 ---
@app.callback(
    Output('airbnb-map', 'figure'),
    Input('review-slider', 'value')
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
        map_style="carto-positron",
    )

    fig.update_layout(
        mapbox_bounds={
            "west": filtered_data['longitude'].min() - 0.05,
            "east": filtered_data['longitude'].max() + 0.05,
            "south": filtered_data['latitude'].min() - 0.05,
            "north": filtered_data['latitude'].max() + 0.05
        },
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True)
