import streamlit as st
from fpdf import FPDF
import io
from policy_forms import (
    policy_manual_form,
    policy_summary_display,
    policy_cancel_form,
    policy_mta_form,
    mta_summary_display,
    policy_renewal_form,
    renewal_summary_display
)
# from prebind_forms import (
#     prebind_quotation_form, 
#     quotation_summary_display, 
#     quotation_action_buttons, 
#     quotation_history_display,
#     convert_quotation_to_policy_data
# )
from db_utils import insert_policy, update_policy, fetch_data, insert_claim, update_claim
import time
from datetime import datetime, date


# def policy_edit_tab():
#     st.header("Policy Edit")
#     if "policy_edit_page" not in st.session_state:
#         st.session_state.policy_edit_page = "main"

#     if st.session_state.policy_edit_page == "main":
#         transaction_type = st.selectbox("Select Transaction Type", ["Pre-Bind", "New Business", "MTA", "Renewal", "Policy Cancellation"])
#         if st.button("Proceed", key="policy_proceed_btn"):
#             st.session_state.transaction_type = transaction_type
#             st.session_state.policy_edit_page = "transaction_form"
#             st.rerun()

def policy_edit_tab():
    st.header("Policy Edit")
    if "policy_edit_page" not in st.session_state:
        st.session_state.policy_edit_page = "main"
    if "policy_entry_mode" not in st.session_state:
        st.session_state.policy_entry_mode = None

    if st.session_state.policy_edit_page == "main":
        st.markdown("#### Select Method of Policy Entry")
        st.markdown("<div style='margin-top: 50px'></div>", unsafe_allow_html=True)
        _,_, col1,_,_,_,_ ,col2,_,_,_ = st.columns(11)
        

        with col1:
            manual_btn = st.button("Manual", key="manual_entry_btn",type="primary", use_container_width=True)
        with col2:
            upload_btn = st.button("Upload", key="upload_btn", type="primary", use_container_width=True)

        if manual_btn:
            st.session_state.policy_entry_mode = "manual"
            st.rerun()
        elif upload_btn:
            st.session_state.policy_entry_mode = "upload"
            st.rerun()

        # Show transaction type selection only if manual selected
        if st.session_state.policy_entry_mode == "manual":
            transaction_type = st.selectbox(
                "Select Transaction Type",
                ["New Business", "MTA", "Renewal", "Policy Cancellation"], width=500, 
            )
            if st.button("Proceed", key="policy_proceed_btn"):
                st.session_state.transaction_type = transaction_type
                st.session_state.policy_edit_page = "transaction_form"
                st.session_state.policy_entry_mode = None
                st.rerun()
        elif st.session_state.policy_entry_mode in ["upload"]:
            st.info("Feature coming soon!")

    elif st.session_state.policy_edit_page == "transaction_form":
        ttype = st.session_state.transaction_type
        st.markdown(f"### {ttype} Form")


        if ttype == "New Business":
            if "show_policy_summary" not in st.session_state:
                st.session_state.show_policy_summary = False
            
            if not st.session_state.show_policy_summary:
                form_data, submit, back = policy_manual_form()


                if submit:
                    if not form_data["POLICY_NO"].strip():
                        st.error("Fill all the mandatory fields.")
                    else:
                        form_data["TransactionType"] = "New Business"  # Set type
                        try:
                            insert_policy(form_data)
                            st.success("New Business form submitted successfully.")
                            # Store the policy data and show summary
                            st.session_state.policy_data = form_data
                            st.session_state.show_policy_summary = True
                            st.rerun()
                        except Exception as db_exc:
                            st.error(f"Failed to insert policy: {db_exc}")
                if back:
                    st.session_state.policy_edit_page = "main"
                    st.rerun()
            else:
                # Show the policy summary
                policy_data = st.session_state.policy_data
                
                # Display policy summary
                policy_summary_display(policy_data)

                if st.button("Main menu", key="back_to_main_from_summary"):
                    st.session_state.policy_edit_page = "main"
                    st.session_state.show_policy_summary = False
                    if "policy_data" in st.session_state:
                        del st.session_state.policy_data
                    st.rerun()

        # elif ttype == "Pre-Bind":
        #     if "prebind_step" not in st.session_state:
        #         st.session_state.prebind_step = "quotation_form"
            
        #     if st.session_state.prebind_step == "quotation_form":
        #         st.markdown("#### Pre-Bind Quotation Form")
                
        #         # Use the prebind quotation form
        #         form_data, submit, back, missing_fields = prebind_quotation_form()
                
        #         if submit:
        #             if missing_fields:
        #                 st.error(f"Please fill all mandatory fields: {', '.join(missing_fields)}")
        #             else:
        #                 try:
        #                     # Insert quotation into database
        #                     insert_quotation(form_data)
        #                     st.session_state.quotation_data = form_data
        #                     st.session_state.prebind_step = "quotation_summary"
        #                     st.success("Quotation generated successfully!")
        #                     st.rerun()
        #                 except Exception as e:
        #                     st.error(f"Failed to generate quotation: {e}")
                
        #         if back:
        #             st.session_state.policy_edit_page = "main"
        #             st.session_state.prebind_step = "quotation_form"
        #             if "temp_policy_id" in st.session_state:
        #                 del st.session_state.temp_policy_id
        #             st.rerun()
            
        #     elif st.session_state.prebind_step == "quotation_summary":
        #         quotation_data = st.session_state.quotation_data
                
        #         # Display quotation summary
        #         quotation_summary_display(quotation_data)
                
        #         # Action buttons
        #         download_pdf, send_quote, convert_policy, back_to_form = quotation_action_buttons()
                
        #         if download_pdf:
        #             # Generate PDF
        #             pdf = FPDF()
        #             pdf.add_page()
        #             pdf.set_font("Arial", size=12)
        #             pdf.cell(200, 10, txt="Quotation Summary", ln=True, align="C")
        #             pdf.ln(10)
        #             for key, value in quotation_data.items():
        #                 pdf.cell(0, 10, f"{key}: {value}", ln=True)
        #             # Output PDF to bytes
        #             pdf_bytes = pdf.output(dest='S').encode('latin1')
        #             st.download_button(
        #                 label="Download Quotation PDF",
        #                 data=pdf_bytes,
        #                 file_name=f"Quotation_{quotation_data.get('POLICY_NO', 'quotation')}.pdf",
        #                 mime="application/pdf"
        #             )
                
        #         if send_quote:
        #             # Update status to "Sent"
        #             st.session_state.quotation_data['STATUS'] = "Sent"
        #             st.success("Quote status updated to 'Sent'")
        #             st.rerun()
                
        #         if convert_policy:
        #             # Navigate to policy conversion
        #             st.session_state.prebind_step = "convert_policy"
        #             st.rerun()
                
        #         if back_to_form:
        #             st.session_state.prebind_step = "quotation_form"
        #             st.rerun()
                
        #         # Display quotation history
        #         quotation_history_display(quotation_data.get("CUST_ID", ""))
                
        #         if st.button("Back to Main", key="back_to_main"):
        #             st.session_state.policy_edit_page = "main"
        #             st.session_state.prebind_step = "quotation_form"
        #             if "temp_policy_id" in st.session_state:
        #                 del st.session_state.temp_policy_id
        #             if "quotation_data" in st.session_state:
        #                 del st.session_state.quotation_data
        #             st.rerun()
            
        #     elif st.session_state.prebind_step == "convert_policy":
        #         st.markdown("#### Convert Quotation to Policy")
        #         quotation_data = st.session_state.quotation_data
                
        #         # Convert quotation data to policy form defaults
        #         policy_defaults = convert_quotation_to_policy_data(quotation_data)
                
        #         # Use policy manual form with pre-filled data
        #         form_data, submit, back = policy_manual_form(defaults=policy_defaults)
                
        #         if submit:
        #             if not form_data["POLICY_NO"].strip():
        #                 st.error("Please enter a Policy Number.")
        #             else:
        #                 form_data["TransactionType"] = "New Business"
        #                 try:
        #                     insert_policy(form_data)
        #                     # Mark quotation as converted
        #                     mark_quotation_converted(quotation_data["TEMP_POLICY_ID"], form_data["POLICY_NO"])
        #                     st.success(f"Policy {form_data['POLICY_NO']} created successfully from quotation!")
        #                     time.sleep(5)
                            
        #                     # Clean up session state
        #                     st.session_state.policy_edit_page = "main"
        #                     st.session_state.prebind_step = "quotation_form"
        #                     if "temp_policy_id" in st.session_state:
        #                         del st.session_state.temp_policy_id
        #                     if "quotation_data" in st.session_state:
        #                         del st.session_state.quotation_data
        #                     st.rerun()
        #                 except Exception as e:
        #                     st.error(f"Failed to create policy: {e}")
                
        #         if back:
        #             st.session_state.prebind_step = "quotation_summary"
        #             st.rerun()

        ######
        
        elif ttype == "Policy Cancellation":
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
                                    st.rerun()
                            else:
                                st.warning("No policy found with that number.")
                                
                    if back_btn:
                        st.session_state.policy_edit_page = "main"
                        st.session_state.cancel_policy_fetched = False
                        st.session_state.cancel_policy_data = None
                        st.session_state.cancel_final_confirm = False
                        st.rerun()
            else:
                # Convert date strings to date objects if needed for the form
                policy_data = st.session_state.cancel_policy_data.copy()
                
                # Handle date conversions
                date_fields = ["DRV_DOB", "DRV_DLI", "POL_ISSUE_DATE", "POL_EFF_DATE", "POL_EXPIRY_DATE"]
                for field in date_fields:
                    if field in policy_data and isinstance(policy_data[field], str):
                        try:
                            policy_data[field] = datetime.strptime(policy_data[field], "%Y-%m-%d").date()
                        except:
                            policy_data[field] = date(2000, 1, 1) if field in ["DRV_DOB", "DRV_DLI"] else date.today()
                
                # Use the policy_cancel_form with pre-filled data
                form_data, submit_cancel, back_cancel = policy_cancel_form(defaults=policy_data)
                
                if submit_cancel:
                    # Keep the existing validation and calculation logic
                    new_premium = form_data["PREMIUM2"]
                    cancel_date = form_data["CANCELLATION_DATE"]
                    confirm_cancel = form_data.get("confirm_cancel", False)
                    original_premium = st.session_state.cancel_policy_data.get("PREMIUM2", 0)
                    
                    if not confirm_cancel:
                        st.warning("Please confirm cancellation by checking the box before submitting.")
                    # Validate return premium does not exceed original premium
                    elif float(new_premium) > float(original_premium):
                        st.error("Return Premium cannot exceed the original premium.")
                    # Double confirm before DB update
                    elif not st.session_state.get("cancel_final_confirm", False):
                        st.session_state.cancel_final_confirm = True
                        st.warning("This action will permanently cancel the policy. Click 'Submit Cancellation' again to proceed.")
                    else:
                        try:
                            # Keep the existing calculation logic
                            negative_premium = -abs(float(new_premium) if new_premium is not None else 0)
                            update_policy(
                                st.session_state.cancel_policy_data["POLICY_NO"],
                                {
                                    "isCancelled": 1,
                                    "PREMIUM2": int(negative_premium),
                                    "CANCELLATION_DATE": str(cancel_date),
                                    "TransactionType": "Policy Cancellation"
                                }
                            )
                            st.success(f"Policy {st.session_state.cancel_policy_data['POLICY_NO']} cancelled successfully.")
                            time.sleep(3)
                            
                            # Reset session state
                            st.session_state.policy_edit_page = "main"
                            st.session_state.cancel_policy_fetched = False
                            st.session_state.cancel_policy_data = None
                            st.session_state.cancel_final_confirm = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cancellation failed: {e}")
                
                if back_cancel:
                    st.session_state.cancel_policy_fetched = False
                    st.session_state.cancel_policy_data = None
                    st.session_state.cancel_final_confirm = False
                    st.rerun()
        
        #######
        elif ttype == "MTA":
            if "mta_policy_fetched" not in st.session_state:
                st.session_state.mta_policy_fetched = False
                st.session_state.mta_policy_data = None
                st.session_state.show_mta_summary = False


            if not st.session_state.mta_policy_fetched:
                with st.form("mta_policy_fetch_form"):
                    policy_no = st.text_input("Enter Policy Number *", key="mta_policy_no")
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
                                    st.session_state.mta_policy_fetched = True
                                    st.session_state.mta_policy_data = result[0]
                                    st.session_state.show_mta_summary = False
                                    st.rerun()
                            else:
                                st.warning("No policy found with that number.")
                                
                    if back_btn:
                        st.session_state.policy_edit_page = "main"
                        st.session_state.mta_policy_fetched = False
                        st.session_state.mta_policy_data = None
                        st.session_state.show_mta_summary = False
                        st.rerun()

            elif not st.session_state.show_mta_summary:
                # Convert date strings to date objects if needed for the form
                policy_data = st.session_state.mta_policy_data.copy()
                
                # Handle date conversions
                date_fields = ["DRV_DOB", "DRV_DLI", "POL_ISSUE_DATE", "POL_EFF_DATE", "POL_EXPIRY_DATE"]
                for field in date_fields:
                    if field in policy_data:
                        if isinstance(policy_data[field], str):
                            try:
                                # Parse string to datetime, then extract date
                                policy_data[field] = datetime.strptime(policy_data[field], "%Y-%m-%d").date()
                            except:
                                try:
                                    # Try parsing with time component
                                    policy_data[field] = datetime.strptime(policy_data[field][:10], "%Y-%m-%d").date()
                                except:
                                    policy_data[field] = date(2000, 1, 1) if field in ["DRV_DOB", "DRV_DLI"] else date.today()
                        elif hasattr(policy_data[field], 'date'):
                            # Convert datetime object to date object
                            policy_data[field] = policy_data[field].date()
                
                # Use the policy_mta_form with pre-filled data
                form_data, submit_mta, back_mta = policy_mta_form(defaults=policy_data)
                
                if submit_mta:
                    # Collect changed fields with proper date comparison
                    edit_fields = {}
                    original_policy = st.session_state.mta_policy_data
                    
                    for key, new_value in form_data.items():
                        if key in original_policy:
                            original_value = original_policy[key]
                            
                            # Special handling for date fields
                            if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                                # Convert original value to date for comparison
                                if hasattr(original_value, 'date'):
                                    # If original is datetime, get date part
                                    original_date = original_value.date()
                                elif isinstance(original_value, str):
                                    # If original is string, parse to date
                                    try:
                                        # Handle both with and without time component
                                        if ' ' in original_value:
                                            original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
                                        else:
                                            original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
                                    except:
                                        original_date = original_value
                                else:
                                    original_date = original_value
                                
                                # Compare dates only
                                if new_value != original_date:
                                    edit_fields[key] = new_value
                            else:
                                # Regular comparison for non-date fields
                                if str(new_value) != str(original_value):
                                    edit_fields[key] = new_value
                    
                    # Always update TransactionType for MTA
                    edit_fields["TransactionType"] = "MTA"
                    
                    # Remove TransactionType from edit_fields if no other changes were made
                    if len(edit_fields) == 1 and "TransactionType" in edit_fields:
                        st.info("No fields were modified.")
                    else:
                        try:
                            update_policy(original_policy["POLICY_NO"], edit_fields)
                            # Store the updated data and changes for summary
                            st.session_state.mta_updated_data = {**original_policy, **edit_fields}
                            st.session_state.mta_changes = edit_fields
                            st.session_state.show_mta_summary = True
                            st.success("MTA updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"MTA update failed: {e}")

                if back_mta:
                    st.session_state.mta_policy_fetched = False
                    st.session_state.mta_policy_data = None
                    st.session_state.show_mta_summary = False
                    st.rerun()
            else:
                # Show MTA Summary
                updated_data = st.session_state.mta_updated_data
                changes_made = st.session_state.mta_changes
                
                # Display what was changed
                st.subheader("Changes Made")
                if changes_made:
                    changes_list = []
                    for field, new_value in changes_made.items():
                        if field != "TransactionType":
                            old_value = st.session_state.mta_policy_data.get(field, "")
                            changes_list.append(f"**{field}:** {old_value} → {new_value}")
                    
                    if changes_list:
                        for change in changes_list:
                            st.write(change)
                    st.markdown("---")
                
                # Display MTA summary using the imported function
                mta_summary_display(updated_data)
                
                # Action buttons
                _, col2, _ = st.columns([1, 1, 1])

                with col2:  # Use the middle column
                    back_to_main = st.button("Back to Main", use_container_width=True)
                
                
                if back_to_main:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.mta_policy_fetched = False
                    st.session_state.mta_policy_data = None
                    st.session_state.show_mta_summary = False
                    if "mta_updated_data" in st.session_state:
                        del st.session_state.mta_updated_data
                    if "mta_changes" in st.session_state:
                        del st.session_state.mta_changes
                    st.rerun()




        #############
        else:  # Renewal
            if "renewal_policy_fetched" not in st.session_state:
                st.session_state.renewal_policy_fetched = False
                st.session_state.renewal_policy_data = None
                st.session_state.show_renewal_summary = False

            if not st.session_state.renewal_policy_fetched:
                with st.form("renewal_policy_fetch_form"):
                    policy_no = st.text_input("Enter Policy Number *", key="renewal_policy_no")
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
                                    st.session_state.renewal_policy_fetched = True
                                    st.session_state.renewal_policy_data = result[0]
                                    st.session_state.show_renewal_summary = False
                                    st.rerun()
                            else:
                                st.warning("No policy found with that number.")
                                
                    if back_btn:
                        st.session_state.policy_edit_page = "main"
                        st.session_state.renewal_policy_fetched = False
                        st.session_state.renewal_policy_data = None
                        st.session_state.show_renewal_summary = False
                        st.rerun()
            
            elif not st.session_state.show_renewal_summary:
                # Convert date strings to date objects if needed for the form
                policy_data = st.session_state.renewal_policy_data.copy()
                
                # Handle date conversions
                date_fields = ["DRV_DOB", "DRV_DLI", "POL_ISSUE_DATE", "POL_EFF_DATE", "POL_EXPIRY_DATE"]
                for field in date_fields:
                    if field in policy_data and isinstance(policy_data[field], str):
                        try:
                            policy_data[field] = datetime.strptime(policy_data[field], "%Y-%m-%d").date()
                        except:
                            policy_data[field] = date(2000, 1, 1) if field in ["DRV_DOB", "DRV_DLI"] else date.today()
                
                # Use the policy_renewal_form with pre-filled data
                form_data, submit_renewal, back_renewal = policy_renewal_form(defaults=policy_data)
                
                if submit_renewal:
                    # Collect changed fields
                    edit_fields = {}
                    original_policy = st.session_state.renewal_policy_data
                    
                    for key, new_value in form_data.items():
                        if key in original_policy:
                            original_value = original_policy[key]
                            
                            # Special handling for date fields
                            if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                                # Convert original value to date for comparison
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
                                
                                # Compare dates only
                                if new_value != original_date:
                                    edit_fields[key] = new_value
                            else:
                                # Regular comparison for non-date fields
                                if str(new_value) != str(original_value):
                                    edit_fields[key] = new_value
                    
                    # Always update TransactionType for Renewal
                    edit_fields["TransactionType"] = "Renewal"
                    
                    # For renewal, always update the dates even if they appear the same
                    # Force update POL_ISSUE_DATE to current date
                    edit_fields["POL_ISSUE_DATE"] = form_data["POL_ISSUE_DATE"]
                    edit_fields["POL_EFF_DATE"] = form_data["POL_EFF_DATE"]
                    edit_fields["POL_EXPIRY_DATE"] = form_data["POL_EXPIRY_DATE"]
                    
                    if edit_fields:
                        try:
                            update_policy(original_policy["POLICY_NO"], edit_fields)
                            # Store the updated data and changes for summary
                            st.session_state.renewal_updated_data = {**original_policy, **edit_fields}
                            st.session_state.renewal_changes = edit_fields
                            st.session_state.show_renewal_summary = True
                            st.success("Renewal updated successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Renewal update failed: {e}")
                    else:
                        st.info("No fields were modified.")

                if back_renewal:
                    st.session_state.renewal_policy_fetched = False
                    st.session_state.renewal_policy_data = None
                    st.session_state.show_renewal_summary = False
                    st.rerun()
            
            else:
                # Show Renewal Summary
                updated_data = st.session_state.renewal_updated_data
                changes_made = st.session_state.renewal_changes
                
                # Display what was changed
                st.subheader("Changes Made")
                if changes_made:
                    changes_list = []
                    for field, new_value in changes_made.items():
                        if field != "TransactionType":
                            old_value = st.session_state.renewal_policy_data.get(field, "")
                            changes_list.append(f"**{field}:** {old_value} → {new_value}")
                    
                    if changes_list:
                        for change in changes_list:
                            st.write(change)
                    st.markdown("---")
                
                # Display Renewal summary using the imported function
                renewal_summary_display(updated_data)
                
                # Center the back button
                _, col, _ = st.columns([1, 1, 1])
                with col:
                    back_to_main = st.button("Back to Main", use_container_width=True)

                if back_to_main:
                    st.session_state.policy_edit_page = "main"
                    st.session_state.renewal_policy_fetched = False
                    st.session_state.renewal_policy_data = None
                    st.session_state.show_renewal_summary = False
                    if "renewal_updated_data" in st.session_state:
                        del st.session_state.renewal_updated_data
                    if "renewal_changes" in st.session_state:
                        del st.session_state.renewal_changes
                    st.rerun()

def claims_edit_tab():
    st.header("Claims Edit")
    
    if "claims_edit_page" not in st.session_state:
        st.session_state.claims_edit_page = "main"

    if st.session_state.claims_edit_page == "main":
        transaction_type = st.selectbox(
            "Select Claims Transaction Type", 
            ["New Claim", "Claim Update", "Claim Closure", "Claim Reopen"]
        )

        st.markdown("<div style='margin-top: 50px'></div>", unsafe_allow_html=True)

        if st.button("Proceed", key="claims_proceed_btn"):
            st.session_state.claims_transaction_type = transaction_type
            st.session_state.claims_edit_page = "transaction_form"
            st.rerun()

    elif st.session_state.claims_edit_page == "transaction_form":
        ttype = st.session_state.claims_transaction_type
        st.markdown(f"### {ttype} Form")

        if ttype == "New Claim":
            # Auto-generate Claim No if not provided
            if "claim_no" not in st.session_state:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                st.session_state.claim_no = f"CLM{timestamp}"

            with st.form("new_claim_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    policy_no = st.text_input("Policy No *", key="new_claim_policy_no")
                    date_of_accident = st.date_input("Date of Accident *", value=date.today())
                    date_of_intimation = st.date_input("Date of Intimation *", value=date.today())
                    place_of_loss = st.text_input("Place of Loss *")
                    claim_type = st.selectbox("Claim Type *", ["OD", "TP"])
                    intimated_amount = st.number_input("Intimated Amount *", min_value=0.0, format="%.2f")
                    
                                        
                
                with col2:
                    executive = st.text_input("Executive *")
                    nationality = st.text_input("Nationality", value="Indian")
                    claim_no = st.text_input("Claim No", value=st.session_state.claim_no, disabled=True)
                    intimated_sf = st.number_input("Intimated SF", min_value=0.0, format="%.2f")
                    account_code_value = st.text_input("Account Code", value="")  # Replace with actual value if needed

                # # Vehicle details section (auto-filled from Policy)
                # st.markdown("#### Vehicle Details (Auto-filled from Policy)")
                # vehicle_col1, vehicle_col2 = st.columns(2)
                
                # with vehicle_col1:
                #     make = st.text_input("Make", disabled=True, key="claim_make")
                #     model = st.text_input("Model", disabled=True, key="claim_model")
                #     chassis_no = st.text_input("Chassis No", disabled=True, key="claim_chassis")
                #     product = st.text_input("Product", disabled=True)

                
                # with vehicle_col2:
                #     regn = st.text_input("Registration No", disabled=True, key="claim_regn")
                #     model_year = st.text_input("Model Year", disabled=True, key="claim_year")
                #     sum_insured = st.text_input("Sum Insured", disabled=True, key="claim_sum_insured")
                submit = st.form_submit_button("Submit New Claim")
                back = st.form_submit_button("Back")

                if submit:
                    # Validate mandatory fields
                    if not all([policy_no.strip(), place_of_loss.strip(), executive.strip()]):
                        st.error("Please fill all mandatory fields marked with *")
                    else:
                        # Fetch policy details to auto-fill vehicle details
                        try:
                            query = f"SELECT * FROM dbo.Policy WHERE POLICY_NO = '{policy_no}'"
                            policy_result = fetch_data(query)
                            
                            if policy_result:
                                policy_data = policy_result[0]

                                # Calculate age from DRV_DOB
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
                                
                                # Check if policy is active
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
                                        "AGE": age,  # or ask user
                                        "TYPE": claim_type,
                                        "DRIVING_LICENSE_ISSUE": policy_data.get("DRV_DLI", ""),  # or ask user
                                        "BODY_TYPE": policy_data.get("BODY", ""),  # or ask user
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
                                        "CLAIM_STAGE": "New Claim",
                                        "CLAIM_STATUS": "New Claim",

                                    }
                                    
                                    # Insert claim into database
                                    insert_claim(claim_data)
                                    st.success(f"Claim {claim_no} created successfully!")
                                    time.sleep(5)
                                    
                                    # Reset session state
                                    st.session_state.claims_edit_page = "main"
                                    if "claim_no" in st.session_state:
                                        del st.session_state.claim_no
                                    st.rerun()
                            else:
                                st.error("Policy not found. Please check the policy number.")
                        except Exception as e:
                            st.error(f"Failed to create claim: {e}")
                
                if back:
                    st.session_state.claims_edit_page = "main"
                    if "claim_no" in st.session_state:
                        del st.session_state.claim_no
                    st.rerun()

        elif ttype == "Claim Update":
            if "claim_fetched" not in st.session_state:
                st.session_state.claim_fetched = False

            if not st.session_state.claim_fetched:
                with st.form("fetch_claim_form"):
                    claim_no = st.text_input("Enter Claim No *")
                    fetch = st.form_submit_button("Fetch Claim")
                    back = st.form_submit_button("Back")

                    if fetch and claim_no.strip():
                        query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                        result = fetch_data(query)
                        if result:
                            if result[0].get("STATUS", "").lower() == "closed":
                                st.warning(f"Claim {claim_no} is already closed.")
                            else:
                                st.session_state.claim_fetched = True
                                st.session_state.claim_data = result[0]
                        else:
                            st.error("No claim found with that number.")
                    elif fetch:
                        st.error("Please enter Claim Number to proceed.")
                    
                    if back:
                        st.session_state.claims_edit_page = "main"
                        st.session_state.claim_fetched = False
                        st.rerun()
            else:
                claim_data = st.session_state.claim_data
                st.markdown(f"#### Update Claim: {claim_data['CLAIM_NO']}")
                
                with st.form("update_claim_form"):
                    # Editable fields
                    intimated_amount = st.number_input("Intimated Amount", 
                                                     value=float(claim_data.get("INTIMATED_AMOUNT", 0)), 
                                                     min_value=0.0, format="%.2f")
                    intimated_sf = st.number_input("Intimated SF", 
                                                 value=float(claim_data.get("INTIMATED_SF", 0)), 
                                                 min_value=0.0, format="%.2f")
                    claim_type = st.selectbox("Claim Type", ["OD", "TP"], 
                                            index=0 if claim_data.get("CLAIM_TYPE") == "OD" else 1)
                    status = st.selectbox("Status", 
                                        ["Under Review", "Approved", "Rejected", "Pending Documentation"],
                                        index=["Under Review", "Approved", "Rejected", "Pending Documentation"].index(
                                            claim_data.get("STATUS", "Under Review")))
                    remarks = st.text_area("Remarks", value=claim_data.get("REMARKS", ""))

                    # Non-editable fields for reference
                    st.markdown("#### Claim Details (Read-only)")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Claim No", value=claim_data.get("CLAIM_NO", ""), disabled=True)
                        st.text_input("Policy No", value=claim_data.get("POLICY_NO", ""), disabled=True)
                        st.text_input("Date of Accident", value=str(claim_data.get("DATE_OF_ACCIDENT", "")), disabled=True)
                    with col2:
                        st.text_input("Place of Loss", value=claim_data.get("PLACE_OF_LOSS", ""), disabled=True)
                        st.text_input("Executive", value=claim_data.get("EXECUTIVE", ""), disabled=True)
                        st.text_input("Vehicle", value=f"{claim_data.get('MAKE', '')} {claim_data.get('MODEL', '')}", disabled=True)

                    submit = st.form_submit_button("Update Claim")
                    back = st.form_submit_button("Back")

                    if submit:
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
                            st.success("Claim updated successfully!")
                            time.sleep(5)
                            
                            st.session_state.claims_edit_page = "main"
                            st.session_state.claim_fetched = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update claim: {e}")
                    
                    if back:
                        st.session_state.claim_fetched = False
                        st.rerun()

        elif ttype == "Claim Closure":
            if "claim_closure_fetched" not in st.session_state:
                st.session_state.claim_closure_fetched = False

            if not st.session_state.claim_closure_fetched:
                with st.form("fetch_claim_closure_form"):
                    claim_no = st.text_input("Enter Claim No *")
                    fetch = st.form_submit_button("Fetch Claim")
                    back = st.form_submit_button("Back")

                    if fetch and claim_no.strip():
                        query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                        result = fetch_data(query)
                        if result:
                            if result[0].get("STATUS", "").lower() == "closed":
                                st.warning(f"Claim {claim_no} is already closed.")
                            else:
                                st.session_state.claim_closure_fetched = True
                                st.session_state.claim_closure_data = result[0]
                        else:
                            st.error("No claim found with that number.")
                    elif fetch:
                        st.error("Please enter Claim Number to proceed.")
                    
                    if back:
                        st.session_state.claims_edit_page = "main"
                        st.session_state.claim_closure_fetched = False
                        st.rerun()
            else:
                claim_data = st.session_state.claim_closure_data
                st.markdown(f"#### Close Claim: {claim_data['CLAIM_NO']}")
                
                with st.form("close_claim_form"):
                    # Closure fields
                    final_settlement = st.number_input("Final Settlement Amount *", 
                                                     min_value=0.0, format="%.2f")
                    closure_date = st.date_input("Closure Date *", value=date.today())
                    closure_remarks = st.text_area("Closure Remarks *")

                    # Display claim summary
                    st.markdown("#### Claim Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Claim No", value=claim_data.get("CLAIM_NO", ""), disabled=True)
                        st.text_input("Policy No", value=claim_data.get("POLICY_NO", ""), disabled=True)
                        st.text_input("Intimated Amount", value=str(claim_data.get("INTIMATED_AMOUNT", "")), disabled=True)
                    with col2:
                        st.text_input("Current Status", value=claim_data.get("STATUS", ""), disabled=True)
                        st.text_input("Claim Type", value=claim_data.get("CLAIM_TYPE", ""), disabled=True)
                        st.text_input("Date of Accident", value=str(claim_data.get("DATE_OF_ACCIDENT", "")), disabled=True)

                    confirm_closure = st.checkbox("I confirm I want to close this claim")
                    submit = st.form_submit_button("Close Claim")
                    back = st.form_submit_button("Back")

                    if submit:
                        if not confirm_closure:
                            st.error("Please confirm claim closure by checking the box.")
                        elif not closure_remarks.strip():
                            st.error("Please provide closure remarks.")
                        else:
                            try:
                                closure_data = {
                                    "FINAL_SETTLEMENT_AMOUNT": float(final_settlement),
                                    "CLAIMCLOSUREDATE": closure_date,
                                    "CLAIM_STATUS": "Closed",
                                    "CLAIM_REMARKS": f"{claim_data.get('REMARKS', '')}\n\nClosure Remarks: {closure_remarks}",
                                    "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "CLAIM_STAGE": "Closed"
                                }
                                
                                update_claim(claim_data["CLAIM_NO"], closure_data)
                                st.success(f"Claim {claim_data['CLAIM_NO']} closed successfully!")
                                time.sleep(5)
                                
                                st.session_state.claims_edit_page = "main"
                                st.session_state.claim_closure_fetched = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to close claim: {e}")
                    
                    if back:
                        st.session_state.claim_closure_fetched = False
                        st.rerun()

        elif ttype == "Claim Reopen":
            if "claim_reopen_fetched" not in st.session_state:
                st.session_state.claim_reopen_fetched = False

            if not st.session_state.claim_reopen_fetched:
                with st.form("fetch_claim_reopen_form"):
                    claim_no = st.text_input("Enter Claim No *")
                    fetch = st.form_submit_button("Fetch Claim")
                    back = st.form_submit_button("Back")

                    if fetch and claim_no.strip():
                        query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                        result = fetch_data(query)
                        if result:
                            if result[0].get("CLAIM_STATUS", "") != "Closed":
                                st.warning(f"Claim {claim_no} is not closed. Only closed claims can be reopened.")
                            else:
                                st.session_state.claim_reopen_fetched = True
                                st.session_state.claim_reopen_data = result[0]
                        else:
                            st.error("No claim found with that number.")
                    elif fetch:
                        st.error("Please enter Claim Number to proceed.")
                    
                    if back:
                        st.session_state.claims_edit_page = "main"
                        st.session_state.claim_reopen_fetched = False
                        st.rerun()
            else:
                claim_data = st.session_state.claim_reopen_data
                st.markdown(f"#### Reopen Claim: {claim_data['CLAIM_NO']}")
                
                with st.form("reopen_claim_form"):
                    # Reopen fields
                    reason_for_reopen = st.text_area("Reason for Reopening *")
                    reopen_date = st.date_input("Reopen Date *", value=date.today())
                    new_status = st.selectbox("New Status", 
                                            ["Under Review", "Pending Documentation", "Investigation"])

                    # Display claim summary
                    st.markdown("#### Closed Claim Summary")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Claim No", value=claim_data.get("CLAIM_NO", ""), disabled=True)
                        st.text_input("Policy No", value=claim_data.get("POLICY_NO", ""), disabled=True)
                        st.text_input("Final Settlement", value=str(claim_data.get("FINAL_SETTLEMENT_AMOUNT", "")), disabled=True)
                    with col2:
                        st.text_input("Closure Date", value=str(claim_data.get("CLAIMCLOSUREDATE", "")), disabled=True)
                        st.text_input("Claim Type", value=claim_data.get("TYPE", ""), disabled=True)
                        st.text_input("Executive", value=claim_data.get("EXECUTIVE", ""), disabled=True)

                    confirm_reopen = st.checkbox("I confirm I want to reopen this claim")
                    submit = st.form_submit_button("Reopen Claim")
                    back = st.form_submit_button("Back")

                    if submit:
                        if not confirm_reopen:
                            st.error("Please confirm claim reopening by checking the box.")
                        elif not reason_for_reopen.strip():
                            st.error("Please provide reason for reopening.")
                        else:
                            try:
                                reopen_data = {
                                    "CLAIM_STATUS": new_status,
                                    "REOPEN_DATE": reopen_date,
                                    "REOPEN_REASON": reason_for_reopen,
                                    "CLAIM_REMARKS": f"{claim_data.get('REMARKS', '')}\n\nReopened on {reopen_date}: {reason_for_reopen}",
                                    "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                update_claim(claim_data["CLAIM_NO"], reopen_data)
                                st.success(f"Claim {claim_data['CLAIM_NO']} reopened successfully!")
                                time.sleep(5)
                                
                                st.session_state.claims_edit_page = "main"
                                st.session_state.claim_reopen_fetched = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to reopen claim: {e}")
                    
                    if back:
                        st.session_state.claim_reopen_fetched = False
                        st.rerun()

