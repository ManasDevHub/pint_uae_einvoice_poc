# Architecture Diagram for UAE E-Invoicing Engine

```mermaid
graph TD
    A[ERP System] -->|JSON/XML Payload| B(FastAPI Endpoint: /api/v1/validate-invoice)
    
    subgraph Core Engine [Validation Platform]
    B --> C{Transformation Layer}
    C --> |Pydantic Models| D[Invoice Validator]
    D --> E(Rule Engine)
    
    subgraph Configuration
    E -.-> F[uae_pint_ae_rules.json]
    F -.-> |Loads dynamic format/presence rules| E
    end
    
    D --> G(Mathematical Cross-Check Engine)
    D --> H(XML Schematron Validator Mock)
    
    E --> |Format Results| D
    G --> |Calculation Results| D
    H --> |UBL XSD Results| D
    end
    
    D --> |Generates Validation Report| I[API Response]
    
    J[Mock ASP/FTA Node] -.->|External Integration Mock| B
```

## System Layers
1. **Input Layer**: Handles generic JSON/XML payloads coming from the ERP Adapters.
2. **Transformation Layer**: Maps data to the core standardized schema.
3. **Core Engine (Validator)**: The brain of the POC holding hardcoded logic (Cross Checks).
4. **Rule Engine**: Loads runtime configuration for 51 PINT mandatory rules (presence, regex).
5. **ASP Mock**: Allows E2E integration testing to simulate response from actual Tax APIs.
