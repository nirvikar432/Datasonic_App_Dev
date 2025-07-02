import streamlit as st
import pandas as pd
from db_utils import fetch_data

def claims_tab():
    st.header("Claims")
    claims_query = "SELECT TOP 20 * FROM Claims"
    claims = fetch_data(claims_query)
    df_claims = pd.DataFrame(claims) if claims else pd.DataFrame()

    col1, col2 = st.columns([7, 3])
    with col2:
        search_col1, search_col2 = st.columns([40, 10])
        claims_search = search_col1.text_input("Search", key="claims_search", placeholder="Search", label_visibility="collapsed")
        search_button = search_col2.button("🔎", key="claims_search_button")
    with col1:
        st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)

    try:
        if claims_search and not df_claims.empty:
            mask = df_claims.apply(lambda row: row.astype(str).str.contains(claims_search, case=False, na=False).any(), axis=1)
            df_claims = df_claims[mask]

        if not df_claims.empty:
            total_rows = len(df_claims)
            # Default page size
            page_size = st.session_state.get("claims_page_size", 10)
            total_pages = (total_rows - 1) // page_size + 1
            page_num = st.session_state.get("claims_page", 1)
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size

            # Show caption above the table
            st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")
            # Show table
            st.dataframe(df_claims.iloc[start_idx:end_idx])

            # Show page size and page selection below the table
            space, col_page, space, col_size = st.columns([10, 2, 10, 2])
            with col_size:
                page_size = st.selectbox(
                    "Records",
                    options=[10, 25, 50, 100, len(df_claims) if len(df_claims) > 0 else 1],
                    index=0,
                    key="claims_page_size"
                )
            with col_page:
                total_pages = (total_rows - 1) // page_size + 1
                page_num = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=page_num,
                    step=1,
                    key="claims_page",
                )
        else:
            st.info("No claims data found.")
    except Exception as e:
        st.error(f"Error fetching claims: {e}")