#!/usr/bin/env python3
"""
question.py
 
Computes the average B cell count for melanoma patients who are:
    - male
    - responders (response = 'yes')
    - at baseline (time_from_treatment_start = 0)
 
Considers ALL sample types (PBMC, WB) and ALL treatments (miraclib,
phauximab, none) -- no filtering beyond condition/sex/response/timepoint.
 
Usage:
    python question.py
"""
 
import os
import sqlite3
import pandas as pd
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cell_counts.db")
 
QUERY = """
SELECT s.name AS sample, cc.count
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
JOIN cell_counts cc ON cc.sample_id = s.sample_id
JOIN cell_populations cp ON cc.population_id = cp.population_id
WHERE sub.condition = 'melanoma'
  AND sub.sex = 'M'
  AND sub.response = 'yes'
  AND s.time_from_treatment_start = 0
  AND cp.name = 'b_cell';
"""
 
 
def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(QUERY, conn)
    finally:
        conn.close()
 
    n = len(df)
    avg = df["count"].mean()
 
    print(f"Matching samples: {n}")
    print(f"Average B cell count: {avg:.2f}")
 
 
if __name__ == "__main__":
    main()
 