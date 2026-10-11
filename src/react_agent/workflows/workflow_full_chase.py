"""
NPT Fleet: The Master Sail Plan - Workflow Full Chase (Level 3: Full Press of Sail)
Architecture: Unified Multi-Agent Synthesis Pipeline with Prepopulation Fast-Forward
Execution Order:
  Level 2 Check:
    Inspects writings/cargo/cargo_{metadata_id}/.
    If bilgeladle_alignment.md, cutlass_audit.md, grog_extraction.md exist,
    FAST-FORWARDS with zero LLM re-computation!
    If absent, executes workflow_cargo_triage (Bilgeladle -> Cutlass -> Grog).
  Turn 4 - SCALLYWAG: Consumes the 3 cargo dossiers + author inquiry prompt to author
                      a cynical, unvarnished synthesis essay anchored in verbatim chapter quotes.
                      Writes writings/chases/{chase_id}/stage5_scallywag_essay.md.
  Turn 5 - PEER REVIEWS: Bilgeladle and Cutlass independently audit Scallywag's essay
                         for quote accuracy and argumentative rigor.
                         Writes writings/chases/{chase_id}/stage6_peer_reviews.md.
"""

import os
import sys
import json
import shutil
import argparse
from typing import Optional, Dict, Any, List

# Ensure react_agent root is on sys.path
AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_ROOT = os.path.abspath(os.path.join(AGENT_ROOT, "..", ".."))
if AGENT_ROOT not in sys.path:
    sys.path.insert(0, AGENT_ROOT)

from core.agent_engine import AgentEngine
from tools.cargo_db_tools import log_fleet_enrichment
from workflows.workflow_cargo_triage import run_cargo_triage, get_cargo_metadata


