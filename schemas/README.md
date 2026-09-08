# Data Validation Schemas (`schemas/`)

This directory houses formal JSON and YAML schemas used to validate data contracts, API payloads, agent handoff structures, and metadata models across the NPT Fleet.

---

## 📋 Active & Planned Schemas

### 1. Citation & Reference Payloads
- `citation_payload_schema.json`: Formal JSON schema defining the required structure for reference vector nodes, CrossRef metadata, Zotero fields, and URL provenance.
- `citation_payload_example.json`: Few-shot exemplar demonstrating a valid, schema-compliant citation payload.

### 2. Extensible Data Contracts (Under Active Development)
This directory is designated for all machine-verifiable contracts across the fleet, including:
- **Chase Response Schemas**: Multi-stage gate output formats for Pegleg orchestrations.
- **Zotero Metadata YAML Schemas**: Intellectual provenance mappings for Zotero integration.
- **Ontology Extraction Schemas**: LangExtract and Turtle RDF graph validation contracts.
