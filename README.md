# Cell Count Analysis

Loads `cell-count.csv` into a normalized SQLite database and answers Bob's
questions about immune cell population frequencies, with an interactive
dashboard presenting the results.

## Project structure

```
cell-count.csv                  # source data
load_data.py                    # Part 1: builds cell_counts.db from the CSV
frequency_summary.py            # Part 2: relative frequency per sample/population
responder_analysis.py           # Part 3: responder vs. non-responder stats + boxplots
baseline_subset_analysis.py     # Part 4: baseline (day 0) subset breakdowns
avg_bcell_male_responders.py    # ad-hoc query (average B cell count, male responders)
dashboard.py                    # Streamlit dashboard presenting Parts 2-4
requirements.txt                # Python dependencies
Makefile                        # setup / pipeline / dashboard targets
```

Running the pipeline produces (all git-ignored, regenerated each run):
`cell_counts.db`, `frequency_summary.csv`, `responder_stats.csv`,
`responder_boxplots.png`.

## Running in GitHub Codespaces

Open this repository in a Codespace, then from the integrated terminal
(repository root):

```bash
make setup      # creates .venv and installs dependencies from requirements.txt
make pipeline   # builds cell_counts.db and runs the Part 2-4 analyses
make dashboard  # starts the interactive dashboard on port 8501
```

`make dashboard` runs Streamlit bound to `0.0.0.0:8501`. Codespaces will
detect the open port and show a "Open in Browser" notification / a **Ports**
tab entry — use that forwarded URL to view the dashboard. Leave the command
running in the terminal; press `Ctrl+C` to stop it.

These same three commands also work in a local clone (macOS/Linux/WSL) with
Python 3 installed; on Windows, use a shell where `python3`/`make` are
available (e.g. WSL, or run the underlying commands in the Makefile manually
via `python` instead of `python3` if needed).

## What each pipeline stage does

1. **`load_data.py`** — creates a normalized schema (`projects`, `subjects`,
   `samples`, `cell_populations`, `cell_counts`) and loads every row of
   `cell-count.csv` into it.
2. **`frequency_summary.py`** — for every sample, computes each population's
   count as a percentage of that sample's total cell count. Writes
   `frequency_summary.csv`.
3. **`responder_analysis.py`** — restricts to melanoma / miraclib / PBMC
   samples, compares relative frequencies between responders and
   non-responders per population using a Mann-Whitney U test with
   Benjamini-Hochberg correction (5 populations tested), and saves
   `responder_boxplots.png` + `responder_stats.csv`.
4. **`baseline_subset_analysis.py`** — restricts to melanoma / miraclib /
   PBMC samples at `time_from_treatment_start = 0` and reports sample counts
   per project, and subject counts by response and by sex.

## Dashboard

**Dashboard link:** 

The dashboard (`dashboard.py`) reads directly from `cell_counts.db` and
presents:
- **Part 2** — the full per-sample/per-population frequency table, with a
  per-sample breakdown chart and CSV download.
- **Part 3** — interactive boxplots of relative frequency by response
  status, plus the full statistical test results table.
- **Part 4** — sample/subject counts for the baseline cohort, broken down
  by project, response, and sex.

It must be run after `make pipeline`, since it reads the database that step
creates.
