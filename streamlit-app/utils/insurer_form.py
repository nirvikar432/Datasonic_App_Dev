import streamlit as st
import random
import string
from db_utils import fetch_data
from datetime import date, datetime, timedelta
import time

def generate_facility_id():
    """Generate facility ID by incrementing the last used facility ID by 1"""
    try:
        # Query to get the last facility ID, sorted in descending order
        query = "SELECT TOP 1 Facility_ID FROM insurer ORDER BY Facility_ID DESC"
        result = fetch_data(query)
        
        if result and result[0]['Facility_ID']:
            # Extract the existing facility ID
            last_id = result[0]['Facility_ID']
            
            # Parse the existing ID - assuming format is "FACNNN" where NNN is a number
            prefix = "FAC"
            if last_id.startswith(prefix) and len(last_id) >= len(prefix):
                # Extract the numeric part
                num_part = last_id[len(prefix):]
                
                try:
                    # Try to convert to integer and increment
                    next_num = int(num_part) + 1
                    # Format with leading zeros to maintain consistent length
                    # If numpart was "001", we want to maintain 3 digits: "002"
                    next_id = f"{prefix}{next_num:0{len(num_part)}d}"
                    return next_id
                except ValueError:
                    # If the numeric part isn't a valid integer, fall back to default
                    pass
        
        # Default case: If no previous ID exists or can't be parsed
        return "FAC001"  # Start with FAC001
        
    except Exception as e:
        # Log the error and return default ID
        print(f"Error generating facility ID: {e}")
        return "FAC001"  # Default fallback

def generate_insurer_id():
    # Generate two random uppercase letters
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    # Get current datetime as YYYYMMDDHHMMSS
    dt_str = datetime.now().strftime("%Y%m%d%H%M%S")
    # Format: INSXXYYYYMMDDHHMMSS
    return f"INS{random_letters}{dt_str}"

# def check_facility_exists(facility_id):
#     """Check if Facility ID already exists in database"""
#     try:
#         query = "SELECT COUNT(*) FROM insurer WHERE Facility_ID = ?"
#         result = fetch_data(f"SELECT COUNT(*) as count FROM insurer WHERE Facility_ID = '{facility_id}'")
#         if result and result[0]['count'] > 0:
#             return True
#         return False
#     except Exception:
#         return False

