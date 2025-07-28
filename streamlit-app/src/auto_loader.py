from time import time
import streamlit as st
import json
import sys
import os
from datetime import datetime, date
import time
import random


# Use absolute import for testing
from policy_forms import (
    policy_manual_form,
    policy_renewal_form,
    policy_mta_form,
    policy_cancel_form,

)


from db_utils import insert_policy, update_policy, fetch_data, insert_claim, update_claim


# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fetch json data from json.json file
def fetch_json_data():
    """Fetch JSON data from a file"""
    try:
        #For testing purposes, we can load a sample JSON file
        # json_files = [
        #     "streamlit-app/utils/json/NBpolicy.json",
        #     "streamlit-app/utils/json/NBclaim.json",
        #     "streamlit-app/utils/json/REpolicy.json",
        #     "streamlit-app/utils/json/MTApolicy.json",
        #     "streamlit-app/utils/json/CANpolicy.json",
        #     "streamlit-app/utils/json/UPDATEclaim.json",
        #     "streamlit-app/utils/json/CLOclaim.json",
        #     "streamlit-app/utils/json/Reclaim.json",
        # ]
        with open("streamlit-app/utils/json/Reclaim.json", "r") as f:
        # selected_file = random.choice(json_files)
        # with open(selected_file, "r") as f:
            data = json.load(f)
            st.write("JSON Data Loaded:", data)
        return data
    except Exception as e:
        st.error(f"Error loading JSON data: {e}")
        return None

def load_policy_from_json():
    """Load policy data from JSON and route to appropriate form"""
    try:
        data = fetch_json_data()
        if not data:
            return False
        
        policy_type = data.get("Type", "")
        
        # For Renewal policies, first fetch the existing policy to get complete data
        if policy_type == "Renewal":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                    result = fetch_data(query)
                    if result:
                        # Store the original policy data in session state for renewal processing
                        st.session_state.renewal_policy_data = result[0]
                        st.session_state.renewal_policy_fetched = True
                        
                        # Combine JSON data with existing policy data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "policy_renewal_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("Renewal JSON missing POLICY_NO field")
                return False
        
        # Handle other policy types
        elif policy_type == "New Business":
            st.session_state.form_to_show = "policy_manual_form"
            st.session_state.form_defaults = data
            return True
        elif policy_type == "MTA":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                    result = fetch_data(query)
                    if result:
                        # Store the original policy data in session state for MTA processing
                        st.session_state.mta_policy_data = result[0]
                        st.session_state.mta_policy_fetched = True
                        
                        # Combine JSON data with existing policy data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "policy_mta_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("MTA JSON missing POLICY_NO field")
                return False
        elif policy_type == "Policy Cancellation":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                    result = fetch_data(query)
                    if result:
                        # Show already cancelled or Lapsed warning
                        if result[0].get("isCancelled", 0) == 1:
                            st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                            return False
                        elif result[0].get("isLapsed", 0) == 1:
                            st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
                            return False
                            
                        # Store the original policy data in session state for cancellation processing
                        st.session_state.cancel_policy_data = result[0]
                        st.session_state.cancel_policy_fetched = True
                        
                        # Combine JSON data with existing policy data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "policy_cancel_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("Cancellation JSON missing POLICY_NO field")
                return False
        elif policy_type == "New Claim":
            st.session_state.form_to_show = "claim_manual_form"
            st.session_state.form_defaults = data
            return True
        
        elif policy_type == "Claim Update":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    result = fetch_data(query)
                    if result:
                        # Check if claim is already closed
                        if result[0].get("CLAIM_STATUS", "").lower() == "closed":
                            st.warning(f"Claim {claim_no} is already closed and cannot be updated.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for update processing
                        st.session_state.claim_update_data = result[0]
                        st.session_state.claim_update_fetched = True
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "claim_update_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Update JSON missing CLAIM_NO field")
                return False
        
        elif policy_type == "Claim Close":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    result = fetch_data(query)
                    if result:
                        # Check if claim is already closed
                        if result[0].get("CLAIM_STATUS", "").lower() == "closed":
                            st.warning(f"Claim {claim_no} is already closed.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for close processing
                        st.session_state.claim_close_data = result[0]
                        st.session_state.claim_close_fetched = True
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "claim_close_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Close JSON missing CLAIM_NO field")
                return False
        
        elif policy_type == "Claim Reopen":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    result = fetch_data(query)
                    if result:
                        # Check if claim is currently closed (must be closed to reopen)
                        if result[0].get("CLAIM_STATUS", "").lower() != "closed":
                            st.warning(f"Claim {claim_no} is not closed and cannot be reopened.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for reopen processing
                        st.session_state.claim_reopen_data = result[0]
                        st.session_state.claim_reopen_fetched = True
                        
                        # Add current date to the remarks
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        original_remarks = result[0].get("CLAIM_REMARKS", "")
                        reopen_reason = data.get("REOPEN_REASON", "No reason provided")
                        new_remarks = f"{original_remarks}\n\nReopened on {current_date}: {reopen_reason}"
                        data["CLAIM_REMARKS"] = new_remarks
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        combined_data = {**result[0], **data}
                        st.session_state.form_to_show = "claim_reopen_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Reopen JSON missing CLAIM_NO field")
                return False
            
        else:
            st.error(f"Unknown policy type: {policy_type}")
            return False
    except Exception as e:
        st.error(f"Error loading policy data: {e}")
        return False

