"""
NPT Fleet Tools: PostgreSQL Cargo Ontology Operations
Architecture: Native Relational Knowledge Graph (ADR-003 & ADR-015)
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

def _get_strict_cargo_connection():
    """Establishes connection to Content/Cargo warehouse (CONTENT_DATABASE_URL)."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return None
    try:
        url = urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
    except Exception as e:
        print(f"[CARGO ONTOLOGY DB FAULT] {str(e)}")
        return None


def upsert_ontology_node(node_id: str, node_type: str, label: str, description: str = "", metadata_id: int = None, glossary_term: str = None, chapter_anchor: int = None, properties: dict = None) -> str:
    """
    Agent Tool: Adds or updates a conceptual, vignette, actor, or asset node in the cargo ontology.
    Node types: 'ASSET', 'CONCEPT', 'VIGNETTE', 'NAMED_ACTOR', 'CHAPTER'.
    Invoked By: BILGELADLE.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Database unavailable."

    props_json = json.dumps(properties or {})
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cargo.ontology_nodes (
                node_id, node_type, label, description, metadata_id, glossary_term, chapter_anchor, properties, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (node_id) DO UPDATE SET
                label = EXCLUDED.label,
                description = COALESCE(EXCLUDED.description, cargo.ontology_nodes.description),
                metadata_id = COALESCE(EXCLUDED.metadata_id, cargo.ontology_nodes.metadata_id),
                glossary_term = COALESCE(EXCLUDED.glossary_term, cargo.ontology_nodes.glossary_term),
                chapter_anchor = COALESCE(EXCLUDED.chapter_anchor, cargo.ontology_nodes.chapter_anchor),
                properties = EXCLUDED.properties;
            """,
            (node_id, node_type.upper(), label, description, metadata_id, glossary_term, chapter_anchor, props_json)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return f"[SUCCESS] Ontology node '{node_id}' ({node_type}) upserted."
    except Exception as e:
        if conn: conn.close()
        return f"[ERROR] Failed to upsert node: {str(e)}"


def upsert_ontology_edge(source_node_id: str, predicate: str, target_node_id: str, context: str = "", weight: float = 1.0, properties: dict = None) -> str:
    """
    Agent Tool: Creates or updates a directed semantic relationship in the cargo ontology.
    Predicates: 'documents_vignette', 'exemplifies_concept', 'perpetrated_by', 'anchors_to_chapter', 'leads_to', 'contradicts'.
    Invoked By: BILGELADLE.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Database unavailable."

    props_json = json.dumps(properties or {})
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO cargo.ontology_edges (
                source_node_id, predicate, target_node_id, context, weight, properties, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (source_node_id, predicate, target_node_id) DO UPDATE SET
                context = EXCLUDED.context,
                weight = EXCLUDED.weight,
                properties = EXCLUDED.properties;
            """,
            (source_node_id, predicate.lower().strip(), target_node_id, context, weight, props_json)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return f"[SUCCESS] Edge [{source_node_id}] --({predicate})--> [{target_node_id}] recorded."
    except Exception as e:
        if conn: conn.close()
        return f"[ERROR] Failed to record edge: {str(e)}"


