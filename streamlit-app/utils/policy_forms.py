import streamlit as st
from db_utils import fetch_data
from datetime import datetime, date



def policy_manual_form(defaults=None):
    if defaults is None:
        defaults = {}

    try:
        broker_query = "SELECT Broker_ID, Broker_Name, Commission FROM Broker"
        broker_data = fetch_data(broker_query)
        broker_names = ["Select Broker"] + [row["Broker_Name"] for row in broker_data] if broker_data else ["No Brokers Found"]
    except Exception as e:
        st.error(f"Failed to fetch broker data: {e}")
        broker_names = ["Error loading brokers"]
        broker_data = []
    
    try:
        insurer_query = "SELECT Facility_ID, Facility_Name, Group_Size, Insurer_ID, Insurer_Name, Participation FROM insurer"
        insurer_data = fetch_data(insurer_query)
        # Get unique facility names only
        unique_facilities = list(set([row["Facility_Name"] for row in insurer_data])) if insurer_data else []
        facility_names = ["Select Facility"] + sorted(unique_facilities) if unique_facilities else ["No Facilities Found"]
    except Exception as e:
        st.error(f"Failed to fetch insurer data: {e}")
        facility_names = ["Error loading facilities"]
        insurer_data = []
    
 # Move selections OUTSIDE the form for immediate re-rendering
    st.caption("Fields marked with * are mandatory")
    
    # Broker Details Section
    st.subheader("Broker Details")
    selected_broker = st.selectbox("Select Broker *", broker_names, key="broker_select", index=broker_names.index(defaults.get("Broker_Name", "Select Broker"))  if defaults and defaults.get("Broker_Name", "Select Broker") in broker_names else 0)
    
    # Display broker details if a broker is selected
    if selected_broker and selected_broker != "Select Broker" and selected_broker != "No Brokers Found" and selected_broker != "Error loading brokers":
        selected_broker_data = next((broker for broker in broker_data if broker["Broker_Name"] == selected_broker), None)
        if selected_broker_data:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                st.text_input("Broker ID", value=str(selected_broker_data.get("Broker_ID", "")), disabled=True, key="broker_id_display")
            with col_b2:
                st.text_input("Broker Name", value=str(selected_broker_data.get("Broker_Name", "")), disabled=True, key="broker_name_display")
            with col_b3:
                st.text_input("Commission", value=str(selected_broker_data.get("Commission", "")), disabled=True, key="broker_commission_display")

    # Insurer Details Section
    st.subheader("Insurer Details")
    selected_facility = st.selectbox("Select Facility *", facility_names, key="facility_select", index=facility_names.index(defaults.get("Facility_Name", "Select Facility")) if defaults and defaults.get("Facility_Name", "Select Facility") in facility_names else 0)
    
    # Display insurer details if a facility is selected
    if selected_facility and selected_facility != "Select Facility" and selected_facility != "No Facilities Found" and selected_facility != "Error loading facilities":
        # Get all insurers for the selected facility
        facility_insurers = [insurer for insurer in insurer_data if insurer["Facility_Name"] == selected_facility]
        
        if facility_insurers:
            st.markdown(f"**Facility:** {selected_facility}")
            
            # Show facility details (using first record for facility info)
            first_record = facility_insurers[0]
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.text_input("Facility ID", value=str(first_record.get("Facility_ID", "")), disabled=True, key="facility_id_display")
            with col_f2:
                st.text_input("Group Size", value=str(first_record.get("Group_Size", "")), disabled=True, key="group_size_display")
            

            st.markdown("**Insurers in this Facility:**")
            
            # Create table using st.table for static display
            import pandas as pd
            
            insurer_df = pd.DataFrame([{
                "Insurer ID": insurer.get("Insurer_ID", ""),
                "Insurer Name": insurer.get("Insurer_Name", ""),
                "Participation": insurer.get("Participation", "")
            } for insurer in facility_insurers])
            
            if not insurer_df.empty:
                insurer_df.index = insurer_df.index + 1
                st.table(insurer_df)

    with st.form("policy_manual_form"):
        # Customer Details Section
        st.subheader("Customer Details")
        col1, col2, col3 = st.columns(3)
        cust_id = col1.text_input("Customer ID *", value=str(defaults.get("CUST_ID", "")))
        regn = col2.text_input("REGION", value=defaults.get("REGN", ""))
        executive = col3.text_input("EXECUTIVE *", value=defaults.get("EXECUTIVE", ""))

        # Vehicle Details Section
        st.subheader("Vehicle Details")
        col4, col5, col6 = st.columns(3)
        body = col4.text_input("BODY", value=defaults.get("BODY", ""))
        make = col5.text_input("MAKE", value=defaults.get("MAKE", ""))
        model = col6.text_input("MODEL", value=defaults.get("MODEL", ""))

        col10, col11, col12 = st.columns(3)
        veh_seats = col10.text_input("VEHICLE SEATS", value=str(defaults.get("VEH_SEATS", "")))
        model_year = col11.text_input("MODEL YEAR", value=str(defaults.get("MODEL_YEAR", "")))
        chassis_no = col12.text_input("CHASSIS NO *", value=defaults.get("CHASSIS_NO", ""))

        col7, col8, col9 = st.columns(3)
        use_of_vehicle = col7.text_input("USE OF VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""))
        product = col8.text_input("PRODUCT", value=defaults.get("PRODUCT", ""))

        # Driver Details Section
        st.subheader("Driver Details")
        col13, col14, col24 = st.columns(3)
        drv_dob = col13.date_input("DRIVER DOB", value=defaults.get("DRV_DOB", date(2000,1,1)),
                                   min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
                                   max_value=date.today()       # Allow up to current date
        )
        drv_dli = col14.date_input("DRIVER DLI", value=defaults.get("DRV_DLI", date(2000,1,1)),
                                   min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
                                   max_value=date.today()       # Allow up to current date
        )
        nationality = col24.text_input("NATIONALITY *", value=defaults.get("NATIONALITY", ""))


        # Coverage and Premium Details Section
        st.subheader("Premium")
        col15, col16, col17 = st.columns(3)
        policy_no = col15.text_input("POLICY NO *", value=defaults.get("POLICY_NO", ""))
        policytype = col16.text_input("POLICY TYPE", value=defaults.get("POLICYTYPE", ""))
        sum_insured = col17.text_input("SUM INSURED *", value=str(defaults.get("SUM_INSURED", "")))

        col21, col22, col23 = st.columns(3)
        pol_issue_date = col21.date_input("POLICY ISSUE DATE *", value=defaults.get("POL_ISSUE_DATE", date.today()))
        pol_eff_date = col22.date_input("POLICY EFFECTIVE DATE *", value=defaults.get("POL_EFF_DATE", date.today()))
        # pol_expiry_date = col23.date_input("POLICY EXPIRY DATE *", value=defaults.get("POL_EXPIRY_DATE", date.today()))
        def get_default_expiry_date():
            today = date.today()
            try:
                return today.replace(year=today.year + 1)
            except ValueError:  # Handle Feb 29 on non-leap years
                return today.replace(year=today.year + 1, month=2, day=28)

        pol_expiry_date = col23.date_input("POLICY EXPIRY DATE *", value=defaults.get("POL_EXPIRY_DATE", get_default_expiry_date()))

        col18, col19, col20 = st.columns(3)
        premium2 = col18.text_input("PREMIUM *", value=str(defaults.get("PREMIUM2", "")))

        submit = st.form_submit_button("Submit")
        back = st.form_submit_button("Back")

        # Convert text inputs to int where needed
        def to_int(val):
            try:
                return int(val)
            except Exception:
                return None
            
        # Get selected broker ID for form data
        selected_broker_id = ""
        if selected_broker and selected_broker != "Select Broker":
            selected_broker_data = next((broker for broker in broker_data if broker["Broker_Name"] == selected_broker), None)
            if selected_broker_data:
                selected_broker_id = selected_broker_data.get("Broker_ID", "")

        # Get selected facility ID for form data
        selected_facility_id = ""
        if selected_facility and selected_facility != "Select Facility":
            facility_insurers = [insurer for insurer in insurer_data if insurer["Facility_Name"] == selected_facility]
            if facility_insurers:
                selected_facility_id = facility_insurers[0].get("Facility_ID", "")

        form_data = {
            "CUST_ID": to_int(cust_id),
            "EXECUTIVE": executive,
            "Broker_ID": selected_broker_id,
            "Broker_Name": selected_broker if selected_broker != "Select Broker" else "",
            "Facility_ID": selected_facility_id,  # Add facility ID to form data
            "Facility_Name": selected_facility if selected_facility != "Select Facility" else "",
            "BODY": body,
            "MAKE": make,
            "MODEL": model,
            "USE_OF_VEHICLE": use_of_vehicle,
            "MODEL_YEAR": to_int(model_year),
            "CHASSIS_NO": chassis_no,
            "REGN": regn,
            "POLICY_NO": policy_no,
            "POL_EFF_DATE": pol_eff_date,
            "POL_EXPIRY_DATE": pol_expiry_date,
            "SUM_INSURED": to_int(sum_insured),
            "POL_ISSUE_DATE": pol_issue_date,
            "PREMIUM2": to_int(premium2),
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": to_int(veh_seats),
            "PRODUCT": product,
            "POLICYTYPE": policytype,
            "NATIONALITY": nationality
        }
        
        # Validation for mandatory fields (add facility selection)
        mandatory_fields = [
            ("CUST_ID", cust_id),
            ("EXECUTIVE", executive),
            ("BROKER", selected_broker if selected_broker != "Select Broker" else ""),
            ("FACILITY", selected_facility if selected_facility != "Select Facility" else ""),
            ("CHASSIS_NO", chassis_no),
            ("POLICY_NO", policy_no),
            ("POL_EFF_DATE", pol_eff_date),
            ("POL_EXPIRY_DATE", pol_expiry_date),
            ("SUM_INSURED", sum_insured),
            ("PREMIUM2", premium2),
            ("POL_ISSUE_DATE", pol_issue_date),
            ("NATIONALITY", nationality)
        ]
        missing = [name for name, val in mandatory_fields if (isinstance(val, str) and not val.strip()) or val is None]
        # Check if submit button was pressed
        if submit:
            # Check for broker selection specifically
            if not selected_broker or selected_broker == "Select Broker":
                st.error("Please select a Broker before submitting the form.")
                return form_data, False, back  # Return False for submit to prevent processing
            
            # Check for facility selection specifically
            if not selected_facility or selected_facility == "Select Facility":
                st.error("Please select a Facility before submitting the form.")
                return form_data, False, back  # Return False for submit to prevent processing
            
            # Check other missing mandatory fields
            if missing:
                st.error(f"Please fill all mandatory fields: {', '.join(missing)}.")
                return form_data, False, back  # Return False for submit to prevent processing
        
        return form_data, submit, back
    

def policy_summary_display(policy_data):
    """
    Display policy summary in a formatted layout
    """
    st.markdown("#### Policy Summary")
    
    # Display policy summary in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Information")
        st.write(f"**Policy Number:** {policy_data['POLICY_NO']}")
        st.write(f"**Customer ID:** {policy_data['CUST_ID']}")
        st.write(f"**Executive:** {policy_data['EXECUTIVE']}")
        if policy_data.get('NATIONALITY'):
            st.write(f"**Nationality:** {policy_data['NATIONALITY']}")
        
        st.subheader("Vehicle Information")
        st.write(f"**Make/Model:** {policy_data.get('MAKE', '')} {policy_data.get('MODEL', '')}")
        st.write(f"**Year:** {policy_data.get('MODEL_YEAR', '')}")
        st.write(f"**Chassis:** {policy_data['CHASSIS_NO']}")
        if policy_data.get('REGN'):
            st.write(f"**Registration:** {policy_data['REGN']}")
        st.write(f"**Use:** {policy_data.get('USE_OF_VEHICLE', '')}")
        st.write(f"**Seats:** {policy_data.get('VEH_SEATS', '')}")
        if policy_data.get('BODY'):
            st.write(f"**Body Type:** {policy_data['BODY']}")
    
    with col2:
        st.subheader("Policy Details")
        st.write(f"**Policy Type:** {policy_data.get('POLICYTYPE', '')}")
        st.write(f"**Product:** {policy_data.get('PRODUCT', '')}")
        st.write(f"**Sum Insured:** ₹{policy_data['SUM_INSURED']:,}")
        st.write(f"**Premium:** ₹{policy_data['PREMIUM2']:,}")
        
        st.subheader("Coverage Period")
        st.write(f"**Issue Date:** {policy_data['POL_ISSUE_DATE']}")
        st.write(f"**Effective Date:** {policy_data['POL_EFF_DATE']}")
        st.write(f"**Expiry Date:** {policy_data['POL_EXPIRY_DATE']}")
        
        st.subheader("Broker & Insurer")
        if policy_data.get('Broker_Name'):
            st.write(f"**Broker:** {policy_data['Broker_Name']}")
        if policy_data.get('Facility_Name'):
            st.write(f"**Facility:** {policy_data['Facility_Name']}")


    



def policy_cancel_form(defaults=None):
    if defaults is None:
        defaults = {}
    
    with st.form("policy_cancel_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Customer Details Section
        st.subheader("Customer Details")
        col1, col2, col3 = st.columns(3)
        cust_id = col1.text_input("Customer ID", value=defaults.get("CUST_ID", 1), disabled=True)
        executive = col2.text_input("EXECUTIVE", value=defaults.get("EXECUTIVE", ""), disabled=True)
        nationality = col3.text_input("NATIONALITY", value=defaults.get("NATIONALITY", ""), disabled=True)

        # Vehicle Details Section
        st.subheader("Vehicle Details")
        col4, col5, col6 = st.columns(3)
        body = col4.text_input("BODY", value=defaults.get("BODY", ""), disabled=True)
        make = col5.text_input("MAKE", value=defaults.get("MAKE", ""), disabled=True)
        model = col6.text_input("MODEL", value=defaults.get("MODEL", ""), disabled=True)

        col7, col8, col9 = st.columns(3)
        veh_seats = col7.text_input("VEHICLE SEATS", value=defaults.get("VEH_SEATS", 1), disabled=True)
        model_year = col8.text_input("MODEL YEAR", value=defaults.get("MODEL_YEAR", 2024), disabled=True)
        chassis_no = col9.text_input("CHASSIS NO", value=defaults.get("CHASSIS_NO", ""), disabled=True)

        col10, col11, col12 = st.columns(3)
        use_of_vehicle = col10.text_input("USE OF VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""), disabled=True)
        product = col11.text_input("PRODUCT", value=defaults.get("PRODUCT", ""), disabled=True)
        regn = col12.text_input("REGION", value=defaults.get("REGN", ""), disabled=True)

        # Driver Details Section
        st.subheader("Driver Details")
        col13, col14, col15 = st.columns(3)
        drv_dob = col13.date_input("DRIVER DOB", value=defaults.get("DRV_DOB", date(2000,1,1)), disabled=True)
        drv_dli = col14.date_input("DRIVER DLI", value=defaults.get("DRV_DLI", date(2000,1,1)), disabled=True)

        # Policy Details Section
        st.subheader("Policy Details")
        col16, col17, col18 = st.columns(3)
        policy_no = col16.text_input("POLICY NO", value=defaults.get("POLICY_NO", ""), disabled=True)
        policytype = col17.text_input("POLICY TYPE", value=defaults.get("POLICYTYPE", ""), disabled=True)
        sum_insured = col18.text_input("SUM INSURED *", value=defaults.get("SUM_INSURED", 0.0), disabled=True)

        col19, col20, col21 = st.columns(3)
        pol_issue_date = col19.date_input("POLICY ISSUE DATE", value=defaults.get("POL_ISSUE_DATE", date.today()), disabled=True)
        pol_eff_date = col20.date_input("POLICY EFFECTIVE DATE", value=defaults.get("POL_EFF_DATE", date.today()), disabled=True)
        pol_expiry_date = col21.date_input("POLICY EXPIRY DATE", value=defaults.get("POL_EXPIRY_DATE", date.today()), disabled=True)

        # Broker and Insurer Details Section
        st.subheader("Broker & Insurer Details")
        col25, col26, col27 = st.columns(3)
        broker_name = col25.text_input("Broker Name", value=defaults.get("Broker_Name", ""), disabled=True)
        facility_name = col26.text_input("Facility Name", value=defaults.get("Facility_Name", ""), disabled=True)
        # Premium and Cancellation Section
        st.subheader("Premium & Cancellation")
        col22, col23, col24 = st.columns(3)
        original_premium = col22.text_input("Original Premium", value=defaults.get("PREMIUM2", 0.0), disabled=True)

        premium2 = col23.text_input("Return Premium *", value=defaults.get("PREMIUM2", 0.0), disabled=False)
        cancel_date = col24.date_input("Cancellation Date *", value=date.today(), key="cancel_date")

        # Confirmation Section
        st.subheader("Confirmation")
        confirm_cancel = st.checkbox("I confirm I want to cancel this policy", key="cancel_confirm")
        
        submit = st.form_submit_button("Submit Cancellation")
        back = st.form_submit_button("Back")

        # Convert text inputs to int where needed
        def to_int(val):
            try:
                return int(val)
            except Exception:
                return None

        form_data = {
            "CUST_ID": to_int(cust_id),
            "EXECUTIVE": executive,
            "NATIONALITY": defaults.get("NATIONALITY", ""),
            "BODY": body,
            "MAKE": make,
            "MODEL": model,
            "USE_OF_VEHICLE": use_of_vehicle,
            "MODEL_YEAR": model_year,
            "CHASSIS_NO": chassis_no,
            "REGN": regn,
            "POLICY_NO": policy_no,
            "POL_EFF_DATE": pol_eff_date,
            "POL_EXPIRY_DATE": pol_expiry_date,
            "SUM_INSURED": sum_insured,
            "POL_ISSUE_DATE": pol_issue_date,
            "PREMIUM2": int(premium2) if premium2 else 0,
            "ORIGINAL_PREMIUM": original_premium,
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": veh_seats,
            "PRODUCT": product,
            "POLICYTYPE": policytype,
            "CANCELLATION_DATE": str(cancel_date),
            "isCancelled": 1,
            "TransactionType": "Policy Cancellation",
            "confirm_cancel": confirm_cancel
        }
        
        # Validation for mandatory fields
        mandatory_fields = [
            ("RETURN_PREMIUM", premium2),
            ("CANCELLATION_DATE", cancel_date)
        ]
        
        if submit:
            # Check confirmation first
            if not confirm_cancel:
                st.error("⚠️ Please confirm cancellation by checking the box before submitting.")
                return form_data, False, back
            
            # Validate return premium does not exceed original premium
            if premium2 > original_premium:
                st.error("⚠️ Return Premium cannot exceed the original premium.")
                return form_data, False, back
            
            # Check other mandatory fields
            missing = [name for name, val in mandatory_fields if (isinstance(val, str) and not val.strip()) or val is None]
            if missing:
                st.error(f"⚠️ Please fill all mandatory fields: {', '.join(missing)}.")
                return form_data, False, back
        
        return form_data, submit, back
    



def policy_mta_form(defaults=None):
    if defaults is None:
        defaults = {}
    
    with st.form("policy_mta_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Customer Details Section
        st.subheader("Customer Details")
        col1, col2, col3 = st.columns(3)
        cust_id = col1.text_input("Customer ID", value=str(defaults.get("CUST_ID", "")), disabled=True)
        executive = col2.text_input("EXECUTIVE", value=defaults.get("EXECUTIVE", ""), disabled=True)
        nationality = col3.text_input("NATIONALITY", value=defaults.get("NATIONALITY", ""), disabled=True)

        # Vehicle Details Section
        st.subheader("Vehicle Details")
        col4, col5, col6 = st.columns(3)
        body = col4.text_input("BODY", value=defaults.get("BODY", ""))
        make = col5.text_input("MAKE", value=defaults.get("MAKE", ""))
        model = col6.text_input("MODEL", value=defaults.get("MODEL", ""))

        col7, col8, col9 = st.columns(3)
        veh_seats = col7.text_input("VEHICLE SEATS", value=str(defaults.get("VEH_SEATS", "")))
        model_year = col8.text_input("MODEL YEAR", value=str(defaults.get("MODEL_YEAR", "")))
        chassis_no = col9.text_input("CHASSIS NO", value=defaults.get("CHASSIS_NO", ""), disabled=True)

        col10, col11, col12 = st.columns(3)
        use_of_vehicle = col10.text_input("USE OF VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""))
        product = col11.text_input("PRODUCT", value=defaults.get("PRODUCT", ""))
        regn = col12.text_input("REGION", value=defaults.get("REGN", ""))

        # Driver Details Section
        st.subheader("Driver Details")
        col13, col14, col15 = st.columns(3)
        drv_dob = col13.date_input(
            "DRIVER DOB", 
            value=defaults.get("DRV_DOB", date(2000,1,1)),
            min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
            max_value=date.today()       # Allow up to current date
        )
        drv_dli = col14.date_input("DRIVER DLI", value=defaults.get("DRV_DLI", date(2000,1,1)),
                                   min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
                                   max_value=date.today()       # Allow up to current date
        )

        # Policy Details Section
        st.subheader("Policy Details")
        col16, col17, col18 = st.columns(3)
        policy_no = col16.text_input("POLICY NO", value=defaults.get("POLICY_NO", ""), disabled=True)
        policytype = col17.text_input("POLICY TYPE", value=defaults.get("POLICYTYPE", ""))
        sum_insured = col18.text_input("SUM INSURED", value=str(defaults.get("SUM_INSURED", "")), disabled=False)

        col19, col20, col21 = st.columns(3)
        pol_issue_date = col19.date_input("POLICY ISSUE DATE", value=defaults.get("POL_ISSUE_DATE", date.today()), disabled=True)
        pol_eff_date = col20.date_input("POLICY EFFECTIVE DATE", value=defaults.get("POL_EFF_DATE", date.today()), disabled=True)
        pol_expiry_date = col21.date_input("POLICY EXPIRY DATE", value=defaults.get("POL_EXPIRY_DATE", date.today()), disabled=True)


        #Broker and Insurer Details Section
        st.subheader("Broker & Insurer Details")
        col25, col26, col27 = st.columns(3)
        broker_name = col25.text_input("Broker Name", value=defaults.get("Broker_Name", ""), disabled=True)
        facility_name = col26.text_input("Facility Name", value=defaults.get("Facility_Name", ""), disabled=True)

        # Premium Section
        st.subheader("Premium")
        col22, col23, col24 = st.columns(3)
        premium2 = col22.text_input("PREMIUM", value=str(defaults.get("PREMIUM2", "")))

        submit = st.form_submit_button("Submit MTA")
        back = st.form_submit_button("Back")

        # Convert text inputs to appropriate types
        def to_int(val):
            try:
                return int(val)
            except Exception:
                return None
            
        #for float conversion
        def to_float(val):
            try:
                return float(val)
            except Exception:
                return None

        form_data = {
            "CUST_ID": to_int(cust_id),
            "EXECUTIVE": executive,
            "NATIONALITY": nationality,
            "BODY": body,
            "MAKE": make,
            "MODEL": model,
            "USE_OF_VEHICLE": use_of_vehicle,
            "MODEL_YEAR": to_int(model_year),
            "CHASSIS_NO": chassis_no,
            "REGN": regn,
            "POLICY_NO": policy_no,
            "POL_EFF_DATE": pol_eff_date,
            "POL_EXPIRY_DATE": pol_expiry_date,
            "SUM_INSURED": to_float(sum_insured),
            "POL_ISSUE_DATE": pol_issue_date,
            "PREMIUM2": to_int(premium2),
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": to_int(veh_seats),
            "PRODUCT": product,
            "POLICYTYPE": policytype,
            "TransactionType": "MTA"
        }
        
        return form_data, submit, back


def mta_summary_display(policy_data):
    """
    Display MTA summary in a formatted layout
    """
    st.markdown("#### MTA Summary")

    # Display MTA summary in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Information")
        st.write(f"**Policy Number:** {policy_data['POLICY_NO']}")
        st.write(f"**Customer ID:** {policy_data['CUST_ID']}")
        st.write(f"**Executive:** {policy_data['EXECUTIVE']}")
        if policy_data.get('NATIONALITY'):
            st.write(f"**Nationality:** {policy_data['NATIONALITY']}")
        
        st.subheader("Vehicle Information")
        st.write(f"**Make/Model:** {policy_data.get('MAKE', '')} {policy_data.get('MODEL', '')}")
        st.write(f"**Year:** {policy_data.get('MODEL_YEAR', '')}")
        st.write(f"**Chassis:** {policy_data['CHASSIS_NO']}")
        if policy_data.get('REGN'):
            st.write(f"**Region:** {policy_data['REGN']}")
        st.write(f"**Use:** {policy_data.get('USE_OF_VEHICLE', '')}")
        st.write(f"**Seats:** {policy_data.get('VEH_SEATS', '')}")
        if policy_data.get('BODY'):
            st.write(f"**Body Type:** {policy_data['BODY']}")
    
    with col2:
        st.subheader("Policy Details")
        st.write(f"**Policy Type:** {policy_data.get('POLICYTYPE', '')}")
        st.write(f"**Product:** {policy_data.get('PRODUCT', '')}")
        st.write(f"**Sum Insured:** {policy_data['SUM_INSURED']:,}")
        st.write(f"**Premium:** {policy_data['PREMIUM2']:,}")

        st.subheader("Coverage Period")
        st.write(f"**Issue Date:** {policy_data['POL_ISSUE_DATE']}")
        st.write(f"**Effective Date:** {policy_data['POL_EFF_DATE']}")
        st.write(f"**Expiry Date:** {policy_data['POL_EXPIRY_DATE']}")
        
        st.subheader("Broker & Insurer")
        if policy_data.get('Broker_Name'):
            st.write(f"**Broker:** {policy_data['Broker_Name']}")
        if policy_data.get('Facility_Name'):
            st.write(f"**Facility:** {policy_data['Facility_Name']}")


def policy_renewal_form(defaults=None):
    if defaults is None:
        defaults = {}
    
    with st.form("policy_renewal_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Customer Details Section
        st.subheader("Customer Details")
        col1, col2, col3 = st.columns(3)
        cust_id = col1.text_input("Customer ID", value=str(defaults.get("CUST_ID", "")), disabled=True)
        executive = col2.text_input("EXECUTIVE", value=defaults.get("EXECUTIVE", ""))
        nationality = col3.text_input("NATIONALITY", value=defaults.get("NATIONALITY", ""))

        # Vehicle Details Section
        st.subheader("Vehicle Details")
        col4, col5, col6 = st.columns(3)
        body = col4.text_input("BODY", value=defaults.get("BODY", ""))
        make = col5.text_input("MAKE", value=defaults.get("MAKE", ""))
        model = col6.text_input("MODEL", value=defaults.get("MODEL", ""))

        col7, col8, col9 = st.columns(3)
        veh_seats = col7.text_input("VEHICLE SEATS", value=str(defaults.get("VEH_SEATS", "")))
        model_year = col8.text_input("MODEL YEAR", value=str(defaults.get("MODEL_YEAR", "")))
        chassis_no = col9.text_input("CHASSIS NO", value=defaults.get("CHASSIS_NO", ""), disabled=True)

        col10, col11, col12 = st.columns(3)
        use_of_vehicle = col10.text_input("USE OF VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""))
        product = col11.text_input("PRODUCT", value=defaults.get("PRODUCT", ""))
        regn = col12.text_input("REGION", value=defaults.get("REGN", ""))

        # Driver Details Section
        st.subheader("Driver Details")
        col13, col14, col15 = st.columns(3)
        drv_dob = col13.date_input("DRIVER DOB", value=defaults.get("DRV_DOB", date(2000,1,1)),
                                   
                                   min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
                                   max_value=date.today()  )
        drv_dli = col14.date_input("DRIVER DLI", value=defaults.get("DRV_DLI", date(2000,1,1)),
                                   min_value=date(1940, 1, 1),  # Allow dates as far back as 1940
                                   max_value=date.today()  )

        # Policy Details Section
        st.subheader("Policy Details")
        col16, col17, col18 = st.columns(3)
        policy_no = col16.text_input("POLICY NO", value=defaults.get("POLICY_NO", ""), disabled=True)
        policytype = col17.text_input("POLICY TYPE", value=defaults.get("POLICYTYPE", ""))
        sum_insured = col18.text_input("SUM INSURED", value=str(defaults.get("SUM_INSURED", "")))

        # Auto-calculate renewed dates (add 1 year)
        original_eff_date = defaults.get("POL_EFF_DATE", datetime.today())
        original_expiry_date = defaults.get("POL_EXPIRY_DATE", datetime.today())

        if isinstance(original_eff_date, str):
            try:
                original_eff_date = datetime.strptime(original_eff_date, "%Y-%m-%d").date()
            except:
                original_eff_date = datetime.today()
        
        if isinstance(original_expiry_date, str):
            try:
                original_expiry_date = datetime.strptime(original_expiry_date, "%Y-%m-%d").date()
            except:
                original_expiry_date = datetime.today()

        # Calculate new dates (add 1 year)
        if (original_expiry_date > datetime.today()):
            new_eff_date = original_eff_date.replace(year=original_eff_date.year + 1)
            new_expiry_date = original_expiry_date.replace(year=original_expiry_date.year + 1)
        else:
            new_eff_date = date.today()
            new_expiry_date = new_eff_date.replace(year=new_eff_date.year + 1)

        col19, col20, col21 = st.columns(3)
        pol_issue_date = col19.date_input("POLICY ISSUE DATE", value=date.today(), disabled=True)
        pol_eff_date = col20.date_input("POLICY EFFECTIVE DATE", value=new_eff_date, disabled=True)
        pol_expiry_date = col21.date_input("POLICY EXPIRY DATE", value=new_expiry_date, disabled=True)

        # Broker and Insurer Details Section
        st.subheader("Broker & Insurer Details")
        col25, col26, col27 = st.columns(3)
        broker_name = col25.text_input("Broker Name", value=defaults.get("Broker_Name", ""), disabled=True)
        facility_name = col26.text_input("Facility Name", value=defaults.get("Facility_Name", ""), disabled=True)

        # Premium Section
        st.subheader("Premium")
        col22, col23, col24 = st.columns(3)
        premium2 = col22.text_input("PREMIUM", value=str(defaults.get("PREMIUM2", "")))

        submit = st.form_submit_button("Submit Renewal")
        back = st.form_submit_button("Back")

        # Convert text inputs to appropriate types
        def to_int(val):
            try:
                return int(val)
            except Exception:
                return None
            
        def to_float(val):
            try:
                return float(val)
            except Exception:
                return None

        form_data = {
            "CUST_ID": to_int(cust_id),
            "EXECUTIVE": executive,
            "NATIONALITY": nationality,
            "BODY": body,
            "MAKE": make,
            "MODEL": model,
            "USE_OF_VEHICLE": use_of_vehicle,
            "MODEL_YEAR": to_int(model_year),
            "CHASSIS_NO": chassis_no,
            "REGN": regn,
            "POLICY_NO": policy_no,
            "POL_EFF_DATE": pol_eff_date,
            "POL_EXPIRY_DATE": pol_expiry_date,
            "POL_ISSUE_DATE": pol_issue_date,
            "SUM_INSURED": to_float(sum_insured),
            "PREMIUM2": to_int(premium2),
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": to_int(veh_seats),
            "PRODUCT": product,
            "POLICYTYPE": policytype,
            "TransactionType": "Renewal",
            
        }
        
        return form_data, submit, back


def renewal_summary_display(policy_data):
    """
    Display Renewal summary in a formatted layout
    """
    st.markdown("#### Renewal Summary")

    # Display Renewal summary in two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Customer Information")
        st.write(f"**Policy Number:** {policy_data['POLICY_NO']}")
        st.write(f"**Customer ID:** {policy_data['CUST_ID']}")
        st.write(f"**Executive:** {policy_data['EXECUTIVE']}")
        if policy_data.get('NATIONALITY'):
            st.write(f"**Nationality:** {policy_data['NATIONALITY']}")
        
        st.subheader("Vehicle Information")
        st.write(f"**Make/Model:** {policy_data.get('MAKE', '')} {policy_data.get('MODEL', '')}")
        st.write(f"**Year:** {policy_data.get('MODEL_YEAR', '')}")
        st.write(f"**Chassis:** {policy_data['CHASSIS_NO']}")
        if policy_data.get('REGN'):
            st.write(f"**Region:** {policy_data['REGN']}")
        st.write(f"**Use:** {policy_data.get('USE_OF_VEHICLE', '')}")
        st.write(f"**Seats:** {policy_data.get('VEH_SEATS', '')}")
        if policy_data.get('BODY'):
            st.write(f"**Body Type:** {policy_data['BODY']}")
    
    with col2:
        st.subheader("Policy Details")
        st.write(f"**Policy Type:** {policy_data.get('POLICYTYPE', '')}")
        st.write(f"**Product:** {policy_data.get('PRODUCT', '')}")
        
        # Handle None values for numeric fields
        sum_insured = policy_data.get('SUM_INSURED')
        if sum_insured is not None:
            try:
                st.write(f"**Sum Insured:** ₹{int(sum_insured):,}")
            except (ValueError, TypeError):
                st.write(f"**Sum Insured:** {sum_insured}")
        else:
            st.write("**Sum Insured:** N/A")
        
        premium = policy_data.get('PREMIUM2')
        if premium is not None:
            try:
                st.write(f"**Premium:** ₹{int(premium):,}")
            except (ValueError, TypeError):
                st.write(f"**Premium:** {premium}")
        else:
            st.write("**Premium:** N/A")

        st.subheader("Coverage Period")
        pol_issue_date = policy_data.get('POL_ISSUE_DATE')
        if pol_issue_date:
            st.write(f"**Issue Date:** {pol_issue_date}")
        else:
            st.write("**Issue Date:** N/A")
            
        pol_eff_date = policy_data.get('POL_EFF_DATE')
        if pol_eff_date:
            st.write(f"**Effective Date:** {pol_eff_date}")
        else:
            st.write("**Effective Date:** N/A")
            
        pol_expiry_date = policy_data.get('POL_EXPIRY_DATE')
        if pol_expiry_date:
            st.write(f"**Expiry Date:** {pol_expiry_date}")
        else:
            st.write("**Expiry Date:** N/A")
        
        st.subheader("Broker & Insurer")
        if policy_data.get('Broker_Name'):
            st.write(f"**Broker:** {policy_data['Broker_Name']}")
        if policy_data.get('Facility_Name'):
            st.write(f"**Facility:** {policy_data['Facility_Name']}")