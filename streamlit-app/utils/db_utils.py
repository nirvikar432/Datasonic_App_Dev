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
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    username = os.getenv('DB_USERNAME')
    password = os.getenv('DB_PASSWORD')

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
    


def insert_cv_metadata(cv_data):
    """Insert CV metadata into APP_CV_DATA table"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    conn = None
    
    try:
        print(f"DEBUG: Attempting to insert CV metadata: {cv_data}")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO APP_CV_DATA (
            Normal_Image_Hash, Annotated_Image_Hash, Normal_Image_Name, 
            Normal_Image_Unique_Name, Annotated_Image_Name, Annotated_Image_Unique_Name,
            Normal_Image_Blob_Link, Annotated_Image_Blob_Link, JSON,
            Normal_Image_GUID, Annotated_Image_GUID, Total_Detections,
            Severity, Severity_Reason, Dent_Count, Crack_Count, Scratch_Count,
            Broken_Light_Count, Flat_Tire_Count, Shattered_Glass_Count,
            Reference_Number, Unique_ID, Created_By
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            cv_data.get("normal_image_hash"),
            cv_data.get("annotated_image_hash"),
            cv_data.get("normal_image_name"),
            cv_data.get("normal_image_unique_name"),
            cv_data.get("annotated_image_name"),
            cv_data.get("annotated_image_unique_name"),
            cv_data.get("normal_image_blob_link"),
            cv_data.get("annotated_image_blob_link"),
            cv_data.get("json"),
            cv_data.get("normal_image_guid"),
            cv_data.get("annotated_image_guid"),
            cv_data.get("total_detections", 0),
            cv_data.get("severity"),
            cv_data.get("severity_reason"),
            cv_data.get("dent_count", 0),
            cv_data.get("crack_count", 0),
            cv_data.get("scratch_count", 0),
            cv_data.get("broken_light_count", 0),
            cv_data.get("flat_tire_count", 0),
            cv_data.get("shattered_glass_count", 0),
            cv_data.get("reference_number"),
            cv_data.get("unique_id"),
            cv_data.get("created_by", "system")
        )
        
        cursor.execute(insert_query, values)
        conn.commit()
        
        # Get the inserted UID
        cursor.execute("SELECT @@IDENTITY")
        cv_uid = cursor.fetchone()[0]
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log the operation
        log_database_operation(
            operation="INSERT",
            table_name="APP_CV_DATA",
            rows_affected=1,
            execution_time_ms=execution_time,
            correlation_id=correlation_id,
            additional_data={
                "cv_uid": cv_uid,
                "claim_uid": cv_data.get("unique_id"),
                "normal_guid": cv_data.get("normal_image_guid"),
                "annotated_guid": cv_data.get("annotated_image_guid"),
                "reference_number": cv_data.get("reference_number")
            }
        )
        
        return cv_uid
        
    except Exception as e:
        if conn:
            conn.rollback()
        execution_time = (time.time() - start_time) * 1000
        log_error(
            error=e,
            module_name="db_utils",
            function_name="insert_cv_metadata",
            correlation_id=correlation_id,
            execution_time_ms=execution_time
        )
        raise e
    finally:
        if conn:
            cursor.close()
            conn.close()

def fetch_cv_metadata_by_claim_uid(claim_uid):
    """Fetch CV metadata by Claim UID"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            cv.*,
            c.CLAIM_NO,
            c.POLICY_NO,
            c.MAKE,
            c.MODEL,
            c.CLAIM_STATUS
        FROM APP_CV_DATA cv
        LEFT JOIN New_Claims c ON cv.Unique_ID = c.Unique_ID
        WHERE cv.Unique_ID = %s
        ORDER BY cv.Upload_Date DESC
        """
        
        cursor.execute(query, (claim_uid,))
        result = cursor.fetchall()
        
        return result
        
    except Exception as e:
        log_error(e, "db_utils", "fetch_cv_metadata_by_claim_uid")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

def fetch_cv_metadata_by_reference(reference_number):
    """Fetch CV metadata by reference number (Policy/Claim number)"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            cv.*,
            c.CLAIM_NO,
            c.POLICY_NO,
            c.MAKE,
            c.MODEL,
            c.CLAIM_STATUS
        FROM APP_CV_DATA cv
        LEFT JOIN New_Claims c ON cv.Unique_ID = c.Unique_ID
        WHERE cv.Reference_Number = %s
        ORDER BY cv.Upload_Date DESC
        """
        
        cursor.execute(query, (reference_number,))
        result = cursor.fetchall()
        
        return result
        
    except Exception as e:
        log_error(e, "db_utils", "fetch_cv_metadata_by_reference")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

def update_cv_metadata_claim_link(cv_uid, claim_uid):
    """Update CV metadata to link with claim UID"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        UPDATE APP_CV_DATA 
        SET Unique_ID = %s, Updated_Date = GETDATE() 
        WHERE UID = %s
        """
        
        cursor.execute(query, (claim_uid, cv_uid))
        conn.commit()
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        log_error(e, "db_utils", "update_cv_metadata_claim_link")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

def fetch_all_cv_metadata(limit=100):
    """Fetch all CV metadata with optional limit"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = f"""
        SELECT TOP {limit}
            cv.UID,
            cv.Normal_Image_Name,
            cv.Annotated_Image_Name,
            cv.Normal_Image_Blob_Link,
            cv.Annotated_Image_Blob_Link,
            cv.Total_Detections,
            cv.Severity,
            cv.Upload_Date,
            cv.Reference_Number,
            cv.Created_By,
            c.CLAIM_NO,
            c.POLICY_NO,
            c.CLAIM_STATUS
        FROM APP_CV_DATA cv
        LEFT JOIN New_Claims c ON cv.Unique_ID = c.Unique_ID
        ORDER BY cv.Upload_Date DESC
        """
        
        cursor.execute(query)
        result = cursor.fetchall()
        
        return result
        
    except Exception as e:
        log_error(e, "db_utils", "fetch_all_cv_metadata")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()




#ML METADATA
def insert_ml_prediction_metadata(ml_data):
    """Insert ML prediction metadata into APP_ML_DATA table"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    conn = None
    
    try:
        print(f"DEBUG: ML prediction data received: {ml_data}")
        
        # Validate Unique_ID
        unique_id = ml_data.get("unique_id")
        if unique_id:
            try:
                uuid.UUID(str(unique_id))
            except (ValueError, TypeError):
                print(f"WARNING: Invalid unique_id: {unique_id}")
                unique_id = None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO APP_ML_DATA (
            Unique_ID, JSON, PREDICTED_VALUE, INPUT_FEATURES, 
            REFERENCE_NUMBER, API_ENDPOINT, PROCESSING_TIME_MS, Created_By
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            unique_id,
            ml_data.get("json"),
            ml_data.get("predicted_value"),
            ml_data.get("input_features"),
            ml_data.get("reference_number"),
            ml_data.get("api_endpoint"),
            ml_data.get("processing_time_ms"),
            ml_data.get("created_by", "system")
        )
        
        print(f"DEBUG: Executing ML prediction insert with values: {values}")
        
        cursor.execute(insert_query, values)
        conn.commit()
        
        # Get the inserted UID
        cursor.execute("SELECT @@IDENTITY")
        ml_uid_result = cursor.fetchone()
        ml_uid = ml_uid_result[0] if ml_uid_result else None
        
        print(f"DEBUG: Successfully inserted ML prediction with UID: {ml_uid}")
        
        execution_time = (time.time() - start_time) * 1000
        
        # Log the operation
        log_database_operation(
            operation="INSERT",
            table_name="APP_ML_DATA",
            rows_affected=1,
            execution_time_ms=execution_time,
            correlation_id=correlation_id,
            additional_data={
                "ml_uid": ml_uid,
                "policy_uid": unique_id,
                "predicted_value": ml_data.get("predicted_value"),
                "reference_number": ml_data.get("reference_number")
            }
        )
        
        return ml_uid
        
    except Exception as e:
        if conn:
            conn.rollback()
        execution_time = (time.time() - start_time) * 1000
        
        print(f"ERROR: Failed to insert ML prediction: {e}")
        print(f"ERROR: ML data was: {ml_data}")
        
        log_error(
            error=e,
            module_name="db_utils",
            function_name="insert_ml_prediction_metadata",
            correlation_id=correlation_id,
            execution_time_ms=execution_time,
            additional_data={"ml_data_keys": list(ml_data.keys()) if ml_data else None}
        )
        raise e
    finally:
        if conn:
            cursor.close()
            conn.close()

