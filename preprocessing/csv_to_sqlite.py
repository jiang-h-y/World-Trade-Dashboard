"""
file: csv_to_sqlite.py
author: Heidi Jiang
description: A program to convert a CSV file into a SQLite database.
"""

import pandas as pd
import sqlite3

FILENAME = "../data/port_activity.csv"
DB_PATH = "../db/port_activity.db"
TABLE_NAME = "Ports"

def main():
    df = pd.read_csv(FILENAME)
    con = sqlite3.connect(DB_PATH)
    df.to_sql(TABLE_NAME, con, if_exists="replace")

if __name__ == "__main__":
    main()