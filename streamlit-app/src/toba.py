import streamlit as st
import time
from datetime import datetime
import pandas as pd


from broker_form import (
    broker_form,
    broker_summary_display
)
from insurer_form import (
    insurer_form,
    insurer_summary_display
)

from insurer_broker_upload import (
    load_data_from_json,
    show_insurer_broker_form
)

from db_utils import insert_broker, insert_insurer, fetch_data


def toba_tab():
    """TOBA (Terms of Business Agreement) management tab"""
    st.header("TOBA - Broker & Insurer Management")
    
    if "toba_page" not in st.session_state:
        st.session_state.toba_page = "main"
    if "toba_entry_type" not in st.session_state:
        st.session_state.toba_entry_type = None
    if "show_broker_summary" not in st.session_state:
        st.session_state.show_broker_summary = False
    if "show_insurer_summary" not in st.session_state:
        st.session_state.show_insurer_summary = False

    # Working on upload status
    if "toba_upload_status" not in st.session_state:
        st.session_state.toba_upload_status = None

    if st.session_state.toba_page == "main":
        st.markdown("### Select Entry Type")
        # Create three columns for better layout
        _, col1, _, col2, _, col3, _ = st.columns(7)

        with col1:
            st.markdown("##### Broker Management")
            if st.button("Add New Broker", use_container_width=True, type="primary"):
                st.session_state.toba_entry_type = "Broker"
                st.session_state.toba_page = "form"
                st.session_state.show_broker_summary = False
                st.rerun()
            
            if st.button("View All Brokers", use_container_width=True):
                st.session_state.toba_page = "view_brokers"
                st.rerun()
        
        with col2:
            st.markdown("##### Insurer Management")
            if st.button("Add New Insurer", use_container_width=True, type="primary"):
                st.session_state.toba_entry_type = "Insurer"
                st.session_state.toba_page = "form"
                st.session_state.show_insurer_summary = False
                st.rerun()
            
            if st.button("View All Insurers", use_container_width=True):
                st.session_state.toba_page = "view_insurers"
                st.rerun()
        
        # Working on upload status
        with col3:
            st.markdown("##### Upload TOBA")
            if st.button("Upload", use_container_width=True, type="primary", key="toba_upload_btn"):
                st.session_state.toba_page = "upload_toba"
                st.rerun()

            if st.button("Sync", use_container_width=True):
                st.session_state.toba_page = "sync_toba"
                st.rerun()

    elif st.session_state.toba_page == "form":
        entry_type = st.session_state.toba_entry_type
        
        if entry_type == "Broker":
            if not st.session_state.show_broker_summary:
                # Show broker form
                form_data, submit, back = broker_form()
                
                if submit:
                    try:
                        insert_broker(form_data)
                        st.session_state.broker_data = form_data
                        st.session_state.show_broker_summary = True
                        st.success("Broker added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add broker: {e}")
                
                if back:
                    st.session_state.toba_page = "main"
                    st.session_state.show_broker_summary = False
                    st.rerun()
            
            else:
                # Show broker summary
                broker_summary_display(st.session_state.broker_data)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    add_another = st.button("Add Another Broker")
                with col2:
                    view_all = st.button("View All Brokers")
                with col3:
                    back_to_main = st.button("Back to Main")
                
                if add_another:
                    st.session_state.show_broker_summary = False
                    if "broker_data" in st.session_state:
                        del st.session_state.broker_data
                    st.rerun()
                
                if view_all:
                    st.session_state.toba_page = "view_brokers"
                    st.session_state.show_broker_summary = False
                    st.rerun()
                
                if back_to_main:
                    st.session_state.toba_page = "main"
                    st.session_state.show_broker_summary = False
                    if "broker_data" in st.session_state:
                        del st.session_state.broker_data
                    st.rerun()
        
        elif entry_type == "Insurer":
            if not st.session_state.show_insurer_summary:
                # Show insurer form
                form_data, submit, back = insurer_form()
                
                if submit:
                    try:
                        insert_insurer(form_data)
                        st.session_state.insurer_data = form_data
                        st.session_state.show_insurer_summary = True
                        st.success("Insurer added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to add insurer: {e}")
                
                if back:
                    st.session_state.toba_page = "main"
                    st.session_state.show_insurer_summary = False
                    st.rerun()
            
            else:
                # Show insurer summary
                insurer_summary_display(st.session_state.insurer_data)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    add_another = st.button("Add Another Insurer")
                with col2:
                    view_all = st.button("View All Insurers")
                with col3:
                    back_to_main = st.button("Back to Main")
                
                if add_another:
                    st.session_state.show_insurer_summary = False
                    if "insurer_data" in st.session_state:
                        del st.session_state.insurer_data
                    st.rerun()
                
                if view_all:
                    st.session_state.toba_page = "view_insurers"
                    st.session_state.show_insurer_summary = False
                    st.rerun()
                
                if back_to_main:
                    st.session_state.toba_page = "main"
                    st.session_state.show_insurer_summary = False
                    if "insurer_data" in st.session_state:
                        del st.session_state.insurer_data
                    st.rerun()

    elif st.session_state.toba_page == "view_brokers":
        st.subheader("All Brokers")
        
        try:
            brokers = fetch_data("SELECT * FROM Broker")
            if brokers:
                # Set index to start from 1
                df = pd.DataFrame(brokers)
                # Define column name mappings for brokers
                broker_column_mapping = {
                    'Broker_ID': 'Broker ID',
                    'Broker_Name': 'Broker Name',
                    'Commission': 'Commission Rate (%)',
                    'Date_Of_Onboarding': 'Onboarding Date',
                    'FCA_Registration_Number': 'FCA Registration No.',
                    'Broker_Type': 'Broker Type',
                    'Market_Access': 'Market Access',
                    'Delegated_Authority': 'Delegated Authority',
                    'Longevity_Years': 'Experience (Years)',
                    'Status': 'Status',
                    'Date_Of_Expiry': 'Expiry Date'
                }
                
                # Rename columns that exist in the dataframe
                df = df.rename(columns=broker_column_mapping)

                df.index = df.index + 1
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No brokers found in the database.")
        except Exception as e:
            st.error(f"Failed to fetch brokers: {e}")
        
        if st.button("Back to Main"):
            st.session_state.toba_page = "main"
            st.rerun()
    ###

    elif st.session_state.toba_page == "view_insurers":
        st.subheader("All Insurers")
        
        try:
            # Order by Facility_ID in ascending order
            insurers = fetch_data("SELECT * FROM insurer ORDER BY Facility_ID ASC")
            if insurers:
                df = pd.DataFrame(insurers)
                
                # Display summary statistics
                col1, _,_, col2 = st.columns(4)
                with col1:
                    st.metric("Total Facilities", df['Facility_ID'].nunique())
                with col2:
                    st.metric("Total Insurers", df['Insurer_ID'].nunique())

                insurer_column_mapping = {
                'Facility_ID': 'Facility ID',
                'Facility_Name': 'Facility Name',
                'Group_Size': 'Group Size',
                'Insurer_ID': 'Insurer ID',
                'Insurer_Name': 'Insurer Name',
                'Participation': 'Participation (%)',
                'Date_Of_Onboarding': 'Onboarding Date',
                'FCA_Registration_Number': 'FCA Registration No.',
                'Insurer_Type': 'Insurer Type',
                'Delegated_Authority': 'Delegated Authority',
                'LeadInsurer': 'Lead Insurer',
                'Longevity_Years': 'Experience (Years)',
                'Status': 'Status',
                'Date_Of_Expiry': 'Expiry Date'
            }
                # Rename columns that exist in the dataframe
                df = df.rename(columns=insurer_column_mapping)
                
                # Show the dataframe from index 1
                df.index = df.index + 1

                st.dataframe(df, use_container_width=True)
                
                # Optional: Group by Facility for better visualization
                # st.subheader("Insurers by Facility")
                
                # # Group by Facility_ID for better organization
                # facilities = df['Facility_ID'].unique()
                
                # for facility_id in sorted(facilities):
                #     facility_df = df[df['Facility_ID'] == facility_id]
                #     facility_name = facility_df['Facility_Name'].iloc[0]
                #     group_size = facility_df['Group_Size'].iloc[0]
                #     total_participation = facility_df['Participation'].sum()
                    
                #     with st.expander(f"📋 {facility_id} - {facility_name} (Group Size: {group_size})"):
                #         st.write(f"**Total Participation:** {total_participation:.2f}%")
                        
                #         # Show participation status
                #         if abs(total_participation - 100.0) <= 0.01:
                #             st.success("✅ Perfect participation (100%)")
                #         elif total_participation < 100.0:
                #             st.warning(f"⚠️ Under-allocated: {100 - total_participation:.2f}% missing")
                #         else:
                #             st.error(f"❌ Over-allocated: {total_participation - 100:.2f}% excess")
                        
                #         # Display insurers in this facility
                #         facility_display_df = facility_df[['Insurer_ID', 'Insurer_Name', 'Participation']].copy()
                #         facility_display_df = facility_display_df.sort_values('Participation', ascending=False)
                #         st.dataframe(facility_display_df, use_container_width=True, hide_index=True)
                        
                #         # Show participation chart for this facility
                #         if len(facility_display_df) > 1:
                #             st.bar_chart(facility_display_df.set_index('Insurer_ID')['Participation'])
                if st.button("Back to Main"):
                    st.session_state.toba_page = "main"
                    st.rerun()
            else:
                st.info("No insurers found in the database.")
        except Exception as e:
            st.error(f"Failed to fetch insurers: {e}")

            
        
    elif st.session_state.toba_page == "upload_toba":
        st.subheader("Upload TOBA File")
        # uploaded_file = st.file_uploader("File input", type=["pdf"], key="toba_upload")
        load_data_from_json()
        show_insurer_broker_form()        
        # if st.button("Back to Main"):
        #     st.session_state.toba_page = "main"
        #     st.rerun()
    




# elif st.session_state.toba_page == "view_insurers":
#     st.subheader("All Insurers (Ordered by Facility ID)")
    
#     try:
#         # Order by Facility_ID in ascending order, then by Participation descending
#         insurers = fetch_data("SELECT * FROM insurer ORDER BY Facility_ID ASC, Participation DESC")
#         if insurers:
#             df = pd.DataFrame(insurers)
#             st.dataframe(df, use_container_width=True)
#         else:
#             st.info("No insurers found in the database.")
#     except Exception as e:
#         st.error(f"Failed to fetch insurers: {e}")    
    
#     if st.button("Back to Main"):
#         st.session_state.toba_page = "main"
#         st.rerun()