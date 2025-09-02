import os
import dotenv
import streamlit as st
from db_utils import fetch_data
from datetime import datetime, date
from pathlib import Path






dotenv.load_dotenv(Path(__file__).parent.parent / ".env")




import requests
import json

def predict_premium_api(form_data):
    """
    Send form data to premium prediction API and return predicted premium
    
    Args:
        form_data (dict): Form data to send for prediction
        
    Returns:
        int/float: Predicted premium value or None if failed
    """
    try:
        # ✅ REPLACE WITH YOUR ACTUAL API ENDPOINT
        url = os.getenv("ML_PREMIUM_API")
        bearer_token = os.getenv("ML_PREMIUM_BEARER")

        
        # Headers
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }
        
        
        # Show loading spinner
        with st.spinner("🔮 Predicting premium based on your data..."):
            # Make API request
            response = requests.post(url, headers=headers, data=json.dumps(form_data))

        
        if response.status_code == 200:
            try:
                result = response.json()
                
                
                if "predictions" in result:
                    predicted_premium = result["predictions"][0][0]

                    # Show success message with details
                    st.success(f"✅ Premium predicted successfully!")
                    st.write(f"**Predicted Premium:** {predicted_premium:,}")

                    return predicted_premium
                    
                else:
                    st.error("❌ Invalid API response format. Missing 'predicted_premium' field.")
                    st.write("**API Response:**", result)
                    return None
                    
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON response from API")
                st.write("**Raw Response:**", response.text)
                return None
                
        else:
            st.error(f"❌ API Error: {response.status_code}")
            try:
                error_details = response.json()
                st.error(f"Error details: {error_details}")
            except:
                st.error(f"Raw error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏰ Request timed out. The prediction service is taking longer than expected.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("🌐 Connection error. Please check your internet connection or try again later.")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error during premium prediction: {str(e)}")
        return None

# def _format_submission_dt(dt: datetime) -> str:
#     # Millisecond precision like 2015-10-19 05:57:01.900
#     return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def _build_unique_id(policy_no: str, submission_dt: datetime) -> str:
    # Unique_ID = (Policy_No)_(Submission_Date) with compact timestamp yyyymmddHHMMSSmmm
    ts_compact = submission_dt.strftime("%Y%m%d%H%M%S%f")[:-3]  # trim to milliseconds round to 17
    return f"{policy_no}_{ts_compact}"


def validate_numeric_input(value, field_name, data_type="int", min_val=None, max_val=None, required=True):
    """
    Validate numeric input from text fields
    
    Args:
        value: The input value to validate
        field_name: Name of the field for error messages
        data_type: "int" or "float"
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        required: Whether the field is required
    
    Returns:
        tuple: (is_valid, converted_value, error_message)
    """
    # Check if empty and required
    if not value or str(value).strip() == "":
        if required:
            return False, None, f"{field_name} is required"
        else:
            return True, None, ""
    
    # Convert to string and strip whitespace
    str_value = str(value).strip()
    
    # Check for non-numeric characters
    if data_type == "int":
        # Allow only digits, minus sign at start, and decimal point (will be converted to int)
        if not str_value.replace('-', '').replace('.', '').isdigit():
            return False, None, f"{field_name} must contain only numbers"
        
        try:
            # Convert to float first to handle decimal strings, then to int
            converted_value = int(float(str_value))
        except (ValueError, TypeError):
            return False, None, f"{field_name} must be a valid integer"
            
    elif data_type == "float":
        # Allow digits, minus sign, and one decimal point
        if str_value.count('.') > 1 or not str_value.replace('-', '').replace('.', '').isdigit():
            return False, None, f"{field_name} must be a valid decimal number"
        
        try:
            converted_value = float(str_value)
        except (ValueError, TypeError):
            return False, None, f"{field_name} must be a valid decimal number"
    else:
        return False, None, f"Invalid data type specified: {data_type}"
    
    # Check min/max constraints
    if min_val is not None and converted_value < min_val:
        return False, None, f"{field_name} must be at least {min_val}"
    
    if max_val is not None and converted_value > max_val:
        return False, None, f"{field_name} must not exceed {max_val}"
    
    return True, converted_value, ""

