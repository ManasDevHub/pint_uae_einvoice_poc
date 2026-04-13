from app.models.invoice import InvoicePayload

def generate_ubl_xml(invoice: InvoicePayload) -> str:
    """
    Generates a UBL 2.1 XML string from an InvoicePayload for PEPPOL validation.
    """
    # Helper to format floats correctly
    def fv(val): return f"{val:.2f}" if val is not None else "0.00"

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>{invoice.specification_id}</cbc:CustomizationID>
    <cbc:ProfileID>{invoice.business_process_id}</cbc:ProfileID>
    <cbc:ID>{invoice.invoice_number}</cbc:ID>
    <cbc:IssueDate>{invoice.invoice_date}</cbc:IssueDate>
"""
    if invoice.payment_due_date:
        xml += f"    <cbc:DueDate>{invoice.payment_due_date}</cbc:DueDate>\n"

    xml += f"""    <cbc:InvoiceTypeCode>{invoice.invoice_type_code}</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>{invoice.currency_code}</cbc:DocumentCurrencyCode>
"""
    
    # Seller
    xml += f"""    <cac:AccountingSupplierParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{invoice.seller.electronic_scheme}">{invoice.seller.electronic_address}</cbc:EndpointID>
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
                    <cbc:ID>{invoice.seller.tax_scheme_id}</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{invoice.seller.name}</cbc:RegistrationName>
                <cbc:CompanyID schemeID="{invoice.seller.registration_identifier_type}">{invoice.seller.legal_registration}</cbc:CompanyID>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>
"""

    # Buyer
    xml += f"""    <cac:AccountingCustomerParty>
        <cac:Party>
            <cbc:EndpointID schemeID="{invoice.buyer.electronic_scheme}">{invoice.buyer.electronic_address}</cbc:EndpointID>
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
                    <cbc:ID>{invoice.buyer.tax_scheme_id}</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{invoice.buyer.name}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
"""
    
    # Delivery
    if invoice.delivery_date:
        xml += f"""    <cac:Delivery>
        <cbc:ActualDeliveryDate>{invoice.delivery_date}</cbc:ActualDeliveryDate>
    </cac:Delivery>
"""

    # Payment Means
    if invoice.payment_means_type_code:
        xml += f"""    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>{invoice.payment_means_type_code}</cbc:PaymentMeansCode>
    </cac:PaymentMeans>
"""

    # Tax Total
    xml += f"""    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="{invoice.currency_code}">{fv(invoice.totals.tax_amount)}</cbc:TaxAmount>
"""
    for sub in invoice.tax_subtotals:
        xml += f"""        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="{invoice.currency_code}">{fv(sub.taxable_amount)}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="{invoice.currency_code}">{fv(sub.tax_amount)}</cbc:TaxAmount>
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
    xml += f"""    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="{invoice.currency_code}">{fv(invoice.totals.line_extension_amount)}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="{invoice.currency_code}">{fv(invoice.totals.total_without_tax)}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="{invoice.currency_code}">{fv(invoice.totals.total_with_tax)}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="{invoice.currency_code}">{fv(invoice.totals.amount_due)}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>
"""

    # Lines
    for line in invoice.lines:
        xml += f"""    <cac:InvoiceLine>
        <cbc:ID>{line.line_id}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="{line.unit_of_measure}">{line.quantity}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="{invoice.currency_code}">{fv(line.line_net_amount)}</cbc:LineExtensionAmount>
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
            <cbc:PriceAmount currencyID="{invoice.currency_code}">{fv(line.unit_price)}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>
"""
    xml += "</Invoice>"
    return xml
