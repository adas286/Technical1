#!/usr/bin/env python3
"""
baseline_subset_analysis.py
 
Answers Bob's Part 4 questions about melanoma patients treated with
miraclib, restricted to PBMC baseline samples (time_from_treatment_start = 0):
 
1. How many samples came from each project?
2. How many subjects were responders vs. non-responders?
3. How many subjects were male vs. female?
 
Usage:
    baseline_subset_analysis.py
"""
 
import os
import sqlite3
import pandas as pd
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cell_counts.db")
 
# The baseline cohort: melanoma, miraclib, PBMC, time_from_treatment_start = 0.
# One row per sample; a subject could in principle contribute more than one
# baseline sample, so subject-level counts below always de-duplicate by
# subject_id rather than by sample.
BASELINE_QUERY = """
SELECT
    s.sample_id,
    s.name AS sample,
    p.name AS project,
    sub.subject_id,
    sub.name AS subject,
    sub.response,
    sub.sex
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
JOIN projects p ON sub.project_id = p.project_id
WHERE sub.condition = 'melanoma'
  AND sub.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND s.time_from_treatment_start = 0;
"""
 
 
def get_baseline_cohort(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(BASELINE_QUERY, conn)
    finally:
        conn.close()
    return df
 
 
def main():
    df = get_baseline_cohort()
 
    print(f"Baseline cohort: {len(df)} samples from "
          f"{df['subject_id'].nunique()} subjects\n")
 
    print("1) Samples per project:")
    samples_per_project = df.groupby("project")["sample_id"].count()
    print(samples_per_project.to_string(), "\n")
 
    # De-duplicate to one row per subject for subject-level breakdowns,
    # since a subject with >1 baseline sample should only be counted once.
    subjects = df.drop_duplicates(subset="subject_id")
 
    print("2) Subjects by response status:")
    print(subjects["response"].value_counts().to_string(), "\n")
 
    print("3) Subjects by sex:")
    print(subjects["sex"].value_counts().to_string())
 
 
if __name__ == "__main__":
    main()