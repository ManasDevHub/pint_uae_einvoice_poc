import uuid
import time
import random
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import ClientSubmission, SubmissionValidationError, SubmissionFieldMetric

class ASPMockService:
    def __init__(self, db: Session, storage_root: str = "storage/raw_responses"):
        self.db = db
        self.storage_root = storage_root

    def submit_invoice(self, client_id: str, xml_data: str, invoice_number: str, source_filename: str = None, source_module: str = None) -> dict:
        """
        Simulates the ASP handshake: 
        1. Save initial record
        2. Simulate latency
        3. Generate response (Sync or Async)
        4. Save raw response to storage
        5. Save raw request (XML) to storage
        6. Update DB
        """
        # Step 1: Create initial submission record (auditable)
        submission = ClientSubmission(
            client_id=client_id,
            invoice_number=invoice_number,
            overall_status="Pending",
            asp_provider="UAE-ASP-GATEWAY-MOCK",
            source_filename=source_filename,
            source_module=source_module
        )
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)

        # Step 2: Simulate network latency
        start_time = time.time()
        time.sleep(random.uniform(0.1, 0.5))
        
        # Step 3: Determine outcome (Mocking logic)
        # In a real system, this would be an HTTP POST to the ASP
        is_success = "REJECT" not in xml_data.upper()
        status_code = 200 if is_success else 400
        overall_status = "Accepted" if is_success else "Rejected"
        
        response_payload = {
            "submissionId": str(uuid.uuid4()),
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "errors": [] if is_success else [
                {"code": "PINT-AE-01", "message": "Simulated rejection for testing purpose", "xpath": "//cbc:ID"}
            ]
        }

        # Step 4: Save raw response (Audit requirement)
        resp_path = self._save_raw_response(client_id, response_payload)
        
        # Step 5: Save raw request (XML Audit requirement)
        req_path = self._save_raw_request(client_id, xml_data)
        
        # Step 5: Update submission record
        latency = (time.time() - start_time) * 1000
        submission.http_status_code = status_code
        submission.overall_status = overall_status
        submission.response_time_ms = latency
        submission.raw_response_path = resp_path
        submission.raw_request_path = req_path
        
        if not is_success:
            for err in response_payload["errors"]:
                ve = SubmissionValidationError(
                    submission_id=submission.submission_id,
                    error_code=err["code"],
                    error_message=err["message"],
                    xpath_location=err["xpath"]
                )
                self.db.add(ve)
        
        # Simple sample: Add field metrics for one field
        fm = SubmissionFieldMetric(
            submission_id=submission.submission_id,
            client_id=client_id,
            field_name="Invoice ID",
            is_present=True,
            is_valid=is_success
        )
        self.db.add(fm)
        
        self.db.commit()
        return response_payload

    def _save_raw_response(self, client_id: str, payload: dict) -> str:
        now = datetime.now()
        dir_path = os.path.join(self.storage_root, "clients", client_id, str(now.year), f"{now.month:02d}")
        os.makedirs(dir_path, exist_ok=True)
        
        filename = f"response_{str(uuid.uuid4())[:8]}.json"
        full_path = os.path.join(dir_path, filename)
        
        with open(full_path, "w") as f:
            json.dump(payload, f, indent=2)
            
        return full_path

    def _save_raw_request(self, client_id: str, xml_data: str) -> str:
        now = datetime.now()
        dir_path = os.path.join(self.storage_root, "clients", client_id, str(now.year), f"{now.month:02d}")
        os.makedirs(dir_path, exist_ok=True)
        
        filename = f"request_{str(uuid.uuid4())[:8]}.xml"
        full_path = os.path.join(dir_path, filename)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(xml_data)
            
        return full_path
