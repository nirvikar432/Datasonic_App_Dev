import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import fetch_data

def charts_tab():
    st.header("Charts & Analytics")

    # Fetch data for charts
    policy_df = pd.DataFrame(fetch_data("SELECT TOP 20 * FROM Policy"))
    claims_df = pd.DataFrame(fetch_data("SELECT TOP 20 * FROM Claims"))

    # Active Policy Count
    active_policy_count = policy_df[policy_df["isCancelled"] == 0].shape[0] if not policy_df.empty else 0
    st.metric("Active Policies", active_policy_count)

    # Cross-filter UI
    st.subheader("Cross Filter")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        policy_filter = st.multiselect(
            "Filter by Policy Number",
            options=policy_df["POLICY_NO"].unique() if not policy_df.empty else [],
            key="chart_policy_filter"
        )
    with filter_col2:
        claim_filter = st.multiselect(
            "Filter by Claim Number",
            options=claims_df["CLAIM_NO"].unique() if not claims_df.empty else [],
            key="chart_claim_filter"
        )

    # Apply filters
    filtered_policy_df = policy_df
    filtered_claims_df = claims_df

    if policy_filter:
        filtered_policy_df = filtered_policy_df[filtered_policy_df["POLICY_NO"].isin(policy_filter)]
        filtered_claims_df = filtered_claims_df[filtered_claims_df["POLICY_NO"].isin(policy_filter)]
    if claim_filter:
        filtered_claims_df = filtered_claims_df[filtered_claims_df["CLAIM_NO"].isin(claim_filter)]
        filtered_policy_df = filtered_policy_df[filtered_policy_df["POLICY_NO"].isin(filtered_claims_df["POLICY_NO"].unique())]

    # Show filtered counts
    st.write(f"Filtered Active Policies: {filtered_policy_df[filtered_policy_df['isCancelled'] == 0].shape[0] if not filtered_policy_df.empty else 0}")
    st.write(f"Filtered Claims: {filtered_claims_df.shape[0] if not filtered_claims_df.empty else 0}")

    # chart: Active policies by product[testing]
    if not filtered_policy_df.empty and "PRODUCT" in filtered_policy_df.columns:
        fig = px.bar(
            filtered_policy_df[filtered_policy_df["isCancelled"] == 0].groupby("PRODUCT").size().reset_index(name="Active Policies"),
            x="PRODUCT",
            y="Active Policies",
            title="Active Policies by Product"
        )
        st.plotly_chart(fig, use_container_width=True)

    # chart: Claims by Policy [testing]
    if not filtered_claims_df.empty:
        fig2 = px.histogram(
            filtered_claims_df,
            x="POLICY_NO",
            title="Claims Count by Policy"
        )
        st.plotly_chart(fig2, use_container_width=True)