def fetch_ml_predictions_by_policy_uid(policy_uid):
    """Fetch ML predictions by Policy UID"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            ml.*,
            p.POLICY_NO,
            p.CUST_ID,
            p.MAKE,
            p.MODEL,
            p.PREMIUM2 as ACTUAL_PREMIUM
        FROM APP_ML_DATA ml
        LEFT JOIN New_Policy p ON ml.Unique_ID = p.Unique_ID
        WHERE ml.Unique_ID = %s
        ORDER BY ml.PREDICTION_DATE DESC
        """
        
        cursor.execute(query, (policy_uid,))
        result = cursor.fetchall()
        
        return result
        
    except Exception as e:
        log_error(e, "db_utils", "fetch_ml_predictions_by_policy_uid")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

def fetch_ml_predictions_by_reference(reference_number):
    """Fetch ML predictions by reference number (Policy number)"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT 
            ml.*,
            p.POLICY_NO,
            p.CUST_ID,
            p.MAKE,
            p.MODEL,
            p.PREMIUM2 as ACTUAL_PREMIUM
        FROM APP_ML_DATA ml
        LEFT JOIN New_Policy p ON ml.Unique_ID = p.Unique_ID
        WHERE ml.REFERENCE_NUMBER = %s
        ORDER BY ml.PREDICTION_DATE DESC
        """
        
        cursor.execute(query, (reference_number,))
        result = cursor.fetchall()
        
        return result
        
    except Exception as e:
        log_error(e, "db_utils", "fetch_ml_predictions_by_reference")
        return []
    finally:
        if conn:
            cursor.close()
            conn.close()

