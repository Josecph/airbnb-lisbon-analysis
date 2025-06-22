import pandas as pd
import geopandas as gpd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

COLORS = {
    'background': '#fdf6e3',
    'text': '#657b83',
    'primary': '#b58900',
    'secondary': '#268bd2'
}


app = Dash(__name__, external_stylesheets=[
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
    "https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap",
    "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap",
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
pastel_colors = ['#f6c5af', '#b5d4e5', '#f2e1c2', '#c1d9ce', '#e5c7d3']

language_color_map = {
    'en': '#f6c5af',
    'pt': '#b5d4e5',
    'fr': '#f2e1c2',
    'de': '#c1d9ce',
    'es': '#e5c7d3'
}

color_discrete_map = language_color_map


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
fig_bar = px.bar(
    quarterly_reviews,
    x='quarter',
    y='num_reviews',
    color_discrete_sequence=['#f6c5af']  
)

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
    color_continuous_scale=['#f6c5af', '#b5d4e5', '#f2e1c2', '#c1d9ce', '#e5c7d3'],
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
    title=None
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
                style={
                    'color': COLORS['text'],
                    'font-family': 'Roboto',
                    'font-weight': '500'
                }),
        html.Div(style={
            'borderTop': f'2px solid {COLORS["primary"]}',
            'borderBottom': f'2px solid {COLORS["primary"]}'
        }, 
        children=[
            dcc.Tabs(
                id="tabs",
                value='tab1',
                style={
                    'fontFamily': 'Roboto',
                    'backgroundColor': COLORS['background'],
                    'fontSize': '16px',
                    'color': COLORS['text']
                },
                className="mb-4",
                children=[
                    dcc.Tab(
                        label='Occupancy by Nationality & Parish',
                        value='tab1',
                        style={
                            'fontFamily': 'Roboto',
                            'backgroundColor': COLORS['background'],
                            'color': COLORS['text'],
                            'padding': '12px',
                            'fontWeight': '400',
                            'border': 'none'
                        },
                        selected_style={
                            'fontFamily': 'Roboto',
                            'color': COLORS['secondary'],
                            'borderBottom': f'4px solid {COLORS["primary"]}',
                            'backgroundColor': '#fffdf5',
                            'fontWeight': '600'
                        }
                    ),
                    dcc.Tab(
                        label='Price Distribution Map',
                        value='tab2',
                        style={
                            'fontFamily': 'Roboto',
                            'backgroundColor': COLORS['background'],
                            'color': COLORS['text'],
                            'padding': '12px',
                            'fontWeight': '400',
                            'border': 'none'
                        },
                        selected_style={
                            'fontFamily': 'Roboto',
                            'color': COLORS['secondary'],
                            'borderBottom': f'4px solid {COLORS["primary"]}',
                            'backgroundColor': '#fffdf5',
                            'fontWeight': '600'
                        }
                    ),
                    dcc.Tab(
                        label='Price vs Reviews Map',
                        value='tab3',
                        style={
                            'fontFamily': 'Roboto',
                            'backgroundColor': COLORS['background'],
                            'color': COLORS['text'],
                            'padding': '12px',
                            'fontWeight': '400',
                            'border': 'none'
                        },
                        selected_style={
                            'fontFamily': 'Roboto',
                            'color': COLORS['secondary'],
                            'borderBottom': f'4px solid {COLORS["primary"]}',
                            'backgroundColor': '#fffdf5',
                            'fontWeight': '600'
                        }
                    )
                ]
            )
        ])
    ], className="container"),
    html.Div(
        id='tabs-content',
        className="container",
        style={
            'background': COLORS['background'],
            'padding': '20px',
            'border-radius': '8px',
            'box-shadow': '0 2px 4px rgba(0,0,0,0.1)'
        }
    )
], style={
    'backgroundColor': '#f9f6f2',  
    'minHeight': '100vh'           
})



# --- Callback para renderizar abas ---
@app.callback(
    Output('tabs-content', 'children'),
    Input('tabs', 'value')
)
def render_tab(tab):
    title_style = {
        'font-family': 'Poppins',
        'font-weight': '600',
        'font-size': '20px',
        'color': COLORS['text'],
        'margin-bottom': '15px'
    }

    if tab == 'tab1':
        return html.Div([
            html.P("By nationality and parish (Region of Lisbon)", style=title_style),
            dcc.Graph(figure=fig_map, style={'height': '60vh'}),
            dcc.Graph(figure=fig_bar, style={'height': '35vh'})
        ])
    elif tab == 'tab2':
        return html.Div([
            html.P("Airbnb Price Distribution", style=title_style),
            dcc.Graph(figure=fig_price)
        ])
    elif tab == 'tab3':
        return html.Div([
            html.P("Airbnb Listings (Filtered by Review Count)", style=title_style),
            dcc.Graph(id='airbnb-map'),
            html.Div([
                html.Label("Review Count Threshold:",
                           style={
                               'font-family': 'Poppins',
                               'font-weight': '500',
                               'font-size': '16px',
                               'color': COLORS['text']
                           }),
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
        color_continuous_scale=['#f6c5af', '#b5d4e5', '#f2e1c2', '#c1d9ce', '#e5c7d3'],
        zoom=11,
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