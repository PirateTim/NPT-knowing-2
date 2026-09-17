---
name: extract-epistemic-triples
description: Extracts two-tier epistemic triples (operatives + upstream institutional enablers), witness warrants, and terminal doom points from manuscript sections and external cargo.
agents: [bilgeladle]
---

# SKILL: Extract Epistemic Triples

## Purpose & Architectural Mandate
This skill governs **BILGELADLE** in converting manuscript sections or external cargo assets into formal, human-attributed, two-tier epistemic triples for the Fleet Knowledge Graph in PostgreSQL (`cargo.ontology_*`).

It strictly enforces the foundational epistemology of *The End of Knowing*:
1. **Agency is Human:** Inanimate constructs, corporations, and algorithms do not make choices. Specific individuals and defined editorial gatekeepers make choices.
2. **The Invariant Predicates:**
   - `destroys our ability to know anything` (Cognitive / immediate citizen blinding)
   - `does permanent epistemic damage to the human knowledge system` (Structural / archive contamination)
3. **The Two-Tier Attribution Mandate:** Every extraction must capture both the front-line operative and the upstream institutional gatekeeper who granted the platform.
4. **The Witness Quarantine:** Diagnosticians, whistleblowers, and critics (e.g. Ben Smith, I.F. Stone, Michael Hastings) are witnesses/warrants; they are strictly barred from being the Subject of a destruction triple.
5. **The Doom Point Requirement:** Every triple must trace the choice past the midpoint mechanism directly to the terminal, catastrophic failure state.

---

## The Execution Protocol

### Step 1: Text Disambiguation & Role Partitioning
Read the target section or asset and partition all mentioned entities into two strict sets:
* **Perpetrators & Enablers:** Human beings making deliberate choices to dissociate from obtainable empirical facts, or gatekeepers authorizing the publication of unverified claims.
* **Witnesses & Diagnosticians:** Observers, scholars, or chroniclers diagnosing the failure or providing testimony. (These MUST be quarantined into `witness_testimony`).

### Step 2: The Two-Tier Attribution Mapping

For every event of epistemic destruction, generate a **Twin Triple**:

#### Tier 1: The Operative Triple (The Bylined / Front-Line Actor)
* **Subject:** The specific individual with the byline, microphone, or office (e.g., `Judith Miller`, `Ross Douthat`, `Dick Cheney`).
* **Predicate:** `destroys our ability to know anything`
* **Qualifier:** The deliberate behavioral choice, starting with `by choosing not to obtain obtainable empirical facts...` or `by choosing to launder...`
* **The Doom Point:** The immediate cognitive blinding or manufactured consent inflicted on the public.

#### Tier 2: The Upstream Enabler Triple (The Institutional Gatekeeper)
* **Subject:** The decision-makers who controlled the publishing apparatus, masthead, or charter (e.g., `The decision makers at The New York Times who decided this fit the tagline of "All the News That's Fit to Print"`).
* **Predicate:** `does permanent epistemic damage to the human knowledge system`
* **Qualifier:** The institutional choice to stamp the unverified or narcissistic claim with the prestige of the institution.
* **The Doom Point:** The permanent, structural poisoning of the public historical record and civilizational training distribution.

### Step 3: Witness Warrant Attachment
Attach any diagnostic quotes, citations, or historical testimony (e.g., Ben Smith in *Traffic*, I.F. Stone, Michael Hastings) as evidentiary warrants backing the triples.