def validate_text_input(value, field_name, min_length=None, max_length=None, required=True, allowed_chars=None, pattern=None):
    """
    Validate text input fields
    
    Args:
        value: The input value to validate
        field_name: Name of the field for error messages
        min_length: Minimum length required
        max_length: Maximum length allowed
        required: Whether the field is required
        allowed_chars: String of allowed characters (e.g., "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        pattern: Regex pattern to match
    
    Returns:
        tuple: (is_valid, cleaned_value, error_message)
    """
    import re
    
    # Handle None or empty values
    if not value:
        value = ""
    
    str_value = str(value).strip()
    
    # Check if empty and required
    if not str_value and required:
        return False, "", f"{field_name} is required"
    
    # Check minimum length
    if min_length is not None and len(str_value) < min_length:
        return False, str_value, f"{field_name} must be at least {min_length} characters long"
    
    # Check maximum length
    if max_length is not None and len(str_value) > max_length:
        return False, str_value, f"{field_name} must not exceed {max_length} characters"
    
    # Check allowed characters
    if allowed_chars is not None:
        for char in str_value:
            if char not in allowed_chars:
                return False, str_value, f"{field_name} contains invalid character: '{char}'"
    
    # Check regex pattern
    if pattern is not None:
        if not re.match(pattern, str_value):
            return False, str_value, f"{field_name} format is invalid"
    
    return True, str_value, ""

def validate_customer_id(cust_id):
    """Specific validation for Customer ID"""
    return validate_numeric_input(
        cust_id, 
        "Customer ID", 
        data_type="int", 
        min_val=1, 
        max_val=999999, 
        required=True
    )

def validate_vehicle_seats(seats):
    """Specific validation for Vehicle Seats"""
    return validate_numeric_input(
        seats, 
        "Vehicle Seats", 
        data_type="int", 
        min_val=1, 
        max_val=50, 
        required=False
    )

def validate_model_year(year):
    """Specific validation for Model Year"""
    from datetime import date
    current_year = date.today().year
    return validate_numeric_input(
        year, 
        "Model Year", 
        data_type="int", 
        min_val=1900, 
        max_val=current_year, 
        required=False
    )

def validate_sum_insured(amount):
    """Specific validation for Sum Insured"""
    return validate_numeric_input(
        amount, 
        "Sum Insured", 
        data_type="float", 
        min_val=0.01, 
        max_val=99999999.99, 
        required=True
    )

def validate_premium(amount):
    """Specific validation for Premium"""
    return validate_numeric_input(
        amount, 
        "Premium", 
        data_type="int", 
        min_val=1, 
        max_val=9999999, 
        required=True
    )

def validate_chassis_number(chassis):
    """Specific validation for Chassis Number"""
    # Chassis numbers are typically alphanumeric, 17 characters
    return validate_text_input(
        chassis, 
        "Chassis Number", 
        min_length=10, 
        max_length=17, 
        required=True, 
        allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    )

def validate_policy_number(policy_no):
    """Specific validation for Policy Number"""
    return validate_text_input(
        policy_no, 
        "Policy Number", 
        min_length=5, 
        max_length=50, 
        required=True, 
        allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/-_"
    )

def validate_executive_name(executive):
    """Specific validation for Executive Name"""
    return validate_text_input(
        executive, 
        "Executive", 
        min_length=2, 
        max_length=100, 
        required=True, 
        allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz.-'"
    )

