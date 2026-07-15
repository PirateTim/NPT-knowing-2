"""
NPT Fleet Tool: Quick Silver Ledger Dashboard View
"""
import os
import sys
import json
from urllib.parse import urlparse
import pg8000.dbapi

def get_latest_enrichment():
    print("=========================================================")
    print("        NPT FLEET LEDGER: LATEST SILVER ENRICHMENT       ")
    print("=========================================================")
    
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[ERROR] CONTENT_DATABASE_URL environment variable not set.")
        return

    try:
        url = urlparse(conn_string)
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
        cursor = conn.cursor()
        
        # Pull the latest enrichment row and join with content_metadata to grab the Title
        query = """
            SELECT 
                e.agent_name, 
                e.enrichment_type, 
                e.payload, 
                e.created_at, 
                m.title, 
                m.source_url
            FROM cargo.fleet_enrichments e
            JOIN cargo.content_metadata m ON e.metadata_id = m.id
            ORDER BY e.created_at DESC
            LIMIT 1;
        """
        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            print("[NOTICE] The cargo.fleet_enrichments ledger is currently empty.")
            return

        agent_name, enrichment_type, payload, created_at, title, source_url = row

        # Parse the JSONB payload back out for pretty printing
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload # pg8000 handles dict conversion automatically sometimes

        print(f"Timestamp: {created_at}")
        print(f"Agent:     {agent_name.upper()}")
        print(f"Type:      {enrichment_type.upper()}")
        print(f"Asset:     {title}")
        print(f"URL:       {source_url}")
        print("-" * 57)
        print(f"SAIL LOCKER ASSIGNMENT: {data.get('sail_locker', 'UNKNOWN')}")
        print("-" * 57)
        print("\n### EPISTEMIC INTEGRITY OVERVIEW:")
        print(data.get("epistemic_integrity_overview", "No overview provided."))
        
        print("\n### DETECTED EPISTEMIC ERRORS:")
        errors = data.get("detected_errors", [])
        if not errors:
            print("None detected.")
        for idx, err in enumerate(errors, 1):
            print(f"\n  {idx}. Category: {err.get('error_category')}")
            print(f"     Evidence: '{err.get('evidence')}'")
            print(f"     Severance: {err.get('epistemic_severance')}")
        print("\n=========================================================")

    except Exception as e:
        print(f"[DASHBOARD FAULT] Failed to read ledger: {str(e)}")

if __name__ == "__main__":
    # Ensure local path references work
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    get_latest_enrichment()