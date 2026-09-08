"""
NPT Fleet Tools: Bilgeladle Chapter Structural Analysis & Synthesis Essay Engine
Architecture: Map-Expand-Reduce Thesis Alignment (ADR-005)
"""
import os
import re
import json
import time
import datetime
from urllib.parse import urlparse
import pg8000.dbapi
from google import genai
from google.genai import types

def _get_cargo_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("[ERROR] CONTENT_DATABASE_URL not set in environment.")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def _read_chapter_silver_text(chapter_number: int) -> str:
    """Helper: Reads section or chapter text prioritizing local Bronze+ tier."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ch_slug = f"ch{chapter_number:02d}"
    
    # 1. Try Bronze+ chapter directory
    bronze_plus_dir = os.path.join(base_dir, "ship", "bronze_plus", "chapters", ch_slug)
    if os.path.exists(bronze_plus_dir):
        sections = []
        for fname in sorted(os.listdir(bronze_plus_dir)):
            if fname.endswith("_bronze_plus.md"):
                with open(os.path.join(bronze_plus_dir, fname), "r", encoding="utf-8") as f:
                    sections.append(f.read())
        if sections:
            return "\n\n---\n\n".join(sections)

    # 2. Try Bronze chapter directory
    bronze_dir = os.path.join(base_dir, "ship", "bronze", "chapters", ch_slug)
    if os.path.exists(bronze_dir):
        sections = []
        for fname in sorted(os.listdir(bronze_dir)):
            if fname.endswith("_bronze.md"):
                with open(os.path.join(bronze_dir, fname), "r", encoding="utf-8") as f:
                    sections.append(f.read())
        if sections:
            return "\n\n---\n\n".join(sections)

    # 3. Fallback to Sacred Monolith
    monolith = os.path.join(base_dir, "manuscript", "2026-02-24AChapters_complete.md")
    if os.path.exists(monolith):
        with open(monolith, "r", encoding="utf-8") as f:
            return f.read()

    raise FileNotFoundError(f"Could not find text for Chapter {chapter_number}")

def _get_learnings_file_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents", "bilgeladle", "chapter_learnings.json"))

def _load_chapter_learnings() -> dict:
    path = _get_learnings_file_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_chapter_learning(chapter_number: int, learning: str):
    path = _get_learnings_file_path()
    learnings = _load_chapter_learnings()
    learnings[str(chapter_number)] = {
        "chapter_number": chapter_number,
        "thesis_insight": learning,
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(learnings, f, indent=2)

def perform_chapter_structural_analysis(chapter_number: int) -> str:
    """
    Agent Tool: Performs chapter-level structural analysis.
    Isolates core vector of knowledge destruction FIRST, then narrative vignette, anchor quotes,
    Chain of Ruin vector breakdown, and Heroes vs. Villains ledger.
    Inherits cumulative thesis insights from prior chapters (1..N-1, or 1..12 recursion).
    """
    try:
        ch_text = _read_chapter_silver_text(chapter_number)

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        client = genai.Client(api_key=api_key)

        # Build cumulative thesis progression from PREVIOUS chapter learnings (strictly < chapter_number)
        learnings_dict = _load_chapter_learnings()
        cumulative_md = ""
        prior_keys = [k for k in learnings_dict.keys() if int(k) < chapter_number]
        if prior_keys:
            cumulative_md = "CUMULATIVE THESIS PROGRESSION (Prior Chapter Learnings):\n"
            for k in sorted(prior_keys, key=lambda x: int(x)):
                item = learnings_dict[k]
                cumulative_md += f"- Chapter {item['chapter_number']}: {item['thesis_insight']}\n"
        else:
            cumulative_md = "CUMULATIVE THESIS PROGRESSION: No prior chapter learnings (First Chapter in Sequence).\n"

        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine and Master Philologist for 'The End of Knowing'.
Analyze the following text of Chapter {chapter_number} of the manuscript and perform a rigorous structural analysis.

{cumulative_md}

CRITICAL DIRECTIVE ON VIGNETTES:
Nearly every chapter opens with a narrative vignette (a case study or anecdote). DO NOT fall into the 'Vignette Trap' of treating the opening story as the theme itself. The vignette is merely forensic evidence; the theme is always the structural, philosophical, or epistemological vector of knowledge destruction (e.g. abandoning formal logic for probabilistic prediction, data exhaustion limits, active fraud of context).

CHAPTER TEXT:
{ch_text}

Perform a 5-part structural analysis formatted in JSON:

1. "vector_of_knowledge_destruction": Identify the core epistemological suicide pact, institutional lie, or structural collapse explored in this chapter. (MUST BE EXTRACTED FIRST BEFORE LOOKING AT THE VIGNETTE).
2. "vignette": Describe the opening narrative vignette or case study used merely as an illustrative vehicle to ground the chapter.
3. "anchor_quotes": Identify key anchor quotes used in the chapter, the original authors/thinkers (e.g., Ayn Rand, Noam Chomsky, Yann LeCun, Alan Sokal, etc.), their intellectual roots, and WHY they were chosen to anchor this chapter's thesis.
4. "chain_of_ruin": Map out how the 3 stages manifest in this chapter:
   - "pre_existing_decay": Pre-existing institutional/systemic erosion prior to tech.
   - "technological_catalyst": How new technology accelerates and scales the consequences.
   - "proactive_negligence": Specific human failure and intentional abandonment of verification duties.
5. "heroes_and_villains":
   - "heroes": List of defenders of ground-truth, human lineage, and verification in this chapter with their role.
   - "villains": List of agents/institutions of active ignorance, commercial liquidation, or epistemic sabotage.

Return ONLY a valid JSON object matching this structure.
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

        res_text = response.text.strip()

        # Save extracted vector_of_knowledge_destruction into cumulative learning vault
        try:
            parsed = json.loads(res_text)
            vector_insight = parsed.get("vector_of_knowledge_destruction", "")
            if vector_insight:
                _save_chapter_learning(chapter_number, vector_insight)
        except Exception as parse_err:
            print(f"[WARNING] Could not parse JSON to update chapter learnings: {parse_err}")

        return res_text

    except Exception as e:
        return f"[ERROR] perform_chapter_structural_analysis failed: {str(e)}"

def _filter_section_text(ch_text: str, section_filter: str) -> str:
    """Helper: Filters chapter silver text to isolate a specific section (e.g. '1.2' or 'Section 1.2')."""
    if not section_filter:
        return ch_text
    
    sec_num = str(section_filter).strip().lstrip("section ").strip()
    
    # Split text into markdown headers
    pattern = r'(^#+\s+.*)'
    parts = re.split(pattern, ch_text, flags=re.MULTILINE)
    
    matching_text = []
    capture = False
    
    for i in range(1, len(parts), 2):
        header = parts[i]
        content = parts[i+1] if i+1 < len(parts) else ""
        
        # Match header containing section number (e.g., '1.2' or 'Section 1.2')
        if re.search(r'\b' + re.escape(sec_num) + r'\b', header, re.IGNORECASE) or sec_num.lower() in header.lower():
            capture = True
            matching_text.append(f"{header}\n{content}")
        elif capture:
            # Stop capturing if we hit another main section header
            if re.search(r'^#+\s+(?:Section\s+)?\d+\.\d+', header, re.IGNORECASE):
                break
            matching_text.append(f"{header}\n{content}")
            
    if matching_text:
        return "\n\n".join(matching_text)
    
    return ch_text

def generate_chapter_expansion_document(chapter_number: int, section_filter: str = None, overwrite: bool = False) -> str:
    """
    Agent Tool: Generates a deep, unconstrained Bronze+/Silver Chapter Expansion Document.
    Takes the chapter's vector of knowledge destruction (or a specific section) and expands it into an 
    exhaustive, thesis-driven document that maps Fleet Glossary terms, anticipates institutional defenses, 
    and applies the vector to real-world infrastructure events NOT present in the raw manuscript text.
    Saves to manuscript/chapter_expansions/ch{num:02d}_expansion.md (or ch{num:02d}_sec{filter}_expansion.md).
    """
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ch_slug = f"ch{chapter_number:02d}"
        exp_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
        os.makedirs(exp_dir, exist_ok=True)
        if section_filter:
            sec_slug = re.sub(r'[^a-zA-Z0-9\.]', '', str(section_filter))
            exp_path = os.path.join(exp_dir, f"{ch_slug}_sec{sec_slug}_expansion.md")
        else:
            exp_path = os.path.join(exp_dir, f"{ch_slug}_expansion.md")

        if os.path.exists(exp_path) and not overwrite:
            return f"[SKIP] Expansion file already exists at: {exp_path}"

        ch_text = _read_chapter_silver_text(chapter_number)
        if section_filter:
            ch_text = _filter_section_text(ch_text, section_filter)
        learnings_dict = _load_chapter_learnings()
        ch_learning = learnings_dict.get(str(chapter_number), {}).get("thesis_insight", "")
        prior_keys = [k for k in learnings_dict.keys() if int(k) < chapter_number]
        prior_cumulative_md = ""
        if prior_keys:
            prior_cumulative_md = "CUMULATIVE THESIS PROGRESSION (Prior Chapter Learnings):\n"
            for k in sorted(prior_keys, key=lambda x: int(x)):
                item = learnings_dict[k]
                prior_cumulative_md += f"- Chapter {item['chapter_number']}: {item['thesis_insight']}\n"
        else:
            prior_cumulative_md = "CUMULATIVE THESIS PROGRESSION: No prior chapter learnings (First Chapter in Sequence).\n"

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        # Fetch Fleet Glossary definitions
        glossary_text = ""
        try:
            conn = _get_cargo_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT term, definition FROM cargo.system_glossary ORDER BY term;")
                rows = cur.fetchall()
                glossary_text = "\n".join([f"- {r[0]}: {r[1]}" for r in rows])
                cur.close()
                conn.close()
        except Exception as ge:
            glossary_text = f"Glossary fetch warning: {ge}"

        client = genai.Client(api_key=api_key)

        scope_heading = f"Section {section_filter}" if section_filter else f"Chapter {chapter_number}"
        scope_instruction = ""
        reduce_context = ""
        if section_filter and ("1.1" in str(section_filter) or "vignette" in str(section_filter).lower()):
            red_v1_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "chapter_reduces", f"ch{chapter_number:02d}_reduce_v1_forensic_matrix.md"))
            if os.path.exists(red_v1_path):
                with open(red_v1_path, "r", encoding="utf-8") as rf:
                    reduce_context = f"\n\nCHAPTER {chapter_number} MASTER REDUCE MAP (FORENSIC MATRIX):\n" + rf.read() + "\n\n"

            scope_instruction = f"""
