"""
NPT Fleet: The Master Sail Plan - Workflow Cargo Triage & Preprocessing (Level 2)
Architecture: Inverted Shared-Thread Pipeline (thread_cargo_{metadata_id})
Execution Order:
  Turn 1 - BILGELADLE: Reads raw text once, evaluates against ship/SHIP_DECK_PLANS.md,
                       assigns Primary Chapter Anchor (0-12 or NONE) and Sail Locker.
                       If DOLDRUMS, pipeline halts for Author triage (Level 1 Doldrums Breakout).
  Turn 2 - CUTLASS:    Inherits raw text & chapter anchor from thread context.
                       Performs forensic logic audit (SAYS vs IS, Popperian demarcation, Chain of Ruin).
                       Writes writings/cargo/cargo_{id}/cutlass_audit.md.
  Turn 3 - GROG:       Inherits thread context. Produces Straight Summary (<250 words)
                       and extracts upstream primary source sightings into centralized ledger.
                       Writes writings/cargo/cargo_{id}/grog_extraction.md.
Deliverable:
  Pre-populates the reusable asset dossier in writings/cargo/cargo_{metadata_id}/
  allowing future Full Chases to fast-forward with zero token spend.
"""

import os
import sys
import re
import json
import argparse
from typing import Optional, Dict, Any

# Ensure react_agent root is on sys.path
AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from core.agent_engine import AgentEngine
from tools.cargo_db_tools import _get_strict_cargo_connection, log_fleet_enrichment


def get_cargo_metadata(metadata_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves authoritative asset metadata from cargo.content_metadata."""
    conn = _get_strict_cargo_connection()
    if not conn:
        print("[ERROR] Failed to connect to cargo database.")
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, title, source_url, gcp_bucket_path, authors, abstract, item_type
            FROM cargo.content_metadata
            WHERE id = %s
            LIMIT 1;
            """,
            (metadata_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1] or f"Cargo {row[0]}",
            "source_url": row[2] or "",
            "gcp_bucket_path": row[3] or "",
            "authors": row[4] or "Unknown",
            "abstract": row[5] or "",
            "item_type": row[6] or "article"
        }
    except Exception as e:
        print(f"[ERROR] Metadata query failed: {e}")
        return None
    finally:
        conn.close()


