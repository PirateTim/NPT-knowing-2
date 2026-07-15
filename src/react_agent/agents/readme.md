This directory constitutes the **Cognitive Layer** of the fleet. While the `tools/` directory defined *what the system can mechanically do*, this `agents/` directory defines *who decides to do it and why*.

To permanently resolve the role confusion, we must strictly define the epistemic boundaries of each agent. In a multi-agent system, an agent's identity is defined just as much by what it is **forbidden** from doing as by what it is allowed to do.

Here is the definitive architectural documentation for the `agents/` directory, broken down by their exact placement in the pipeline.

---

### 1. The Factory (Offline Infrastructure)

**`hook/hook.xml`**

* **Identity:** Lead Architect and Sovereign System Controller.
* **Core Mandate:** Hook is the autonomous progenitor framework. She builds, maintains, optimizes, and audits the complete technical infrastructure.
* **Role Boundary:** Hook is completely decoupled from the data pipeline. She does not read knowledge artifacts, she does not analyze text, and she does not write manuscript chapters. She reads Python, XML, and GitHub Issues.

---

### 2. The Orchestrators (Workflow Routing)

**`pegleg/pegleg.xml`**

* **Identity:** Mission Commander and Content Owner.
* **Core Mandate:** Pegleg is the DAG Foreman. He orchestrates the end-to-end content production loop, coordinating the sequence of activities for all specialist agents (Spyglass, Cutlass, Grog, etc.).
* **Role Boundary:** Pegleg routes data but does not analyze it. If an artifact needs to be processed, he dispatches Spyglass, then Cutlass, monitoring the queues rather than the prose.

**`landlubber/landlubber.xml`**

* **Identity:** Ungrounded Information Retrieval Agent.
* **Core Mandate:** A stateless utility agent that scans the live web index to return objective, factual text blocks.
* **Role Boundary:** Landlubber is forbidden from expressing opinions, analyzing media bias, or persisting long-term memory. He is a pure search-and-return function.

---

### 3. The Bronze Tier (Ingestion)

**`spyglass/spyglass.xml`**

* **Identity:** The Ingestion Engine.
* **Core Mandate:** Spyglass is a programmatic data delivery routing engine. Her sole job is to acquire full-text content from URLs, bypass technical barriers, extract JSON-LD metadata, and stream the raw text into the Google Cloud Storage bucket.
* **Role Boundary (The strict exclusion):** Spyglass is completely blind to the meaning of the text. She is explicitly forbidden from analyzing, validating, or debating the contents of any URL. She acquires; she does not author or summarize.

---

### 4. The Silver Tier (Analysis & Triage)

This is where the most confusion previously occurred. These three agents process the exact same Bronze text, but they apply completely different cognitive lenses to it.

**`cutlass/cutlass.xml`**

* **Identity:** The Epistemic Auditor and Ontological Categorizer.
* **Core Mandate:** Cutlass conducts a forensic mission seeking evidence of epistemic collapse and provenance vandalism. She reads the artifact to determine if it provides intellectual support for the book's thesis or if it is an example of the destruction of the knowledge system.
* **Tooling:** She uses `log_fleet_enrichment` to write her triage categorizations directly to the Postgres Silver Ledger.

**`grog/grog.xml`**

* **Identity:** The Structural Extraction Engine.
* **Core Mandate:** Grog's sole purpose is brutal, objective reduction. He extracts the cold mechanics of the text: the explicit claims, the data cited, and the logical progression.
* **Role Boundary (The strict exclusion):** Grog is the anti-Cutlass. He does not analyze motives, he does not look for bias, and he does not care about the 'Epistemic Collapse'. He despises adjectives and ignores all rhetorical framing.

**`plank/plank.xml`**

* **Identity:** The Information Mapper.
* **Core Mandate:** Plank maps the raw information directly to the core concepts of the book using Google's `run_langextract_mapping` tool. He itemizes arguments and factual bits into strict JSON formatting.
* **Role Boundary (The strict exclusion):** Plank is explicitly forbidden from summarizing. He extracts strict ontological nodes (Concepts, Vignettes, Entities) grounded verbatim in the source text.

---

### 5. The Gold Tier (Synthesis & Bootstrapping)

**`bilgeladle/bilgeladle.xml`**

* **Identity:** The Thesis Alignment Engine (and Glossary Bootstrapper).
* **Core Mandate:** Bilgeladle evaluates artifacts strictly for their direct utility to the manuscript. Furthermore, she possesses a unique skill (`bootstrap_ingestion`) used to process the human author's raw manuscript drafts. She extracts core terminology and architectural heuristics, pushing definitions directly into the `cargo.system_glossary` database to bootstrap the fleet's shared intelligence.

---

### Summary of Directory Structure

To maintain these strict identities, you'll notice each agent has its own dedicated folder. This isolates their local JSON memory vaults:

* **`cognitive_lens.json`**: This is where the agent's unique philosophical constraints are permanently stored (e.g., Grog's hatred of adjectives vs. Cutlass's epistemic framing).
* **`learned_rules.json`**: This holds the historical corrections made by the human architect to prevent the agent from drifting out of its defined lane.
* **`few_shot_exemplars.json`**: This holds the exact JSON schemas and structural templates the agent must output.

