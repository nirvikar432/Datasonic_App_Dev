import streamlit as st

def policy_manual_form(defaults=None):
    if defaults is None:
        defaults = {}
    with st.form("policy_manual_form"):
        cust_id = st.number_input("CUST_ID", value=defaults.get("CUST_ID", 1), step=1, format="%d")
        executive = st.text_input("EXECUTIVE", value=defaults.get("EXECUTIVE", ""))
        body = st.text_input("BODY", value=defaults.get("BODY", ""))
        make = st.text_input("MAKE", value=defaults.get("MAKE", ""))
        model = st.text_input("MODEL", value=defaults.get("MODEL", ""))
        use_of_vehicle = st.text_input("USE_OF_VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""))
        model_year = st.number_input("MODEL_YEAR", value=defaults.get("MODEL_YEAR", 2024), step=1, format="%d")
        chassis_no = st.text_input("CHASSIS_NO", value=defaults.get("CHASSIS_NO", ""))
        regn = st.text_input("REGN", value=defaults.get("REGN", ""))
        policy_no = st.text_input("POLICY_NO *", value=defaults.get("POLICY_NO", ""), help="Mandatory")
        pol_eff_date = st.date_input("POL_EFF_DATE", value=defaults.get("POL_EFF_DATE"))
        pol_expiry_date = st.date_input("POL_EXPIRY_DATE", value=defaults.get("POL_EXPIRY_DATE"))
        sum_insured = st.number_input("SUM_INSURED", value=defaults.get("SUM_INSURED", 0.0), format="%.2f")
        pol_issue_date = st.date_input("POL_ISSUE_DATE", value=defaults.get("POL_ISSUE_DATE"))
        premium2 = st.number_input("PREMIUM2", value=defaults.get("PREMIUM2", 0.0), format="%.2f")
        drv_dob = st.date_input("DRV_DOB", value=defaults.get("DRV_DOB"))
        drv_dli = st.date_input("DRV_DLI", value=defaults.get("DRV_DLI"))
        veh_seats = st.number_input("VEH_SEATS", value=defaults.get("VEH_SEATS", 1), step=1, format="%d")
        product = st.text_input("PRODUCT", value=defaults.get("PRODUCT", ""))
        policytype = st.text_input("POLICYTYPE", value=defaults.get("POLICYTYPE", ""))
        submit = st.form_submit_button("Submit")
        back = st.form_submit_button("Back")
        form_data = {
            "CUST_ID": cust_id,
            "EXECUTIVE": executive,
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
            "PREMIUM2": premium2,
            "DRV_DOB": drv_dob,
            "DRV_DLI": drv_dli,
            "VEH_SEATS": veh_seats,
            "PRODUCT": product,
            "POLICYTYPE": policytype
        }
        return form_data, submit, back