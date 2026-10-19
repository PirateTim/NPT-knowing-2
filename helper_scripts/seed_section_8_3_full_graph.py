"""
NPT Fleet: Full Section 8.3 Graph Topology Seeder

How to run:
    uv run python helper_scripts/seed_section_8_3_full_graph.py

What it does:
    Populates all 5 manuscript chunks, concept nodes, and epistemic relationship edges for Section 8.3 as reference exemplar.

Last run: Unknown
"""

# Record execution timestamp
try:
    import os, sys
    _tracker_dir = os.path.join(os.path.dirname(__file__), "..") if os.path.basename(os.path.dirname(__file__)) in ("db_provisioning", "maintenance") else os.path.dirname(__file__)
    if _tracker_dir not in sys.path:
        sys.path.insert(0, _tracker_dir)
    import run_tracker
    run_tracker.record_run(__file__)
except Exception:
    pass

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

def seed_full_section_8_3():
    conn = get_db_connection()
    cursor = conn.cursor()
    print("[GRAPH SEEDER] Seeding complete Section 8.3 graph topology into PostgreSQL...")

    # =========================================================================
    # 1. MANUSCRIPT CHUNKS (p001 through p005)
    # =========================================================================
    chunks = [
        ("chunk:ch08_sec8.3_p001", "ch08_sec8.3_p001 (Austerity Deception)", "Fiscal necessity as secondary deception; infinite capital for replacement vs. ground truth as technical debt.", 1),
        ("chunk:ch08_sec8.3_p002", "ch08_sec8.3_p002 (Stargate vs. NASA Goddard)", "Contrast between Microsoft/OpenAI $100B Stargate and $10M NASA Goddard library closure.", 2),
        ("chunk:ch08_sec8.3_p003", "ch08_sec8.3_p003 (Regulatory Over-compliance)", "Institutions using privacy/data minimization laws as legal shields to purge environmental impact tables.", 3),
        ("chunk:ch08_sec8.3_p004", "ch08_sec8.3_p004 (Commercial Enclosure of SSRN)", "Elsevier acquisition of Bepress/SSRN bricking supplemental data and runtime verification environments.", 4),
        ("chunk:ch08_sec8.3_p005", "ch08_sec8.3_p005 (Sanitized School Libraries)", "Purging physical history books from school libraries to force students into liquid, remote-editable digital platforms.", 5),
    ]

    for nid, label, desc, p_num in chunks:
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
                nid,
                "MANUSCRIPT_CHUNK",
                label,
                desc,
                8,
                json.dumps({
                    "source_table": "ship.letters_of_marque",
                    "chunk_id": nid.replace("chunk:", ""),
                    "chapter_number": 8,
                    "section_number": "8.3",
                    "paragraph_sequence_number": p_num
                })
            )
        )
    print("  -> Upserted 5 Manuscript Chunks")

    # =========================================================================
    # 2. CONCEPT NODES (Hook 5-Part Causal Anatomy)
    # =========================================================================
    concepts = [
        (
            "CONCEPT:civilizational_capital_asymmetry",
            "Civilizational Capital Asymmetry",
            "The structural economic inversion where capital markets allocate infinite funding to automated prediction while starving primary empirical preservation of nominal maintenance.",
            {
                "epistemic_invariant": "Societies that prioritize statistical plausibility over empirical verification starve ground-truth custodial labor while lavishing infinite speculative capital on generative simulation machines.",
                "actor_class": "Technology conglomerate executives, venture capital syndicates, and enterprise procurement officers",
                "behavioral_qualifier": "by actively channeling hundreds of billions into speculative generative compute while treating ten-million-dollar archival baselines as an intolerable cost center",
                "exculpatory_alibi": "Technological inevitability, market demand, and fiscal austerity",
                "epistemic_harm": "The empirical foundation of human knowledge is hollowed out, leaving generative AI models to recursively train on simulations of data whose physical receipts have been incinerated."
            }
        ),
        (
            "CONCEPT:ontological_demotion_of_undigitized_truth",
            "Ontological Demotion of Undigitized Truth",
            "The managerial reclassification of physical, un-digitized primary observational evidence from foundational knowledge into disposable operational clutter.",
            {
                "epistemic_invariant": "If a primary observational record cannot be ingested as structured tokens by the dominant computational paradigm, administrative classes redefine it as non-data overhead, accelerating its physical destruction.",
                "actor_class": "Institutional research directors, facilities administrators, and agency operations executives",
                "behavioral_qualifier": "by deliberately choosing to rebrand un-tokenized physical observation logs as spatial clutter rather than allocating archival custodial resources",
                "exculpatory_alibi": "Workforce optimization, facilities consolidation, and operational efficiency",
                "epistemic_harm": "Permanent, unrecoverable erasure of ground-truth observational receipts (e.g., Soviet flight logs, Hubble calibration manuals) that can never be reconstructed by synthetic models."
            }
        ),
        (
            "CONCEPT:weaponized_regulatory_compliance",
            "Weaponized Regulatory Compliance",
            "The intentional exploitation of privacy and data-protection mandates as legal pretexts to purge discoverable historical records and public science.",
            {
                "epistemic_invariant": "When institutions face accountability for policy failures, they weaponize statutory compliance frameworks to erase the baseline empirical records that could document their malfeasance.",
                "actor_class": "Government agency general counsels, regulatory compliance officers, and department heads",
                "behavioral_qualifier": "by actively invoking 'data minimization' and 'privacy protection' to permanently delete longitudinal public environmental baselines and hydrology tables",
                "exculpatory_alibi": "Statutory privacy compliance, citizen data protection, and administrative risk management",
                "epistemic_harm": "Evaporation of longitudinal civic evidence, rendering environmental degradation and corporate regulatory capture legally and historically invisible."
            }
        ),
        (
            "CONCEPT:commercial_enclosure_of_verification_infrastructure",
            "Commercial Enclosure of Verification Infrastructure",
            "The private equity capture of open scholarly commons, converting persistent academic records into proprietary dependencies and bricking supplemental verification data.",
            {
                "epistemic_invariant": "When monopolistic publishing conglomerates acquire open academic archives, they subordinate long-term archival persistence to quarterly software optimization, severing peer-reviewed claims from their runtime receipts.",
                "actor_class": "Conglomerate publishing executives, private equity platform acquirers, and proprietary repository managers",
                "behavioral_qualifier": "by acquiring community repositories (Bepress/SSRN) and deprecating the software execution environments required to verify peer-reviewed datasets",
                "exculpatory_alibi": "Platform modernization, infrastructure consolidation, and security updates",
                "epistemic_harm": "The scientific record degrades into un-replicable 'Ghost Facts' because the raw data and software required to verify published papers are bricked."
            }
        ),
        (
            "CONCEPT:epistemic_liquidation_via_platform_dependency",
            "Epistemic Liquidation via Platform Dependency",
            "The systematic replacement of persistent physical print records with remotely revocable, centrally managed digital subscription streams.",
            {
                "epistemic_invariant": "Replacing immutable physical artifacts with centralized digital portals transforms permanent historical knowledge into an ephemeral, remotely modifiable software service.",
                "actor_class": "Public school district administrators, educational software monopolies, and state board trustees",
                "behavioral_qualifier": "by systematically deaccessioning physical humanities books from shelves and mandating licensed digital readers with remote deletion privileges",
                "exculpatory_alibi": "Curriculum modernization, administrative efficiency, and digital equity",
                "epistemic_harm": "History loses its permanence ('stone') and becomes a liquid state ('vapor') subject to real-time ideological censorship, silent modification, and remote deletion."
            }
        )
    ]

    for cid, label, desc, props in concepts:
        cursor.execute(
            """
            INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, chapter_anchor, properties, created_at)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (node_id) DO UPDATE SET
                label = EXCLUDED.label,
                description = EXCLUDED.description,
                properties = EXCLUDED.properties;
            """,
            (cid, "CONCEPT", label, desc, 8, json.dumps(props))
        )
    print(f"  -> Upserted {len(concepts)} Concept Nodes")

    # =========================================================================
    # 3. CARGO NODES (Surfaced via Gateway A Discovery Engine)
    # =========================================================================
    cargo_items = [
        (
            "cargo:1194", 1194,
            "NASA's Largest Library Is Closing (NYT 2025-12-31)",
            "Goddard Space Flight Center library closed; unique Soviet space race documents and Hubble records discarded amid workforce cuts.",
            {"source_url": "https://www.nytimes.com/2025/12/31/climate/nasa-goddard-library-closing.html?hl=en-US", "outlet": "The New York Times"}
        ),
        (
            "cargo:1288", 1288,
            "Microsoft Asks 'Who Needs A Library When You've Got AI?'",
            "Reporting on Microsoft's corporate campaign positioning AI copilots as replacements for physical libraries.",
            {"source_url": "https://kotaku.com/microsoft-library-ai-copilot-errors-2000660247", "outlet": "Kotaku/Tech News"}
        ),
        (
            "cargo:13", 13,
            "AI's Voracious Appetite for Data Imperils Privacy Principles (Bloomberg Law)",
            "Bloomberg Law investigation on corporate data minimization pretexts, litigation discovery, and regulatory retention.",
            {"source_url": "https://news.bloomberglaw.com/litigation/ais-voracious-appetite-for-data", "outlet": "Bloomberg Law"}
        ),
        (
            "cargo:403", 403,
            "Is the Staggeringly Profitable Business of Scientific Publishing Bad for Science?",
            "Guardian long-form forensic investigation on Elsevier/RELX commercial enclosure and 40% profit margins locking down academic knowledge.",
            {"source_url": "https://www.theguardian.com/science/2017/jun/27/profitable-business-scientific-publishing-bad-for-science", "outlet": "The Guardian"}
        ),
        (
            "cargo:402", 402,
            "The Retreat to Analog: When Digital Tools Stop Feeling Like Progress",
            "Analysis of digital lock-in, forced licensing dependency, and the cultural return to physical preservation.",
            {"source_url": "https://theintersect.com/retreat-to-analog", "outlet": "The Intersect"}
        )
    ]

    for nid, mid, label, desc, props in cargo_items:
        cursor.execute(
            """
            INSERT INTO cargo.ontology_nodes (node_id, node_type, label, description, metadata_id, chapter_anchor, properties, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (node_id) DO UPDATE SET
                label = EXCLUDED.label,
                description = EXCLUDED.description,
                properties = EXCLUDED.properties;
            """,
            (nid, "CARGO", label, desc, mid, 8, json.dumps(props))
        )
    print(f"  -> Upserted {len(cargo_items)} Cargo Nodes")

    # =========================================================================
    # 4. EDGES (Bipartite Instantiations + Structural Concept Edges + Peer Links)
    # =========================================================================
    edges = [
        # P1: Austerity Deception -> Capital Asymmetry
        ("chunk:ch08_sec8.3_p001", "instantiates", "CONCEPT:civilizational_capital_asymmetry", 1.0,
         "Author establishes the macro thesis: ground truth treated as technical debt while automation replacement budgets are infinite.", {}),
        
        # P2: Stargate vs Goddard -> Capital Asymmetry & Ontological Demotion
        ("chunk:ch08_sec8.3_p002", "instantiates", "CONCEPT:civilizational_capital_asymmetry", 1.0,
         "Contrasts $100B Stargate spend against $10M Goddard library cut.", {}),
        ("chunk:ch08_sec8.3_p002", "instantiates", "CONCEPT:ontological_demotion_of_undigitized_truth", 1.0,
         "Managerial class labels Soviet mission logs 'clutter' lacking forward compatibility with the machine.", {}),

        # P3: Regulatory Over-compliance -> Weaponized Compliance
        ("chunk:ch08_sec8.3_p003", "instantiates", "CONCEPT:weaponized_regulatory_compliance", 1.0,
         "EDGI audit documents federal removal of hydrology tables and impact reports under 'data minimization' pretext.", {}),

        # P4: Elsevier Enclosure -> Commercial Enclosure of Verification
        ("chunk:ch08_sec8.3_p004", "instantiates", "CONCEPT:commercial_enclosure_of_verification_infrastructure", 1.0,
         "Elsevier acquisition of Bepress/SSRN bricks supplemental datasets, turning peer-reviewed papers into uncheckable Ghost Facts.", {}),

        # P5: Sanitized School Libraries -> Platform Dependency
        ("chunk:ch08_sec8.3_p005", "instantiates", "CONCEPT:epistemic_liquidation_via_platform_dependency", 1.0,
         "PEN America index shows 10,000+ book removals forcing students into liquid, remote-editable digital services.", {}),

        # Cargo 1194 (NASA Library) -> Concept & Chunk
        ("cargo:1194", "instantiates", "CONCEPT:ontological_demotion_of_undigitized_truth", 0.95,
         "NYT reporting confirms unique early space race documents warehoused or thrown out amid workforce cuts.", {}),
        ("cargo:1194", "evidentiary_receipt_for", "chunk:ch08_sec8.3_p002", 0.98,
         "Primary empirical report confirming Goddard Library liquidation cited in paragraph 2.", {}),

        # Cargo 1288 (Microsoft Library pitch) -> Concept & Chunk
        ("cargo:1288", "instantiates", "CONCEPT:civilizational_capital_asymmetry", 0.94,
         "Documents Microsoft pitching generative AI copilots as the direct replacement for physical libraries.", {}),
        ("cargo:1288", "evidentiary_receipt_for", "chunk:ch08_sec8.3_p002", 0.92,
         "Direct evidence of corporate rhetoric arguing libraries are unnecessary in the age of AI.", {}),

        # Cargo 13 (Bloomberg Privacy/Minimization) -> Concept & Chunk
        ("cargo:13", "instantiates", "CONCEPT:weaponized_regulatory_compliance", 0.90,
         "Bloomberg Law forensic report on corporate and agency data minimization rules impacting records and litigation.", {}),
        ("cargo:13", "evidentiary_receipt_for", "chunk:ch08_sec8.3_p003", 0.88,
         "Corroborating legal reporting on the intersection of data minimization and records purging.", {}),

        # Cargo 403 (Guardian Elsevier investigation) -> Concept & Chunk
        ("cargo:403", "instantiates", "CONCEPT:commercial_enclosure_of_verification_infrastructure", 0.96,
         "Investigative report exposing RELX/Elsevier monopoly margins and lock-in of scientific papers and archives.", {}),
        ("cargo:403", "evidentiary_receipt_for", "chunk:ch08_sec8.3_p004", 0.95,
         "Ground-truth investigation of Elsevier's acquisition strategy and repository monopoly.", {}),

        # Cargo 402 (Retreat to Analog) -> Concept & Chunk
        ("cargo:402", "instantiates", "CONCEPT:epistemic_liquidation_via_platform_dependency", 0.89,
         "Analysis of the vulnerability of digital licensing models versus the physical permanence of print.", {}),
        ("cargo:402", "evidentiary_receipt_for", "chunk:ch08_sec8.3_p005", 0.87,
         "Corroborating analysis of why digital media facilitates retroactive censorship.", {}),

        # Structural Concept-to-Concept Dynamics (Tier 2 Edges)
        ("CONCEPT:civilizational_capital_asymmetry", "amplifies", "CONCEPT:ontological_demotion_of_undigitized_truth", 0.90,
         "Infinite capital poured into automated prediction systems accelerates the budget-cutting of physical archives.", {}),
        ("CONCEPT:weaponized_regulatory_compliance", "rationalizes", "CONCEPT:ontological_demotion_of_undigitized_truth", 0.88,
         "Compliance language provides the legal alibi that justifies discarding un-tokenized physical records.", {}),
        ("CONCEPT:commercial_enclosure_of_verification_infrastructure", "amplifies", "CONCEPT:epistemic_liquidation_via_platform_dependency", 0.91,
         "Monopoly control over research repositories forces academic and public consumers into captive subscription streams.", {})
    ]

    for src, pred, tgt, wt, ctx, props in edges:
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
        else:
            cursor.execute(
                """
                INSERT INTO cargo.ontology_edges (source_node_id, predicate, target_node_id, weight, context, properties, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
                """,
                (src, pred, tgt, wt, ctx, json.dumps(props))
            )
    conn.commit()
    cursor.close()
    conn.close()
    print(f"  -> Upserted {len(edges)} Edges into cargo.ontology_edges.")
    print("[SUCCESS] Full Section 8.3 graph topology live in database!")

if __name__ == "__main__":
    seed_full_section_8_3()
