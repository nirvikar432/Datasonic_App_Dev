import streamlit as st
from datetime import date, timedelta
import time
import uuid

def prebind_quotation_form(defaults=None):
    """
    Pre-Bind quotation form for generating quotes before policy issuance
    """
    if defaults is None:
        defaults = {}
    
    # Auto-generate TEMP_POLICY_ID if not provided
    if "temp_policy_id" not in st.session_state:
        st.session_state.temp_policy_id = f"TEMP_{int(time.time())}"
    
    with st.form("prebind_quotation_form"):
        # Display auto-generated TEMP_POLICY_ID
        st.text_input("TEMP_POLICY_ID", value=st.session_state.temp_policy_id, disabled=True)
        
        # Customer Details Section
        st.subheader("Customer Details")
        col1, col2, col3 = st.columns(3)
        cust_id = col1.text_input("Customer ID *", value=defaults.get("CUST_ID", ""), help="Mandatory")
        cust_name = col2.text_input("Customer Name *", value=defaults.get("CUST_NAME", ""), help="Mandatory")
        cust_dob = col3.date_input("Customer DOB *", value=defaults.get("CUST_DOB", date(1990, 1, 1)), help="Mandatory")
        
        col4, col5, col6 = st.columns(3)
        cust_contact = col4.text_input("Contact Number *", value=defaults.get("CUST_CONTACT", ""), help="Mandatory")
        cust_email = col5.text_input("Email", value=defaults.get("CUST_EMAIL", ""), help="Optional")
        executive = col6.text_input("Executive *", value=defaults.get("EXECUTIVE", ""), help="Mandatory")
        
        # Vehicle Details Section
        st.subheader("Vehicle Details")
        col7, col8, col9 = st.columns(3)
        chassis_no = col7.text_input("Chassis Number *", value=defaults.get("CHASSIS_NO", ""), help="Mandatory")
        make = col8.text_input("Make *", value=defaults.get("MAKE", ""), help="Mandatory")
        model = col9.text_input("Model *", value=defaults.get("MODEL", ""), help="Mandatory")
        
        col10, col11, col12 = st.columns(3)
        model_year = col10.text_input("Model Year *", value=str(defaults.get("MODEL_YEAR", "")), help="Mandatory")
        regn = col11.text_input("Registration Number", value=defaults.get("REGN", ""), help="Optional")
        use_of_vehicle = col12.selectbox("Use of Vehicle *", 
                                       ["Private Car", "Commercial", "Taxi", "Goods Carrying"], 
                                       index=0 if defaults.get("USE_OF_VEHICLE", "") == "" else 
                                       ["Private Car", "Commercial", "Taxi", "Goods Carrying"].index(defaults.get("USE_OF_VEHICLE", "Private Car")),
                                       help="Mandatory")
        
        # Driver Details Section
        st.subheader("Driver Details")
        col13, col14, col15 = st.columns(3)
        drv_dob = col13.date_input("Driver DOB *", value=defaults.get("DRV_DOB", date(1990, 1, 1)), help="Mandatory")
        drv_dli = col14.date_input("Driver License Issue *", value=defaults.get("DRV_DLI", date(2010, 1, 1)), help="Mandatory")
        veh_seats = col15.text_input("Vehicle Seats *", value=str(defaults.get("VEH_SEATS", "5")), help="Mandatory")
        
        # Coverage and Premium Details Section
        st.subheader("Coverage & Premium")
        col16, col17, col18 = st.columns(3)
        coverage_type = col16.selectbox("Coverage Type *", 
                                      ["COMPREHENSIVE", "THIRD PARTY"], 
                                      index=0 if defaults.get("COVERAGE_TYPE", "") in ["", "COMPREHENSIVE"] else 1,
                                      help="Comprehensive: Includes coverage for your own damage + Others | Third Party: Covers damage caused to others only")
        sum_insured = col17.text_input("Sum Insured *", value=str(defaults.get("SUM_INSURED", "")), help="Mandatory")
        premium_estimate = col18.text_input("Premium Estimate *", value=str(defaults.get("PREMIUM_ESTIMATE", "")), help="Mandatory")
        
        col19, col20, col21 = st.columns(3)
        product_type = col19.text_input("Product Type *", value=defaults.get("PRODUCT_TYPE", ""), help="Mandatory")
        validity_period = col20.selectbox("Quotation Validity", 
                                        ["7 days", "15 days", "1 month"], 
                                        index=["7 days", "15 days", "1 month"].index(defaults.get("VALIDITY_PERIOD", "7 days")),
                                        help="Quote validity period")
        policy_type = col21.text_input("Policy Type", value=defaults.get("POLICY_TYPE", ""), help="Optional")
        
        # Calculate validity expiry date
        validity_days = {"7 days": 7, "15 days": 15, "1 month": 30}
        validity_expiry = date.today() + timedelta(days=validity_days[validity_period])
        st.date_input("Quote Expiry Date", value=validity_expiry, disabled=True)
        
        # Remarks Section
        remarks = st.text_area("Remarks/Notes", value=defaults.get("REMARKS", ""), help="Optional notes for underwriters or executives")
        
        # Form submission buttons
        submit = st.form_submit_button("Generate Quotation")
        back = st.form_submit_button("Back")
        
        # Validation for mandatory fields
        mandatory_fields = {
            "Customer ID": cust_id,
            "Customer Name": cust_name,
            "Contact Number": cust_contact,
            "Executive": executive,
            "Chassis Number": chassis_no,
            "Make": make,
            "Model": model,
            "Model Year": model_year,
            "Sum Insured": sum_insured,
            "Premium Estimate": premium_estimate,
            "Product Type": product_type
        }
        
        # Prepare form data
        form_data = {
            "TEMP_POLICY_ID": st.session_state.temp_policy_id,
            "CUST_ID": cust_id,
            "CUST_NAME": cust_name,
            "CUST_DOB": cust_dob,
            "CUST_CONTACT": cust_contact,
            "CUST_EMAIL": cust_email,
            "EXECUTIVE": executive,
            "CHASSIS_NO": chassis_no,
            "MAKE": make,
            "MODEL": model,
            "MODEL_YEAR": model_year,
            "REGN": regn,
            "USE_OF_VEHICLE": use_of_vehicle,
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": veh_seats,
            "COVERAGE_TYPE": coverage_type,
            "SUM_INSURED": sum_insured,
            "PREMIUM_ESTIMATE": premium_estimate,
            "PRODUCT_TYPE": product_type,
            "POLICY_TYPE": policy_type,
            "VALIDITY_PERIOD": validity_period,
            "VALIDITY_EXPIRY": validity_expiry,
            "STATUS": "Draft",
            "CREATED_DATE": date.today(),
            "REMARKS": remarks
        }
        
        # Check for missing mandatory fields
        missing_fields = [field for field, value in mandatory_fields.items() if not str(value).strip()]
        
        return form_data, submit, back, missing_fields


