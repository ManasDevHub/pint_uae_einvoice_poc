from lxml import etree
from typing import Dict, Any
from app.models.invoice import InvoicePayload, SellerDetails, BuyerDetails, InvoiceLineItem, DocumentTotals, TaxBreakdown

class UBLXMLAdapter:
    """
    Adapter to transform UBL 2.1 XML (UAE PINT AE standard) into Internal InvoicePayload.
    """
    NS = {
        'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    }

    def transform(self, xml_content: bytes) -> InvoicePayload:
        try:
            tree = etree.fromstring(xml_content)
        except Exception as e:
            raise ValueError(f"Invalid XML format: {str(e)}")

        def get_val(path, root=tree):
            res = root.xpath(path, namespaces=self.NS)
            return res[0].text if res else None

        # Root fields
        invoice_number = get_val('cbc:ID')
        invoice_date = get_val('cbc:IssueDate')
        invoice_type_code = get_val('cbc:InvoiceTypeCode') or "380"
        currency_code = get_val('cbc:DocumentCurrencyCode') or "AED"
        spec_id = get_val('cbc:CustomizationID') or "urn:peppol:pint:billing-1.0:ae:en:1.0"

        # Seller
        seller_node = tree.xpath('cac:AccountingSupplierParty/cac:Party', namespaces=self.NS)
        seller = SellerDetails()
        if seller_node:
            s_node = seller_node[0]
            seller.name = get_val('cac:PartyName/cbc:Name', s_node)
            seller.trn = get_val('cac:PartyTaxScheme/cbc:CompanyID', s_node)
            seller.address = get_val('cac:PostalAddress/cac:Country/cbc:IdentificationCode', s_node) # Simplification
            seller.country_code = get_val('cac:PostalAddress/cac:Country/cbc:IdentificationCode', s_node) or "AE"

        # Buyer
        buyer_node = tree.xpath('cac:AccountingCustomerParty/cac:Party', namespaces=self.NS)
        buyer = BuyerDetails()
        if buyer_node:
            b_node = buyer_node[0]
            buyer.name = get_val('cac:PartyName/cbc:Name', b_node)
            buyer.trn = get_val('cac:PartyTaxScheme/cbc:CompanyID', b_node) # If any
            buyer.country_code = get_val('cac:PostalAddress/cac:Country/cbc:IdentificationCode', b_node) or "AE"

        # Lines
        lines = []
        line_nodes = tree.xpath('cac:InvoiceLine', namespaces=self.NS)
        for node in line_nodes:
            line = InvoiceLineItem(
                line_id=get_val('cbc:ID', node),
                item_name=get_val('cac:Item/cbc:Name', node),
                quantity=float(get_val('cbc:InvoicedQuantity', node) or 0),
                unit_price=float(get_val('cac:Price/cbc:PriceAmount', node) or 0),
                line_net_amount=float(get_val('cbc:LineExtensionAmount', node) or 0),
                tax_category=get_val('cac:Item/cac:ClassifiedTaxCategory/cbc:ID', node) or "S",
                tax_rate=float(get_val('cac:Item/cac:ClassifiedTaxCategory/cbc:Percent', node) or 5) / 100,
            )
            # Rough tax amount calculation if missing in XML
            line.tax_amount = round(line.line_net_amount * line.tax_rate, 2)
            lines.append(line)

        # Totals
        totals_node = tree.xpath('cac:LegalMonetaryTotal', namespaces=self.NS)
        totals = DocumentTotals()
        if totals_node:
            t_node = totals_node[0]
            totals.line_extension_amount = float(get_val('cbc:LineExtensionAmount', t_node) or 0)
            totals.total_without_tax = float(get_val('cbc:TaxExclusiveAmount', t_node) or 0)
            totals.total_with_tax = float(get_val('cbc:TaxInclusiveAmount', t_node) or 0)
            totals.amount_due = float(get_val('cbc:PayableAmount', t_node) or 0)
            
            # Tax amount from separate Tag
            tax_amount = get_val('cac:TaxTotal/cbc:TaxAmount', tree)
            totals.tax_amount = float(tax_amount or (totals.total_with_tax - totals.total_without_tax))

        return InvoicePayload(
            specification_id=spec_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            invoice_type_code=invoice_type_code,
            currency_code=currency_code,
            seller=seller,
            buyer=buyer,
            lines=lines,
            totals=totals
        )
