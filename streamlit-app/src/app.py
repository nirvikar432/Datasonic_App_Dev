import streamlit as st
import pandas as pd
import sys
import os


# Set browser tab title and page config
st.set_page_config(page_title="Datasonic Policy Portal", page_icon="📝", layout="wide")

# Custom CSS for light background
# st.markdown(
#     """
#     <style>
#         body, .stApp {
#             background-color: #f8f9fa !important;
#         }
#         .stTextInput > div > div > input, .stSelectbox > div > div > div {
#             background-color: #fff !important;
#             color: #black !important;
#         }
#         .stDataFrame, .stTable {
#             background-color: #fff !important;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from db_utils import fetch_data
from db_utils import insert_policy
from policy_forms import policy_manual_form


def main():
    st.title("Policy and Claims Management")
    tabs = st.tabs(["Policies", "Claims", "Policies Edit", "Claims Edit"])
    with tabs[0]:
        st.header("Policies")
        col1, col2, col3 = st.columns([7, 3, 1])
        with col2:
            policy_search = st.text_input("Search", key="policy_search", placeholder="Search", label_visibility="visible")
        with col3:
            st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)
        with col1:
            policy_limit = st.selectbox("Records", options=[10, 50, 100, 500, "All"], index=0)

        try:
            if policy_limit == "All":
                policy_query = "SELECT * FROM Policy"
            else:
                policy_query = f"SELECT TOP {policy_limit} * FROM Policy"
            policies = fetch_data(policy_query)
            df_policies = pd.DataFrame(policies) if policies else pd.DataFrame()
            if policy_search and not df_policies.empty:
                mask = df_policies.apply(lambda row: row.astype(str).str.contains(policy_search, case=False, na=False).any(), axis=1)
                df_policies = df_policies[mask]
            if not df_policies.empty:
                st.dataframe(df_policies)
            else:
                st.info("No policy data found.")
        except Exception as e:
            st.error(f"Error fetching policies: {e}")

    with tabs[1]:
        st.header("Claims")
        col1, col2, col3 = st.columns([7, 3, 1])
        with col2:
            claims_search = st.text_input("Search", key="claims_search", placeholder="Enter the column name", label_visibility="visible")
        with col3:
            st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)
        with col1:
            claims_limit = st.selectbox("Records", options=[10, 50, 100, 500, "All"], index=0, key="claims_limit")

        try:
            if claims_limit == "All":
                claims_query = "SELECT * FROM Claims"
            else:
                claims_query = f"SELECT TOP {claims_limit} * FROM Claims"
            claims = fetch_data(claims_query)
            df_claims = pd.DataFrame(claims) if claims else pd.DataFrame()
            if claims_search and not df_claims.empty:
                mask = df_claims.apply(lambda row: row.astype(str).str.contains(claims_search, case=False, na=False).any(), axis=1)
                df_claims = df_claims[mask]
            if not df_claims.empty:
                st.dataframe(df_claims)
            else:
                st.info("No claims data found.")
        except Exception as e:
            st.error(f"Error fetching claims: {e}")

    with tabs[2]:
        st.header("Policies Edit")
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
                # with st.form("new_business_form"):
                st.markdown("#### New Business - Manual Entry")
                # Generate and maintain a unique cust_id in the format temp_01, temp_02, etc.
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
                with st.form("existing_policy_form"):
                    policy_no = st.text_input("Enter Policy Number *")
                    fetch = st.form_submit_button("Proceed")
                    back = st.form_submit_button("Back")
                    if fetch and policy_no.strip():
                        st.session_state.fetched = True
                    elif fetch:
                        st.warning("Please enter Policy Number to proceed.")
                    if back:
                        st.session_state.policy_edit_page = "main"
                        st.rerun()

                if st.session_state.get("fetched"):
                    st.markdown(f"#### {ttype} - Update Form")
                    with st.form("update_policy_form"):
                        premium = st.number_input("Update PREMIUM", format="%.2f")
                        upload_doc = st.file_uploader("Upload Document")
                        upload_email = st.file_uploader("Upload Email")
                        submit = st.form_submit_button("Submit")
                        if submit:
                            st.success(f"{ttype} details updated successfully. Changes committed.")

    with tabs[3]:
        st.header("Claims Edit")
        st.info("Claims edit functionality coming soon...")

if __name__ == "__main__":
    main()



