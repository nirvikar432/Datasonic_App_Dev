# from datetime import datetime, date
# import os
# from pathlib import Path
# import pyodbc
# import streamlit as st
# import time
# import traceback
# import psutil
# import uuid
# import json 
# import dotenv

# dotenv.load_dotenv(Path(__file__).parent.parent / ".env")


# def get_db_connection():
 

#     # Define your connection parameters
#     server = 'datasonic.database.windows.net'
#     database ='datasonicdb'
#     username = 'nirvikar'
#     password = 'datasonic@123'



#     # Create a connection string
#     connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

#     # Establish a connection to the database
#     conn = pyodbc.connect(connection_string)
#     return conn

# def fetch_data(query):
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     cursor.execute(query)
#     data = cursor.fetchall()
    
#     # Convert data to a list of dictionaries for easier handling
#     columns = [column[0] for column in cursor.description]
#     results = [dict(zip(columns, row)) for row in data]
    
#     cursor.close()
#     conn.close()
    
#     return results

# def insert_policy(policy_data):

#     """Insert policy with logging"""
#     start_time = time.time()
#     correlation_id = str(uuid.uuid4())

#     user_ip = get_user_ip()
#     current_page = get_current_page()
    
#     try:
#         log_app_event(
#             log_level="INFO",
#             message="Policy insertion started",
#             module_name="Database",
#             action_type="INSERT_START",
#             function_name="insert_policy",
#             reference_type="POLICY",
#             reference_number=policy_data.get("POLICY_NO"),
#             correlation_id=correlation_id,
#             user_ip_address=user_ip,
#             request_path=current_page, # Now populated
#         )
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         columns = ', '.join(policy_data.keys())
#         placeholders = ', '.join(['?'] * len(policy_data))
#         sql = f"INSERT INTO New_Policy ({columns}) VALUES ({placeholders})"
#         # try:
#         cursor.execute(sql, list(policy_data.values()))
#         rows_affected = cursor.rowcount
#         conn.commit()
#         execution_time = int((time.time() - start_time) * 1000)
#         log_database_operation(
#             operation="INSERT",
#             table_name="New_Policy",
#             rows_affected=rows_affected,
#             execution_time_ms=execution_time,
#             reference_type="POLICY",
#             reference_number=policy_data.get("POLICY_NO"),
#             transaction_type=policy_data.get("TransactionType"),
#             correlation_id=correlation_id,
#             user_ip_address=user_ip,
#             request_path=current_page
#         )
        
#         return True
#     except Exception as e:
#         log_error(
#             error=e,
#             module_name="Database",
#             function_name="insert_policy",
#             reference_type="POLICY",
#             reference_number=policy_data.get("POLICY_NO"),
#             correlation_id=correlation_id,
#             user_ip_address=user_ip,
#             request_path=current_page
#         )
#         raise



# def execute_query(query):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     try:
#         cursor.execute(query)
#         conn.commit()
#     finally:
#         cursor.close()
#         conn.close()

    
# def insert_claim(claim_data):
#     """Insert new claim into database"""
#     start_time = time.time()
#     correlation_id = str(uuid.uuid4())

#     try:
#         log_app_event(
#             log_level="INFO",
#             message="Claim insertion started",
#             module_name="Database",
#             action_type="INSERT_START",
#             function_name="insert_claim",
#             reference_type="CLAIM",
#             reference_number=claim_data.get("CLAIM_NO"),
#             correlation_id=correlation_id
#         )
    
#         conn = get_db_connection()
#         cursor = conn.cursor()
    
#         columns = ', '.join(claim_data.keys())
#         placeholders = ', '.join(['?' for _ in claim_data])
#         values = tuple(claim_data.values())
    
#         query = f"INSERT INTO New_Claims ({columns}) VALUES ({placeholders})"
#         cursor.execute(query, values)
#         rows_affected = cursor.rowcount

#         conn.commit()
#         execution_time = int((time.time() - start_time) * 1000)

#         log_database_operation(
#             operation="INSERT",                           
#             table_name="New_Claims",
#             rows_affected=rows_affected,
#             execution_time_ms=execution_time,
#             reference_type="CLAIM",
#             reference_number=claim_data.get("CLAIM_NO"),
#             transaction_type=claim_data.get("TransactionType"),
#             correlation_id=correlation_id
#         )

#         return True

#     except Exception as e:
#         log_error(
#             error=e,
#             module_name="Database",
#             function_name="insert_claim",
#             reference_type="CLAIM",
#             reference_number=claim_data.get("CLAIM_NO"),
#             correlation_id=correlation_id
#         )
#         raise
#     finally:
#         if conn:
#             try:
#                 cursor.close()
#                 conn.close()
#             except:
#                 pass



