from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class SellerDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = Field(None, alias="seller_name")
    trn: Optional[str] = Field(None, alias="seller_trn")
    address: Optional[str] = Field(None, alias="seller_address")
    city: Optional[str] = Field(None, alias="seller_city")
    subdivision: Optional[str] = Field(None, alias="seller_subdivision")  # Emirate code
    country_code: Optional[str] = Field("AE", alias="seller_country_code")
    electronic_address: Optional[str] = Field(None, alias="seller_electronic_address")
    electronic_scheme: Optional[str] = Field("0235", alias="seller_electronic_scheme")
    legal_registration: Optional[str] = Field(None, alias="seller_legal_registration")
    registration_identifier_type: Optional[str] = Field(None, alias="seller_registration_identifier_type")
    tax_scheme_id: Optional[str] = Field("VAT", alias="seller_tax_scheme_id")
    postal_code: Optional[str] = Field(None, alias="seller_postal_code")

class BuyerDetails(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: Optional[str] = Field(None, alias="buyer_name")
    trn: Optional[str] = Field(None, alias="buyer_trn")
    address: Optional[str] = Field(None, alias="buyer_address")
    city: Optional[str] = Field(None, alias="buyer_city")
    subdivision: Optional[str] = Field(None, alias="buyer_subdivision")
    country_code: Optional[str] = Field("AE", alias="buyer_country_code")
    electronic_address: Optional[str] = Field(None, alias="buyer_electronic_address")
    electronic_scheme: Optional[str] = Field("0235", alias="buyer_electronic_scheme")
    legal_registration: Optional[str] = Field(None, alias="buyer_legal_registration")
    registration_identifier_type: Optional[str] = Field(None, alias="buyer_registration_identifier_type")
    tax_scheme_id: Optional[str] = Field("VAT", alias="buyer_tax_scheme_id")
    postal_code: Optional[str] = Field(None, alias="buyer_postal_code")


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    line_id: Optional[str] = Field(None, alias="line_id")
    item_name: Optional[str] = Field(None, alias="item_name")
    item_description: Optional[str] = Field(None, alias="item_description")
    unit_of_measure: str = Field("EA", alias="unit_of_measure")
    quantity: float = Field(0.0, alias="quantity")
    unit_price: float = Field(0.0, alias="unit_price")
    gross_price: Optional[float] = Field(None, alias="gross_price")
    price_base_quantity: float = Field(1.0, alias="price_base_quantity")
    discount_amount: float = Field(0.0, alias="discount_amount")
    line_net_amount: float = Field(0.0, alias="line_net_amount")
    tax_category: str = Field("S", alias="tax_category")
    tax_rate: float = Field(0.05, alias="tax_rate")
    tax_amount: float = Field(0.0, alias="tax_amount")
    aed_tax_amount: Optional[float] = Field(None, alias="vat_line_amount_aed") # Internal matches alias

class TaxBreakdown(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    tax_category_code: str = Field("S", alias="tax_category_code")
    tax_rate: float = Field(0.05, alias="tax_rate")
    taxable_amount: float = Field(0.0, alias="taxable_amount")
    tax_amount: float = Field(0.0, alias="tax_amount")

class DocumentTotals(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    line_extension_amount: float = Field(0.0, alias="line_extension_amount")
    total_without_tax: float = Field(0.0, alias="total_without_tax")
    tax_amount: float = Field(0.0, alias="tax_amount")
    total_with_tax: float = Field(0.0, alias="total_with_tax")
    amount_due: float = Field(0.0, alias="amount_due")

class InvoicePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    """
    Standard Base JSON payload reflecting the PINT AE Structure.
    """
    specification_id: str = Field("urn:peppol:pint:billing-1.0:ae:en:1.0", alias="specification_id")
    business_process_id: str = Field("urn:fdc:peppol.eu:2017:poacc:billing:01:1.0", alias="business_process_id")
    invoice_number: str = Field(..., min_length=1, max_length=100, alias="invoice_number")
    invoice_date: str = Field(..., alias="invoice_date")
    payment_due_date: Optional[str] = Field(None, alias="payment_due_date")
    invoice_type_code: str = Field("380", alias="invoice_type_code")
    payment_means_type_code: Optional[str] = Field("30", alias="payment_means_type_code")
    transaction_type: str = Field("B2B", alias="transaction_type")
    transaction_type_code: Optional[str] = Field("10000000", alias="transaction_type_code")
    currency_code: str = Field("AED", alias="currency_code")
    tax_category_code: str = Field("S", alias="tax_category_code")
    tax_point_date: Optional[str] = Field(None, alias="tax_point_date")
    order_reference: Optional[str] = Field(None, alias="order_reference")
    payment_terms: Optional[str] = Field("Standard 30 Days", alias="payment_terms")
    delivery_date: Optional[str] = Field(None, alias="delivery_date")
    
    seller: SellerDetails = Field(default_factory=SellerDetails)
    buyer: BuyerDetails = Field(default_factory=BuyerDetails)
    lines: List[InvoiceLineItem] = Field(..., min_length=1, max_length=1000)
    tax_subtotals: List[TaxBreakdown] = Field(default_factory=list)
    totals: DocumentTotals = Field(default_factory=DocumentTotals)

    def extract_flat_data(self) -> dict:
        """
        Creates a flattened dictionary for the rule engine.
        """
        return {
            "specification_id": self.specification_id,
            "business_process_id": self.business_process_id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "payment_due_date": self.payment_due_date,
            "invoice_type_code": self.invoice_type_code,
            "transaction_type": self.transaction_type,
            "transaction_type_code": self.transaction_type_code,
            "is_b2b": self.transaction_type.upper() == "B2B",
            "is_b2c": self.transaction_type.upper() == "B2C",
            "currency_code": self.currency_code,
            "payment_means_type_code": self.payment_means_type_code,
            "tax_category_code": self.tax_category_code,
            
            # Seller Fields (A2)
            "seller_name": self.seller.name,
            "seller_trn": self.seller.trn,
            "seller_address": self.seller.address,
            "seller_city": self.seller.city,
            "seller_subdivision": self.seller.subdivision,
            "seller_country_code": self.seller.country_code,
            "seller_electronic_address": self.seller.electronic_address,
            "seller_electronic_scheme": self.seller.electronic_scheme,
            "seller_legal_registration": self.seller.legal_registration,
            "seller_registration_identifier_type": self.seller.registration_identifier_type,
            "seller_tax_scheme_id": self.seller.tax_scheme_id,

            # Buyer Fields (A3)
            "buyer_name": self.buyer.name,
            "buyer_trn": self.buyer.trn,
            "buyer_address": self.buyer.address,
            "buyer_city": self.buyer.city,
            "buyer_subdivision": self.buyer.subdivision,
            "buyer_country_code": self.buyer.country_code,
            "buyer_electronic_address": self.buyer.electronic_address,
            "buyer_electronic_scheme": self.buyer.electronic_scheme,
            "buyer_legal_registration": self.buyer.legal_registration,
            "buyer_registration_identifier_type": self.buyer.registration_identifier_type,
            "buyer_tax_scheme_id": self.buyer.tax_scheme_id,

            # Totals (A4)
            "line_extension_amount": self.totals.line_extension_amount,
            "total_without_tax": self.totals.total_without_tax,
            "tax_amount": self.totals.tax_amount, # A4.3
            "total_with_tax": self.totals.total_with_tax,
            "amount_due": self.totals.amount_due,
            
            "line_count": len(self.lines),
            "tax_subtotals_count": len(self.tax_subtotals),

            # Header Expansion
            "tax_point_date": self.tax_point_date,
            "order_reference": self.order_reference,
            "payment_terms": self.payment_terms,
            "delivery_date": self.delivery_date,
            "seller_postal_code": self.seller.postal_code,
            "buyer_postal_code": self.buyer.postal_code,

            # Tax Breakdown Expansion (A5) - First entry proxy for presence/format rules
            "tax_subtotal_taxable_amount": self.tax_subtotals[0].taxable_amount if self.tax_subtotals else None,
            "tax_subtotal_tax_amount": self.tax_subtotals[0].tax_amount if self.tax_subtotals else None, # A5.2
            "tax_category_rate": self.tax_subtotals[0].tax_rate if self.tax_subtotals else None,

            # Line Level Proxy (First Line) - A6
            "line_id": self.lines[0].line_id if self.lines else None,
            "item_name": self.lines[0].item_name if self.lines else None,
            "item_description": self.lines[0].item_description if self.lines else None, # A6.13
            "unit_of_measure": self.lines[0].unit_of_measure if self.lines else None,
            "quantity": self.lines[0].quantity if self.lines else None,
            "unit_price": self.lines[0].unit_price if self.lines else None,
            "gross_price": self.lines[0].gross_price if self.lines else None, # A6.6
            "price_base_quantity": self.lines[0].price_base_quantity if self.lines else None,
            "line_net_amount": self.lines[0].line_net_amount if self.lines else None,
            "line_tax_category": self.lines[0].tax_category if self.lines else None,
            "line_tax_rate": self.lines[0].tax_rate if self.lines else None,
            "vat_line_amount_aed": self.lines[0].aed_tax_amount if self.lines else None, # A6.10
            "line_amount_aed": self.lines[0].line_net_amount if self.lines else None, # A6.11 (net is used as base)
        }
        }
