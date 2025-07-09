import streamlit as st
import pandas as pd
from db_utils import fetch_data

def policy_tab():
    st.header("Policies")
    policy_query = "SELECT TOP 100 * FROM Policy"
    policies = fetch_data(policy_query)
    df_policies = pd.DataFrame(policies) if policies else pd.DataFrame()
    

    col1, col2 = st.columns([7, 3])
    with col2:
        search_col1, search_col2 = st.columns([40, 10])
        policy_search = search_col1.text_input("Search", key="policy_search", placeholder="Global Search", label_visibility="collapsed")
        search_button = search_col2.button("🔎", key="policy_search_button")
    with col1:
        st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)

    try:
        for col in ["isCancelled", "TransactionType", "isLapsed", "CANCELLATION_DATE"]:
            if col in df_policies.columns:
                df_policies = df_policies.drop(columns=[col])
        if policy_search and not df_policies.empty:
            mask = df_policies.apply(lambda row: row.astype(str).str.contains(policy_search, case=False, na=False).any(), axis=1)
            df_policies = df_policies[mask]

        if not df_policies.empty:
            total_rows = len(df_policies)
            # Default page size
            page_size = st.session_state.get("policy_page_size", 10)
            total_pages = (total_rows - 1) // page_size + 1
            page_num = st.session_state.get("policy_page", 1)
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size

            # Caption
            st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")
            # Table
            # Set index to start from 1
            display_df = df_policies.iloc[start_idx:end_idx].reset_index(drop=True)
            display_df.index = display_df.index + 1
            st.dataframe(display_df)

            # Show page size and page selection below the table
            space, col_page, space, col_size = st.columns([10, 2,10,2])
            with col_size:
                page_size = st.selectbox(
                    "Records",
                    options=[10, 25, 50, 100, len(df_policies) if len(df_policies) > 0 else 1],
                    index=0,
                    key="policy_page_size"
                )
            with col_page:
                total_pages = (total_rows - 1) // page_size + 1
                page_num = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=page_num,
                    step=1,
                    key="policy_page",
                )
        else:
            st.info("No policy data found.")
    except Exception as e:
        st.error(f"Error fetching policies: {e}")