def insurer_form(defaults=None):
    """Form for adding/editing insurer information"""
    if defaults is None:
        defaults = {}
    
    # Initialize session state for group size if not exists
    if "insurer_group_size" not in st.session_state:
        st.session_state.insurer_group_size = defaults.get("Group_Size", 1)
    
    # Facility Details Section (outside the main form)
    st.subheader("Facility Information")
    col2, col3, col1, col4 = st.columns(4)

    # with col1:
        # facility_id = st.text_input("Facility ID *", value=defaults.get("Facility_ID", ""),
        #                         help="Format: FACXXX (e.g., FAC001)", key="facility_id_input")
        
        # Real-time validation
        # if facility_id and len(facility_id) >= 3:
        #     if check_facility_exists(facility_id):
        #         st.warning(f"⚠️ Facility ID '{facility_id}' already exists!")
        #     else:
        #         st.success(f"✅ Facility ID '{facility_id}' is available")
    with col1:
        date_of_onboarding = st.date_input(
                "Date of Onboarding *", 
                value=defaults.get("Date_Of_Onboarding", date.today())
            )
    with col2:
        facility_name = st.text_input("Facility Name *", value=defaults.get("Facility_Name", ""),
                                     key="facility_name_input")
    with col3:
        # Group size selector that updates the form dynamically
        group_size = st.number_input("Group Size *", 
                                    value=int(st.session_state.insurer_group_size), 
                                    min_value=1, max_value=50, step=1,
                                    key="group_size_input",
                                    help="Number of insurers in this facility")
    
    with col4:
        longevity_years = st.number_input("Longevity (Years)", value=int(defaults.get("Longevity_Years", 0)), min_value=0, key=f"longevity_years")


        
        # Update session state when group size changes
        if group_size != st.session_state.insurer_group_size:
            st.session_state.insurer_group_size = group_size
            st.rerun()
    
    # Main form with dynamic insurer fields
    with st.form("insurer_form"):
        st.caption("Fields marked with * are mandatory")
        
        # Dynamic Insurer Details Section based on Group Size
        st.subheader(f"Insurer Information (Total: {group_size} Insurers)")
        
        insurers_data = []
        total_participation = 0.0
        
        # Create dynamic insurer fields based on group size
        for i in range(group_size):
            st.markdown(f"**Insurer {i+1}**")
            
            # Create columns for each insurer
            col_name, col_participation = st.columns(2)
            
            # Get default values for this insurer if available
            insurer_defaults = defaults.get("insurers", [])
            current_insurer = insurer_defaults[i] if i < len(insurer_defaults) else {}
            
            insurer_id = generate_insurer_id()
            
            insurer_name = col_name.text_input(
                f"Insurer Name *", 
                value=current_insurer.get("Insurer_Name", ""),
                key=f"insurer_name_{i}"
            )
            
            participation = col_participation.number_input(
                f"Participation % *", 
                value=float(current_insurer.get("Participation", 0.0)), 
                min_value=0.0, 
                max_value=100.0, 
                step=0.01, 
                format="%.2f",
                key=f"participation_{i}"
            )
            
            total_participation += participation

            col_fca, col_type = st.columns(2)
            
            fca_registration = col_fca.text_input(
                f"FCA Registration Number *", 
                value=current_insurer.get("FCA_Registration_Number", ""),
                key=f"fca_registration_{i}"
            )
            insurer_type = col_type.selectbox(
                f"Insurer Type *", 
                options=["Direct", "Reinsurer", "Broker"],
                index=current_insurer.get("Insurer_Type_Index", 0),
                key=f"insurer_type_{i}"
            )

            # longevity_years = col_long_year.number_input("Longevity (Years)", value=int(defaults.get("Longevity_Years", 0)), min_value=0, key=f"longevity_years_{i}")
            delegated_authority = st.checkbox(
                f"Delegated Authority *", 
                value=current_insurer.get("Delegated_Authority", False),
                key=f"delegated_authority_{i}"
            )
            # lead_insurer = st.checkbox(
            #     f"Lead Insurer *", 
            #     value=current_insurer.get("LeadInsurer", False),
            #     key=f"lead_insurer_{i}"
            # )

            
            insurers_data.append({
                "Insurer_ID": insurer_id,
                "Insurer_Name": insurer_name,
                "Participation": participation,
                "FCA_Registration_Number": fca_registration,
                "Insurer_Type": insurer_type,
                # "Longevity_Years": longevity_years,
                "Delegated_Authority": delegated_authority,
                "Status": "Active" if date_of_onboarding and (date_of_onboarding + timedelta(days=longevity_years * 365)) > date.today() else "Completed",
                "Date_Of_Expiry": (date_of_onboarding + timedelta(days=longevity_years * 365)).strftime("%Y-%m-%d") if date_of_onboarding else None,
            })
            
            # Add a separator between insurers (except for the last one)
            if i < group_size - 1:
                st.markdown("---")
        
        # Show total participation
        if group_size > 1:
            # Create columns for participation display
            part_col1, part_col2 = st.columns([3, 1])
            with part_col1:
                st.markdown(f"**Total Participation: {total_participation:.2f}%**")
            with part_col2:
                if abs(total_participation - 100.0) <= 0.01:
                    st.success("✅ 100%")
                else:
                    st.error(f"❌ {total_participation:.2f}%")
            
            if abs(total_participation - 100.0) > 0.01:
                st.warning(f"⚠️ Total participation should equal 100%. Current total: {total_participation:.2f}%")
        
        submit = st.form_submit_button("Submit Insurers", type="primary")
        back = st.form_submit_button("Back")
        
        # Get facility data from session state inputs
        form_data = {
            "Date_Of_Onboarding": date_of_onboarding,
            "Facility_ID": generate_facility_id(),
            "Facility_Name": facility_name,
            "Longevity_Years": longevity_years,
            "Group_Size": group_size,
            "insurers": insurers_data,
            "Total_Participation": total_participation
        }
        
        # Validation
        if submit:
            # Validate facility information
            mandatory_facility_fields = [
                ("Facility Name", facility_name),
                ("Group Size", str(group_size))
            ]
            missing_facility = [name for name, val in mandatory_facility_fields if not val or not str(val).strip()]
            
            if missing_facility:
                st.error(f"Please fill all mandatory facility fields: {', '.join(missing_facility)}.")
                return form_data, False, back
            
            # Validate each insurer
            for i, insurer in enumerate(insurers_data):
                # Check mandatory fields for each insurer
                # if not insurer["Insurer_ID"] or not insurer["Insurer_ID"].strip():
                #     st.error(f"Insurer ID for Insurer {i+1} is mandatory.")
                #     return form_data, False, back
                
                if not insurer["Insurer_Name"] or not insurer["Insurer_Name"].strip():
                    st.error(f"Insurer Name for Insurer {i+1} is mandatory.")
                    return form_data, False, back
                
                # Validate Insurer ID format
                # if not insurer["Insurer_ID"].startswith("INS") or len(insurer["Insurer_ID"]) != 9:
                #     st.error(f"Insurer ID {i+1} must follow format: INSXX#### (e.g., INSBI5019)")
                #     return form_data, False, back
                
                # Check for duplicate Insurer IDs
                # for j, other_insurer in enumerate(insurers_data):
                #     if i != j and insurer["Insurer_ID"] == other_insurer["Insurer_ID"]:
                #         st.error(f"Duplicate Insurer ID found: {insurer['Insurer_ID']} (Insurer {i+1} and {j+1})")
                #         return form_data, False, back
            
            # Validate total participation for multiple insurers
            if group_size > 1 and abs(total_participation - 100.0) > 0.01:  # Allow small floating point differences
                st.error(f"Total participation must equal 100%. Current total: {total_participation:.2f}%")
                return form_data, False, back
            
            # If single insurer, participation can be any value
            if group_size == 1 and total_participation <= 0:
                st.error("Participation percentage must be greater than 0.")
                return form_data, False, back
        
        return form_data, submit, back


