from datetime import datetime, timezone
import os
from app.models.invoice import InvoicePayload
from app.models.report import ValidationReport, ValidationErrorItem, ValidationMetrics, FieldResult, FieldGroup
from app.core.rules_engine import RuleEngine

DEFAULT_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "rules", "uae_pint_ae_rules.json")

class InvoiceValidator:
    def __init__(self, rules_path: str = DEFAULT_RULES_PATH):
        self.rule_engine = RuleEngine(rules_path)

    def validate(self, invoice: InvoicePayload) -> ValidationReport:
        errors = []
        
        # 1. Rule Engine Evaluation
        flat_data = invoice.extract_flat_data()
        rule_errors = self.rule_engine.evaluate(flat_data)
        errors.extend(rule_errors)
        
        # PINT AE Total Checks: Use the count from the rules engine
        total_checks = self.rule_engine.rules_loaded
        
        # 2. Mathematical & Business Rule Validation (A4, A5, A6)
        
        # A4.1 Sum of Line Net Amounts
        calculated_line_total = sum(round(line.line_net_amount or 0, 2) for line in invoice.lines)
        lea = invoice.totals.line_extension_amount
        if lea is not None and abs(calculated_line_total - lea) > 0.01:
             errors.append(ValidationErrorItem(
                field="line_extension_amount",
                error=f"A4.1: Sum of lines extension amount ({calculated_line_total}) != totals.line_extension_amount ({lea})",
                severity="HIGH", category="CALCULATION"
            ))

        # A4.2 Total Amount Without Tax
        twt = invoice.totals.total_without_tax
        if twt is not None and abs(calculated_line_total - twt) > 0.01:
            errors.append(ValidationErrorItem(
                field="total_without_tax",
                error=f"A4.2: Total without tax ({twt}) != calculated lines total ({calculated_line_total})",
                severity="HIGH", category="CALCULATION"
            ))
            
        # A4.3 Total Tax Amount
        calculated_tax = sum(line.tax_amount or 0 for line in invoice.lines)
        ta = invoice.totals.tax_amount
        if ta is not None and abs(calculated_tax - ta) > 0.01:
            errors.append(ValidationErrorItem(
                field="tax_amount",
                error=f"A4.3: Sum of line taxes ({calculated_tax}) != totals.tax_amount ({ta})",
                severity="HIGH", category="CALCULATION"
            ))
            
        # A4.4 Total Amount With Tax
        if twt is not None and ta is not None:
            expected_total = round(twt + ta, 2)
            twt_with_tax = invoice.totals.total_with_tax
            if twt_with_tax is not None and abs(expected_total - twt_with_tax) > 0.01:
                errors.append(ValidationErrorItem(
                    field="total_with_tax",
                    error=f"A4.4: total_without_tax + tax_amount ({expected_total}) != totals.total_with_tax ({twt_with_tax})",
                    severity="HIGH", category="CALCULATION"
                ))
            
        # A5 Tax Breakdown
        if not invoice.tax_subtotals:
            errors.append(ValidationErrorItem(
                field="tax_category_code",
                error="A5: Tax Breakdown (Tax Subtotals) is mandatory for PINT AE compliance.",
                severity="HIGH", category="COMPLIANCE"
            ))
        else:
            calc_taxable = round(sum(tb.taxable_amount or 0 for tb in invoice.tax_subtotals), 2)
            calc_tax_sum = round(sum(tb.tax_amount or 0 for tb in invoice.tax_subtotals), 2)
            
            if twt is not None and abs(calc_taxable - twt) > 0.01:
                errors.append(ValidationErrorItem(
                    field="tax_subtotal_taxable_amount",
                    error=f"A5.1: Sum of tax breakdown taxable amounts ({calc_taxable}) != total_without_tax ({twt})",
                    severity="HIGH", category="CALCULATION"
                ))
            if ta is not None and abs(calc_tax_sum - ta) > 0.01:
                errors.append(ValidationErrorItem(
                    field="tax_subtotal_tax_amount",
                    error=f"A5.2: Sum of tax breakdown tax amounts ({calc_tax_sum}) != totals.tax_amount ({ta})",
                    severity="HIGH", category="CALCULATION"
                ))

        # A6 Line Items Loop
        for i, line in enumerate(invoice.lines):
            line_idx = i + 1
            qty = line.quantity or 0
            up = line.unit_price or 0
            lna = line.line_net_amount or 0
            # A6.4 Line Net Amount = Qty * Net Price
            expected_net = round(qty * up, 2)
            if abs(expected_net - lna) > 0.01:
                errors.append(ValidationErrorItem(
                    field="line_net_amount",
                    error=f"A6.4: Line {line_idx} net amount {lna} != Qty * Unit Price ({expected_net})",
                    severity="HIGH", category="CALCULATION"
                ))
            
            # A6.5/A6.6/A6.7: Gross Price logic
            if line.gross_price is not None and line.gross_price > 0:
                discount_per_unit = (line.discount_amount or 0) / qty if qty > 0 else 0
                expected_unit_price = round(line.gross_price - discount_per_unit, 2)
                if abs(expected_unit_price - up) > 0.01:
                    errors.append(ValidationErrorItem(
                        field="unit_price",
                        error=f"A6.5: Line {line_idx} unit price {up} != Gross {line.gross_price} - Discount/Qty ({expected_unit_price})",
                        severity="MEDIUM", category="CALCULATION"
                    ))

            # A6.9 Tax Rate Check
            if line.tax_category == "S" and line.tax_rate != 0.05:
                errors.append(ValidationErrorItem(
                    field="line_tax_rate",
                    error=f"A6.9: Standard Category (S) must have exactly 5% (0.05) rate on Line {line_idx}.",
                    severity="HIGH", category="COMPLIANCE"
                ))
            elif line.tax_category in ["Z", "E", "O"] and line.tax_rate != 0.00:
                errors.append(ValidationErrorItem(
                    field="line_tax_rate",
                    error=f"A6.9: Zero/Exempt category ({line.tax_category}) must have 0% rate on Line {line_idx}.",
                    severity="HIGH", category="COMPLIANCE"
                ))

        high_severity_errors = [e for e in errors if e.severity == "HIGH"]
        is_valid = len(high_severity_errors) == 0
        
        # 3. Dynamic Metrics
        failed_checks = len(high_severity_errors)
        passed_checks = max(0, total_checks - failed_checks)
        pass_percentage = (passed_checks / total_checks) * 100 if total_checks > 0 else 100.0
        
        metrics = ValidationMetrics(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            pass_percentage=round(pass_percentage, 2)
        )
        
        field_results = self.build_field_results(invoice, errors)
        
        return ValidationReport(
            invoice_number=invoice.invoice_number,
            is_valid=is_valid,
            total_errors=len(errors),
            errors=high_severity_errors,
            warnings=[e for e in errors if e.severity != "HIGH"],
            metrics=metrics,
            field_results=field_results,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def build_field_results(self, invoice: InvoicePayload, errors: list) -> list:
        error_fields = {e.field for e in errors}
        error_map = {e.field: e for e in errors}

        def fr(field, label, value, pint_ref):
            failed = field in error_fields
            # Hard check for empty values to ensure UI shows "missing"
            is_empty = value is None or str(value).strip() == ""
            return FieldResult(
                field=field, label=label,
                value=str(value) if not is_empty else '— missing',
                status='fail' if failed else 'pass',
                pint_ref=pint_ref,
                error=error_map[field].error if failed else None
            )

        return [
            FieldGroup(group='A1: Invoice details', fields=[
                fr('invoice_number',          'Invoice number',      invoice.invoice_number,          'A1.1'),
                fr('invoice_date',            'Invoice date',        invoice.invoice_date,            'A1.2'),
                fr('invoice_type_code',       'Invoice type code',   invoice.invoice_type_code,       'A1.3'),
                fr('currency_code',           'Currency code',       invoice.currency_code,           'A1.4'),
                fr('payment_due_date',        'Payment due date',    invoice.payment_due_date,        'A1.5'),
                fr('transaction_type_code',   'Transaction type code', invoice.transaction_type_code, 'A1.6'),
                fr('business_process_id',     'Business process',    invoice.business_process_id,     'A1.7'),
                fr('specification_id',        'Specification ID',    invoice.specification_id,        'A1.8'),
                fr('payment_means_type_code', 'Payment means code',  invoice.payment_means_type_code, 'A1.9'),
            ]),
            FieldGroup(group='A2: Seller details', fields=[
                fr('seller_name',                    'Legal name',             invoice.seller.name,                    'A2.1'),
                fr('seller_trn',                     'Tax identifier (TRN)',   invoice.seller.trn,                     'A2.6'),
                fr('seller_electronic_address',      'Electronic address',     invoice.seller.electronic_address,      'A2.2'),
                fr('seller_electronic_scheme',       'Electronic scheme',      invoice.seller.electronic_scheme,       'A2.3'),
                fr('seller_legal_registration',      'Legal registration',     invoice.seller.legal_registration,      'A2.4'),
                fr('seller_registration_identifier_type', 'Registration type', invoice.seller.registration_identifier_type, 'A2.5'),
                fr('seller_address',                 'Address line 1',         invoice.seller.address,                 'A2.8'),
                fr('seller_city',                    'City',                   invoice.seller.city,                    'A2.9'),
                fr('seller_subdivision',             'Subdivision (Emirate)',  invoice.seller.subdivision,             'A2.10'),
                fr('seller_country_code',            'Country code',           invoice.seller.country_code,            'A2.11'),
                fr('seller_tax_scheme_id',           'Tax scheme ID',          invoice.seller.tax_scheme_id,           'A2.7'),
            ]),
            FieldGroup(group='A3: Buyer details', fields=[
                fr('buyer_name',                    'Legal name',             invoice.buyer.name,                    'A3.1'),
                fr('buyer_trn',                     'Tax identifier (TRN)',   invoice.buyer.trn,                     'A3.6'),
                fr('buyer_electronic_address',      'Electronic address',     invoice.buyer.electronic_address,      'A3.2'),
                fr('buyer_electronic_scheme',       'Electronic scheme',      invoice.buyer.electronic_scheme,       'A3.3'),
                fr('buyer_legal_registration',      'Legal registration',     invoice.buyer.legal_registration,      'A3.4'),
                fr('buyer_registration_identifier_type', 'Registration type', invoice.buyer.registration_identifier_type, 'A3.5'),
                fr('buyer_address',                 'Address line 1',         invoice.buyer.address,                 'A3.8'),
                fr('buyer_city',                    'City',                   invoice.buyer.city,                    'A3.9'),
                fr('buyer_subdivision',             'Subdivision (Emirate)',  invoice.buyer.subdivision,             'A3.10'),
                fr('buyer_country_code',            'Country code',           invoice.buyer.country_code,            'A3.11'),
                fr('buyer_tax_scheme_id',           'Tax scheme ID',          invoice.buyer.tax_scheme_id,           'A3.7'),
            ]),
            FieldGroup(group='A4: Document totals', fields=[
                fr('line_extension_amount', 'Sum of line net amounts', invoice.totals.line_extension_amount, 'A4.1'),
                fr('total_without_tax',     'Total without tax',       invoice.totals.total_without_tax,     'A4.2'),
                fr('tax_amount',            'Total tax amount',        invoice.totals.tax_amount,            'A4.3'),
                fr('total_with_tax',        'Total with tax',           invoice.totals.total_with_tax,        'A4.4'),
                fr('amount_due',            'Amount due',              invoice.totals.amount_due,            'A4.5'),
            ]),
            FieldGroup(group='A5: Tax breakdown', fields=[
                fr('tax_subtotal_taxable_amount', 'Taxable amount',   invoice.tax_subtotals[0].taxable_amount if invoice.tax_subtotals else None, 'A5.1'),
                fr('tax_subtotal_tax_amount',     'Tax amount',       invoice.tax_subtotals[0].tax_amount if invoice.tax_subtotals else None,     'A5.2'),
                fr('tax_category_code',           'Tax category code', invoice.tax_category_code,                                              'A5.3'),
                fr('tax_category_rate',           'Tax category rate', invoice.tax_subtotals[0].tax_rate if invoice.tax_subtotals else None,     'A5.4'),
            ]),
            FieldGroup(group='A6: Line items', fields=[
                fr('line_id',          'Line identifier',     invoice.lines[0].line_id if invoice.lines else None,          'A6.1'),
                fr('quantity',         'Invoiced quantity',   invoice.lines[0].quantity if invoice.lines else None,         'A6.2'),
                fr('unit_of_measure',  'Unit of measure',     invoice.lines[0].unit_of_measure if invoice.lines else None,  'A6.3'),
                fr('line_net_amount',  'Line net amount',     invoice.lines[0].line_net_amount if invoice.lines else None,  'A6.4'),
                fr('unit_price',       'Item net price',      invoice.lines[0].unit_price if invoice.lines else None,       'A6.5'),
                fr('gross_price',      'Item gross price',    invoice.lines[0].gross_price if invoice.lines else None,      'A6.6'),
                fr('price_base_qty',   'Price base quantity', invoice.lines[0].price_base_quantity if invoice.lines else None, 'A6.7'),
                fr('line_tax_category', 'Tax category',        invoice.lines[0].tax_category if invoice.lines else None,     'A6.8'),
                fr('line_tax_rate',    'Tax rate',            invoice.lines[0].tax_rate if invoice.lines else None,         'A6.9'),
                fr('item_name',        'Item name',           invoice.lines[0].item_name if invoice.lines else None,        'A6.12'),
            ]),
        ]
