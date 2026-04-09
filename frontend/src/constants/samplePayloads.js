export const SAMPLES = {
  b2b: {
    label: 'Valid B2B',
    color: 'text-emerald-400',
    payload: {
      invoice_number: "INV-2026-AE-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-30",
      invoice_type_code: "380",
      payment_means_type_code: "10",
      transaction_type: "B2B",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "accounts@adamas-tech.ae",
        seller_legal_registration: "DED-2024-12345",
        seller_registration_identifier_type: "DED",
        seller_address: "Dubai Internet City, Dubai, UAE",
        seller_city: "Dubai",
        seller_subdivision: "DU",
        seller_country_code: "AE"
      },
      buyer: {
        buyer_name: "Gulf Trading FZE",
        buyer_trn: "100999888777666",
        buyer_electronic_address: "finance@gulftrade.ae",
        buyer_legal_registration: "ADGM-2023-67890",
        buyer_registration_identifier_type: "ADGM",
        buyer_address: "Abu Dhabi, UAE",
        buyer_city: "Abu Dhabi",
        buyer_subdivision: "AZ",
        buyer_country_code: "AE"
      },
      lines: [{
        line_id: "1",
        item_name: "ERP Consulting Services",
        unit_of_measure: "EA",
        quantity: 10,
        unit_price: 500,
        line_net_amount: 5000,
        tax_category: "S",
        tax_rate: 0.05,
        tax_amount: 250
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
    label: 'Valid B2C',
    color: 'text-sky-400',
    payload: {
      invoice_number: "INV-POS-2026-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-15",
      invoice_type_code: "380",
      payment_means_type_code: "30",
      transaction_type: "B2C",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "pos@adamas-tech.ae",
        seller_legal_registration: "DED-123",
        seller_registration_identifier_type: "DED",
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
        unit_of_measure: "EA",
        quantity: 2,
        unit_price: 100,
        line_net_amount: 200,
        tax_category: "S",
        tax_rate: 0.05,
        tax_amount: 10
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
      invoice_number: "CN-AE-2026-001",
      invoice_date: "2026-04-01",
      payment_due_date: "2026-04-10",
      invoice_type_code: "381",
      payment_means_type_code: "10",
      transaction_type: "B2B",
      currency_code: "AED",
      tax_category_code: "S",
      seller: {
        seller_name: "Adamas Tech Consulting LLC",
        seller_trn: "100200300400500",
        seller_electronic_address: "accounts@adamas-tech.ae",
        seller_address: "Dubai Internet City",
        seller_city: "Dubai",
        seller_subdivision: "DU",
        seller_country_code: "AE",
        seller_legal_registration: "DED-123",
        seller_registration_identifier_type: "DED"
      },
      buyer: {
        buyer_name: "Gulf Trading FZE",
        buyer_trn: "100999888777666",
        buyer_address: "Abu Dhabi",
        buyer_city: "Abu Dhabi",
        buyer_subdivision: "AZ",
        buyer_country_code: "AE",
        buyer_legal_registration: "ADGM-456",
        buyer_registration_identifier_type: "ADGM"
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
