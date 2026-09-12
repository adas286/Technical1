#!/usr/bin/env python3
"""
responder_analysis.py
 
Answers Bob's question: among melanoma patients treated with miraclib
(PBMC samples only), which immune cell populations differ in relative
frequency between responders and non-responders?
 
Usage:
    python responder_analysis.py
 
Outputs:
    - responder_boxplots.png   : one boxplot per cell population
    - responder_stats.csv      : Mann-Whitney U test results per population
    - prints a plain-English summary of significant populations to stdout
"""
 
import os
import sqlite3
 
import matplotlib
matplotlib.use("Agg")  # no display needed; just save to file
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
 
from frequency_summary import compute_frequency_summary
 
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "cell_counts.db")
BOXPLOT_PATH = os.path.join(SCRIPT_DIR, "responder_boxplots.png")
STATS_CSV = os.path.join(SCRIPT_DIR, "responder_stats.csv")
 
ALPHA = 0.05
 
# Melanoma, miraclib, PBMC samples with a valid response
COHORT_QUERY = """
SELECT s.sample_id, s.name AS sample, sub.response
FROM samples s
JOIN subjects sub ON s.subject_id = sub.subject_id
WHERE sub.condition = 'melanoma'
  AND sub.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND sub.response IS NOT NULL;
"""
 
 
def build_cohort(db_path=DB_PATH):
    """Melanoma + miraclib + PBMC samples, joined to per-sample population
    percentages, labeled by responder status."""
    conn = sqlite3.connect(db_path)
    try:
        cohort = pd.read_sql_query(COHORT_QUERY, conn)
    finally:
        conn.close()
 
    freq = compute_frequency_summary(db_path)
    merged = cohort.merge(freq, on="sample", how="inner")
    return merged[["sample", "response", "population", "count",
                    "total_count", "percentage"]]
 
 
def make_boxplots(df, out_path=BOXPLOT_PATH):
    populations = sorted(df["population"].unique())
    fig, axes = plt.subplots(1, len(populations), figsize=(4 * len(populations), 5),
                              sharey=False)
    if len(populations) == 1:
        axes = [axes]
 
    for ax, pop in zip(axes, populations):
        sub = df[df["population"] == pop]
        data = [
            sub.loc[sub["response"] == "no", "percentage"],
            sub.loc[sub["response"] == "yes", "percentage"],
        ]
        ax.boxplot(data, tick_labels=["non-responder", "responder"])
        ax.set_title(pop)
        ax.set_ylabel("% of total cells")
 
    fig.suptitle("Relative frequency by response status\n"
                  "(melanoma, miraclib, PBMC samples)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
 
 
def run_tests(df):
    """Mann-Whitney U test per population (non-parametric: cell-frequency
    percentages are bounded and not assumed normal), with Benjamini-Hochberg
    correction for testing 5 populations at once."""
    results = []
    for pop in sorted(df["population"].unique()):
        sub = df[df["population"] == pop]
        responders = sub.loc[sub["response"] == "yes", "percentage"]
        non_responders = sub.loc[sub["response"] == "no", "percentage"]
 
        u_stat, p_value = stats.mannwhitneyu(
            responders, non_responders, alternative="two-sided"
        )
        results.append({
            "population": pop,
            "n_responders": len(responders),
            "n_non_responders": len(non_responders),
            "median_responder_pct": responders.median(),
            "median_non_responder_pct": non_responders.median(),
            "u_statistic": u_stat,
            "p_value": p_value,
        })
 
    results_df = pd.DataFrame(results)
 
    # Benjamini-Hochberg FDR correction across the 5 population-level tests.
    # Standard procedure: sort ascending, compute p * m / rank, then take a
    # cumulative minimum from the largest rank down to the smallest so
    # adjusted p-values are monotonically non-decreasing with rank.
    results_df = results_df.sort_values("p_value").reset_index(drop=True)
    m = len(results_df)
    rank = pd.Series(range(1, m + 1), index=results_df.index)
    raw_adjusted = results_df["p_value"] * m / rank
    p_adjusted = raw_adjusted[::-1].cummin()[::-1]
    results_df["p_adjusted"] = p_adjusted.clip(upper=1.0)
    results_df["significant_at_0.05"] = results_df["p_adjusted"] < ALPHA
 
    return results_df
 
 
def main():
    df = build_cohort()
    make_boxplots(df)
    results_df = run_tests(df)
    results_df.to_csv(STATS_CSV, index=False)
 
    print(f"Boxplots saved to {BOXPLOT_PATH}")
    print(f"Full stats table saved to {STATS_CSV}\n")
    print(results_df.to_string(index=False))
 
    sig = results_df[results_df["significant_at_0.05"]]
    print("\n--- Summary ---")
    if sig.empty:
        print("No cell population showed a statistically significant "
              f"difference (BH-adjusted p < {ALPHA}) between responders "
              "and non-responders in this cohort.")
    else:
        for _, row in sig.iterrows():
            direction = ("higher" if row["median_responder_pct"] >
                         row["median_non_responder_pct"] else "lower")
            print(f"- {row['population']}: significantly {direction} in "
                  f"responders (median {row['median_responder_pct']:.2f}% "
                  f"vs {row['median_non_responder_pct']:.2f}%; "
                  f"BH-adjusted p = {row['p_adjusted']:.4g})")
 
 
if __name__ == "__main__":
    main()