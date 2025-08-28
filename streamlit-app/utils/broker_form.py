import streamlit as st
import random
import string
from datetime import date, datetime, timedelta
import time
import re

from db_utils import fetch_data


# def generate_broker_id():
#     # Generate two random uppercase letters
#     random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
#     # Get current datetime as YYYYMMDDHHMMSS
#     dt_str = datetime.now().strftime("%Y%m%d%H%M%S")
#     # Format: BRKXXYYYYMMDDHHMMSS
#     return f"BRK{random_letters}{dt_str}"


def generate_broker_id(broker_name, fca_number):
    """
    Generate broker ID in format: BRK{Initial letters of first two words}{FCA Number}
    Example: "Lowe, Davis and Howell Brokers" + "1627" = "BRKLD1627"
    """
    try:
        # Clean and split broker name into words
        # Remove punctuation and extra spaces
        cleaned_name = re.sub(r'[^\w\s]', ' ', broker_name)
        words = [word.strip() for word in cleaned_name.split() if word.strip()]
        
        # Get first letters of first two words
        if len(words) >= 2:
            initials = (words[0][0] + words[1][0]).upper()
        elif len(words) == 1:
            # If only one word, use first two letters
            initials = words[0][:2].upper()
        else:
            # Fallback to random letters if no valid words
            initials = ''.join(random.choices(string.ascii_uppercase, k=2))
        
        # Clean FCA number (remove any non-digits)
        clean_fca = ''.join(c for c in str(fca_number) if c.isdigit())
        
        # Generate broker ID
        broker_id = f"BRK{initials}{clean_fca}"
        
        return broker_id
        
    except Exception as e:
        print(f"DEBUG: Error generating broker ID: {e}")
        # Fallback to original timestamp method
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        dt_str = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"BRK{random_letters}{dt_str}"



def broker_form(defaults=None):
    """Form for adding/editing broker information"""
    if defaults is None:
        defaults = {}
    
    with st.form("broker_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Broker Details Section
        st.subheader("Broker Information")  
        col1, col2, col3 = st.columns(3)

        broker_name = col1.text_input("Broker Name *", value=defaults.get("Broker_Name", ""))
        commission = col2.number_input("Commission (%) *", value=float(defaults.get("Commission", 0.0)), 
                                    min_value=0.0, max_value=50.0, step=0.01, format="%.2f")
        date_of_onboarding = col3.date_input("Date of Onboarding *", 
                                            value=defaults.get("Date_Of_Onboarding", None))

        col4, col5, col6 = st.columns(3)
        longevity_years = col4.number_input("Longevity (Years) *", value=int(defaults.get("Longevity_Years", 0)), min_value=0)
        fca_registration = col5.text_input("FCA Registration Number *", 
                                        value=defaults.get("FCA_Registration_Number", ""))
        broker_type = col6.selectbox("Broker Type *", 
                                    options=["Retail", "Wholesale", "Reinsurance", "Coverholder"],
                                    index=defaults.get("Broker_Type_Index", 0))

        col7,_,_ = st.columns(3)
        

        market_access = col7.selectbox("Market Access *", 
                                    options=["Lloyd’s", "Company Market", "Both"],
                                    index=defaults.get("Market_Access_Index", 0))
        
        col8 = st.columns(1)[0]
        delegated_authority = col8.checkbox("Delegated Authority", 
                                            value=defaults.get("Delegated_Authority", False))

        
        submit = st.form_submit_button("Submit Broker")
        back = st.form_submit_button("Back")

        form_data = {
            "Broker_ID": None,
            "Broker_Name": broker_name,
            "Commission": commission,
            "Date_Of_Onboarding": date_of_onboarding,
            "FCA_Registration_Number": fca_registration,
            "Broker_Type": broker_type,
            "Market_Access": market_access,
            "Delegated_Authority": delegated_authority,
            "Longevity_Years": longevity_years,
            "Date_Of_Expiry": (date_of_onboarding + timedelta(days=longevity_years * 365)).strftime("%Y-%m-%d") if date_of_onboarding else None,
            "Status": "Active" if date_of_onboarding and (date_of_onboarding + timedelta(days=longevity_years * 365)) > date.today() else "Completed",
            "Submission_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "GUID": None
        }
        
        # Validation
        if submit:
            mandatory_fields = [
                ("Broker Name", broker_name),
                ("Commission", commission),
                ("Date of Onboarding", date_of_onboarding),
                ("FCA Registration Number", fca_registration),
                ("Broker Type", broker_type),
                ("Market Access", market_access),
                ("Longevity (Years)", longevity_years)
            ]
            missing = [
                name for name, val in mandatory_fields
                if (isinstance(val, str) and not val.strip()) or (not isinstance(val, str) and not val)
            ]            
            if missing:
                st.error(f"Please fill all mandatory fields: {', '.join(missing)}.")
                return form_data, False, back
            
            # Check if FCA Registration Number exists
            query = f"SELECT Broker_ID, Broker_Name FROM Broker WHERE FCA_Registration_Number = '{fca_registration}'"
            result = fetch_data(query)

            if result and fca_registration.strip():
                # FCA Registration exists, use the existing Broker ID and Name from DB
                existing_broker_id = result[0]["Broker_ID"]
                existing_name = result[0]["Broker_Name"]
                form_data["Broker_ID"] = existing_broker_id 
                form_data["Broker_Name"] = existing_name            
            else:
                # broker_id = generate_broker_id()
                broker_id = generate_broker_id(broker_name, fca_registration)
                form_data["Broker_ID"] = broker_id
                print(f"DEBUG: Generated new Broker_ID: {broker_id} from name '{broker_name}' and FCA '{fca_registration}'")


        return form_data, submit, back
    

def broker_summary_display(broker_data):
    """Display broker summary in a formatted layout"""
    st.markdown("#### Broker Summary")
    
    col1 = st.columns(1)[0]
    
    with col1:
        st.subheader("Broker Information")
        st.write(f"**Broker ID:** {broker_data['Broker_ID']}")
        st.write(f"**Broker Name:** {broker_data['Broker_Name']}")
        st.write(f"**Commission:** {broker_data['Commission']:.2f}%")
        st.write(f"**Date of Onboarding:** {broker_data['Date_Of_Onboarding']}")
        st.write(f"**FCA Registration Number:** {broker_data['FCA_Registration_Number']}")
        st.write(f"**Broker Type:** {broker_data['Broker_Type']}")
        st.write(f"**Market Access:** {broker_data['Market_Access']}")
        st.write(f"**Delegated Authority:** {'Yes' if broker_data['Delegated_Authority'] else 'No'}")
        st.write(f"**Longevity (Years):** {broker_data['Longevity_Years']}")
        st.write(f"**Date of Expiry:** {broker_data['Date_Of_Expiry']}")
        st.write(f"**Status:** {broker_data['Status']}")

