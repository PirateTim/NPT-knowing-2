"""
NPT Fleet Tools: Semantic Extraction Engine & Knowledge Graph Synthesizer
Architecture: Google LangExtract Native Integration (Grounded Extraction -> Graph Primitives)

Design Philosophy:
1. High Signal-to-Noise Ratio: Filters out web scraper noise, copyright footers, and publisher brand lists.
2. Neo4j & Knowledge Graph 1:1 Mapping: Formats output as unique canonical 'nodes' and directed 'edges' carrying verbatim source_quotes.
3. Non-Blocking Downstream Auditing: Flags unverified entities (e.g. hosts, pundits, media outlets) with `requires_downstream_audit` and specific `audit_question` parameters so Cutlass isn't distracted by web searches during the initial extraction pass, while allowing downstream agents to perform targeted verification later.
"""
import os
import json
import textwrap
import datetime
from dotenv import load_dotenv
import langextract as lx

# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def run_langextract_mapping(text_content: str) -> str:
    """
    Agent Tool: The Strict Ontology & Knowledge Graph Mapper.
    
    Purpose:
    Bridges unstructured Bronze text into structured Silver JSON data formatted as Graph Primitives 
    (Nodes, Edges, Arguments, Vignettes, Chronology) for Neo4j and Knowledge Graph expansion.
    
    Key Engineering Features:
    1. Verbatim Grounding: Enforces LangExtract's `char_interval` check to eliminate LLM hallucinations.
    2. Boilerplate Stripping: Omits publisher footers, copyright blocks, and redundant brand footers.
    3. Entity Consolidation: Deduplicates repeated entity mentions into single canonical node objects with accumulated source quotes.
    4. Downstream Audit Flags: Labels unverified figures (e.g., podcast hosts) for deferred research agents.

    Invoked By: CUTLASS (Epistemic Auditor), PLANK (Ontology Mapper), and BILGELADLE (Thesis Alignment).
    """
    try:
        # Load environment configuration (.env) for API credentials
        load_dotenv()
        
        # 1. Define overarching extraction prompt for Google LangExtract
        # We explicitly instruct the model to ignore generic site chrome/footers and prioritize structural claims and entities.
        prompt = textwrap.dedent("""\
            Perform a high-signal Knowledge Graph extraction on the text.
            Do NOT extract site footers, copyright boilerplate, publisher brand lists, or repetitive shallow mentions.
            
            Extract the following structural categories:
            - empirical_entities: Canonical people, institutions, platforms, podcasts, or technologies.
              Attributes: 
                - name: Canonical entity name.
                - entity_type: Person, Organization, Platform, Podcast, Technology.
                - institutional_context: Institutional role, affiliation, or host context.
                - requires_downstream_audit: "true" if entity's background, credibility, or reach needs downstream external verification; "false" otherwise.
                - audit_question: Specific research question if downstream audit is required (e.g. "What is the reach and sponsorship model of Lenny's Podcast?").
            - arguments: Major claims about epistemic decay, labor degradation, or knowledge destruction.
              Attributes:
                - claim: High-level claim summary.
            - vignettes: Concrete events demonstrating consequences of technological abstraction or corporate downsizing.
              Attributes:
                - summary: Vignette event summary.
            - relationships: Directed relationships connecting two entities or an entity to a claim/vignette.
              Attributes:
                - source_entity: Name of the origin entity.
                - target_entity: Name of the target entity or claim.
                - relationship_type: GUEST_ON, ELIMINATED_ROLES, FUNDED_BY, PUBLISHED_BY, REPLACED_WITH, ADVOCATES.
            - concepts: Epistemic or technical terms defined in the text.
            - chronology: Specific dates or temporal markers.
              Attributes:
                - date: Formatted date string.
            
            Extract exact quotes for source text. Prioritize high-signal structural nodes and relationships.
        """)
        
        # 2. Provide a strict ExampleData template guiding the Gemini model's structural output schema
        examples = [
            lx.data.ExampleData(
                text="On April 21, 2025, Head of Instagram Adam Mosseri appeared on Lenny's Podcast hosted by Lenny Rachitsky to announce that Instagram was shutting down silly AI projects and replacing specialized data scientists with generalist pods...",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="chronology",
                        extraction_text="April 21, 2025",
                        attributes={"date": "2025-04-21"}
                    ),
                    lx.data.Extraction(
                        extraction_class="empirical_entities",
                        extraction_text="Adam Mosseri",
                        attributes={
                            "name": "Adam Mosseri",
                            "entity_type": "Person",
                            "institutional_context": "Head of Instagram / Meta Executive",
                            "requires_downstream_audit": "false"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="empirical_entities",
                        extraction_text="Lenny Rachitsky",
                        attributes={
                            "name": "Lenny Rachitsky",
                            "entity_type": "Person",
                            "institutional_context": "Host of Lenny's Podcast",
                            "requires_downstream_audit": "true",
                            "audit_question": "What is the audience reach, sponsorship model, and journalistic independence of Lenny's Podcast?"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="empirical_entities",
                        extraction_text="Instagram",
                        attributes={
                            "name": "Instagram",
                            "entity_type": "Platform",
                            "institutional_context": "Division of Meta",
                            "requires_downstream_audit": "false"
                        }
                    ),
                    lx.data.Extraction(
                        extraction_class="vignette",
                        extraction_text="Instagram was shutting down silly AI projects and replacing specialized data scientists with generalist pods",
                        attributes={"summary": "Instagram AI downsizing and team restructuring"}
                    ),
                    lx.data.Extraction(
                        extraction_class="relationships",
                        extraction_text="Adam Mosseri appeared on Lenny's Podcast hosted by Lenny Rachitsky",
                        attributes={
                            "source_entity": "Adam Mosseri",
                            "target_entity": "Lenny Rachitsky",
                            "relationship_type": "GUEST_ON"
                        }
                    )
                ]
            )
        ]
        
        # 3. Resolve Gemini API Key from active environment variables
        api_key = os.getenv("LANGEXTRACT_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # 4. Execute LangExtract (handles text chunking, parallelization, and grounding alignment natively)
        result = lx.extract(
            text_or_documents=text_content,
            prompt_description=prompt,
            examples=examples,
            model_id="gemini-3.5-flash",
            api_key=api_key
        )
        
        # 5. Filter grounded results & strip known publisher site footer boilerplates
        # Terms like 'Axel Springer' or 'Henry Blodget' are common web scraper noise from news page footers.
        boilerplate_terms = {"axel springer", "henry blodget", "markets insider", "terms of service", "copyright", "privacy policy"}
        
        raw_extractions = []
        for e in result.extractions:
            # Grounding check: char_interval ensures the quote physically exists in the text
            if not e.char_interval:
                continue
            quote_lower = e.extraction_text.strip().lower()
            if any(b in quote_lower for b in boilerplate_terms):
                continue
            raw_extractions.append(e)

        # 6. Post-process extractions into Graph Primitives (Nodes & Edges) to prevent Neo4j node fragmentation
        nodes_dict = {}
        edges_list = []
        arguments_list = []
        vignettes_list = []
        chronology_list = []
        concepts_list = []

        for e in raw_extractions:
            cat = e.extraction_class
            text_quote = e.extraction_text.strip()
            attrs = e.attributes or {}

            # Process Canonical Entity Nodes (Deduplicated by normalized Entity ID)
            if cat == "empirical_entities":
                node_name = attrs.get("name") or text_quote
                node_id = f"entity_{node_name.lower().replace(' ', '_')}"
                
                if node_id not in nodes_dict:
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "type": "Entity",
                        "category": attrs.get("entity_type", "Entity"),
                        "name": node_name,
                        "institutional_context": attrs.get("institutional_context", ""),
                        "requires_downstream_audit": str(attrs.get("requires_downstream_audit", "false")).lower() == "true",
                        "audit_question": attrs.get("audit_question", ""),
                        "source_quotes": [text_quote]
                    }
                else:
                    # Accumulate distinct occurrence quotes for provenance tracking
                    if text_quote not in nodes_dict[node_id]["source_quotes"]:
                        nodes_dict[node_id]["source_quotes"].append(text_quote)
                    # Preserve downstream audit flags if present in any extraction pass
                    if attrs.get("audit_question") and not nodes_dict[node_id]["audit_question"]:
                        nodes_dict[node_id]["audit_question"] = attrs.get("audit_question")
                        nodes_dict[node_id]["requires_downstream_audit"] = True

            # Process Directed Graph Edges (Source -> Target with Relationship Type)
            elif cat == "relationships":
                edges_list.append({
                    "source_node": attrs.get("source_entity", ""),
                    "target_node": attrs.get("target_entity", ""),
                    "relationship_type": attrs.get("relationship_type", "RELATED_TO"),
                    "source_quote": text_quote
                })

            # Process Structural Arguments & Core Claims
            elif cat == "argument":
                arguments_list.append({
                    "claim": attrs.get("claim", text_quote),
                    "source_quote": text_quote
                })

            # Process Empirical Vignettes & Case Studies
            elif cat == "vignette":
                vignettes_list.append({
                    "summary": attrs.get("summary", text_quote),
                    "source_quote": text_quote
                })

            # Process Chronological Events
            elif cat == "chronology":
                chronology_list.append({
                    "date": attrs.get("date", text_quote),
                    "source_quote": text_quote
                })

            # Process Epistemic Terms & Concepts
            elif cat == "concepts":
                concepts_list.append({
                    "term": text_quote,
                    "attributes": attrs
                })

        # 7. Assemble final Bronze+ JSON payload with metadata lineage header
        final_payload = {
            "metadata": {
                "extraction_engine": "google-langextract",
                "model": "gemini-3.5-flash",
                "timestamp": datetime.datetime.now().isoformat()
            },
            "nodes": list(nodes_dict.values()),
            "edges": edges_list,
            "arguments": arguments_list,
            "vignettes": vignettes_list,
            "chronology": chronology_list,
            "concepts": concepts_list
        }
        
        return json.dumps(final_payload, indent=2)

    except Exception as e:
        return f"[ERROR] LangExtract failed: {str(e)}"