SPECIAL VIGNETTE HANDLING DIRECTIVE:
Section {section_filter} is a NARRATIVE VIGNETTE (an illustrative case study / story like Camp Mystic, Paul Yura, Bryton Shang), NOT the core thesis vector itself.
You have FULL COGNITIVE DISCRETION to format this expansion in whatever structural style is most effective (e.g. Narrative Explainer, Contextual Summary, Historical Backgrounder, or Forensic Case Study Bridge).
You must anchor this story directly to the chapter's core thesis and the MASTER REDUCE MAP provided below, showing how the human tragedy of Camp Mystic illustrates the mathematical and philosophical vectors of knowledge destruction (Jelinek's Statistical Turn, Perplexity, Texture Hacking, and Transactional Truth).
"""
        elif section_filter:
            scope_instruction = f"""
CRITICAL SCOPE REQUIREMENT:
You are generating an expansion ONLY for Section {section_filter}. 
Do NOT include or expand upon premises, case studies, or quotes from other sections of Chapter {chapter_number} (e.g., do not bring in Sokal, Bulhak, Schwartz, or Caligula unless they are explicitly in Section {section_filter}).
Focus 100% of your forensic analysis, glossary mappings, and real-world extrapolations on the specific vector defined in Section {section_filter}.
"""

        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine and Master Philologist for 'The End of Knowing'.
Your task is to generate a comprehensive, deep-dive EXPANSION DOCUMENT (Bronze+ / Silver tier) for {scope_heading}.

{scope_instruction}

{reduce_context}

{prior_cumulative_md}

CHAPTER CORE INSIGHT RECORDED FOR THIS CHAPTER:
{ch_learning}

FLEET GLOSSARY TERMS AVAILABLE:
{glossary_text}

TARGET MANUSCRIPT TEXT (SECTION {section_filter if section_filter else 'ALL'}):
{ch_text}

EXPANSION INSTRUCTIONS:
Do not merely summarize the text. You must take the specific Vector of Knowledge Destruction in this text seriously and EXPAND it into a deep analytical document. 
Explicitly bring in real-world infrastructure failures, AI industry developments, legal/policy traps, and institutional dynamics THAT ARE NOT EVEN IN THE SOURCE TEXT, but represent direct real-world manifestations of this specific vector's core thesis.

Structure your markdown output with these 6 clear sections:

# {scope_heading} Expansion: [Title]
*Bronze+ / Silver Deep Thesis Expansion for Bilgeladle Knowledge Engine*

## 1. Core Vector of Knowledge Destruction
Elaborate deeply on the specific epistemological suicide pact, institutional lie, or architectural failure defined in this section/chapter text. Explain why this vector represents a point of no return for truth and knowing.

## 2. Forensic Analysis of Key Manuscript Premises
Examine the foundational arguments, anchor quotes, and intellectual lineage from the chapter text. Unpack their philosophical and technical weight.

## 3. Fleet Glossary Intersections & Conceptual Frameworks
Map the chapter's core vector to specific Fleet Glossary terms (e.g. Behaviorist Delusion, Active Fraud of Context, Plausibility Engine). Define how this chapter enriches or extends those terms.

## 4. Real-World Extrapolations & External Applications (Beyond Manuscript Text)
Apply this chapter's vector of destruction to modern events, AI announcements, regulatory failures, or corporate practices NOT explicitly mentioned in the raw chapter text. Show how this chapter's thesis operates as a predictive lens for modern events.

## 5. Anticipated Institutional Defenses & Forensic Counter-Critiques
Anticipate how legacy institutions (newsrooms, tech companies, regulators) will defend their practices. Provide Bilgeladle's unprompted, forensic counter-critique exposing their self-defense mechanisms.

## 6. Downstream Guidance for Scallywag & Fleet Agents
Provide clear instructions for how downstream agents (e.g., Scallywag, Cutlass) should use this chapter's vector when evaluating incoming assets, writing newsletters, or crafting public-facing commentary.
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt
        )

        expansion_text = response.text.strip()

        # Save to file
        exp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "chapter_expansions"))
        os.makedirs(exp_dir, exist_ok=True)
        if section_filter:
            sec_slug = re.sub(r'[^a-zA-Z0-9\.]', '', str(section_filter))
            exp_path = os.path.join(exp_dir, f"ch{chapter_number:02d}_sec{sec_slug}_expansion.md")
        else:
            exp_path = os.path.join(exp_dir, f"ch{chapter_number:02d}_expansion.md")

        with open(exp_path, "w", encoding="utf-8") as f:
            f.write(expansion_text)

        return f"[SUCCESS] Chapter {chapter_number} Expansion Document written to: {exp_path}"

    except Exception as e:
        return f"[ERROR] generate_chapter_expansion_document failed: {str(e)}"

def generate_chapter_synthesis_essay(chapter_number: int) -> str:
    """
    Agent Tool: Generates an author-editable Chapter Synthesis Essay.
    Synthesizes structural analysis, intellectual roots, heroes/villains, and Chain of Ruin vectors.
    Saves directly to local disk at manuscript/chapter_essays/ch{num:02d}_synthesis_essay.md for author review.
    """
    try:
        analysis_raw = perform_chapter_structural_analysis(chapter_number)
        if analysis_raw.startswith("[ERROR]"):
            return analysis_raw

        analysis = json.loads(analysis_raw)
        ch_text = _read_chapter_silver_text(chapter_number)

        # Extract title from ch_text
        title_match = re.search(r'#+\s*(?:Chapter\s+\d+:?\s*)?(.*)', ch_text)
        ch_title = title_match.group(1).strip() if title_match else f"Chapter {chapter_number}"

        essay_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "chapter_essays"))
        os.makedirs(essay_dir, exist_ok=True)
        essay_path = os.path.join(essay_dir, f"ch{chapter_number:02d}_synthesis_essay.md")

        vignette = analysis.get("vignette", "N/A")
        anchor_quotes = analysis.get("anchor_quotes", [])
        chain = analysis.get("chain_of_ruin", {})
        hv = analysis.get("heroes_and_villains", {})

        quotes_md = ""
        for q in anchor_quotes:
            if isinstance(q, dict):
                quotes_md += f"- **{q.get('author', 'Author')}**: \"{q.get('quote', q.get('summary', ''))}\"\n  - *Intellectual Lineage & Choice Rationale*: {q.get('intellectual_roots', q.get('rationale', ''))}\n"
            else:
                quotes_md += f"- {q}\n"

        heroes_md = ""
        for h in hv.get("heroes", []):
            if isinstance(h, dict):
                heroes_md += f"- **{h.get('name', 'Hero')}**: {h.get('role', h.get('description', ''))}\n"
            else:
                heroes_md += f"- {h}\n"

        villains_md = ""
        for v in hv.get("villains", []):
            if isinstance(v, dict):
                villains_md += f"- **{v.get('name', 'Villain')}**: {v.get('role', v.get('description', ''))}\n"
            else:
                villains_md += f"- {v}\n"

        essay_content = f"""# Synthesis Essay: Chapter {chapter_number} — {ch_title}