# def insert_broker(broker_data):
#     """Insert broker with error handling or update if FCA_Registration_Number exists"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # First check if the FCA_Registration_Number already exists
#         fca_registration = broker_data.get("FCA_Registration_Number")
#         if fca_registration and fca_registration.strip():
#             # Check if FCA Registration Number exists
#             check_query = "SELECT Broker_ID FROM Broker WHERE FCA_Registration_Number = ?"
#             cursor.execute(check_query, (fca_registration))
#             existing_record = cursor.fetchone()
            
#             if existing_record:
#                 # Record exists, perform an update instead of insert
#                 update_fields = {k: v for k, v in broker_data.items() 
#                                if k not in ["Broker_ID", "FCA_Registration_Number"]}
                
#                 if update_fields:
#                     set_clause = ', '.join([f"{key} = ?" for key in update_fields.keys()])
#                     values = list(update_fields.values()) + [fca_registration]
#                     update_query = f"UPDATE Broker SET {set_clause} WHERE FCA_Registration_Number = ?"
#                     cursor.execute(update_query, values)
#                     conn.commit()
#                     return "updated"  # Return status to indicate an update occurred
#                 else:
#                     return "no_changes"  # No changes to make
        
#         # If we reach here, either no FCA_Registration_Number was provided or no existing record found
#         # Proceed with insert
#         insert_query = """
#         INSERT INTO Broker (
#             Broker_ID, Broker_Name, Commission, Date_Of_Onboarding,
#             FCA_Registration_Number, Broker_Type, Market_Access, Delegated_Authority, Longevity_Years, Date_Of_Expiry, Status, Submission_Date, GUID)
#               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
        
#         values = (
#             broker_data.get("Broker_ID"),
#             broker_data.get("Broker_Name"),
#             broker_data.get("Commission"),
#             broker_data.get("Date_Of_Onboarding"),
#             fca_registration,
#             broker_data.get("Broker_Type"),
#             broker_data.get("Market_Access"),
#             broker_data.get("Delegated_Authority"),
#             broker_data.get("Longevity_Years"),
#             broker_data.get("Date_Of_Expiry"),
#             broker_data.get("Status", "Active"),  # Default to Active if not provided
#             broker_data.get("Submission_Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
#             broker_data.get("GUID", None)
#         )
        
#         cursor.execute(insert_query, values)
#         conn.commit()
#         return "inserted"  # Return status to indicate an insert occurred
        
#     except pyodbc.IntegrityError as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Broker data integrity error: {e}")
#         st.info("💡 This usually means the Broker ID already exists")
#         raise
#     except pyodbc.Error as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Database error during broker operation: {e}")
#         raise
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Unexpected error during broker operation: {e}")
#         raise
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()


# def insert_insurer(insurer_data):
#     """Insert facility and multiple insurers with error handling"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # Insert each insurer in the facility
#         insurers = insurer_data.get('insurers', [])
        
#         if not insurers:
#             raise ValueError("No insurers provided in the data")

#         # Find lead insurer (one with max participation)
#         lead_insurer_id = max(insurers, key=lambda x: x.get('Participation', 0)).get('Insurer_ID')

#         # Insert each insurer record
#         for i, insurer in enumerate(insurers):
#             insert_query = """
#                 INSERT INTO insurer (
#                     Facility_ID, Facility_Name, Group_Size, Insurer_ID, Insurer_Name, Participation,
#                     Date_Of_Onboarding, FCA_Registration_Number, Insurer_Type, Delegated_Authority, LeadInsurer,
#                     Longevity_Years, Status, Date_Of_Expiry, GUID, Submission_Date
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """

            
#             values = (
#                 insurer_data.get("Facility_ID"),
#                 insurer_data.get("Facility_Name"),
#                 insurer_data.get("Group_Size"),
#                 insurer.get("Insurer_ID"),
#                 insurer.get("Insurer_Name"),
#                 insurer.get("Participation"),
#                 insurer.get("Date_Of_Onboarding"),
#                 insurer.get("FCA_Registration_Number"),
#                 insurer.get("Insurer_Type"),
#                 insurer.get("Delegated_Authority"),
#                 1 if insurer.get("Insurer_ID") == lead_insurer_id else 0,
#                 insurer.get("Longevity_Years", 0),  # Default to 0 if not provided
#                 insurer.get("Status", "Active"),  # Default to Active if not provided
#                 insurer.get("Date_Of_Expiry", None),  # Default to None if not provided
#                 insurer.get("GUID", None),  # Default to None if not provided
#                 insurer.get("Submission_Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
#             )

            
#             try:
#                 cursor.execute(insert_query, values)
#                 st.info(f"✓ Inserted Insurer {i+1}: {insurer.get('Insurer_ID')} - {insurer.get('Insurer_Name')}")
#                 time.sleep(2)  # Pause briefly to show each success message
#             except Exception as e:
#                 st.error(f"✗ Error inserting Insurer {i+1} ({insurer.get('Insurer_ID', 'Unknown')}): {e}")
#                 raise
        
#         conn.commit()
#         st.success(f"Successfully inserted all {len(insurers)} insurer(s) for facility {insurer_data.get('Facility_ID')}")
#         time.sleep(5)  # Pause for a moment to let the user see the success message
        
#     except pyodbc.IntegrityError as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Data integrity error: {e}")
#         st.info("💡 This usually means duplicate IDs or constraint violations")
#         raise
#     except pyodbc.Error as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Database error: {e}")
#         raise
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         st.error(f"Unexpected error: {e}")
#         raise
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()



# def insert_upload_document(document_data):
#     """Insert document with logging"""
#     start_time = time.time()
#     correlation_id = str(uuid.uuid4())
#     """Insert document upload record into UploadDocument table"""
#     conn = None

#     try:        
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         insert_query = """
#         INSERT INTO document
#         (Hash, Unique_File_Name, Original_File_Name, GUID, JSON, Type, Transaction_Type, Reference_Number, Blob_Link, UploadDate, ProcessingStatus)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
        
