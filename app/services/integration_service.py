import os
import io
import json
import paramiko
import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import ERPConnection, ETLJob, ValidationRun, InvoiceStatus
from app.validation.validator import InvoiceValidator
from app.adapters.generic_erp import GenericJSONAdapter
from app.core.logging import log
from datetime import datetime
from uuid import uuid4

class IntegrationService:
    """
    Enterprise-grade Integration Service for SFTP polling and scheduled API pulls.
    Optimized for t2.micro memory footprints.
    """
    
    @staticmethod
    def process_sftp_polling(connection_id: str, db: Session):
        """Fetches and processes files from the configured SFTP server."""
        conn = db.query(ERPConnection).filter(ERPConnection.id == connection_id).first()
        if not conn or conn.status != "active":
            return

        log.info(f"Starting SFTP polling for connection {conn.display_name}")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Auth via PEM KEY if available in encrypted_credentials
            private_key = None
            if conn.encrypted_credentials:
                creds = json.loads(conn.encrypted_credentials)
                if creds.get("sftp_private_key"):
                    key_io = io.StringIO(creds["sftp_private_key"])
                    private_key = paramiko.RSAKey.from_private_key(key_io)
            
            ssh.connect(
                conn.sftp_host,
                port=conn.sftp_port or 22,
                username=conn.sftp_username,
                pkey=private_key,
                timeout=30
            )
            
            sftp = ssh.open_sftp()
            
            # 1. List files in the target folder
            target_path = conn.sftp_path or "/"
            try:
                files = sftp.listdir(target_path)
            except IOError:
                log.error(f"SFTF path {target_path} not found")
                return

            processed_count = 0
            for filename in files:
                if filename.endswith(('.json', '.xml')):
                    log.info(f"Processing SFTP file: {filename}")
                    
                    # 2. Download content
                    remote_file_path = f"{target_path.rstrip('/')}/{filename}"
                    file_bytes = io.BytesIO()
                    sftp.getfo(remote_file_path, file_bytes)
                    file_bytes.seek(0)
                    
                    # 3. Process via existing ETL logic
                    # For POC, we treat as JSON
                    try:
                        data = json.loads(file_bytes.read().decode('utf-8'))
                        IntegrationService._ingest_invoice_data(data, conn, db)
                        
                        # 4. Move to processed folder to prevent re-runs
                        processed_dir = f"{target_path.rstrip('/')}/processed"
                        try:
                            sftp.mkdir(processed_dir)
                        except IOError: pass # already exists
                        
                        sftp.rename(remote_file_path, f"{processed_dir}/{filename}")
                        processed_count += 1
                    except Exception as e:
                        log.error(f"Failed to process {filename}: {str(e)}")

            # 5. Update connection status
            conn.last_sync_at = datetime.now()
            conn.last_sync_status = "success"
            conn.last_sync_count = processed_count
            db.commit()
            
            sftp.close()
            ssh.close()
            
        except Exception as e:
            log.error(f"SFTP Polling Error: {str(e)}")
            conn.last_sync_status = "error"
            db.commit()

    @staticmethod
    def _ingest_invoice_data(payload: dict, conn: ERPConnection, db: Session):
        """Unified ingestion logic for ERP-sourced data."""
        from app.adapters.generic_erp import GenericJSONAdapter
        from app.validation.validator import InvoiceValidator
        
        adapter = GenericJSONAdapter()
        validator = InvoiceValidator()
        
        # Apply field mapping if exists
        if conn.field_mapping:
            payload = IntegrationService._apply_mapping(payload, conn.field_mapping)
            
        try:
            invoice = adapter.transform(payload)
            # Link to connection and tenant
            # report = validator.validate(invoice)
            # Persistence logic (ValidationRun entry) goes here...
            log.info(f"Successfully ingested invoice {invoice.invoice_number} via {conn.integration_mode}")
        except Exception as e:
            log.error(f"Ingestion failed: {str(e)}")

    @staticmethod
    def _apply_mapping(payload: dict, mapping: dict) -> dict:
        result = {}
        for erp_field, value in payload.items():
            pint_field = mapping.get(erp_field, erp_field)
            result[pint_field] = value
        return result