*Author-Editable Cognitive Compass for Bilgeladle (Thesis Alignment Engine)*

---

## 1. Narrative Vignette & Case Study
{vignette}

---

## 2. Anchor Quotes & Intellectual Lineage
{quotes_md}

---

## 3. The Chain of Ruin Vector Analysis
- **Stage 1: Pre-existing Decay**: {chain.get('pre_existing_decay', 'N/A')}
- **Stage 2: Technological Catalyst**: {chain.get('technological_catalyst', 'N/A')}
- **Stage 3: Proactive Negligence**: {chain.get('proactive_negligence', 'N/A')}

---

## 4. Heroes and Villains Ledger

### 🛡️ Heroes of Ground-Truth & Provenance
{heroes_md}

### ⚠️ Agents of Epistemic Collapse & Active Ignorance
{villains_md}

---

## 5. Chapter Core Stance & Thesis Alignment
This chapter operates as an architectural forensic audit within *The End of Knowing*. Bilgeladle uses this synthesis essay as her primary reference to route incoming assets, evaluate external claims against the core thesis, and preserve the epistemic lineage of ground-truth.
"""

        with open(essay_path, "w", encoding="utf-8") as f:
            f.write(essay_content)

        return f"[SUCCESS] Chapter {chapter_number} Synthesis Essay written to local file: {essay_path}"

    except Exception as e:
        return f"[ERROR] generate_chapter_synthesis_essay failed: {str(e)}"

def evaluate_asset_alignment(asset_text: str) -> str:
    """
    Agent Tool: Implements the Map-Expand-Reduce asset routing pattern.
    Maps incoming asset against pgVector ship.letters_of_marque, expands against chapter essays
    and glossary, and emits a chapter routing decision with thesis rationale.
    """
    try:
        if not asset_text or len(asset_text.strip()) == 0:
            return "[ERROR] asset_text is required for evaluation."

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        client = genai.Client(api_key=api_key)

        # 1. MAP: Compute embedding for asset text snippet and query ship.letters_of_marque
        embed_resp = client.models.embed_content(
            model="gemini-embedding-001",
            contents=asset_text[:2000],
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        vec_str = str(list(embed_resp.embeddings[0].values))

        conn = _get_cargo_db_connection()
        cursor = conn.cursor()

        # 1. MAP: Compute embedding for asset text snippet and query ship.letters_of_marque
        cursor.execute(
            """
            SELECT chapter_number, section_number, header_title, SUBSTRING(chunk_text FROM 1 FOR 150),
                   1 - (vector_embedding <=> %s::vector) AS similarity
            FROM ship.letters_of_marque
            ORDER BY vector_embedding <=> %s::vector ASC
            LIMIT 5;
            """,
            (vec_str, vec_str)
        )
        vector_matches = cursor.fetchall()

        # Fetch Fleet Glossary terms from cargo.system_glossary
        cursor.execute("SELECT term, definition FROM cargo.system_glossary ORDER BY term;")
        glossary_rows = cursor.fetchall()
        cursor.close()
        conn.close()

        match_summary = ""
        for row in vector_matches:
            match_summary += f"- Chapter {row[0]} (Sec {row[1]} - {row[2]}): Similarity {float(row[4]):.4f} | Snippet: \"{row[3]}...\"\n"

        glossary_summary = ""
        for g_term, g_def in glossary_rows:
            glossary_summary += f"- **{g_term}**: {g_def}\n"

        # 2. EXPAND: Read available local chapter essays and profiles for context
        essay_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "chapter_essays"))
        chapter_essays_summary = ""
        if os.path.exists(essay_dir):
            for fname in sorted(os.listdir(essay_dir)):
                if fname.endswith("_synthesis_essay.md"):
                    with open(os.path.join(essay_dir, fname), "r", encoding="utf-8") as ef:
                        chapter_essays_summary += f"\n--- {fname} ---\n{ef.read()[:1500]}\n"

        # Also fallback to local wiki glossary file if DB returned empty
        if not glossary_summary:
            wiki_glossary_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "local_wiki", "fleet_glossary_alphabetical_bilgeladle.md"))
            if os.path.exists(wiki_glossary_file):
                with open(wiki_glossary_file, "r", encoding="utf-8") as gf:
                    glossary_summary = gf.read()[:4000]

        # 3. REDUCE: LLM reasoning turn to decide chapter placement, temporal provenance, and retrospective critique
        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine for 'The End of Knowing'.
- MANUSCRIPT TIMELINE CONTEXT: The core manuscript draft corpus was frozen in January 2026.
- TEMPORAL PROVENANCE AWARENESS: In a fast-moving domain like AI and information collapse, publication dates and event sequences are critical. Always compare the asset's publication date against the manuscript freeze date (January 2026) and event date.
- FLEET GLOSSARY MANDATE: You must explicitly map the asset to the project's Fleet Glossary terms.
- UNPROMPTED RETROSPECTIVE CRITIQUE: You do not sycophantically match terms. Ask unprompted: "This is a follow-up/anniversary piece related to something I know about. Has the passage of time yielded genuine structural insight, or is the source merely recycling legacy newsroom tropes and institutional self-defense while remaining blind to the core epistemic collapse?"

INCOMING ASSET:
{asset_text[:4000]}

PGVECTOR SEMANTIC SEARCH MATCHES (MAP):
{match_summary}

FLEET GLOSSARY TERMS & DEFINITIONS (EXPAND):
{glossary_summary[:4000] if glossary_summary else '[No glossary loaded]'}

CHAPTER SYNTHESIS ESSAYS (EXPAND):
{chapter_essays_summary if chapter_essays_summary else '[No local essays generated yet - rely on vector matches]'}

Format your response in Markdown:

### 1. Chapter Routing Recommendation
State the exact chapter (e.g. Chapter 1: Is True / Sounds True) where this asset belongs.

### 2. Epistemic Domain Vector & Temporal Provenance
Define the specific vector of ruin illustrated. Analyze the publication date and event timeline relative to the manuscript's January 2026 draft freeze.

### 3. Glossary Term Mapping
Extract and map the EXACT terms from the Fleet Glossary (e.g., Tacit Knowledge, Active Fraud of Context, Transactional Truth) that this asset illustrates. Quote the asset text to prove the mapping.

### 4. Thesis Justification & Evidence Mapping
Explain precisely WHY this asset belongs in that chapter. Quote key parts of the asset and map them to manuscript themes, anchor quotes, and heroes/villains.

### 5. Unprompted Retrospective Critique
Evaluate the asset's critical value. Did the author/outlet gain genuine structural insight with the passage of time, or are they recycling legacy newsroom tropes (e.g., blaming 'unexpected weather' or 'bureaucratic delay') while remaining blind to the technological/epistemic collapse that caused it?

### 6. The Missing Link
What vital ground-truth provenance or context does this asset deliberately omit that the manuscript must provide?
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt
        )

        evaluation_text = response.text.strip()

        # Derive a clean slug for local_wiki output
        slug_match = re.search(r'https?://[^/]+/(?:[^/]+/)*([^/?#\n]+)', asset_text)
        if slug_match:
            raw_slug = slug_match.group(1).replace('.html', '').replace('.php', '')
        else:
            first_line = asset_text.split('\n')[0][:50]
            raw_slug = first_line

        raw_slug = re.sub(r'[^a-zA-Z0-9_\-]+', '-', raw_slug).strip('-').lower()
        asset_slug = raw_slug if raw_slug else f"asset_{int(time.time())}"
        wiki_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "local_wiki"))
        os.makedirs(wiki_dir, exist_ok=True)
        wiki_file_path = os.path.join(wiki_dir, f"{asset_slug}_bilgeladle.md")

        # Extract target chapter number from response for frontmatter
        ch_match = re.search(r'Chapter\s+(\d+)', evaluation_text, re.IGNORECASE)
        target_ch = ch_match.group(1) if ch_match else "1"

        yaml_header = f"""---
