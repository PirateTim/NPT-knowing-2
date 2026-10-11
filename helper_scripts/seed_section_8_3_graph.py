"""
NPT Fleet: Seed Initial Concept Nodes and Edges for Section 8.3 Paragraph 2
Inserts the foundational graph topology into cargo.ontology_nodes and cargo.ontology_edges
connecting ship.letters_of_marque (ch08_sec8.3_p002) to cargo.content_metadata (1194)
via the two invariant Concept Nodes.
"""

import os
import sys
import json
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("CONTENT_DATABASE_URL missing from .env")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:]
    )

def seed_graph():
    conn = get_db_connection()
    cursor = conn.cursor()
    print("[GRAPH SEEDER] Connected to PostgreSQL. Seeding initial nodes and edges...")

    # 1. MANUSCRIPT CHUNK NODE
    chunk_id = "chunk:ch08_sec8.3_p002"
    cursor.execute(
        """
        INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            label = EXCLUDED.label,
            description = EXCLUDED.description,
            properties = EXCLUDED.properties;
        """,
        (
            chunk_id,
            "MANUSCRIPT_CHUNK",
            "ch08_sec8.3_p002 (Stargate vs. NASA Goddard)",
            "Manuscript paragraph contrasting Microsoft/OpenAI $100B Stargate with NASA Goddard Library closure.",
            8,
            json.dumps({
                "source_table": "ship.letters_of_marque",
                "chunk_id": "ch08_sec8.3_p002",
                "chapter_number": 8,
                "section_number": "8.3",
                "paragraph_sequence_number": 2
            })
        )
    )
    print(f"  -> Upserted Node: {chunk_id}")

    # 2. CONCEPT NODE 1: Ontological Demotion of Undigitized Truth
    concept_1_id = "CONCEPT:ontological_demotion_of_undigitized_truth"
    concept_1_props = {
        "epistemic_invariant": "If a primary observational record cannot be ingested as structured tokens by the dominant computational paradigm, administrative classes redefine it as non-data overhead, accelerating its physical destruction.",
        "actor_class": "Institutional research directors, facilities administrators, and agency operations executives",
        "behavioral_qualifier": "by deliberately choosing to rebrand un-tokenized physical observation logs as spatial clutter rather than allocating archival custodial resources",
        "exculpatory_alibi": "Workforce optimization, facilities consolidation, and operational efficiency",
        "epistemic_harm": "Permanent, unrecoverable erasure of ground-truth observational receipts (e.g., Soviet flight logs, Hubble calibration manuals) that can never be reconstructed by synthetic models."
    }
    cursor.execute(
        """
        INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            label = EXCLUDED.label,
            description = EXCLUDED.description,
            properties = EXCLUDED.properties;
        """,
        (
            concept_1_id,
            "CONCEPT",
            "Ontological Demotion of Undigitized Truth",
            "The managerial reclassification of physical, un-digitized primary observational evidence from foundational knowledge into disposable operational clutter.",
            8,
            json.dumps(concept_1_props)
        )
    )
    print(f"  -> Upserted Node: {concept_1_id}")

    # 3. CONCEPT NODE 2: Civilizational Capital Asymmetry
    concept_2_id = "CONCEPT:civilizational_capital_asymmetry"
    concept_2_props = {
        "epistemic_invariant": "Societies that prioritize statistical plausibility over empirical verification starve ground-truth custodial labor while lavishing infinite speculative capital on generative simulation machines.",
        "actor_class": "Technology conglomerate executives, venture capital syndicates, and enterprise procurement officers",
        "behavioral_qualifier": "by actively channeling hundreds of billions into speculative generative compute while treating ten-million-dollar archival baselines as an intolerable cost center",
        "exculpatory_alibi": "Technological inevitability, market demand, and fiscal austerity",
        "epistemic_harm": "The empirical foundation of human knowledge is hollowed out, leaving generative AI models to recursively train on simulations of data whose physical receipts have been incinerated."
    }
    cursor.execute(
        """
        INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            label = EXCLUDED.label,
            description = EXCLUDED.description,
            properties = EXCLUDED.properties;
        """,
        (
            concept_2_id,
            "CONCEPT",
            "Civilizational Capital Asymmetry",
            "The structural economic inversion where capital markets allocate infinite funding to automated prediction while starving primary empirical preservation of nominal maintenance.",
            8,
            json.dumps(concept_2_props)
        )
    )
    print(f"  -> Upserted Node: {concept_2_id}")

    # 4. CARGO NODE: NASA Goddard Library Closure (Metadata ID 1194)
    cargo_id = "cargo:1194"
    cursor.execute(
        """
        INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, metadata_id, chapter_anchor, properties, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
        ON CONFLICT (node_id) DO UPDATE SET
            label = EXCLUDED.label,
            description = EXCLUDED.description,
            properties = EXCLUDED.properties;
        """,
        (
            cargo_id,
            "CARGO",
            "NASA's Largest Library Is Closing (NYT 2025-12-31)",
            "Holdings from Goddard Space Flight Center library, including unique documents from early space race, warehoused or thrown out amid workforce cuts.",
            1194,
            8,
            json.dumps({
                "metadata_id": 1194,
                "source_url": "https://www.nytimes.com/2025/12/31/climate/nasa-goddard-library-closing.html?hl=en-US",
                "gcp_bucket_path": "acquisitions/nasas-largest-library-is-closing-amid-staff-and-lab-cuts.txt",
                "publication_date": "2025-12-31"
            })
        )
    )
    print(f"  -> Upserted Node: {cargo_id}")

    # 5. EDGES
    edges_to_insert = [
        # Manuscript -> Concept 1
        (
            chunk_id,
            "instantiates",
            concept_1_id,
            1.0,
            "Author cites Goddard library liquidation to demonstrate how un-digitized data is treated as clutter lacking forward compatibility.",
            {"evidentiary_type": "manuscript_premise", "chapter": 8, "section": "8.3"}
        ),
        # Manuscript -> Concept 2
        (
            chunk_id,
            "instantiates",
            concept_2_id,
            1.0,
            "Author contrasts $100B Stargate spend against $10M Goddard library cut (0.01% ratio).",
            {"evidentiary_type": "manuscript_premise", "ratio": "0.01%"}
        ),
        # Cargo -> Concept 1
        (
            cargo_id,
            "instantiates",
            concept_1_id,
            0.95,
            "NYT reporting confirms unique Soviet-era space race documents and Goddard collections are being thrown out or warehoused amid staff cuts.",
            {"reporting_outlet": "The New York Times", "reporting_date": "2025-12-31"}
        ),
        # Cargo -> Manuscript (Direct Peer Evidentiary Receipt)
        (
            cargo_id,
            "evidentiary_receipt_for",
            chunk_id,
            0.98,
            "Direct primary empirical receipt matching the author's citation in Section 8.3 Paragraph 2.",
            {"receipt_type": "primary_investigative_report", "matching_confidence": 0.98}
        ),
        # Concept 2 -> Concept 1 (Structural ontology edge)
        (
            concept_2_id,
            "amplifies",
            concept_1_id,
            0.90,
            "Unconstrained capital allocation to synthetic AI systems starves the operational budgets of physical archival facilities, accelerating collection liquidation.",
            {"causal_relation": "macro_economic_pressure"}
        )
    ]

    for src, pred, tgt, wt, ctx, props in edges_to_insert:
        # Check if edge already exists to prevent duplicates
        cursor.execute(
            """
            SELECT edge_id FROM cargo.ontology_edges
            WHERE source_node_id = %s AND predicate = %s AND target_node_id = %s
            """,
            (src, pred, tgt)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.execute(
                """
                UPDATE cargo.ontology_edges
                SET weight = %s, context = %s, properties = %s::jsonb
                WHERE edge_id = %s
                """,
                (wt, ctx, json.dumps(props), existing[0])
            )
            print(f"  -> Updated Edge [{existing[0]}]: {src} --[{pred}]--> {tgt}")
        else:
            cursor.execute(
                """
                INSERT INTO cargo.ontology_edges (source_node_id, predicate, target_node_id, weight, context, properties, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
                """,
                (src, pred, tgt, wt, ctx, json.dumps(props))
            )
            print(f"  -> Created Edge: {src} --[{pred}]--> {tgt}")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n[SUCCESS] Initial graph topology for Section 8.3 Paragraph 2 committed to database.")

if __name__ == "__main__":
    seed_graph()
