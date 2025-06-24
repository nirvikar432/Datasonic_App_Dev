import streamlit as st
import pandas as pd
import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from db_utils import fetch_data

def main():
    st.title("Policy and Claims Management")

    tabs = st.tabs(["Policies", "Claims","Policies Edit", "Claims Edit"])

    with tabs[0]:
        st.header("Policies")
        col1, col2, col3 = st.columns([7, 3, 1])
        with col2:
            policy_search = st.text_input("Search", key="policy_search", placeholder="Enter the column name", label_visibility="visible")
        with col3:
            st.markdown('<span style="font-size: 2em;"></span>', unsafe_allow_html=True)
        with col1:
            policy_limit = st.selectbox(
                "Records",
                options=[10, 50, 100, 500, "All"],
                index=0
            )

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
            claims_limit = st.selectbox(
                "Records",
                options=[10, 50, 100, 500, "All"],
                index=0,
                key="claims_limit"
            )

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
        # Use session state to manage navigation between pages
        if "policy_edit_page" not in st.session_state:
            st.session_state.policy_edit_page = "main"

        if st.session_state.policy_edit_page == "main":
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Pre Bind", key="prebind_btn"):
                    st.session_state.policy_edit_page = "prebind"
                    st.rerun()
            with col2:
                if st.button("Post Bind", key="postbind_btn"):
                    st.session_state.policy_edit_page = "postbind"
                    st.rerun()

        elif st.session_state.policy_edit_page == "prebind":
            st.markdown("#### Pre Bind Options")
            pb_col1, pb_col2, pb_col3 = st.columns(3)
            with pb_col1:
                if st.button("Manual Form", key="prebind_manual"):
                    st.session_state.policy_edit_page = "prebind_manual_form"
                    st.rerun()
            with pb_col2:
                st.button("From PDF", key="prebind_pdf")
            with pb_col3:
                st.button("From Email", key="prebind_email")
            if st.button("Back", key="prebind_back"):
                st.session_state.policy_edit_page = "main"
                st.rerun()
        elif st.session_state.policy_edit_page == "prebind_manual_form":
            st.markdown("#### Pre Bind - Manual Form")
            with st.form("prebind_manual_form"):
                cust_id = st.number_input("CUST_ID", step=1, format="%d")
                executive = st.text_input("EXECUTIVE")
                body = st.text_input("BODY")
                make = st.text_input("MAKE")
                model = st.text_input("MODEL")
                use_of_vehicle = st.text_input("USE_OF_VEHICLE")
                model_year = st.number_input("MODEL_YEAR", step=1, format="%d")
                chassis_no = st.text_input("CHASSIS_NO")
                regn = st.text_input("REGN")
                policy_no = st.text_input("POLICY_NO *", help="Mandatory")
                pol_eff_date = st.date_input("POL_EFF_DATE")
                pol_expiry_date = st.date_input("POL_EXPIRY_DATE")
                sum_insured = st.number_input("SUM_INSURED", format="%.2f")
                pol_issue_date = st.date_input("POL_ISSUE_DATE")
                premium2 = st.number_input("PREMIUM2", format="%.2f")
                drv_dob = st.date_input("DRV_DOB")
                drv_dli = st.date_input("DRV_DLI")
                veh_seats = st.number_input("VEH_SEATS", step=1, format="%d")
                submitted = st.form_submit_button("Submit")
                back = st.form_submit_button("Back")
                if submitted:
                    if not policy_no.strip():
                        st.error("POLICY_NO is mandatory. Please fill it before submitting.")
                    else:
                        st.success("Form submitted successfully!")
                        # Here you can add your DB insert logic
                if back:
                    st.session_state.policy_edit_page = "prebind"
                    st.rerun()

        elif st.session_state.policy_edit_page == "postbind":
            st.markdown("#### Post Bind Options")
            pob_col1, pob_col2, pob_col3 = st.columns(3)
            with pob_col1:
                st.button("Manual Form", key="postbind_manual")
            with pob_col2:
                st.button("From PDF", key="postbind_pdf")
            with pob_col3:
                st.button("From Email", key="postbind_email")
            if st.button("Back", key="postbind_back"):
                st.session_state.policy_edit_page = "main"
                st.rerun()

    with tabs[3]:
        st.header("Claims Edit")
        col1, col2, col3 = st.columns([7, 3, 1])
        # Add your Claims Edit logic here

if __name__ == "__main__":
    main()