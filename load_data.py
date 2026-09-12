#!/usr/bin/env python3
"""
load_data.py created by Aarushi Das (9/12/2026)
 
Initializes a SQLite database (cell_counts.db) with a normalized schema and
loads all rows from cell-count.csv into it.
 
Usage:
    python load_data.py
 
Expects cell-count.csv to sit next to this script (repository root).
Creates / overwrites cell_counts.db in the same directory.
"""
 
import csv
import os
import sqlite3
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "cell-count.csv")
DB_PATH = os.path.join(SCRIPT_DIR, "cell_counts.db")
 
# The five cell-population columns in the source CSV. Treated as data
# (rows in cell_populations / cell_counts), not as schema, so adding a new
# population later doesn't require a schema change.
POPULATION_COLUMNS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
 
SCHEMA = """
PRAGMA foreign_keys = ON;
 
CREATE TABLE projects (
    project_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE
);
 
CREATE TABLE subjects (
    subject_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    project_id  INTEGER NOT NULL REFERENCES projects(project_id),
    condition   TEXT NOT NULL,
    age         INTEGER,
    sex         TEXT,
    treatment   TEXT NOT NULL,
    response    TEXT
);
 
CREATE TABLE samples (
    sample_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                       TEXT NOT NULL UNIQUE,
    subject_id                 INTEGER NOT NULL REFERENCES subjects(subject_id),
    sample_type                TEXT NOT NULL,
    time_from_treatment_start  INTEGER
);
 
CREATE TABLE cell_populations (
    population_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL UNIQUE
);
 
CREATE TABLE cell_counts (
    sample_id      INTEGER NOT NULL REFERENCES samples(sample_id),
    population_id  INTEGER NOT NULL REFERENCES cell_populations(population_id),
    count          INTEGER NOT NULL,
    PRIMARY KEY (sample_id, population_id)
);
 
CREATE INDEX idx_subjects_project ON subjects(project_id);
CREATE INDEX idx_samples_subject ON samples(subject_id);
CREATE INDEX idx_cell_counts_population ON cell_counts(population_id);
"""
 
 
def init_db(conn):
    """Create a fresh schema, dropping any existing tables first so the
    script can be re-run safely."""
    conn.executescript(
        """
        DROP TABLE IF EXISTS cell_counts;
        DROP TABLE IF EXISTS cell_populations;
        DROP TABLE IF EXISTS samples;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS projects;
        """
    )
    conn.executescript(SCHEMA)
 
    # Seed the cell_populations lookup table up front from the known
    # column names, so cell_counts can reference population_id immediately.
    conn.executemany(
        "INSERT INTO cell_populations (name) VALUES (?)",
        [(name,) for name in POPULATION_COLUMNS],
    )
    conn.commit()
 
 
def load_csv(conn, csv_path):
    project_ids = {}     # name -> project_id
    subject_ids = {}     # name -> subject_id
    population_ids = {}  # name -> population_id
 
    cur = conn.cursor()
    cur.execute("SELECT population_id, name FROM cell_populations")
    for pop_id, name in cur.fetchall():
        population_ids[name] = pop_id
 
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # --- project (get or create) ---
            project_name = row["project"]
            project_id = project_ids.get(project_name)
            if project_id is None:
                cur.execute(
                    "INSERT OR IGNORE INTO projects (name) VALUES (?)",
                    (project_name,),
                )
                cur.execute(
                    "SELECT project_id FROM projects WHERE name = ?",
                    (project_name,),
                )
                project_id = cur.fetchone()[0]
                project_ids[project_name] = project_id
 
            # --- subject (get or create) ---
            subject_name = row["subject"]
            subject_id = subject_ids.get(subject_name)
            if subject_id is None:
                response = row["response"] if row["response"] != "" else None
                cur.execute(
                    """INSERT INTO subjects
                       (name, project_id, condition, age, sex, treatment, response)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        subject_name,
                        project_id,
                        row["condition"],
                        int(row["age"]) if row["age"] != "" else None,
                        row["sex"],
                        row["treatment"],
                        response,
                    ),
                )
                subject_id = cur.lastrowid
                subject_ids[subject_name] = subject_id
 
            # --- sample (one row in the CSV = one sample = one insert) ---
            cur.execute(
                """INSERT INTO samples
                   (name, subject_id, sample_type, time_from_treatment_start)
                   VALUES (?, ?, ?, ?)""",
                (
                    row["sample"],
                    subject_id,
                    row["sample_type"],
                    int(row["time_from_treatment_start"])
                    if row["time_from_treatment_start"] != ""
                    else None,
                ),
            )
            sample_id = cur.lastrowid
 
            # --- cell counts (5 rows per sample, long format) ---
            cur.executemany(
                "INSERT INTO cell_counts (sample_id, population_id, count) VALUES (?, ?, ?)",
                [
                    (sample_id, population_ids[pop_col], int(row[pop_col]))
                    for pop_col in POPULATION_COLUMNS
                ],
            )
 
    conn.commit()
 
 
def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
 
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        load_csv(conn, CSV_PATH)
 
        # Quick sanity check printed to stdout
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM samples")
        n_samples = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM subjects")
        n_subjects = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM cell_counts")
        n_counts = cur.fetchone()[0]
        print(f"Loaded {n_samples} samples, {n_subjects} subjects, "
              f"{n_counts} cell count records into {DB_PATH}")
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    main()