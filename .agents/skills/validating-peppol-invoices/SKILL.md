---
name: validating-peppol-invoices
description: Validates Peppol UBL XML invoices and credit notes
  against EN16931 (CEN) and Peppol BIS Billing 3.0 schematron
  rules via the Peppol Validator API. Use when validating
  e-invoices, checking Peppol compliance, debugging UBL XML
  validation errors, or verifying invoices before sending via
  the Peppol network.
---

# Validating Peppol Invoices

POST XML to the Peppol Validator API and parse the JSON result.

## Endpoint

`POST https://peppolvalidator.com/api/v1/validate`

Send raw XML with `Content-Type: application/xml`:

```bash
curl -X POST https://peppolvalidator.com/api/v1/validate \
  -H "Content-Type: application/xml" \
  -d @invoice.xml
```

Returns JSON with status ("valid" / "invalid" / "error"),
errors, warnings, and invoice metadata.