#         cursor.execute(insert_query, (
#             document_data["Hash"],
#             document_data["Unique_File_Name"],
#             document_data["Original_File_Name"],
#             document_data["GUID"],
#             document_data["JSON"],
#             document_data["Type"],
#             document_data["Transaction_Type"],
#             document_data["Reference_Number"],
#             document_data["Blob_Link"],
#             document_data["UploadDate"],
#             document_data["ProcessingStatus"]
#         ))
#         rows_affected = cursor.rowcount
#         conn.commit()
#         # cursor.close()

#         execution_time = int((time.time() - start_time) * 1000)

#         log_document_operation(
#             action_type="DOCUMENT_INSERTED",
#             document_info={
#                 'file_name': document_data.get('Original_File_Name'),
#                 'file_size_kb': None,  # Calculate if available
#                 'file_hash': document_data.get('Hash'),
#                 'blob_url': document_data.get('Blob_Link'),
#                 'guid': document_data.get('GUID')
#             },
#             reference_type=document_data.get('Type'),
#             reference_number=document_data.get('Reference_Number'),
#             correlation_id=correlation_id,
#             execution_time_ms=execution_time
#         )
        
#         return True

#     except Exception as e:
#         log_error(
#             error=e,
#             module_name="Document_Management",
#             function_name="insert_upload_document",
#             document_guid=document_data.get('GUID'),
#             correlation_id=correlation_id
#         )
#         raise


# def update_document_unique_id(guid_string, unique_id):
#     """Update document table's Unique_ID based on comma-separated GUID string"""
#     if not guid_string or not unique_id:
#         print(f"DEBUG: Missing data - guid_string: {guid_string}, unique_id: {unique_id}")
#         return
    
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # Split comma-separated GUIDs
#         guids = [guid.strip() for guid in guid_string.split(',') if guid.strip()]
#         print(f"DEBUG: Processing {len(guids)} GUIDs: {guids}")
#         print(f"DEBUG: Unique_ID to set: {unique_id}")
        
#         # Check existing records first
#         for guid in guids:
#             check_query = "SELECT GUID, Unique_ID, Original_File_Name FROM document WHERE GUID = ?"
#             cursor.execute(check_query, (guid,))
#             existing = cursor.fetchone()
#             if existing:
#                 print(f"DEBUG: Found document - GUID: {existing[0]}, Current Unique_ID: {existing[1]}, File: {existing[2]}")
#             else:
#                 print(f"DEBUG: No document found with GUID: {guid}")
        
#         # Update each document record
#         updated_count = 0
#         for guid in guids:
#             update_query = """
#             UPDATE document 
#             SET Unique_ID = ? 
#             WHERE GUID = ? AND (Unique_ID IS NULL OR Unique_ID = '')
#             """
#             cursor.execute(update_query, (unique_id, guid))
#             rows_affected = cursor.rowcount
#             print(f"DEBUG: Updated {rows_affected} rows for GUID: {guid}")
#             updated_count += rows_affected
        
#         conn.commit()
#         print(f"DEBUG: Successfully updated {updated_count} document records with Unique_ID: {unique_id}")
        
#         # Verify the updates
#         for guid in guids:
#             verify_query = "SELECT GUID, Unique_ID FROM document WHERE GUID = ?"
#             cursor.execute(verify_query, (guid,))
#             result = cursor.fetchone()
#             if result:
#                 print(f"DEBUG: Verification - GUID: {result[0]}, New Unique_ID: {result[1]}")
        