# def insurer_form_preview():
    # """Preview the insurer form structure without submission"""
    # st.subheader("Insurer Form Preview")
    
    # # Group size selector
    # group_size = st.number_input("Select Group Size to Preview Form", 
    #                             value=1, min_value=1, max_value=10, step=1)
    
    # st.markdown(f"**This will create {group_size} insurer input field(s):**")
    
    # # Show preview of what fields will be created
    # for i in range(group_size):
    #     with st.expander(f"Insurer {i+1} Fields"):
    #         col1, col2, col3 = st.columns(3)
    #         with col1:
    #             st.text_input(f"Insurer ID {i+1}", disabled=True, placeholder="INSXX####")
    #         with col2:
    #             st.text_input(f"Insurer Name {i+1}", disabled=True, placeholder="Insurance Company Name")
    #         with col3:
    #             st.number_input(f"Participation % {i+1}", disabled=True, value=0.0)
    #         col4, col5, col6 = st.columns(3)
    #         with col4:
    #             st.date_input(f"Date of Onboarding {i+1}", disabled=True)
    #         with col5:
    #             st.text_input(f"FCA Registration Number {i+1}", disabled=True, placeholder="FCA123456")
    #         with col6:
    #             st.selectbox(f"Insurer Type {i+1}", 
    #                         options=["Direct", "Reinsurer", "Broker"], 
    #                         index=0, disabled=True)
    #         st.checkbox(f"Delegated Authority {i+1}", disabled=True)
    #         st.checkbox(f"Lead Insurer {i+1}", disabled=True)
    
    # if group_size > 1:
    #     st.info(f"💡 For {group_size} insurers, the total participation should equal 100%")


# def reset_insurer_form():
    """Reset the insurer form session state"""
    if "insurer_group_size" in st.session_state:
        del st.session_state.insurer_group_size
    
    # Clear any other insurer form related session state
    keys_to_remove = [key for key in st.session_state.keys() if key.startswith(('insurer_', 'facility_', 'group_size_'))]
    for key in keys_to_remove:
        del st.session_state[key]


