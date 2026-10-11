"""
NPT Fleet: Concept Node Editor Utility
Tool to inspect, list, and fine-tune concept definitions and Hook 5-part causal anatomy
inside cargo.ontology_nodes in PostgreSQL.
"""

import os
import sys
import json
import argparse
import urllib.parse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from .env")
    url = urllib.parse.urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/")
    )

def list_concepts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT node_id, label, chapter_anchor
        FROM cargo.ontology_nodes
        WHERE node_type = 'CONCEPT'
        ORDER BY node_id
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    print(f"\n--- ACTIVE CONCEPT NODES ({len(rows)}) ---")
    for nid, label, chap in rows:
        print(f"• {nid} (Ch {chap or '?'}) - {label}")

def get_concept(node_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT node_id, label, description, chapter_anchor, properties
        FROM cargo.ontology_nodes
        WHERE node_id = %s
        """,
        (node_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        print(f"[ERROR] Concept node '{node_id}' not found.", file=sys.stderr)
        return
    nid, label, desc, chap, props = row
    print(f"\n=======================================================")
    print(f"NODE ID:        {nid}")
    print(f"LABEL:          {label}")
    print(f"CHAPTER:        {chap}")
    print(f"DESCRIPTION:    {desc}")
    print("-------------------------------------------------------")
    print("HOOK 5-PART CAUSAL ANATOMY (properties):")
    print(json.dumps(props or {}, indent=2))
    print("=======================================================\n")

def update_concept_property(node_id: str, prop_key: str, prop_val: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE cargo.ontology_nodes
        SET properties = jsonb_set(COALESCE(properties, '{}'::jsonb), %s::text[], %s::jsonb),
            created_at = NOW()
        WHERE node_id = %s
        """,
        ([prop_key], json.dumps(prop_val), node_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[SUCCESS] Updated property '{prop_key}' on '{node_id}'.")
    get_concept(node_id)

def update_concept_description(node_id: str, new_desc: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE cargo.ontology_nodes
        SET description = %s
        WHERE node_id = %s
        """,
        (new_desc, node_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[SUCCESS] Updated description on '{node_id}'.")
    get_concept(node_id)

def main():
    parser = argparse.ArgumentParser(description="NPT Concept Node Editor")
    parser.add_argument("--list", action="store_true", help="List all concept nodes")
    parser.add_argument("--get", type=str, help="View concept node details by node_id")
    parser.add_argument("--set-prop", nargs=3, metavar=("NODE_ID", "KEY", "VALUE"),
                        help="Update a property within properties JSONB (e.g. epistemic_harm, actor_class)")
    parser.add_argument("--set-desc", nargs=2, metavar=("NODE_ID", "DESCRIPTION"),
                        help="Update the top-level description of a concept node")

    args = parser.parse_args()
    if args.list:
        list_concepts()
    elif args.get:
        get_concept(args.get)
    elif args.set_prop:
        nid, k, v = args.set_prop
        update_concept_property(nid, k, v)
    elif args.set_desc:
        nid, d = args.set_desc
        update_concept_description(nid, d)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
