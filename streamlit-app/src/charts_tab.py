import streamlit as st
import pandas as pd
import plotly.express as px
from db_utils import fetch_data

def charts_tab():
    st.header("Charts & Analytics")

    # Fetch data for charts
    policy_df = pd.DataFrame(fetch_data("SELECT TOP 1000 * FROM New_Policy"))
    claims_df = pd.DataFrame(fetch_data("SELECT TOP 20 * FROM New_Claims"))

    # Convert date columns to datetime
    if not policy_df.empty and "POL_EFF_DATE" in policy_df.columns:
        policy_df["POL_EFF_DATE"] = pd.to_datetime(policy_df["POL_EFF_DATE"], errors='coerce')

    # Active Policy Count
    active_policy_count = policy_df[policy_df["isCancelled"] == 0].shape[0] if not policy_df.empty else 0
    # active_policy_count = policy_df[(policy_df["isCancelled"] == 0) & (policy_df["isLapsed"] == 0)].shape[0] if not policy_df.empty else 0
    st.metric("Active Policies", active_policy_count)

    # Create two columns for charts and controls
    chart_col1, chart_col2 = st.columns(2)

    if not policy_df.empty and "POL_EFF_DATE" in policy_df.columns:
        # Filter active policies
        active_policies = policy_df[policy_df["isCancelled"] == 0].copy()
        # active_policies = policy_df[(policy_df["isCancelled"] == 0) & (policy_df["isLapsed"] == 0)].copy()
        
        # --- LEFT COLUMN: Bar Chart + Time Granularity Selector ---
        with chart_col1:
            st.subheader("Active Policy Analysis")
            time_granularity = st.selectbox("Select Time Granularity", ["Year", "Month"], key="time_granularity")

            # Group data based on time granularity
            if time_granularity == "Year":
                active_policies["Period"] = active_policies["POL_EFF_DATE"].dt.year
                period_counts = active_policies.groupby("Period").size().reset_index(name="Active Policies")
                period_counts["Period"] = period_counts["Period"].astype(str)
                bar_title = "Active Policies by Year"
                period_col = "Period"
            elif time_granularity == "Month":
                active_policies["Month"] = active_policies["POL_EFF_DATE"].dt.strftime("%b")
                period_counts = active_policies.groupby("Month").size().reindex(
                    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                ).reset_index(name="Active Policies").dropna()
                period_counts["Month"] = pd.Categorical(period_counts["Month"], categories=[
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ], ordered=True)
                period_counts = period_counts.sort_values("Month")
                bar_title = "Active Policies by Month (All Years)"
                period_col = "Month"
            else:
                period_counts = pd.DataFrame()
                period_col = "Period"
                bar_title = ""

            # Bar Chart
            if not period_counts.empty:
                fig_bar = px.bar(
                    period_counts,
                    x=period_col,
                    y="Active Policies",
                    title=bar_title
                )
                fig_bar.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- RIGHT COLUMN: Pie Chart + Period Selector ---
        with chart_col2:
            st.subheader("Select Period for Policy Type Analysis")
            available_periods = period_counts[period_col].astype(str).tolist() if not period_counts.empty else []
            selected_period = st.selectbox(
                f"Select {time_granularity}",
                options=["All"] + available_periods,
                key="period_selector"
            )

            if "POLICYTYPE" in active_policies.columns:
                # Filter data based on selected period
                if selected_period != "All":
                    filtered_for_pie = active_policies[active_policies[period_col].astype(str) == selected_period]
                    pie_title = f"Policy Types Distribution - {selected_period}"
                else:
                    filtered_for_pie = active_policies
                    pie_title = f"Policy Types Distribution - All {time_granularity}s"
                
                if not filtered_for_pie.empty:
                    policy_type_counts = filtered_for_pie["POLICYTYPE"].value_counts().reset_index()
                    policy_type_counts.columns = ["Policy Type", "Count"]
                    
                    fig_pie = px.pie(
                        policy_type_counts,
                        values="Count",
                        names="Policy Type",
                        title=pie_title
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info(f"No policy data available for {selected_period}")
            else:
                st.info("Policy Type data not available for pie chart")

    # # Cross-filter UI
    # st.subheader("Cross Filter")
    # filter_col1, filter_col2 = st.columns(2)
    # with filter_col1:
    #     policy_filter = st.multiselect(
    #         "Filter by Policy Number",
    #         options=policy_df["POLICY_NO"].unique() if not policy_df.empty else [],
    #         key="chart_policy_filter"
    #     )
    # with filter_col2:
    #     claim_filter = st.multiselect(
    #         "Filter by Claim Number",
    #         options=claims_df["CLAIM_NO"].unique() if not claims_df.empty else [],
    #         key="chart_claim_filter"
    #     )

    # # Apply filters
    # filtered_policy_df = policy_df
    # filtered_claims_df = claims_df

    # if policy_filter:
    #     filtered_policy_df = filtered_policy_df[filtered_policy_df["POLICY_NO"].isin(policy_filter)]
    #     filtered_claims_df = filtered_claims_df[filtered_claims_df["POLICY_NO"].isin(policy_filter)]
    # if claim_filter:
    #     filtered_claims_df = filtered_claims_df[filtered_claims_df["CLAIM_NO"].isin(claim_filter)]
    #     filtered_policy_df = filtered_policy_df[filtered_policy_df["POLICY_NO"].isin(filtered_claims_df["POLICY_NO"].unique())]

    # # Show filtered counts
    # st.write(f"Filtered Active Policies: {filtered_policy_df[filtered_policy_df['isCancelled'] == 0].shape[0] if not filtered_policy_df.empty else 0}")
    # st.write(f"Filtered Claims: {filtered_claims_df.shape[0] if not filtered_claims_df.empty else 0}")

    # # Chart: Active policies by product[testing]
    # if not filtered_policy_df.empty and "PRODUCT" in filtered_policy_df.columns:
    #     fig = px.bar(
    #         filtered_policy_df[filtered_policy_df["isCancelled"] == 0].groupby("PRODUCT").size().reset_index(name="Active Policies"),
    #         x="PRODUCT",
    #         y="Active Policies",
    #         title="Active Policies by Product"
    #     )
    #     st.plotly_chart(fig, use_container_width=True)

    # # Chart: Claims by Policy [testing]
    # if not filtered_claims_df.empty:
    #     fig2 = px.histogram(
    #         filtered_claims_df,
    #         x="POLICY_NO",
    #         title="Claims Count by Policy"
    #     )
    #     st.plotly_chart(fig2, use_container_width=True)