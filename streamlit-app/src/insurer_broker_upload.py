from time import time
import streamlit as st
import json
import sys
import os
from datetime import datetime, date
import time
import random
import tempfile
import uuid
import hashlib
import requests
from pathlib import Path
import dotenv

# Use absolute import for testing
from broker_form import broker_form
from insurer_form import insurer_form

from db_utils import (
    fetch_data, insert_broker, insert_insurer, insert_upload_document, 
    update_document_unique_id, log_app_event, log_document_operation, 
    log_error, log_performance
)

# Load environment variables
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
API_URL = os.getenv("API_URL")
API_CODE = os.getenv("API_CODE")

# Ensure the parent directory is in sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Helper functions (copied from auto_loader.py)
def clear_session_state():
    """Clear all form-related session state variables"""
    keys_to_delete = [
        "form_to_show", "form_defaults", "submission_mode", "json_data", 
        "document_guids", "toba_page"
    ]
    
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    
    st.session_state.last_reset = datetime.now().timestamp()

def compute_file_hash(file_path):
    """Compute SHA-256 hash of file"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def upload_to_blob(file_path, blob_name, metadata):
    """Upload file to Azure Blob Storage"""
    from azure.storage.blob import BlobServiceClient, ContentSettings
    
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=blob_name)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True, metadata=metadata,
            content_settings=ContentSettings(content_type="application/octet-stream"))

    return blob_client.url

def process_multiple_documents_with_api(file_paths, file_names):
    """Send multiple documents to API for processing and return the extracted JSON data"""
    correlation_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        log_app_event(
            log_level="INFO",
            message=f"TOBA API call started for {len(file_paths)} documents",
            module_name="TOBA_Document_AI",
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
        
        for i, (file_path, file_name) in enumerate(zip(file_paths, file_names)):
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                    if not file_content:
                        raise ValueError(f"File {file_path} is empty")
                    
                    files[f'file{i+1}'] = (file_name, file_content, 'application/octet-stream')
            except Exception as file_error:
                raise Exception(f"Error reading file {file_path}: {file_error}")
        
        if not files:
            raise ValueError("No valid files to process")
        
        params = {'code': API_CODE}
        
        # Validate API configuration
        if not API_URL:
            raise ValueError("API_URL is not configured")
        if not API_CODE:
            raise ValueError("API_CODE is not configured")
        
        print(f"DEBUG: Making TOBA API request to {API_URL} with {len(files)} files")
        response = requests.post(API_URL, files=files, params=params, timeout=300)
        
        api_time = int((time.time() - start_time) * 1000)
        
        # Log API completion
        log_app_event(
            log_level="INFO" if response.status_code == 200 else "ERROR",
            message=f"TOBA API call completed with status {response.status_code}",
            module_name="TOBA_Document_AI",
            action_type="API_CALL_COMPLETE",
            api_endpoint=API_URL,
            api_response_code=response.status_code,
            api_response_time_ms=api_time,
            correlation_id=correlation_id
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            # Check if response has content
            if not response.text.strip():
                raise Exception("API returned empty response")
            
            try:
                result = response.json()
                print(f"DEBUG: TOBA API response received: {type(result)}")
                return result
            except ValueError as json_error:
                print(f"DEBUG: JSON parse error: {json_error}")
                print(f"DEBUG: Raw response: {response.text}")
                raise Exception(f"Invalid JSON response from API: {json_error}")
        else:
            error_msg = f"TOBA API Error: {response.status_code} - {response.text}"
            print(f"DEBUG: {error_msg}")
            raise Exception(error_msg)
            
    except requests.exceptions.Timeout:
        error_msg = "TOBA API request timed out after 300 seconds"
        log_error(
            error=Exception(error_msg),
            module_name="TOBA_Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id
        )
        raise Exception(error_msg)
        
    except requests.exceptions.ConnectionError as conn_error:
        error_msg = f"Cannot connect to TOBA API at {API_URL}: {conn_error}"
        log_error(
            error=Exception(error_msg),
            module_name="TOBA_Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id
        )
        raise Exception(error_msg)
        
    except Exception as e:
        print(f"DEBUG: Exception in TOBA process_multiple_documents_with_api: {e}")
        log_error(
            error=e,
            module_name="TOBA_Document_AI",
            function_name="process_multiple_documents_with_api",
            api_endpoint=API_URL,
            correlation_id=correlation_id,
            additional_data={
                "file_count": len(file_paths) if file_paths else 0,
                "file_names": file_names if file_names else []
            }
        )
        raise Exception(f"Error processing TOBA documents with API: {e}")

def handle_toba_fallback(file_names, toba_type):
    """Handle TOBA files when API fails"""
    fallback_data = {
        "classification": {
            "category": "toba",
            "subcategory": toba_type
        },
        "extracted_fields": {},
        "files_processed": file_names,
        "fallback_processing": True
    }
    return fallback_data

def build_guid_fields(guids):
    """Build GUID fields dictionary for database insertion"""
    guid_fields = {}
    if guids:
        guid_fields["GUID"] = ",".join(guids)
    return guid_fields

def display_upload_summary(document_records, json_data):
    """Display summary of uploaded TOBA documents and extracted data"""
    st.subheader("TOBA Upload Summary")
    
    # Document details in expandable section
    with st.expander("Document Details", expanded=False):
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
    with st.expander("Extracted TOBA Data", expanded=False):
        st.json(json_data)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", len(document_records))
    with col2:
        st.metric("Document Type", document_records[0]['Type'] if document_records else "N/A")
    with col3:
        st.metric("Transaction Type", document_records[0]['Transaction_Type'] if document_records else "N/A")

def upload_toba_document():
    """Upload TOBA document with enhanced functionality"""
    correlation_id = str(uuid.uuid4())
    start_time = time.time()

    try:
        log_app_event(
            log_level="INFO",
            message="TOBA document upload session started",
            module_name="TOBA_Document_Upload",
            action_type="UPLOAD_START",
            function_name="upload_toba_document",
            correlation_id=correlation_id
        )

        st.header("TOBA Slip Upload")

        # Check if there was a successful submission
        if "form_submitted" in st.session_state and st.session_state.form_submitted:
            st.session_state.form_submitted = False
            if "json_data" in st.session_state:
                del st.session_state.json_data
            if "document_guids" in st.session_state:
                del st.session_state.document_guids
            st.success("Form submitted successfully!")
            st.rerun()

        with st.form("toba_document_upload_form"):
            uploaded_files = st.file_uploader(
                "Upload TOBA File *", 
                type=["pdf", "docx", "eml"], 
                accept_multiple_files=True,
                help="Upload TOBA (Terms of Business Agreement) documents for Broker or Insurer onboarding"
            )
            submit = st.form_submit_button("Upload TOBA Slip")
            back = st.form_submit_button("Back")
            
            if submit:
                if not uploaded_files or len(uploaded_files) == 0:
                    st.error("Please upload a TOBA Slip.")
                else:
                    try:
                        upload_start_time = time.time()

                        with st.spinner("Uploading TOBA Slip..."):
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
                                    unique_filename = f"TOBA_{timestamp}_{file_hash[:8]}_{guid[:4]}{file_extension}"

                                    # Upload to Azure Blob Storage
                                    metadata = {
                                        "guid": guid,
                                        "original_filename": original_filename,
                                        "unique_filename": unique_filename,
                                        "file_hash": file_hash,
                                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "file_size": str(uploaded_file.size),
                                        "document_category": "TOBA"
                                    }
                                    
                                    blob_url = upload_to_blob(
                                        file_path=temp_file_paths[-1],
                                        blob_name=unique_filename,
                                        metadata=metadata
                                    )

                                    # Prepare document record for document metadata table
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
                                    
                                    # Log each file upload
                                    log_document_operation(
                                        action_type="TOBA_FILE_UPLOADED",
                                        document_info={
                                            'file_name': uploaded_file.name,
                                            'file_size_kb': uploaded_file.size / 1024,
                                            'file_hash': file_hash,
                                            'blob_url': blob_url,
                                            'guid': guid,
                                            'document_category': 'TOBA'
                                        },
                                        correlation_id=correlation_id,
                                        execution_time_ms=int((time.time() - file_start_time) * 1000)
                                    )
                                    
                                except Exception as file_error:
                                    log_error(
                                        error=file_error,
                                        module_name="TOBA_Document_Upload",
                                        function_name="upload_toba_document",
                                        correlation_id=correlation_id,
                                        additional_data={"file_name": uploaded_file.name, "file_index": i}
                                    )
                                    st.error(f"Failed to process file {uploaded_file.name}: {file_error}")
                                    continue

                            # Performance logging OUTSIDE the loop
                            total_upload_time = int((time.time() - upload_start_time) * 1000)
                            log_performance("upload_multiple_toba_documents", total_upload_time, correlation_id=correlation_id)

                            # Store GUIDs in session state for later use
                            st.session_state.document_guids = guids
                            
                            # Process all files with API together
                            if temp_file_paths:  # Only if we have successfully processed files
                                st.session_state.json_data = None
                                with st.spinner("Extracting TOBA data from documents..."):
                                    try:
                                        json_data = process_multiple_documents_with_api(
                                            file_paths=temp_file_paths,
                                            file_names=file_names
                                        )
                                        st.session_state.json_data = json_data
                                    except Exception as api_error:
                                        log_error(
                                            error=api_error,
                                            module_name="TOBA_Document_AI",
                                            function_name="process_multiple_documents_with_api",
                                            correlation_id=correlation_id
                                        )
                                        st.warning(f"API processing failed: {api_error}. Using fallback processing...")
                                        
                                        # Try to determine TOBA type from filename
                                        toba_type = "Unknown"
                                        for name in file_names:
                                            name_lower = name.lower()
                                            if "broker" in name_lower:
                                                toba_type = "Broker"
                                                break
                                            elif "insurer" in name_lower:
                                                toba_type = "Insurer"
                                                break
                                        
                                        json_data = handle_toba_fallback(file_names, toba_type)

                                # Extract document classification with defaults
                                document_type = "toba"  # DEFAULT VALUE
                                transaction_type = "unknown"  # DEFAULT VALUE
                                reference_number = None

                                # Handle API error case
                                if "error" in json_data:
                                    print(f"DEBUG: TOBA API error detected: {json_data}")
                                    document_type = "toba_error"
                                    transaction_type = "processing_failed"
                                else:
                                    # Normal processing
                                    if "classification" in json_data:
                                        classification = json_data.get("classification", {})
                                        document_type = classification.get("category", "toba")
                                        transaction_type = classification.get("subcategory", "unknown")
                                    elif "Type" in json_data:
                                        transaction_type = json_data.get("Type", "unknown")

                                    # Extract reference numbers based on transaction type ###############################################################################
                                    extracted_fields = json_data.get("extracted_fields", {})
                                    if transaction_type.lower() == "broker":
                                        reference_number = extracted_fields.get("BROKER_ID", None)
                                    elif transaction_type.lower() == "insurer":
                                        reference_number = extracted_fields.get("FACILITY_ID", None)

                                # Ensure we never have None/NULL values
                                if not document_type or document_type is None:
                                    document_type = "toba"
                                if not transaction_type or transaction_type is None:
                                    transaction_type = "unknown"

                                print(f"DEBUG: Final TOBA document_type: {document_type}, transaction_type: {transaction_type}")

                                # Update document records and insert into database
                                successful_inserts = 0
                                for i, record in enumerate(document_records):
                                    try:
                                        # Ensure all required fields have values
                                        record.update({
                                            "JSON": json.dumps(json_data) if json_data else "{}",
                                            "Type": document_type if document_type else "toba",
                                            "Transaction_Type": transaction_type if transaction_type else "unknown", 
                                            "Reference_Number": reference_number,
                                            "ProcessingStatus": "Completed" if "error" not in json_data else "Error"
                                        })
                                        
                                        print(f"DEBUG: Inserting TOBA record {i+1}: Type={record['Type']}, Transaction_Type={record['Transaction_Type']}")
                                        
                                        insert_upload_document(record)
                                        successful_inserts += 1
                                        st.success(f"TOBA Document {record['Original_File_Name']} logged successfully!")
                                        
                                    except Exception as db_error:
                                        print(f"DEBUG: Database insert failed for TOBA {record.get('Original_File_Name', 'unknown')}: {db_error}")
                                        log_error(
                                            error=db_error,
                                            module_name="TOBA_Document_Upload",
                                            function_name="insert_upload_document",
                                            correlation_id=correlation_id,
                                            additional_data={
                                                "document_guid": record.get("GUID"),
                                                "document_type": record.get("Type"),
                                                "transaction_type": record.get("Transaction_Type"),
                                                "record": record
                                            }
                                        )
                                        st.error(f"Failed to log TOBA document {record['Original_File_Name']}: {db_error}")

                                # Clean up temp files
                                for file_path in temp_file_paths:
                                    try:
                                        os.remove(file_path)
                                    except Exception as cleanup_error:
                                        print(f"Warning: Could not remove temp file {file_path}: {cleanup_error}")
                                
                                st.success(f"{successful_inserts}/{len(uploaded_files)} TOBA document(s) uploaded successfully!")
                                
                                if successful_inserts > 0:
                                    display_upload_summary(document_records, json_data)
                            else:
                                st.error("No TOBA files were successfully processed.")

                    except Exception as e:
                        log_error(
                            error=e,
                            module_name="TOBA_Document_Upload",
                            function_name="upload_toba_document",
                            correlation_id=correlation_id
                        )
                        st.error(f"TOBA Upload failed: {e}")
            
            if back:
                clear_session_state()
                st.session_state.submission_mode = None
                if "json_data" in st.session_state:
                    del st.session_state.json_data
                st.rerun()
                
        return st.session_state.json_data if 'json_data' in st.session_state else None

    finally:
        # Always log session end
        total_session_time = int((time.time() - start_time) * 1000)
        log_app_event(
            log_level="INFO",
            message="TOBA document upload session completed",
            module_name="TOBA_Document_Upload",
            action_type="UPLOAD_END",
            function_name="upload_toba_document",
            correlation_id=correlation_id,
            execution_time_ms=total_session_time
        )

# Updated fetch_json_data function
# def fetch_json_data():
#     """Fetch TOBA JSON data from document upload"""
#     try:
#         data = upload_toba_document()

#         # Check if json_data is None or not valid
#         if data is None:
#             st.warning("Upload TOBA document.")
#             return None

#         # Handle the new JSON structure for TOBA documents
#         if "files_processed" in data:
#             st.success(f"Processed {len(data['files_processed'])} TOBA files: {', '.join(data['files_processed'])}")
            
#             # Extract classification
#             classification = data.get("classification", {})
#             subcategory = classification.get("subcategory", "")
#             category = classification.get("category", "")
            
#             # Extract the fields
#             extracted_fields = data.get("extracted_fields", {})
            
#             # Clean up numeric fields for TOBA documents
#             if "COMMISSION_PERCENT" in extracted_fields and extracted_fields["COMMISSION_PERCENT"]:
#                 commission = extracted_fields["COMMISSION_PERCENT"]
#                 if isinstance(commission, str):
#                     commission = ''.join(c for c in commission if c.isdigit() or c == '.')
#                     try:
#                         extracted_fields["COMMISSION_PERCENT"] = float(commission)
#                     except ValueError:
#                         pass

#             if "PARTICIPATION_PERCENT" in extracted_fields and extracted_fields["PARTICIPATION_PERCENT"]:
#                 participation = extracted_fields["PARTICIPATION_PERCENT"]
#                 if isinstance(participation, str):
#                     participation = ''.join(c for c in participation if c.isdigit() or c == '.')
#                     try:
#                         extracted_fields["PARTICIPATION_PERCENT"] = float(participation)
#                     except ValueError:
#                         pass

#             # Convert integer fields
#             for field in ["GROUP_SIZE", "LONGEVITY_YEARS"]:
#                 if field in extracted_fields and extracted_fields[field]:
#                     try:
#                         extracted_fields[field] = int(extracted_fields[field])
#                     except ValueError:
#                         pass

#             # Handle multiple insurers for insurer TOBA
#             if subcategory == "Insurer" and "INSURERS" in extracted_fields:
#                 # For insurer TOBA, we'll process the first insurer or create a summary
#                 insurers = extracted_fields.get("INSURERS", [])
#                 if insurers:
#                     st.info(f"Found {len(insurers)} insurers in the TOBA document. Processing first insurer for form.")
#                     first_insurer = insurers[0]
#                     # Merge first insurer data with facility data
#                     extracted_fields.update(first_insurer)
                        
#             normalized_data = {
#                 "Type": subcategory if subcategory else category,
#                 **extracted_fields  # Add all extracted fields directly
#             }
            
#             st.write("Extracted TOBA JSON Data:", normalized_data)
#             return normalized_data
            
#         else:
#             st.write("TOBA JSON Data Loaded:", data)
#             return data
            
#     except Exception as e:
#         st.error(f"Error loading TOBA JSON data: {e}")
#         return None

def fetch_json_data():
    """Fetch TOBA JSON data from document upload and normalize to expected structure"""
    try:
        data = upload_toba_document()

        # Check if json_data is None or not valid
        if data is None:
            st.warning("Upload TOBA document.")
            return None

        # Handle the new JSON structure for TOBA documents
        if "files_processed" in data:
            st.success(f"Processed {len(data['files_processed'])} TOBA files: {', '.join(data['files_processed'])}")
            
            # Extract classification
            classification = data.get("classification", {})
            subcategory = classification.get("subcategory", "")
            category = classification.get("category", "")
            
            # Extract the fields
            extracted_fields = data.get("extracted_fields", {})
            
            # Handle Broker TOBA documents  
            if subcategory == "Broker":
                # Clean up commission percent
                commission = extracted_fields.get("COMMISSION_PERCENT", "")
                if isinstance(commission, str):
                    commission = ''.join(c for c in commission if c.isdigit() or c == '.')
                    try:
                        commission = float(commission)
                    except ValueError:
                        commission = 0.0
                
                # Map broker data to your expected structure
                normalized_data = {
                    "Type": "Broker",
                    "Broker_Name": extracted_fields.get("BROKER_NAME"),
                    "Commission": commission,
                    "Date_Of_Onboarding": extracted_fields.get("DATE_OF_ONBOARDING"),
                    "Longevity_Years": int(extracted_fields.get("LONGEVITY_YEARS", 0)) if extracted_fields.get("LONGEVITY_YEARS") else 0,
                    "FCA_Registration_Number": extracted_fields.get("FCA_REGISTRATION_NUMBER"),
                    "Broker_Type_Index": map_broker_type_to_index(extracted_fields.get("BROKER_TYPE", "")),
                    "Market_Access_Index": map_market_access_to_index(extracted_fields.get("MARKET_ACCESS", "")),
                    "Delegated_Authority": bool(extracted_fields.get("DELEGATED_AUTHORITY", False))
                }
            
            # Handle Insurer TOBA documents with multiple insurers
            elif subcategory == "Insurer" and "INSURERS" in extracted_fields:
                insurers_raw = extracted_fields.get("INSURERS", [])
                
                # Map the raw API response to your expected structure
                mapped_insurers = []
                for i, insurer in enumerate(insurers_raw):
                    mapped_insurer = {
                        "Insurer_Name": insurer.get("INSURER_NAME", ""),
                        "Date_Of_Onboarding": insurer.get("DATE_OF_ONBOARDING", ""),
                        "Longevity_Years": int(insurer.get("LONGEVITY_YEARS", 0)) if insurer.get("LONGEVITY_YEARS") else 0,
                        "Participation": float(insurer.get("PARTICIPATION_PERCENT", 0.0)) if insurer.get("PARTICIPATION_PERCENT") else 0.0,
                        "FCA_Registration_Number": insurer.get("FCA_REGISTRATION_NUMBER", ""),
                        "Insurer_Type_Index": map_insurer_type_to_index(insurer.get("INSURER_TYPE", "")),
                        "Delegated_Authority": bool(insurer.get("DELEGATED_AUTHORITY", False))
                    }
                    mapped_insurers.append(mapped_insurer)
                
                # Create the normalized structure for Insurer TOBA
                normalized_data = {
                    "Type": "Insurer",
                    "Facility_ID": extracted_fields.get("FACILITY_ID", ""),
                    "Facility_Name": extracted_fields.get("FACILITY_NAME", ""),
                    "Group_Size": int(extracted_fields.get("GROUP_SIZE", 0)) if extracted_fields.get("GROUP_SIZE") else 0,
                    "insurers": mapped_insurers
                }
                
                st.info(f"Found {len(mapped_insurers)} insurers in the TOBA document.")
            
            else:
                # Fallback for unknown types or direct field mapping
                normalized_data = {
                    "Type": subcategory if subcategory else category,
                    **extracted_fields
                }
            
            # st.write("Mapped TOBA JSON Data:", normalized_data)
            return normalized_data
            
        else:
            # Direct JSON data (not from API processing)
            st.write("Direct TOBA JSON Data:", data)
            return data
            
    except Exception as e:
        st.error(f"Error loading TOBA JSON data: {e}")
        return None

def map_broker_type_to_index(broker_type):
    """Map broker type string to index for your form"""
    type_mapping = {
        "Retail": 0,
        "Wholesale": 1,
        "Reinsurance": 2,
        "Coverholder": 3
    }
    return type_mapping.get(broker_type)

def map_index_to_broker_type(index):
    """Map index back to broker type string"""
    index_mapping = {
        0: "Retail",
        1: "Wholesale", 
        2: "Reinsurance",
        3: "Coverholder"
    }
    return index_mapping.get(index)

def map_market_access_to_index(market_access):
    """Map market access string to index for your form"""
    access_mapping = {
        "Lloyd’s": 0,
        "Company Market": 1,
        "Both": 2
    }
    return access_mapping.get(market_access)

def map_index_to_market_access(index):
    """Map index back to market access string"""
    index_mapping = {
        0: "Lloyd’s",
        1: "Company Market",
        2: "Both"
    }
    return index_mapping.get(index)

def map_insurer_type_to_index(insurer_type):
    """Map insurer type string to index for your form"""
    type_mapping = {
        "Direct": 0,
        "Reinsurer": 1, 
        "Broker": 2
    }
    return type_mapping.get(insurer_type)

def map_index_to_insurer_type(index):
    """Map index back to insurer type string"""
    index_mapping = {
        0: "Direct",
        1: "Reinsurer",
        2: "Broker"
    }
    return index_mapping.get(index)

def load_data_from_json():
    """Load TOBA data from JSON and route to appropriate form"""
    try:
        data = fetch_json_data()
        if not data:
            return False
        
        toba_type = data.get("Type", "")
        if toba_type == "Broker":
            st.session_state.form_to_show = "broker_manual_form"
            st.session_state.form_defaults = data
            return True
        elif toba_type == "Insurer":
            st.session_state.form_to_show = "insurer_manual_form"
            st.session_state.form_defaults = data
            return True
        else:
            st.error(f"Unknown TOBA type: {toba_type}")
            return False
    except Exception as e:
        st.error(f"Error loading TOBA data: {e}")
        return False

def show_insurer_broker_form():
    """Show insurer or broker form based on uploaded document type"""
    if hasattr(st.session_state, "form_to_show") and st.session_state.form_to_show:
        defaults = st.session_state.get("form_defaults", {})

        if st.session_state.form_to_show == "broker_manual_form":
            form_data, submit, back = broker_form(defaults)

            if submit:
                try:
                    # Add GUID fields if available from document upload
                    # Handle GUID from document upload
                    if "document_guids" in st.session_state and st.session_state.document_guids:
                        # Use the first GUID if multiple documents, or join them
                        if len(st.session_state.document_guids) == 1:
                            form_data["GUID"] = st.session_state.document_guids[0]
                        else:
                            # Multiple documents - store as comma-separated
                            form_data["GUID"] = ",".join(st.session_state.document_guids)
                        
                        print(f"DEBUG: Setting GUID in form_data: {form_data['GUID']}")
                    else:
                        # No document upload - generate a new GUID or leave as NULL
                        form_data["GUID"] = None
                        print("DEBUG: No document GUID found")

                    if not form_data.get("Submission_Date"):
                        form_data["Submission_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    insert_broker(form_data)
                    broker_id = form_data.get("Broker_ID")
                    if not broker_id:
                        # Fallback: try to get from session state or re-generate
                        st.error("Failed to get Broker_ID after insert")
                        return
                    
                    # # Update document table with broker data
                    # if guid_string:
                    #     print(f"DEBUG: Updating TOBA documents with Broker_ID: {form_data.get('Broker_ID')}")
                    #     update_document_unique_id(guid_string, form_data.get("Broker_ID", ""))
                    # else:
                    #     print("DEBUG: No GUID string found for broker, skipping document update")
                    # Update document table with broker data if document was uploaded
                    if "document_guids" in st.session_state and st.session_state.document_guids:
                        guid_string = ",".join(st.session_state.document_guids)
                        print(f"DEBUG: Updating TOBA documents with Broker_ID: {broker_id}")
                        try:
                            # Update both Unique_ID AND Reference_Number
                            update_document_unique_id(guid_string, broker_id)
                            update_document_reference_number(guid_string, broker_id)
                            print(f"DEBUG: Successfully linked documents to Broker_ID: {broker_id}")
                        except Exception as update_error:
                            print(f"DEBUG: Failed to update documents: {update_error}")
                            st.warning(f"Broker added but failed to link documents: {update_error}")
                    else:
                        print("DEBUG: No document GUIDs found for linking")

                    clear_session_state()
                    st.session_state.toba_page = "main"  # Go to main page after submit
                    st.session_state.submission_mode = None

                    if "form_to_show" in st.session_state:
                        del st.session_state.form_to_show
                    if "form_defaults" in st.session_state:
                        del st.session_state.form_defaults
                    st.success("Broker added successfully!")
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add broker: {e}")
            if back:
                clear_session_state()

                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()

        if st.session_state.form_to_show == "insurer_manual_form":
            form_data, submit, back = insurer_form(defaults)

            if submit:
                try:
                    # Add GUID fields if available from document upload
                    guid_string = None
                    if "document_guids" in st.session_state:
                        guid_fields = build_guid_fields(st.session_state.document_guids)
                        form_data.update(guid_fields)
                        guid_string = guid_fields.get("GUID")

                    insert_insurer(form_data)
                    
                    # Update document table with insurer data
                    if guid_string:
                        print(f"DEBUG: Updating TOBA documents with Facility_ID: {form_data.get('FACILITY_ID')}")
                        update_document_unique_id(guid_string, form_data.get("FACILITY_ID", ""))
                    else:
                        print("DEBUG: No GUID string found for insurer, skipping document update")
                        
                    
                    clear_session_state()
                    st.session_state.toba_page = "main"  # Go to main page after submit
                    st.session_state.submission_mode = None
                    if "form_to_show" in st.session_state:
                        del st.session_state.form_to_show
                    if "form_defaults" in st.session_state:
                        del st.session_state.form_defaults
                    st.success("Insurer added successfully!")
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to add insurer: {e}")
            if back:
                clear_session_state()
                st.session_state.policy_edit_page = "main"
                st.session_state.submission_mode = None
                if "form_to_show" in st.session_state:
                    del st.session_state.form_to_show
                if "form_defaults" in st.session_state:
                    del st.session_state.form_defaults
                st.rerun()















# from time import time
# import streamlit as st
# import json
# import sys
# import os
# from datetime import datetime, date
# import time
# import random

# # Use absolute import for testing
# from broker_form import broker_form
# from insurer_form import insurer_form


# from db_utils import fetch_data, insert_broker, insert_insurer


# # Ensure the parent directory is in sys.path for imports
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# # Fetch json data from json.json file
# def fetch_json_data():
#     """Fetch JSON data from a file"""
#     try:
#         #For Testing purposes, we can use a static file path
#         # json_files = [
#         #     "streamlit-app/utils/json/TOBA_Broker.json",
#         #     "streamlit-app/utils/json/TOBA_Insurer.json"
#         # ]
#         # selected_file = random.choice(json_files)

#         with open("streamlit-app/utils/json/TOBA_Insurer.json", "r") as f:
#         # with open(selected_file, "r") as f:
#             data = json.load(f)
#             st.write("JSON Data Loaded:", data)
#         return data
#     except Exception as e:
#         st.error(f"Error loading JSON data: {e}")
#         return None

# def load_data_from_json():
#     """Load policy data from JSON and route to appropriate form"""
#     try:
#         data = fetch_json_data()
#         if not data:
#             return False
        
#         policy_type = data.get("Type", "")
#         if policy_type == "Broker":
#             st.session_state.form_to_show = "broker_manual_form"
#             st.session_state.form_defaults = data
#             return True
#         elif policy_type == "Insurer":
#             st.session_state.form_to_show = "insurer_manual_form"
#             st.session_state.form_defaults = data
#             return True
#         else:
#             st.error(f"Unknown TOBA type: {policy_type}")
#             return False
#     except Exception as e:
#         st.error(f"Error loading TOBA data: {e}")
#         return False

# def show_insurer_broker_form():

#     if hasattr(st.session_state, "form_to_show") and st.session_state.form_to_show:
#         defaults = st.session_state.get("form_defaults", {})

#         if st.session_state.form_to_show == "broker_manual_form":
#             form_data, submit, back = broker_form(defaults)

#             if submit:
#                 try:
#                     insert_broker(form_data)
#                     # st.session_state.broker_data = form_data
#                     st.session_state.toba_page = "main"  # Go to main page after submit
#                     if "form_to_show" in st.session_state:
#                         del st.session_state.form_to_show
#                     if "form_defaults" in st.session_state:
#                         del st.session_state.form_defaults
#                     st.success("Broker added successfully!")
#                     time.sleep(5)
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Failed to add broker: {e}")
#             if back:
#                 st.session_state.toba_page = "main"
#                 st.session_state.show_broker_summary = False
#                 st.rerun()

#         if st.session_state.form_to_show == "insurer_manual_form":
#             form_data, submit, back = insurer_form(defaults)

#             if submit:
#                 try:
#                     insert_insurer(form_data)
#                     st.session_state.toba_page = "main"  # Go to main page after submit
#                     if "form_to_show" in st.session_state:
#                         del st.session_state.form_to_show
#                     if "form_defaults" in st.session_state:
#                         del st.session_state.form_defaults
#                     st.success("Insurer added successfully!")
#                     time.sleep(5)
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Failed to add insurer: {e}")
#             if back:
#                 st.session_state.toba_page = "main"
#                 st.rerun()

    

