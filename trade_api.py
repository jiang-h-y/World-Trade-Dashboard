"""
file: trade_api.py
author: Heidi Jiang
description: An API that facilitates data retrieval/visualization given
an SQLite database.
"""

import sqlite3
import pandas as pd
import plotly.express as px

class TradeAPI:

    # instance methods
    def __init__(self, db_path):
        """ Constructor that takes in a database path

        Source referenced:
        https://docs.python.org/3/library/sqlite3.html
        """
        self.con = sqlite3.connect(db_path)
        self.cursor = self.con.cursor()
        self.years = self.load_years()
        self.countries = self.load_countries()

    def load_years(self):
        """ Gets all distinct years and returns them as a list

        Source referenced:
        https://docs.python.org/3/library/sqlite3.html
        """
        query = """
                SELECT DISTINCT year FROM Ports
                """
        self.cursor.execute(query)
        # returns the results as a list of years
        return [item[0] for item in self.cursor.fetchall()]

    def load_countries(self):
        """ Gets all distinct country names and returns them as a list """
        query = """
                SELECT DISTINCT country FROM Ports
                """
        self.cursor.execute(query)
        return [item[0] for item in self.cursor.fetchall()]

    def total_ships(self, year):
        """
        Parameters: an int
        Returns: an int
        Does: sums the number of ship arrivals in a given year

        Source referenced:
        https://stackoverflow.com/questions/22776756/parameterized-queries-
        in-sqlite3-using-question-marks
        """
        query = """
                SELECT SUM(portcalls)
                FROM Ports
                WHERE year = ?
                """
        self.cursor.execute(query, (year,))
        # pulls out the value from a list of a tuple
        return self.cursor.fetchall()[0][0]

    def ie_dist(self, year):
        """
        Parameters: an int
        Returns: a tuple (import_pct, export_pct), where both values are floats
        Does: finds the percent of imports and exports that made up
        total trade in a given year
        """
        query = """
                SELECT SUM(import), SUM(export)
                FROM Ports
                WHERE year = ?
                """
        self.cursor.execute(query, (year,))
        imports, exports = self.cursor.fetchall()[0]
        total = imports + exports
        import_pct = (imports / total) * 100
        export_pct = (exports / total) * 100
        return round(import_pct, 1), round(export_pct, 1)

    def get_world_data(self, year):
        """
        Parameters: an int
        Returns: a DataFrame
        Does: returns a DataFrame of world trade data for a given year

        # Source referenced:
        https://pandas.pydata.org/docs/reference/api/pandas.read_sql_query.html
        """
        query = """
                SELECT ISO3,
                SUM(import) AS Imports, 
                SUM(export) AS Exports
                FROM Ports
                WHERE year = ?
                GROUP BY ISO3
                """
        df = pd.read_sql_query(query, self.con, params=[year])
        df = TradeAPI.scale_ie(df)
        df["Trade"] = df["Imports"] + df["Exports"]
        return df

    def get_country_data(self, country):
        """
        Parameters: a string
        Returns: a DataFrame
        Does: aggregates trade data by month for a given country and returns
        the results as a DataFrame

        Source referenced:
        https://stackoverflow.com/questions/68310077/converting-separate-series
        -for-year-month-day-to-a-single-datetime-series
        """
        query = """
                SELECT SUM(import) AS Imports, 
                SUM(export) AS Exports, 
                year, month
                FROM Ports
                WHERE country = ?
                GROUP BY year, month
                """
        df = pd.read_sql_query(query, self.con, params=[country])
        df = self.scale_ie(df)

        # assigns the day to be the first of the month so that date data can be
        # converted to datetime while still grouping by month
        df["day"] = 1
        df["Date"] = pd.to_datetime(df[["year", "month", "day"]])
        return df

    # static methods
    @staticmethod
    def scale_ie(df, scale=1000000):
        """
        Parameters:
            df: a DataFrame
            scale: an optional int/float scaling value
        Returns: a DataFrame
        Does: scales imports and exports columns in a DataFrame
        """
        df = df.copy()
        df["Imports"] = df["Imports"] / scale
        df["Exports"] = df["Exports"] / scale
        return df

    @staticmethod
    def top_share(df):
        """
        Parameters: a DataFrame
        Returns: a float
        Does: calculates the #1 country's % share of total global trade based on
        a DataFrame
        """
        max_trade = df["Trade"].max()
        sum_trade = df["Trade"].sum()
        pct = (max_trade / sum_trade) * 100
        return round(pct, 1)

    @staticmethod
    def make_choropleth(df, year, w, h, vmax=7000):
        """
        Parameters:
            df: a DataFrame
            year: an int
            w: width (an int)
            h: height (an int)
            vmax: an optional int
        Returns: a Plotly Express figure
        Does: generates a Plotly Express choropleth

        Sources referenced:
        https://plotly.github.io/plotly.py-docs/generated/plotly.express.
        choropleth.html
        https://plotly.com/python/choropleth-maps/
        """
        fig = px.choropleth(
            df, locations="ISO3", color="Trade",
            color_continuous_scale="Viridis_r", range_color=(0, vmax),
            title=f"Trade Volume Around the World in {year}",
            labels={"Trade": "Millions of Metric Tons"}
        )
        fig.update_layout(width=w, height=h, autosize=False)
        return fig

    @staticmethod
    def make_lineplot(df, country, w, h):
        """
        Parameters:
            df: a DataFrame
            country: a string
            w: width (an int)
            h: height (an int)
        Returns: a Plotly Express figure
        Does: generates a Plotly Express line chart

        Sources referenced:
        https://plotly.com/python-api-reference/generated/plotly.express.line
        https://plotly.com/python/line-charts/
        """
        fig = px.line(
            df, x="Date", y=["Imports", "Exports"],
            labels={"value": "Trade Volume (in millions of metric tons)",
                    "variable": "Category"},
            title=f"{country} Trade Volume"
        )
        fig.update_layout(width=w, height=h, autosize=False)
        return fig