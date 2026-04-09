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
            for k, v in base.items():
                if target in k or k in target: return v
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
            "invoice_number": cleanup_excel_number(get_val("invoice_number", get_val("invoiceno", get_val("bill_no", "INV-TEMP")))),
            "invoice_date": str(get_val("invoice_date", get_val("date", "2026-04-01"))),
            "payment_due_date": str(get_val("payment_due_date", get_val("due_date", ""))),
            "invoice_type_code": str(cleanup_excel_number(get_val("invoice_type_code", "380"))),
            "currency_code": str(get_val("currency_code", get_val("currency", "AED"))),
            "tax_category_code": str(get_val("tax_category_code", get_val("tax_category", "S"))),
            "transaction_type": str(get_val("transaction_type", "B2B")),
        }
        
        if not norm_data["payment_due_date"]:
            norm_data["payment_due_date"] = norm_data["invoice_date"]

        # 3. Handle Seller (Nested vs Flat)
        raw_seller = get_val("seller")
        if isinstance(raw_seller, dict):
            seller_trn = cleanup_excel_number(get_val("trn", get_val("seller_trn", ""), src=raw_seller))
            norm_data["seller"] = {
                "name": str(get_val("name", get_val("seller_name", "Adamas Tech Consulting"), src=raw_seller)),
                "trn": seller_trn if seller_trn else None,
                "address": str(get_val("address", get_val("seller_address", "Business Bay"), src=raw_seller)),
                "city": str(get_val("city", get_val("seller_city", "Dubai"), src=raw_seller)),
                "subdivision": str(get_val("subdivision", "DU", src=raw_seller)).upper(),
                "country_code": str(get_val("country_code", "AE", src=raw_seller)),
                "electronic_address": str(get_val("electronic_address", seller_trn, src=raw_seller)),
                "legal_registration": str(get_val("legal_registration", "DED-998877", src=raw_seller)),
                "registration_identifier_type": str(get_val("registration_identifier_type", "DED", src=raw_seller)),
            }
        else:
            seller_trn = cleanup_excel_number(get_val("seller_trn", get_val("trn", "")))
            norm_data["seller"] = {
                "name": str(get_val("seller_name", get_val("seller", "Adamas Tech Consulting"))),
                "trn": seller_trn if seller_trn else None,
                "address": str(get_val("seller_address", "Business Bay")),
                "city": str(get_val("seller_city", "Dubai")),
                "subdivision": str(get_val("seller_subdivision", get_val("seller_emirate", "DU"))).upper(),
                "country_code": str(get_val("seller_country_code", "AE")),
                "electronic_address": str(get_val("seller_electronic_address", seller_trn)),
                "legal_registration": str(get_val("seller_legal_registration", "DED-998877")),
                "registration_identifier_type": str(get_val("seller_registration_identifier_type", "DED")),
            }

        # 4. Handle Buyer (Nested vs Flat)
        raw_buyer = get_val("buyer")
        if isinstance(raw_buyer, dict):
            buyer_trn = cleanup_excel_number(get_val("trn", get_val("buyer_trn", ""), src=raw_buyer))
            norm_data["buyer"] = {
                "name": str(get_val("name", get_val("buyer_name", "Walk-in Customer"), src=raw_buyer)),
                "trn": buyer_trn if buyer_trn else None,
                "address": str(get_val("address", get_val("buyer_address", "UAE"), src=raw_buyer)),
                "city": str(get_val("city", get_val("buyer_city", "Dubai"), src=raw_buyer)),
                "subdivision": str(get_val("subdivision", "DU", src=raw_buyer)).upper(),
                "country_code": str(get_val("country_code", "AE", src=raw_buyer)),
                "electronic_address": str(get_val("electronic_address", buyer_trn if buyer_trn else "CONSUMER", src=raw_buyer)),
                "legal_registration": str(get_val("legal_registration", buyer_trn if buyer_trn else "L-123456", src=raw_buyer)),
                "registration_identifier_type": str(get_val("registration_identifier_type", "DED", src=raw_buyer)),
            }
        else:
            buyer_trn = cleanup_excel_number(get_val("buyer_trn", ""))
            norm_data["buyer"] = {
                "name": str(get_val("buyer_name", get_val("buyer", "Walk-in Customer"))),
                "trn": buyer_trn if len(buyer_trn) >= 15 else None,
                "address": str(get_val("buyer_address", "UAE")),
                "city": str(get_val("buyer_city", "Dubai")),
                "subdivision": str(get_val("buyer_subdivision", get_val("buyer_emirate", "DU"))).upper(),
                "country_code": str(get_val("buyer_country_code", "AE")),
                "electronic_address": str(get_val("buyer_electronic_address", buyer_trn if buyer_trn else "CONSUMER")),
                "legal_registration": str(get_val("buyer_legal_registration", buyer_trn if buyer_trn else "L-123456")),
                "registration_identifier_type": str(get_val("buyer_registration_identifier_type", "DED" if not buyer_trn else "TRN")),
            }

        # 5. Handle Lines (Extreme robustness)
        lines = []
        if isinstance(data_copy.get("lines"), list):
            # If line is already a dict, keep it as is (Pydantic will validate)
            lines = data_copy["lines"]
        else:
            # Try to build at least one line from flat keys
            item = get_val("item_name", get_val("description", get_val("item", "")))
            qty = safe_float(get_val("quantity", get_val("qty", 0)))
            price = safe_float(get_val("unit_price", get_val("price", 0)))
            
            if item or qty > 0 or price > 0:
                rate = safe_float(get_val("tax_rate", 0.05))
                if rate > 1: rate = rate / 100 
                net_amount = safe_float(get_val("line_net_amount", get_val("net_amount", qty * price)))
                tax_amount = safe_float(get_val("tax_amount", net_amount * rate))
                lines.append({
                    "line_id": str(get_val("line_id", "1")),
                    "item_name": item if item else "Consulting Services",
                    "quantity": qty if qty > 0 else 1.0,
                    "unit_price": price,
                    "line_net_amount": net_amount,
                    "tax_category": str(get_val("tax_category", "S")),
                    "tax_rate": rate,
                    "tax_amount": tax_amount
                })
        
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
                total_without_tax = sum(line.get("line_net_amount", 0) for line in lines) if isinstance(lines[0], dict) else 0
            if tax_amount == 0 and lines:
                tax_amount = sum(line.get("tax_amount", 0) for line in lines) if isinstance(lines[0], dict) else 0
                
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
