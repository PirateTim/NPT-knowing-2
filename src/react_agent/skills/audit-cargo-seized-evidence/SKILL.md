---
name: audit-cargo-seized-evidence
description: Audits Silver manuscript assertions against captured web text already seized by Spyglass in the Cargo Hold / GCP Bucket.
agents: [cutlass, grog]
---

# SKILL: Audit Cargo Seized Evidence

## Overview
This skill audits whether the content of external assets seized by **Spyglass** into the Cargo Hold / GCP Bucket empirically supports the specific thesis assertions made in the Silver manuscript text.

---

## Execution Protocol

1. **LOAD SEIZED ASSET**:
   - Read the captured document payload directly from Cargo Hold / GCP Bucket (`read_knowledge_artifact`) or local acquisitions (`read_local_file`) already seized by Spyglass.
   - DO NOT call Landlubber to re-fetch the web page.

2. **ASSERTION COMPARISON**:
   - Extract the specific manuscript claim or Toulmin argument relying on this citation.
   - Compare the claim against the actual text payload of the seized asset.

3. **EVIDENTIARY EVALUATION**:
   - Verify if the seized source text explicitly proves, grounds, or demonstrates the claim.
   - Audit for misattribution, exaggeration, or synthetic translation laundering.

4. **SAIL LOCKER TAXONOMY ASSIGNMENT**:
   - Assign the asset to EXACTLY ONE of the four uppercase Sail Locker categories:
     - `MAINSAIL`: Direct ground-truth evidence supporting the 3-stage Chain of Ruin. Triggers full Grog/Bilgeladle/Scallywag processing.
     - `BILGE`: Active specimen of agnotology / corporate slop that degrades reader critical thinking.
     - `JIB`: Secondary institutional critique / bad actor anecdote.
     - `DOLDRUMS`: Ambiguous or unclassified content. **Pegleg uses DOLDRUMS to HALT downstream agent processing and quarantine the asset for the Captain's (Author's) review.**
   - DO NOT output custom text strings into `sail_locker`.

5. **AUDIT DISPOSITION**:
   - `VERIFIED_PASS`: The seized Cargo Hold content empirically validates the manuscript claim.
   - `FLAGGED_EVIDENTIARY_MISMATCH`: The seized content contradicts, misattributes, or fails to support the claim.
