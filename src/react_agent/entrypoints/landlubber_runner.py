import os
import sys
import datetime
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

def log_landlubber_audit(query, result):
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    file_path = os.path.join(log_dir, "landlubber_interactions.log")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n[{ts}] QUERY -> {query}\n{'='*60}\n{result}\n")

def run_isolated_search(query: str):
    try:
        xml_path = "src/react_agent/agents/landlubber/landlubber.xml"
        system_instruction = "You are a precise information retrieval agent."
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            mandate_elem = root.find(".//core_mandate")
            if mandate_elem is not None:
                system_instruction = "".join(mandate_elem.itertext()).strip()

        client = genai.Client()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=query,
            config=config
        )
        
        result = response.text if response.text else "[NOTICE] Landlubber returned an empty web response."
        
        # Unified Logging and Output
        log_landlubber_audit(query, result)
        print(result)
            
    except Exception as e:
        print(f"[RUNNER EXCEPTION] Landlubber runtime fault: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Missing target search query operand.", file=sys.stderr)
        sys.exit(1)
    run_isolated_search(sys.argv[1])