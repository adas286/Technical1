#!/usr/bin/env python3
"""
frequency_summary.py
 
Answers Bob's question: "What is the frequency of each cell type in each
sample?"
 
Queries cell_counts.db and prints/saves a long-format summary table with one
row per (sample, population):
 
    sample, total_count, population, count, percentage
 
Usage:
    python frequency_summary.py
 
Writes frequency_summary.csv to the repository root and prints a preview.
"""
 
import os
import sqlite3
import pandas as pd
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cell_counts.db")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "frequency_summary.csv")
 
QUERY = """
SELECT
    s.name AS sample,
    totals.total_count AS total_count,
    cp.name AS population,
    cc.count AS count,
    ROUND(100.0 * cc.count / totals.total_count, 4) AS percentage
FROM cell_counts cc
JOIN samples s ON cc.sample_id = s.sample_id
JOIN cell_populations cp ON cc.population_id = cp.population_id
JOIN (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
) AS totals ON totals.sample_id = cc.sample_id
ORDER BY s.name, cp.name;
"""
 
 
def compute_frequency_summary(db_path=DB_PATH):
    """Return the frequency summary as a pandas DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(QUERY, conn)
    finally:
        conn.close()
    return df
 
 
def main():
    df = compute_frequency_summary()
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT_CSV}")
    print(df.head(10).to_string(index=False))
 
 
if __name__ == "__main__":
    main()
 
