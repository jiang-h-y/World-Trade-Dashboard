"""
file: trade_panel.py
author: Heidi Jiang
description: A program that generates a world trade dashboard using
port activity data from the International Monetary Fund (IMF).

Data source:
https://portwatch.imf.org/datasets/959214444157458aad969389b3ebe1a0/about
"""

from trade_api import TradeAPI
import panel as pn
pn.extension()

DB_PATH = "db/port_activity.db"

# API
tapi = TradeAPI(DB_PATH)

# ----- SHARED WIDGETS (used in both tabs) -----
# Sources referenced:
# https://panel.holoviz.org/how_to/layout/spacing.html
# https://panel.holoviz.org/reference/panes/Markdown.html
spacer = pn.Spacer(height=15)

note = pn.pane.Markdown("""Note: Recent trade volumes may seem unusually low 
because data is still incomplete for the current period.""")

width = pn.widgets.IntSlider(
    name="Width", start=600, end=1500, step=100, value=900
)

height = pn.widgets.IntSlider(
    name="Height", start=400, end=900, step=100, value=500
)

plot_card = pn.Card(
    pn.Column(width, height),
    title="Adjust Plot Dimensions", width=320,
    header_background="#0078A8", header_color="#FFFFFF"
)

# ----- TAB 1 -----
# MAIN WIDGETS
year_select = pn.widgets.Select(
    options=tapi.years, value=2025
)

year_card = pn.Card(
    year_select, title="Year", width=320,
    header_background="#0078A8", header_color="#FFFFFF"
)

# CALLBACK FUNCTIONS
def get_total_ships(year):
    """ Given a year (int), return the total number of ships (int) """
    return tapi.total_ships(year)

def get_import_pct(year):
    """ Given a year (int), return the percent of imports (float) """
    return tapi.ie_dist(year)[0]

def get_export_pct(year):
    """ Given a year (int), return the percent of exports (float) """
    return tapi.ie_dist(year)[1]

def get_world_df(year):
    """ Given a year int, return world trade data as a DataFrame; isolates data
    to prevent multiple calls of a computationally-intensive SQL query """
    return tapi.get_world_data(year)

def get_top_share(df):
    """ Given a DataFrame, return the #1 country's percent of
    total trade (float) """
    return tapi.top_share(df)

def get_worldmap(df, year, w, h):
    """ Return a choropleth figure given a DataFrame,
    year (int), width (int), and height (int) """
    return tapi.make_choropleth(df, year, w, h)

# CALLBACK BINDINGS
ship_bind = pn.bind(get_total_ships, year_select)
import_bind = pn.bind(get_import_pct, year_select)
export_bind = pn.bind(get_export_pct, year_select)

world_data_bind = pn.bind(get_world_df, year_select)
top_share_bind = pn.bind(get_top_share, world_data_bind)
worldmap = pn.bind(get_worldmap, world_data_bind, year_select, width, height)

# STYLIZATION WIDGETS
# Sources referenced:
# https://panel.holoviz.org/tutorials/basic/indicators_performance.html
# https://panel.holoviz.org/reference/indicators/Number.html
ship_ind = pn.indicators.Number(
    name="Total Ship Arrivals", value=ship_bind, format="{value} ships",
    colors=[(float("inf"), "#F0802B")], title_size="12pt", font_size="30pt"
)

import_ind = pn.indicators.Number(
    name="Imports % of Total Trade", value=import_bind, format="{value}%",
    colors=[(float("inf"), "#F0802B")], title_size="12pt", font_size="30pt"
)
export_ind = pn.indicators.Number(
    name="Exports % of Total Trade", value=export_bind, format="{value}%",
    colors=[(float("inf"), "#F0802B")], title_size="12pt", font_size="30pt"
)

top_share_ind = pn.indicators.Number(
    name="#1 Country's Trade Share",
    value=top_share_bind, format="{value}%",
    colors=[(float("inf"), "#F0802B")], title_size="12pt", font_size="30pt"
)

# TAB 1 LAYOUT
# Sources referenced:
# https://panel.holoviz.org/reference/layouts/Column.html
# https://panel.holoviz.org/reference/layouts/Row.html
tab1 = pn.Column(
    note,
    pn.Row(
        pn.Column(top_share_ind, ship_ind, import_ind, export_ind),
        worldmap,
        pn.Column(year_card, spacer, plot_card)
    )
)

# ----- TAB 2 -----
# WIDGETS
# Source referenced:
# https://panel.holoviz.org/reference/widgets/AutocompleteInput.html
country_select = pn.widgets.AutocompleteInput(
    options=tapi.countries, case_sensitive=False,
    search_strategy="includes", placeholder="Enter a country name...",
    value="United States"
)

search_card = pn.Card(
    country_select,
    title="Search", width=320,
    header_background="#0078A8", header_color="#FFFFFF"
)

# CALLBACK FUNCTION/BINDING
def get_lineplot(country, w, h):
    """ Callback function that returns a line plot figure,
    given a country (string), width (int), and height (int) """
    df = tapi.get_country_data(country)
    fig = tapi.make_lineplot(df, country, w, h)
    return fig

lineplot = pn.bind(get_lineplot, country_select, width, height)

# TAB 2 LAYOUT
tab2 = pn.Column(
    note,
    pn.Row(
        lineplot,
        pn.Column(search_card, spacer, plot_card)
    )
)

# ----- DASHBOARD LAYOUT -----
layout = pn.template.FastListTemplate(
    title="World Trade Dashboard",
    sidebar=[
    ],
    theme_toggle=False,
    main=[
        pn.Tabs(
            ("World Trade Data", tab1),
            ("Trade Volume by Country", tab2)
        ),
    ],
    header_background="#015D82"
).servable()

layout.show()