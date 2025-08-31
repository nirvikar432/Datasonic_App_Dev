import streamlit as st
import pandas as pd
import sys
from db_utils import fetch_data
from pathlib import Path

# ✅ Add the utils directory to the path
utils_path = Path(__file__).parent.parent / "utils"
sys.path.insert(0, str(utils_path))

def policy_tab():
    st.header("Policy Management")
    policy_query = "SELECT TOP 100 * FROM New_Policy"
    policies = fetch_data(policy_query)
    df_policies = pd.DataFrame(policies) if policies else pd.DataFrame()
    

    col1, col2 = st.columns([7, 3])
    with col2:
        search_col1, search_col2 = st.columns([40, 10])
        policy_search = search_col1.text_input("Search", key="policy_search", placeholder="Search", label_visibility="collapsed")
        search_button = search_col2.button("🔎", key="policy_search_button")
    with col1:
        st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)

    try:
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
            
            # Table with renamed columns
            display_df = df_policies.iloc[start_idx:end_idx].reset_index(drop=True)
            
            # Define column name mappings (customize as needed)
            column_mapping = {
                'CUST_ID': 'Customer ID',
                'EXECUTIVE': 'Executive',
                'BODY': 'Body Type',
                'MAKE': 'Vehicle Make',
                'MODEL': 'Vehicle Model',
                'USE_OF_VEHICLE': 'Vehicle Use',
                'MODEL_YEAR': 'Model Year',
                'CHASSIS_NO': 'Chassis Number',
                'REGN': 'Registration',
                'POLICY_NO': 'Policy Number',
                'POL_EFF_DATE': 'Effective Date',
                'POL_EXPIRY_DATE': 'Expiry Date',
                'SUM_INSURED': 'Sum Insured',
                'POL_ISSUE_DATE': 'Issue Date',
                'PREMIUM2': 'Premium Amount',
                'DRV_DOB': 'Driver DOB',
                'DRV_DLI': 'Driver License',
                'VEH_SEATS': 'Vehicle Seats',
                'PRODUCT': 'Product Type',
                'POLICYTYPE': 'Policy Type',
                'NATIONALITY': 'Nationality',
                'Broker_ID': 'Broker ID',
                'Broker_Name': 'Broker Name',
                'Facility_ID': 'Facility ID',
                'Facility_Name': 'Facility Name',
                'isCancelled': 'Cancel Status',
                'isLapsed': 'Lapse Status',
                'CANCELLATION_DATE': 'Cancellation Date',
                'TransactionType': 'Transaction Type'
            }
            
            # Rename columns that exist in the dataframe
            display_df = display_df.rename(columns=column_mapping)
            
            # Set index to start from 1
            display_df.index = display_df.index + 1
            st.dataframe(display_df, use_container_width=True, height=410, hide_index=True)

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
                    key="policy_page"
                )
        else:
            st.info("No policy data found.")
    except Exception as e:
        st.error(f"Error fetching policies: {e}")