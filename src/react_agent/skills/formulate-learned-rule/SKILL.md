---
name: formulate-learned-rule
description: Inductive learning protocol. Extracts durable, generalized heuristics and architectural principles from specific operational incidents, corrections, or discoveries.
agents: [hook, pegleg, cutlass, grog, plank, bilgeladle, scallywag, spyglass]
---

# SKILL: Formulate Generalized Fleet Learning & Heuristic

## Overview
This skill governs how any NPT Fleet agent or progenitor (Hook, Antigravity) translates a concrete operational breakdown, human author correction, or discovery into a **durable, generalized cognitive heuristic**.

### Core Philosophy: Inductive Generalization over Brittle Proscription
- **Anti-Pattern (Brittle Rule)**: Hardcoding a point-in-time command with `ALWAYS`, `NEVER`, or `MUST` tied to a single domain name, chapter number, or temporary tool artifact (e.g. *"If URL is law.com, NEVER scrape"*).
- **Target Pattern (Generalized Heuristic)**: Abstracting the underlying cognitive, epistemic, or mechanical principle so the fleet makes intelligent decisions across all future analogous scenarios (e.g. *"When encountering hard commercial paywalls or deterministic auth barriers, immediately register domain telemetry to failed_metadata and pivot to open preprints or abstract extraction"*).

---

## The 3-Tier Inductive Abstraction Framework

Whenever tasked with learning or formulating a heuristic, execute this 3-step cognitive process:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. INCIDENT OBSERVATION (The Specific Concrete Trigger)                         │
│    What broke, failed, or was corrected in the immediate turn or session?      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 2. MECHANISTIC ROOT CAUSE (The Underlying Dynamic)                              │
│    Why did it fail? What systemic, epistemic, or technical friction occurred?   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 3. INDUCTIVE GENERALIZATION (The Durable Heuristic)                             │
│    What principle or decision model should guide future reasoning across ANY    │
│    similar chapter, URL, asset, or multi-agent interaction?                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Execution Protocol

### Step 1: Deconstruct the Incident
Identify the exact breakdown and separate the **incidental details** (specific URL, specific author name, specific line number) from the **architectural pattern**:
- Is this an *Access/Ingestion Barrier* (paywalls, anti-bot protections, rate limits)?
- Is this a *Bibliographic/Provenance Failure* (unanchored parent containers, missing URLs, placeholder strings)?
- Is this an *Epistemic/Analytical Failure* (accepting PR spin at face value, confusing narrative vignettes with core thesis vectors)?
- Is this an *Orchestration/Lifecycle Failure* (token runaway, premature circuit breaker tripping, directory naming divergence)?

### Step 2: Formulate the Heuristic (Generalize)
Draft the learning using the structured schema:
1. **`category`**: Choose from canonical operational categories:
   - `Epistemic & Knowledge-System Lenses`
   - `Access Barrier & Ingestion Triage`
   - `Bibliographic Architecture & Provenance`
   - `Manuscript Pedagogical & Structural Heuristics`
   - `Multi-Agent Orchestration & Circuit Breakers`
2. **`scope`**: `<AGENT_NAME_UPPER>_LOCAL` (if domain-specific) or `FLEET_UNIVERSAL` (if cross-cutting).
3. **`incident_context`**: 1-2 sentence description of the concrete trigger.
4. **`underlying_mechanism`**: 1-2 sentence explanation of the fundamental friction/cause.
5. **`generalized_heuristic`**: Clear, guidance-oriented principle for future decision-making. Avoid ungrounded prescriptive fluff.

---

## Required JSON Data Contract

```json
{
  "heuristic_id": "<AGENT_NAME_UPPER>-HEURISTIC-<NUMBER>",
  "scope": "<AGENT_NAME_UPPER>_LOCAL",
  "category": "<CATEGORY_NAME>",
  "incident_context": "Concrete summary of the specific event or correction that triggered this learning.",
  "underlying_mechanism": "Deconstruction of why the friction occurred.",
  "generalized_heuristic": "The durable, generalized heuristic guiding future autonomous choices.",
  "timestamp_utc": "YYYY-MM-DD HH:MM:SS UTC"
}
```

---

## Contrast Matrix: Weak vs. High-Value Heuristics

| Trigger Incident | Weak / Brittle Rule (DO NOT WRITE) | High-Value Generalized Heuristic |
| :--- | :--- | :--- |
| Scraping failed on `law.com` | `SPYGLASS-RULE-104: If URL is law.com, you MUST NEVER scrape it.` | `ACCESS_BARRIER_TRIAGE: When acquisition tools encounter hard commercial paywalls or deterministic authentication walls, do not waste turns on speculative browser retries. Register domain telemetry to cargo.failed_metadata immediately and pivot to open preprints or author repositories.` |
| Chapter 1 Section 1.1 vignette mistreated as thesis | `BILGELADLE-RULE-007: Section 1.1 is Paul Yura and you MUST NOT treat him as the thesis.` | `VIGNETTE_ANCHORING_PRINCIPLE: Opening chapter sections are illustrative narrative vignettes, not core theoretical vectors. Expand narrative vignettes after core thesis reductions are established, anchoring human stories directly to the systemic vectors of knowledge destruction.` |
| CrossRef returned bad metadata on book chapter | `PLANK-RULE-102: CrossRef failed on History of AI so NEVER use it for books.` | `MULTI_TIER_BIBLIOGRAPHIC_RESOLUTION: Query CrossRef for journal articles and formal conference proceedings where DOI matching is robust; for book chapters or non-standard monographs, verify the parent book container and fallback to search grounding or official library catalogs.` |

---

## Step 3: Commit via Memory Tools
Call `record_learned_rule(agent_name, learning_json)` or `record_fleet_learning(agent_name, learning_json)`. The tool will automatically check for existing heuristics in the same domain to prevent duplicate accumulation.
