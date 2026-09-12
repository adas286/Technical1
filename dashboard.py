#!/usr/bin/env python3
"""
dashboard.py
 
Interactive dashboard presenting the Part 2-4 results, read live from the
SQLite database that the pipeline (load_data.py + friends) builds.
 
Run with:
    streamlit run dashboard.py
 
(the Makefile's `make dashboard` target does this for you).
"""
 
import os
 
import pandas as pd
import plotly.express as px
import streamlit as st
 
from frequency_summary import compute_frequency_summary, DB_PATH
from responder_analysis import build_cohort, run_tests
from baseline_subset_analysis import get_baseline_cohort
 
st.set_page_config(page_title="Cell Count Dashboard", layout="wide")
 
st.title("Cell Count Analysis Dashboard")
 
if not os.path.exists(DB_PATH):
    st.error(
        f"Database not found at `{DB_PATH}`. Run `make pipeline` first "
        "to build it from cell-count.csv."
    )
    st.stop()
 
tab2, tab3, tab4 = st.tabs([
    "Part 2 — Frequency Summary",
    "Part 3 — Responder Analysis",
    "Part 4 — Baseline Subset",
])
 
# ---------------------------------------------------------------------------
# Part 2: relative frequency of each cell population, per sample
# ---------------------------------------------------------------------------
with tab2:
    st.header("Relative frequency of each cell population per sample")
 
    freq_df = compute_frequency_summary()
 
    samples = sorted(freq_df["sample"].unique())
    selected_sample = st.selectbox(
        "Filter to a single sample (optional)", ["All samples"] + samples
    )
 
    if selected_sample != "All samples":
        display_df = freq_df[freq_df["sample"] == selected_sample]
        one_sample = display_df
        fig = px.bar(
            one_sample, x="population", y="percentage",
            title=f"Population breakdown for {selected_sample}",
            text="percentage",
        )
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)
    else:
        display_df = freq_df
 
    st.dataframe(display_df, use_container_width=True, height=400)
    st.caption(f"{len(freq_df)} rows total "
               f"({freq_df['sample'].nunique()} samples x 5 populations)")
 
    csv_bytes = freq_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download full frequency_summary.csv",
        data=csv_bytes,
        file_name="frequency_summary.csv",
        mime="text/csv",
    )
 
# ---------------------------------------------------------------------------
# Part 3: responders vs non-responders (melanoma, miraclib, PBMC)
# ---------------------------------------------------------------------------
with tab3:
    st.header("Responders vs. non-responders")
    st.caption("Melanoma patients treated with miraclib, PBMC samples only.")
 
    cohort_df = build_cohort()
 
    if cohort_df.empty:
        st.warning("No samples matched the melanoma / miraclib / PBMC filter.")
    else:
        fig = px.box(
            cohort_df, x="response", y="percentage", color="response",
            facet_col="population", facet_col_wrap=5,
            category_orders={"response": ["no", "yes"]},
            labels={"percentage": "% of total cells", "response": "Response"},
            points="outliers",
        )
        fig.update_yaxes(matches=None)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig, use_container_width=True)
 
        st.subheader("Mann-Whitney U test per population (BH-corrected)")
        stats_df = run_tests(cohort_df)
        st.dataframe(stats_df, use_container_width=True)
 
        sig = stats_df[stats_df["significant_at_0.05"]]
        if sig.empty:
            st.info(
                "No cell population shows a statistically significant "
                "difference (BH-adjusted p < 0.05) between responders and "
                "non-responders in this cohort."
            )
        else:
            for _, row in sig.iterrows():
                direction = ("higher" if row["median_responder_pct"] >
                             row["median_non_responder_pct"] else "lower")
                st.success(
                    f"**{row['population']}**: significantly {direction} in "
                    f"responders (median {row['median_responder_pct']:.2f}% "
                    f"vs {row['median_non_responder_pct']:.2f}%; "
                    f"BH-adjusted p = {row['p_adjusted']:.4g})"
                )
 
# ---------------------------------------------------------------------------
# Part 4: baseline subset (melanoma, miraclib, PBMC, time = 0)
# ---------------------------------------------------------------------------
with tab4:
    st.header("Baseline subset (day 0)")
    st.caption("Melanoma, miraclib, PBMC samples at time_from_treatment_start = 0.")
 
    baseline_df = get_baseline_cohort()
 
    if baseline_df.empty:
        st.warning("No samples matched the baseline filter.")
    else:
        st.metric("Total baseline samples", len(baseline_df))
        st.metric("Unique subjects", baseline_df["subject_id"].nunique())
 
        subjects_df = baseline_df.drop_duplicates(subset="subject_id")
 
        col1, col2, col3 = st.columns(3)
 
        with col1:
            st.subheader("Samples per project")
            proj_counts = (
                baseline_df.groupby("project")["sample_id"]
                .count().reset_index(name="n_samples")
            )
            st.dataframe(proj_counts, use_container_width=True)
            st.plotly_chart(
                px.bar(proj_counts, x="project", y="n_samples"),
                use_container_width=True,
            )
 
        with col2:
            st.subheader("Subjects by response")
            resp_counts = (
                subjects_df["response"].value_counts()
                .reset_index()
            )
            resp_counts.columns = ["response", "n_subjects"]
            st.dataframe(resp_counts, use_container_width=True)
            st.plotly_chart(
                px.bar(resp_counts, x="response", y="n_subjects"),
                use_container_width=True,
            )
 
        with col3:
            st.subheader("Subjects by sex")
            sex_counts = (
                subjects_df["sex"].value_counts()
                .reset_index()
            )
            sex_counts.columns = ["sex", "n_subjects"]
            st.dataframe(sex_counts, use_container_width=True)
            st.plotly_chart(
                px.bar(sex_counts, x="sex", y="n_subjects"),
                use_container_width=True,
            )
 

