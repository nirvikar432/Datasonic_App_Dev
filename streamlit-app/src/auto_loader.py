from time import time
import streamlit as st
import json
import sys
import os
from datetime import datetime, date
import time
import random
import streamlit as st
import tempfile
from azure.storage.blob import BlobServiceClient, ContentSettings
import uuid, hashlib, os, tempfile
import dotenv
from pathlib import Path
import requests

# Use absolute import for testing
from policy_forms import (
    policy_manual_form,
    policy_renewal_form,
    policy_mta_form,
    policy_cancel_form,

)

from db_utils import (
    insert_policy, fetch_data, insert_claim, insert_upload_document, update_document_unique_id
)
from db_utils import log_app_event, log_document_operation, log_error, log_performance



dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
API_URL = os.getenv("API_URL")
API_CODE = os.getenv("API_CODE")


# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add these functions directly to auto_loader.py to avoid circular imports
def _build_unique_id(policy_no: str, submission_dt: datetime) -> str:
    """Build unique ID with policy number and timestamp"""
    if isinstance(submission_dt, str):
        submission_dt = datetime.strptime(submission_dt, "%Y-%m-%d %H:%M:%S.%f")
    ts_compact = submission_dt.strftime("%Y%m%d%H%M%S%f")[:-3]  # trim to milliseconds
    return f"{policy_no}_{ts_compact}"

def _clear_new_policy_generated_keys():
    """Clear policy-specific generated keys"""
    for k in [
        "manual_policy_submission_dt",
        "manual_policy_submission_policy_no",
        "manual_policy_submission_uid"
    ]:
        if k in st.session_state:
            del st.session_state[k]

def _clear_new_claim_generated_keys():
    """Clear claim-specific generated keys"""
    for k in [
        "manual_claim_submission_dt",
        "manual_claim_submission_claim_no",
        "manual_claim_submission_uid"
    ]:
        if k in st.session_state:
            del st.session_state[k]

def _fetch_latest_policy(policy_no: str):
    """Pick the newest row for this policy number"""
    query = f"""
        SELECT TOP 1 *
        FROM New_Policy
        WHERE POLICY_NO = '{policy_no}'
        ORDER BY 
            CASE WHEN Submission_Date IS NULL THEN 1 ELSE 0 END ASC,
            Submission_Date DESC,
            Unique_ID DESC
    """
    return fetch_data(query)

def _fetch_latest_claims(claim_no: str):
    """Pick the newest row for this claim number"""
    query = f"""
        SELECT TOP 1 *
        FROM New_Claims
        WHERE CLAIM_NO = '{claim_no}'
        ORDER BY 
            CASE WHEN Submission_Date IS NULL THEN 1 ELSE 0 END ASC,
            Submission_Date DESC,
            Unique_ID DESC
    """
    return fetch_data(query)





# Add this helper function at the top of your file after imports
def clear_session_state():
    """Clear all form-related session state variables"""
    keys_to_delete = [
        # Form controls
        "form_to_show", "form_defaults", "submission_mode", "json_data", 
        
        # Policy specific keys
        "renewal_policy_data", "renewal_policy_fetched", "renewal_updated_data", 
        "mta_policy_data", "mta_policy_fetched", "cancel_policy_data", 
        "cancel_policy_fetched", "cancel_final_confirm",
        
        # Claim specific keys  
        "claim_update_data", "claim_update_fetched", "claim_close_data", 
        "claim_close_fetched", "claim_reopen_data", "claim_reopen_fetched",
        "claim_no",

        # GUID storage keys
        "document_guids"  # NEW: Store GUIDs for form submission
    ]
    
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
            
    # Hard reset for page state
    st.session_state.policy_edit_page = "main"
    
    # Force browser cache refresh with timestamp
    st.session_state.last_reset = datetime.now().timestamp()



def display_upload_summary(document_records, json_data):
    """Display summary of uploaded documents and extracted data"""
    
    st.subheader("Upload Summary")
    
    # Document details in expandable section
    with st.expander("Document Details", expanded=True):
        for i, record in enumerate(document_records):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**File {i+1}:** {record['Original_File_Name']}")
                st.write(f"**GUID:** {record['GUID']}")
                st.write(f"**Unique File Name:** {record['Unique_File_Name']}")
            with col2:
                st.write(f"**Type:** {record['Type']}")
                st.write(f"**Transaction:** {record['Transaction_Type']}")
            with col3:
                st.write(f"**Hash:** {record['Hash'][:12]}...")
                st.write(f"**Status:** {record['ProcessingStatus']}")
            
            st.divider()
    
    # Extracted JSON data
    with st.expander("Extracted Data", expanded=False):
        st.json(json_data)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", len(document_records))
    with col2:
        st.metric("Document Type", document_records[0]['Type'] if document_records else "N/A")
    with col3:
        st.metric("Transaction Type", document_records[0]['Transaction_Type'] if document_records else "N/A")