def compile_cargo_topic_map() -> str:
    """
    Agent Tool: Generates the comprehensive, human-readable Topic Map markdown artifact
    at writings/cargo_topic_map.md from the active PostgreSQL ontology graph.
    Invoked By: BILGELADLE.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        return "[ERROR] Database unavailable."

    try:
        cursor = conn.cursor()

        # 1. High-level metrics
        cursor.execute("SELECT node_type, COUNT(*) FROM cargo.ontology_nodes GROUP BY node_type;")
        node_counts = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("SELECT predicate, COUNT(*) FROM cargo.ontology_edges GROUP BY predicate;")
        edge_counts = {r[0]: r[1] for r in cursor.fetchall()}

        # 2. Fetch all chapters
        cursor.execute("SELECT node_id, label, description, chapter_anchor FROM cargo.ontology_nodes WHERE node_type = 'CHAPTER' ORDER BY chapter_anchor;")
        chapters = cursor.fetchall()

        # Build markdown text
        lines = []
        lines.append("# The End of Knowing: Cargo Hold Topic Map & Conceptual Ontology")
        lines.append("\n**Curated By:** BILGELADLE (Thesis Cartographer)")
        lines.append(f"**Classification:** Living Forensic Knowledge Graph (PostgreSQL `cargo.ontology_*`)")
        lines.append(f"**Total Assets Indexed:** {node_counts.get('ASSET', 0)} | **Concepts:** {node_counts.get('CONCEPT', 0)} | **Vignettes:** {node_counts.get('VIGNETTE', 0)} | **Actors:** {node_counts.get('NAMED_ACTOR', 0)}\n")
        lines.append("---\n")

        # 3. Chapter-by-Chapter breakdown
        for ch_id, ch_label, ch_desc, ch_num in chapters:
            lines.append(f"## {ch_label}")
            lines.append(f"*{ch_desc}*\n")

            # Fetch concepts anchoring to this chapter
            cursor.execute("""
                SELECT n.node_id, n.label, n.description, e.context
                FROM cargo.ontology_nodes n
                JOIN cargo.ontology_edges e ON n.node_id = e.source_node_id
                WHERE e.target_node_id = %s AND e.predicate = 'anchors_to_chapter';
            """, (ch_id,))
            concepts = cursor.fetchall()

            if not concepts:
                lines.append("> *No cargo assets currently anchored to this chapter.*\n")
                continue

            for c_id, c_label, c_desc, c_ctx in concepts:
                lines.append(f"### ⚓ Concept: {c_label}")
                if c_desc:
                    lines.append(f"> **Theoretical Mechanism:** {c_desc}")

                # Fetch vignettes exemplifying this concept
                cursor.execute("""
                    SELECT v.node_id, v.label, v.description, e.context
                    FROM cargo.ontology_nodes v
                    JOIN cargo.ontology_edges e ON v.node_id = e.source_node_id
                    WHERE e.target_node_id = %s AND e.predicate = 'exemplifies_concept';
                """, (c_id,))
                vignettes = cursor.fetchall()

                for v_id, v_label, v_desc, v_ctx in vignettes:
                    lines.append(f"\n* **Vignette:** **{v_label}**")
                    if v_desc:
                        lines.append(f"  - *Forensic Warrant:* {v_desc}")

                    # Fetch actors
                    cursor.execute("""
                        SELECT a.label
                        FROM cargo.ontology_nodes a
                        JOIN cargo.ontology_edges e ON a.node_id = e.target_node_id
                        WHERE e.source_node_id = %s AND e.predicate = 'perpetrated_by';
                    """, (v_id,))
                    actors = [r[0] for r in cursor.fetchall()]
                    if actors:
                        lines.append(f"  - *Named Actors:* {', '.join(actors)}")

                    # Fetch assets documenting this vignette
                    cursor.execute("""
                        SELECT a.label, a.metadata_id, a.description
                        FROM cargo.ontology_nodes a
                        JOIN cargo.ontology_edges e ON a.node_id = e.source_node_id
                        WHERE e.target_node_id = %s AND e.predicate = 'documents_vignette';
                    """, (v_id,))
                    assets = cursor.fetchall()
                    if assets:
                        lines.append("  - *Cargo Holdings:*")
                        for a_lbl, a_mid, a_desc in assets:
                            lines.append(f"    - `cargo_{a_mid}`: [{a_lbl}](file:///c:/Users/timot/NPT-knowing-2/acquisitions/)")

                lines.append("")

            lines.append("---\n")

        cursor.close()
        conn.close()

        output_content = "\n".join(lines)
        os.makedirs("writings", exist_ok=True)
        topic_map_path = os.path.abspath("writings/cargo_topic_map.md")
        with open(topic_map_path, "w", encoding="utf-8") as f:
            f.write(output_content)

        return f"[SUCCESS] Living Topic Map successfully compiled to '{topic_map_path}'. ({len(lines)} lines)"

    except Exception as e:
        if conn: conn.close()
        return f"[ERROR] Topic Map compilation failed: {str(e)}"
