---
name: fact-plumbing
description: Plumbs the depth of a text to extract explicit assertions of fact and unstated assumptions, formatted as high-density bullet points structured for conversion into ontological triples.
agents: [grog]
---

# SKILL: Fact Plumbing

## Overview
**Fact Plumbing** (named for plumbing the depth and reading the knots along the lead line) is Grog's skill for extracting the core empirical and logical baseline of a text. Grog plumbs the document to identify:
1. **Explicit Assertions of Fact**: What the author directly claims is true, happened, or exists.
2. **Unstated Assumptions**: The implicit premises or foundational prerequisites the author relies upon without explicitly stating or proving them.

These extractions are expressed as precise bullet points containing sufficient subject-predicate-object clarity to be convertible into ontological triples `(Subject -> Predicate -> Object)`.

---

## Core Principles

1. **Brutal Reduction**:
   - Strip away rhetorical flourishes, analogies, metaphors, and emotional framing.
   - Retain only the verifiable assertion or the implicit presupposition.

2. **Triple-Ready Density**:
   - Each bullet point must specify the exact entity/agent (Subject), the action/relation/condition (Predicate), and the outcome/target/claim (Object).
   - Include specific dates, quantities, proper nouns, and concrete terms where present.

3. **Separation of Assertions from Assumptions**:
   - **Explicit Assertions**: Facts stated directly as truth in the text.
   - **Unstated Assumptions**: Necessary baseline beliefs required for the author's statements to hold, which the author took for granted without proving.

4. **Leveraging Cutlass's Stage 2 Assessment**:
   - Cutlass's Stage 2 audit flags specific causal leaps, unverified warrants, texture hacking, and epistemic failure modes.
   - Grog uses Cutlass's audit as an attentional guide to locate where the text makes unstated assumptions or relies on unsubstantiated assertions, plumbing them into precise structured points.

5. **Zero Editorializing**:
   - Grog does NOT evaluate whether an assertion is true or false.
   - Grog simply records: "The text asserts X" and "The argument assumes Y".

---

## Output Format

When executing `fact-plumbing`, structure the output as follows:

```markdown
### Fact Plumbing (Assertions & Assumptions)

#### Explicit Assertions of Fact
- [Subject] -> [Predicate / Relationship / Action] -> [Object / Empirical Claim / Metric]
- [Subject] -> [Predicate / Relationship / Action] -> [Object / Empirical Claim / Metric]

#### Unstated Assumptions
- [Implicit Premise 1: Foundational prerequisite taken as given without proof]
- [Implicit Premise 2: Unstated causal or institutional assumption required for the text's claims to hold]
```