def validate_all_form_fields(form_data):
    """
    Validate all form fields at once
    Returns: (is_valid, errors_dict, validated_data)
    """
    errors = {}
    validated_data = {}
    
    # Validate Customer ID
    is_valid, value, error = validate_customer_id(form_data.get("CUST_ID"))
    if not is_valid:
        errors["CUST_ID"] = error
    else:
        validated_data["CUST_ID"] = value
    
    # Validate Executive
    is_valid, value, error = validate_executive_name(form_data.get("EXECUTIVE"))
    if not is_valid:
        errors["EXECUTIVE"] = error
    else:
        validated_data["EXECUTIVE"] = value
    
    # Validate Chassis Number
    is_valid, value, error = validate_chassis_number(form_data.get("CHASSIS_NO"))
    if not is_valid:
        errors["CHASSIS_NO"] = error
    else:
        validated_data["CHASSIS_NO"] = value
    
    # Validate Policy Number
    is_valid, value, error = validate_policy_number(form_data.get("POLICY_NO"))
    if not is_valid:
        errors["POLICY_NO"] = error
    else:
        validated_data["POLICY_NO"] = value
    
    # Validate Sum Insured
    is_valid, value, error = validate_sum_insured(form_data.get("SUM_INSURED"))
    if not is_valid:
        errors["SUM_INSURED"] = error
    else:
        validated_data["SUM_INSURED"] = value
    
    # Validate Premium
    is_valid, value, error = validate_premium(form_data.get("PREMIUM2"))
    if not is_valid:
        errors["PREMIUM2"] = error
    else:
        validated_data["PREMIUM2"] = value
    
    # Validate Vehicle Seats (optional)
    if form_data.get("VEH_SEATS"):
        is_valid, value, error = validate_vehicle_seats(form_data.get("VEH_SEATS"))
        if not is_valid:
            errors["VEH_SEATS"] = error
        else:
            validated_data["VEH_SEATS"] = value
    
    # Validate Model Year (optional)
    if form_data.get("MODEL_YEAR"):
        is_valid, value, error = validate_model_year(form_data.get("MODEL_YEAR"))
        if not is_valid:
            errors["MODEL_YEAR"] = error
        else:
            validated_data["MODEL_YEAR"] = value
    
    # Validate Nationality
    is_valid, value, error = validate_text_input(
        form_data.get("NATIONALITY"), 
        "Nationality", 
        min_length=2, 
        max_length=50, 
        required=True
    )
    if not is_valid:
        errors["NATIONALITY"] = error
    else:
        validated_data["NATIONALITY"] = value
    
    return len(errors) == 0, errors, validated_data

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
    
    st.caption("Fields marked with * are mandatory")

    # ====================================================== BROKER DETAILS FORM SECTION ======================================================
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

    
    # ====================================================== POLICY MANUAL FORM SECTION ======================================================
    # with st.form("policy_manual_form"):
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
    # Add real-time policy number validation
    if policy_no.strip():
        try:            
            # Check if policy exists
            check_query = f"SELECT COUNT(*) as count FROM New_Policy WHERE POLICY_NO = '{policy_no.strip()}'"
            result = fetch_data(check_query)
            
            if result and result[0]['count'] > 0:
                st.error("❌ This policy number already exists in the database!")
                st.warning("Please use a different policy number for New Business.")
            else:
                st.success("✅ Policy number is available")
        except Exception as e:
            st.warning(f"Could not verify policy number: {e}")


    policytype = col16.text_input("POLICY TYPE", value=defaults.get("POLICYTYPE", ""))
    sum_insured = col17.text_input("SUM INSURED *", value=float(defaults.get("SUM_INSURED", 0.0)))

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

    # col18, col19, col20 = st.columns(3)
    # premium2 = col18.text_input("PREMIUM *", value=int(defaults.get("PREMIUM2", 0)))
    # ✅ ENHANCED PREMIUM SECTION WITH PREDICT BUTTON
    st.markdown("#### Premium Calculation")
    col18, col19, col20 = st.columns([2, 1, 1])
    
    with col18:
        # ✅ INITIALIZE PREMIUM IN SESSION STATE IF NOT EXISTS
        if "predicted_premium" not in st.session_state:
            st.session_state.predicted_premium = defaults.get("PREMIUM2", 0)
        
        premium2 = st.text_input(
            "PREMIUM *", 
            value=str(st.session_state.predicted_premium),
            key="premium_input"
        )

    with col19:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


        if st.button("Predict Premium", type="secondary", use_container_width=True):
            # Collect all current form data for prediction
            # prediction_data = {
            #     "CUST_ID": cust_id.strip() if cust_id else "",
            #     "EXECUTIVE": executive.strip() if executive else "",
            #     "REGN": regn.strip() if regn else "",
            #     "BODY": body.strip() if body else "",
            #     "MAKE": make.strip() if make else "",
            #     "MODEL": model.strip() if model else "",
            #     "VEH_SEATS": veh_seats.strip() if veh_seats else "",
            #     "MODEL_YEAR": model_year.strip() if model_year else "",
            #     "CHASSIS_NO": chassis_no.strip() if chassis_no else "",
            #     "USE_OF_VEHICLE": use_of_vehicle.strip() if use_of_vehicle else "",
            #     "PRODUCT": product.strip() if product else "",
            #     "DRV_DOB": str(drv_dob) if drv_dob else "",
            #     "DRV_DLI": str(drv_dli) if drv_dli else "",
            #     "NATIONALITY": nationality.strip() if nationality else "",
            #     "POLICY_NO": policy_no.strip() if policy_no else "",
            #     "POLICYTYPE": policytype.strip() if policytype else "",
            #     "SUM_INSURED": sum_insured.strip() if sum_insured else "",
            #     "POL_ISSUE_DATE": str(pol_issue_date) if pol_issue_date else "",
            #     "POL_EFF_DATE": str(pol_eff_date) if pol_eff_date else "",
            #     "POL_EXPIRY_DATE": str(pol_expiry_date) if pol_expiry_date else ""
            # }
            payload = {
                "formatType": "dataframe",
                "orientation": "values",
                "inputs": [
                    [
                        47,
                        14080,
                        4,
                        27,
                        0,
                        177,
                        795,
                        13270,
                        20505,
                        107563,
                        749 ,
                        1,
                        348 ,
                        2004 ,
                        11711 ,
                        16 ,
                        821 ,
                        6
                    ]
                ]
            }

            # Call premium prediction API
            predicted_premium = predict_premium_api(payload)
            
            if predicted_premium is not None:
                st.session_state.predicted_premium = predicted_premium
                st.rerun()  # Refresh to update the input field
    
    with col20:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Clear", type="secondary", use_container_width=True):
            st.session_state.predicted_premium = 0
            st.rerun()
    # ====================================================== INSURER DETAILS FORM SECTION ======================================================
    st.subheader("Insurer Details")
    selected_facility = st.selectbox("Select Carrier *", facility_names, key="facility_select", index=facility_names.index(defaults.get("Facility_Name", "Select Facility")) if defaults and defaults.get("Facility_Name", "Select Facility") in facility_names else 0)
    
    # Display insurer details if a facility is selected
    if selected_facility and selected_facility != "Select Facility" and selected_facility != "No Facilities Found" and selected_facility != "Error loading facilities":
        # Get all insurers for the selected facility
        facility_insurers = [insurer for insurer in insurer_data if insurer["Facility_Name"] == selected_facility]
        
        if facility_insurers:
            st.markdown(f"**Carrier:** {selected_facility}")
            
            # Show facility details (using first record for facility info)
            first_record = facility_insurers[0]
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.text_input("Carrier ID", value=str(first_record.get("Facility_ID", "")), disabled=True, key="facility_id_display")
            with col_f2:
                st.text_input("Group Size", value=str(first_record.get("Group_Size", "")), disabled=True, key="group_size_display")
            

            st.markdown("**Insurers in this Carrier:**")
            
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


        
    # ====================================================== FORM SECTION ENDS ======================================================
        # -------- System Generated Fields (Submission_Date & Unique_ID) --------
        # We generate once per policy number change to keep stable while user edits.
        policy_no_current = policy_no.strip()
        session_key_root = "manual_policy_submission"
        stored_policy_no = st.session_state.get(f"{session_key_root}_policy_no")
        # if (stored_policy_no != policy_no_current) or (f"{session_key_root}_dt" not in st.session_state):
        if (stored_policy_no != policy_no_current):
            # (Re)generate
            submission_dt_obj = datetime.now()
            # .strftime("%Y-%m-%d %H:%M:%S.%f")
            st.session_state[f"{session_key_root}_dt"] = submission_dt_obj
            st.session_state[f"{session_key_root}_policy_no"] = policy_no_current
            st.session_state[f"{session_key_root}_uid"] = _build_unique_id(policy_no_current, submission_dt_obj)

        submission_dt_obj = st.session_state[f"{session_key_root}_dt"]
        unique_id_val = st.session_state[f"{session_key_root}_uid"]

        col_b1, _, col_b3 = st.columns(3)
        with col_b1:
            submit = st.form_submit_button("Submit")

        with col_b3:
            back = st.form_submit_button("Back")


        # Fix the conversion functions in policy_manual_form
        def to_int(val):
            if val is None or val == "":
                return None
            try:
                return int(float(val))  # Convert to float first to handle decimal strings
            except (ValueError, TypeError):
                return None

        def to_float(val):
            if val is None or val == "":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
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
            "SUM_INSURED": to_float(sum_insured),
            "POL_ISSUE_DATE": pol_issue_date,
            "PREMIUM2": to_int(premium2),
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": to_int(veh_seats),
            "PRODUCT": product,
            "POLICYTYPE": policytype,
            "NATIONALITY": nationality,
            # New fields
            # "Submission_Date": submission_dt_obj,          # datetime object (can convert when inserting DB)
            "Submission_Date": submission_dt_obj.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if isinstance(submission_dt_obj, datetime) else submission_dt_obj,
            "Unique_ID": unique_id_val
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
            

                # Validate all form fields
            is_valid, validation_errors, validated_data = validate_all_form_fields({
                "CUST_ID": cust_id,
                "EXECUTIVE": executive,
                "CHASSIS_NO": chassis_no,
                "POLICY_NO": policy_no,
                "SUM_INSURED": sum_insured,
                "PREMIUM2": premium2,
                "VEH_SEATS": veh_seats,
                "MODEL_YEAR": model_year,
                "NATIONALITY": nationality
            })
            
            if not is_valid:
                # Display all validation errors
                st.error("Please enter the correct data in the fields:")
                for field, error in validation_errors.items():
                    st.error(f"• {error}")
                return form_data, False, back
            
            # If validation passes, update form_data with validated values
            form_data.update(validated_data)
        
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

        def to_float(val):
            try:
                return float(val)
            except Exception:
                return 0.0
            
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
            "ORIGINAL_PREMIUM": int(original_premium) if original_premium else 0,
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
            if int(premium2) > int(original_premium):
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
        policytype = col17.selectbox("POLICY TYPE *", options=["TP", "COMP"], index=0)
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
        premium2 = col22.text_input("PREMIUM *", value=str(defaults.get("PREMIUM2", "")))

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