import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the utils directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
from db_utils import fetch_data

def log_viewer_tab():
    st.header("📊 Application Logs")
    
    # Date filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    # Level filter
    log_levels = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    selected_level = st.selectbox("Log Level", log_levels)
    
    # Module filter
    modules = ["ALL", "Document_Upload", "Document_Management", "Database", "Document_AI", "Performance", "User_Activity"]
    selected_module = st.selectbox("Module", modules)
    
    if st.button("🔍 Search Logs"):
        try:
            # Build query
            query = f"""
            SELECT TOP 1000
                Log_Timestamp,
                Log_Level,
                Module_Name,
                Action_Type,
                Function_Name,
                Log_Message,
                Reference_Type,
                Reference_Number,
                Execution_Time_MS,
                Error_Code
            FROM App_Logs 
            WHERE Log_Date BETWEEN '{start_date}' AND '{end_date}'
            """
            
            if selected_level != "ALL":
                query += f" AND Log_Level = '{selected_level}'"
            
            if selected_module != "ALL":
                query += f" AND Module_Name = '{selected_module}'"
            
            query += " ORDER BY Log_Timestamp DESC"
            
            # Fetch and display logs
            logs = fetch_data(query)
            
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(df, use_container_width=True)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Logs as CSV",
                    data=csv,
                    file_name=f"app_logs_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No logs found for the selected criteria.")
                
        except Exception as e:
            st.error(f"Error fetching logs: {e}")
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    
    try:
        stats_query = f"""
        SELECT 
            COUNT(*) as Total_Logs,
            SUM(CASE WHEN Log_Level = 'ERROR' THEN 1 ELSE 0 END) as Error_Count,
            AVG(Execution_Time_MS) as Avg_Execution_Time,
            COUNT(DISTINCT Module_Name) as Active_Modules
        FROM App_Logs 
        WHERE Log_Date >= '{start_date}'
        """
        
        stats = fetch_data(stats_query)
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Logs", stats[0]['Total_Logs'])
            col2.metric("Errors", stats[0]['Error_Count'])
            col3.metric("Avg Execution (ms)", f"{stats[0]['Avg_Execution_Time']:.2f}" if stats[0]['Avg_Execution_Time'] else "N/A")
            col4.metric("Active Modules", stats[0]['Active_Modules'])
            
    except Exception as e:
        st.error(f"Error fetching stats: {e}")