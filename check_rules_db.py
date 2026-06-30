"""
NPT Fleet: Diagnostic Check for Ontology Rules Database
"""
import os
import sys
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def check_ontology_rules():
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing DATABASE_URL in .env")
        sys.exit(1)

    url = urlparse(conn_string)
    db_name = url.path[1:]
    
    print(f"\n--- Checking 'agent_state.ontology_rules' in {db_name} ---")

    try:
        conn = pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=db_name
        )
        cursor = conn.cursor()

        cursor.execute("SELECT rule_id, agent_name, substring(rule_directive from 1 for 60) as excerpt FROM agent_state.ontology_rules;")
        rows = cursor.fetchall()

        if not rows:
            print("[RESULT] The table is completely empty (0 rows).")
        else:
            print(f"[RESULT] Found {len(rows)} rules in the database:\n")
            for row in rows:
                print(f" ID: {row[0]} | Agent: {row[1]} | Directive: {row[2]}...")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to query database: {e}")

if __name__ == "__main__":
    check_ontology_rules()