import streamlit as st

def broker_form(defaults=None):
    """Form for adding/editing broker information"""
    if defaults is None:
        defaults = {}
    
    with st.form("broker_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Broker Details Section
        st.subheader("Broker Information")
        col1, col2, col3 = st.columns(3)
        
        broker_id = col1.text_input("Broker ID *", value=defaults.get("Broker_ID", ""), 
                                   help="Format: BRKXX#### (e.g., BRKRG2617)")
        broker_name = col2.text_input("Broker Name *", value=defaults.get("Broker_Name", ""))
        commission = col3.number_input("Commission (%)", value=float(defaults.get("Commission", 0.0)), 
                                     min_value=0.0, max_value=50.0, step=0.01, format="%.2f")
        
        submit = st.form_submit_button("Submit Broker")
        back = st.form_submit_button("Back")
        
        form_data = {
            "Broker_ID": broker_id,
            "Broker_Name": broker_name,
            "Commission": commission
        }
        
        # Validation
        if submit:
            mandatory_fields = [
                ("Broker ID", broker_id),
                ("Broker Name", broker_name),
                ("Commission", commission)
            ]
            missing = [name for name, val in mandatory_fields if not val or not val.strip()]
            
            if missing:
                st.error(f"Please fill all mandatory fields: {', '.join(missing)}.")
                return form_data, False, back
            
            # Validate Broker ID format
            if not broker_id.startswith("BRK") or len(broker_id) != 9:
                st.error("Broker ID must follow format: BRKXX#### (e.g., BRKRG2617)")
                return form_data, False, back
        
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
        