def update_ml_prediction_policy_link(ml_uid, policy_uid):
    """Update ML prediction to link with policy UID"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        UPDATE APP_ML_DATA 
        SET Unique_ID = %s, Updated_Date = GETDATE() 
        WHERE UID = %s
        """
        
        cursor.execute(query, (policy_uid, ml_uid))
        conn.commit()
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        log_error(e, "db_utils", "update_ml_prediction_policy_link")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

# def fetch_all_ml_predictions(limit=100):
#     """Fetch all ML predictions with optional limit"""
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(as_dict=True)
        
#         query = f"""
#         SELECT TOP {limit}
#             ml.UID,
#             ml.PREDICTED_VALUE,
#             ml.PREDICTION_DATE,
#             ml.REFERENCE_NUMBER,
#             ml.Created_By,
#             p.POLICY_NO,
#             p.CUST_ID,
#             p.MAKE,
#             p.MODEL,
#             p.PREMIUM2 as ACTUAL_PREMIUM,
#             p.TransactionType
#         FROM APP_ML_DATA ml
#         LEFT JOIN New_Policy p ON ml.Unique_ID = p.Unique_ID
#         ORDER BY ml.PREDICTION_DATE DESC
#         """
        
#         cursor.execute(query)
#         result = cursor.fetchall()
        
#         return result
        
#     except Exception as e:
#         log_error(e, "db_utils", "fetch_all_ml_predictions")
#         return []
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()