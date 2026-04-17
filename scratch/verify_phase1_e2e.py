import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.tests.mutation_engine import XMLMutationEngine
from app.services.asp_mock import ASPMockService
from app.db.models import ClientSubmission, SubmissionValidationError
from sqlalchemy import func

def run_verification():
    db = SessionLocal()
    try:
        print("--- PHASE 1 E2E VERIFICATION ---")
        
        # 1. Initialize Engines
        template = "data/sample_invoice.xml"
        engine = XMLMutationEngine(template)
        mock_asp = ASPMockService(db)
        
        client_id = "test-enterprise-client"
        
        # 2. Scenario: Success Case
        print("\n[Scenario 1] Valid Submission...")
        mutations_valid = [
            {'xpath': '//cbc:ID', 'value': 'INV-PHASE1-SUCCESS'}
        ]
        xml_valid = engine.mutate(mutations_valid)
        res_valid = mock_asp.submit_invoice(client_id, xml_valid, "INV-PHASE1-SUCCESS")
        print(f"Outcome: {res_valid['status']} (HTTP {res_valid.get('status_code', 200)})")
        
        # 3. Scenario: Rejection Case (Mutating to trigger mock rejection)
        print("\n[Scenario 2] Rejected Submission (Mutated XML)...")
        mutations_fail = [
            {'xpath': '//cbc:ID', 'value': 'REJECT-INVOICE-001'}
        ]
        xml_fail = engine.mutate(mutations_fail)
        res_fail = mock_asp.submit_invoice(client_id, xml_fail, "REJECT-INVOICE-001")
        print(f"Outcome: {res_fail['status']}")
        
        # 4. Check Database Integrity
        print("\n[Audit] Checking Database Records...")
        subs = db.query(ClientSubmission).filter(ClientSubmission.client_id == client_id).all()
        print(f"Total Submissions found: {len(subs)}")
        
        for s in subs:
            print(f"- ID: {s.invoice_number} | Status: {s.overall_status} | Response Path: {s.raw_response_path}")
            if s.overall_status == "Rejected":
                errors = db.query(SubmissionValidationError).filter(SubmissionValidationError.submission_id == s.submission_id).all()
                print(f"  -> Errors Captured: {len(errors)}")
                for e in errors:
                    print(f"     * Error: {e.error_code} - {e.error_message}")

        # 5. Check Local Data Persistence
        if subs:
            path = subs[0].raw_response_path
            if os.path.exists(path):
                print(f"\n[Storage] Verified: Raw response file persists at {path}")
            else:
                print("\n[Storage] ERROR: Response file missing!")

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
