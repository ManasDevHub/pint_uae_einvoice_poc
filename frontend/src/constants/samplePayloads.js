export const SAMPLES = {
  b2b: {
    label: 'B1: B2B Standard',
    color: 'text-emerald-400',
    payload: {
      specification_id: "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
      business_process_id: "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
      invoice_number: "INV-2026-AE-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-30",
      invoice_type_code: "380",
      payment_means_type_code: "30",
      payment_terms: "Standard 30 Days",
      transaction_type: "B2B",
      transaction_type_code: "10000000",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "accounts@adamas-tech.ae",
        seller_electronic_scheme: "0235",
        seller_legal_registration: "DED-2024-12345",
        seller_registration_identifier_type: "DED",
        seller_tax_scheme_id: "VAT",
        seller_address: "Dubai Internet City",
        seller_city: "Dubai",
        seller_subdivision: "DU",
        seller_country_code: "AE"
      },
      buyer: {
        buyer_name: "Gulf Trading FZE",
        buyer_trn: "100999888777666",
        buyer_electronic_address: "finance@gulftrade.ae",
        buyer_electronic_scheme: "0235",
        buyer_legal_registration: "ADGM-2023-67890",
        buyer_registration_identifier_type: "ADGM",
        buyer_tax_scheme_id: "VAT",
        buyer_address: "Abu Dhabi, UAE",
        buyer_city: "Abu Dhabi",
        buyer_subdivision: "AZ",
        buyer_country_code: "AE"
      },
      lines: [{
        line_id: "1",
        item_name: "ERP Consulting Services",
        item_description: "Cloud ERP Implementation",
        unit_of_measure: "EA",
        quantity: 10,
        unit_price: 500,
        gross_price: 500,
        price_base_quantity: 1.0,
        line_net_amount: 5000,
        tax_category: "S",
        tax_rate: 0.05,
        tax_amount: 250,
        vat_line_amount_aed: 250,
        line_amount_aed: 5000
      }],
      tax_subtotals: [{
        tax_category_code: "S",
        tax_rate: 0.05,
        taxable_amount: 5000,
        tax_amount: 250
      }],
      totals: {
        line_extension_amount: 5000,
        total_without_tax: 5000,
        tax_amount: 250,
        total_with_tax: 5250,
        amount_due: 5250
      }
    }
  },
  b2c: {
    label: 'B2: B2C Standard',
    color: 'text-sky-400',
    payload: {
      specification_id: "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0",
      business_process_id: "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
      invoice_number: "INV-POS-2026-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-15",
      invoice_type_code: "380",
      payment_means_type_code: "30",
      payment_terms: "Cash on delivery",
      transaction_type: "B2C",
      transaction_type_code: "01000000",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "pos@adamas-tech.ae",
        seller_electronic_scheme: "0235",
        seller_legal_registration: "DED-123",
        seller_registration_identifier_type: "DED",
        seller_tax_scheme_id: "VAT",
        seller_address: "Dubai Internet City",
        seller_city: "Dubai",
        seller_subdivision: "DU",
        seller_country_code: "AE"
      },
      buyer: {
        buyer_name: "Individual Customer",
        buyer_address: "Sharjah, UAE",
        buyer_city: "Sharjah",
        buyer_subdivision: "SH",
        buyer_country_code: "AE"
      },
      lines: [{
        line_id: "1",
        item_name: "Retail Product Sale",
        item_description: "POS Retail Item",
        unit_of_measure: "EA",
        quantity: 2,
        unit_price: 100,
        gross_price: 100,
        price_base_quantity: 1.0,
        line_net_amount: 200,
        tax_category: "S",
        tax_rate: 0.05,
        tax_amount: 10,
        vat_line_amount_aed: 10,
        line_amount_aed: 200
      }],
      tax_subtotals: [{
        tax_category_code: "S",
        tax_rate: 0.05,
        taxable_amount: 200,
        tax_amount: 10
      }],
      totals: {
        line_extension_amount: 200,
        total_without_tax: 200,
        tax_amount: 10,
        total_with_tax: 210,
        amount_due: 210
      }
    }
  },
  creditNote: {
    label: 'Credit Note',
    color: 'text-violet-400',
    payload: {
      specification_id: "urn:peppol:pint:billing-1.0:ae:en:1.0",
      business_process_id: "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
      invoice_number: "CN-AE-2026-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-10",
      invoice_type_code: "381",
      payment_means_type_code: "10",
      transaction_type: "B2B",
      transaction_type_code: "10000000",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "accounts@adamas-tech.ae",
        seller_electronic_scheme: "0235",
        seller_legal_registration: "DED-123",
        seller_registration_identifier_type: "DED",
        seller_tax_scheme_id: "VAT",
        seller_address: "Dubai Internet City",
        seller_city: "Dubai",
        seller_subdivision: "DU",
        seller_country_code: "AE"
      },
      buyer: {
        buyer_name: "Gulf Trading FZE",
        buyer_trn: "100999888777666",
        buyer_electronic_address: "finance@gulftrade.ae",
        buyer_electronic_scheme: "0235",
        buyer_legal_registration: "ADGM-456",
        buyer_registration_identifier_type: "ADGM",
        buyer_tax_scheme_id: "VAT",
        buyer_address: "Abu Dhabi",
        buyer_city: "Abu Dhabi",
        buyer_subdivision: "AZ",
        buyer_country_code: "AE"
      },
      lines: [{
        line_id: "1",
        item_name: "Consulting Return",
        unit_of_measure: "EA",
        quantity: -2,
        unit_price: 500,
        line_net_amount: -1000,
        tax_category: "S",
        tax_rate: 0.05,
        tax_amount: -50
      }],
      tax_subtotals: [{
        tax_category_code: "S",
        tax_rate: 0.05,
        taxable_amount: -1000,
        tax_amount: -50
      }],
      totals: {
        line_extension_amount: -1000,
        total_without_tax: -1000,
        tax_amount: -50,
        total_with_tax: -1050,
        amount_due: -1050
      }
    }
  },
  negative: {
    label: 'Fail (E4/E10/E11)',
    color: 'text-red-400',
    payload: {
      invoice_number: "INV-FAIL-001",
      invoice_date: "2026-04-01",
      payment_due_date: "",                   // Fail: Missing
      invoice_type_code: "380",
      payment_means_type_code: "999",         // Fail: Invalid format
      transaction_type: "B2B",
      currency_code: "XYZ",                   // Fail: Invalid currency
      tax_category_code: "S",
      seller: {
        seller_name: "Bad Corp",
        seller_trn: "12345",                  // Fail: Bad TRN
        seller_address: "",                    // Fail: Missing
        seller_country_code: "US"              // Fail: Not AE
      },
      buyer: {
        buyer_name: "Client",
        buyer_trn: "100999888777666",
        buyer_country_code: "AE"
      },
      lines: [{
        line_id: "1",
        item_name: "Invalid Item",
        unit_of_measure: "INVALID",           // Fail: Invalid UoM
        quantity: -5,                         // Fail: Negative for 380
        unit_price: 100,
        line_net_amount: 100,
        tax_category: "Z",                    // Fail: Mismatch
        tax_rate: 0.05,                       // Fail: Rate mismatch for Z
        tax_amount: 50                        // Fail: Calculation mismatch
      }],
      tax_subtotals: [{
        tax_category_code: "S",
        tax_rate: 0.05,
        taxable_amount: 500,
        tax_amount: 25
      }],
      totals: {
        line_extension_amount: 100,
        total_without_tax: 100,
        tax_amount: 5,
        total_with_tax: 999,                  // Fail: Total mismatch
        amount_due: 105
      }
    }
  }
}

export const DEMO_API_KEY = 'demo-key-123'
