import pandas as pd
import numpy as np

class TestLoader:
    # Mapping common test case field names to UBL XPaths
    FIELD_TO_XPATH = {
        'Invoice Number': '//cbc:ID',
        'Invoice Date': '//cbc:IssueDate',
        'Invoice Type Code': '//cbc:InvoiceTypeCode',
        'Currency': '//cbc:DocumentCurrencyCode',
        'Seller TRN': '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID',
        'Buyer TRN': '//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID',
        'Seller Name': '//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name',
        'Buyer Name': '//cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name',
        'Tax Amount': '//cac:TaxTotal/cbc:TaxAmount',
        'Payable Amount': '//cac:LegalMonetaryTotal/cbc:PayableAmount',
        # Add more based on the Excel's "Field / Component" column
    }

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_cases(self, limit=None):
        """
        Loads test cases from Excel, skipping headers and cleaning data.
        Returns a list of dicts.
        """
        # Read Excel skipping the first 2 rows (header is effectively on the 3rd row / index 2)
        df = pd.read_excel(self.file_path, header=2)
        
        # Rename columns for easier access
        df.columns = [
            'sl_no', 'module', 'field_component', 'test_case_id', 'test_type', 
            'description', 'test_data', 'expected_result', 'business_rule', 
            'priority', 'phase', 'status'
        ]

        # Clean up
        df = df.dropna(subset=['test_case_id'])
        if limit:
            df = df.head(limit)

        test_cases = []
        for _, row in df.iterrows():
            field_name = str(row['field_component']).strip()
            xpath = self.FIELD_TO_XPATH.get(field_name)
            
            # If no direct mapping, try a fuzzy match or default to a header field for demo
            if not xpath:
                xpath = '//cbc:Note' # fallback

            test_cases.append({
                'id': str(row['test_case_id']),
                'group': str(row['test_type']),
                'field': field_name,
                'xpath': xpath,
                'input': str(row['test_data']),
                'expected': str(row['expected_result']).upper(),
                'rule': str(row['business_rule'])
            })
            
        return test_cases