def quotation_summary_display(quotation_data):
    """
    Display quotation summary in a formatted layout
    """
    st.markdown("#### Quotation Summary")
    
    # Display quotation summary in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Information")
        st.write(f"**TEMP Policy ID:** {quotation_data['TEMP_POLICY_ID']}")
        st.write(f"**Customer ID:** {quotation_data['CUST_ID']}")
        st.write(f"**Name:** {quotation_data['CUST_NAME']}")
        st.write(f"**Contact:** {quotation_data['CUST_CONTACT']}")
        if quotation_data['CUST_EMAIL']:
            st.write(f"**Email:** {quotation_data['CUST_EMAIL']}")
        st.write(f"**Executive:** {quotation_data['EXECUTIVE']}")
        
        st.subheader("Vehicle Information")
        st.write(f"**Make/Model:** {quotation_data['MAKE']} {quotation_data['MODEL']}")
        st.write(f"**Year:** {quotation_data['MODEL_YEAR']}")
        st.write(f"**Chassis:** {quotation_data['CHASSIS_NO']}")
        if quotation_data['REGN']:
            st.write(f"**Registration:** {quotation_data['REGN']}")
        st.write(f"**Use:** {quotation_data['USE_OF_VEHICLE']}")
        st.write(f"**Seats:** {quotation_data['VEH_SEATS']}")
    
    with col2:
        st.subheader("Coverage Details")
        st.write(f"**Coverage Type:** {quotation_data['COVERAGE_TYPE']}")
        st.write(f"**Sum Insured:** ₹{quotation_data['SUM_INSURED']}")
        st.write(f"**Premium Estimate:** ₹{quotation_data['PREMIUM_ESTIMATE']}")
        st.write(f"**Product Type:** {quotation_data['PRODUCT_TYPE']}")
        if quotation_data['POLICY_TYPE']:
            st.write(f"**Policy Type:** {quotation_data['POLICY_TYPE']}")
        
        st.subheader("Validity Information")
        st.write(f"**Valid For:** {quotation_data['VALIDITY_PERIOD']}")
        st.write(f"**Expires On:** {quotation_data['VALIDITY_EXPIRY']}")
        st.write(f"**Status:** {quotation_data['STATUS']}")
        st.write(f"**Created On:** {quotation_data['CREATED_DATE']}")
    
    if quotation_data['REMARKS']:
        st.subheader("Remarks")
        st.write(quotation_data['REMARKS'])


