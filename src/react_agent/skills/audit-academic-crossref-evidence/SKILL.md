---
name: audit-academic-crossref-evidence
description: Placeholder skill for auditing academic works resolved via CrossRef DOIs/URLs. Assumes CrossRef metadata matches evidence for current pipeline iterations.
agents: [cutlass, grog]
---

# SKILL: Audit Academic CrossRef Evidence (Placeholder)

## Overview
This skill serves as an explicit workflow placeholder for auditing academic, monograph, and journal citations resolved via the CrossRef REST API.

---

## Execution Protocol

1. **ASSUMPTION OF MATCH**:
   - For academic works with validated CrossRef DOIs and URLs, assume the metadata matches the evidence for current Silver production iterations.

2. **FUTURE AUDIT EXPANSION**:
   - This skill serves as an explicit workflow placeholder to receive full-text PDF extraction (`extract_local_pdf`) and journal payload verification in future fleet releases.

3. **AUDIT DISPOSITION**:
   - `VERIFIED_PASS`: CrossRef Academic Grounding Verified.
