"""
NPT Fleet Tools: Semantic Extraction Engine
Architecture: Google LangExtract Native Integration (Grounded Extraction)
"""
import json
import textwrap
import langextract as lx

# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def run_langextract_mapping(text_content: str) -> str:
    """
    Agent Tool: The Strict Ontology Mapper.
    Purpose: Bridges unstructured Bronze text into structured Silver JSON data. 
    It forces the extraction of exact, verbatim concepts, vignettes, and arguments. 
    Critically, it uses LangExtract's `char_interval` check to automatically strip out 
    any LLM hallucinations that do not physically exist in the source text.
    Invoked By: PLANK (The Information Mapper) and BILGELADLE (Thesis Alignment).
    """
    try:
        # 1. Define the overarching extraction instructions
        prompt = textwrap.dedent("""\
            Extract all structural elements from the manuscript chapter:
            - vignettes: A physical event demonstrating consequences of technological abstraction.
            - concepts: Epistemic or technological terms defined in the text.
            - chronology: Specific events and dates.
            - arguments: Specific claims about the destruction of the knowledge system.
            - empirical_entities: People, technologies, or institutions mentioned.
            
            Use exact text for all extractions. Do not paraphrase.
            Provide meaningful attributes (like summary, date, role, or item_type) to add context.
        """)
        
        # 2. Provide a strict ExampleData template to guide the model's output schema
        examples = [
            lx.data.ExampleData(
                text="The tragedy at Camp Mystic was not a glitch... On April 21, 2025, the office’s Warning Coordination Meteorologist, Paul Yura, announced his early retirement. They realized they didn't need the computer to understand the definition... they only needed the machine to know that, statistically...",
                extractions=[
                    lx.data.Extraction(
                        # The missing Vignette example
                        extraction_class="vignette",
                        extraction_text="The tragedy at Camp Mystic was not a glitch...",
                        attributes={"summary": "Camp Mystic Tragedy"}
                    ),
                    lx.data.Extraction(
                        # The missing Chronology example
                        extraction_class="chronology",
                        extraction_text="On April 21, 2025",
                        attributes={"date": "2025-04-21"}
                    ),
                    lx.data.Extraction(
                        # The missing Empirical Entity example
                        extraction_class="empirical_entities",
                        extraction_text="Warning Coordination Meteorologist, Paul Yura",
                        attributes={"role": "Meteorologist"}
                    ),
                    lx.data.Extraction(
                        # The missing Argument example
                        extraction_class="argument",
                        extraction_text="They realized they didn't need the computer to understand the definition... they only needed the machine to know that, statistically...",
                        attributes={"claim": "The Statistical Turn abandoned verifiable logic for probability."}
                    )
                ]
            )
        ]
        
        # 3. Execute LangExtract (it handles the chunking, parallelization, and grounding natively)
        result = lx.extract(
            text_or_documents=text_content,
            prompt_description=prompt,
            examples=examples,
            model_id="gemini-3.5-flash", 
        )
        
        # 4. Filter for grounded results (char_interval exists) and format as JSON
        # The 'if e.char_interval' check automatically strips out any LLM hallucinations 
        # that don't physically exist in your manuscript text.
        extracted_data = [
            {
                "category": e.extraction_class,
                "source_quote": e.extraction_text,
                "attributes": e.attributes,
            }
            for e in result.extractions
            if e.char_interval  # THE FIX: Absolute grounding enforcement
        ]
        
        return json.dumps(extracted_data, indent=2)

    except Exception as e:
        return f"[ERROR] LangExtract failed: {str(e)}"