import os
import sys
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def run_isolated_search(query: str):
    """Executes a completely stateless, first-party web search pass aligned to Landlubber's profile."""
    try:
        # 1. Parse Landlubber's XML Profile to enforce system prompt identity matching
        xml_path = "src/react_agent/agents/landlubber/landlubber.xml"
        system_instruction = "You are a precise information retrieval agent."
        
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            mandate_elem = root.find(".//core_mandate")
            if mandate_elem is not None:
                system_instruction = "".join(mandate_elem.itertext()).strip()

        # 2. Boot the ungrounded native developer client
        client = genai.Client()
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        
        # 3. Fire a single-pass turn directly against the live search index
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=query,
            config=config
        )
        
        if response.text:
            print(response.text)
        else:
            print("[NOTICE] Landlubber returned an empty web response.")
            
    except Exception as e:
        print(f"[RUNNER EXCEPTION] Landlubber runtime fault: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Missing target search query operand.", file=sys.stderr)
        sys.exit(1)
        
    search_query = sys.argv[1]
    run_isolated_search(search_query)