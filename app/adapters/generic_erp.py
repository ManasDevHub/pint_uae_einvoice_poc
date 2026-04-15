from typing import Dict, Any, List
from app.adapters.base import BaseERPAdapter
from app.models.invoice import InvoicePayload
import re

class GenericJSONAdapter(BaseERPAdapter):
    """
    Adapter that handles the Generic JSON structure for the POC.
    Extremely robust key mapping for Excel/CSV ingest.
    """
    def _normalize_key(self, key: str) -> str:
        """Strip all non-alphanumeric and lowercase."""
        return re.sub(r'[^a-zA-Z0-9]', '', str(key)).lower()

    def transform(self, raw_data: Dict[str, Any]) -> InvoicePayload:
        """
        Robust transformation logic that prioritizes nested structures (JSON)
        while maintaining flat-key fallbacks (Excel/CSV).
        """
        data_copy = raw_data.copy()
        
        # 1. Create a lookup map of normalized keys to raw values
        lookup = {self._normalize_key(k): v for k, v in data_copy.items()}
        
        # Helper to get value using fuzzy key
        def get_val(fuzzy_key: str, default: Any = None, src: dict = None) -> Any:
            target = self._normalize_key(fuzzy_key)
            base = {self._normalize_key(k): v for k, v in src.items()} if src else lookup
            if target in base: return base[target]
            
            # Fuzzy match safety: 
            # 1. Prefer keys that contain the target (e.g. 'invoice_no' contains 'invoice')
            # 2. Avoid keys that ARE substrings of target (e.g. 'type' should not match 'transaction_type_code')
            for k, v in base.items():
                if target in k and not isinstance(v, dict): 
                    return v
            return default

        # Numeric cleanup helpers
        def safe_float(val: Any, default: float = 0.0) -> float:
            if val is None or val == "" or str(val).lower() == "nan": return default
            try:
                if isinstance(val, str): val = val.replace(',', '').strip()
                return float(val)
            except (ValueError, TypeError): return default

        def cleanup_excel_number(val: Any) -> Any:
            if val is None or str(val).lower() == "nan": return ""
            s_val = str(val).strip()
            if s_val.endswith(".0"): s_val = s_val[:-2]
            return s_val

        # 2. Extract Basic Header Info
        norm_data = {
            "specification_id": str(get_val("specification_id", "urn:peppol:pint:billing-1.0:ae:en:1.0")),
            "business_process_id": str(get_val("business_process_id", "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")),
            "invoice_number": cleanup_excel_number(get_val("invoice_number", get_val("invoiceno", get_val("bill_no", "INV-TEMP")))),
            "invoice_date": str(get_val("invoice_date", get_val("date", "2026-04-01"))),
            "payment_due_date": str(get_val("payment_due_date", get_val("due_date", ""))),
            "invoice_type_code": str(cleanup_excel_number(get_val("invoice_type_code", "380"))),
            "payment_means_type_code": str(cleanup_excel_number(get_val("payment_means_type_code", "30"))),
            "transaction_type": str(get_val("transaction_type", "B2B")),
            "transaction_type_code": str(cleanup_excel_number(get_val("transaction_type_code", "10000000"))),
            "currency_code": str(get_val("currency_code", get_val("currency", "AED"))),
            "tax_category_code": str(get_val("tax_category_code", get_val("tax_category", "S"))),
            "tax_point_date": get_val("tax_point_date", None),
            "order_reference": get_val("order_reference", None),
            "payment_terms": str(get_val("payment_terms", "Standard 30 Days")),
            "delivery_date": get_val("delivery_date", None),
            "buyer_reference": get_val("buyer_reference", get_val("reference", "REF-001"))
        }
        
        if not norm_data["payment_due_date"]:
            norm_data["payment_due_date"] = norm_data["invoice_date"]

        # 3. Handle Seller (Nested vs Flat)
        raw_seller = get_val("seller")
        if isinstance(raw_seller, dict):
            seller_trn = cleanup_excel_number(get_val("trn", get_val("seller_trn", ""), src=raw_seller))
            # PINT AE Requirement: TRNs must have a country prefix (e.g. AE)
            if seller_trn and len(seller_trn) == 15 and not seller_trn.startswith("AE"):
                seller_trn = f"AE{seller_trn}"
            
            norm_data["seller"] = {
                "name": str(get_val("name", get_val("seller_name", "Adamas Tech Consulting"), src=raw_seller)),
                "trn": seller_trn if seller_trn else None,
                "address": str(get_val("address", get_val("seller_address", "Business Bay"), src=raw_seller)),
                "city": str(get_val("city", get_val("seller_city", "Dubai"), src=raw_seller)),
                "subdivision": str(get_val("subdivision", "DU", src=raw_seller)).upper(),
                "country_code": str(get_val("country_code", "AE", src=raw_seller)),
                "electronic_address": str(get_val("electronic_address", get_val("seller_electronic_address", ""), src=raw_seller)),
                "electronic_scheme": str(get_val("electronic_scheme", get_val("seller_electronic_scheme", "0235"), src=raw_seller)),
                "legal_registration": str(get_val("legal_registration", "DED-998877", src=raw_seller)),
                "registration_identifier_type": str(get_val("registration_identifier_type", "DED", src=raw_seller)),
                "bank_iban": str(get_val("bank_iban", get_val("seller_bank_iban", "AE000000000000000000000"), src=raw_seller)),
            }
        else:
            seller_trn = cleanup_excel_number(get_val("seller_trn", get_val("trn", "")))
            if seller_trn and len(seller_trn) == 15 and not seller_trn.startswith("AE"):
                seller_trn = f"AE{seller_trn}"

            norm_data["seller"] = {
                "name": str(get_val("seller_name", get_val("seller", "Adamas Tech Consulting"))),
                "trn": seller_trn if seller_trn else None,
                "address": str(get_val("seller_address", "Business Bay")),
                "city": str(get_val("seller_city", "Dubai")),
                "subdivision": str(get_val("seller_subdivision", get_val("seller_emirate", "DU"))).upper(),
                "country_code": str(get_val("seller_country_code", "AE")),
                "electronic_address": str(get_val("seller_electronic_address", "")),
                "electronic_scheme": str(get_val("seller_electronic_scheme", "0235")),
                "legal_registration": str(get_val("seller_legal_registration", "DED-998877")),
                "registration_identifier_type": str(get_val("seller_registration_identifier_type", "DED")),
                "bank_iban": str(get_val("seller_bank_iban", "AE000000000000000000000")),
            }
        
        # Default seller electronic address to TRN if empty
        if not norm_data["seller"]["electronic_address"]:
            norm_data["seller"]["electronic_address"] = norm_data["seller"]["trn"] or "accounts@adamas-tech.ae"

        # 4. Handle Buyer (Nested vs Flat)
        raw_buyer = get_val("buyer")
        if isinstance(raw_buyer, dict):
            buyer_trn = cleanup_excel_number(get_val("trn", get_val("buyer_trn", ""), src=raw_buyer))
            if buyer_trn and len(buyer_trn) == 15 and not buyer_trn.startswith("AE"):
                buyer_trn = f"AE{buyer_trn}"

            norm_data["buyer"] = {
                "name": str(get_val("name", get_val("buyer_name", "Walk-in Customer"), src=raw_buyer)),
                "trn": buyer_trn if buyer_trn else None,
                "address": str(get_val("address", get_val("buyer_address", "UAE"), src=raw_buyer)),
                "city": str(get_val("city", get_val("buyer_city", "Dubai"), src=raw_buyer)),
                "subdivision": str(get_val("subdivision", "DU", src=raw_buyer)).upper(),
                "country_code": str(get_val("country_code", "AE", src=raw_buyer)),
                "electronic_address": str(get_val("electronic_address", get_val("buyer_electronic_address", ""), src=raw_buyer)),
                "electronic_scheme": str(get_val("electronic_scheme", get_val("buyer_electronic_scheme", "0235"), src=raw_buyer)),
                "legal_registration": str(get_val("legal_registration", buyer_trn if buyer_trn else "L-123456", src=raw_buyer)),
                "registration_identifier_type": str(get_val("registration_identifier_type", "DED", src=raw_buyer)),
            }
        else:
            buyer_trn = cleanup_excel_number(get_val("buyer_trn", ""))
            if buyer_trn and len(buyer_trn) == 15 and not buyer_trn.startswith("AE"):
                buyer_trn = f"AE{buyer_trn}"

            norm_data["buyer"] = {
                "name": str(get_val("buyer_name", get_val("buyer", "Walk-in Customer"))),
                "trn": buyer_trn if buyer_trn else None,
                "address": str(get_val("buyer_address", "UAE")),
                "city": str(get_val("buyer_city", "Dubai")),
                "subdivision": str(get_val("buyer_subdivision", get_val("buyer_emirate", "DU"))).upper(),
                "country_code": str(get_val("buyer_country_code", "AE")),
                "electronic_address": str(get_val("buyer_electronic_address", "")),
                "electronic_scheme": str(get_val("buyer_electronic_scheme", "0235")),
                "legal_registration": str(get_val("buyer_legal_registration", buyer_trn if buyer_trn else "L-123456")),
                "registration_identifier_type": str(get_val("buyer_registration_identifier_type", "DED" if not buyer_trn else "TRN")),
            }
        
        # Default buyer electronic address if empty
        if not norm_data["buyer"]["electronic_address"]:
            if norm_data["transaction_type"].upper() == "B2B":
                norm_data["buyer"]["electronic_address"] = norm_data["buyer"]["trn"] or "finance@client-group.ae"
            else:
                norm_data["buyer"]["electronic_address"] = "consumer@example.com"

        # Explicitly align transaction_type_code if not provided
        provided_code = str(cleanup_excel_number(get_val("transaction_type_code", "")))
        if not provided_code or provided_code == "":
            norm_data["transaction_type_code"] = "10000000" if norm_data["transaction_type"] == "B2B" else "01000000"
        else:
            norm_data["transaction_type_code"] = provided_code

        # 5. Handle Lines (Extreme robustness)
        lines = []
        raw_lines = data_copy.get("lines")

        # Define internal normalization for lines
        def normalize_line(l_row: dict, idx: int = 1) -> dict:
            l_lookup = {self._normalize_key(k): v for k, v in l_row.items()}
            def get_lk(fuzzy: str, default: Any = None) -> Any:
                target = self._normalize_key(fuzzy)
                if target in l_lookup: return l_lookup[target]
                for k, v in l_lookup.items():
                    if target in k and not isinstance(v, dict): return v
                return default

            item = get_lk("item_name", get_lk("description", get_lk("item", "")))
            qty = safe_float(get_lk("quantity", get_lk("qty", 0)))
            price = safe_float(get_lk("unit_price", get_lk("price", 0)))
            rate = safe_float(get_lk("tax_rate", get_lk("line_tax_rate", 0.05)))
            if rate > 1: rate = rate / 100 
            
            net_amount = safe_float(get_lk("line_net_amount", get_lk("net_amount", qty * price)))
            tax_amount = safe_float(get_lk("tax_amount", get_lk("line_tax_amount", net_amount * rate)))

            return {
                "line_id": str(get_lk("line_id", str(idx))),
                "item_name": str(item) if item else "Consulting Services",
                "item_description": str(get_lk("item_description", get_lk("description", item))),
                "unit_of_measure": str(get_lk("unit_of_measure", get_lk("uom", "EA"))),
                "quantity": qty if qty > 0 else 1.0,
                "unit_price": price,
                "gross_price": safe_float(get_lk("gross_price", get_lk("item_gross_price", price))),
                "price_base_quantity": safe_float(get_lk("price_base_quantity", 1.0)),
                "discount_amount": safe_float(get_lk("discount_amount", 0.0)),
                "line_net_amount": net_amount,
                "tax_category": str(get_lk("tax_category", get_lk("line_tax_category", "S"))),
                "tax_rate": rate,
                "tax_amount": tax_amount,
                "vat_line_amount_aed": safe_float(get_lk("vat_line_amount_aed", tax_amount)),
                "line_amount_aed": safe_float(get_lk("line_amount_aed", net_amount))
            }

        if isinstance(raw_lines, list):
            for i, l in enumerate(raw_lines):
                if isinstance(l, dict):
                    lines.append(normalize_line(l, i+1))
        else:
            # Fallback for flat row
            line = normalize_line(data_copy, 1)
            if line["item_name"] or line["quantity"] > 0:
                lines.append(line)
        
        norm_data["lines"] = lines

        # 6. Totals
        raw_totals = get_val("totals")
        if isinstance(raw_totals, dict):
            total_without_tax = safe_float(get_val("total_without_tax", get_val("line_extension_amount", 0.0), src=raw_totals))
            tax_amount = safe_float(get_val("tax_amount", 0.0, src=raw_totals))
            line_ext = safe_float(get_val("line_extension_amount", total_without_tax, src=raw_totals))
            
            norm_data["totals"] = {
                "line_extension_amount": line_ext,
                "total_without_tax": total_without_tax,
                "tax_amount": tax_amount,
                "total_with_tax": safe_float(get_val("total_with_tax", get_val("total", total_without_tax + tax_amount), src=raw_totals)),
                "amount_due": safe_float(get_val("amount_due", get_val("balance", total_without_tax + tax_amount), src=raw_totals))
            }
        else:
            total_without_tax = safe_float(get_val("total_without_tax", get_val("subtotal", 0)))
            tax_amount = safe_float(get_val("tax_amount", 0))
            
            if total_without_tax == 0 and lines:
                total_without_tax = sum(line.get("line_net_amount", 0) for line in lines)
            if tax_amount == 0 and lines:
                tax_amount = sum(line.get("tax_amount", 0) for line in lines)
                
            norm_data["totals"] = {
                "line_extension_amount": total_without_tax,
                "total_without_tax": total_without_tax,
                "tax_amount": tax_amount,
                "total_with_tax": safe_float(get_val("total_with_tax", get_val("total", total_without_tax + tax_amount))),
                "amount_due": safe_float(get_val("amount_due", get_val("balance", total_without_tax + tax_amount)))
            }

        # 7. Generate Tax Subtotals
        tax_map = {}
        for line in lines:
            if not isinstance(line, dict): continue
            cat = line.get("tax_category", "S")
            rate = line.get("tax_rate", 0.05)
            key = f"{cat}_{rate}"
            if key not in tax_map:
                tax_map[key] = {"tax_category_code": cat, "tax_rate": rate, "taxable_amount": 0.0, "tax_amount": 0.0}
            tax_map[key]["taxable_amount"] += float(line.get("line_net_amount", 0.0))
            tax_map[key]["tax_amount"] += float(line.get("tax_amount", 0.0))
        norm_data["tax_subtotals"] = list(tax_map.values())

        return InvoicePayload(**norm_data)
