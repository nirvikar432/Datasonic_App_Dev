import streamlit as st
from policy_forms import policy_manual_form
from prebind_forms import (
    prebind_quotation_form, 
    quotation_summary_display, 
    quotation_action_buttons, 
    quotation_history_display,
    convert_quotation_to_policy_data
)
from db_utils import insert_policy, update_policy, fetch_data, insert_quotation, update_quotation, mark_quotation_converted
import time
from datetime import datetime, timedelta, date


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

        # if "temp_policy_no" not in st.session_state:
        #     # You can use a prefix and increment, or fetch the max from DB if needed
        #     last_temp = st.session_state.get("last_temp_policy_no", 1000)
        #     st.session_state.temp_policy_no = f"TEMP{last_temp + 1}"
        #     st.session_state.last_temp_policy_no = last_temp + 1

        if ttype == "New Business":
            form_data, submit, back = policy_manual_form()

            # # --- Progress Bar for New Business Form ---
            # if form_data:
            #     total_fields = len(form_data)
            #     filled_fields = sum(1 for v in form_data.values() if str(v).strip())
            #     progress = min(filled_fields / total_fields, 1.0) if total_fields > 0 else 0
            #     st.progress(progress, text=f"Form completion: {int(progress*100)}%")

            if submit:
                if not form_data["POLICY_NO"].strip():
                    st.error("Fill all the mandatory fields.")
                else:
                    form_data["TransactionType"] = "New Business"  # Set type
                    st.success("New Business form submitted successfully.")
                    try:
                        insert_policy(form_data)
                        st.success("Policy inserted into the database.")
                        # # Increment temp policy number for next use
                        # st.session_state.temp_policy_no = f"TEMP{int(st.session_state.temp_policy_no[4:]) + 1}"
                        # st.session_state.last_temp_policy_no = int(st.session_state.temp_policy_no[4:])
                    except Exception as db_exc:
                        st.error(f"Failed to insert policy: {db_exc}")
            if back:
                st.session_state.policy_edit_page = "main"
                st.rerun()

        elif ttype == "Pre-Bind":
            if "prebind_step" not in st.session_state:
                st.session_state.prebind_step = "quotation_form"
            
            if st.session_state.prebind_step == "quotation_form":
                st.markdown("#### Pre-Bind Quotation Form")
                
                # Use the prebind quotation form
                form_data, submit, back, missing_fields = prebind_quotation_form()
                
                if submit:
                    if missing_fields:
                        st.error(f"Please fill all mandatory fields: {', '.join(missing_fields)}")
                    else:
                        try:
                            # Insert quotation into database
                            insert_quotation(form_data)
                            st.session_state.quotation_data = form_data
                            st.session_state.prebind_step = "quotation_summary"
                            st.success("Quotation generated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to generate quotation: {e}")
                
                if back:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.prebind_step = "quotation_form"
                    if "temp_policy_id" in st.session_state:
                        del st.session_state.temp_policy_id
                    st.rerun()
            
            elif st.session_state.prebind_step == "quotation_summary":
                quotation_data = st.session_state.quotation_data
                
                # Display quotation summary
                quotation_summary_display(quotation_data)
                
                # Action buttons
                download_pdf, send_quote, convert_policy, back_to_form = quotation_action_buttons()
                
                if download_pdf:
                    # TODO: Implement PDF generation
                    st.info("PDF generation feature coming soon!")
                
                if send_quote:
                    # Update status to "Sent"
                    st.session_state.quotation_data['STATUS'] = "Sent"
                    st.success("Quote status updated to 'Sent'")
                    st.rerun()
                
                if convert_policy:
                    # Navigate to policy conversion
                    st.session_state.policy_edit_page = "convert_policy"
                    st.rerun()
                
                if back_to_form:
                    st.session_state.prebind_step = "quotation_form"
                    st.rerun()
                
                # Display quotation history
                quotation_history_display(quotation_data.get("CUST_ID", ""))
                
                if st.button("Back to Main"):
                    st.session_state.policy_edit_page = "main"
                    st.session_state.prebind_step = "quotation_form"
                    if "temp_policy_id" in st.session_state:
                        del st.session_state.temp_policy_id
                    if "quotation_data" in st.session_state:
                        del st.session_state.quotation_data
                    st.rerun()

        elif st.session_state.policy_edit_page == "convert_policy":
            st.markdown("#### Convert Quotation to Policy")
            quotation_data = st.session_state.quotation_data
            
            # Convert quotation data to policy form defaults
            policy_defaults = convert_quotation_to_policy_data(quotation_data)
            
            # Use policy manual form with pre-filled data
            form_data, submit, back = policy_manual_form(defaults=policy_defaults)
            
            if submit:
                if not form_data["POLICY_NO"].strip():
                    st.error("Please enter a Policy Number.")
                else:
                    form_data["TransactionType"] = "New Business"
                    form_data["CONVERTED_FROM_TEMP"] = quotation_data["TEMP_POLICY_ID"]
                    
                    try:
                        insert_policy(form_data)
                        # Mark quotation as converted
                        mark_quotation_converted(quotation_data["TEMP_POLICY_ID"], form_data["POLICY_NO"])
                        st.success(f"Policy {form_data['POLICY_NO']} created successfully from quotation!")
                        time.sleep(2)
                        
                        # Clean up session state
                        st.session_state.policy_edit_page = "main"
                        st.session_state.prebind_step = "quotation_form"
                        if "temp_policy_id" in st.session_state:
                            del st.session_state.temp_policy_id
                        if "quotation_data" in st.session_state:
                            del st.session_state.quotation_data
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create policy: {e}")
            
            if back:
                st.session_state.prebind_step = "quotation_summary"
                st.session_state.policy_edit_page = "transaction_form"
                st.rerun()
        
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
                                # Show already cancelled or Lapsed warning at initial state
                                if result[0].get("isCancelled", 0) == 1:
                                    st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                                elif result[0].get("isLapsed", 0) == 1:
                                    st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
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
                with st.form("cancel_policy_form"):
                    # Show all fields, only premium is editable
                    for key, value in policy_data.items():
                        if key.lower() == "premium2":
                            new_premium = st.text_input("Return Premium", value=str(value), key="cancel_edit_premium")
                            continue
                        elif key.lower() == "cancellation_date":
                            cancel_date = st.date_input("Cancellation Date", value=date.today(), key="cancel_date")
                        elif key.lower() in ["iscancelled", "transactiontype", "islapsed"]:
                            continue  # Don't show isCancelled, TransactionType, and isLapsed
                        else:
                            st.text_input(key, value=str(value), disabled=True, key=f"cancel_{key}")
                    

                    confirm_cancel = st.checkbox("I confirm I want to cancel this policy", key="cancel_confirm")
                    submit_cancel = st.form_submit_button("Submit Cancellation")
                    back_cancel = st.form_submit_button("Back")

                    if submit_cancel:
                        if not confirm_cancel:
                            st.warning("Please confirm cancellation by checking the box before submitting.")
                        # Validate return premium does not exceed original premium
                        elif float(new_premium) > float(policy_data.get("PREMIUM2", 0)):
                            st.error("Return Premium cannot exceed the original premium.")
                        # Double confirm before DB update
                        elif not st.session_state.get("cancel_final_confirm", False):
                            st.session_state.cancel_final_confirm = True
                            st.warning("This action will permanently cancel the policy. Click 'Submit Cancellation' again to proceed.")
                        else:
                            try:
                                negative_premium = -abs(float(new_premium) if new_premium is not None else 0)
                                update_policy(
                                    policy_data["POLICY_NO"],
                                    {
                                        "isCancelled": 1,
                                        "PREMIUM2": int(negative_premium),
                                        "CANCELLATION_DATE": str(cancel_date),
                                        "TransactionType": "Policy Cancellation"
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
                            # Show already cancelled or Lapsed warning at initial state
                            if result[0].get("isCancelled", 0) == 1:
                                st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                            elif result[0].get("isLapsed", 0) == 1:
                                st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
                            else:
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
                    "SUM INSURED","DRV_DOB", "DRV_DLI", "PREMIUM2", "USE_OF_VEHICLE", "VEH_SEATS", "PRODUCT",
                    "POLICYTYPE", "BODY", "MAKE", "MODEL", "USE_OF_VEHICLE", "MODEL_YEAR", "REGN"
                ]
                # Normalize keys for matching
                editable_keys = [k.replace(" ", "").lower() for k in editable_fields]
                non_editable_keys = [k.replace(" ", "").lower() for k in non_editable_fields]

                with st.form("update_mta_policy_form"):
                    for key, value in policy_data.items():
                        input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                        key_norm = key.replace(" ", "").lower()
                        # Do not show Transaction Type and isLapsed fields
                        if key_norm in ["transactiontype", "islapsed"]:
                            continue
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
                            # Always update TransactionType for MTA
                            edit_fields["TransactionType"] = "MTA"
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
                            # Show already cancelled or Lapsed warning at initial state
                            if result[0].get("isCancelled", 0) == 1:
                                st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                            elif result[0].get("isLapsed", 0) == 1:
                                st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
                            else:
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

                        if key.lower() in ["islapsed", "transactiontype","cancellation_date", "iscancelled"]:
                            continue  # Field is hidden from the user
                        # Detect year fields
                        if key.lower() in ["pol_eff_date", "pol_expiry_date"]:
                            try:
                                # Parse the date string to a date object
                                date_obj = datetime.strptime(str(value), "%Y-%m-%d")
                                # Add one year (365 days, or use replace for exact year increment)
                                new_date = date_obj.replace(year=date_obj.year + 1)
                                new_date_str = new_date.strftime("%Y-%m-%d")
                            except Exception:
                                new_date_str = str(value)
                            st.text_input(f"{key}", value=new_date_str, key=input_key, disabled=True)
                        elif key.lower() == "pol_issue_date":
                            # Set POL_ISSUE_DATE as current date (uneditable)
                            today_str = str(date.today())
                            st.text_input("POL_ISSUE_DATE", value=today_str, key=input_key, disabled=True)
                        else:
                            st.text_input(f"{key}", value=str(value), key=input_key)

                    submit = st.form_submit_button("Submit")
                    back2 = st.form_submit_button("Back")
                    if submit:
                        # Collect all fields except year fields (since they are uneditable)
                        for key, value in policy_data.items():
                            input_key = f"edit_val_{key}_{policy_data['POLICY_NO']}"
                            # Skip hidden fields
                            if key.lower() in ["islapsed", "transactiontype", "cancellation_date", "iscancelled"]:
                                continue
                            if key.lower() in ["start_year", "end_year"]:
                                try:
                                    new_val = str(int(value) + 1)
                                except Exception:
                                    new_val = str(value)
                            elif key.lower() == "pol_issue_date":
                                new_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            elif key.lower() in ["pol_eff_date", "pol_expiry_date"]:
                                # These are disabled, so use the incremented value from above
                                try:
                                    date_obj = datetime.strptime(str(value), "%Y-%m-%d")
                                    new_date = date_obj.replace(year=date_obj.year + 1)
                                    new_val = new_date.strftime("%Y-%m-%d")
                                except Exception:
                                    new_val = str(value)
                            else:
                                new_val = st.session_state.get(input_key, value)
                            if str(new_val) != str(value):
                                edit_fields[key] = new_val
                        # Always update TransactionType for Renewal
                        edit_fields["TransactionType"] = "Renewal"
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