def run_cargo_triage(
    metadata_id: int,
    force_turn2_3: bool = False,
    model_override: Optional[str] = None,
    author_locker: Optional[str] = None,
    author_note: Optional[str] = None,
    cost_tracker: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes the 3-turn Inverted Shared-Thread Pipeline for a single cargo asset.
    Thread ID: thread_cargo_{metadata_id}
    """
    cargo = get_cargo_metadata(metadata_id)
    if not cargo:
        return {"status": "ERROR", "message": f"Cargo asset id={metadata_id} not found in cargo.content_metadata."}

    if author_locker and author_locker.upper() in ("MAINSAIL", "BILGE", "JIB"):
        force_turn2_3 = True

    thread_id = f"thread_cargo_{metadata_id}"
    cargo_dir = os.path.join(WORKSPACE_ROOT, "writings", "cargo", f"cargo_{metadata_id}")
    os.makedirs(cargo_dir, exist_ok=True)

    print("\n" + "=" * 70)
    print(f" NPT FLEET: CARGO TRIAGE & PREPROCESSING PIPELINE (cargo_{metadata_id})")
    print(f" TITLE: {cargo['title']}")
    print(f" PATH:  {cargo['gcp_bucket_path']}")
    print(f" THREAD: {thread_id}")
    if author_locker:
        print(f" AUTHOR CALIBRATION: Locker = {author_locker} | Note = {author_note}")
    print("=" * 70)

    xml_dir = os.path.join(AGENT_ROOT, "agents")
    pipeline_result = {
        "metadata_id": metadata_id,
        "title": cargo["title"],
        "thread_id": thread_id,
        "turns_completed": []
    }

    # =========================================================================
    # TURN 1: BILGELADLE (Triage, Chapter Anchor & Sail Locker)
    # =========================================================================
    print(f"\n>>> [TURN 1: BILGELADLE] Evaluating asset against 13 Chapter Backbones...")
    bilgeladle_xml = os.path.join(xml_dir, "bilgeladle", "bilgeladle.xml")
    bilgeladle = AgentEngine("bilgeladle", xml_profile_path=bilgeladle_xml, model_override=model_override, cost_tracker=cost_tracker)
    
    turn1_prompt = f"""
You are executing Turn 1 of the Cargo Intake Pipeline for cargo asset id={cargo['id']}.

ASSET DETAILS:
- Metadata ID: {cargo['id']}
- Title: {cargo['title']}
- Source URL: {cargo['source_url']}
- GCS Path: {cargo['gcp_bucket_path']}
- Item Type: {cargo['item_type']}
"""
    if author_locker:
        turn1_prompt += f"""
AUTHOR CALIBRATION OVERRIDE:
- The human Author has sovereignly assigned this asset to Sail Locker: {author_locker.upper()}
- Author Rationale / Guidance Note: {author_note or 'None provided'}
- Adopt this Sail Locker calibration in your evaluation and focus your analysis on finding the exact Chapter Anchor and Section Ribs that support this assignment.
"""
    turn1_prompt += f"""
INSTRUCTIONS:
1. Call `read_knowledge_artifact("{cargo['gcp_bucket_path']}")` to stream and read the raw text of this asset into our conversation context.
2. Evaluate this asset against the 13 Master Chapter Backbones in `ship/SHIP_DECK_PLANS.md` (pre-loaded in your context).
3. Assign EXACTLY ONE Primary Chapter Anchor:
   - If it aligns with a chapter, specify: integer 0–12 and Chapter Title.
   - If it does NOT meaningfully align with any of the 13 Chapters, specify: NONE (UNANCHORED).
4. Identify candidate Section Ribs (Operative, Enabler, Qualifier, Doom Point).
5. Assign the authoritative Sail Locker:
   - MAINSAIL: Core theoretical, historical, or empirical foundation for the chapter.
   - BILGE: Empirical crime scene of epistemic rot, corporate PR deceit, or unverified output to autopsy.
   - JIB: Methodological or cross-cutting supporting evidence.
   - DOLDRUMS: Ambiguous, marginal, unanchored, suspected flotsam/wherry, or defective/incomplete scrape.
6. ADVISORY TAGS (Human Sovereignty Guardrail):
   - You CANNOT assign FLOTSAM or WHERRY directly. If you recommend the Author discard this as spam/irrelevant, tag: 'Recommended Locker: FLOTSAM'. If developer/infrastructure tooling, tag: 'Recommended Locker: WHERRY'.
   - If the raw text is a truncated paywall preview, 403 block, or empty shell, tag: 'Needs Reacquisition: TRUE'.
7. 3-STAGE CHAIN OF RUIN DIAGNOSIS (The Book Framework):
   - Stage 1: Pre-existing Epistemic Decay (The Structural Trap) — What prior credential rot, paywall enclosure, or ungrounded training distribution does this asset rely on?
   - Stage 2: Technological Catalyst (The Lossy Mirror) — How is computation, scaling laws, or algorithmic tooling deployed to scale, automate, or launder this pre-existing rot?
   - Stage 3: Proactive Negligence (The Human Shield) — What specific human decisions (liability evasion, duty abandonment, refusal to license authentic ground truth) are being protected behind the machine?
8. THESIS PARALLELS & CONCEPTUAL LENSES:
   - Draw concise, grounded connections to specific metaphors and concepts in *The End of Knowing* (e.g. The Alchemist's Bill, The Caligula Loop, The Private Reserve, The Malthusian Fuel Limit). Keep your analysis calibrated (~450–600 words total for the dossier).
   - Note any Secondary Chapter Cross-References.
   - (Do NOT write generic downstream instructions for Grog or Scallywag; Cutlass will provide actionable forensic ammunition).
9. Write your complete evaluation to local disk at: `writings/cargo/cargo_{cargo['id']}/bilgeladle_alignment.md` using `write_local_file`.
10. Summarize your final verdict in your response with these exact header fields:
   - Primary Chapter Anchor: [0-12 or NONE (UNANCHORED)]
   - Candidate Section Ribs: [e.g. Sec 3.6, Sec 3.7]
   - Sail Locker: [MAINSAIL | BILGE | JIB | DOLDRUMS]
   - Recommended Locker: [None | FLOTSAM | WHERRY]
   - Needs Reacquisition: [TRUE | FALSE]
   - Alignment Summary: [1-2 sentences]
"""
    try:
        session1 = bilgeladle.start_chat_session(thread_id)
        resp1 = bilgeladle.execute_turn(session1, turn1_prompt)
        bilgeladle.save_checkpoint(thread_id, session1.get_history())
        pipeline_result["turns_completed"].append("bilgeladle")
        print(f"[TURN 1 COMPLETE] Bilgeladle response:\n{resp1[:400]}...\n")
    finally:
        bilgeladle.close()

    # Parse Turn 1 verdict
    primary_chapter_match = re.search(
        r"Primary Chapter Anchor[:\*]+\s*(?:CHAPTER\s*)?(\d+|NONE(?:\s*\(UNANCHORED\))?)",
        resp1,
        re.IGNORECASE
    )
    sail_locker_match = re.search(
        r"Sail Locker[:\*]+\s*(?:Assignment[:\*]+\s*)?(MAINSAIL|BILGE|JIB|DOLDRUMS)",
        resp1,
        re.IGNORECASE
    )
    rec_locker_match = re.search(
        r"Recommended Locker[:\*]+\s*(FLOTSAM|WHERRY|None)",
        resp1,
        re.IGNORECASE
    )
    reacq_match = re.search(
        r"Needs Reacquisition[:\*]+\s*(TRUE|FALSE)",
        resp1,
        re.IGNORECASE
    )

    primary_chapter = primary_chapter_match.group(1) if primary_chapter_match else "NONE"
    sail_locker = sail_locker_match.group(1).upper() if sail_locker_match else "DOLDRUMS"
    rec_locker = rec_locker_match.group(1).upper() if rec_locker_match else "NONE"
    needs_reacq = (reacq_match.group(1).upper() == "TRUE") if reacq_match else False

    pipeline_result["primary_chapter"] = primary_chapter
    pipeline_result["sail_locker"] = sail_locker
    pipeline_result["recommended_locker"] = rec_locker
    pipeline_result["needs_reacquisition"] = needs_reacq

    # Autonomous Re-Acquisition Circuit Breaker:
    # If Bilgeladle determines the asset is a truncated paywall preview, 403 block, or defective stub:
    if needs_reacq:
        print(f"\n[AUTO-CIRCUIT] Asset cargo_{metadata_id} flagged by Bilgeladle as defective/stub text.")
        from tools.cargo_db_tools import requeue_defective_cargo
        reacq_res = requeue_defective_cargo(
            metadata_id=cargo['id'],
            source_url=cargo['source_url'],
            reason="Bilgeladle Turn 1 detected truncated paywall preview / bot challenge stub"
        )
        print(f"    -> {reacq_res.get('message')}")
        pipeline_result["status"] = "AUTO_REQUEUED" if reacq_res.get("action") == "REQUEUED" else "DEAD_LETTER_MAX_RETRIES"
        pipeline_result["reacq_result"] = reacq_res
        return pipeline_result

    # Gate Check: If DOLDRUMS and not force, halt pipeline for Author review (Level 1 Doldrums Breakout)
    if sail_locker == "DOLDRUMS" and not force_turn2_3:
        print(f"\n[GATE HALT] Asset cargo_{metadata_id} placed in DOLDRUMS (Chapter Anchor: {primary_chapter}).")
        print(f"Advisory: Recommended Locker = {rec_locker}, Needs Reacquisition = {needs_reacq}.")
        print("Halting pipeline to protect Author tokens and cognitive state. Triage console will surface this item.")
        pipeline_result["status"] = "HALTED_DOLDRUMS"
        return pipeline_result

    # =========================================================================
    # TURN 2: CUTLASS (Targeted Forensic Logic Audit)
    # =========================================================================
    print(f"\n>>> [TURN 2: CUTLASS] Executing targeted Popperian logic audit for Chapter {primary_chapter}...")
    cutlass_xml = os.path.join(xml_dir, "cutlass", "cutlass.xml")
    cutlass = AgentEngine("cutlass", xml_profile_path=cutlass_xml, model_override=model_override, cost_tracker=cost_tracker)

    turn2_prompt = f"""
You are executing Turn 2 of the Cargo Intake Pipeline for cargo asset id={cargo['id']}.
Notice that Bilgeladle evaluated this asset in Turn 1 and established:
- Primary Chapter Anchor: {primary_chapter}
- Candidate Section Ribs from Deck Plans
- Initial Sail Locker: {sail_locker}
- 3-Stage Chain of Ruin Diagnosis (Pre-existing Decay, Technological Catalyst, Proactive Negligence)
"""
    if author_locker:
        turn2_prompt += f"""
AUTHOR CALIBRATION OVERRIDE:
- The human Author has sovereignly assigned this asset to Sail Locker: {author_locker.upper()}
- Author Guidance / Intent: {author_note or 'None provided'}
- Confirm this Sail Locker assignment in Section 4 unless you detect an unambiguous disqualifying defect.
"""
    turn2_prompt += f"""
INSTRUCTIONS:
1. The raw text and Bilgeladle's Turn 1 evaluation (including Chapter Anchor and Chain of Ruin) are already in this thread context. You are STRICTLY FORBIDDEN from repeating or re-writing the 3-Stage Chain of Ruin or writing a redundant Sail Locker re-justification.
2. Perform a targeted forensic logic audit against Chapter {primary_chapter}'s core thesis and epistemic friction:
   - Section 1: Epistemic Deconstruction (What the Asset SAYS vs. What the Asset IS).
   - Section 2: Popperian Logic Audit & Toulmin Causal Warrants (Falsifiability, Causal Claim, Grounds, Warrant, Rebuttal).
   - Section 3: Classical & Epistemic Fallacy Scan (audit against formal fallacies and the 32 Epistemic Failure Modes; list only present fallacies).
   - Section 4: Anti-Financial Reductionism & Epistemic Scorecard (0.0 to 10.0), with single-sentence confirmation of the Sail Locker.
   - Section 5: Downstream Directives for Grog and Scallywag:
     * FOR GROG: Specific quantitative metrics, numbers, or exact quotes to isolate for the Straight Summary.
     * FOR SCALLYWAG: Named human perpetrators, institutional hypocrisies, and smoking guns ripe for polemical autopsy.
3. Keep your audit razor-sharp and high-density (~700–900 words total).
4. Write your completed audit to local disk at: `writings/cargo/cargo_{cargo['id']}/cutlass_audit.md` using `write_local_file`.
5. Call `log_full_audit_dossier` to synchronize the authoritative Sail Locker and dossier path with PostgreSQL.
6. Provide a crisp summary of your audit findings and confirmed Sail Locker.
"""
    try:
        session2 = cutlass.start_chat_session(thread_id)
        resp2 = cutlass.execute_turn(session2, turn2_prompt)
        cutlass.save_checkpoint(thread_id, session2.get_history())
        pipeline_result["turns_completed"].append("cutlass")
        print(f"[TURN 2 COMPLETE] Cutlass response:\n{resp2[:400]}...\n")
    finally:
        cutlass.close()

    # Re-check Sail Locker from Cutlass response if updated
    cutlass_locker_match = re.search(r"Sail Locker(?:\s*Confirmation)?[:\*]+\s*(?:Assignment[:\*]+\s*)?(MAINSAIL|BILGE|JIB|DOLDRUMS)", resp2, re.IGNORECASE)
    if cutlass_locker_match:
        sail_locker = cutlass_locker_match.group(1).upper()
        pipeline_result["sail_locker"] = sail_locker

    if sail_locker == "DOLDRUMS" and not force_turn2_3:
        print(f"\n[GATE HALT] Cutlass confirmed or moved cargo_{metadata_id} to DOLDRUMS. Halting Turn 3.")
        pipeline_result["status"] = "HALTED_DOLDRUMS_AFTER_CUTLASS"
        return pipeline_result

    # =========================================================================
    # TURN 3: GROG (Straight Summary & Upstream Primary Source Sightings)
    # =========================================================================
    print(f"\n>>> [TURN 3: GROG] Extracting straight summary and upstream primary source sightings...")
    grog_xml = os.path.join(xml_dir, "grog", "grog.xml")
    grog = AgentEngine("grog", xml_profile_path=grog_xml, model_override=model_override, cost_tracker=cost_tracker)

    turn3_prompt = f"""
You are executing Turn 3 of the Cargo Intake Pipeline for cargo asset id={cargo['id']}.
The raw asset text, Bilgeladle's alignment, and Cutlass's audit are already present in this conversation thread.
"""
    if author_note:
        turn3_prompt += f"""
AUTHOR GUIDANCE FOR SUMMARY & SIGHTINGS:
- The human Author provided the following guidance note: "{author_note}"
- Pay special attention to capturing any primary sources, books, reports, or data sightings highlighted by the Author!
"""
    turn3_prompt += f"""
INSTRUCTIONS:
1. Generate an objective, high-density STRAIGHT SUMMARY (< 250 words) capturing the core factual assertions and empirical findings without judgment or editorializing, tailored as clean context for Scallywag.
2. Perform an exhaustive scan for UPSTREAM PRIMARY SOURCE SIGHTINGS:
   - Identify all referenced whitepapers, datasets, academic studies, legal filings, government reports, or foundational books mentioned in the text.
   - For EACH sighting you discover, you MUST invoke the `record_fleet_sighting` tool:
     `record_fleet_sighting(source_cargo_id={cargo['id']}, source_title="{cargo['title'].replace('"', '')}", sighted_title=..., source_type=..., url_or_locator=..., context_quote=...)`
3. Write your complete extraction deliverable to: `writings/cargo/cargo_{cargo['id']}/grog_extraction.md` using `write_local_file`.
4. Call `log_fleet_enrichment` with agent_name="grog", enrichment_type="cargo_intake_turn3", and summary payload.
5. Summarize your straight summary and list all sightings recorded.
"""
    try:
        session3 = grog.start_chat_session(thread_id)
        resp3 = grog.execute_turn(session3, turn3_prompt)
        grog.save_checkpoint(thread_id, session3.get_history())
        pipeline_result["turns_completed"].append("grog")
        print(f"[TURN 3 COMPLETE] Grog response:\n{resp3[:400]}...\n")
    finally:
        grog.close()

    pipeline_result["status"] = "COMPLETED"
    print("\n" + "=" * 70)
    print(f" PIPELINE COMPLETED FOR cargo_{metadata_id}")
    print(f" CHAPTER ANCHOR: {primary_chapter}")
    print(f" FINAL LOCKER:   {sail_locker}")
    print(f" DOSSIERS:       writings/cargo/cargo_{metadata_id}/")
    print("=" * 70)
    return pipeline_result


# Backward compatibility alias
run_cargo_intake = run_cargo_triage


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Cargo Triage & Preprocessing (Level 2)")
    parser.add_argument("--metadata-id", "-id", type=int, default=None, help="Cargo metadata ID to process")
    parser.add_argument("--force", action="store_true", help="Force Turns 2 and 3 even if placed in Doldrums")
    parser.add_argument("--model", type=str, default=None, help="Optional model override (defaults to DEFAULT_MODEL)")
    args = parser.parse_args()

    if not args.metadata_id:
        print("[ERROR] Please provide --metadata-id <ID>.")
        sys.exit(1)

    result = run_cargo_triage(
        metadata_id=args.metadata_id,
        force_turn2_3=args.force,
        model_override=args.model
    )
    print("\nResult:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
