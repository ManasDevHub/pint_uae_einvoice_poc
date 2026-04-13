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
        
        # 1. Rule Engine Evaluation (Config-driven for presence, regex, format)
        flat_data = invoice.extract_flat_data()
        rule_errors = self.rule_engine.evaluate(flat_data)
        errors.extend(rule_errors)
        total_checks = max(len(self.rule_engine.fields_config), 51)
        
        # 2. Hardcoded Cross-field & Mathematical Calculations (Business Logic)
        calculated_line_total = sum(round(line.line_net_amount, 2) for line in invoice.lines)
        
        for line in invoice.lines:
            # PINT AE: Gross Price - Discount = Net Price check
            if line.gross_price is not None:
                expected_net = round(line.gross_price - (line.discount_amount / line.quantity if line.quantity > 0 else 0), 2)
                if abs(expected_net - line.unit_price) > 0.01:
                    errors.append(ValidationErrorItem(
                        field="unit_price",
                        error=f"A6.5: Net price {line.unit_price} != Gross {line.gross_price} - Discount/Qty",
                        severity="MEDIUM",
                        category="CALCULATION"
                    ))

            # E11: Negative quantities rejection (Except for Credit Notes - 381)
            is_credit_note = invoice.invoice_type_code == "381"
            if line.quantity < 0 and not is_credit_note:
                errors.append(ValidationErrorItem(
                    field="quantity",
                    error=f"E11: Negative Quantities not allowed for Standard Invoice. Found {line.quantity}",
                    severity="HIGH",
                    category="CALCULATION"
                ))
                
            if line.tax_category != invoice.tax_category_code:
                errors.append(ValidationErrorItem(
                    field="invoiced_item_tax_category",
                    error=f"E10: Line tax category {line.tax_category} does not match header {invoice.tax_category_code}",
                    severity="HIGH",
                    category="COMPLIANCE"
                ))
                
            if line.unit_of_measure not in ["EA", "MTR", "KGM", "HUR", "LTR", "C62"]:
                errors.append(ValidationErrorItem(
                    field="unit_of_measure",
                    error=f"A6.3: Unit of Measure ({line.unit_of_measure}) must be valid UN/ECE Rec 20.",
                    severity="HIGH",
                    category="COMPLIANCE"
                ))
                
            expected_line_tax = round(line.line_net_amount * line.tax_rate, 2)
            if abs(expected_line_tax - line.tax_amount) > 0.01:
                errors.append(ValidationErrorItem(
                    field="tax_amount",
                    error=f"A6.9: Line {line.line_id} tax {line.tax_amount} does not match rate {line.tax_rate}",
                    severity="HIGH",
                    category="CALCULATION"
                ))
                
            # UAE VAT Category Rate Enforcement (A5.4)
            if line.tax_category == "S" and line.tax_rate != 0.05:
                errors.append(ValidationErrorItem(
                    field="tax_rate",
                    error=f"Standard Tax Category (S) must have exactly 5% (0.05) rate. Found {line.tax_rate}",
                    severity="HIGH",
                    category="COMPLIANCE"
                ))
            elif line.tax_category in ["Z", "E", "O"] and line.tax_rate != 0.00:
                errors.append(ValidationErrorItem(
                    field="tax_rate",
                    error=f"Zero-rated/Exempt/OoS Category ({line.tax_category}) must have 0% rate. Found {line.tax_rate}",
                    severity="HIGH",
                    category="COMPLIANCE"
                ))
                
        # A4.1 Sum of Line Net Amounts
        if abs(calculated_line_total - invoice.totals.line_extension_amount) > 0.01:
             errors.append(ValidationErrorItem(
                field="line_extension_amount",
                error=f"A4.1: Sum of lines ({calculated_line_total}) != line_extension_amount ({invoice.totals.line_extension_amount})",
                severity="HIGH",
                category="CALCULATION"
            ))

        if abs(calculated_line_total - invoice.totals.total_without_tax) > 0.01:
            errors.append(ValidationErrorItem(
                field="total_without_tax",
                error=f"A4.2: Total without tax ({invoice.totals.total_without_tax}) != calculated lines total ({calculated_line_total})",
                severity="HIGH",
                category="CALCULATION"
            ))
            
        calculated_tax = sum(line.tax_amount for line in invoice.lines)
        if abs(calculated_tax - invoice.totals.tax_amount) > 0.01:
            errors.append(ValidationErrorItem(
                field="tax_amount",
                error=f"A4.3: Sum of line taxes ({calculated_tax}) != totals.tax_amount ({invoice.totals.tax_amount})",
                severity="HIGH",
                category="CALCULATION"
            ))
            
        expected_total = invoice.totals.total_without_tax + invoice.totals.tax_amount
        if abs(expected_total - invoice.totals.total_with_tax) > 0.01:
            errors.append(ValidationErrorItem(
                field="total_with_tax",
                error=f"A4.4: total_without_tax + tax_amount != total_with_tax ({invoice.totals.total_with_tax})",
                severity="HIGH",
                category="CALCULATION"
            ))
            
        if invoice.tax_category_code in ["Z", "E", "O"] and invoice.totals.tax_amount != 0.0:
            errors.append(ValidationErrorItem(
                field="tax_amount",
                error=f"Total tax amount must be 0 for Exempt/Zero-Rated category {invoice.tax_category_code}.",
                severity="HIGH",
                category="CALCULATION"
            ))
            
        # A5 Tax Breakdown validations
        if not invoice.tax_subtotals:
            errors.append(ValidationErrorItem(
                field="tax_subtotals",
                error="A5: Tax Breakdown is mandatory.",
                severity="HIGH",
                category="COMPLIANCE"
            ))
        else:
            calc_taxable = 0.0
            calc_tax = 0.0
            for tb in invoice.tax_subtotals:
                calc_taxable += tb.taxable_amount
                calc_tax += tb.tax_amount
                expected_tb_tax = round(tb.taxable_amount * tb.tax_rate, 2)
                if abs(expected_tb_tax - tb.tax_amount) > 0.01:
                    errors.append(ValidationErrorItem(
                        field="tax_subtotals.tax_amount",
                        error=f"A5.2: Tax Breakdown tax amount {tb.tax_amount} does not match rate {tb.tax_rate}",
                        severity="HIGH",
                        category="CALCULATION"
                    ))
            
            if abs(calc_taxable - invoice.totals.total_without_tax) > 0.01:
                errors.append(ValidationErrorItem(
                    field="tax_subtotals.taxable_amount",
                    error=f"A5.1: Sum of taxable amounts ({calc_taxable}) != total_without_tax ({invoice.totals.total_without_tax})",
                    severity="HIGH",
                    category="CALCULATION"
                ))
            if abs(calc_tax - invoice.totals.tax_amount) > 0.01:
                errors.append(ValidationErrorItem(
                    field="tax_subtotals.tax_amount",
                    error=f"A5.2: Sum of tax breakdown amounts ({calc_tax}) != totals.tax_amount ({invoice.totals.tax_amount})",
                    severity="HIGH",
                    category="CALCULATION"
                ))
            
        high_severity_errors = [e for e in errors if e.severity == "HIGH"]
        is_valid = len(high_severity_errors) == 0
        
        # 3. Metrics generation
        failed_checks = len(high_severity_errors)
        passed_checks = total_checks - failed_checks
        pass_percentage = (passed_checks / total_checks) * 100 if total_checks > 0 else 0.0
        
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
            return FieldResult(
                field=field, label=label,
                value=str(value) if (value is not None and value != "") else '— missing',
                status='fail' if failed else 'pass',
                pint_ref=pint_ref,
                error=error_map[field].error if failed else None
            )

        groups = [
            FieldGroup(group='Invoice header', fields=[
                fr('invoice_number',          'Invoice number',      invoice.invoice_number,          'A1.1'),
                fr('invoice_date',            'Invoice date',        invoice.invoice_date,            'A1.2'),
                fr('payment_due_date',        'Payment due date',    invoice.payment_due_date,        'A1.5'),
                fr('invoice_type_code',       'Invoice type code',   invoice.invoice_type_code,       'A1.3'),
                fr('payment_means_type_code', 'Payment means',       invoice.payment_means_type_code, 'A1.9'),
                fr('currency_code',           'Currency',            invoice.currency_code,           'A1.7'),
                fr('transaction_type',        'Transaction type',    invoice.transaction_type,        'A1.10'),
                fr('transaction_type_code',   'Transaction type code', invoice.transaction_type_code, 'A1.6'),
            ]),
            FieldGroup(group='Seller details', fields=[
                fr('seller_name',                    'Seller name',             invoice.seller.name,                    'A2.1'),
                fr('seller_trn',                     'Seller TRN',              invoice.seller.trn,                     'A2.3'),
                fr('seller_electronic_address',      'Electronic address',      invoice.seller.electronic_address,      'A2.2'),
                fr('seller_legal_registration',      'Legal registration',      invoice.seller.legal_registration,      'A2.4'),
                fr('seller_registration_identifier_type', 'Registration type', invoice.seller.registration_identifier_type, 'A2.5'),
                fr('seller_city',                    'City',                    invoice.seller.city,                    'A2.9'),
                fr('seller_subdivision',             'Emirate code',            invoice.seller.subdivision,             'A2.10'),
                fr('seller_country_code',            'Country code',            invoice.seller.country_code,            'A2.11'),
            ]),
            FieldGroup(group='Buyer details', fields=[
                fr('buyer_name',                    'Buyer name',           invoice.buyer.name,                    'A3.1'),
                fr('buyer_trn',                     'Buyer TRN',            invoice.buyer.trn,                     'A3.3'),
                fr('buyer_electronic_address',      'Electronic address',   invoice.buyer.electronic_address,      'A3.2'),
                fr('buyer_legal_registration',      'Legal registration',   invoice.buyer.legal_registration,      'A3.4'),
                fr('buyer_registration_identifier_type', 'Registration type', invoice.buyer.registration_identifier_type, 'A3.5'),
                fr('buyer_city',                    'City',                 invoice.buyer.city,                    'A3.9'),
                fr('buyer_subdivision',             'Emirate code',         invoice.buyer.subdivision,             'A3.10'),
                fr('buyer_country_code',            'Country code',         invoice.buyer.country_code,            'A3.11'),
            ])
        ]
        
        # Dynamically append Line Items
        for i, line in enumerate(invoice.lines):
            line_idx_label = f"Line {i+1}"
            groups.append(FieldGroup(group=f'{line_idx_label} details', fields=[
                fr('line_id', f'{line_idx_label} ID', line.line_id, 'A6.1'),
                fr('item_name', f'{line_idx_label} Item', line.item_name, 'A6.2'),
                fr('unit_of_measure', f'{line_idx_label} UoM', line.unit_of_measure, 'A6.3'),
                fr('quantity', f'{line_idx_label} Quantity', line.quantity, 'A6.4'),
                fr('unit_price', f'{line_idx_label} Unit Price', line.unit_price, 'A6.5'),
                fr('tax_category', f'{line_idx_label} Tax category', line.tax_category, 'A6.8'),
                fr('tax_rate', f'{line_idx_label} Tax rate', line.tax_rate, 'A6.9'),
                fr('tax_amount', f'{line_idx_label} Tax amount', line.tax_amount, 'A6.12'),
                fr('line_net_amount', f'{line_idx_label} Net amount', line.line_net_amount, 'A6.6'),
            ]))
            
        groups.append(FieldGroup(group='Document totals', fields=[
            fr('total_without_tax', 'Total without tax', invoice.totals.total_without_tax, 'A5.1'),
            fr('tax_amount',        'Total tax amount',  invoice.totals.tax_amount,        'A5.2'),
            fr('total_with_tax',    'Total with tax',    invoice.totals.total_with_tax,    'A5.3'),
            fr('amount_due',        'Amount due',        invoice.totals.amount_due,        'A5.4'),
        ]))
        
        return groups
