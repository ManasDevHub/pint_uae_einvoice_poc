import json
import re
from datetime import datetime
from typing import List
from app.models.report import ValidationErrorItem

class RuleEngine:
    def __init__(self, rules_path: str):
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Support the new "fields" layout from the strict requirement
            self.fields_config = data.get("fields", [])
            
        # Optional: For metric counts
        self.rules_loaded = len(self.fields_config)

    def evaluate(self, data: dict) -> List[ValidationErrorItem]:
        errors = []
        for config in self.fields_config:
            field = config["field"]
            val = data.get(field)
            severity = config.get("severity", "HIGH")
            category = config.get("category", "COMPLIANCE")
            message = config.get("message", "Validation failed.")
            
            rules = config.get("rules", [])
            is_empty = val is None or str(val).strip() == ""
            has_error_for_field = False
            
            for rule in rules:
                if has_error_for_field:
                    break # Skip subsequent chained rules if one already failed
                
                if rule == "required":
                    if is_empty:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "required_if_b2b":
                    is_b2b = data.get("is_b2b") is True
                    if is_b2b and is_empty:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "date_format" and not is_empty:
                    try:
                        datetime.strptime(str(val), "%Y-%m-%d")
                    except ValueError:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "not_future" and not is_empty:
                    try:
                        # Only check if it passed date format effectively
                        dt = datetime.strptime(str(val), "%Y-%m-%d")
                        if dt > datetime.now():
                            errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                            has_error_for_field = True
                    except Exception:
                        pass # Format error covers it
                        
                elif rule == "valid_type_code" and not is_empty:
                    if str(val) not in ["380", "381", "386"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "valid_payment_code" and not is_empty:
                    if str(val) not in ["1", "10", "30", "31", "42", "48", "49", "58"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "must_be_ae" and not is_empty:
                    if str(val) != "AE":
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "valid_tax_category" and not is_empty:
                    if str(val) not in ["S", "Z", "E", "O"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "valid_uom" and not is_empty:
                    # EA (Each), MTR (Meter), KGM (Kilogram), HUR (Hour), LTR (Liter), C62 (Unit)
                    if str(val) not in ["EA", "MTR", "KGM", "HUR", "LTR", "C62"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "valid_currency" and not is_empty:
                    if str(val) not in ["AED", "USD", "EUR", "GBP"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                        
                elif rule == "trn_format" and not is_empty:
                    # Only enforce TRN format for B2B or if explicitly provided for B2C
                    # For B2C, we skip format check if the field contains junk dictionary strings from mapping
                    is_b2b = data.get("is_b2b") is True
                    if not is_b2b and (str(val).startswith("{") or "consumer" in str(val).lower()):
                        continue # Skip junk for B2C
                        
                    if not re.match(r"^[0-9]{15}$", str(val)):
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "valid_emirate_code" and not is_empty:
                    # AZ (Abu Dhabi), AJ (Ajman), SH (Sharjah), DU (Dubai), RK (Ras Al Khaimah), FU (Fujairah), UQ (Umm Al Quwain)
                    if str(val).upper() not in ["AZ", "AJ", "SH", "DU", "RK", "FU", "UQ"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "valid_binary_flag" and not is_empty:
                    # 8-digit binary flag (e.g. 10000000)
                    if not re.match(r"^[0-1]{8}$", str(val)):
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "valid_specification_id" and not is_empty:
                    valid_urns = [
                        "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
                        "urn:peppol:pint:billing-1.0:ae:en:1.0"
                    ]
                    if not any(u == str(val) or u in str(val) for u in valid_urns):
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "must_be_0235" and not is_empty:
                    if str(val) != "0235":
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True
                
                elif rule == "email_format" and not is_empty:
                    # Basic email regex
                    is_b2b = data.get("is_b2b") is True
                    # Skip email format check for B2C if it contains junk strings (e.g. dict representations)
                    if not is_b2b and (str(val).startswith("{") or "consumer" in str(val).lower()):
                        continue

                    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
                    if not re.match(email_regex, str(val)):
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "valid_transaction_type" and not is_empty:
                    if str(val).upper() not in ["B2B", "B2C"]:
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

                elif rule == "valid_invoice_number" and not is_empty:
                    # Alphanumeric with some symbols / - and SPACE
                    if not re.match(r"^[a-zA-Z0-9\-/ ]+$", str(val)):
                        errors.append(ValidationErrorItem(field=field, error=message, severity=severity, category=category))
                        has_error_for_field = True

        return errors