def show_policy_form():

    if hasattr(st.session_state, "form_to_show") and st.session_state.form_to_show:
        defaults = st.session_state.get("form_defaults", {})

        if st.session_state.form_to_show == "policy_manual_form":
            st.markdown("### NEW BUSINESS FORM")
            form_data, submit, back = policy_manual_form(defaults)

            if submit:
                if not form_data["POLICY_NO"].strip():
                    st.error("Fill all the mandatory fields.")
                else:
                    form_data["TransactionType"] = "New Business"
                    try:
                        insert_policy(form_data)
                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        if "form_to_show" in st.session_state:
                            del st.session_state.form_to_show
                        if "form_defaults" in st.session_state:
                            del st.session_state.form_defaults
                        st.success("New Business form submitted successfully.")
                        time.sleep(5)
                        st.rerun()
                    except Exception as db_exc:
                        st.error(f"Failed to insert policy: {db_exc}")
            if back:
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()


        elif st.session_state.form_to_show == "policy_renewal_form":
            defaults = st.session_state.get("form_defaults", {})
            form_data, submit_renewal, back_renewal = policy_renewal_form(defaults)

            if submit_renewal:
                # Collect changed fields as per your logic
                edit_fields = {}
                original_policy = st.session_state.renewal_policy_data

                for key, new_value in form_data.items():
                    if key in original_policy:
                        original_value = original_policy[key]
                        # Handle date fields
                        if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                            if hasattr(original_value, 'date'):
                                original_date = original_value.date()
                            elif isinstance(original_value, str):
                                try:
                                    if ' ' in original_value:
                                        original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
                                    else:
                                        original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
                                except:
                                    original_date = original_value
                            else:
                                original_date = original_value
                            if new_value != original_date:
                                edit_fields[key] = new_value
                        else:
                            if str(new_value) != str(original_value):
                                edit_fields[key] = new_value

                # Always update the dates
                edit_fields["POL_ISSUE_DATE"] = form_data["POL_ISSUE_DATE"]
                edit_fields["POL_EFF_DATE"] = form_data["POL_EFF_DATE"]
                edit_fields["POL_EXPIRY_DATE"] = form_data["POL_EXPIRY_DATE"]

                if edit_fields:
                    try:
                        update_policy(original_policy["POLICY_NO"], edit_fields)
                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "renewal_policy_fetched", 
                            "renewal_policy_data",
                            "renewal_updated_data", 
                            "renewal_changes"
                        ]

                        for key in keys_to_delete:
                            if key in st.session_state:
                                del st.session_state[key]
                    
                        st.success("Renewal updated successfully.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Renewal update failed: {e}")
                else:
                    st.info("No fields were modified.")

            if back_renewal:
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()
        
        elif st.session_state.form_to_show == "policy_mta_form":
            # st.markdown("### MID-TERM ADJUSTMENT FORM")
            defaults = st.session_state.get("form_defaults", {})
            form_data, submit_mta, back_mta = policy_mta_form(defaults)
            
            if submit_mta:
                # Collect changed fields as per your logic
                edit_fields = {}
                original_policy = st.session_state.mta_policy_data

                for key, new_value in form_data.items():
                    if key in original_policy:
                        original_value = original_policy[key]
                        # Handle date fields
                        if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                            if hasattr(original_value, 'date'):
                                original_date = original_value.date()
                            elif isinstance(original_value, str):
                                try:
                                    if ' ' in original_value:
                                        original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
                                    else:
                                        original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
                                except:
                                    original_date = original_value
                            else:
                                original_date = original_value
                            if new_value != original_date:
                                edit_fields[key] = new_value
                        else:
                            if str(new_value) != str(original_value):
                                edit_fields[key] = new_value



                if edit_fields:
                    try:
                        update_policy(original_policy["POLICY_NO"], edit_fields)
                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "mta_policy_fetched", 
                            "mta_policy_data"
                        ]

                        for key in keys_to_delete:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.success("MTA updated successfully.")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"MTA update failed: {e}")
                else:
                    st.info("No fields were modified.")

            if back_mta:
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                if "mta_policy_fetched" in st.session_state:
                    del st.session_state.mta_policy_fetched
                if "mta_policy_data" in st.session_state:
                    del st.session_state.mta_policy_data
                st.rerun()

            if st.session_state.form_to_show == "claim_manual_form":
                show_claims_form(defaults)
        
        elif st.session_state.form_to_show == "policy_cancel_form":
            st.markdown("### POLICY CANCELLATION FORM")
            defaults = st.session_state.get("form_defaults", {})
            
            # Display the cancellation form with combined defaults
            form_data, submit_cancel, back_cancel = policy_cancel_form(defaults)

            if submit_cancel:
                # Validate cancellation form data
                if not form_data.get("confirm_cancel", False):
                    st.warning("Please confirm cancellation by checking the box before submitting.")
                else:
                    original_policy = st.session_state.cancel_policy_data
                    new_premium = form_data["PREMIUM2"]
                    original_premium = original_policy.get("PREMIUM2", 0)
                    cancel_date = form_data["CANCELLATION_DATE"]
                    
                    # Validate return premium doesn't exceed original premium
                    if float(new_premium) > float(original_premium):
                        st.error("Return Premium cannot exceed the original premium.")
                    else:
                        try:
                            # Process the cancellation
                            negative_premium = -abs(float(new_premium) if new_premium is not None else 0)
                            update_policy(
                                original_policy["POLICY_NO"],
                                {
                                    "isCancelled": 1,
                                    "PREMIUM2": int(negative_premium),
                                    "CANCELLATION_DATE": str(cancel_date),
                                    "TransactionType": "Policy Cancellation"
                                }
                            )
                            
                            # Clean up session state and return to main
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "cancel_policy_fetched", 
                                "cancel_policy_data",
                                "cancel_final_confirm"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success(f"Policy {original_policy['POLICY_NO']} cancelled successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cancellation failed: {e}")

            if back_cancel:
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                if "cancel_policy_fetched" in st.session_state:
                    del st.session_state.cancel_policy_fetched
                if "cancel_policy_data" in st.session_state:
                    del st.session_state.cancel_policy_data
                st.rerun()

        elif st.session_state.form_to_show == "claim_update_form":
            st.markdown("### CLAIM UPDATE FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_update_data
            
            with st.form("update_claim_form"):
                # Editable fields
                intimated_amount = st.number_input("Intimated Amount", 
                                                value=float(defaults.get("INTIMATED_AMOUNT", 0)), 
                                                min_value=0.0, format="%.2f")
                intimated_sf = st.number_input("Intimated SF", 
                                            value=float(defaults.get("INTIMATED_SF", 0)), 
                                            min_value=0.0, format="%.2f")
                claim_type = st.selectbox("Claim Type", ["OD", "TP"], 
                                        index=0 if defaults.get("TYPE", "OD") == "OD" else 1)
                status = st.selectbox("Status", 
                                    ["Under Review", "Approved", "Rejected", "Pending Documentation"],
                                    index=["Under Review", "Approved", "Rejected", "Pending Documentation"].index(
                                        defaults.get("CLAIM_STATUS", "Under Review")))
                remarks = st.text_area("Remarks", value=defaults.get("CLAIM_REMARKS", ""))

                # Non-editable fields for reference
                st.markdown("#### Claim Details (Read-only)")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Date of Accident", value=str(defaults.get("DATE_OF_ACCIDENT", "")), disabled=True)
                with col2:
                    st.text_input("Place of Loss", value=defaults.get("PLACE_OF_LOSS", ""), disabled=True)
                    st.text_input("Executive", value=defaults.get("EXECUTIVE", ""), disabled=True)
                    st.text_input("Vehicle", value=f"{defaults.get('MAKE', '')} {defaults.get('MODEL', '')}", disabled=True)

                submit_update = st.form_submit_button("Update Claim")
                back_update = st.form_submit_button("Back to Main Menu")

                if submit_update:
                    try:
                        update_data = {
                            "INTIMATED_AMOUNT": intimated_amount,
                            "INTIMATED_SF": intimated_sf,
                            "TYPE": claim_type,
                            "CLAIM_STATUS": status,
                            "CLAIM_REMARKS": remarks,
                            "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "CLAIM_STAGE": "Updated"
                        }
                        
                        update_claim(claim_data["CLAIM_NO"], update_data)
                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        
                        # Clean up session state variables
                        keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "claim_update_fetched", 
                            "claim_update_data"
                        ]

                        for key in keys_to_delete:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.success("Claim updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update claim: {e}")
                
                if back_update:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_update_fetched", 
                        "claim_update_data"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()

        elif st.session_state.form_to_show == "claim_close_form":
            st.markdown("### CLAIM CLOSURE FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_close_data
            
            with st.form("close_claim_form"):
                # Closure fields
                final_settlement = st.number_input("Final Settlement Amount *", 
                                                value=float(defaults.get("FINAL_SETTLEMENT_AMOUNT", 0)), 
                                                min_value=0.0, format="%.2f")
                closure_date = st.date_input("Closure Date *", value=datetime.strptime(defaults.get("CLAIM_CLOSURE_DATE", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date())
                closure_remarks = st.text_area("Closure Remarks *", value=defaults.get("CLAIM_REMARKS", ""))

                # Display claim summary
                st.markdown("#### Claim Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Intimated Amount", value=str(defaults.get("INTIMATED_AMOUNT", "")), disabled=True)
                with col2:
                    st.text_input("Current Status", value=defaults.get("CLAIM_STATUS", ""), disabled=True)
                    st.text_input("Claim Type", value=defaults.get("TYPE", ""), disabled=True)
                    st.text_input("Date of Accident", value=str(defaults.get("DATE_OF_ACCIDENT", "")), disabled=True)

                confirm_closure = st.checkbox("I confirm I want to close this claim")
                submit_close = st.form_submit_button("Close Claim")
                back_close = st.form_submit_button("Back to Main Menu")

                if submit_close:
                    if not confirm_closure:
                        st.error("Please confirm claim closure by checking the box.")
                    elif not closure_remarks.strip():
                        st.error("Please provide closure remarks.")
                    else:
                        try:
                            closure_data = {
                                "FINAL_SETTLEMENT_AMOUNT": float(final_settlement),
                                "CLAIM_CLOSURE_DATE": closure_date,
                                "CLAIM_STATUS": "Closed",
                                "CLAIM_REMARKS": closure_remarks,
                                "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "CLAIM_STAGE": "Closed"
                            }
                            
                            update_claim(claim_data["CLAIM_NO"], closure_data)
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            
                            # Clean up session state variables
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "claim_close_fetched", 
                                "claim_close_data"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success(f"Claim {claim_data['CLAIM_NO']} closed successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to close claim: {e}")
                
                if back_close:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_close_fetched", 
                        "claim_close_data"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()

        elif st.session_state.form_to_show == "claim_reopen_form":
            st.markdown("### CLAIM REOPEN FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_reopen_data
            
            with st.form("reopen_claim_form"):
                # Reopen fields
                reason_for_reopen = st.text_area("Reason for Reopening *", 
                                                value=defaults.get("REOPEN_REASON", ""))
                reopen_date = st.date_input("Reopen Date", value=datetime.now())
                new_status = st.selectbox("New Status", 
                                        ["Under Review", "Pending Documentation", "Investigation"],
                                        index=["Under Review", "Pending Documentation", "Investigation"].index(
                                            defaults.get("CLAIM_STATUS", "Under Review")))

                # Display claim summary
                st.markdown("#### Closed Claim Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Final Settlement", value=str(defaults.get("FINAL_SETTLEMENT_AMOUNT", "")), disabled=True)
                with col2:
                    st.text_input("Closure Date", value=str(defaults.get("CLAIM_CLOSURE_DATE", "")), disabled=True)
                    st.text_input("Claim Type", value=defaults.get("TYPE", ""), disabled=True)
                    st.text_input("Executive", value=defaults.get("EXECUTIVE", ""), disabled=True)

                confirm_reopen = st.checkbox("I confirm I want to reopen this claim")
                submit_reopen = st.form_submit_button("Reopen Claim")
                back_reopen = st.form_submit_button("Back to Main Menu")

                if submit_reopen:
                    if not confirm_reopen:
                        st.error("Please confirm claim reopening by checking the box.")
                    elif not reason_for_reopen.strip():
                        st.error("Please provide reason for reopening.")
                    else:
                        try:
                            reopen_data = {
                                "CLAIM_STATUS": new_status,
                                "CLAIM_STAGE": "Reopened",
                                "REOPEN_REASON": reason_for_reopen,
                                "CLAIM_REMARKS": defaults.get("CLAIM_REMARKS", ""),  # Already formatted with date and reason
                                "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            update_claim(claim_data["CLAIM_NO"], reopen_data)
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            
                            # Clean up session state variables
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "claim_reopen_fetched", 
                                "claim_reopen_data"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success(f"Claim {claim_data['CLAIM_NO']} reopened successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reopen claim: {e}")
                
                if back_reopen:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_reopen_fetched", 
                        "claim_reopen_data"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()

def show_claims_form(defaults):
    st.markdown("### NEW CLAIM FORM")
    # Generate claim_no if not present
    if "claim_no" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.claim_no = f"CLM{timestamp}"

    with st.form("new_claim_form"):
        col1, col2 = st.columns(2)
        with col1:
            policy_no = st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), key="claim_policy_no")
            date_of_accident = st.date_input("Date of Accident", value=defaults.get("DATE_OF_ACCIDENT", date.today()), key="claim_acc_date")
            date_of_intimation = st.date_input("Date of Intimation", value=defaults.get("DATE_OF_INTIMATION", date.today()), key="claim_int_date")
            place_of_loss = st.text_input("Place of Loss", value=defaults.get("PLACE_OF_LOSS", ""), key="claim_place_loss")
            claim_type = st.selectbox("Claim Type *", ["OD", "TP"], index=0 if defaults.get("CLAIM_TYPE", "OD") == "OD" else 1, key="claim_type")
            intimated_amount = st.number_input("Intimated Amount", value=defaults.get("INTIMATED_AMOUNT", 0.0), key="claim_int_amount")

        with col2:
            executive = st.text_input("Executive *", value=defaults.get("EXECUTIVE", ""), key="claim_executive")
            nationality = st.text_input("Nationality", value=defaults.get("NATIONALITY", ""), key="claim_nationality")
            claim_no = st.text_input("Claim No", value=st.session_state.claim_no, disabled=True, key="claim_no")
            intimated_sf = st.number_input("Intimated SF", value=defaults.get("INTIMATED_SF", 0.0), key="claim_intimated_sf")
            account_code_value = st.text_input("Account Code", value=defaults.get("ACCOUNT_CODE", ""), key="claim_account_code")

        submit = st.form_submit_button("Submit New Claim")
        back = st.form_submit_button("Back to Main Menu", type="secondary")

        if submit:
            if not all([policy_no.strip(), place_of_loss.strip(), executive.strip()]):
                st.error("Please fill all mandatory fields marked with *")
            else:
                try:
                    query = f"SELECT * FROM dbo.Policy WHERE POLICY_NO = '{policy_no}'"
                    policy_result = fetch_data(query)
                    if policy_result:
                        policy_data = policy_result[0]
                        drv_dob = policy_data.get("DRV_DOB", None)
                        if drv_dob:
                            if isinstance(drv_dob, str):
                                try:
                                    drv_dob = datetime.strptime(drv_dob, "%Y-%m-%d").date()
                                except Exception:
                                    drv_dob = None
                        if drv_dob:
                            today = date.today()
                            age = today.year - drv_dob.year - ((today.month, today.day) < (drv_dob.month, drv_dob.day))
                        else:
                            age = ""
                        if policy_data.get("isCancelled", 0) == 1:
                            st.error("Cannot create claim for cancelled policy")
                        elif policy_data.get("isLapsed", 0) == 1:
                            st.error("Cannot create claim for lapsed policy")
                        else:
                            claim_data = {
                                "Account_Code": account_code_value,
                                "DATE_OF_INTIMATION": date_of_intimation,
                                "DATE_OF_ACCIDENT": date_of_accident,
                                "PLACE_OF_LOSS": place_of_loss,
                                "CLAIM_NO": claim_no,
                                "AGE": age,
                                "TYPE": claim_type,
                                "DRIVING_LICENSE_ISSUE": policy_data.get("DRV_DLI", ""),
                                "BODY_TYPE": policy_data.get("BODY", ""),
                                "MAKE": policy_data.get("MAKE", ""),
                                "MODEL": policy_data.get("MODEL", ""),
                                "YEAR": policy_data.get("MODEL_YEAR", ""),
                                "CHASIS_NO": policy_data.get("CHASSIS_NO", ""),
                                "REG": policy_data.get("REGN", ""),
                                "SUM_INSURED": policy_data.get("SUM_INSURED", ""),
                                "POLICY_NO": policy_no,
                                "POLICY_START": policy_data.get("POL_EFF_DATE", ""),
                                "POLICY_END": policy_data.get("POL_EXPIRY_DATE", ""),
                                "INTIMATED_AMOUNT": intimated_amount,
                                "INTIMATED_SF": intimated_sf,
                                "EXECUTIVE": executive,
                                "PRODUCT": policy_data.get("PRODUCT", ""),
                                "POLICYTYPE": policy_data.get("POLICYTYPE", ""),
                                "NATIONALITY": nationality,
                                "Broker_ID": policy_data.get("Broker_ID", ""),
                                "Broker_Name": policy_data.get("Broker_Name", ""),
                                "Facility_ID": policy_data.get("Facility_ID", ""),
                                "Facility_Name": policy_data.get("Facility_Name", ""),
                                "CLAIM_STAGE": "New Claim",
                                "CLAIM_STATUS": "New Claim",
                                "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            }
                            try:
                                insert_claim(claim_data)
                                st.session_state.claims_edit_page = "main"
                                st.session_state.submission_mode = None
                                if "claim_no" in st.session_state:
                                    del st.session_state.claim_no
                                if "form_to_show" in st.session_state:
                                    del st.session_state.form_to_show
                                if "form_defaults" in st.session_state:
                                    del st.session_state.form_defaults
                                st.success(f"Claim {claim_no} created successfully!")
                                time.sleep(5)
                                st.rerun()
                            except Exception as db_exc:
                                st.error(f"Failed to insert claim: {db_exc}")
                    else:
                        st.error("Policy not found. Please check the policy number.")
                except Exception as e:
                    st.error(f"Error fetching policy data: {e}")

        if back:
            st.session_state.claims_edit_page = "main"
            st.session_state.submission_mode = None
            if "claim_no" in st.session_state:
                del st.session_state.claim_no
            if "form_to_show" in st.session_state:
                del st.session_state.form_to_show
            if "form_defaults" in st.session_state:
                del st.session_state.form_defaults
            st.rerun()