def insurer_summary_display(insurer_data):
    """Display insurer summary in a formatted layout"""
    st.markdown("#### Insurer Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Facility Information")
        st.write(f"**Facility ID:** {insurer_data['Facility_ID']}")
        st.write(f"**Facility Name:** {insurer_data['Facility_Name']}")
        st.write(f"**Group Size:** {insurer_data['Group_Size']}")
        st.write(f"**Date of Onboarding:** {insurer_data['Date_Of_Onboarding']}")
        st.write(f"**Longevity (Years):** {insurer_data['Longevity_Years']}")

        st.write(f"**Total Participation:** {insurer_data.get('Total_Participation', 0):.2f}%")
    
    with col2:
        st.subheader("Insurers in this Facility")
        insurers = insurer_data.get('insurers', [])
        if insurers:
            lead_insurer_id = max(insurers, key=lambda x: x.get('Participation', 0)).get('Insurer_ID')

        # Set LeadInsurer flag for each insurer
        for insurer in insurers:
            insurer['LeadInsurer'] = (insurer.get('Insurer_ID') == lead_insurer_id)

        for i, insurer in enumerate(insurers):
            st.markdown(f"**Insurer {i+1}:**")
            st.write(f"  • ID: {insurer['Insurer_ID']}")
            st.write(f"  • Name: {insurer['Insurer_Name']}")
            st.write(f"  • Participation: {insurer['Participation']:.2f}%")
            st.write(f"  • FCA Registration Number: {insurer['FCA_Registration_Number']}")
            st.write(f"  • Insurer Type: {insurer['Insurer_Type']}")
            st.write(f"  • Lead Insurer: {'Yes' if insurer.get('LeadInsurer') else 'No'}")
            st.write(f"  • Delegated Authority: {'Yes' if insurer['Delegated_Authority'] else 'No'}")
            st.write(f"  • Status: {insurer['Status']}")
            st.write(f"  • Date of Expiry: {insurer['Date_Of_Expiry']}")
            if i < len(insurers) - 1:
                st.markdown("---")


def facility_insurer_breakdown_display(facility_data):
    """Display detailed breakdown of facility and its insurers"""
    st.markdown("#### Facility & Insurer Breakdown")
    
    # Facility Overview
    st.subheader("📋 Facility Overview")
    facility_col1, facility_col2, facility_col3 = st.columns(3)
    
    with facility_col1:
        st.metric("Facility ID", facility_data['Facility_ID'])
    with facility_col2:
        st.metric("Group Size", facility_data['Group_Size'])
    with facility_col3:
        total_participation = facility_data.get('Total_Participation', 0)
        st.metric("Total Participation", f"{total_participation:.2f}%", 
                 delta="Perfect!" if abs(total_participation - 100.0) <= 0.01 else f"Off by {abs(100 - total_participation):.2f}%")
    
    st.write(f"**Facility Name:** {facility_data['Facility_Name']}")
    
    # Insurers Breakdown
    st.subheader("🏢 Insurers Breakdown")
    
    insurers = facility_data.get('insurers', [])
    
    if insurers:
        # Create a table-like display
        header_col1, header_col2, header_col3, header_col4 = st.columns([1, 2, 3, 1.5])
        
        with header_col1:
            st.markdown("**#**")
        with header_col2:
            st.markdown("**Insurer ID**")
        with header_col3:
            st.markdown("**Insurer Name**")
        with header_col4:
            st.markdown("**Participation**")
        
        st.markdown("---")
        
        for i, insurer in enumerate(insurers):
            row_col1, row_col2, row_col3, row_col4 = st.columns([1, 2, 3, 1.5])
            
            with row_col1:
                st.write(f"{i+1}")
            with row_col2:
                st.code(f"{insurer['Insurer_ID']}")
            with row_col3:
                st.write(f"{insurer['Insurer_Name']}")
            with row_col4:
                participation = insurer['Participation']
                if participation > 0:
                    st.success(f"{participation:.2f}%")
                else:
                    st.error(f"{participation:.2f}%")
        
        # Participation Chart (if multiple insurers)
        if len(insurers) > 1:
            st.subheader("📊 Participation Distribution")
            
            # Create data for chart
            import pandas as pd
            chart_data = pd.DataFrame({
                'Insurer ID': [ins['Insurer_ID'] for ins in insurers],
                'Insurer Name': [ins['Insurer_Name'][:20] + "..." if len(ins['Insurer_Name']) > 20 else ins['Insurer_Name'] for ins in insurers],
                'Participation': [ins['Participation'] for ins in insurers]
            })
            
            # Display chart
            st.bar_chart(chart_data.set_index('Insurer ID')['Participation'])
            
            # Display data table
            st.subheader("📋 Participation Table")
            st.dataframe(chart_data, use_container_width=True)
    else:
        st.info("No insurers found for this facility.")