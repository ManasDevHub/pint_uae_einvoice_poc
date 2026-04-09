# Future Roadmap & Scaling

Currently, the POC handles a subset of business cases (a clean B2B Invoice with minimal tax setups). To evolve this into a **fully scalable SaaS compliance engine**, the following roadmap must be pursued.

## Phase 1: Full Standard Implementation
1. **Expand Configuration**: Define all 51 PINT AE mandatory rules within `uae_pint_ae_rules.json` and build test cases for all boundary values.
2. **UBL 2.1 XMLEngine**: The POC stubs XML validation. In production, we integrate `lxml` with `.xsd` validation mapping to the EN 16931 ruleset. Full Schematron file ingestion capability.
3. **Tax Code Coverage**: Enhance calculation validators to parse multi-tax level mappings (e.g., standard S, zero Z, exempt E).

## Phase 2: ERP Integration Automation & Adapters
1. **Adapter Layer**: Build microservices that transform standard Oracle/SAP IDOCs and Dynamics 365 JSON schemas into the internal `InvoicePayload`.
2. **Webhooks / Event Bus**: Transition from REST to Kafka or RabbitMQ event-driven messaging to buffer 10,000+ invoice traffic asynchronously during month-end.

## Phase 3: Tenant Security & Dashboarding
1. **Multi-Tenancy Setup**: Parameterize `uae_pint_ae_rules.json` per organization (tenant) using database routing.
2. **Reporting**: Expose telemetry directly to ELK Stack or Prometheus, powering a "Dashboard" for executives checking error distributions over time. 
3. **Real ASP connection**: Drop the `asp_mock` and integrate securely using mTLS with live Peppol/ASP access points.
