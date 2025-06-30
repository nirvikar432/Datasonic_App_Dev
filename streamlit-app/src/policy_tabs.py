import streamlit as st
import pandas as pd
from db_utils import fetch_data

def policy_tab():
    st.header("Policies")
    policy_query = "SELECT TOP 20 * FROM Policy WHERE isCancelled = 0"
    policies = fetch_data(policy_query)
    df_policies = pd.DataFrame(policies) if policies else pd.DataFrame()

    col1, col2, col3 = st.columns([7, 3, 1])
    with col1:
        page_size = st.selectbox(
            "Records per page",
            options=[10, 25, 50, 100, len(df_policies) if len(df_policies) > 0 else 1],
            index=0,
            key="policy_page_size", label_visibility="collapsed", placeholder="Records per page"
        )
    with col2:
        search_col1, search_col2 = st.columns([4, 1])
        policy_search = search_col1.text_input("Search", key="policy_search", placeholder="Search", label_visibility="collapsed")
        search_button = search_col2.button("🔎", key="policy_search_button")
    with col3:
        st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)

    try:
        if "isCancelled" in df_policies.columns:
            df_policies = df_policies.drop(columns=["isCancelled"])
        if policy_search and not df_policies.empty:
            mask = df_policies.apply(lambda row: row.astype(str).str.contains(policy_search, case=False, na=False).any(), axis=1)
            df_policies = df_policies[mask]

        if not df_policies.empty:
            total_rows = len(df_policies)
            total_pages = (total_rows - 1) // page_size + 1
            page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="policy_page")
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size
            st.dataframe(df_policies.iloc[start_idx:end_idx])
            st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")
        else:
            st.info("No policy data found.")
    except Exception as e:
        st.error(f"Error fetching policies: {e}")