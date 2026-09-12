VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: setup pipeline dashboard clean

# Installs all dependencies into a project-local virtual environment,
# so this works the same way regardless of how the base Python is managed.
setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Runs the full data pipeline start to finish, with no manual steps:
#   1. build the SQLite database from cell-count.csv
#   2. compute the Part 2 relative-frequency summary table
#   3. run the Part 3 responder-vs-non-responder statistical analysis
#   4. compute the Part 4 baseline subset breakdowns
pipeline:
	$(PYTHON) load_data.py
	$(PYTHON) frequency_summary.py
	$(PYTHON) responder_analysis.py
	$(PYTHON) baseline_subset_analysis.py

# Starts the interactive dashboard (Part 2-4 results), reading live from
# the database the pipeline created. Binds to 0.0.0.0 so GitHub Codespaces
# can forward the port.
dashboard:
	$(PYTHON) -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

clean:
	rm -rf $(VENV) cell_counts.db frequency_summary.csv responder_stats.csv responder_boxplots.png
