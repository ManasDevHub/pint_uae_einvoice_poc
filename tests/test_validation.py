import pytest
from app.models.invoice import InvoicePayload, InvoiceLineItem, DocumentTotals, SellerDetails, BuyerDetails
from app.validation.validator import InvoiceValidator
from app.adapters.generic_erp import GenericJSONAdapter

# Fixtures are automatically imported from conftest.py

def test_valid_invoice(valid_invoice):
    validator = InvoiceValidator()
    report = validator.validate(valid_invoice)
    assert report.is_valid is True
    assert report.total_errors == 0
    assert report.metrics.pass_percentage == 100.0

def test_invalid_trn_format(valid_invoice):
    valid_invoice.seller.trn = "123" # Pydantic attribute is trn, JSON alias is seller_trn
    validator = InvoiceValidator()
    report = validator.validate(valid_invoice)
    assert report.is_valid is False
    errors = [e for e in report.errors if e.field == "seller_trn"]
    assert len(errors) > 0
    assert errors[0].category == "FORMAT"
    assert errors[0].category == "FORMAT"
    
def test_calculation_mismatch(valid_invoice):
    # Mess up the totals cross check
    valid_invoice.totals.tax_amount = 300 
    validator = InvoiceValidator()
    report = validator.validate(valid_invoice)
    assert report.is_valid is False
    errors = [e for e in report.errors if e.field == "tax_amount"]
    assert len(errors) > 0
    assert errors[0].category == "CALCULATION"

def test_b2b_conditional_rule_failure(valid_invoice):
    # Rule requires B2B TRN
    valid_invoice.transaction_type = "B2B"
    valid_invoice.buyer.trn = None
    validator = InvoiceValidator()
    report = validator.validate(valid_invoice)
    assert report.is_valid is False
    errors = [e for e in report.errors if e.field == "buyer_trn"]
    assert len(errors) > 0

def test_b2c_conditional_rule_success(valid_b2c_invoice):
    validator = InvoiceValidator()
    report = validator.validate(valid_b2c_invoice)
    assert report.is_valid is True

def test_generic_adapter_b2c_inference():
    raw_payload = {
        "invoice_number": "INV-002",
        "invoice_date": "2026-04-03",
        "invoice_type_code": "380",
        "payment_means_type_code": "10",
        "tax_category_code": "S",
        "currency_code": "AED",
        "buyer": { "buyer_name": "Consumer Guy" },
        "lines": [{"item_name": "x", "quantity": 1, "unit_price": 10}]
    }
    adapter = GenericJSONAdapter()
    invoice = adapter.transform(raw_payload)
    assert invoice.transaction_type == "B2C"

def test_generic_adapter_b2b_inference():
    raw_payload = {
        "invoice_number": "INV-003",
        "invoice_date": "2026-04-03",
        "buyer": {"buyer_name": "BizCorp", "buyer_trn": "999888777666555"},
        "lines": [{"item_name": "y", "quantity": 2, "unit_price": 20}]
    }
    adapter = GenericJSONAdapter()
    invoice = adapter.transform(raw_payload)
    assert invoice.transaction_type == "B2B"

def test_metrics_integrity(valid_invoice):
    # Induce multiple errors
    valid_invoice.seller.trn = "1"
    valid_invoice.buyer.trn = "2"
    valid_invoice.totals.tax_amount = 0
    report = InvoiceValidator().validate(valid_invoice)
    assert report.metrics.total_checks == report.metrics.passed_checks + report.metrics.failed_checks
    assert report.metrics.failed_checks == report.total_errors

def test_error_category_enum(valid_invoice):
    valid_invoice.seller.trn = "1"
    valid_invoice.totals.tax_amount = 0
    report = InvoiceValidator().validate(valid_invoice)
    valid_categories = {"FORMAT", "CALCULATION", "COMPLIANCE"}
    valid_severities = {"HIGH", "MEDIUM", "LOW"}
    for error in report.errors:
        assert error.category in valid_categories
        assert error.severity in valid_severities

def test_multi_line_aggregation(valid_invoice):
    valid_invoice.lines.append(
        InvoiceLineItem(
            line_id="2", item_name="Extra", unit_of_measure="EA", quantity=2,
            unit_price=100, line_net_amount=200, tax_category="S", tax_rate=0.05, tax_amount=10
        )
    )
    valid_invoice.totals.total_without_tax = 5200
    valid_invoice.totals.tax_amount = 260
    valid_invoice.totals.total_with_tax = 5460
    valid_invoice.totals.amount_due = 5460
    report = InvoiceValidator().validate(valid_invoice)
    assert report.is_valid is True