def quotation_action_buttons():
    """
    Display action buttons for quotation management
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        download_pdf = st.button("📄 Download PDF")
    
    with col2:
        send_quote = st.button("📧 Send Quote")
    
    with col3:
        convert_policy = st.button("🔄 Convert to Policy")
    
    with col4:
        back_to_form = st.button("⬅️ Back to Form")
    
    return download_pdf, send_quote, convert_policy, back_to_form


def quotation_history_display(cust_id):
    """
    Display quotation history for a customer
    """
    st.markdown("---")
    st.subheader("Quotation History")
    
    # TODO: Implement quotation history fetch based on CUST_ID
    # For now, show placeholder
    if cust_id:
        st.info(f"Previous quotations for Customer ID: {cust_id} will be displayed here.")
        
        # Placeholder table structure
        import pandas as pd
        placeholder_data = {
            "TEMP_POLICY_ID": ["TEMP_001", "TEMP_002"],
            "Created Date": ["2024-01-15", "2024-02-10"],
            "Coverage Type": ["COMPREHENSIVE", "THIRD PARTY"],
            "Premium": ["₹15,000", "₹8,500"],
            "Status": ["Expired", "Sent"],
            "Validity": ["7 days", "15 days"]
        }
        st.dataframe(pd.DataFrame(placeholder_data), use_container_width=True)
    else:
        st.info("Enter Customer ID to view quotation history.")


def convert_quotation_to_policy_data(quotation_data):
    """
    Convert quotation data to policy form defaults
    """
    return {
        "CUST_ID": quotation_data.get("CUST_ID", ""),
        "EXECUTIVE": quotation_data.get("EXECUTIVE", ""),
        "CHASSIS_NO": quotation_data.get("CHASSIS_NO", ""),
        "MAKE": quotation_data.get("MAKE", ""),
        "MODEL": quotation_data.get("MODEL", ""),
        "MODEL_YEAR": quotation_data.get("MODEL_YEAR", ""),
        "REGN": quotation_data.get("REGN", ""),
        "USE_OF_VEHICLE": quotation_data.get("USE_OF_VEHICLE", ""),
        "DRV_DOB": quotation_data.get("DRV_DOB", date(1990, 1, 1)),
        "DRV_DLI": quotation_data.get("DRV_DLI", date(2010, 1, 1)),
        "VEH_SEATS": quotation_data.get("VEH_SEATS", ""),
        "SUM_INSURED": quotation_data.get("SUM_INSURED", ""),
        "PREMIUM2": quotation_data.get("PREMIUM_ESTIMATE", ""),
        "PRODUCT": quotation_data.get("PRODUCT_TYPE", ""),
        "POLICYTYPE": quotation_data.get("POLICY_TYPE", ""),
        "POL_EFF_DATE": date.today(),
        "POL_EXPIRY_DATE": date.today() + timedelta(days=365),
        "POL_ISSUE_DATE": date.today(),
        "BODY": ""  # Add default for BODY field
    }