---
name: dead-reckoning
description: Injects precise factual assessment of what an information artifact is—its provenance, author posture, publication timing, platform context, and trustworthiness indicators—without subjective judgment or editorial bias.
agents: [grog]
---

# SKILL: Dead Reckoning

## Overview
**Dead Reckoning** is Grog's skill for establishing the navigational and contextual coordinates of an asset. It creates a concise, factual brief on *what this information artifact is*—not a summary of the body text, and not merely bibliographic citations, but a precise factual accounting of the source's background, platform posture, timing, and trustworthiness indicators.

Grog does **NOT** judge or moralize about the content or the source. Grog's mandate is to inject relevant factual context so that downstream agents (Cutlass, Bilgeladle, Scallywag) have the grounding necessary to make analytical and epistemic evaluations.

---

## Core Principles

1. **Facts Over Judgments**:
   - Do NOT say: *"The author is biased and trying to deceive readers."*
   - DO say: *"This content is written by a Harvard professor and bestselling non-fiction author, published in a major national magazine in response to a current event, coinciding with the promotional tour for her new book on the same topic."*
   - DO say: *"This article is from an online technology newsletter and appears largely generated or aggregated from secondary tech news sources; this publication routinely aggregates breaking news rapidly with variable editorial oversight."*

2. **Dimensions of Dead Reckoning**:
   - **Authorial Identity & Footing**: Current professional role, institutional affiliation, primary domain expertise, and known commercial/academic background.
   - **Publication & Platform Context**: Publication type (peer-reviewed journal, trade press, op-ed, Substack, corporate press release, anonymous forum), target audience, and editorial model.
   - **Timing & Catalyst**: Why was this published now? (e.g., in response to breaking news, regulatory filing, product release, book tour, venture funding round).
   - **Trustworthiness & Signal Indicators**: Primary vs. secondary sourcing, methodology presence, disclosures, and structural indicators of authenticity vs. aggregation/synthesis.

3. **Leveraging Cutlass's Stage 2 Assessment**:
   - When Cutlass's Stage 2 audit is provided in the prompt, Grog reads Cutlass's classification of what the asset "IS" (e.g. corporate whitepaper, agnotological PR release, academic study).
   - Grog uses Cutlass's findings to immediately anchor the factual provenance, author footing, and platform context without speculative searching, while strictly translating Cutlass's critique into neutral, objective facts.

4. **Single Asset Scope**:
   - Always executed on a single content asset. Never compare multiple assets in this skill.

---

## Output Format

When executing `dead-reckoning`, output a clean markdown section:

```markdown
### Dead Reckoning (Provenance & Context)
- **Artifact Nature**: [Brief statement of what the artifact physically and institutionally is]
- **Author & Affiliation**: [Author's verifiable background, institutional standing, and domain footing]
- **Platform & Medium**: [Publication venue, audience reach, and editorial context]
- **Publication Catalyst & Timing**: [Timing factors, news triggers, promotional cycles, or regulatory contexts]
- **Trustworthiness & Signal Indicators**: [Factual indicators: primary reporting vs curation/AI aggregation, direct attribution, disclosures]
```
