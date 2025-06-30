import streamlit as st
from policy_forms import policy_manual_form
from db_utils import insert_policy, update_policy, fetch_data

def policy_edit_tab():
    st.header("Policy Edit")
    if "policy_edit_page" not in st.session_state:
        st.session_state.policy_edit_page = "main"

    if st.session_state.policy_edit_page == "main":
        transaction_type = st.selectbox("Select Transaction Type", ["Pre-Bind", "New Business", "MTA", "Renewal", "Policy Cancellation"])
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

            # --- Progress Bar for New Business Form ---
            if form_data:
                total_fields = len(form_data)
                filled_fields = sum(1 for v in form_data.values() if str(v).strip())
                progress = min(filled_fields / total_fields, 1.0) if total_fields > 0 else 0
                st.progress(progress, text=f"Form completion: {int(progress*100)}%")

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
        elif ttype == "Pre-Bind":
            st.markdown("#### Pre-Bind Form")
        
        elif ttype == "Policy Cancellation":
            # Step 1: Enter Policy Number
            if "cancel_policy_fetched" not in st.session_state:
                st.session_state.cancel_policy_fetched = False
                st.session_state.cancel_policy_data = None

            if not st.session_state.cancel_policy_fetched:
                with st.form("cancel_policy_fetch_form"):
                    policy_no = st.text_input("Enter Policy Number *", key="cancel_policy_no")
                    fetch_btn = st.form_submit_button("Fetch Policy")
                    back_btn = st.form_submit_button("Back")
                    if fetch_btn:
                        if not policy_no.strip():
                            st.error("Please enter a policy number.")
                        else:
                            query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                            result = fetch_data(query)
                            if result:
                                # Show already cancelled warning at initial state
                                if result[0].get("isCancelled", 0) == 1:
                                    st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                                else:
                                    st.session_state.cancel_policy_fetched = True
                                    st.session_state.cancel_policy_data = result[0]
                                    st.session_state.cancel_final_confirm = False
                            else:
                                st.warning("No policy found with that number.")
                    if back_btn:
                        st.session_state.policy_edit_page = "main"
                        st.session_state.cancel_policy_fetched = False
                        st.session_state.cancel_policy_data = None
                        st.session_state.cancel_final_confirm = False
                        st.rerun()
            else:
                policy_data = st.session_state.cancel_policy_data
                from datetime import date
                with st.form("cancel_policy_form"):
                    # Show all fields, only premium is editable
                    for key, value in policy_data.items():
                        if key.lower() == "premium2":
                            new_premium = st.text_input("Return Premium", value=str(value), key="cancel_edit_premium")
                            continue
                        elif key.lower() == "cancellation_date":
                            cancel_date = st.date_input("Cancellation Date", value=date.today(), key="cancel_date")
                        elif key.lower() == "iscancelled":
                            continue  # Don't show isCancelled
                        else:
                            st.text_input(key, value=str(value), disabled=True, key=f"cancel_{key}")
                    

                    confirm_cancel = st.checkbox("I confirm I want to cancel this policy", key="cancel_confirm")
                    submit_cancel = st.form_submit_button("Submit Cancellation")
                    back_cancel = st.form_submit_button("Back")

                    if submit_cancel:
                        if not confirm_cancel:
                            st.warning("Please confirm cancellation by checking the box before submitting.")
                        # Double confirm before DB update
                        elif not st.session_state.get("cancel_final_confirm", False):
                            st.session_state.cancel_final_confirm = True
                            st.warning("This action will permanently cancel the policy. Click 'Submit Cancellation' again to proceed.")
                        else:
                            try:
                                # premium_val = float(new_premium) if new_premium is not None else 0
                                negative_premium = -abs(float(new_premium) if new_premium is not None else 0)
                                update_policy(
                                    policy_data["POLICY_NO"],
                                    {
                                        "isCancelled": 1,
                                        "PREMIUM2": str(negative_premium),
                                        "CANCELLATION_DATE": str(cancel_date)
                                    }
                                )
                                st.success(f"Policy {policy_data['POLICY_NO']} cancelled successfully.")
                                time.sleep(3)
                                st.session_state.policy_edit_page = "main"
                                st.session_state.cancel_policy_fetched = False
                                st.session_state.cancel_policy_data = None
                                st.session_state.cancel_final_confirm = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cancellation failed: {e}")
                    if back_cancel:
                        st.session_state.policy_edit_page = "main"
                        st.session_state.cancel_policy_fetched = False
                        st.session_state.cancel_policy_data = None
                        st.session_state.cancel_final_confirm = False
                        st.rerun()

        elif ttype == "MTA":
            if "fetched" not in st.session_state:
                st.session_state.fetched = False

            # Step 1: Policy number input form
            if not st.session_state.fetched:
                with st.form("mta_policy_form"):
                    policy_no = st.text_input("Enter Policy Number *")
                    fetch = st.form_submit_button("Proceed")
                    back = st.form_submit_button("Back")
                    if fetch and policy_no.strip():
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

                # Define editable and non-editable fields for MTA
                non_editable_fields = [
                    "POLICY_NO", "CHASSIS_NO", "POL_EFF_DATE", "POL_EXPIRY_DATE"
                ]
                editable_fields = [
                    "SUM INSURED", "PREMIUM2", "USE_OF_VEHICLE", "VEH_SEATS", "PRODUCT",
                    "POLICYTYPE", "BODY", "MAKE", "MODEL", "USE_OF_VEHICLE", "MODEL_YEAR", "REGN"
                ]
                # Normalize keys for matching
                editable_keys = [k.replace(" ", "").lower() for k in editable_fields]
                non_editable_keys = [k.replace(" ", "").lower() for k in non_editable_fields]

                with st.form("update_mta_policy_form"):
                    for key, value in policy_data.items():
                        input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                        key_norm = key.replace(" ", "").lower()
                        if key_norm in non_editable_keys:
                            st.text_input(f"{key}", value=str(value), key=input_key, disabled=True)
                        elif key_norm in editable_keys:
                            st.text_input(f"{key}", value=str(value), key=input_key)
                        elif key.lower() in ["cancellation_date", "iscancelled"]:
                            continue  # Skip cancellation date and isCancelled field
                        else:
                            st.text_input(f"{key}", value=str(value), key=input_key, disabled=True)

                    submit = st.form_submit_button("Submit")
                    back2 = st.form_submit_button("Back")
                    if submit:
                        for key, value in policy_data.items():
                            input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                            key_norm = key.replace(" ", "").lower()
                            if key_norm in non_editable_keys:
                                new_val = value  # keep as is
                            elif key_norm in editable_keys:
                                new_val = st.session_state[input_key]
                            else:
                                new_val = value
                            if str(new_val) != str(value):
                                edit_fields[key] = new_val
                        if edit_fields:
                            try:
                                update_policy(policy_data["POLICY_NO"], edit_fields)
                                st.success("Selected fields updated successfully.")
                                time.sleep(3)
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
            

        else:  # Renewal
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

                # Render all fields with data, increment start and end year by +1, and make year fields uneditable
                with st.form("update_policy_form"):
                    for key, value in policy_data.items():
                        input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                        # Detect year fields
                        if key.lower() in ["pol_eff_date", "pol_expiry_date"]:
                            try:
                                new_year = int(value) + 1
                            except Exception:
                                new_year = value
                            st.text_input(f"{key}", value=str(new_year), key=input_key, disabled=True)
                        elif key.lower() in ["cancellation_date", "iscancelled"]:
                            continue  # Skip cancellation date and isCancelled field
                        else:
                            st.text_input(f"{key}", value=str(value), key=input_key)

                    submit = st.form_submit_button("Submit")
                    back2 = st.form_submit_button("Back")
                    if submit:
                        # Collect all fields except year fields (since they are uneditable)
                        for key, value in policy_data.items():
                            input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                            if key.lower() in ["start_year", "end_year"]:
                                # Use incremented value
                                try:
                                    new_val = str(int(value) + 1)
                                except Exception:
                                    new_val = str(value)
                            else:
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

def claims_edit_tab():
        st.header("Claims Edit")
        st.info("Claims edit functionality coming soon...")
        # Placeholder for future claims edit functionality