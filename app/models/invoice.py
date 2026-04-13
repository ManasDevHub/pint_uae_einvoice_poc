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
    line_id: Optional[str] = None
    item_name: Optional[str] = None
    item_description: Optional[str] = None
    unit_of_measure: str = "EA"
    quantity: float = 0.0
    unit_price: float = 0.0
    gross_price: Optional[float] = None
    price_base_quantity: float = 1.0
    discount_amount: float = 0.0
    line_net_amount: float = 0.0
    tax_category: str = "S"
    tax_rate: float = 0.05
    tax_amount: float = 0.0
    aed_tax_amount: Optional[float] = None

class TaxBreakdown(BaseModel):
    tax_category_code: str = "S"
    tax_rate: float = 0.05
    taxable_amount: float = 0.0
    tax_amount: float = 0.0

class DocumentTotals(BaseModel):
    line_extension_amount: float = 0.0  # Sum of line net amounts
    total_without_tax: float = 0.0
    tax_amount: float = 0.0
    total_with_tax: float = 0.0
    amount_due: float = 0.0

class InvoicePayload(BaseModel):
    """
    Standard Base JSON payload reflecting the PINT AE Structure.
    """
    specification_id: str = "urn:peppol:pint:billing-1.0:ae:en:1.0"
    business_process_id: str = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: str = Field(...)
    payment_due_date: Optional[str] = None
    invoice_type_code: str = "380"
    payment_means_type_code: Optional[str] = "30" # Default to Credit Transfer
    transaction_type: str = "B2B"
    transaction_type_code: Optional[str] = "10000000" # UAE 8-digit binary flag
    currency_code: str = "AED"
    tax_category_code: str = "S"
    tax_point_date: Optional[str] = None
    order_reference: Optional[str] = None
    payment_terms: Optional[str] = "Standard 30 Days"
    delivery_date: Optional[str] = None
    
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
            "tax_amount": self.totals.tax_amount,
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

            # Line Level Proxy (First Line)
            "line_id": self.lines[0].line_id if self.lines else None,
            "item_name": self.lines[0].item_name if self.lines else None,
            "unit_of_measure": self.lines[0].unit_of_measure if self.lines else None,
            "quantity": self.lines[0].quantity if self.lines else None,
            "unit_price": self.lines[0].unit_price if self.lines else None,
            "line_net_amount": self.lines[0].line_net_amount if self.lines else None
        }
