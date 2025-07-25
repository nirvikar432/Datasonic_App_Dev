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
    policy_summary_display,
    policy_renewal_form,
)


from db_utils import insert_policy, update_policy, fetch_data, insert_claim, update_claim


# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fetch json data from json.json file
def fetch_json_data():
    """Fetch JSON data from a file"""
    try:
        #For testing purposes, we can load a sample JSON file
        json_files = [
            "streamlit-app/utils/json/NBpolicy.json",
            "streamlit-app/utils/json/NBclaim.json",
        ]
        # with open("streamlit-app/utils/json/NBclaim.json", "r") as f:
        selected_file = random.choice(json_files)
        with open(selected_file, "r") as f:
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
        if policy_type == "New Business":
            st.session_state.form_to_show = "policy_manual_form"
            st.session_state.form_defaults = data
            return True
        if policy_type == "New Claim":
            st.session_state.form_to_show = "claim_manual_form"
            st.session_state.form_defaults = data
            return True
        # elif policy_type == "Renewal":
        #     st.session_state.form_to_show = "policy_renewal_form"
        #     st.session_state.form_defaults = data
        #     return True
        # elif policy_type == "MTA":
        #     st.session_state.form_to_show = "policy_mta_form"
        #     st.session_state.form_defaults = data
        #     return True
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
                        # st.session_state.policy_data = form_data
                        # st.session_state.show_policy_summary = True
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

        if st.session_state.form_to_show == "claim_manual_form":
            show_claims_form(defaults)

        

        # For the ploicy renewal form
        # elif st.session_state.form_to_show == "policy_renewal_form":
        #     policy_no = defaults.get("POLICY_NO", "")
        #     query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
        #     result = fetch_data(query)
        #     if result:
        #         st.session_state.renewal_policy_data = result[0]
        #         st.session_state.renewal_policy_fetched = True
        #         st.rerun()
        #     # Merge DB data with JSON defaults
        #     policy_data = st.session_state.get("renewal_policy_data", {})
        #     json_defaults = st.session_state.get("form_defaults", {})
        #     merged_defaults = policy_data.copy()
        #     for k, v in json_defaults.items():
        #         if v not in [None, ""]:
        #             merged_defaults[k] = v
        #         # Convert date strings to date objects if needed for the form
        #     date_fields = ["DRV_DOB", "DRV_DLI", "POL_ISSUE_DATE", "POL_EFF_DATE", "POL_EXPIRY_DATE"]
        #     for field in date_fields:
        #         if field in merged_defaults and isinstance(merged_defaults[field], str):
        #             try:
        #                 merged_defaults[field] = datetime.strptime(merged_defaults[field], "%Y-%m-%d").date()
        #             except:
        #                 merged_defaults[field] = date(2000, 1, 1) if field in ["DRV_DOB", "DRV_DLI"] else date.today()

        #         # Use the merged defaults for the form
        #     st.markdown("### POLICY RENEWAL FORM")
        #     st.write("DB policy_data:", policy_data)
        #     st.write("Merged defaults for form:", merged_defaults)
        #     form_data, submit_renewal, back_renewal = policy_renewal_form(merged_defaults)
                
        #     if submit_renewal:
        #         # Collect changed fields
        #         edit_fields = {}
        #         original_policy = st.session_state.renewal_policy_data
                
        #         for key, new_value in form_data.items():
        #             if key in original_policy:
        #                 original_value = original_policy[key]
                        
        #                 # Special handling for date fields
        #                 if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
        #                     # Convert original value to date for comparison
        #                     if hasattr(original_value, 'date'):
        #                         original_date = original_value.date()
        #                     elif isinstance(original_value, str):
        #                         try:
        #                             if ' ' in original_value:
        #                                 original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
        #                             else:
        #                                 original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
        #                         except:
        #                             original_date = original_value
        #                     else:
        #                         original_date = original_value
                            
        #                     # Compare dates only
        #                     if new_value != original_date:
        #                         edit_fields[key] = new_value
        #                 else:
        #                     # Regular comparison for non-date fields
        #                     if str(new_value) != str(original_value):
        #                         edit_fields[key] = new_value
                    
        #             # Always update TransactionType for Renewal
        #         edit_fields["TransactionType"] = "Renewal"
                    
        #         # For renewal, always update the dates even if they appear the same
        #         # Force update POL_ISSUE_DATE to current date
        #         edit_fields["POL_ISSUE_DATE"] = form_data["POL_ISSUE_DATE"]
        #         edit_fields["POL_EFF_DATE"] = form_data["POL_EFF_DATE"]
        #         edit_fields["POL_EXPIRY_DATE"] = form_data["POL_EXPIRY_DATE"]
                    
        #         if edit_fields:
        #             try:
        #                 update_policy(original_policy["POLICY_NO"], edit_fields)
        #                 # Store the updated data and changes for summary
        #                 st.session_state.renewal_updated_data = {**original_policy, **edit_fields}
        #                 st.session_state.renewal_changes = edit_fields
        #                 st.session_state.show_renewal_summary = True
        #                 st.success("Renewal updated successfully.")
        #                 time.sleep(2)
        #                 st.rerun()
        #             except Exception as e:
        #                 st.error(f"Renewal update failed: {e}")
        #         else:
        #             st.info("No fields were modified.")

        #     if back_renewal:
        #         st.session_state.renewal_policy_fetched = False
        #         st.session_state.renewal_policy_data = None
        #         st.session_state.show_renewal_summary = False
        #         st.rerun()
        
        # elif st.session_state.form_to_show == "policy_mta_form":
        #     st.markdown("### POLICY MTA FORM")
        #     # Implement MTA form logic here
        #     # form_data, submit_mta, back_mta = policy_mta_form(defaults)
        #     # Handle submission and back actions similarly to the renewal form


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