def run_full_chase(
    metadata_id: int,
    prompt: str,
    chase_id: str,
    model_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the Level 3 Full Chase Workflow.
    Fast-forwards if cargo dossiers are already prepopulated by Level 2 Triage.
    """
    cargo = get_cargo_metadata(metadata_id)
    if not cargo:
        return {"status": "ERROR", "message": f"Cargo asset id={metadata_id} not found."}

    chase_clean = chase_id.strip()
    chase_dir = os.path.join(WORKSPACE_ROOT, "writings", "chases", chase_clean)
    os.makedirs(chase_dir, exist_ok=True)

    cargo_dir = os.path.join(WORKSPACE_ROOT, "writings", "cargo", f"cargo_{metadata_id}")
    aln_path = os.path.join(cargo_dir, "bilgeladle_alignment.md")
    aud_path = os.path.join(cargo_dir, "cutlass_audit.md")
    ext_path = os.path.join(cargo_dir, "grog_extraction.md")

    print("\n" + "=" * 70)
    print(f" NPT FLEET: WORKFLOW FULL CHASE ({chase_clean})")
    print(f" ASSET: cargo_{metadata_id} ({cargo['title']})")
    print(f" PROMPT: {prompt}")
    print(f" SINK:  {chase_dir}")
    print("=" * 70)

    # =========================================================================
    # STEP 1: CHECK OR RUN LEVEL 2 PREPOPULATION (BILGELADLE -> CUTLASS -> GROG)
    # =========================================================================
    dossiers_exist = os.path.isfile(aln_path) and os.path.isfile(aud_path) and os.path.isfile(ext_path)

    if dossiers_exist:
        print(f"\n>>> [CHASE FAST-FORWARD] Reusable dossiers detected in writings/cargo/cargo_{metadata_id}/.")
        print("    -> Level 2 dossiers verified: Bilgeladle Alignment, Cutlass Audit, Grog Extraction.")
        print("    -> Fast-forwarding directly to Scallywag with ZERO duplicate token spend!")
    else:
        print(f"\n>>> [CHASE LEVEL 2] Dossiers missing or incomplete. Running workflow_cargo_triage first...")
        triage_res = run_cargo_triage(metadata_id=metadata_id, model_override=model_override)
        if triage_res.get("status") == "HALTED_DOLDRUMS":
            print(f"\n[CHASE HALT] Asset cargo_{metadata_id} placed in DOLDRUMS. Chase cannot proceed without Author calibration.")
            return {
                "status": "HALTED_DOLDRUMS",
                "message": "Asset requires human triage calibration in the Triage Console before Full Chase can run.",
                "chase_id": chase_clean,
                "metadata_id": metadata_id
            }

    # Stage dossiers into chase directory
    stg2_aln = os.path.join(chase_dir, "stage2_bilgeladle_alignment.md")
    stg3_aud = os.path.join(chase_dir, "stage3_cutlass_audit.md")
    stg4_ext = os.path.join(chase_dir, "stage4_grog_extraction.md")

    if os.path.isfile(aln_path):
        shutil.copy2(aln_path, stg2_aln)
    if os.path.isfile(aud_path):
        shutil.copy2(aud_path, stg3_aud)
    if os.path.isfile(ext_path):
        shutil.copy2(ext_path, stg4_ext)

    # Read dossiers for context
    with open(aln_path, "r", encoding="utf-8", errors="replace") as f:
        bilge_text = f.read()
    with open(aud_path, "r", encoding="utf-8", errors="replace") as f:
        cutlass_text = f.read()
    with open(ext_path, "r", encoding="utf-8", errors="replace") as f:
        grog_text = f.read()

    # =========================================================================
    # STEP 2: STAGE 0 - PEGLEG (Prompt Refinement & Forensic Brief)
    # =========================================================================
    print(f"\n>>> [STAGE 0: PEGLEG] Deconstructing prompt and preparing Forensic Brief...")
    xml_dir = os.path.join(AGENT_ROOT, "agents")
    pegleg_xml = os.path.join(xml_dir, "pegleg", "pegleg.xml")
    pegleg = AgentEngine("pegleg", xml_profile_path=pegleg_xml, model_override=model_override)
    pegleg_thread = f"thread_pegleg_{chase_clean}"
    brief_path = os.path.join(chase_dir, "stage0_forensic_brief.md")

    stage0_prompt = f"""
You are PEGLEG executing Stage 0 (Architectural Briefing & Prompt Inquest) for Full Chase {chase_clean}.
RAW AUTHOR INQUIRY:
"{prompt}"

ASSET CONTEXT:
ID: {cargo['id']}
Title: {cargo['title']}
Bilgeladle Alignment Summary: {bilge_text[:800]}

MANDATE (SOCRATIC COACH & PROMPT ARCHITECT POSTURE):
You have NO domain knowledge of the manuscript (*The End of Knowing*) and MUST NOT guess chapter ribs (that is strictly Bilgeladle's domain in Stage 2). Instead, you protect the cognitive horsepower of the downstream synthesis engine (Scallywag), who holds dual doctorates in philosophy and psychology.
1. Socratic Interrogation & Elevation: Decouple surface requests or potential listicle traps from the deep causal or philosophical core being tested.
2. Scope & Rules of Engagement: Define explicit boundaries, valid evidence standards, and mandatory causal Toulmin warrants.
3. Formulate a rigorous Forensic Brief for Scallywag, establishing:
   - Refined Causal / Epistemological Inquest
   - Scope & Demarcation Boundaries
   - Rules of Engagement (mandatory causal Toulmin warrants, anti-listicle standards)
4. Write your deliverable directly to: `{brief_path.replace(chr(92), '/')}` using `write_local_file`.
"""
    try:
        session0 = pegleg.start_chat_session(pegleg_thread)
        brief_resp = pegleg.execute_turn(session0, stage0_prompt)
        pegleg.save_checkpoint(pegleg_thread, session0.get_history())
        print(f"[STAGE 0 COMPLETE] Forensic Brief drafted:\n{brief_resp[:300]}...\n")
    finally:
        pegleg.close()

    brief_content = ""
    if os.path.isfile(brief_path):
        with open(brief_path, "r", encoding="utf-8", errors="replace") as bf:
            brief_content = bf.read()
    else:
        brief_content = brief_resp

    # =========================================================================
    # STEP 3: TURN 4 - SCALLYWAG (Satirical Synthesis Essay)
    # =========================================================================
    print(f"\n>>> [TURN 4: SCALLYWAG] Authoring satirical synthesis essay for chase {chase_clean}...")
    scallywag_xml = os.path.join(xml_dir, "scallywag", "scallywag.xml")
    scallywag = AgentEngine("scallywag", xml_profile_path=scallywag_xml, model_override=model_override)

    scallywag_thread = f"thread_scallywag_{chase_clean}"
    essay_path = os.path.join(chase_dir, "stage5_scallywag_essay.md")

    turn4_prompt = f"""
You are executing Turn 4 (The Satirical Synthesis Essay) of the Full Chase ({chase_clean}) for cargo asset id={cargo['id']}.

STAGE 0 FORENSIC BRIEF:
{brief_content}

CHASE INQUIRY / AUTHOR PROMPT:
"{prompt}"

PREPOPULATED ASSET DOSSIERS:
--- BILGELADLE THESIS ALIGNMENT ---
{bilge_text}

--- CUTLASS EPISTEMIC AUDIT ---
{cutlass_text}

--- GROG OBJECTIVE EXTRACTION ---
{grog_text}

INSTRUCTIONS:
1. Review the intellectual context established by Bilgeladle, the forensic logic targets identified by Cutlass, and the objective facts extracted by Grog.
2. If Bilgeladle locked a Primary Chapter Anchor, call `read_manuscript_chapter(chapter_number)` to load verbatim prose and quotes from *The End of Knowing*.
3. Author a formidable, razor-sharp synthesis essay answering the Author's inquiry prompt:
   - Target individual human agency, misanthropes, and proactive negligence (never reify institutions or blame algorithms).
   - Anchor your polemic in textual quotes from the manuscript and empirical facts from the cargo.
   - Do NOT produce a superficial listicle or token-wasting URL dump. Every claim must have a rigorous Toulmin warrant.
   - Channel cynicism into surgical philosophical dissection.
4. Write your completed essay directly to: `{essay_path.replace(chr(92), '/')}` using `write_local_file`.
5. Call `log_fleet_enrichment` with agent_name="scallywag", enrichment_type="chase_stage5_essay", and metadata_id={cargo['id']}.
6. Provide a summary of your essay thesis and anchor quotes.
"""
    try:
        session4 = scallywag.start_chat_session(scallywag_thread)
        resp4 = scallywag.execute_turn(session4, turn4_prompt)
        scallywag.save_checkpoint(scallywag_thread, session4.get_history())
        print(f"[TURN 4 COMPLETE] Scallywag response:\n{resp4[:400]}...\n")
    finally:
        scallywag.close()

    # =========================================================================
    # STEP 4: TURN 5 - ADVERSARIAL PEER REVIEWS (Bilgeladle, Cutlass, Grog)
    # =========================================================================
    print(f"\n>>> [TURN 5: ADVERSARIAL PEER REVIEWS] Conducting independent reviews across 3 specialists...")
    review_path = os.path.join(chase_dir, "stage6_peer_reviews.md")
    b_review_path = os.path.join(chase_dir, "stage6_bilgeladle_review.md")
    c_review_path = os.path.join(chase_dir, "stage6_cutlass_review.md")
    g_review_path = os.path.join(chase_dir, "stage6_grog_review.md")

    # Read Scallywag's essay
    essay_content = ""
    if os.path.isfile(essay_path):
        with open(essay_path, "r", encoding="utf-8", errors="replace") as ef:
            essay_content = ef.read()

    # 1. Bilgeladle Peer Review
    bilgeladle_xml = os.path.join(xml_dir, "bilgeladle", "bilgeladle.xml")
    bilgeladle = AgentEngine("bilgeladle", xml_profile_path=bilgeladle_xml, model_override=model_override)
    b_review_thread = f"thread_bilgeladle_review_{chase_clean}"
    b_review_prompt = f"""
Conduct an Adversarial Thesis Peer Review of Scallywag's draft essay for Full Chase {chase_clean}:
ESSAY:
{essay_content}

VERIFICATION MANDATE:
1. Verify verbatim fidelity of all manuscript quotes against *The End of Knowing*.
2. Verify alignment to the Primary Chapter Anchor and Section Ribs (audit for cosmetic name-dropping vs authentic integration of chapter mechanics).
3. Score strictly on the universal 0.0 to 10.0 Epistemic Signal Scale (pass >= 8.0 / 10.0; 100-point scale is banned).
4. Issue a formal verdict: APPROVED or REJECTED_FOR_REVISION.
Format scorecard as:
## Forensic Scorecard (0.0 – 10.0)
- Score: [X.X] / 10.0
- Verdict: [APPROVED | REJECTED_FOR_REVISION]
- Chapter Anchor Fidelity: [Assessment]
"""
    try:
        session_b = bilgeladle.start_chat_session(b_review_thread)
        b_review_text = bilgeladle.execute_turn(session_b, b_review_prompt)
        bilgeladle.save_checkpoint(b_review_thread, session_b.get_history())
        with open(b_review_path, "w", encoding="utf-8") as bf:
            bf.write(b_review_text)
    finally:
        bilgeladle.close()

    # 2. Cutlass Peer Review
    cutlass_xml = os.path.join(xml_dir, "cutlass", "cutlass.xml")
    cutlass = AgentEngine("cutlass", xml_profile_path=cutlass_xml, model_override=model_override)
    c_review_thread = f"thread_cutlass_review_{chase_clean}"
    c_review_prompt = f"""
Conduct an Adversarial Epistemic Peer Review of Scallywag's draft essay for Full Chase {chase_clean}:
ESSAY:
{essay_content}

VERIFICATION MANDATE:
1. Epistemic Rigor & Anti-Slop: Audit for intellectual laziness, superficial listicles, token-wasting URL dumps, and missing Toulmin warrants.
2. Popperian Demarcation: Verify empirical grounding against seized facts without unfalsifiable hand-waving.
3. Score strictly on the universal 0.0 to 10.0 Epistemic Signal Scale (pass >= 8.0 / 10.0).
4. Issue a formal verdict: APPROVED or REJECTED_FOR_REVISION.
Format scorecard as:
## Forensic Scorecard (0.0 – 10.0)
- Score: [X.X] / 10.0
- Verdict: [APPROVED | REJECTED_FOR_REVISION]
- Logic & Demarcation Assessment: [Assessment]
"""
    try:
        session_c = cutlass.start_chat_session(c_review_thread)
        c_review_text = cutlass.execute_turn(session_c, c_review_prompt)
        cutlass.save_checkpoint(c_review_thread, session_c.get_history())
        with open(c_review_path, "w", encoding="utf-8") as cf:
            cf.write(c_review_text)
    finally:
        cutlass.close()

    # 3. Grog Peer Review (Cargo Meaning Preservation)
    grog_xml = os.path.join(xml_dir, "grog", "grog.xml")
    grog = AgentEngine("grog", xml_profile_path=grog_xml, model_override=model_override)
    g_review_thread = f"thread_grog_review_{chase_clean}"
    g_review_prompt = f"""
Conduct an Objective Cargo Meaning Preservation Peer Review of Scallywag's draft essay for Full Chase {chase_clean}:
ESSAY:
{essay_content}

CARGO ASSET DOSSIER SUMMARY:
{grog_text[:1500]}

VERIFICATION MANDATE (GROG-RULE-008):
1. Inquest: "Does Scallywag accurately represent the cargo asset's meaning?"
2. Meaning Preservation: Did Scallywag distort, exaggerate, caricature, or confabulate claims not supported by the seized cargo asset, or was the asset's meaning preserved with factual fidelity?
3. Firewall: Do NOT check or score external bibliographic citations (Plank's remit).
4. Score strictly on the universal 0.0 to 10.0 Epistemic Signal Scale (pass >= 8.0 / 10.0).
5. Issue a formal verdict: APPROVED or REJECTED_FOR_REVISION.
Format scorecard as:
## Forensic Scorecard (0.0 – 10.0)
- Score: [X.X] / 10.0
- Verdict: [APPROVED | REJECTED_FOR_REVISION]
- Cargo Meaning Fidelity: [Assessment]
"""
    try:
        session_g = grog.start_chat_session(g_review_thread)
        g_review_text = grog.execute_turn(session_g, g_review_prompt)
        grog.save_checkpoint(g_review_thread, session_g.get_history())
        with open(g_review_path, "w", encoding="utf-8") as gf:
            gf.write(g_review_text)
    finally:
        grog.close()

    # Assemble and write final peer reviews file
    combined_reviews = f"""# Full Chase Peer Review Consensus: {chase_clean}
**Asset**: cargo_{metadata_id} ({cargo['title']})

---

## 1. Bilgeladle Thesis & Textual Veracity Review
{b_review_text}

---

## 2. Cutlass Epistemic & Evidentiary Rigor Review
{c_review_text}

---

## 3. Grog Cargo Meaning Preservation Review
{g_review_text}
"""
    with open(review_path, "w", encoding="utf-8") as rf:
        rf.write(combined_reviews)

    # =========================================================================
    # STEP 5: STAGE 5B - SCALLYWAG REVISION TURN (IF REVISION REQUIRED)
    # =========================================================================
    all_reviews_text = (b_review_text + "\n" + c_review_text + "\n" + g_review_text).lower()
    needs_revision = "rejected" in all_reviews_text or "revision required" in all_reviews_text

    # Check for scores below 8.0
    import re
    scores = re.findall(r"score:\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10", all_reviews_text)
    for s_str in scores:
        try:
            if float(s_str) < 8.0:
                needs_revision = True
                break
        except ValueError:
            pass

    if needs_revision:
        print(f"\n>>> [STAGE 5B: SCALLYWAG REVISION] Adversarial gate tripped (< 8.0 or REJECTED). Dispatching revision turn...")
        revision_prompt = f"""
COMMAND: Execute Stage 5B Adversarial Revision Turn for Full Chase {chase_clean}.
The Team of Rivals has audited your draft essay and identified intellectual shortcomings:

BILGELADLE REVIEW:
{b_review_text}

CUTLASS REVIEW:
{c_review_text}

GROG REVIEW:
{g_review_text}

REVISION MANDATE:
1. Address every specific critique: eliminate superficial listicle enumerations, anchor deeply to the primary chapter's causal mechanics, and ensure exact factual fidelity to the cargo asset.
2. Rewrite `stage5_scallywag_essay.md` to resolve all friction points.
3. Write your revised deliverable directly to: `{essay_path.replace(chr(92), '/')}` using `write_local_file`.
"""
        try:
            scallywag_rev = AgentEngine("scallywag", xml_profile_path=scallywag_xml, model_override=model_override)
            session_rev = scallywag_rev.start_chat_session(scallywag_thread)
            resp_rev = scallywag_rev.execute_turn(session_rev, revision_prompt)
            scallywag_rev.save_checkpoint(scallywag_thread, session_rev.get_history())
            print(f"[STAGE 5B COMPLETE] Scallywag revised essay:\n{resp_rev[:300]}...\n")
        finally:
            scallywag_rev.close()

    # Status tracking
    status_path = os.path.join(chase_dir, "chase_status.md")
    status_content = f"""# Chase Execution Status: {chase_clean}
- **Status**: COMPLETED
- **Cargo Asset**: cargo_{metadata_id}
- **Title**: {cargo['title']}
- **Inquiry Prompt**: {prompt}
- **Deliverables**:
  - `stage0_forensic_brief.md`: Pegleg Architectural Prompt Inquest
  - `stage2_bilgeladle_alignment.md`: Primary Chapter Anchor locked
  - `stage3_cutlass_audit.md`: Epistemic Scorecard & Sail Locker
  - `stage4_grog_extraction.md`: Objective facts & sightings
  - `stage5_scallywag_essay.md`: Satirical synthesis essay
  - `stage6_bilgeladle_review.md`: Thesis & chapter anchor review
  - `stage6_cutlass_review.md`: Logic, demarcation & anti-slop review
  - `stage6_grog_review.md`: Cargo meaning preservation review
  - `stage6_peer_reviews.md`: Consolidated Team of Rivals consensus
"""
    with open(status_path, "w", encoding="utf-8") as sf:
        sf.write(status_content)

    print("\n" + "=" * 70)
    print(f" FULL CHASE COMPLETED: {chase_clean}")
    print(f" BRIEF DELIVERABLE: {brief_path}")
    print(f" ESSAY DELIVERABLE: {essay_path}")
    print(f" REVIEWS DELIVERABLE: {review_path}")
    print(f" CHASE PACKAGE: {chase_dir}")
    print("=" * 70)

    return {
        "status": "COMPLETED",
        "chase_id": chase_clean,
        "metadata_id": metadata_id,
        "brief_path": brief_path,
        "essay_path": essay_path,
        "review_path": review_path,
        "chase_dir": chase_dir
    }


def main():
    parser = argparse.ArgumentParser(description="NPT Fleet: Workflow Full Chase (Level 3)")
    parser.add_argument("--metadata-id", "-id", type=int, required=True, help="Cargo metadata ID")
    parser.add_argument("--prompt", "-p", type=str, required=True, help="Author inquiry / synthesis prompt")
    parser.add_argument("--chase-id", "-c", type=str, required=True, help="Chase identifier (e.g. chase-sept-23-rot)")
    parser.add_argument("--model", type=str, default=None, help="Optional model override")
    args = parser.parse_args()

    result = run_full_chase(
        metadata_id=args.metadata_id,
        prompt=args.prompt,
        chase_id=args.chase_id,
        model_override=args.model
    )
    print("\nResult:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
