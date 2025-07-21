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