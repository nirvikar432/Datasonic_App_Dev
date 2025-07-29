import streamlit as st
import tempfile
from azure.storage.blob import BlobServiceClient, ContentSettings
import uuid, hashlib, os, tempfile
import dotenv
from pathlib import Path
from datetime import datetime

dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")


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


def upload_document():
    st.header("Document Upload")
    
    # Document upload form
    with st.form("document_upload_form"):
        
        uploaded_file = st.file_uploader("Upload File *", type=["pdf", "docx", "eml"])
        
        submit = st.form_submit_button("Upload Document")
        back = st.form_submit_button("Back")
        
        if submit:
            if not uploaded_file:
                st.error("Please upload a file.")
            else:
                try:
                    with st.spinner("Uploading document..."):
                        # Save uploaded file to temp location
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(uploaded_file.read())
                            file_path = temp_file.name
                        
                        # Generate unique identifiers
                        guid = str(uuid.uuid4())
                        file_hash = compute_file_hash(file_path)
                        file_extension = os.path.splitext(uploaded_file.name)[-1]
                        
                        # Upload to Azure Blob Storage
                        metadata = {
                            "guid": guid,
                            "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        blob_url = upload_to_blob(
                            file_path=file_path,
                            blob_name=uploaded_file.name,
                            metadata=metadata
                        )
                        
                        # Clean up temp file
                        os.remove(file_path)
                        
                        # Optional: Extract document info (mock implementation)
                        # result = extract_info(uploaded_file.getvalue())
                        
                        # Insert record into database (you'll need to implement this)
                    #     insert_document_record(
                    #         file_hash=file_hash,
                    #         guid=guid,
                    #         blob_url=blob_url,
                    #         document_type=document_type
                    # )
                        
                        # Show success message
                        st.success("Document uploaded successfully!")
                        
                        # Display document details
                        st.subheader("Document Details")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**File Name:** {uploaded_file.name}")
                        with col2:
                            st.write(f"**Upload Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            st.write(f"**Document ID:** {guid}")
                            st.write(f"**File Hash:** {file_hash[:10]}...")
                except Exception as e:
                    st.error(f"Upload failed: {e}")
        
        if back:
            st.session_state.submission_mode = None
            st.rerun()

