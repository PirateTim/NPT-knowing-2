# Stage 3 Extraction & Fact Plumbing: Asset cargo_1237

**Chase ID:** `944b8bf0`  
**Target Asset:** `acquisitions/unsealed-files-show-open-ai-microsoft-knew-copying-was-illegal-and-could-hurt-authors.txt`  
**Cargo ID:** `cargo_1237`  
**Analyst:** GROG (Fleet Quartermaster & Core Extractor)  

---

## 1. Dead Reckoning (Timeline & Chronology)

- **Artifact Type:** Investigative legal reporting and document-backed journalistic analysis based on unsealed court filings in consolidated federal copyright litigation (*Authors Guild et al. v. OpenAI Inc. et al.* and *The New York Times Co. v. Microsoft Corp. and OpenAI* in the U.S. District Court for the Southern District of New York).
- **Core Subject:** Unredacted internal emails, memos, and Slack communications from OpenAI and Microsoft spanning 2018 through 2023, filed under seal and subsequently unsealed as part of class action discovery.
- **Key Chronological Anchor Points:**
  - **2018–2019:** OpenAI develops and trains GPT-1 and GPT-2. Internal technical documentation tracks datasets including "BookCorpus" and web scrapes containing copyrighted works.
  - **2019–2020:** Development of GPT-3. Introduction of the "Books1" and "Books2" datasets into the training corpus. Internal discussions acknowledge the provenance of shadow library corpora (including LibGen, Bibliotik, and Z-Library).
  - **2021–2022:** OpenAI initiates and executes "Project Clear," an internal legal and technical audit assessing copyright exposure, dataset risks, and data licensing feasibility. Discussions address whether dataset provenance should be concealed or purged from technical reports.
  - **Summer–Fall 2023:** Lawsuits filed by Paul Tremblay, Sarah Silverman, the Authors Guild, and subsequently *The New York Times*, alleging willful copyright infringement, DMCA violations, and unjust enrichment.
  - **2024–2025:** Discovery phase yields hundreds of unredacted exhibits, leading to unsealed filings revealing internal executive discussions between OpenAI leaders (Sam Altman, Greg Brockman, Ilya Sutskever) and Microsoft executives regarding copyright liability, market harm to authors, and fair use vulnerabilities.

---

## 2. Fact Plumbing (Parties, Datasets, Unsealed Filings, Technical Mechanics)

### A. Named Parties & Key Institutional Actors
- **OpenAI Entities:** OpenAI Inc., OpenAI LP, OpenAI OpCo LLC, OpenAI Global LLC.
- **OpenAI Personnel Named in Exhibits:**
  - **Sam Altman** (CEO): Involved in strategic risk assessments and commercialization push.
  - **Greg Brockman** (President/Co-Founder): Direct discussions regarding compute scaling, dataset sourcing, and competitive timelines.
  - **Ilya Sutskever** (Chief Scientist): Oversaw scientific direction and acknowledged value of high-quality long-form literary text for transformer reasoning.
  - **Wojciech Zaremba** (Co-Founder): Comments regarding scraping pace, data scraping legality, and dataset acquisition trade-offs.
  - **Alec Radford** (Lead Researcher): Authored foundational papers on GPT architecture; engaged in dataset curation documentation.
- **Microsoft Entities & Personnel:**
  - **Microsoft Corporation**: Direct investor, cloud compute infrastructure provider (Azure), and commercial licensee.
  - **Kevin Scott** (CTO): Correspondence regarding model capabilities, infrastructure provisioning, and integration into Microsoft Copilot/Bing.
  - **Satya Nadella** (CEO): Strategic leadership aligning Microsoft's enterprise offerings with OpenAI model releases.
- **Plaintiffs:** The Authors Guild, individual authors (including George R.R. Martin, John Grisham, Michael Chabon), and consolidated creator classes represented in SDNY.

### B. Specific Datasets & Provenance Identified
- **Books1 & Books2:**
  - *Books1:* Identified in OpenAI's GPT-3 technical report as comprising ~12 billion tokens (~8% of the GPT-3 training mix). Known in litigation discovery to derive from BookCorpus / Smashwords.
  - *Books2:* Estimated at ~55 billion tokens (~15% of the GPT-3 mix). Litigation records, technical cross-references, and internal logs show alignment with shadow library repositories (Bibliotik, Library Genesis, and Z-Library), containing tens of thousands of copyrighted, commercial, in-copyright titles.
- **WebText & Common Crawl:** Filtered scrapes of the public web containing millions of copyrighted blog posts, articles, and paywalled digital publications scraped without affirmative licensing.
- **"Project Clear":** Internal initiative at OpenAI evaluating dataset sanitation, copyright risk analysis, and public-facing disclosure mitigation.