def compute_file_hash(file_path):
    """Compute SHA-256 hash of file"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def upload_to_blob(file_path, blob_name, metadata):
    """Upload file to Azure Blob Storage"""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=blob_name)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True, metadata=metadata,
            content_settings=ContentSettings(content_type="application/octet-stream"))

    return blob_client.url



# def process_document_with_api(file_path, file_name):
#     """Send document to API for processing and return the extracted JSON data"""
#     try:
#         # Prepare the files and data for the API request
#         files = {
#             'file': (file_name, open(file_path, 'rb'), 'application/pdf')
#         }
        
#         params = {
#             'code': API_CODE
#     }
        
#         # Make the API request
#         response = requests.post(API_URL, files=files, params=params)
        
#         # Check if the request was successful
#         if response.status_code == 200:
#             return response.json()
#         else:
#             raise Exception(f"API Error: {response.status_code} - {response.text}")
            
#     except Exception as e:
#         raise Exception(f"Error processing document with API: {e}")


def process_multiple_documents_with_api(file_paths, file_names):
    """Send multiple documents to API for processing and return the extracted JSON data"""
    correlation_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        log_app_event(
            log_level="INFO",
            message=f"API call started for {len(file_paths)} documents",
            module_name="Document_AI",
            action_type="API_CALL_START",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id
        )
        
        # Validate inputs
        if not file_paths or not file_names:
            raise ValueError("file_paths and file_names cannot be empty")
        
        if len(file_paths) != len(file_names):
            raise ValueError("file_paths and file_names must have the same length")
        
        # Prepare the files for the API request
        files = {}
        
        # Add each file to the files dictionary with a different key
        for i, (file_path, file_name) in enumerate(zip(file_paths, file_names)):
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    if not file_content:
                        raise ValueError(f"File {file_path} is empty")
                    
                    # Create a unique key for each file (file1, file2, etc.)
                    files[f'file{i+1}'] = (file_name, file_content, 'application/octet-stream')
            except Exception as file_error:
                raise Exception(f"Error reading file {file_path}: {file_error}")
        
        if not files:
            raise ValueError("No valid files to process")
        
        params = {
            'code': API_CODE
        }
        
        # Validate API configuration
        if not API_URL:
            raise ValueError("API_URL is not configured")
        if not API_CODE:
            raise ValueError("API_CODE is not configured")
        
        # Make the API request
        print(f"DEBUG: Making API request to {API_URL} with {len(files)} files")
        response = requests.post(API_URL, files=files, params=params, timeout=300)
        
        api_time = int((time.time() - start_time) * 1000)
        
        # Log API completion
        log_app_event(
            log_level="INFO" if response.status_code == 200 else "ERROR",
            message=f"API call completed with status {response.status_code}",
            module_name="Document_AI",
            action_type="API_CALL_COMPLETE",
            api_endpoint=API_URL,
            api_response_code=response.status_code,
            api_response_time_ms=api_time,
            correlation_id=correlation_id
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"DEBUG: API response received: {type(result)}")
                return result
            except ValueError as json_error:
                raise Exception(f"Invalid JSON response from API: {json_error}")
        else:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            print(f"DEBUG: {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.Timeout:
        error_msg = "API request timed out after 300 seconds"
        log_error(
            error=Exception(error_msg),
            module_name="Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id,
            additional_data={"timeout": 300}
        )
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError:
        error_msg = f"Cannot connect to API at {API_URL}"
        log_error(
            error=Exception(error_msg),
            module_name="Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id
        )
        raise Exception(error_msg)
        
    except Exception as e:
        print(f"DEBUG: Exception in process_multiple_documents_with_api: {e}")
        log_error(
            error=e,
            module_name="Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id,
            additional_data={
                "file_count": len(file_paths) if file_paths else 0,
                "file_names": file_names if file_names else []
            }
        )
        # Re-raise the exception instead of swallowing it
        raise Exception(f"Error processing documents with API: {e}")

# def process_multiple_documents_with_api(file_paths, file_names):
#     """Send multiple documents to API for processing and return the extracted JSON data"""
#     try:
#         # Prepare the files and data for the API request
#         files = {}
        
#         # Add each file to the files dictionary with a different key
#         for i, (file_path, file_name) in enumerate(zip(file_paths, file_names)):
#             with open(file_path, 'rb') as f:
#                 # Create a unique key for each file (file1, file2, etc.)
#                 files[f'file{i+1}'] = (file_name, f.read(), 'application/octet-stream')
        
#         params = {
#             'code': API_CODE
#         }
        
#         # Make the API request
#         response = requests.post(API_URL, files=files, params=params)
        
#         # Check if the request was successful
#         if response.status_code == 200:
#             return response.json()
#         else:
#             raise Exception(f"API Error: {response.status_code} - {response.text}")
            
#     except Exception as e:
#         raise Exception(f"Error processing documents with API: {e}")

# def upload_document():
#     st.header("Document Upload")

#     # Check if there was a successful submission
#     if "form_submitted" in st.session_state and st.session_state.form_submitted:
#         # Clear the flag and all related data
#         st.session_state.form_submitted = False
#         if "json_data" in st.session_state:
#             del st.session_state.json_data
#         if "document_guids" in st.session_state:
#             del st.session_state.document_guids
#         st.success("Form submitted successfully!")
#         st.rerun()

#     with st.form("document_upload_form"):
#         uploaded_files = st.file_uploader("Upload File *", type=["pdf", "docx", "eml"], accept_multiple_files=True)
#         submit = st.form_submit_button("Upload Document")
#         back = st.form_submit_button("Back")
        
#         if submit:
#             if not uploaded_files or len(uploaded_files) == 0:
#                 st.error("Please upload a file.")
#             else:
#                 try:
#                     with st.spinner("Uploading documents..."):
#                         # Create temp files for all uploaded files
#                         temp_file_paths = []
#                         file_names = []
#                         file_hashes = []
#                         guids = []
#                         document_records = []
                        
#                         # Process each file in the list
#                         for i, uploaded_file in enumerate(uploaded_files):
#                             # Save uploaded file to temp location
#                             with tempfile.NamedTemporaryFile(delete=False) as temp_file:
#                                 temp_file.write(uploaded_file.read())
#                                 temp_file_paths.append(temp_file.name)
                            
#                             # Generate unique identifier for each file
#                             # Updated: Insert datetime before file extension
#                             file_name_without_ext = os.path.splitext(uploaded_file.name)[0]
#                             file_extension = os.path.splitext(uploaded_file.name)[1]
#                             # current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds, truncate to milliseconds
#                             original_filename = f"{file_name_without_ext}{file_extension}"

#                             guid = str(uuid.uuid4())
#                             guids.append(guid)
#                             file_hash = compute_file_hash(temp_file_paths[-1])
#                             file_hashes.append(file_hash)
#                             file_names.append(uploaded_file.name)

#                             # Create unique filename with timestamp
#                             # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds, truncate to milliseconds
#                             unique_filename = f"{timestamp}_{file_hash[:8]}_{guid[:4]}{file_extension}"

#                             # Upload to Azure Blob Storage
#                             metadata = {
#                                 "guid": guid,
#                                 "original_filename": original_filename,
#                                 "Unique_filename": unique_filename,
#                                 "file_hash": file_hash,
#                                 "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                             }
                            
#                             blob_url = upload_to_blob(
#                                 file_path=temp_file_paths[-1],
#                                 blob_name=unique_filename,  # ← NOW uses enhanced filename
#                                 metadata=metadata
#                             )

#                             # Prepare document record (without JSON data for now)
#                             document_record = {
#                                 "Hash": file_hash,
#                                 "Unique_File_Name": unique_filename,
#                                 "Original_File_Name": original_filename,  # Now formatted as filename_20250111_143045.pdf
#                                 "GUID": guid,
#                                 "Blob_Link": blob_url,
#                                 "UploadDate": datetime.now(),
#                                 # .strftime("%Y-%m-%d %H:%M:%S"),
#                                 "ProcessingStatus": "Processing"
#                             }
#                             document_records.append(document_record)

#                         # Store GUIDs in session state for later use in form submission
#                         st.session_state.document_guids = guids
                        
#                         # Process all files with API together
#                         st.session_state.json_data = None
#                         with st.spinner("Extracting data from documents..."):
#                             # process_multiple_documents_with_api to handle multiple files
#                             json_data = process_multiple_documents_with_api(
#                                 file_paths=temp_file_paths,
#                                 file_names=file_names
#                             )
                            
#                             # Store in session state
#                             st.session_state.json_data = json_data

#                          # Step 3: Extract Type and Transaction Type from JSON
#                         document_type = None
#                         transaction_type = None
#                         reference_number = None  # NEW: For Policy/Claim linking


#                         if "classification" in json_data:
#                             classification = json_data.get("classification", {})
#                             document_type = classification.get("category", "")
#                             transaction_type = classification.get("subcategory", "")
#                         elif "Type" in json_data:
#                             transaction_type = json_data.get("Type", "")
#                             # Map transaction type to document type
#                             if "Policy" in transaction_type or "Business" in transaction_type:
#                                 document_type = "policy"
#                             elif "Claim" in transaction_type:
#                                 document_type = "claim"

#                         # NEW: Extract reference numbers based on document type
#                         extracted_fields = json_data.get("extracted_fields", {})
                        
#                         if document_type == "policy":
#                             # For policy documents, extract POLICY_NO
#                             reference_number = extracted_fields.get("POLICY_NO", None)
#                         elif document_type == "claim":
#                             # For claim documents, extract CLAIM_NO
#                             reference_number = extracted_fields.get("CLAIM_NO", None)
                        
#                         # Fallback: Try to extract from top level if not found in extracted_fields
#                         if not reference_number:
#                             if document_type == "policy":
#                                 reference_number = json_data.get("POLICY_NO", None)
#                             elif document_type == "claim":
#                                 reference_number = json_data.get("CLAIM_NO", None)

#                         # Step 4: Update document records with JSON data and insert into database
#                         for i, record in enumerate(document_records):
#                             record.update({
#                                 "JSON": json.dumps(json_data),
#                                 "Type": document_type,
#                                 "Transaction_Type": transaction_type,
#                                 "Reference_Number": reference_number,  # NEW: Add reference number Policy_No or Claim_No
#                                 "ProcessingStatus": "Completed"
#                             })
                            
#                             # Insert into UploadDocument table
#                             try:
#                                 insert_upload_document(record)
#                                 st.success(f"Document {record['Original_File_Name']} logged successfully!")
#                             except Exception as db_error:
#                                 st.warning(f"Failed to log document {record['Original_File_Name']}: {db_error}")
                        
#                         # Clean up temp files
#                         for file_path in temp_file_paths:
#                             os.remove(file_path)
                        
#                         st.success(f"{len(uploaded_files)} document(s) uploaded successfully!")
                        
#                         display_upload_summary(document_records, json_data)

#                 except Exception as e:
#                     st.error(f"Upload failed: {e}")
        
#         if back:
#             clear_session_state()
#             st.session_state.submission_mode = None
#             if "json_data" in st.session_state:
#                 del st.session_state.json_data
#             st.rerun()
#     return st.session_state.json_data if 'json_data' in st.session_state else None

def upload_document():
    correlation_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_app_event(
            log_level="INFO",
            message="Document upload session started",
            module_name="Document_Upload",
            action_type="UPLOAD_START",
            function_name="upload_document",
            correlation_id=correlation_id
        )

        st.header("Document Upload")

        # Check if there was a successful submission
        if "form_submitted" in st.session_state and st.session_state.form_submitted:
            st.session_state.form_submitted = False
            if "json_data" in st.session_state:
                del st.session_state.json_data
            if "document_guids" in st.session_state:
                del st.session_state.document_guids
            st.success("Form submitted successfully!")
            st.rerun()

        with st.form("document_upload_form"):
            uploaded_files = st.file_uploader("Upload File *", type=["pdf", "docx", "eml"], accept_multiple_files=True)
            submit = st.form_submit_button("Upload Document")
            back = st.form_submit_button("Back")
            
            if submit:
                if not uploaded_files or len(uploaded_files) == 0:
                    st.error("Please upload a file.")
                else:
                    try:
                        upload_start_time = time.time()

                        with st.spinner("Uploading documents..."):
                            # Initialize collections
                            temp_file_paths = []
                            file_names = []
                            file_hashes = []
                            guids = []
                            document_records = []
                            
                            # Process each file in the list
                            for i, uploaded_file in enumerate(uploaded_files):
                                file_start_time = time.time()
                                
                                try:
                                    # Save uploaded file to temp location
                                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                                        temp_file.write(uploaded_file.read())
                                        temp_file_paths.append(temp_file.name)
                                    
                                    # Generate unique identifiers
                                    file_name_without_ext = os.path.splitext(uploaded_file.name)[0]
                                    file_extension = os.path.splitext(uploaded_file.name)[1]
                                    original_filename = f"{file_name_without_ext}{file_extension}"

                                    guid = str(uuid.uuid4())
                                    guids.append(guid)
                                    file_hash = compute_file_hash(temp_file_paths[-1])
                                    file_hashes.append(file_hash)
                                    file_names.append(uploaded_file.name)

                                    # Create unique filename with timestamp
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]
                                    unique_filename = f"{timestamp}_{file_hash[:8]}_{guid[:4]}{file_extension}"

                                    # Upload to Azure Blob Storage
                                    metadata = {
                                        "guid": guid,
                                        "original_filename": original_filename,
                                        "unique_filename": unique_filename,
                                        "file_hash": file_hash,
                                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "file_size": str(uploaded_file.size)
                                    }
                                    
                                    blob_url = upload_to_blob(
                                        file_path=temp_file_paths[-1],
                                        blob_name=unique_filename,
                                        metadata=metadata
                                    )

                                    # Prepare document record
                                    document_record = {
                                        "Hash": file_hash,
                                        "Unique_File_Name": unique_filename,
                                        "Original_File_Name": original_filename,
                                        "GUID": guid,
                                        "Blob_Link": blob_url,
                                        "UploadDate": datetime.now(),
                                        "ProcessingStatus": "Processing"
                                    }
                                    document_records.append(document_record)
                                    
                                    # FIXED: Log each file upload correctly
                                    log_document_operation(
                                        action_type="FILE_UPLOADED",
                                        document_info={
                                            'file_name': uploaded_file.name,
                                            'file_size_kb': uploaded_file.size / 1024,
                                            'file_hash': file_hash,
                                            'blob_url': blob_url,
                                            'guid': guid
                                        },
                                        correlation_id=correlation_id,
                                        execution_time_ms=int((time.time() - file_start_time) * 1000)
                                    )
                                    
                                except Exception as file_error:
                                    log_error(
                                        error=file_error,
                                        module_name="Document_Upload",
                                        function_name="upload_document",
                                        correlation_id=correlation_id,
                                        additional_data={"file_name": uploaded_file.name, "file_index": i}
                                    )
                                    st.error(f"Failed to process file {uploaded_file.name}: {file_error}")
                                    continue

                            # FIXED: Performance logging OUTSIDE the loop
                            total_upload_time = int((time.time() - upload_start_time) * 1000)
                            log_performance("upload_multiple_documents", total_upload_time, correlation_id=correlation_id)

                            # Store GUIDs in session state for later use
                            st.session_state.document_guids = guids
                            
                            # Process all files with API together
                            if temp_file_paths:  # Only if we have successfully processed files
                                st.session_state.json_data = None
                                with st.spinner("Extracting data from documents..."):
                                    try:
                                        json_data = process_multiple_documents_with_api(
                                            file_paths=temp_file_paths,
                                            file_names=file_names
                                        )
                                        st.session_state.json_data = json_data
                                    except Exception as api_error:
                                        log_error(
                                            error=api_error,
                                            module_name="Document_AI",
                                            function_name="process_multiple_documents_with_api",
                                            correlation_id=correlation_id
                                        )
                                        st.error(f"API processing failed: {api_error}")
                                        json_data = {"error": "API processing failed"}

                                # Extract document classification
                                document_type = None
                                transaction_type = None
                                reference_number = None

                                if "classification" in json_data:
                                    classification = json_data.get("classification", {})
                                    document_type = classification.get("category", "")
                                    transaction_type = classification.get("subcategory", "")
                                elif "Type" in json_data:
                                    transaction_type = json_data.get("Type", "")
                                    if "Policy" in transaction_type or "Business" in transaction_type:
                                        document_type = "policy"
                                    elif "Claim" in transaction_type:
                                        document_type = "claim"

                                # Extract reference numbers
                                extracted_fields = json_data.get("extracted_fields", {})
                                if document_type == "policy":
                                    reference_number = extracted_fields.get("POLICY_NO", None)
                                elif document_type == "claim":
                                    reference_number = extracted_fields.get("CLAIM_NO", None)
                                
                                # Fallback extraction
                                if not reference_number:
                                    if document_type == "policy":
                                        reference_number = json_data.get("POLICY_NO", None)
                                    elif document_type == "claim":
                                        reference_number = json_data.get("CLAIM_NO", None)

                                # Update document records and insert into database
                                successful_inserts = 0
                                for i, record in enumerate(document_records):
                                    try:
                                        record.update({
                                            "JSON": json.dumps(json_data),
                                            "Type": document_type,
                                            "Transaction_Type": transaction_type,
                                            "Reference_Number": reference_number,
                                            "ProcessingStatus": "Completed"
                                        })
                                        
                                        insert_upload_document(record)
                                        successful_inserts += 1
                                        st.success(f"Document {record['Original_File_Name']} logged successfully!")
                                        
                                    except Exception as db_error:
                                        log_error(
                                            error=db_error,
                                            module_name="Document_Upload",
                                            function_name="insert_upload_document",
                                            correlation_id=correlation_id,
                                            additional_data={"document_guid": record.get("GUID")}
                                        )
                                        st.warning(f"Failed to log document {record['Original_File_Name']}: {db_error}")

                                # Clean up temp files
                                for file_path in temp_file_paths:
                                    try:
                                        os.remove(file_path)
                                    except Exception as cleanup_error:
                                        print(f"Warning: Could not remove temp file {file_path}: {cleanup_error}")
                                
                                st.success(f"{successful_inserts}/{len(uploaded_files)} document(s) uploaded successfully!")
                                
                                if successful_inserts > 0:
                                    display_upload_summary(document_records, json_data)
                            else:
                                st.error("No files were successfully processed.")

                    except Exception as e:
                        log_error(
                            error=e,
                            module_name="Document_Upload",
                            function_name="upload_document",
                            correlation_id=correlation_id
                        )
                        st.error(f"Upload failed: {e}")
            
            if back:
                clear_session_state()
                st.session_state.submission_mode = None
                if "json_data" in st.session_state:
                    del st.session_state.json_data
                st.rerun()
                
        return st.session_state.json_data if 'json_data' in st.session_state else None

    finally:
        # FIXED: Always log session end
        total_session_time = int((time.time() - start_time) * 1000)
        log_app_event(
            log_level="INFO",
            message="Document upload session completed",
            module_name="Document_Upload",
            action_type="UPLOAD_END",
            function_name="upload_document",
            correlation_id=correlation_id,
            execution_time_ms=total_session_time
        )

        
# Define field templates for each transaction type
POLICY_NB_FIELDS = ['CUST_ID', 'EXECUTIVE', 'Broker_Name', 'Facility_Name', 'BODY', 'MAKE', 'MODEL', 'USE_OF_VEHICLE', 'MODEL_YEAR', 'CHASSIS_NO', 'REGN', 'POLICY_NO', 'POL_EFF_DATE', 'POL_EXPIRY_DATE', 'SUM_INSURED', 'POL_ISSUE_DATE', 'PREMIUM2', 'DRV_DOB', 'DRV_DLI', 'VEH_SEATS', 'PRODUCT', 'POLICYTYPE', 'NATIONALITY']

POLICY_RENEWAL_FIELDS = ['EXECUTIVE', 'BODY', 'MAKE', 'MODEL', 'USE_OF_VEHICLE', 'MODEL_YEAR', 'REGN', 'SUM_INSURED', 'PREMIUM2', 'DRV_DOB', 'DRV_DLI', 'VEH_SEATS', 'PRODUCT', 'POLICYTYPE', 'NATIONALITY']

POLICY_MTA_FIELDS = ['BODY', 'MAKE', 'MODEL', 'USE_OF_VEHICLE', 'MODEL_YEAR', 'REGN', 'SUM_INSURED', 'PREMIUM2', 'DRV_DOB', 'DRV_DLI', 'VEH_SEATS', 'PRODUCT', 'POLICYTYPE']

POLICY_CANCEL_FIELDS = ['cancel_date', 'premium2']

CLAIM_UPDATE_FIELDS = ['INTIMATED_AMOUNT', 'INTIMATED_SF', 'TYPE', 'CLAIM_STATUS', 'CLAIM_REMARKS']

CLAIM_CLOSE_FIELDS = ['FINAL_SETTLEMENT_AMOUNT', 'CLAIM_CLOSURE_DATE', 'CLAIM_STATUS', 'CLAIM_REMARKS']

CLAIM_REOPEN_FIELDS = ['CLAIM_STATUS', 'REOPEN_REASON']

CLAIMS_NB_FIELDS = ['POLICY_NO', 'DATE_OF_ACCIDENT', 'DATE_OF_INTIMATION', 'PLACE_OF_LOSS', 'CLAIM_TYPE', 'INTIMATED_AMOUNT', 'EXECUTIVE', 'NATIONALITY', 'INTIMATED_SF', 'ACCOUNT_CODE']


def build_guid_fields(guids):
    """Build GUID fields dictionary for database insertion - store all GUIDs in single column with comma separator"""
    guid_fields = {}
    
    if guids:
        # Join all GUIDs with comma separator and store in single GUID column
        guid_fields["GUID"] = ",".join(guids)
    
    return guid_fields

# Fetch json data from json.json file
def fetch_json_data():
    """Fetch JSON data from a file"""
    try:
        data = upload_document()

        # Check if json_data is None or not valid
        if data is None:
            st.warning("Upload document.")
            return None

        # Handle the new JSON structure that contains files_processed
        if "files_processed" in data:
            st.success(f"Processed {len(data['files_processed'])} files: {', '.join(data['files_processed'])}")
            
            # Extract classification
            classification = data.get("classification", {})
            subcategory = classification.get("subcategory", "")
            category = classification.get("category", "")
            
            # Extract the fields
            extracted_fields = data.get("extracted_fields", {})
            
            
            # Clean up numeric fields that might have formatting
            if "SUM_INSURED" in extracted_fields and extracted_fields["SUM_INSURED"]:
                # Remove non-numeric characters like "AED" and commas
                sum_insured = extracted_fields["SUM_INSURED"]
                if isinstance(sum_insured, str):
                    sum_insured = ''.join(c for c in sum_insured if c.isdigit() or c == '.')
                    try:
                        extracted_fields["SUM_INSURED"] = float(sum_insured)
                    except ValueError:
                        pass

            if "INTIMATED_AMOUNT" in extracted_fields and extracted_fields["INTIMATED_AMOUNT"]:
                # Remove non-numeric characters like commas
                intimated_amount = extracted_fields["INTIMATED_AMOUNT"]
                if isinstance(intimated_amount, str):
                    intimated_amount = ''.join(c for c in intimated_amount if c.isdigit() or c == '.')
                    try:
                        extracted_fields["INTIMATED_AMOUNT"] = float(intimated_amount)
                    except ValueError:
                        pass

            if "PREMIUM2" in extracted_fields and extracted_fields["PREMIUM2"]:
                # Remove non-numeric characters like "AED" and commas
                premium = extracted_fields["PREMIUM2"]
                if isinstance(premium, str):
                    premium = ''.join(c for c in premium if c.isdigit() or c == '.')
                    try:
                        extracted_fields["PREMIUM2"] = float(premium)
                    except ValueError:
                        pass
            if "INTIMATED_SF" in extracted_fields and extracted_fields["INTIMATED_SF"]:
                # Remove non-numeric characters like commas
                intimated_sf = extracted_fields["INTIMATED_SF"]
                if isinstance(intimated_sf, str):
                    intimated_sf = ''.join(c for c in intimated_sf if c.isdigit() or c == '.')
                    try:
                        extracted_fields["INTIMATED_SF"] = float(intimated_sf)
                    except ValueError:
                        pass

            # Convert other numeric fields
            for field in ["MODEL_YEAR", "VEH_SEATS", "CUST_ID"]:
                if field in extracted_fields and extracted_fields[field]:
                    try:
                        extracted_fields[field] = int(extracted_fields[field])
                    except ValueError:
                        pass
                        
            normalized_data = {
                "Type": subcategory if subcategory else category,
                **extracted_fields  # Add all extracted fields directly
            }
            
            st.write("Extracted JSON Data:", normalized_data)
            return normalized_data
            
        # Fall back to the old format for backward compatibility
        elif "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
            # Extract document classification
            classification = data["results"][0].get("classification", {})
            subcategory = classification.get("subcategory", "")
            # category = classification.get("category", "")

            # Extract just the fields
            extracted_fields = data["results"][0].get("extracted_fields", {})

            # Clean up numeric fields that might have formatting
            if "SUM_INSURED" in extracted_fields and extracted_fields["SUM_INSURED"]:
                # Remove non-numeric characters like "AED" and commas
                sum_insured = extracted_fields["SUM_INSURED"]
                if isinstance(sum_insured, str):
                    sum_insured = ''.join(c for c in sum_insured if c.isdigit() or c == '.')
                    try:
                        extracted_fields["SUM_INSURED"] = float(sum_insured)
                    except ValueError:
                        pass

            if "PREMIUM2" in extracted_fields and extracted_fields["PREMIUM2"]:
                # Remove non-numeric characters like "AED" and commas
                premium = extracted_fields["PREMIUM2"]
                if isinstance(premium, str):
                    premium = ''.join(c for c in premium if c.isdigit() or c == '.')
                    try:
                        extracted_fields["PREMIUM2"] = float(premium)
                    except ValueError:
                        pass

            # Convert other numeric fields
            for field in ["MODEL_YEAR", "VEH_SEATS", "CUST_ID"]:
                if field in extracted_fields and extracted_fields[field]:
                    try:
                        extracted_fields[field] = int(extracted_fields[field])
                    except ValueError:
                        pass
                normalized_data = {
                    "Type": subcategory if subcategory else "New Business",
                    **extracted_fields  # Add all extracted fields directly
                }
                st.write("Extracted JSON Data:", normalized_data)
                return normalized_data
        else:
            st.write("JSON Data Loaded:", data)
            return data
    except Exception as e:
        st.error(f"Error loading JSON data: {e}")
        return None

def load_policy_from_json():
    """Load policy data from JSON and route to appropriate form"""
    try:
        data = fetch_json_data()
        if not data:
            return False
        
        policy_type = data.get("Type", "")
        
        # For Renewal policies, first fetch the existing policy to get complete data
        if policy_type == "Renewal":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    query = f"SELECT * FROM New_Policy WHERE POLICY_NO = '{policy_no}'"
                    result = fetch_data(query)
                    if result:
                        # Store the original policy data in session state for renewal processing
                        st.session_state.renewal_policy_data = result[0]
                        st.session_state.renewal_policy_fetched = True
                        
                        # Combine JSON data with existing policy data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in POLICY_RENEWAL_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]

                        st.session_state.form_to_show = "policy_renewal_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("Renewal JSON missing POLICY_NO field")
                return False
        
        # Handle other policy types
        elif policy_type == "New Business":
            st.session_state.form_to_show = "policy_manual_form"
            st.session_state.form_defaults = data
            return True
        elif policy_type == "MTA":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    # query = f"SELECT * FROM Policy WHERE POLICY_NO = '{policy_no}'"
                    # result = fetch_data(query)
                    result = _fetch_latest_policy(policy_no)
                    if result:
                        # Show already cancelled or Lapsed warning at initial state
                        if result[0].get("isCancelled", 0) == 1:
                            st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                        elif result[0].get("isLapsed", 0) == 1:
                            st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
                        # Store the original policy data in session state for MTA processing
                        else:
                            st.session_state.mta_policy_data = result[0]
                            st.session_state.mta_policy_fetched = True

                        # Combine JSON data with existing policy data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in POLICY_MTA_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]

                        st.session_state.form_to_show = "policy_mta_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("MTA JSON missing POLICY_NO field")
                return False
        elif policy_type == "Policy Cancellation":
            policy_no = data.get("POLICY_NO", "")
            if policy_no:
                # Fetch complete policy data from DB
                try:
                    # query = f"SELECT * FROM New_Policy WHERE POLICY_NO = '{policy_no}'"
                    # result = fetch_data(query)
                    result = _fetch_latest_policy(policy_no)
                    if result:
                        # Show already cancelled or Lapsed warning
                        if result[0].get("isCancelled", 0) == 1:
                            st.warning(f"Policy {policy_no} is already cancelled.", icon="❌")
                            return False
                        elif result[0].get("isLapsed", 0) == 1:
                            st.warning(f"Policy {policy_no} is already lapsed.", icon="❌")
                            return False
                            
                        # Store the original policy data in session state for cancellation processing
                        st.session_state.cancel_policy_data = result[0]
                        st.session_state.cancel_policy_fetched = True
                        
                        # Combine JSON data with existing policy data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in POLICY_CANCEL_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]

                        st.session_state.form_to_show = "policy_cancel_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Policy {policy_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching policy: {e}")
                    return False
            else:
                st.error("Cancellation JSON missing POLICY_NO field")
                return False
        elif policy_type == "New Claim":
            st.session_state.form_to_show = "claim_manual_form"
            st.session_state.form_defaults = data
            return True
        
        elif policy_type == "Claim Update":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    # query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    # result = fetch_data(query)
                    result = _fetch_latest_claims(claim_no)
                    if result:
                        # Check if claim is already closed
                        claim_status = result[0].get("CLAIM_STATUS", "")
                        # Fix: Check if claim_status is None before calling lower()
                        if claim_status and claim_status.lower() == "closed":
                            st.warning(f"Claim {claim_no} is already closed and cannot be updated.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for update processing
                        st.session_state.claim_update_data = result[0]
                        st.session_state.claim_update_fetched = True
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in CLAIM_UPDATE_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]

                        st.session_state.form_to_show = "claim_update_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Update JSON missing CLAIM_NO field")
                return False
        
        elif policy_type == "Claim Closure":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    # query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    # result = fetch_data(query)
                    result = _fetch_latest_claims(claim_no)
                    if result:
                        # Check if claim is already closed
                        claim_status = result[0].get("CLAIM_STATUS", "")
                        # Fix: Check if claim_status is None before calling lower()
                        if claim_status and claim_status.lower() == "closed":
                            st.warning(f"Claim {claim_no} is already closed.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for close processing
                        st.session_state.claim_close_data = result[0]
                        st.session_state.claim_close_fetched = True
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in CLAIM_CLOSE_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]

                        st.session_state.form_to_show = "claim_close_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Close JSON missing CLAIM_NO field")
                return False
        
        elif policy_type == "Claim Reopen":
            claim_no = data.get("CLAIM_NO", "")
            if claim_no:
                try:
                    # query = f"SELECT * FROM Claims WHERE CLAIM_NO = '{claim_no}'"
                    # result = fetch_data(query)
                    result = _fetch_latest_claims(claim_no)
                    if result:
                        # Check if claim is currently closed (must be closed to reopen)
                        claim_status = result[0].get("CLAIM_STATUS", "")
                        # Fix: Check if claim_status is None before calling lower()
                        if not claim_status or claim_status.lower() != "closed":
                            st.warning(f"Claim {claim_no} is not closed and cannot be reopened.", icon="❌")
                            return False
                        
                        # Store the original claim data in session state for reopen processing
                        st.session_state.claim_reopen_data = result[0]
                        st.session_state.claim_reopen_fetched = True
                        
                        # Add current date to the remarks
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        original_remarks = result[0].get("CLAIM_REMARKS", "")
                        reopen_reason = data.get("REOPEN_REASON", "No reason provided")
                        new_remarks = f"{original_remarks}\n\nReopened on {current_date}: {reopen_reason}"
                        data["CLAIM_REMARKS"] = new_remarks
                        
                        # Combine JSON data with existing claim data (JSON overrides DB)
                        # combined_data = {**result[0], **data}
                        combined_data = result[0].copy()
                        for field in CLAIM_REOPEN_FIELDS:
                            if field in data:
                                combined_data[field] = data[field]
                                
                        st.session_state.form_to_show = "claim_reopen_form"
                        st.session_state.form_defaults = combined_data
                        return True
                    else:
                        st.warning(f"Claim {claim_no} not found in database.")
                        return False
                except Exception as e:
                    st.error(f"Error fetching claim: {e}")
                    return False
            else:
                st.error("Claim Reopen JSON missing CLAIM_NO field")
                return False
            
        else:
            st.error(f"Unknown policy type: {policy_type}")
            return False
    except Exception as e:
        st.error(f"Error loading policy data: {e}")
        return False

def show_policy_form():

    if hasattr(st.session_state, "form_to_show") and st.session_state.form_to_show:
        defaults = st.session_state.get("form_defaults", {})

        if st.session_state.form_to_show == "policy_manual_form":
            st.markdown("### NEW BUSINESS FORM")

            ###### Early Policy Number Validation
            policy_no_to_check = defaults.get("POLICY_NO", "").strip()
            
            if policy_no_to_check:
                try:
                    # Check if policy already exists in database
                    existing_policy = _fetch_latest_policy(policy_no_to_check)
                    
                    if existing_policy and len(existing_policy) > 0:
                        # Policy already exists - show warning and don't open form
                        st.error(f"❌ Policy number '{policy_no_to_check}' already exists in the database!")
                        st.warning("Cannot create a new business policy with an existing policy number.")
                        
                        # Show existing policy details
                        with st.expander("Existing Policy Details", expanded=True):
                            policy_data = existing_policy[0]
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.text_input("Policy No", value=policy_data.get("POLICY_NO", ""), disabled=True)
                                st.text_input("Customer ID", value=str(policy_data.get("CUST_ID", "")), disabled=True)
                                st.text_input("Executive", value=policy_data.get("EXECUTIVE", ""), disabled=True)
                            
                            with col2:
                                st.text_input("Make", value=policy_data.get("MAKE", ""), disabled=True)
                                st.text_input("Model", value=policy_data.get("MODEL", ""), disabled=True)
                                st.text_input("Transaction Type", value=policy_data.get("TransactionType", ""), disabled=True)
                            
                            with col3:
                                st.text_input("Premium", value=str(policy_data.get("PREMIUM2", "")), disabled=True)
                                st.text_input("Sum Insured", value=str(policy_data.get("SUM_INSURED", "")), disabled=True)
                                st.text_input("Status", 
                                            value="Cancelled" if policy_data.get("isCancelled") == 1 
                                                  else "Lapsed" if policy_data.get("isLapsed") == 1 
                                                  else "Active", 
                                            disabled=True)
                        
                        # Provide action buttons
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button("Try Different Transaction", type="primary", use_container_width=True):
                                st.info("**Suggestions:**\n- Use **MTA** to modify existing policy\n- Use **Renewal** to renew existing policy\n- Use **Cancellation** to cancel existing policy")
                        
                        with col_btn2:
                            if st.button("Edit Policy Number", type="secondary", use_container_width=True):
                                st.info("Please upload a new document with a different policy number for New Business.")
                        
                        with col_btn3:
                            if st.button("↩️ Back to Upload", use_container_width=True):
                                clear_session_state()
                                st.session_state.policy_edit_page = "main"
                                st.session_state.submission_mode = None
                                if "form_to_show" in st.session_state:
                                    del st.session_state.form_to_show
                                if "form_defaults" in st.session_state:
                                    del st.session_state.form_defaults
                                st.rerun()
                        
                        return  # Exit the function without showing the form
                        
                except Exception as e:
                    st.error(f"Error checking policy existence: {e}")
                    # Continue to form if there's an error checking (failsafe)

            ###### Early Policy Number Validation End

            # Add system generated fields before calling form
            policy_no_current = defaults.get("POLICY_NO", "").strip()
            session_key_root = "manual_policy_submission"
            stored_policy_no = st.session_state.get(f"{session_key_root}_policy_no")
            
            if (stored_policy_no != policy_no_current) or (f"{session_key_root}_dt" not in st.session_state):
                # Generate and snap to SQL datetime precision
                submission_dt_obj = datetime.now()
                st.session_state[f"{session_key_root}_dt"] = submission_dt_obj
                st.session_state[f"{session_key_root}_policy_no"] = policy_no_current
                st.session_state[f"{session_key_root}_uid"] = _build_unique_id(policy_no_current, submission_dt_obj)

            submission_dt_obj = st.session_state[f"{session_key_root}_dt"]
            unique_id_val = st.session_state[f"{session_key_root}_uid"]
            form_data, submit, back = policy_manual_form(defaults)

            if submit:
                if not form_data["POLICY_NO"].strip():
                    st.error("Fill all the mandatory fields.")
                else:
                    # Add system generated fields to form data
                    form_data.update({
                        "TransactionType": "New Business",
                        "Submission_Date": submission_dt_obj,
                        "Unique_ID": _build_unique_id(form_data["POLICY_NO"], submission_dt_obj)
                    })

                    # Add GUID fields if available from document upload
                    guid_string = None
                    if "document_guids" in st.session_state:
                        guid_fields = build_guid_fields(st.session_state.document_guids)
                        form_data.update(guid_fields)
                        guid_string = guid_fields.get("GUID")  # ADD THIS LINE

                    try:
                        insert_policy(form_data)

                        # Update document table with policy Unique_ID
                        if guid_string:
                            print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {form_data['Unique_ID']}")
                            update_document_unique_id(guid_string, form_data["Unique_ID"])
                        else:
                            print("DEBUG: No GUID string found, skipping document update")
                        _clear_new_policy_generated_keys()  # clear generated keys post-insert

                        clear_session_state()

                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        if "form_to_show" in st.session_state:
                            del st.session_state.form_to_show
                        if "form_defaults" in st.session_state:
                            del st.session_state.form_defaults
                        st.success("New Business form submitted successfully.")
                        time.sleep(5)
                        st.rerun()
                    except Exception as db_exc:
                        st.error(f"Failed to insert policy: {db_exc}")
            if back:
                clear_session_state()

                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()


        elif st.session_state.form_to_show == "policy_renewal_form":
            defaults = st.session_state.get("form_defaults", {})
            form_data, submit_renewal, back_renewal = policy_renewal_form(defaults)

            if submit_renewal:
                try:
                    original = st.session_state.renewal_policy_data
                    submission_dt = datetime.now()
                    new_row = original.copy()
                    new_row.update(form_data)
                    new_row.update({
                        "TransactionType": "Renewal",
                        "Submission_Date": submission_dt,
                        "Unique_ID": _build_unique_id(original.get("POLICY_NO",""), submission_dt)
                    })

                    # Add GUID fields if available from document upload
                    guid_string = None
                    if "document_guids" in st.session_state:
                        guid_fields = build_guid_fields(st.session_state.document_guids)
                        new_row.update(guid_fields)
                        guid_string = guid_fields.get("GUID")  # ADD THIS LINE

                    insert_policy(new_row)
                    
                    # Update document table with policy Unique_ID
                    if guid_string:
                        print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                        update_document_unique_id(guid_string, new_row["Unique_ID"])
                    else:
                        print("DEBUG: No GUID string found, skipping document update")

                    st.session_state.renewal_inserted_data = new_row
                    st.session_state.show_renewal_summary = True
                    keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "renewal_policy_fetched", 
                            "renewal_policy_data",
                            "renewal_updated_data", 
                            "renewal_changes"
                        ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("Renewal transaction inserted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Renewal insert failed: {e}")
                # Collect changed fields as per your logic
                # edit_fields = {}
                # original_policy = st.session_state.renewal_policy_data

                # for key, new_value in form_data.items():
                #     if key in original_policy:
                #         original_value = original_policy[key]
                #         # Handle date fields
                #         if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                #             if hasattr(original_value, 'date'):
                #                 original_date = original_value.date()
                #             elif isinstance(original_value, str):
                #                 try:
                #                     if ' ' in original_value:
                #                         original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
                #                     else:
                #                         original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
                #                 except:
                #                     original_date = original_value
                #             else:
                #                 original_date = original_value
                #             if new_value != original_date:
                #                 edit_fields[key] = new_value
                #         else:
                #             if str(new_value) != str(original_value):
                #                 edit_fields[key] = new_value

                # Always update the dates
                # edit_fields["POL_ISSUE_DATE"] = form_data["POL_ISSUE_DATE"]
                # edit_fields["POL_EFF_DATE"] = form_data["POL_EFF_DATE"]
                # edit_fields["POL_EXPIRY_DATE"] = form_data["POL_EXPIRY_DATE"]

                # if edit_fields:
                #     try:
                #         update_policy(original_policy["POLICY_NO"], edit_fields)
                #         clear_session_state()

                #         st.session_state.policy_edit_page = "main"
                #         st.session_state.submission_mode = None

                #         keys_to_delete = [
                #             "form_to_show", 
                #             "form_defaults", 
                #             "renewal_policy_fetched", 
                #             "renewal_policy_data",
                #             "renewal_updated_data", 
                #             "renewal_changes"
                #         ]

                #         for key in keys_to_delete:
                #             if key in st.session_state:
                #                 del st.session_state[key]
                    
                #         st.success("Renewal updated successfully.")
                #         time.sleep(2)
                #         st.rerun()
                #     except Exception as e:
                #         st.error(f"Renewal update failed: {e}")
                # else:
                #     st.info("No fields were modified.")

            if back_renewal:
                clear_session_state()

                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()
        
        elif st.session_state.form_to_show == "policy_mta_form":
            defaults = st.session_state.get("form_defaults", {})
            form_data, submit_mta, back_mta = policy_mta_form(defaults)
            
            if submit_mta:
                try:
                    original = st.session_state.mta_policy_data
                    submission_dt = datetime.now()
                    new_row = original.copy()
                    new_row.update(form_data)
                    new_row.update({
                        "TransactionType": "MTA",
                        "Submission_Date": submission_dt,
                        "Unique_ID": _build_unique_id(original.get("POLICY_NO",""), submission_dt)
                    })
                    
                    # Add GUID fields if available from document upload
                    guid_string = None
                    if "document_guids" in st.session_state:
                        guid_fields = build_guid_fields(st.session_state.document_guids)
                        new_row.update(guid_fields)
                        guid_string = guid_fields.get("GUID")  # ADD THIS LINE

                    insert_policy(new_row)
                    
                    # Update document table with policy Unique_ID
                    if guid_string:
                        print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                        update_document_unique_id(guid_string, new_row["Unique_ID"])
                    else:
                        print("DEBUG: No GUID string found, skipping document update")

                    st.session_state.mta_inserted_data = new_row
                    st.session_state.show_mta_summary = True
                    keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "mta_policy_fetched", 
                            "mta_policy_data"
                        ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success("MTA transaction inserted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"MTA insert failed: {e}")
                # Collect changed fields as per your logic
                # edit_fields = {}
                # original_policy = st.session_state.mta_policy_data

                # for key, new_value in form_data.items():
                #     if key in original_policy:
                #         original_value = original_policy[key]
                #         # Handle date fields
                #         if key in ["POL_EFF_DATE", "POL_EXPIRY_DATE", "POL_ISSUE_DATE", "DRV_DOB", "DRV_DLI"]:
                #             if hasattr(original_value, 'date'):
                #                 original_date = original_value.date()
                #             elif isinstance(original_value, str):
                #                 try:
                #                     if ' ' in original_value:
                #                         original_date = datetime.strptime(original_value[:10], "%Y-%m-%d").date()
                #                     else:
                #                         original_date = datetime.strptime(original_value, "%Y-%m-%d").date()
                #                 except:
                #                     original_date = original_value
                #             else:
                #                 original_date = original_value
                #             if new_value != original_date:
                #                 edit_fields[key] = new_value
                #         else:
                #             if str(new_value) != str(original_value):
                #                 edit_fields[key] = new_value



                # if edit_fields:
                #     try:
                #         update_policy(original_policy["POLICY_NO"], edit_fields)
                #         clear_session_state()
                #         st.session_state.policy_edit_page = "main"
                #         st.session_state.submission_mode = None
                #         keys_to_delete = [
                #             "form_to_show", 
                #             "form_defaults", 
                #             "mta_policy_fetched", 
                #             "mta_policy_data"
                #         ]

                #         for key in keys_to_delete:
                #             if key in st.session_state:
                #                 del st.session_state[key]
                        
                #         st.success("MTA updated successfully.")
                #         time.sleep(2)
                #         st.rerun()
                #     except Exception as e:
                #         st.error(f"MTA update failed: {e}")
                # else:
                #     st.info("No fields were modified.")

            if back_mta:
                clear_session_state()
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                if "mta_policy_fetched" in st.session_state:
                    del st.session_state.mta_policy_fetched
                if "mta_policy_data" in st.session_state:
                    del st.session_state.mta_policy_data
                st.rerun()

        elif st.session_state.form_to_show == "claim_manual_form":
            show_claims_form(defaults)
        
        elif st.session_state.form_to_show == "policy_cancel_form":
            st.markdown("### POLICY CANCELLATION FORM")
            defaults = st.session_state.get("form_defaults", {})
            
            # Display the cancellation form with combined defaults
            form_data, submit_cancel, back_cancel = policy_cancel_form(defaults)

            if submit_cancel:
                new_premium = form_data["PREMIUM2"]
                cancel_date = form_data["CANCELLATION_DATE"]
                confirm_cancel = form_data.get("confirm_cancel", False)
                original = st.session_state.cancel_policy_data
                original_premium = st.session_state.cancel_policy_data.get("PREMIUM2", 0)
                # Validate cancellation form data
                if not form_data.get("confirm_cancel", False):
                    st.warning("Please confirm cancellation by checking the box before submitting.")
                else:
                    original_policy = st.session_state.cancel_policy_data
                    new_premium = form_data["PREMIUM2"]
                    original_premium = original_policy.get("PREMIUM2", 0)
                    cancel_date = form_data["CANCELLATION_DATE"]
                    
                    # Validate return premium doesn't exceed original premium
                    if float(new_premium) > float(original_premium):
                        st.error("Return Premium cannot exceed the original premium.")
                    else:
                        try:
                            # Process the cancellation
                            # Build new transaction row (do NOT modify original row)
                            submission_dt = datetime.now()
                            new_row = original.copy()
                            negative_premium = -abs(float(new_premium) if new_premium is not None else 0)
                            # update_policy(
                            #     original_policy["POLICY_NO"],
                            #     {
                            #         "isCancelled": 1,
                            #         "PREMIUM2": int(negative_premium),
                            #         "CANCELLATION_DATE": str(cancel_date),
                            #         "TransactionType": "Policy Cancellation"
                            #     }
                            # )

                            new_row.update({
                                "PREMIUM2": -abs(int(new_premium) if new_premium else 0),
                                "CANCELLATION_DATE": str(cancel_date),
                                "isCancelled": 1,
                                "TransactionType": "Policy Cancellation",
                                "Submission_Date": submission_dt,
                                "Unique_ID": _build_unique_id(original.get("POLICY_NO",""), submission_dt)
                            })

                            # Add GUID fields if available from document upload
                            guid_string = None
                            if "document_guids" in st.session_state:
                                guid_fields = build_guid_fields(st.session_state.document_guids)
                                new_row.update(guid_fields)
                                guid_string = guid_fields.get("GUID")  # ADD THIS LINE

                            insert_policy(new_row)
                            
                            # Update document table with policy Unique_ID
                            if guid_string:
                                print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                                update_document_unique_id(guid_string, new_row["Unique_ID"])
                            else:
                                print("DEBUG: No GUID string found, skipping document update")

                            st.success(f"Cancellation transaction inserted for policy {original['POLICY_NO']}.")
                            time.sleep(3)
                            
                            # Clean up session state and return to main
                            clear_session_state()
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "cancel_policy_fetched", 
                                "cancel_policy_data",
                                "cancel_final_confirm"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            # st.success(f"Policy {original_policy['POLICY_NO']} cancelled successfully.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Cancellation failed: {e}")

            if back_cancel:
                clear_session_state()
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                if "cancel_policy_fetched" in st.session_state:
                    del st.session_state.cancel_policy_fetched
                if "cancel_policy_data" in st.session_state:
                    del st.session_state.cancel_policy_data
                st.rerun()

        elif st.session_state.form_to_show == "claim_update_form":
            st.markdown("### CLAIM UPDATE FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_update_data

            st.markdown(f"#### Update Claim: {claim_data.get('CLAIM_NO', '')}")
            with st.form("update_claim_form"):
                # Editable fields
                # intimated_amount = st.number_input("Intimated Amount", 
                #                                 value=float(defaults.get("INTIMATED_AMOUNT", 0)), 
                #                                 min_value=0.0, format="%.2f")

                intimated_amount_value = defaults.get("INTIMATED_AMOUNT")
                intimated_amount = st.number_input("Intimated Amount", 
                                                value=float(intimated_amount_value) if intimated_amount_value is not None else 0.0, 
                                                min_value=0.0, format="%.2f")
                
                
                # intimated_sf = st.number_input("Intimated SF", 
                #                             value=float(defaults.get("INTIMATED_SF", 0)), 
                #                             min_value=0.0, format="%.2f")

                intimated_sf_value = defaults.get("INTIMATED_SF")
                intimated_sf = st.number_input("Intimated SF", 
                                            value=float(intimated_sf_value) if intimated_sf_value is not None else 0.0, 
                                            min_value=0.0, format="%.2f")

                claim_type = st.selectbox("Claim Type", ["OD", "TP"], 
                                        index=0 if defaults.get("TYPE", "OD") == "OD" else 1)
                                        
                # Fix for the status dropdown to safely handle None values
                status_options = ["Under Review", "Approved", "Rejected", "Pending Documentation"]
                current_status = defaults.get("CLAIM_STATUS", "Under Review")
                
                # Ensure current_status is not None and is in the list
                if current_status is None or current_status not in status_options:
                    current_status = "Under Review"
                    
                status = st.selectbox("Status", 
                                    status_options,
                                    index=status_options.index(current_status))
                                    
                remarks = st.text_area("Remarks", value=defaults.get("CLAIM_REMARKS", ""))

                # Non-editable fields for reference
                st.markdown("#### Claim Details (Read-only)")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Date of Accident", value=str(defaults.get("DATE_OF_ACCIDENT", "")), disabled=True)
                with col2:
                    st.text_input("Place of Loss", value=defaults.get("PLACE_OF_LOSS", ""), disabled=True)
                    st.text_input("Executive", value=defaults.get("EXECUTIVE", ""), disabled=True)
                    st.text_input("Vehicle", value=f"{defaults.get('MAKE', '')} {defaults.get('MODEL', '')}", disabled=True)

                submit_update = st.form_submit_button("Update Claim")
                back_update = st.form_submit_button("Back")

                if submit_update:
                    try:
                        submission_dt = datetime.now()
                         # Build new transaction row (insert new row instead of updating)
                        # original = st.session_state.claim_data
                        original = st.session_state.claim_update_data
                        new_row = original.copy()
                        new_row.update({
                            "INTIMATED_AMOUNT": intimated_amount,
                            "INTIMATED_SF": intimated_sf,
                            "TYPE": claim_type,
                            "CLAIM_STATUS": status,
                            "CLAIM_REMARKS": remarks,
                            "CLAIM_STAGE": "Updated",
                            # System generated fields with aligned precision
                            "Submission_Date": submission_dt,
                            "Unique_ID": _build_unique_id(original.get("CLAIM_NO", ""), submission_dt)
                        })

                        # Add GUID fields if available from document upload
                        guid_string = None
                        if "document_guids" in st.session_state:
                            guid_fields = build_guid_fields(st.session_state.document_guids)
                            new_row.update(guid_fields)
                            guid_string = guid_fields.get("GUID")  # ADD THIS LINE
                
                        insert_claim(new_row)
                        
                        # Update document table with claim Unique_ID
                        if guid_string:
                            print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                            update_document_unique_id(guid_string, new_row["Unique_ID"])
                        else:
                            print("DEBUG: No GUID string found, skipping document update")

                        clear_session_state()
                        st.session_state.policy_edit_page = "main"
                        st.session_state.submission_mode = None
                        
                        # Clean up session state variables
                        keys_to_delete = [
                            "form_to_show", 
                            "form_defaults", 
                            "claim_update_fetched", 
                            "claim_update_data"
                        ]

                        for key in keys_to_delete:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.success("Claim updated successfully!")
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update claim: {e}")
                
                if back_update:
                    clear_session_state()
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_update_fetched", 
                        "claim_update_data"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()

        elif st.session_state.form_to_show == "claim_close_form":
            st.markdown("### CLAIM CLOSURE FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_close_data
            
            with st.form("close_claim_form"):
                # Closure fields
                # final_settlement = st.number_input("Final Settlement Amount *", 
                #                                 value=float(defaults.get("FINAL_SETTLEMENT_AMOUNT", 0)), 
                #                                 min_value=0.0, format="%.2f")

                # After (safe handling of None value):
                final_settlement_value = defaults.get("FINAL_SETTLEMENT_AMOUNT")
                # Convert to float only if it's not None, otherwise use 0
                final_settlement = st.number_input("Final Settlement Amount *", 
                                                value=float(final_settlement_value) if final_settlement_value is not None else 0.0, 
                                                min_value=0.0, format="%.2f")
                # closure_date = st.date_input("Closure Date *", value=datetime.strptime(defaults.get("CLAIM_CLOSURE_DATE", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date())
                # Get the closure date value with safety check
                closure_date_value = defaults.get("CLAIM_CLOSURE_DATE")
                # If value exists and is a string, try to parse it, otherwise use current date
                if closure_date_value and isinstance(closure_date_value, str):
                    try:
                        closure_date = st.date_input("Closure Date *", 
                                                    value=datetime.strptime(closure_date_value, "%Y-%m-%d").date())
                    except ValueError:
                        closure_date = st.date_input("Closure Date *", value=datetime.now())
                else:
                    closure_date = st.date_input("Closure Date *", value=datetime.now())

                closure_remarks = st.text_area("Closure Remarks *", value=defaults.get("CLAIM_REMARKS", ""))

                # Display claim summary
                st.markdown("#### Claim Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Intimated Amount", value=str(defaults.get("INTIMATED_AMOUNT", "")), disabled=True)
                with col2:
                    st.text_input("Current Status", value=defaults.get("CLAIM_STATUS", ""), disabled=True)
                    st.text_input("Claim Type", value=defaults.get("TYPE", ""), disabled=True)
                    st.text_input("Date of Accident", value=str(defaults.get("DATE_OF_ACCIDENT", "")), disabled=True)

                confirm_closure = st.checkbox("I confirm I want to close this claim")
                submit_close = st.form_submit_button("Close Claim")
                back_close = st.form_submit_button("Back")

                if submit_close:
                    if not confirm_closure:
                        st.error("Please confirm claim closure by checking the box.")
                    elif not closure_remarks.strip():
                        st.error("Please provide closure remarks.")
                    else:
                        try:
                            # closure_data = {
                            #     "FINAL_SETTLEMENT_AMOUNT": float(final_settlement),
                            #     "CLAIM_CLOSURE_DATE": closure_date,
                            #     "CLAIM_STATUS": "Closed",
                            #     "CLAIM_REMARKS": closure_remarks,
                            #     "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            #     "CLAIM_STAGE": "Closed"
                            # }
                            
                            # update_claim(claim_data["CLAIM_NO"], closure_data)
                            # Generate system metadata for closure transaction
                            submission_dt = datetime.now()
                            
                            # Build new transaction row (insert new row instead of updating)
                            original = st.session_state.claim_close_data
                            new_row = original.copy()
                            new_row.update({
                                "FINAL_SETTLEMENT_AMOUNT": float(final_settlement),
                                "CLAIM_CLOSURE_DATE": closure_date,
                                "CLAIM_STATUS": "Closed",
                                "CLAIM_REMARKS": f"{claim_data.get('CLAIM_REMARKS', '')}\n\nClosure Remarks: {closure_remarks}",
                                "CLAIM_STAGE": "Closed",
                                "Submission_Date": submission_dt,
                                "Unique_ID": _build_unique_id(original.get("CLAIM_NO", ""), submission_dt)
                            })

                            # Add GUID fields if available from document upload
                            guid_string = None
                            if "document_guids" in st.session_state:
                                guid_fields = build_guid_fields(st.session_state.document_guids)
                                new_row.update(guid_fields)
                                guid_string = guid_fields.get("GUID")  # ADD THIS LINE
                            
                            insert_claim(new_row)
                            
                            # Update document table with claim Unique_ID
                            if guid_string:
                                print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                                update_document_unique_id(guid_string, new_row["Unique_ID"])
                            else:
                                print("DEBUG: No GUID string found, skipping document update")

                            clear_session_state()
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            
                            # Clean up session state variables
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "claim_close_fetched", 
                                "claim_close_data"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success(f"Claim {claim_data['CLAIM_NO']} closed successfully!")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to close claim: {e}")
                
                if back_close:
                    clear_session_state()
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_close_fetched", 
                        "claim_close_data",
                        "json_data",
                        "submission_mode"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]

                    # Set main page state
                    st.session_state.policy_edit_page = "main"
                    
                    st.rerun()

        elif st.session_state.form_to_show == "claim_reopen_form":
            st.markdown("### CLAIM REOPEN FORM")
            defaults = st.session_state.get("form_defaults", {})
            claim_data = st.session_state.claim_reopen_data
            
            with st.form("reopen_claim_form"):
                # Reopen fields
                reason_for_reopen = st.text_area("Reason for Reopening *", 
                                                value=defaults.get("REOPEN_REASON", ""))
                reopen_date = st.date_input("Reopen Date", value=datetime.now())


                # Fix for status selection
                status_options = ["Under Review", "Pending Documentation", "Investigation"]
                current_status = defaults.get("CLAIM_STATUS", "Under Review")
                
                # Safety check
                if current_status is None or current_status not in status_options:
                    current_status = "Under Review"
        
                new_status = st.selectbox("New Status", 
                            status_options,
                            index=status_options.index(current_status))

                # Display claim summary
                st.markdown("#### Closed Claim Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("Claim No", value=defaults.get("CLAIM_NO", ""), disabled=True)
                    st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), disabled=True)
                    st.text_input("Final Settlement", value=str(defaults.get("FINAL_SETTLEMENT_AMOUNT", "")), disabled=True)
                with col2:
                    st.text_input("Closure Date", value=str(defaults.get("CLAIM_CLOSURE_DATE", "")), disabled=True)
                    st.text_input("Claim Type", value=defaults.get("TYPE", ""), disabled=True)
                    st.text_input("Executive", value=defaults.get("EXECUTIVE", ""), disabled=True)

                confirm_reopen = st.checkbox("I confirm I want to reopen this claim")
                submit_reopen = st.form_submit_button("Reopen Claim")
                back_reopen = st.form_submit_button("Back")

                if submit_reopen:
                    if not confirm_reopen:
                        st.error("Please confirm claim reopening by checking the box.")
                    elif not reason_for_reopen.strip():
                        st.error("Please provide reason for reopening.")
                    else:
                        try:
                            # reopen_data = {
                            #     "CLAIM_STATUS": new_status,
                            #     "CLAIM_STAGE": "Reopened",
                            #     "REOPEN_REASON": reason_for_reopen,
                            #     "CLAIM_REMARKS": defaults.get("CLAIM_REMARKS", ""),  # Already formatted with date and reason
                            #     "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            # }
                            
                            # update_claim(claim_data["CLAIM_NO"], reopen_data)
                            submission_dt = datetime.now()
                                
                            # Build new transaction row (insert new row instead of updating)
                            original = st.session_state.claim_reopen_data
                            new_row = original.copy()
                            new_row.update({
                                "CLAIM_STATUS": new_status,
                                "CLAIM_STAGE": "Reopened",
                                "REOPEN_REASON": reason_for_reopen,
                                "CLAIM_REMARKS": f"{claim_data.get('CLAIM_REMARKS', '')}\n\nReopened on {reopen_date}: {reason_for_reopen}",
                                "Submission_Date": submission_dt,
                                "Unique_ID": _build_unique_id(original.get("CLAIM_NO", ""), submission_dt)
                            })

                            # Add GUID fields if available from document upload
                            guid_string = None
                            if "document_guids" in st.session_state:
                                guid_fields = build_guid_fields(st.session_state.document_guids)
                                new_row.update(guid_fields)
                                guid_string = guid_fields.get("GUID")  # ADD THIS LINE
                    
                            insert_claim(new_row)

                            # Update document table with claim Unique_ID
                            if guid_string:
                                print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {new_row['Unique_ID']}")
                                update_document_unique_id(guid_string, new_row["Unique_ID"])
                            else:
                                print("DEBUG: No GUID string found, skipping document update")

                            clear_session_state()

                            # Set a flag to indicate successful submission
                            st.session_state.reopen_success = True
                            st.session_state.policy_edit_page = "main"
                            st.session_state.submission_mode = None
                            
                            # Clean up session state variables
                            keys_to_delete = [
                                "form_to_show", 
                                "form_defaults", 
                                "claim_reopen_fetched", 
                                "claim_reopen_data"
                            ]

                            for key in keys_to_delete:
                                if key in st.session_state:
                                    del st.session_state[key]
                            
                            st.success(f"Claim {claim_data['CLAIM_NO']} reopened successfully!")
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to reopen claim: {e}")
                
                if back_reopen:
                    clear_session_state()
                    st.session_state.policy_edit_page = "main"
                    st.session_state.submission_mode = None
                    
                    # Clean up session state variables
                    keys_to_delete = [
                        "form_to_show", 
                        "form_defaults", 
                        "claim_reopen_fetched", 
                        "claim_reopen_data"
                    ]

                    for key in keys_to_delete:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.rerun()

def show_claims_form(defaults):
    st.markdown("### NEW CLAIM FORM")
    # Generate claim_no if not present
    if "claim_no" not in st.session_state:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.claim_no = f"CLM{timestamp}"

    ###### Early Claim Number Validation
    claim_no_to_check = defaults.get("CLAIM_NO", st.session_state.claim_no).strip()
    
    if claim_no_to_check:
        try:
            # Check if claim already exists in database
            existing_claim = _fetch_latest_claims(claim_no_to_check)
            
            if existing_claim and len(existing_claim) > 0:
                # Claim already exists - show warning and don't open form
                st.error(f"❌ Claim number '{claim_no_to_check}' already exists in the database!")
                st.warning("Cannot create a new claim with an existing claim number.")
                
                # Show existing claim details
                with st.expander("Existing Claim Details", expanded=True):
                    claim_data = existing_claim[0]
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.text_input("Claim No", value=claim_data.get("CLAIM_NO", ""), disabled=True)
                        st.text_input("Policy No", value=claim_data.get("POLICY_NO", ""), disabled=True)
                        st.text_input("Executive", value=claim_data.get("EXECUTIVE", ""), disabled=True)
                    
                    with col2:
                        st.text_input("Claim Type", value=claim_data.get("TYPE", ""), disabled=True)
                        st.text_input("Place of Loss", value=claim_data.get("PLACE_OF_LOSS", ""), disabled=True)
                        st.text_input("Intimated Amount", value=str(claim_data.get("INTIMATED_AMOUNT", "")), disabled=True)
                    
                    with col3:
                        st.text_input("Claim Status", value=claim_data.get("CLAIM_STATUS", ""), disabled=True)
                        st.text_input("Claim Stage", value=claim_data.get("CLAIM_STAGE", ""), disabled=True)
                        st.text_input("Date of Accident", value=str(claim_data.get("DATE_OF_ACCIDENT", "")), disabled=True)
                
                # Provide action buttons
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("🔄 Try Different Transaction", type="primary", use_container_width=True):
                        st.info("💡 **Suggestions:**\n- Use **Claim Update** to modify existing claim\n- Use **Claim Closure** to close existing claim\n- Use **Claim Reopen** to reopen closed claim")
                
                with col_btn2:
                    if st.button("📝 Edit Claim Number", type="secondary", use_container_width=True):
                        st.info("Please upload a new document with a different claim number for New Claim.")
                        # Allow user to generate a new claim number
                        if st.button("🆕 Generate New Claim Number"):
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            new_claim_no = f"CLM{timestamp}"
                            st.session_state.claim_no = new_claim_no
                            st.success(f"New claim number generated: {new_claim_no}")
                            st.rerun()
                
                with col_btn3:
                    if st.button("↩️ Back to Upload", use_container_width=True):
                        clear_session_state()
                        st.session_state.claims_edit_page = "main"
                        st.session_state.submission_mode = None
                        if "claim_no" in st.session_state:
                            del st.session_state.claim_no
                        if "form_to_show" in st.session_state:
                            del st.session_state.form_to_show
                        if "form_defaults" in st.session_state:
                            del st.session_state.form_defaults
                        st.rerun()
                
                return  # Exit the function without showing the form
                
        except Exception as e:
            st.error(f"Error checking claim existence: {e}")
            # Continue to form if there's an error checking (failsafe)

    ###### Early Claim Number Validation End

    with st.form("new_claim_form"):
        col1, col2 = st.columns(2)
        with col1:
            policy_no = st.text_input("Policy No", value=defaults.get("POLICY_NO", ""), key="claim_policy_no")
            date_of_accident = st.date_input("Date of Accident", value=defaults.get("DATE_OF_ACCIDENT", date.today()), key="claim_acc_date")
            date_of_intimation = st.date_input("Date of Intimation", value=defaults.get("DATE_OF_INTIMATION", date.today()), key="claim_int_date")
            place_of_loss = st.text_input("Place of Loss", value=defaults.get("PLACE_OF_LOSS", ""), key="claim_place_loss")
            claim_type = st.selectbox("Claim Type *", ["OD", "TP"], index=0 if defaults.get("CLAIM_TYPE", "OD") == "OD" else 1, key="claim_type")
            intimated_amount = st.number_input("Intimated Amount", value=defaults.get("INTIMATED_AMOUNT", 0.0), key="claim_int_amount")

        with col2:
            executive = st.text_input("Executive *", value=defaults.get("EXECUTIVE", ""), key="claim_executive")
            nationality = st.text_input("Nationality", value=defaults.get("NATIONALITY", ""), key="claim_nationality")
            claim_no = st.text_input("Claim No", value=st.session_state.claim_no, disabled=True, key="claim_no")
            intimated_sf = st.number_input("Intimated SF", value=defaults.get("INTIMATED_SF", 0.0), key="claim_intimated_sf")
            account_code_value = st.text_input("Account Code", value=defaults.get("ACCOUNT_CODE", ""), key="claim_account_code")

        # -------- System Generated Fields (Submission_Date & Unique_ID) --------
        claim_no_current = claim_no.strip()
        session_key_root = "manual_claim_submission"
        stored_claim_no = st.session_state.get(f"{session_key_root}_claim_no")
        if (stored_claim_no != claim_no_current) or (f"{session_key_root}_dt" not in st.session_state):
            # Generate and snap to SQL datetime precision
            submission_dt_obj = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            st.session_state[f"{session_key_root}_dt"] = submission_dt_obj
            st.session_state[f"{session_key_root}_claim_no"] = claim_no_current
            st.session_state[f"{session_key_root}_uid"] = _build_unique_id(claim_no_current, submission_dt_obj)

        submission_dt_obj = st.session_state[f"{session_key_root}_dt"]
        unique_id_val = st.session_state[f"{session_key_root}_uid"]


        submit = st.form_submit_button("Submit New Claim")
        back = st.form_submit_button("Back", type="secondary")

        if submit:
            if not all([policy_no.strip(), place_of_loss.strip(), executive.strip()]):
                st.error("Please fill all mandatory fields marked with *")
            else:
                try:
                    policy_result = _fetch_latest_policy(policy_no)
                    if policy_result:
                        policy_data = policy_result[0]
                        drv_dob = policy_data.get("DRV_DOB", None)
                        if drv_dob:
                            if isinstance(drv_dob, str):
                                try:
                                    drv_dob = datetime.strptime(drv_dob, "%Y-%m-%d").date()
                                except Exception:
                                    drv_dob = None
                        if drv_dob:
                            today = date.today()
                            age = today.year - drv_dob.year - ((today.month, today.day) < (drv_dob.month, drv_dob.day))
                        else:
                            age = ""
                        if policy_data.get("isCancelled", 0) == 1:
                            st.error("Cannot create claim for cancelled policy")
                        elif policy_data.get("isLapsed", 0) == 1:
                            st.error("Cannot create claim for lapsed policy")
                        else:
                            claim_data = {
                                "Account_Code": account_code_value,
                                "DATE_OF_INTIMATION": date_of_intimation,
                                "DATE_OF_ACCIDENT": date_of_accident,
                                "PLACE_OF_LOSS": place_of_loss,
                                "CLAIM_NO": claim_no,
                                "AGE": age,
                                "TYPE": claim_type,
                                "DRIVING_LICENSE_ISSUE": policy_data.get("DRV_DLI", ""),
                                "BODY_TYPE": policy_data.get("BODY", ""),
                                "MAKE": policy_data.get("MAKE", ""),
                                "MODEL": policy_data.get("MODEL", ""),
                                "YEAR": policy_data.get("MODEL_YEAR", ""),
                                "CHASIS_NO": policy_data.get("CHASSIS_NO", ""),
                                "REG": policy_data.get("REGN", ""),
                                "SUM_INSURED": policy_data.get("SUM_INSURED", ""),
                                "POLICY_NO": policy_no,
                                "POLICY_START": policy_data.get("POL_EFF_DATE", ""),
                                "POLICY_END": policy_data.get("POL_EXPIRY_DATE", ""),
                                "INTIMATED_AMOUNT": intimated_amount,
                                "INTIMATED_SF": intimated_sf,
                                "EXECUTIVE": executive,
                                "PRODUCT": policy_data.get("PRODUCT", ""),
                                "POLICYTYPE": policy_data.get("POLICYTYPE", ""),
                                "NATIONALITY": nationality,
                                "Broker_ID": policy_data.get("Broker_ID", ""),
                                "Broker_Name": policy_data.get("Broker_Name", ""),
                                "Facility_ID": policy_data.get("Facility_ID", ""),
                                "Facility_Name": policy_data.get("Facility_Name", ""),
                                "CLAIM_STAGE": "New Claim",
                                "CLAIM_STATUS": "New Claim",
                                # "UPDATE_DATE": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                # System generated fields with aligned precision
                                "Submission_Date": submission_dt_obj,
                                "Unique_ID": unique_id_val
                            }
                            
                            # Add GUID fields if available from document upload
                            guid_string = None  # FIXED: was guid_string = {}
                            if "document_guids" in st.session_state:
                                guid_fields = build_guid_fields(st.session_state.document_guids)
                                claim_data.update(guid_fields)
                                guid_string = guid_fields.get("GUID")  # ADD THIS LINE
                
                            try:
                                insert_claim(claim_data)
                                
                                # Update document table with claim Unique_ID
                                if guid_string:
                                    print(f"DEBUG: Calling update_document_unique_id with: {guid_string}, {claim_data['Unique_ID']}")
                                    update_document_unique_id(guid_string, claim_data["Unique_ID"])
                                else:
                                    print("DEBUG: No GUID string found, skipping document update")

                                clear_session_state()
                                st.session_state.claims_edit_page = "main"
                                st.session_state.submission_mode = None
                                if "claim_no" in st.session_state:
                                    del st.session_state.claim_no
                                if "form_to_show" in st.session_state:
                                    del st.session_state.form_to_show
                                if "form_defaults" in st.session_state:
                                    del st.session_state.form_defaults
                                st.success(f"Claim {claim_no} created successfully!")
                                _clear_new_claim_generated_keys()  # Clear generated keys post-insert

                                time.sleep(5)
                                st.rerun()
                            except Exception as db_exc:
                                st.error(f"Failed to insert claim: {db_exc}")
                    else:
                        st.error("Policy not found. Please check the policy number.")
                except Exception as e:
                    st.error(f"Error fetching policy data: {e}")

        if back:
            clear_session_state()
            st.session_state.claims_edit_page = "main"
            st.session_state.submission_mode = None
            if "claim_no" in st.session_state:
                del st.session_state.claim_no
            if "form_to_show" in st.session_state:
                del st.session_state.form_to_show
            if "form_defaults" in st.session_state:
                del st.session_state.form_defaults
            st.rerun()