#     except Exception as e:
#         if conn:
#             conn.rollback()
#         print(f"ERROR: Failed to update document Unique_ID: {e}")
#         raise
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()




# # Add these logging functions at the end of the file

# def log_app_event(
#     log_level="INFO",
#     message="",
#     module_name="",
#     action_type="",
#     function_name="",
#     user_id=None,
#     user_ip_address=None,
#     request_path=None,
#     reference_type=None,
#     reference_number=None,
#     document_guid=None,
#     transaction_type=None,
#     file_name=None,
#     file_size_kb=None,
#     file_hash=None,
#     blob_url=None,
#     execution_time_ms=None,
#     database_operation=None,
#     table_name=None,
#     rows_affected=None,
#     api_endpoint=None,
#     api_response_code=None,
#     api_response_time_ms=None,
#     error_code=None,
#     stack_trace=None,
#     additional_data=None,
#     correlation_id=None
# ):
#     """Log application events to the database"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         if not conn:
#             return False
            
#         cursor = conn.cursor()
        
#         # Get system metrics
#         try:
#             memory_usage = psutil.virtual_memory().percent
#             cpu_usage = psutil.cpu_percent()
#         except:
#             memory_usage = None
#             cpu_usage = None
        
#         # Get user context from session state if available
#         session_id = None
#         try:
#             import streamlit as st
#             session_id = getattr(st.session_state, 'session_id', None)
#         except:
#             pass
        
#         insert_query = """
#         INSERT INTO App_Logs (
#             Log_Level, Log_Message, Module_Name, Action_Type, Function_Name,
#             User_ID, Session_ID, Reference_Type, Reference_Number, Document_GUID,
#             Transaction_Type, File_Name, File_Size_KB, File_Hash, Blob_URL,
#             Execution_Time_MS, Memory_Usage_MB, CPU_Usage_Percent,
#             Database_Operation, Table_Name, Rows_Affected,
#             API_Endpoint, API_Response_Code, API_Response_Time_MS,
#             Error_Code, Stack_Trace, Additional_Data, Correlation_ID
#         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
        
#         cursor.execute(insert_query, (
#             log_level, message, module_name, action_type, function_name,
#             user_id, session_id, reference_type, reference_number, document_guid,
#             transaction_type, file_name, file_size_kb, file_hash, blob_url,
#             execution_time_ms, memory_usage, cpu_usage,
#             database_operation, table_name, rows_affected,
#             api_endpoint, api_response_code, api_response_time_ms,
#             error_code, stack_trace, json.dumps(additional_data) if additional_data else None,
#             correlation_id
#         ))
        
#         conn.commit()
#         return True
        
#     except Exception as e:
#         print(f"Failed to log to database: {e}")
#         # Fallback to file logging
#         try:
#             with open("app_logs_fallback.log", "a") as f:
#                 f.write(f"{datetime.now()} - {log_level} - {message}\n")
#         except:
#             pass
#         return False
#     finally:
#         if conn:
#             try:
#                 cursor.close()
#                 conn.close()
#             except:
#                 pass

# def log_performance(function_name, execution_time_ms, **kwargs):
#     """Log performance metrics"""
#     return log_app_event(
#         log_level="INFO",
#         message=f"Performance: {function_name} executed in {execution_time_ms}ms",
#         module_name="Performance",
#         action_type="PERFORMANCE",
#         function_name=function_name,
#         execution_time_ms=execution_time_ms,
#         **kwargs
#     )

# def log_error(error, module_name, function_name, **kwargs):
#     """Log errors with stack trace"""
#     return log_app_event(
#         log_level="ERROR",
#         message=str(error),
#         module_name=module_name,
#         action_type="ERROR",
#         function_name=function_name,
#         error_code=type(error).__name__,
#         stack_trace=traceback.format_exc(),
#         **kwargs
#     )

# def log_document_operation(action_type, document_info, **kwargs):
#     """Log document-related operations"""
#     return log_app_event(
#         log_level="INFO",
#         message=f"Document {action_type}: {document_info.get('file_name', 'Unknown')}",
#         module_name="Document_Management",
#         action_type=action_type,
#         file_name=document_info.get('file_name'),
#         file_size_kb=document_info.get('file_size_kb'),
#         file_hash=document_info.get('file_hash'),
#         blob_url=document_info.get('blob_url'),
#         document_guid=document_info.get('guid'),
#         **kwargs
#     )

