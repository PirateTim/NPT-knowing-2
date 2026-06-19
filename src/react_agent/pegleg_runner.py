import os
import sys
import json
import datetime
import uuid
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import RDFS, OWL
from urllib.parse import urlparse

# Force path tracing for relative package modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.acquire_content import acquire_content

def run_ingestion_batch(url_list: list):
    """Orchestrates a raw batch list of URLs through the collection tier."""
    manifest = {
        "timestamp": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        "successful_ingestions": [],
        "failed_ingestions": [],
        "specialty_backlog": []
    }
    
    print(f"\n[PEGLEG] Starting execution loop for {len(url_list)} inbound links.")
    print("----------------------------------------------------------------------")
    
    for idx, url in enumerate(url_list, 1):
        url = url.strip()
        if not url:
            continue
            
        print(f"[{idx}/{len(url_list)}] Routing: {url}")
        
        try:
            result = acquire_content(url)
            status = result.get("status")
            
            if status == "cached":
                print(f"  -> [GATEKEEPER] Cache hit. Skipping write.")
                manifest["successful_ingestions"].append(result)
                
            elif status == "completed":
                print(f"  -> [SUCCESS] Stored in bucket at: {result.get('gcp_path')}")
                manifest["successful_ingestions"].append(result)
                
            elif status == "failed":
                if result.get("error") == "SPECIALTY_TOOL_REQUIRED":
                    print(f"  -> [BACKLOG REGISTER] Requires specialty extension: {result.get('requested_tool')}")
                    manifest["specialty_backlog"].append({
                        "url": url,
                        "requested_tool": result.get("requested_tool"),
                        "reason": result.get("reason")
                    })
                else:
                    print(f"  -> [EXTRACTION FAILURE] Both tiers choked. Logging to failure block.")
                    manifest["failed_ingestions"].append({
                        "url": url,
                        "error": result.get("error", "Unknown error")
                    })
                    
        except Exception as runtime_panic:
            print(f"  -> [CRITICAL PANIC] Isolated runtime block exception: {runtime_panic}")
            manifest["failed_ingestions"].append({"url": url, "error": f"Crash: {str(runtime_panic)}"})
            
    summary_path = f"acquisitions/batch_summary_{manifest['timestamp']}.json"
    os.makedirs("acquisitions", exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print("----------------------------------------------------------------------")
    print(f"[PEGLEG COMPLETE] Ingested: {len(manifest['successful_ingestions'])} | "
          f"Failed: {len(manifest['failed_ingestions'])} | "
          f"Specialty Required: {len(manifest['specialty_backlog'])}")
    print(f"[PEGLEG] Operational summary written directly to {summary_path}\n")
    return manifest
# from rdflib import Graph, Literal, RDF, URIRef, Namespace
# from rdflib.namespace import RDFS, OWL

def compile_json_rules_to_turtle():
    """
    Reads Cutlass's flat learned_rules.json file and dynamically compiles
    true semantic graph nodes into our master Turtle (.ttl) ontology file.
    """
    rules_path = "src/react_agent/agents/cutlass/learned_rules.json"
    output_ttl_path = "acquisitions/npt_master_ontology.ttl"
    
    if not os.path.exists(rules_path):
        print("[ONTOLOGY COMPILER] No rules file found yet to compile.")
        return
        
    g = Graph()
    NPT = Namespace("http://schema.npt.cloud/knowing/ontology/")
    g.bind("npt", NPT)
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)
        
    print(f"[ONTOLOGY COMPILER] Parsing {len(rules_data)} rule patterns into RDF triples...")
    
    for rule in rules_data:
        directive = rule.get("rule_directive", "")
        context = rule.get("source_context", "Taught Step")
        
        concept_name = directive.split(" ")[0].replace(",", "").replace(".", "")
        concept_uri = NPT[concept_name]
        
        if "agnotology" in directive.lower() or "ignorance" in directive.lower():
            g.add((concept_uri, RDF.type, OWL.NamedIndividual))
            g.add((concept_uri, RDF.type, NPT.AgnotologicalPhenomenon))
        else:
            g.add((concept_uri, RDF.type, OWL.NamedIndividual))
            g.add((concept_uri, RDF.type, NPT.EpistemicConcept))
            
        g.add((concept_uri, RDFS.label, Literal(concept_name)))
        g.add((concept_uri, RDFS.comment, Literal(f"{directive} (Verified Source: {context})")))

    os.makedirs(os.path.dirname(output_ttl_path), exist_ok=True)
    g.serialize(destination=output_ttl_path, format="turtle")
    print(f"[SUCCESS] Semantic ontology graph safely synced to: {output_ttl_path}")
# =====================================================================
# INVOCATION GATEWAY
# =====================================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Run Ingestion Batch:  python pegleg_runner.py <path_to_url_list_txt_or_json>")
        print("  Compile Ontology:     python pegleg_runner.py --compile-ontology")
        sys.exit(1)
        
    target_source = sys.argv[1]
    
    # 1. INTERCEPT THE MANUAL ONTOLOGY COMPILATION COMMAND
    if target_source == "--compile-ontology":
        compile_json_rules_to_turtle()
        sys.exit(0)
        
    # 2. OTHERWISE, TREAT IT AS A VALID URL MANIFEST PATH
    if not os.path.exists(target_source):
        print(f"[ERROR] Specified URL source target file does not exist: {target_source}")
        sys.exit(1)
        
    urls = []
    # Handle JSON inputs
    if target_source.endswith('.json'):
        with open(target_source, 'r', encoding='utf-8') as f:
            data = json.load(f)
            urls = data if isinstance(data, list) else data.get('urls', [])
    # Default text line splitting
    else:
        with open(target_source, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
    if not urls:
        print("[NOTICE] Target source list parsed out completely empty.")
        sys.exit(0)
        
    run_ingestion_batch(urls)