artifact_id: {asset_slug}
agent: bilgeladle
skill: map_expand_reduce_routing
target_chapter: {target_ch}
timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}
manuscript_freeze_date: 2026-01
---

# Bilgeladle Asset Evaluation: "{asset_slug}"

{evaluation_text}
"""

        with open(wiki_file_path, "w", encoding="utf-8") as wf:
            wf.write(yaml_header)

        return f"{evaluation_text}\n\n---\n*Saved Bilgeladle Asset Assessment artifact to: [local_wiki/{asset_slug}_bilgeladle.md](file:///{wiki_file_path.replace(os.sep, '/')})*"

    except Exception as e:
        return f"[ERROR] evaluate_asset_alignment failed: {str(e)}"

def _load_all_chapter_section_expansions(chapter_number: int) -> tuple[str, int]:
    """Helper: Reads all generated section expansion files for a given chapter from disk."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    ch_slug = f"ch{chapter_number:02d}"
    
    # 1. Check canonical ship/silver/chapters/chXX/
    silver_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
    if os.path.exists(silver_dir):
        files = sorted([f for f in os.listdir(silver_dir) if f.startswith(f"{ch_slug}_sec") and f.endswith("_expansion.md")])
        if files:
            combined_text = []
            for fname in files:
                fpath = os.path.join(silver_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    combined_text.append(f"=== EXPANSION FILE: {fname} ===\n" + f.read())
            return "\n\n".join(combined_text), len(files)

    # 2. Check legacy manuscript/chapter_expansions fallback
    exp_dir = os.path.join(base_dir, "manuscript", "chapter_expansions")
    if os.path.exists(exp_dir):
        prefix = f"ch{chapter_number:02d}_sec"
        files = sorted([f for f in os.listdir(exp_dir) if f.startswith(prefix) and f.endswith(".md")])
        if files:
            combined_text = []
            for fname in files:
                fpath = os.path.join(exp_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    combined_text.append(f"=== EXPANSION FILE: {fname} ===\n" + f.read())
            return "\n\n".join(combined_text), len(files)

    return "", 0

def generate_chapter_reduce_v1_forensic_matrix(chapter_number: int) -> str:
    """
    Reduce Tool (Approach 1): The Forensic Taxonomy & Chain-of-Ruin Matrix.
    Synthesizes section expansions into a forensic, multi-matrix audit document.
    Saves to manuscript/chapter_reduces/ch{num:02d}_reduce_v1_forensic_matrix.md.
    """
    try:
        expansions_text, count = _load_all_chapter_section_expansions(chapter_number)
        if not expansions_text:
            return f"[ERROR] No section expansions found for Chapter {chapter_number} in manuscript/chapter_expansions/."

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine and Master Philologist for 'The End of Knowing'.
Synthesize the following {count} Section Expansion Documents for Chapter {chapter_number} into an exhaustive FORENSIC TAXONOMY & CHAIN-OF-RUIN MATRIX (Approach 1 Reduce Document).

SECTION EXPANSIONS INPUT:
{expansions_text}

REDUCE INSTRUCTIONS (APPROACH 1: FORENSIC MATRIX):
Produce a dense, highly structured forensic reduction formatted in GitHub-flavored markdown:

# Chapter {chapter_number} Reduce Map: Forensic Taxonomy & Chain-of-Ruin Matrix (Approach 1)
*Dense Forensic Synthesis for Bilgeladle Knowledge Engine (Built from {count} Section Expansions)*

## 1. Complete 3-Stage Chain of Ruin Mapping
Explicitly map the entire chapter across the 3 stages of destruction:
- Stage 1: Pre-existing Decay (institutional/human erosion prior to technology)
- Stage 2: Technological Catalyst (the specific mechanism accelerating the collapse)
- Stage 3: Proactive Negligence (the conscious choice to abandon verification and ground truth)

## 2. Epistemic Taxonomy & Vector Matrix
A structured table mapping each section to its:
| Section | Vector of Destruction | Epistemic Fallacy / Loss Function | Ground-Truth Anchor / Remedy |

## 3. Master Intellectual Lineage Table
Table of all key authors/sources cited (e.g. Jelinek, Sokal, Bulhak, Chomsky, LeCun, Epictetus):
| Author / Source | Original Work / Citation | Core Thesis Function in Manuscript |

## 4. Real-World Infrastructure & Historical Proofs
Audit of all real-world case studies and infrastructure failures (Watson, Camp Mystic, Sokal, SCIgen, Steven Schwartz, AI Overviews, Devin AI).

## 5. Downstream Agent Enforcement Matrix (Scallywag & Cutlass Rules)
Direct rules for how Cutlass must classify incoming assets and how Scallywag must frame opinion commentary using this chapter's vectors.
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ch_slug = f"ch{chapter_number:02d}"
        red_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
        os.makedirs(red_dir, exist_ok=True)
        red_path = os.path.join(red_dir, f"ch{chapter_number:02d}_reduce_v1_forensic_matrix.md")

        with open(red_path, "w", encoding="utf-8") as f:
            f.write(response.text.strip())

        return f"[SUCCESS] Chapter {chapter_number} Reduce V1 (Forensic Matrix) written to: {red_path}"

    except Exception as e:
        return f"[ERROR] generate_chapter_reduce_v1_forensic_matrix failed: {str(e)}"

def generate_chapter_reduce_v2_argumentative_arc(chapter_number: int) -> str:
    """
    Reduce Tool (Approach 2): The Progressive Thesis Synthesis (Narrative & Philosophical Arc).
    Synthesizes section expansions into a continuous argumentative synthesis tracing the chapter's building thesis.
    Saves to manuscript/chapter_reduces/ch{num:02d}_reduce_v2_argumentative_arc.md.
    """
    try:
        expansions_text, count = _load_all_chapter_section_expansions(chapter_number)
        if not expansions_text:
            return f"[ERROR] No section expansions found for Chapter {chapter_number} in manuscript/chapter_expansions/."

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine and Master Philologist for 'The End of Knowing'.
Synthesize the following {count} Section Expansion Documents for Chapter {chapter_number} into a continuous PROGRESSIVE THESIS SYNTHESIS (Approach 2 Reduce Document).

SECTION EXPANSIONS INPUT:
{expansions_text}

REDUCE INSTRUCTIONS (APPROACH 2: ARGUMENTATIVE ARC):
Produce a deeply analytical, progressive synthesis that traces the logical domino effect of the chapter:

# Chapter {chapter_number} Reduce Map: Progressive Thesis Synthesis (Approach 2)
*Argumentative Arc Synthesis for Bilgeladle Knowledge Engine (Built from {count} Section Expansions)*

## 1. The Domino Arc of Destruction
Trace the step-by-step logical progression from section to section. Show how the departure in Section 1.2 triggers the vulnerabilities in 1.3/1.4, accelerating into the feedback loops of 1.5, and culminating in the institutional failures of 1.6/1.12.

## 2. Conceptual Cascades & Glossary Intersections
Show how key terms flow into one another (e.g. Statistical Turn ──► Perplexity ──► Texture Hacking ──► Computational Truthiness ──► Caligula Loop ──► Transactional Truth).

## 3. The Philosophical Core & Diagnostic Convergence
Synthesize the philosophical critiques (Chomsky, LeCun, Epictetus, Rand) into a unified argument explaining why probabilistic engines cannot know.

## 4. The Epistemological Verdict
The definitive 3-paragraph summary of what Chapter {chapter_number} proves about the collapse of knowledge systems.
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ch_slug = f"ch{chapter_number:02d}"
        red_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
        os.makedirs(red_dir, exist_ok=True)
        red_path = os.path.join(red_dir, f"ch{chapter_number:02d}_reduce_v2_argumentative_arc.md")

        with open(red_path, "w", encoding="utf-8") as f:
            f.write(response.text.strip())

        return f"[SUCCESS] Chapter {chapter_number} Reduce V2 (Argumentative Arc) written to: {red_path}"

    except Exception as e:
        return f"[ERROR] generate_chapter_reduce_v2_argumentative_arc failed: {str(e)}"

def generate_chapter_reduce_v3_operational_map(chapter_number: int) -> str:
    """
    Reduce Tool (Approach 3): The Operational Fleet Decision Engine (Prompt Injection Ready).
    Synthesizes section expansions into an ultra-dense, token-efficient decision map for agent context injection.
    Saves to manuscript/chapter_reduces/ch{num:02d}_reduce_v3_operational_map.md.
    """
    try:
        expansions_text, count = _load_all_chapter_section_expansions(chapter_number)
        if not expansions_text:
            return f"[ERROR] No section expansions found for Chapter {chapter_number} in manuscript/chapter_expansions/."

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key missing."

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are BILGELADLE, Thesis Alignment Engine and Master Philologist for 'The End of Knowing'.
Synthesize the following {count} Section Expansion Documents for Chapter {chapter_number} into an ULTRA-DENSE OPERATIONAL FLEET DECISION ENGINE (Approach 3 Reduce Document).

SECTION EXPANSIONS INPUT:
{expansions_text}

REDUCE INSTRUCTIONS (APPROACH 3: OPERATIONAL DECISION ENGINE):
Produce an ultra-compact, high-density decision engine designed for low-token prompt injection during live agent runs:

# Chapter {chapter_number} Reduce Map: Operational Fleet Decision Engine (Approach 3)
*Prompt-Injection Optimized Map for Bilgeladle, Scallywag & Cutlass (Built from {count} Section Expansions)*

## 1. Ultra-Dense Vector Lookup Table
| Sec | Core Vector | Key Indicators / Trigger Phrases | Matched Glossary Terms |

## 2. Institutional Defense vs. Forensic Counter-Matrix (Trial Table)
| Institutional Defense | Bilgeladle Forensic Counter-Critique |

## 3. High-Speed Asset Matching Rules (If-Then Routing)
- IF asset discusses X ──► MAP TO Sec Y ──► APPLY RULE Z

## 4. Compressed Core Memory Payload (~300 Words)
A single, highly compressed 300-word paragraph encapsulating the entire chapter's thesis for instant system-prompt context injection.
"""

        response = client.models.generate_content(
            model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
            contents=prompt
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ch_slug = f"ch{chapter_number:02d}"
        red_dir = os.path.join(base_dir, "ship", "silver", "chapters", ch_slug)
        os.makedirs(red_dir, exist_ok=True)
        red_path = os.path.join(red_dir, f"ch{chapter_number:02d}_reduce_v3_operational_map.md")

        with open(red_path, "w", encoding="utf-8") as f:
            f.write(response.text.strip())

        return f"[SUCCESS] Chapter {chapter_number} Reduce V3 (Operational Map) written to: {red_path}"

    except Exception as e:
        return f"[ERROR] generate_chapter_reduce_v3_operational_map failed: {str(e)}"
