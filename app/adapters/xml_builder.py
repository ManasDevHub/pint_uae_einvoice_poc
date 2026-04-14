from app.models.invoice import InvoicePayload

def generate_ubl_xml(invoice: InvoicePayload) -> str:
    """
    Generates a UBL 2.1 XML string from an InvoicePayload for PEPPOL validation.
    Supports both 380 (Invoice) and 381 (Credit Note).
    """
    # Helper to format floats correctly
    def fv(val): return f"{val:.2f}" if val is not None else "0.00"

    is_credit_note = str(invoice.invoice_type_code) == "381"
    root_tag = "CreditNote" if is_credit_note else "Invoice"
    namespace = f"urn:oasis:names:specification:ubl:schema:xsd:{root_tag}-2"
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<{root_tag} xmlns="{namespace}"
             xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
             xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>{invoice.specification_id or "urn:peppol:pint:billing-1.0:ae:en:1.0"}</cbc:CustomizationID>
    <cbc:ProfileID>{invoice.business_process_id or "urn:peppol:bis:billing"}</cbc:ProfileID>
    <cbc:ID>{invoice.invoice_number}</cbc:ID>
    <cbc:IssueDate>{invoice.invoice_date}</cbc:IssueDate>
"""
    if invoice.payment_due_date:
        xml += f"    <cbc:DueDate>{invoice.payment_due_date}</cbc:DueDate>\n"
    
    if is_credit_note:
        xml += f"    <cbc:CreditNoteTypeCode>{invoice.invoice_type_code}</cbc:CreditNoteTypeCode>\n"
    else:
        xml += f"    <cbc:InvoiceTypeCode>{invoice.invoice_type_code}</cbc:InvoiceTypeCode>\n"

    xml += f"    <cbc:DocumentCurrencyCode>{invoice.currency_code}</cbc:DocumentCurrencyCode>\n"
    
    # Requirement R003: Buyer Reference
    xml += f"    <cbc:BuyerReference>{invoice.order_reference or invoice.buyer_reference or 'NOT_PROVIDED'}</cbc:BuyerReference>\n"

    # Seller
    seller_scheme = invoice.seller.electronic_scheme or ("EM" if "@" in (invoice.seller.electronic_address or "") else "0235")
    xml += f"""    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{seller_scheme}">{invoice.seller.electronic_address}</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>{invoice.seller.name}</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>{invoice.seller.address}</cbc:StreetName>
                <cbc:CityName>{invoice.seller.city}</cbc:CityName>
                <cbc:CountrySubentity>{invoice.seller.subdivision}</cbc:CountrySubentity>
                <cac:Country>
                    <cbc:IdentificationCode>{invoice.seller.country_code}</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{invoice.seller.trn}</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>{invoice.seller.tax_scheme_id or 'VAT'}</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{invoice.seller.name}</cbc:RegistrationName>
                <cbc:CompanyID schemeID="0235">{invoice.seller.trn}</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
"""

    # Buyer
    buyer_scheme = invoice.buyer.electronic_scheme or ("EM" if "@" in (invoice.buyer.electronic_address or "") else "0235")
    xml += f"""    <cac:AccountingCustomerParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{buyer_scheme}">{invoice.buyer.electronic_address or 'consumer@example.com'}</cbc:EndpointID>
            <cac:PartyName>
                <cbc:Name>{invoice.buyer.name}</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>{invoice.buyer.address}</cbc:StreetName>
                <cbc:CityName>{invoice.buyer.city}</cbc:CityName>
                <cbc:CountrySubentity>{invoice.buyer.subdivision}</cbc:CountrySubentity>
                <cac:Country>
                    <cbc:IdentificationCode>{invoice.buyer.country_code}</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>"""
    if invoice.buyer.trn:
        xml += f"\n                <cbc:CompanyID>{invoice.buyer.trn}</cbc:CompanyID>"
    xml += f"""
                <cac:TaxScheme>
                    <cbc:ID>{invoice.buyer.tax_scheme_id or 'VAT'}</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{invoice.buyer.name}</cbc:RegistrationName>
                <cbc:CompanyID schemeID="0235">{invoice.buyer.trn or "AE0000000000000"}</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
"""
    
    # Tax Total
    xml += f"""    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{invoice.currency_code}">{fv(abs(invoice.totals.tax_amount))}</cbc:TaxAmount>
"""
    for sub in invoice.tax_subtotals:
        xml += f"""        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="{invoice.currency_code}">{fv(abs(sub.taxable_amount))}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="{invoice.currency_code}">{fv(abs(sub.tax_amount))}</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>{sub.tax_category_code}</cbc:ID>
                <cbc:Percent>{fv(sub.tax_rate * 100)}</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
"""
    xml += "    </cac:TaxTotal>\n"

    # Monetary Total
    total_tag = "LegalMonetaryTotal"
    xml += f"""    <cac:{total_tag}>
        <cbc:LineExtensionAmount currencyID="{invoice.currency_code}">{fv(abs(invoice.totals.line_extension_amount))}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="{invoice.currency_code}">{fv(abs(invoice.totals.total_without_tax))}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="{invoice.currency_code}">{fv(abs(invoice.totals.total_with_tax))}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{invoice.currency_code}">{fv(abs(invoice.totals.amount_due))}</cbc:PayableAmount>
    </cac:{total_tag}>
"""

    # Lines
    line_tag = "CreditNoteLine" if is_credit_note else "InvoiceLine"
    for line in invoice.lines:
        xml += f"""    <cac:{line_tag}>
        <cbc:ID>{line.line_id}</cbc:ID>
        <cbc:{"CreditedQuantity" if is_credit_note else "InvoicedQuantity"} unitCode="{line.unit_of_measure}">{abs(line.quantity)}</cbc:{"CreditedQuantity" if is_credit_note else "InvoicedQuantity"}>
        <cbc:LineExtensionAmount currencyID="{invoice.currency_code}">{fv(abs(line.line_net_amount))}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>{line.item_name}</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>{line.tax_category}</cbc:ID>
                <cbc:Percent>{fv(line.tax_rate * 100)}</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="{invoice.currency_code}">{fv(abs(line.unit_price))}</cbc:PriceAmount>
        </cac:Price>
    </cac:{line_tag}>
"""
    xml += f"</{root_tag}>"
    return xml
    return xml
