import streamlit as st
import pandas as pd
import sys
import os


# Set browser tab title and page config
st.set_page_config(page_title="Datasonic Policy Portal", page_icon="📝", layout="wide")


# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from db_utils import fetch_data, insert_policy,update_policy
from policy_forms import policy_manual_form


def main():
    st.title("Policy and Claims Management")
    tabs = st.tabs(["Policies", "Claims", "Policy Edit", "Claims Edit"])

    with tabs[0]:
        st.header("Policies")
        # Fetch data first
        # policy_query = "SELECT * FROM Policy WHERE isCancelled = 0"
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
            # isCancelled no need
            if "isCancelled" in df_policies.columns:
                df_policies = df_policies.drop(columns=["isCancelled"])
            if policy_search and not df_policies.empty:
                mask = df_policies.apply(lambda row: row.astype(str).str.contains(policy_search, case=False, na=False).any(), axis=1)
                df_policies = df_policies[mask]

            # --- Pagination ---
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

    with tabs[1]:
        st.header("Claims")
        # Always fetch all records, then paginate in pandas
        # claims_query = "SELECT * FROM Claims"
        claims_query = "SELECT TOP 20 * FROM Claims"
        claims = fetch_data(claims_query)
        df_claims = pd.DataFrame(claims) if claims else pd.DataFrame()

        col1, col2, col3 = st.columns([7, 3, 1])
        with col1:
            page_size = st.selectbox(
                "Records per page",
                options=[10, 25, 50, 100, 500, len(df_claims) if len(df_claims) > 0 else 1],
                index=0,
                key="claims_page_size"
            )
        with col2:
            search_col1, search_col2 = st.columns([3, 1])
            claims_search = search_col1.text_input("Search", key="claims_search", placeholder="Search", label_visibility="hidden")
            claims_search_button = search_col2.button("Search", key="claims_search_button")
        with col3:
            st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)
        

        try:

            if claims_search and not df_claims.empty:
                mask = df_claims.apply(lambda row: row.astype(str).str.contains(claims_search, case=False, na=False).any(), axis=1)
                df_claims = df_claims[mask]
            # --- Pagination ---
            if not df_claims.empty:
                total_rows = len(df_claims)
                total_pages = (total_rows - 1) // page_size + 1
                page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="claims_page")
                start_idx = (page_num - 1) * page_size
                end_idx = start_idx + page_size
                st.dataframe(df_claims.iloc[start_idx:end_idx])
                st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")
            else:
                st.info("No claims data found.")
        except Exception as e:
            st.error(f"Error fetching claims: {e}")

    with tabs[2]:
        st.header("Policy Edit")
        if "policy_edit_page" not in st.session_state:
            st.session_state.policy_edit_page = "main"

        if st.session_state.policy_edit_page == "main":
            transaction_type = st.selectbox("Select Transaction Type", ["New Business", "MTA", "Renewal"])
            if st.button("Proceed"):
                st.session_state.transaction_type = transaction_type
                st.session_state.policy_edit_page = "transaction_form"
                st.rerun()

        elif st.session_state.policy_edit_page == "transaction_form":
            ttype = st.session_state.transaction_type
            st.markdown(f"### {ttype} Form")

            if ttype == "New Business":
                # st.markdown("#### New Business Form")
                form_data, submit, back = policy_manual_form()

                if submit:
                    if not form_data["POLICY_NO"].strip():
                        st.error("Fill all the mandatory fields.")
                    else:
                        st.success("New Business form submitted successfully.")
                        try:
                            insert_policy(form_data)
                            st.success("Policy inserted into the database.")
                        except Exception as db_exc:
                            st.error(f"Failed to insert policy: {db_exc}")
                if back:
                    st.session_state.policy_edit_page = "main"
                    st.rerun()

            else:  # MTA or Renewal
                if "fetched" not in st.session_state:
                    st.session_state.fetched = False
                
                # Step 1: Policy number input form
                if not st.session_state.fetched:
                    with st.form("existing_policy_form"):
                        policy_no = st.text_input("Enter Policy Number *")
                        fetch = st.form_submit_button("Proceed")
                        back = st.form_submit_button("Back")
                        if fetch and policy_no.strip():
                        # Fetch policy data
                            query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                            result = fetch_data(query)
                            if result:
                                st.session_state.fetched = True
                                st.session_state.policy_data = result[0]
                                st.session_state.edit_fields = {}
                            else:
                                st.warning("No policy found with that number.")
                        elif fetch:
                            st.warning("Please enter Policy Number to proceed.")
                        if back:
                            st.session_state.policy_edit_page = "main"
                            st.session_state.fetched = False
                            st.rerun()

                # Step 2: Show editable form if fetched
                if st.session_state.get("fetched") and "policy_data" in st.session_state:
                    st.markdown(f"#### {ttype} - Update Form")
                    policy_data = st.session_state.policy_data
                    edit_fields = {}

                    # 1. Render checkboxes and text inputs OUTSIDE the form for instant interactivity
                    for key, value in policy_data.items():
                        edit_key = f"edit_{key}_{policy_data['POLICY_NO']}"
                        input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                        
                        st.text_input(f"{key}",value=str(value),key=input_key,disabled=not st.session_state.get(edit_key, False),label_visibility="hidden")
                        st.checkbox(f"{key}", key=edit_key)

                    # 2. Only the submit/back buttons are in the form
                    with st.form("update_policy_form"):
                        submit = st.form_submit_button("Submit")
                        back2 = st.form_submit_button("Back")
                        if submit:
                            # Collect only edited fields
                            for key, value in policy_data.items():
                                edit_key = f"edit_{key}_{policy_data['POLICY_NO']}"
                                input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                                if st.session_state.get(edit_key, False):
                                    new_val = st.session_state[input_key]
                                    if str(new_val) != str(value):
                                        edit_fields[key] = new_val
                            if edit_fields:
                                try:
                                    update_policy(policy_data["POLICY_NO"], edit_fields)
                                    st.success("Selected fields updated successfully.")
                                    st.session_state.fetched = False
                                    st.session_state.policy_edit_page = "main"
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Update failed: {e}")
                            else:
                                st.info("No fields selected for update.")
                        if back2:
                            st.session_state.fetched = False
                            st.rerun()

    with tabs[3]:
        st.header("Claims Edit")
        st.info("Claims edit functionality coming soon...")
        # Placeholder for future claims edit functionality

    # Footer
    st.markdown(
        """
        <style>
            footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: #f1f1f1;
                text-align: center;
                padding: 0px;
            }
        </style>
        <footer>
            <p>© 2024 Datasonic. All rights reserved.</p>
        </footer>
        """,
        unsafe_allow_html=True
    )   


if __name__ == "__main__":
    main()