# def log_database_operation(operation, table_name, rows_affected, execution_time_ms, **kwargs):
#     """Log database operations"""
#     return log_app_event(
#         log_level="INFO",
#         message=f"Database {operation} on {table_name}: {rows_affected} rows affected",
#         module_name="Database",
#         action_type="DATABASE",
#         database_operation=operation,
#         table_name=table_name,
#         rows_affected=rows_affected,
#         execution_time_ms=execution_time_ms,
#         **kwargs
#     )

# # Update existing functions to include logging
# def log_app_activity(user_action, details=None):
#     """Simple activity logging function"""
#     return log_app_event(
#         log_level="INFO",
#         message=f"User activity: {user_action}",
#         module_name="User_Activity",
#         action_type="USER_ACTION",
#         function_name="log_app_activity",
#         additional_data=details
#     )


# def get_user_ip():
#     """Get user IP address from Streamlit"""
#     try:
#         # Streamlit doesn't directly expose client IP, but we can try these methods
#         import streamlit as st
        
#         # Method 1: Check if running behind proxy
#         if hasattr(st, 'get_option'):
#             # This might work in some deployments
#             return st.get_option('server.address') or 'localhost'
        
#         # Method 2: Use session info if available
#         if hasattr(st.session_state, 'user_ip'):
#             return st.session_state.user_ip
            
#         # Method 3: Default fallback
#         return 'localhost'
        
#     except Exception:
#         return 'unknown'

# def get_current_page():
#     """Get current page context"""
#     try:
#         # You can track this based on your app structure
#         if hasattr(st.session_state, 'current_tab'):
#             return st.session_state.current_tab
#         return 'unknown_page'
#     except:
#         return 'unknown'


from datetime import datetime, date
import os
from pathlib import Path
import pymssql
import streamlit as st
import time
import traceback
import psutil
import uuid
import json 
import dotenv

dotenv.load_dotenv(Path(__file__).parent.parent / ".env")


def get_db_connection():
    """Get database connection using pymssql (cloud-friendly)"""
    # Define your connection parameters
    server = 'datasonic.database.windows.net'
    database ='datasonicdb'
    username = 'nirvikar'
    password = 'datasonic@123'

    # Establish a connection to the database using pymssql
    conn = pymssql.connect(
        server=server,
        user=username,
        password=password,
        database=database,
        timeout=30,
        login_timeout=30,
        charset='UTF-8'
    )
    return conn

def fetch_data(query):
    conn = get_db_connection()
    cursor = conn.cursor(as_dict=True)  # as_dict=True returns results as dictionaries
    
    cursor.execute(query)
    data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return data

def insert_policy(policy_data):
    """Insert policy with logging"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())

    user_ip = get_user_ip()
    current_page = get_current_page()
    
    try:
        log_app_event(
            log_level="INFO",
            message="Policy insertion started",
            module_name="Database",
            action_type="INSERT_START",
            function_name="insert_policy",
            reference_type="POLICY",
            reference_number=policy_data.get("POLICY_NO"),
            correlation_id=correlation_id,
            user_ip_address=user_ip,
            request_path=current_page,
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        columns = ', '.join(policy_data.keys())
        placeholders = ', '.join(['%s'] * len(policy_data))  # Changed from ? to %s
        sql = f"INSERT INTO New_Policy ({columns}) VALUES ({placeholders})"
        
        cursor.execute(sql, list(policy_data.values()))
        rows_affected = cursor.rowcount
        conn.commit()
        execution_time = int((time.time() - start_time) * 1000)
        log_database_operation(
            operation="INSERT",
            table_name="New_Policy",
            rows_affected=rows_affected,
            execution_time_ms=execution_time,
            reference_type="POLICY",
            reference_number=policy_data.get("POLICY_NO"),
            transaction_type=policy_data.get("TransactionType"),
            correlation_id=correlation_id,
            user_ip_address=user_ip,
            request_path=current_page
        )
        
        return True
    except Exception as e:
        log_error(
            error=e,
            module_name="Database",
            function_name="insert_policy",
            reference_type="POLICY",
            reference_number=policy_data.get("POLICY_NO"),
            correlation_id=correlation_id,
            user_ip_address=user_ip,
            request_path=current_page
        )
        raise
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

def execute_query(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def insert_claim(claim_data):
    """Insert new claim into database"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())

    conn = None
    try:
        log_app_event(
            log_level="INFO",
            message="Claim insertion started",
            module_name="Database",
            action_type="INSERT_START",
            function_name="insert_claim",
            reference_type="CLAIM",
            reference_number=claim_data.get("CLAIM_NO"),
            correlation_id=correlation_id
        )
    
        conn = get_db_connection()
        cursor = conn.cursor()
    
        columns = ', '.join(claim_data.keys())
        placeholders = ', '.join(['%s' for _ in claim_data])  # Changed from ? to %s
        values = tuple(claim_data.values())
    
        query = f"INSERT INTO New_Claims ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        rows_affected = cursor.rowcount

        conn.commit()
        execution_time = int((time.time() - start_time) * 1000)

        log_database_operation(
            operation="INSERT",                           
            table_name="New_Claims",
            rows_affected=rows_affected,
            execution_time_ms=execution_time,
            reference_type="CLAIM",
            reference_number=claim_data.get("CLAIM_NO"),
            transaction_type=claim_data.get("TransactionType"),
            correlation_id=correlation_id
        )

        return True

    except Exception as e:
        log_error(
            error=e,
            module_name="Database",
            function_name="insert_claim",
            reference_type="CLAIM",
            reference_number=claim_data.get("CLAIM_NO"),
            correlation_id=correlation_id
        )
        raise
    finally:
        if conn:
            try:
                cursor.close()
                conn.close()
            except:
                pass

