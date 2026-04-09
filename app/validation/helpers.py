import pydantic
from datetime import datetime, timezone
from app.models.report import (
    ValidationReport, 
    ValidationErrorItem, 
    ValidationMetrics, 
    FieldGroup, 
    FieldResult
)

def build_report_from_error(e: pydantic.ValidationError, invoice_number: str = "Unknown") -> ValidationReport:
    """
    Transforms a Pydantic ValidationError into a structured ValidationReport 
    for UI consistency.
    """
    errors = []
    for err in e.errors():
        field_name = str(err['loc'][-1])
        msg = err['msg']
        errors.append(ValidationErrorItem(
            field=field_name,
            error=msg,
            category="FORMAT",
            severity="HIGH"
        ))
        
    metrics = ValidationMetrics(
        total_checks=len(errors),
        passed_checks=0,
        failed_checks=len(errors),
        pass_percentage=0.0
    )
    
    # Create a basic field result for the primary failing fields (up to 10)
    field_results = [
        FieldGroup(group="Schema Validation", fields=[
            FieldResult(
                field=str(err['loc'][-1]),
                label=f"Field: {str(err['loc'][-1])}",
                value="Missing/Invalid",
                status="fail",
                pint_ref="PINT AE",
                error=err['msg']
            ) for err in e.errors()[:10]
        ])
    ]
    
    return ValidationReport(
        invoice_number=invoice_number,
        is_valid=False,
        total_errors=len(errors),
        errors=errors,
        warnings=[],
        metrics=metrics,
        field_results=field_results,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
