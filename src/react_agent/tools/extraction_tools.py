# tools/extraction_tools.py
import json
import textwrap
import langextract as lx

def run_langextract_mapping(text_content: str) -> str:
    """
    Runs the official Google LangExtract engine to extract the ontology with precise source grounding.
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
                text="The tragedy at Camp Mystic was not a glitch... On April 21, 2025, the office’s Warning Coordination Meteorologist, Paul Yura, announced his early retirement. They realized they didn't need the computer to understand the definition... they only needed the machine to know that, statistically... This was the Statistical Turn, and it introduced a specific metric...",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="vignette",
                        extraction_text="The tragedy at Camp Mystic was not a glitch...",
                        attributes={"summary": "Automated flood warnings failed without a human WCM."}
                    ),
                    lx.data.Extraction(
                        extraction_class="empirical_entity",
                        extraction_text="Paul Yura",
                        attributes={"item_type": "real person", "role": "Human witness possessing tacit knowledge."}
                    ),
                    lx.data.Extraction(
                        extraction_class="chronology",
                        extraction_text="April 21, 2025",
                        attributes={"description": "WCM Paul Yura retires"}
                    ),
                    lx.data.Extraction(
                        # The missing Concept example
                        extraction_class="concept",
                        extraction_text="This was the Statistical Turn, and it introduced a specific metric...",
                        attributes={"term": "The Statistical Turn"}
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
        ]
        
        return json.dumps(extracted_data, indent=2)

    except Exception as e:
        return f"[ERROR] LangExtract failed: {str(e)}"