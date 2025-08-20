import hashlib
import uuid
import os
import psutil
import streamlit as st
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, Optional
from db_utils import get_db_connection
import pyodbc

class MetadataManager:
    """Comprehensive metadata management for document processing"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.processing_metrics = {}
    
    def get_enhanced_file_metadata(self, uploaded_file, file_path: str) -> Dict[str, Any]:
        """Extract comprehensive file metadata"""
        try:
            file_stats = os.stat(file_path)
            
            metadata = {
                # Basic file info
                "original_filename": uploaded_file.name,
                "file_size_bytes": uploaded_file.size,
                "file_size_mb": round(uploaded_file.size / (1024 * 1024), 4),
                "file_extension": Path(uploaded_file.name).suffix.lower(),
                "mime_type": uploaded_file.type or "application/octet-stream",
                
                # File system metadata
                "creation_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modification_time": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "access_time": datetime.fromtimestamp(file_stats.st_atime).isoformat(),
                
                # File integrity
                "file_hash_sha256": self.compute_file_hash(file_path),
                "file_hash_md5": self.compute_md5_hash(file_path),
                
                # Upload session metadata
                "upload_timestamp": datetime.now().isoformat(),
                "upload_session_id": str(uuid.uuid4()),
                "processing_start_time": datetime.now().isoformat(),
            }
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to extract file metadata: {str(e)}"}
    
    def get_user_session_metadata(self) -> Dict[str, Any]:
        """Capture user session information"""
        try:
            # Get headers safely
            headers = getattr(st, 'context', {})
            if hasattr(headers, 'headers'):
                user_agent = headers.headers.get("user-agent", "Unknown")
                client_ip = headers.headers.get("x-forwarded-for", "Unknown")
            else:
                user_agent = "Unknown"
                client_ip = "Unknown"
            
            session_metadata = {
                # Streamlit session info
                "session_id": st.session_state.get("session_id", str(uuid.uuid4())),
                "user_agent": user_agent,
                "client_ip": client_ip,
                
                # Session state tracking
                "active_tab": st.session_state.get("active_tab", "unknown"),
                "form_type": st.session_state.get("form_to_show", "none"),
                "submission_mode": st.session_state.get("submission_mode", "none"),
                
                # User workflow tracking
                "upload_count": st.session_state.get("upload_count", 0),
                "session_start_time": self.session_start.isoformat(),
                "last_activity": datetime.now().isoformat(),
                
                # Browser/client info
                "browser_language": "unknown",
                "screen_resolution": "unknown",
                "timezone": "unknown"
            }
            
            # Update upload count
            st.session_state.upload_count = st.session_state.get("upload_count", 0) + 1
            
            return session_metadata
            
        except Exception as e:
            return {"error": f"Failed to extract session metadata: {str(e)}"}
    
    def get_processing_metadata(self, api_response: Dict, processing_duration: float) -> Dict[str, Any]:
        """Capture API processing metadata"""
        try:
            metadata = {
                # API processing info
                "api_processing_time_seconds": round(processing_duration, 4),
                "api_response_status": "success" if api_response else "failed",
                "api_timestamp": datetime.now().isoformat(),
                "api_endpoint": os.getenv("API_URL", "unknown"),
                
                # Extracted data quality
                "fields_extracted_count": len(api_response.get("extracted_fields", {})) if api_response else 0,
                "extraction_confidence": api_response.get("confidence", 0) if api_response else 0,
                "processing_method": "azure_cognitive_services",
                
                # Document analysis results
                "pages_processed": api_response.get("page_count", 1) if api_response else 0,
                "text_regions_found": api_response.get("regions_count", 0) if api_response else 0,
                "tables_detected": api_response.get("tables_count", 0) if api_response else 0,
                "forms_detected": api_response.get("forms_count", 0) if api_response else 0,
                
                # Error information
                "api_errors": api_response.get("errors", []) if api_response else [],
                "warnings": api_response.get("warnings", []) if api_response else []
            }
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to extract processing metadata: {str(e)}"}
    
    def get_business_metadata(self, json_data: Dict, form_type: str) -> Dict[str, Any]:
        """Capture business-specific metadata"""
        try:
            from db_utils import fetch_data
            
            metadata = {
                # Document routing
                "auto_routed_to": form_type or "unknown",
                "routing_confidence": 1.0 if form_type else 0.0,
                "requires_manual_review": False,
                "document_category": json_data.get("Type", "unknown"),
                
                # Business validation
                "policy_found": False,
                "claim_found": False,
                "customer_found": False,
                "validation_errors": [],
                "business_rules_applied": [],
                
                # Extracted business entities
                "policy_number": json_data.get("POLICY_NO", ""),
                "claim_number": json_data.get("CLAIM_NO", ""),
                "customer_id": json_data.get("CUST_ID", ""),
                "vehicle_registration": json_data.get("REGN", ""),
                "chassis_number": json_data.get("CHASSIS_NO", "")
            }
            
            # Validate policy exists
            if metadata["policy_number"]:
                try:
                    policy_result = fetch_data(f"SELECT POLICY_NO, POLICYTYPE, isCancelled, isLapsed FROM Policy WHERE POLICY_NO = '{metadata['policy_number']}'")
                    if policy_result:
                        metadata["policy_found"] = True
                        metadata["policy_status"] = "active"
                        if policy_result[0].get("isCancelled", 0) == 1:
                            metadata["policy_status"] = "cancelled"
                        elif policy_result[0].get("isLapsed", 0) == 1:
                            metadata["policy_status"] = "lapsed"
                        metadata["policy_type"] = policy_result[0].get("POLICYTYPE", "unknown")
                    else:
                        metadata["validation_errors"].append("Policy not found in database")
                except Exception as e:
                    metadata["validation_errors"].append(f"Policy validation failed: {str(e)}")
            
            # Validate claim exists
            if metadata["claim_number"]:
                try:
                    claim_result = fetch_data(f"SELECT CLAIM_NO, CLAIM_STATUS FROM Claims WHERE CLAIM_NO = '{metadata['claim_number']}'")
                    if claim_result:
                        metadata["claim_found"] = True
                        metadata["claim_status"] = claim_result[0].get("CLAIM_STATUS", "unknown")
                    else:
                        metadata["validation_errors"].append("Claim not found in database")
                except Exception as e:
                    metadata["validation_errors"].append(f"Claim validation failed: {str(e)}")
            
            # Set manual review flag based on validation
            metadata["requires_manual_review"] = len(metadata["validation_errors"]) > 0
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to extract business metadata: {str(e)}"}
    
    def get_system_performance_metadata(self) -> Dict[str, Any]:
        """Capture system performance metrics"""
        try:
            # Get memory usage
            memory_info = psutil.virtual_memory()
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get disk usage
            disk_usage = psutil.disk_usage('/')
            
            metadata = {
                # Memory metrics
                "memory_total_gb": round(memory_info.total / (1024**3), 2),
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "memory_used_percent": memory_info.percent,
                
                # CPU metrics
                "cpu_usage_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                
                # Disk metrics
                "disk_total_gb": round(disk_usage.total / (1024**3), 2),
                "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                "disk_used_percent": round((disk_usage.used / disk_usage.total) * 100, 2),
                
                # Application metrics
                "timestamp": datetime.now().isoformat(),
                "environment": os.getenv("ENVIRONMENT", "development"),
                "application_version": "1.0.0",
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to extract performance metadata: {str(e)}"}
    
    def get_azure_blob_metadata(self, blob_url: str, container_name: str) -> Dict[str, Any]:
        """Capture Azure Blob Storage metadata"""
        try:
            metadata = {
                "blob_url": blob_url,
                "container_name": container_name,
                "storage_account": "datasonic_storage",  # From your env
                "azure_region": os.getenv("AZURE_REGION", "unknown"),
                "blob_created_time": datetime.now().isoformat(),
                "access_tier": "Hot",  # Default tier
                "encryption_enabled": True,
                "backup_enabled": False,
                "retention_days": 365
            }
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to extract Azure metadata: {str(e)}"}
    
    def create_comprehensive_metadata_record(self, 
                                           uploaded_file, 
                                           file_path: str, 
                                           json_data: Dict, 
                                           processing_duration: float,
                                           blob_url: str,
                                           form_type: str,
                                           document_guid: str) -> Dict[str, Any]:
        """Create comprehensive metadata record combining all metadata types"""
        try:
            # Get all metadata components
            file_metadata = self.get_enhanced_file_metadata(uploaded_file, file_path)
            session_metadata = self.get_user_session_metadata()
            processing_metadata = self.get_processing_metadata(json_data, processing_duration)
            business_metadata = self.get_business_metadata(json_data, form_type)
            system_metadata = self.get_system_performance_metadata()
            azure_metadata = self.get_azure_blob_metadata(blob_url, os.getenv("AZURE_CONTAINER_NAME", "documents"))
            
            # Create comprehensive record
            comprehensive_record = {
                # Core identifiers
                "metadata_id": str(uuid.uuid4()),
                "document_guid": document_guid,
                "created_timestamp": datetime.now().isoformat(),
                
                # File metadata
                "file_original_name": file_metadata.get("original_filename"),
                "file_size_bytes": file_metadata.get("file_size_bytes"),
                "file_size_mb": file_metadata.get("file_size_mb"),
                "file_extension": file_metadata.get("file_extension"),
                "mime_type": file_metadata.get("mime_type"),
                "file_hash_sha256": file_metadata.get("file_hash_sha256"),
                "file_hash_md5": file_metadata.get("file_hash_md5"),
                
                # Session metadata
                "session_id": session_metadata.get("session_id"),
                "user_agent": session_metadata.get("user_agent"),
                "client_ip": session_metadata.get("client_ip"),
                "upload_count": session_metadata.get("upload_count"),
                "session_start_time": session_metadata.get("session_start_time"),
                
                # Processing metadata
                "api_processing_time": processing_metadata.get("api_processing_time_seconds"),
                "fields_extracted_count": processing_metadata.get("fields_extracted_count"),
                "extraction_confidence": processing_metadata.get("extraction_confidence"),
                "processing_method": processing_metadata.get("processing_method"),
                "pages_processed": processing_metadata.get("pages_processed"),
                
                # Business metadata
                "document_type": business_metadata.get("document_category"),
                "auto_routed_to": business_metadata.get("auto_routed_to"),
                "routing_confidence": business_metadata.get("routing_confidence"),
                "policy_found": business_metadata.get("policy_found"),
                "claim_found": business_metadata.get("claim_found"),
                "requires_manual_review": business_metadata.get("requires_manual_review"),
                "policy_number": business_metadata.get("policy_number"),
                "claim_number": business_metadata.get("claim_number"),
                "customer_id": business_metadata.get("customer_id"),
                "validation_errors": json.dumps(business_metadata.get("validation_errors", [])),
                
                # System metadata
                "memory_used_percent": system_metadata.get("memory_used_percent"),
                "cpu_usage_percent": system_metadata.get("cpu_usage_percent"),
                "disk_used_percent": system_metadata.get("disk_used_percent"),
                "environment": system_metadata.get("environment"),
                "application_version": system_metadata.get("application_version"),
                
                # Azure metadata
                "blob_url": azure_metadata.get("blob_url"),
                "container_name": azure_metadata.get("container_name"),
                "azure_region": azure_metadata.get("azure_region"),
                
                # Combined JSON metadata for analysis
                "full_metadata_json": json.dumps({
                    "file": file_metadata,
                    "session": session_metadata,
                    "processing": processing_metadata,
                    "business": business_metadata,
                    "system": system_metadata,
                    "azure": azure_metadata
                })
            }
            
            return comprehensive_record
            
        except Exception as e:
            return {"error": f"Failed to create comprehensive metadata: {str(e)}"}
    
    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "hash_error"
    
    def compute_md5_hash(self, file_path: str) -> str:
        """Compute MD5 hash of file"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return "md5_error"
    
    def insert_metadata_record(self, metadata_record: Dict[str, Any]) -> bool:
        """Insert metadata record into database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO DocumentMetadata (
                metadata_id, document_guid, created_timestamp,
                file_original_name, file_size_bytes, file_size_mb, file_extension, mime_type,
                file_hash_sha256, file_hash_md5, session_id, user_agent, client_ip,
                upload_count, session_start_time, api_processing_time, fields_extracted_count,
                extraction_confidence, processing_method, pages_processed, document_type,
                auto_routed_to, routing_confidence, policy_found, claim_found,
                requires_manual_review, policy_number, claim_number, customer_id,
                validation_errors, memory_used_percent, cpu_usage_percent, disk_used_percent,
                environment, application_version, blob_url, container_name, azure_region,
                full_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(insert_query, (
                metadata_record.get("metadata_id"),
                metadata_record.get("document_guid"),
                metadata_record.get("created_timestamp"),
                metadata_record.get("file_original_name"),
                metadata_record.get("file_size_bytes"),
                metadata_record.get("file_size_mb"),
                metadata_record.get("file_extension"),
                metadata_record.get("mime_type"),
                metadata_record.get("file_hash_sha256"),
                metadata_record.get("file_hash_md5"),
                metadata_record.get("session_id"),
                metadata_record.get("user_agent"),
                metadata_record.get("client_ip"),
                metadata_record.get("upload_count"),
                metadata_record.get("session_start_time"),
                metadata_record.get("api_processing_time"),
                metadata_record.get("fields_extracted_count"),
                metadata_record.get("extraction_confidence"),
                metadata_record.get("processing_method"),
                metadata_record.get("pages_processed"),
                metadata_record.get("document_type"),
                metadata_record.get("auto_routed_to"),
                metadata_record.get("routing_confidence"),
                metadata_record.get("policy_found"),
                metadata_record.get("claim_found"),
                metadata_record.get("requires_manual_review"),
                metadata_record.get("policy_number"),
                metadata_record.get("claim_number"),
                metadata_record.get("customer_id"),
                metadata_record.get("validation_errors"),
                metadata_record.get("memory_used_percent"),
                metadata_record.get("cpu_usage_percent"),
                metadata_record.get("disk_used_percent"),
                metadata_record.get("environment"),
                metadata_record.get("application_version"),
                metadata_record.get("blob_url"),
                metadata_record.get("container_name"),
                metadata_record.get("azure_region"),
                metadata_record.get("full_metadata_json")
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Failed to insert metadata: {e}")
            return False

# Create global instance
metadata_manager = MetadataManager()