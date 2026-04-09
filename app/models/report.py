from pydantic import BaseModel
from typing import List, Optional

class ValidationErrorItem(BaseModel):
    field: str
    error: str
    severity: str
    category: str  # FORMAT, CALCULATION, COMPLIANCE

class ValidationMetrics(BaseModel):
    total_checks: int
    passed_checks: int
    failed_checks: int
    pass_percentage: float

class FieldResult(BaseModel):
    field: str
    label: str
    value: str
    status: str          # "pass" | "fail" | "warning"
    pint_ref: str        # e.g. "A1.1", "A2.3"
    error: Optional[str] = None

class FieldGroup(BaseModel):
    group: str
    fields: List[FieldResult]

class ValidationReport(BaseModel):
    invoice_number: Optional[str]
    is_valid: bool
    total_errors: int
    errors: List[ValidationErrorItem]
    warnings: List[ValidationErrorItem]
    metrics: ValidationMetrics
    field_results: List[FieldGroup] = []
    timestamp: str

class APIResponse(BaseModel):
    status: str
    message: str
    report: ValidationReport