def insert_broker(broker_data):
    """Insert broker with error handling or update if FCA_Registration_Number exists"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First check if the FCA_Registration_Number already exists
        fca_registration = broker_data.get("FCA_Registration_Number")
        if fca_registration and fca_registration.strip():
            # Check if FCA Registration Number exists
            check_query = "SELECT Broker_ID FROM Broker WHERE FCA_Registration_Number = %s"
            cursor.execute(check_query, (fca_registration,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Record exists, perform an update instead of insert
                update_fields = {k: v for k, v in broker_data.items() 
                               if k not in ["Broker_ID", "FCA_Registration_Number"]}
                
                if update_fields:
                    set_clause = ', '.join([f"{key} = %s" for key in update_fields.keys()])
                    values = list(update_fields.values()) + [fca_registration]
                    update_query = f"UPDATE Broker SET {set_clause} WHERE FCA_Registration_Number = %s"
                    cursor.execute(update_query, values)
                    conn.commit()
                    return "updated"
                else:
                    return "no_changes"
        
        # Proceed with insert
        insert_query = """
        INSERT INTO Broker (
            Broker_ID, Broker_Name, Commission, Date_Of_Onboarding,
            FCA_Registration_Number, Broker_Type, Market_Access, Delegated_Authority, Longevity_Years, Date_Of_Expiry, Status, Submission_Date, GUID)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            broker_data.get("Broker_ID"),
            broker_data.get("Broker_Name"),
            broker_data.get("Commission"),
            broker_data.get("Date_Of_Onboarding"),
            fca_registration,
            broker_data.get("Broker_Type"),
            broker_data.get("Market_Access"),
            broker_data.get("Delegated_Authority"),
            broker_data.get("Longevity_Years"),
            broker_data.get("Date_Of_Expiry"),
            broker_data.get("Status", "Active"),
            broker_data.get("Submission_Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            broker_data.get("GUID", None)
        )
        
        cursor.execute(insert_query, values)
        conn.commit()
        return "inserted"
        
    except pymssql.IntegrityError as e:
        if conn:
            conn.rollback()
        st.error(f"Broker data integrity error: {e}")
        st.info("💡 This usually means the Broker ID already exists")
        raise
    except pymssql.Error as e:
        if conn:
            conn.rollback()
        st.error(f"Database error during broker operation: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Unexpected error during broker operation: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def insert_insurer(insurer_data):
    """Insert facility and multiple insurers with error handling"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert each insurer in the facility
        insurers = insurer_data.get('insurers', [])
        
        if not insurers:
            raise ValueError("No insurers provided in the data")

        # Find lead insurer (one with max participation)
        lead_insurer_id = max(insurers, key=lambda x: x.get('Participation', 0)).get('Insurer_ID')

        # Insert each insurer record
        for i, insurer in enumerate(insurers):
            insert_query = """
                INSERT INTO insurer (
                    Facility_ID, Facility_Name, Group_Size, Insurer_ID, Insurer_Name, Participation,
                    Date_Of_Onboarding, FCA_Registration_Number, Insurer_Type, Delegated_Authority, LeadInsurer,
                    Longevity_Years, Status, Date_Of_Expiry, GUID, Submission_Date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            
            values = (
                insurer_data.get("Facility_ID"),
                insurer_data.get("Facility_Name"),
                insurer_data.get("Group_Size"),
                insurer.get("Insurer_ID"),
                insurer.get("Insurer_Name"),
                insurer.get("Participation"),
                insurer.get("Date_Of_Onboarding"),
                insurer.get("FCA_Registration_Number"),
                insurer.get("Insurer_Type"),
                insurer.get("Delegated_Authority"),
                1 if insurer.get("Insurer_ID") == lead_insurer_id else 0,
                insurer.get("Longevity_Years", 0),
                insurer.get("Status", "Active"),
                insurer.get("Date_Of_Expiry", None),
                insurer.get("GUID", None),
                insurer.get("Submission_Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            
            try:
                cursor.execute(insert_query, values)
                st.info(f"✓ Inserted Insurer {i+1}: {insurer.get('Insurer_ID')} - {insurer.get('Insurer_Name')}")
                time.sleep(2)
            except Exception as e:
                st.error(f"✗ Error inserting Insurer {i+1} ({insurer.get('Insurer_ID', 'Unknown')}): {e}")
                raise
        
        conn.commit()
        st.success(f"Successfully inserted all {len(insurers)} insurer(s) for facility {insurer_data.get('Facility_ID')}")
        time.sleep(5)
        
    except pymssql.IntegrityError as e:
        if conn:
            conn.rollback()
        st.error(f"Data integrity error: {e}")
        st.info("💡 This usually means duplicate IDs or constraint violations")
        raise
    except pymssql.Error as e:
        if conn:
            conn.rollback()
        st.error(f"Database error: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Unexpected error: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def insert_upload_document(document_data):
    """Insert document with logging"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    conn = None

    try:        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO document
        (Hash, Unique_File_Name, Original_File_Name, GUID, JSON, Type, Transaction_Type, Reference_Number, Blob_Link, UploadDate, ProcessingStatus)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            document_data["Hash"],
            document_data["Unique_File_Name"],
            document_data["Original_File_Name"],
            document_data["GUID"],
            document_data["JSON"],
            document_data["Type"],
            document_data["Transaction_Type"],
            document_data["Reference_Number"],
            document_data["Blob_Link"],
            document_data["UploadDate"],
            document_data["ProcessingStatus"]
        ))
        rows_affected = cursor.rowcount
        conn.commit()

        execution_time = int((time.time() - start_time) * 1000)

        log_document_operation(
            action_type="DOCUMENT_INSERTED",
            document_info={
                'file_name': document_data.get('Original_File_Name'),
                'file_size_kb': None,
                'file_hash': document_data.get('Hash'),
                'blob_url': document_data.get('Blob_Link'),
                'guid': document_data.get('GUID')
            },
            reference_type=document_data.get('Type'),
            reference_number=document_data.get('Reference_Number'),
            correlation_id=correlation_id,
            execution_time_ms=execution_time
        )
        
        return True

    except Exception as e:
        log_error(
            error=e,
            module_name="Document_Management",
            function_name="insert_upload_document",
            document_guid=document_data.get('GUID'),
            correlation_id=correlation_id
        )
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

def update_document_unique_id(guid_string, unique_id):
    """Update document table's Unique_ID based on comma-separated GUID string"""
    if not guid_string or not unique_id:
        print(f"DEBUG: Missing data - guid_string: {guid_string}, unique_id: {unique_id}")
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Split comma-separated GUIDs
        guids = [guid.strip() for guid in guid_string.split(',') if guid.strip()]
        print(f"DEBUG: Processing {len(guids)} GUIDs: {guids}")
        print(f"DEBUG: Unique_ID to set: {unique_id}")
        
        # Check existing records first
        for guid in guids:
            check_query = "SELECT GUID, Unique_ID, Original_File_Name FROM document WHERE GUID = %s"
            cursor.execute(check_query, (guid,))
            existing = cursor.fetchone()
            if existing:
                print(f"DEBUG: Found document - GUID: {existing[0]}, Current Unique_ID: {existing[1]}, File: {existing[2]}")
            else:
                print(f"DEBUG: No document found with GUID: {guid}")
        
        # Update each document record
        updated_count = 0
        for guid in guids:
            update_query = """
            UPDATE document 
            SET Unique_ID = %s 
            WHERE GUID = %s AND (Unique_ID IS NULL OR Unique_ID = '')
            """
            cursor.execute(update_query, (unique_id, guid))
            rows_affected = cursor.rowcount
            print(f"DEBUG: Updated {rows_affected} rows for GUID: {guid}")
            updated_count += rows_affected
        
        conn.commit()
        print(f"DEBUG: Successfully updated {updated_count} document records with Unique_ID: {unique_id}")
        
        # Verify the updates
        for guid in guids:
            verify_query = "SELECT GUID, Unique_ID FROM document WHERE GUID = %s"
            cursor.execute(verify_query, (guid,))
            result = cursor.fetchone()
            if result:
                print(f"DEBUG: Verification - GUID: {result[0]}, New Unique_ID: {result[1]}")
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ERROR: Failed to update document Unique_ID: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

# ...existing code... (logging functions remain the same)

def log_app_event(
    log_level="INFO",
    message="",
    module_name="",
    action_type="",
    function_name="",
    user_id=None,
    user_ip_address=None,
    request_path=None,
    reference_type=None,
    reference_number=None,
    document_guid=None,
    transaction_type=None,
    file_name=None,
    file_size_kb=None,
    file_hash=None,
    blob_url=None,
    execution_time_ms=None,
    database_operation=None,
    table_name=None,
    rows_affected=None,
    api_endpoint=None,
    api_response_code=None,
    api_response_time_ms=None,
    error_code=None,
    stack_trace=None,
    additional_data=None,
    correlation_id=None
):
    """Log application events to the database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Get system metrics
        try:
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
        except:
            memory_usage = None
            cpu_usage = None
        
        # Get user context from session state if available
        session_id = None
        try:
            import streamlit as st
            session_id = getattr(st.session_state, 'session_id', None)
        except:
            pass
        
        insert_query = """
        INSERT INTO App_Logs (
            Log_Level, Log_Message, Module_Name, Action_Type, Function_Name,
            User_ID, Session_ID, Reference_Type, Reference_Number, Document_GUID,
            Transaction_Type, File_Name, File_Size_KB, File_Hash, Blob_URL,
            Execution_Time_MS, Memory_Usage_MB, CPU_Usage_Percent,
            Database_Operation, Table_Name, Rows_Affected,
            API_Endpoint, API_Response_Code, API_Response_Time_MS,
            Error_Code, Stack_Trace, Additional_Data, Correlation_ID
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            log_level, message, module_name, action_type, function_name,
            user_id, session_id, reference_type, reference_number, document_guid,
            transaction_type, file_name, file_size_kb, file_hash, blob_url,
            execution_time_ms, memory_usage, cpu_usage,
            database_operation, table_name, rows_affected,
            api_endpoint, api_response_code, api_response_time_ms,
            error_code, stack_trace, json.dumps(additional_data) if additional_data else None,
            correlation_id
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Failed to log to database: {e}")
        # Fallback to file logging
        try:
            with open("app_logs_fallback.log", "a") as f:
                f.write(f"{datetime.now()} - {log_level} - {message}\n")
        except:
            pass
        return False
    finally:
        if conn:
            try:
                cursor.close()
                conn.close()
            except:
                pass

def log_performance(function_name, execution_time_ms, **kwargs):
    """Log performance metrics"""
    return log_app_event(
        log_level="INFO",
        message=f"Performance: {function_name} executed in {execution_time_ms}ms",
        module_name="Performance",
        action_type="PERFORMANCE",
        function_name=function_name,
        execution_time_ms=execution_time_ms,
        **kwargs
    )

def log_error(error, module_name, function_name, **kwargs):
    """Log errors with stack trace"""
    return log_app_event(
        log_level="ERROR",
        message=str(error),
        module_name=module_name,
        action_type="ERROR",
        function_name=function_name,
        error_code=type(error).__name__,
        stack_trace=traceback.format_exc(),
        **kwargs
    )

def log_document_operation(action_type, document_info, **kwargs):
    """Log document-related operations"""
    return log_app_event(
        log_level="INFO",
        message=f"Document {action_type}: {document_info.get('file_name', 'Unknown')}",
        module_name="Document_Management",
        action_type=action_type,
        file_name=document_info.get('file_name'),
        file_size_kb=document_info.get('file_size_kb'),
        file_hash=document_info.get('file_hash'),
        blob_url=document_info.get('blob_url'),
        document_guid=document_info.get('guid'),
        **kwargs
    )

def log_database_operation(operation, table_name, rows_affected, execution_time_ms, **kwargs):
    """Log database operations"""
    return log_app_event(
        log_level="INFO",
        message=f"Database {operation} on {table_name}: {rows_affected} rows affected",
        module_name="Database",
        action_type="DATABASE",
        database_operation=operation,
        table_name=table_name,
        rows_affected=rows_affected,
        execution_time_ms=execution_time_ms,
        **kwargs
    )

def log_app_activity(user_action, details=None):
    """Simple activity logging function"""
    return log_app_event(
        log_level="INFO",
        message=f"User activity: {user_action}",
        module_name="User_Activity",
        action_type="USER_ACTION",
        function_name="log_app_activity",
        additional_data=details
    )

def get_user_ip():
    """Get user IP address from Streamlit"""
    try:
        import streamlit as st
        
        if hasattr(st, 'get_option'):
            return st.get_option('server.address') or 'localhost'
        
        if hasattr(st.session_state, 'user_ip'):
            return st.session_state.user_ip
            
        return 'localhost'
        
    except Exception:
        return 'unknown'

def get_current_page():
    """Get current page context"""
    try:
        if hasattr(st.session_state, 'current_tab'):
            return st.session_state.current_tab
        return 'unknown_page'
    except:
        return 'unknown'