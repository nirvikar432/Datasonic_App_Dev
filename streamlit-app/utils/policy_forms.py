import streamlit as st
from datetime import date

def policy_manual_form(defaults=None):
        if defaults is None:
            defaults = {}
        with st.form("policy_manual_form"):
            # --- Mandatory Fields in 3 columns ---
            col1, col2, col3 = st.columns(3)
            cust_id = col1.number_input("CUST_ID *", value=defaults.get("CUST_ID", 1), step=1, format="%d", help="Mandatory")
            executive = col2.text_input("EXECUTIVE *", value=defaults.get("EXECUTIVE", ""), help="Mandatory")
            chassis_no = col3.text_input("CHASSIS_NO *", value=defaults.get("CHASSIS_NO", ""), help="Mandatory")
            policy_no = col1.text_input("POLICY_NO *", value=defaults.get("POLICY_NO", ""), help="Mandatory")
            pol_eff_date = col2.date_input("POL_EFF_DATE *", value=defaults.get("POL_EFF_DATE", date.today()), help="Mandatory")
            pol_expiry_date = col3.date_input("POL_EXPIRY_DATE *", value=defaults.get("POL_EXPIRY_DATE", date.today()), help="Mandatory")
            sum_insured = col1.number_input("SUM INSURED *", value=defaults.get("SUM_INSURED", 0.0), format="%.2f", help="Mandatory")
            premium2 = col2.number_input("PREMIUM2 *", value=defaults.get("PREMIUM2", 0.0), format="%.2f", help="Mandatory")
            pol_issue_date = col3.date_input("POL_ISSUE_DATE *", value=defaults.get("POL_ISSUE_DATE", date.today()), help="Mandatory")

            # --- Optional Fields in 3 columns ---
            col4, col5, col6 = st.columns(3)
            drv_dob = col4.date_input("DRV_DOB", value=defaults.get("DRV_DOB", date(2000,1,1)), help="Optional")
            drv_dli = col5.date_input("DRV_DLI", value=defaults.get("DRV_DLI", date(2000,1,1)), help="Optional")
            body = col6.text_input("BODY", value=defaults.get("BODY", ""))
            make = col4.text_input("MAKE", value=defaults.get("MAKE", ""))
            model = col5.text_input("MODEL", value=defaults.get("MODEL", ""))
            use_of_vehicle = col6.text_input("USE_OF_VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""))
            model_year = col4.number_input("MODEL_YEAR", value=defaults.get("MODEL_YEAR", 2024), step=1, format="%d")
            regn = col5.text_input("REGN", value=defaults.get("REGN", ""))
            veh_seats = col6.number_input("VEH_SEATS", value=defaults.get("VEH_SEATS", 1), step=1, format="%d")
            product = col4.text_input("PRODUCT", value=defaults.get("PRODUCT", ""))
            policytype = col5.text_input("POLICYTYPE", value=defaults.get("POLICYTYPE", ""))

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
            # Validation for mandatory fields
            mandatory_fields = [
                ("CUST_ID", cust_id),
                ("EXECUTIVE", executive),
                ("CHASSIS_NO", chassis_no),
                ("POLICY_NO", policy_no),
                ("POL_EFF_DATE", pol_eff_date),
                ("POL_EXPIRY_DATE", pol_expiry_date),
                ("SUM_INSURED", sum_insured),
                ("PREMIUM2", premium2),
                ("POL_ISSUE_DATE", pol_issue_date)
            ]
            missing = [name for name, val in mandatory_fields if (isinstance(val, str) and not val.strip()) or val is None]
            if submit and missing:
                st.error(f"Fill all the mandatory fields: {', '.join(missing)}.")
            return form_data, submit, back
    



def policy_cancel_form(defaults=None):
    if defaults is None:
        defaults = {}
    with st.form("policy_cancel_form"):
        # --- Mandatory Fields in 3 columns ---
        col1, col2, col3 = st.columns(3)
        cust_id = col1.number_input("CUST_ID *", value=defaults.get("CUST_ID", 1), step=1, format="%d", disabled=True)
        executive = col2.text_input("EXECUTIVE *", value=defaults.get("EXECUTIVE", ""), disabled=True)
        chassis_no = col3.text_input("CHASSIS_NO *", value=defaults.get("CHASSIS_NO", ""), disabled=True)
        policy_no = col1.text_input("POLICY_NO *", value=defaults.get("POLICY_NO", ""), disabled=True)
        pol_eff_date = col2.date_input("POL_EFF_DATE *", value=defaults.get("POL_EFF_DATE", date.today()), disabled=True)
        pol_expiry_date = col3.date_input("POL_EXPIRY_DATE *", value=defaults.get("POL_EXPIRY_DATE", date.today()), disabled=True)
        sum_insured = col1.number_input("SUM INSURED *", value=defaults.get("SUM_INSURED", 0.0), format="%.2f", disabled=True)
        premium2 = col2.number_input("PREMIUM2 *", value=defaults.get("PREMIUM2", 0.0), format="%.2f", help="Mandatory")
        pol_issue_date = col3.date_input("POL_ISSUE_DATE *", value=defaults.get("POL_ISSUE_DATE", date.today()), disabled=True)
        cancel_date = st.date_input("Cancellation Date", value=date.today(), key="cancel_date")

        # --- Optional Fields in 3 columns ---
        col4, col5, col6 = st.columns(3)
        drv_dob = col4.date_input("DRV_DOB", value=defaults.get("DRV_DOB", date(2000,1,1)), disabled=True)
        drv_dli = col5.date_input("DRV_DLI", value=defaults.get("DRV_DLI", date(2000,1,1)), disabled=True)
        body = col6.text_input("BODY", value=defaults.get("BODY", ""), disabled=True)
        make = col4.text_input("MAKE", value=defaults.get("MAKE", ""), disabled=True)
        model = col5.text_input("MODEL", value=defaults.get("MODEL", ""), disabled=True)
        use_of_vehicle = col6.text_input("USE_OF_VEHICLE", value=defaults.get("USE_OF_VEHICLE", ""), disabled=True)
        model_year = col4.number_input("MODEL_YEAR", value=defaults.get("MODEL_YEAR", 2024), step=1, format="%d", disabled=True)
        regn = col5.text_input("REGN", value=defaults.get("REGN", ""), disabled=True)
        veh_seats = col6.number_input("VEH_SEATS", value=defaults.get("VEH_SEATS", 1), step=1, format="%d", disabled=True)
        product = col4.text_input("PRODUCT", value=defaults.get("PRODUCT", ""), disabled=True)
        policytype = col5.text_input("POLICYTYPE", value=defaults.get("POLICYTYPE", ""), disabled=True)

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
        # Validation for mandatory fields
        mandatory_fields = [
            ("CUST_ID", cust_id),
            ("EXECUTIVE", executive),
            ("CHASSIS_NO", chassis_no),
            ("POLICY_NO", policy_no),
            ("POL_EFF_DATE", pol_eff_date),
            ("POL_EXPIRY_DATE", pol_expiry_date),
            ("SUM_INSURED", sum_insured),
            ("PREMIUM2", premium2),
            ("POL_ISSUE_DATE", pol_issue_date)
        ]
        missing = [name for name, val in mandatory_fields if (isinstance(val, str) and not val.strip()) or val is None]
        if submit and missing:
            st.error(f"Fill all the mandatory fields: {', '.join(missing)}.")
        return form_data, submit, back