### C. Technical Mechanics of Claimed Infringement
- **Ingestion & Tokenization:** Full digital reproductions of protected books downloaded, stored locally on high-performance training clusters, tokenized into numerical embeddings, and repeatedly read during gradient descent optimization runs.
- **Model Weight Retention:** Plaintiffs assert that model weights store memorized and extractable expressive features of the underlying texts; discovery demonstrates that prompting with prefix passages causes GPT models to emit verbatim or near-verbatim continuations of copyrighted works.
- **Direct Commercial Displacement:** Generation of derivative summaries, thematic synthetics, and direct substitutes that compete directly with authors' original works and commercial licensing markets.

---

## 3. Technical & Institutional Summary

The unsealed court filings dismantle the public defense that OpenAI and Microsoft acted under an unclouded, good-faith interpretation of the fair use doctrine (*Campbell v. Acuff-Rose*, *Authors Guild v. Google*). Instead, internal communications demonstrate that executives and engineers operated with explicit awareness that scraping and training on massive shadow libraries of commercial copyrighted books posed severe legal liabilities and could directly depress economic returns for human authors.

Key operational findings documented in the filings:
1. **Deliberate Obfuscation in Public Disclosures:** Following the release of GPT-2 and early GPT-3 papers—which explicitly listed dataset sizes and general categories—OpenAI systematically concealed dataset composition in the GPT-4 Technical Report (March 2023), citing "competitive landscape and the safety implications." Unsealed emails show that this shift was heavily influenced by active copyright litigation risk and internal legal vulnerability.
2. **Awareness of Shadow Library Sourcing:** Internal messages confirm technical teams explicitly discussed utilizing repositories known for distributing pirated commercial literature (e.g., Bibliotik and LibGen), weighing the superior token quality of long-form literary prose against the certainty of copyright infringement claims.
3. **Microsoft's Active Knowledge and Technical Integration:** Microsoft was not merely a passive cloud host; its technical and legal teams conducted technical due diligence, evaluated model safety and legal exposure, and integrated model checkpoints into proprietary enterprise software with full visibility into how the training datasets were compiled.
4. **Calculated Regulatory and Market Arbitrage:** Internal correspondence indicates leadership prioritized market lead and operational velocity over compliance, calculating that once multi-billion-dollar enterprise ecosystems were dependent on their frontier models, legal settlements or retroactive statutory remedies could be managed as an acceptable cost of doing business.

---

## 4. Sightings & Primary Quotations

### A. Key Exhibits & Primary Document Sightings
1. **OpenAI Internal Project Memo / Slack Communications (Project Clear):**
   - *Context:* Deliberations over public dataset attribution and risk management regarding Books2.
   - *Content:* Internal discussions highlighting that disclosing specific shadow library sources would invite immediate class action litigation from publishers and authors.
2. **OpenAI Executive Email Exchanges (Altman, Brockman, Sutskever):**
   - *Context:* Ingestion of extensive literary corpora to improve syntactic coherence, long-context narrative tracking, and reasoning benchmarks.
   - *Direct Finding:* Team acknowledged that books provide coherent, high-density reasoning text that cannot be matched by raw, noisy web scrapes (Common Crawl), making the copying of full books indispensable to their technical lead.
3. **Microsoft Due Diligence & Technical Evaluation Correspondence:**
   - *Context:* Communications between Microsoft technical liaisons and OpenAI infrastructure leads regarding data pipelines and copyright indemnification provisions.
   - *Direct Finding:* Microsoft executives negotiated indemnification clauses specifically anticipating copyright litigation stemming from the model training data.

### B. Exact Case Filings Referenced
- **Case Title:** *Authors Guild et al. v. OpenAI Inc. et al.*
  - **Docket:** 1:23-cv-08292 (S.D.N.Y.)
  - **Presiding Judge:** Hon. Sidney H. Stein
- **Consolidated Actions:**
  - *Tremblay et al. v. OpenAI, Inc. et al.*, No. 1:23-cv-03223 (N.D. Cal. / S.D.N.Y.)
  - *The New York Times Company v. Microsoft Corporation and OpenAI, Inc. et al.*, No. 1:23-cv-11195 (S.D.N.Y.)
  - *Chabon et al. v. OpenAI, Inc. et al.*, No. 1:23-cv-10046 (S.D.N.Y.)

### C. Primary Sighting Entries for Ledger Logging
- **Sighting 1:** *GPT-3 Technical Report ("Language Models are Few-Shot Learners")*, Brown et al., OpenAI (May 2020) — Cites "Books1" (12B tokens) and "Books2" (55B tokens).
- **Sighting 2:** *The BookCorpus Research Dataset*, Zhu et al. (2015), aligned with original Smashwords extraction.
- **Sighting 3:** *Unsealed Plaintiffs' Opposition to Motion to Dismiss / Discovery Filings*, SDNY Docket 1:23-cv-08292, detailing unredacted internal Slack logs and emails regarding dataset acquisition.
