import streamlit as st
from db_utils import fetch_data



def check_facility_exists(facility_id):
    """Check if Facility ID already exists in database"""
    try:
        query = "SELECT COUNT(*) FROM insurer WHERE Facility_ID = ?"
        result = fetch_data(f"SELECT COUNT(*) as count FROM insurer WHERE Facility_ID = '{facility_id}'")
        if result and result[0]['count'] > 0:
            return True
        return False
    except Exception:
        return False

def insurer_form(defaults=None):
    """Form for adding/editing insurer information"""
    if defaults is None:
        defaults = {}
    
    # Initialize session state for group size if not exists
    if "insurer_group_size" not in st.session_state:
        st.session_state.insurer_group_size = defaults.get("Group_Size", 1)
    
    # Facility Details Section (outside the main form)
    st.subheader("Facility Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # facility_id = st.text_input("Facility ID *", value=defaults.get("Facility_ID", ""),
        #                            help="Format: FACXXX (e.g., FAC001)", key="facility_id_input")

        facility_id = st.text_input("Facility ID *", value=defaults.get("Facility_ID", ""),
                                help="Format: FACXXX (e.g., FAC001)", key="facility_id_input")
        
        # Real-time validation
        if facility_id and len(facility_id) >= 3:
            if check_facility_exists(facility_id):
                st.warning(f"⚠️ Facility ID '{facility_id}' already exists!")
            else:
                st.success(f"✅ Facility ID '{facility_id}' is available")
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
            col_id, col_name, col_participation = st.columns(3)
            
            # Get default values for this insurer if available
            insurer_defaults = defaults.get("insurers", [])
            current_insurer = insurer_defaults[i] if i < len(insurer_defaults) else {}
            
            insurer_id = col_id.text_input(
                f"Insurer ID {i+1} *", 
                value=current_insurer.get("Insurer_ID", ""),
                help="Format: INSXX#### (e.g., INSBI5019)",
                key=f"insurer_id_{i}"
            )
            
            insurer_name = col_name.text_input(
                f"Insurer Name {i+1} *", 
                value=current_insurer.get("Insurer_Name", ""),
                key=f"insurer_name_{i}"
            )
            
            participation = col_participation.number_input(
                f"Participation % {i+1}", 
                value=float(current_insurer.get("Participation", 0.0)), 
                min_value=0.0, 
                max_value=100.0, 
                step=0.01, 
                format="%.2f",
                key=f"participation_{i}"
            )
            
            total_participation += participation
            
            insurers_data.append({
                "Insurer_ID": insurer_id,
                "Insurer_Name": insurer_name,
                "Participation": participation
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
            "Facility_ID": facility_id,
            "Facility_Name": facility_name,
            "Group_Size": group_size,
            "insurers": insurers_data,
            "Total_Participation": total_participation
        }
        
        # Validation
        if submit:
            # Validate facility information
            mandatory_facility_fields = [
                ("Facility ID", facility_id),
                ("Facility Name", facility_name),
                ("Group Size", str(group_size))
            ]
            missing_facility = [name for name, val in mandatory_facility_fields if not val or not str(val).strip()]
            
            if missing_facility:
                st.error(f"Please fill all mandatory facility fields: {', '.join(missing_facility)}.")
                return form_data, False, back
            
            # Validate Facility ID format
            if not facility_id.startswith("FAC") or len(facility_id) != 6:
                st.error("Facility ID must follow format: FACXXX (e.g., FAC001)")
                return form_data, False, back
            
            # Validate each insurer
            for i, insurer in enumerate(insurers_data):
                # Check mandatory fields for each insurer
                if not insurer["Insurer_ID"] or not insurer["Insurer_ID"].strip():
                    st.error(f"Insurer ID for Insurer {i+1} is mandatory.")
                    return form_data, False, back
                
                if not insurer["Insurer_Name"] or not insurer["Insurer_Name"].strip():
                    st.error(f"Insurer Name for Insurer {i+1} is mandatory.")
                    return form_data, False, back
                
                # Validate Insurer ID format
                if not insurer["Insurer_ID"].startswith("INS") or len(insurer["Insurer_ID"]) != 9:
                    st.error(f"Insurer ID {i+1} must follow format: INSXX#### (e.g., INSBI5019)")
                    return form_data, False, back
                
                # Check for duplicate Insurer IDs
                for j, other_insurer in enumerate(insurers_data):
                    if i != j and insurer["Insurer_ID"] == other_insurer["Insurer_ID"]:
                        st.error(f"Duplicate Insurer ID found: {insurer['Insurer_ID']} (Insurer {i+1} and {j+1})")
                        return form_data, False, back
            
            # Validate total participation for multiple insurers
            if group_size > 1 and abs(total_participation - 100.0) > 0.01:  # Allow small floating point differences
                st.error(f"Total participation must equal 100%. Current total: {total_participation:.2f}%")
                return form_data, False, back
            
            # If single insurer, participation can be any value
            if group_size == 1 and total_participation <= 0:
                st.error("Participation percentage must be greater than 0.")
                return form_data, False, back
        
        return form_data, submit, back


def insurer_form_preview():
    """Preview the insurer form structure without submission"""
    st.subheader("Insurer Form Preview")
    
    # Group size selector
    group_size = st.number_input("Select Group Size to Preview Form", 
                                value=1, min_value=1, max_value=10, step=1)
    
    st.markdown(f"**This will create {group_size} insurer input field(s):**")
    
    # Show preview of what fields will be created
    for i in range(group_size):
        with st.expander(f"Insurer {i+1} Fields"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.text_input(f"Insurer ID {i+1}", disabled=True, placeholder="INSXX####")
            with col2:
                st.text_input(f"Insurer Name {i+1}", disabled=True, placeholder="Insurance Company Name")
            with col3:
                st.number_input(f"Participation % {i+1}", disabled=True, value=0.0)
    
    if group_size > 1:
        st.info(f"💡 For {group_size} insurers, the total participation should equal 100%")


def reset_insurer_form():
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
        st.write(f"**Total Participation:** {insurer_data.get('Total_Participation', 0):.2f}%")
    
    with col2:
        st.subheader("Insurers in this Facility")
        insurers = insurer_data.get('insurers', [])
        
        for i, insurer in enumerate(insurers):
            st.markdown(f"**Insurer {i+1}:**")
            st.write(f"  • ID: {insurer['Insurer_ID']}")
            st.write(f"  • Name: {insurer['Insurer_Name']}")
            st.write(f"  • Participation: {insurer['Participation']:.2f}%")
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