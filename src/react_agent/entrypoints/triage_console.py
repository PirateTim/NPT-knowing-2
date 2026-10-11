"""
NPT Fleet: Cutlass Rapid Triage & Sail Locker Calibration Console
Streamlit Web Application for zero-token asset inspection, batch fast-triage, and human-in-the-loop learning.
"""

import os
import sys
import re
import json
import datetime
import urllib.parse
from typing import List, Dict, Any, Optional

import streamlit as st
import pg8000.dbapi
from dotenv import load_dotenv

# Set project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

from tools.cloud_knowledge_tools import read_knowledge_artifact
from tools.cargo_db_tools import (
    _get_strict_cargo_connection,
    purge_corrupted_cargo,
    list_fleet_sightings,
    promote_sighting_to_queue
)
from tools.memory_tools import record_learned_rule
from workflows.cargo_intake_pipeline import run_cargo_intake

# Page configuration
st.set_page_config(
    page_title="Cutlass Triage Console | NPT Fleet",
    page_icon="⛵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-signal readability and mobile responsiveness
st.markdown("""
<style>
    .badge-mainsail {
        background-color: #1b5e20; color: #e8f5e9; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-bilge {
        background-color: #b71c1c; color: #ffebee; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-jib {
        background-color: #0d47a1; color: #e3f2fd; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-doldrums {
        background-color: #f57f17; color: #fffde7; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-flotsam {
        background-color: #4a148c; color: #f3e5f5; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-wherry {
        background-color: #00695c; color: #e0f2f1; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-untriaged {
        background-color: #424242; color: #eeeeee; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .badge-reacquiring {
        background-color: #e65100; color: #fff3e0; padding: 4px 10px; border-radius: 4px; font-weight: bold;
    }
    .triage-card {
        background-color: #1a1c24; border: 1px solid #2d3139; border-radius: 8px; padding: 15px; margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# DATABASE QUERIES & DATA RETRIEVAL
# =====================================================================

def fetch_all_cargo_with_triage() -> List[Dict[str, Any]]:
    """
    Fetches all content metadata records alongside their latest Cutlass triage enrichment.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        st.error("Failed to connect to Cargo Database. Verify CONTENT_DATABASE_URL in .env.")
        return []

    query = """
        SELECT DISTINCT ON (cm.id)
            cm.id,
            cm.title,
            cm.source_url,
            cm.item_type,
            cm.publication_title,
            cm.publication_date,
            cm.gcp_bucket_path,
            cm.created_at,
            fe.payload ->> 'sail_locker' AS sail_locker,
            fe.payload ->> 'confidence' AS confidence,
            fe.payload ->> 'author_intent_hypothesis' AS hypothesis,
            fe.payload ->> 'key_warrant_quote' AS warrant,
            fe.payload ->> 'epistemic_integrity_overview' AS overview,
            fe.payload ->> 'dossier_path' AS dossier_path,
            fe.payload AS full_payload,
            fe.created_at AS triaged_at,
            iq.status AS queue_status,
            reacq.id AS reacq_id,
            reacq.payload ->> 'reason' AS reacq_reason
        FROM cargo.content_metadata cm
        LEFT JOIN cargo.fleet_enrichments fe 
            ON cm.id = fe.metadata_id 
            AND fe.agent_name IN ('cutlass', 'author', 'cutlass_calibrated', 'bilgeladle')
            AND fe.enrichment_type IN ('triage', 'triage_quick', 'triage_human_override', 'triage_full_audit', 'cargo_intake_turn1')
        LEFT JOIN cargo.ingestion_queue iq
            ON cm.source_url = iq.target_url
        LEFT JOIN LATERAL (
            SELECT id, payload FROM cargo.fleet_enrichments
            WHERE metadata_id = cm.id AND enrichment_type = 'spyglass_reacquire_request'
            ORDER BY created_at DESC LIMIT 1
        ) reacq ON TRUE
        ORDER BY cm.id, fe.created_at DESC;
    """
    items = []
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            (mid, title, url, itype, pub_title, pub_date, bucket_path, created_at,
             locker, conf, hyp, warrant, overview, dossier_path, full_payload, triaged_at,
             queue_status, reacq_id, reacq_reason) = r

            # Check for active re-acquisition state:
            # If an explicit re-acquisition request is active and the queue is either pending/processing,
            # this asset is in Spyglass's court and must NOT be visible to Cutlass untriaged.
            is_reacquiring = (reacq_id is not None) and (queue_status in ('PENDING', 'PROCESSING') or queue_status is None)
            is_reacquire_failed = (reacq_id is not None) and (queue_status == 'FAILED')

            assigned_locker = (locker or "").upper().strip()
            if is_reacquiring:
                status = "REACQUIRING"
            elif is_reacquire_failed:
                status = "DOLDRUMS"
            elif not assigned_locker:
                status = "UNTRIAGED"
            elif assigned_locker in ("MAINSAIL", "BILGE", "JIB", "DOLDRUMS", "FLOTSAM", "WHERRY"):
                status = assigned_locker
            else:
                status = "DOLDRUMS"

            # Parse hypothesis or fallback
            if is_reacquiring:
                rationale_text = f"🔄 [PENDING SPYGLASS RE-ACQUISITION] Queued for re-download. Reason: {reacq_reason or 'Defective/incomplete content.'}"
            elif is_reacquire_failed:
                rationale_text = f"⚠️ [RE-ACQUISITION FAILED] Spyglass was unable to re-acquire this asset. Consider Dead-Lettering."
            else:
                rationale_text = hyp or overview or ""
                if not rationale_text and isinstance(full_payload, dict):
                    rationale_text = full_payload.get("rationale") or full_payload.get("author_intent_hypothesis") or ""

            parsed_payload = full_payload if isinstance(full_payload, dict) else {}
            if not parsed_payload and isinstance(full_payload, str) and full_payload.startswith("{"):
                try:
                    parsed_payload = json.loads(full_payload)
                except Exception:
                    parsed_payload = {}

            items.append({
                "id": mid,
                "title": title or "Untitled Cargo",
                "source_url": url,
                "item_type": itype or "webpage",
                "publication_title": pub_title or "",
                "publication_date": pub_date or "",
                "gcp_bucket_path": bucket_path or "",
                "created_at": created_at,
                "sail_locker": status,
                "confidence": conf or "N/A",
                "rationale": rationale_text,
                "warrant": warrant or "",
                "dossier_path": dossier_path or "",
                "full_payload": parsed_payload,
                "triaged_at": triaged_at
            })
        cursor.close()
    except Exception as e:
        st.error(f"Error fetching cargo records: {str(e)}")
    finally:
        conn.close()

    return items


@st.cache_data(show_spinner=False, ttl=300)
def get_cached_raw_content(gcp_bucket_path: str) -> str:
    """Reads verbatim text directly from GCS (zero LLM token cost)."""
    if not gcp_bucket_path:
        return "[No GCS bucket path recorded for this asset.]"
    text = read_knowledge_artifact(gcp_bucket_path)
    return text


def _format_dialectical_learning(learning_note: str, new_locker: str, asset_title: str, gcp_bucket_path: str) -> Dict[str, str]:
    """
    Constructs a calibrated, non-absolutist learned rule directive.
    Strictly forbids 'must', 'always', 'never', 'ignore', 'dismiss' in machine-generated
    text unless the Author explicitly authored those words in learning_note.
    Uses dialectical framing: 'consider', 'might be', 'focus on', 'is related to'.
    """
    clean_note = learning_note.strip()
    
    # Check if Author deliberately used any absolutist words
    author_used_absolutist = any(
        re.search(rf"\b{word}\b", clean_note, re.IGNORECASE)
        for word in ["must", "always", "never", "ignore", "dismiss"]
    )
    
    # Format the machine directive using dialectical phrasing
    if clean_note:
        rule_text = (
            f"Sail Locker Calibration ({new_locker}): When reviewing assets similar to '{asset_title}', "
            f"consider that this material is related to {new_locker}. Focus on: {clean_note}"
        )
    else:
        rule_text = (
            f"Sail Locker Calibration ({new_locker}): Consider that assets similar to '{asset_title}' "
            f"might be oriented toward {new_locker} rather than Doldrums."
        )
        
    # Safety assertion: machine text must not introduce banned words
    if not author_used_absolutist:
        for banned in ["must", "always", "never", "ignore", "dismiss"]:
            if banned.lower() not in clean_note.lower():
                pattern = re.compile(rf"\b{banned}\b", re.IGNORECASE)
                rule_text = pattern.sub("consider", rule_text)

    return {
        "rule_directive": rule_text,
        "source_context": f"Author Triage Calibration on {gcp_bucket_path} ({datetime.date.today().isoformat()})"
    }


def record_human_reclassification(metadata_id: int, gcp_bucket_path: str, new_locker: str, learning_note: str, asset_title: str) -> bool:
    """
    Commits an Author human override to cargo.fleet_enrichments and records a calibrated dialectical
    learned rule in both Cutlass's and Bilgeladle's learned_rules.json memory vaults.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        st.error("Database connection unavailable.")
        return False

    try:
        cursor = conn.cursor()
        payload = {
            "sail_locker": new_locker,
            "confidence": 5,
            "author_intent_hypothesis": learning_note or "Manual Author reclassification via Triage Console.",
            "reclassified_by": "Author",
            "timestamp": datetime.datetime.now().isoformat()
        }
        cursor.execute(
            """
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, 'author', 'triage_human_override', %s, NOW());
            """,
            (metadata_id, json.dumps(payload))
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Update Cutlass and Bilgeladle learned_rules.json memory vaults
        if learning_note.strip():
            new_rule = _format_dialectical_learning(learning_note, new_locker, asset_title, gcp_bucket_path)
            for agent_name in ["cutlass", "bilgeladle"]:
                rules_path = os.path.abspath(f"src/react_agent/agents/{agent_name}/learned_rules.json")
                if os.path.exists(rules_path):
                    try:
                        with open(rules_path, "r", encoding="utf-8") as f:
                            rules_data = json.load(f)
                        rules_data.append(new_rule)
                        with open(rules_path, "w", encoding="utf-8") as f:
                            json.dump(rules_data, f, indent=4)
                    except Exception as le:
                        print(f"[WARNING] Failed to update {agent_name} learned_rules.json: {le}")

        return True
    except Exception as e:
        st.error(f"Failed to record reclassification: {str(e)}")
        if conn: conn.close()
        return False


def push_back_to_spyglass(metadata_id: int, source_url: str, reason: str = "") -> bool:
    """
    Re-enqueues an asset into cargo.ingestion_queue for Spyglass to re-acquire with fresh tools.
    Also logs a triage enrichment event recording the pushback.
    """
    conn = _get_strict_cargo_connection()
    if not conn:
        st.error("Database connection unavailable.")
        return False

    try:
        cursor = conn.cursor()
        
        # 1. Insert or reset status in cargo.ingestion_queue
        cursor.execute(
            """
            INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor, added_at, attempt_count)
            VALUES (%s, 'PENDING', 'triage_console_reacquire', NOW(), 0)
            ON CONFLICT (target_url) DO UPDATE SET
                status = 'PENDING',
                attempt_count = 0,
                last_attempted_at = NULL;
            """,
            (source_url,)
        )

        # 2. Reset triage status by clearing previous triage enrichments so it becomes UNTRIAGED
        cursor.execute(
            """
            DELETE FROM cargo.fleet_enrichments 
            WHERE metadata_id = %s 
              AND enrichment_type IN ('triage', 'triage_quick', 'triage_human_override', 'triage_full_audit', 'spyglass_reacquire_request');
            """,
            (metadata_id,)
        )

        # 3. Record enrichment documenting the re-acquisition request
        payload = {
            "action": "PUSH_BACK_TO_SPYGLASS",
            "reason": reason or "Pushed back to Spyglass for re-acquisition (defective/incomplete content).",
            "timestamp": datetime.datetime.now().isoformat()
        }
        cursor.execute(
            """
            INSERT INTO cargo.fleet_enrichments (metadata_id, agent_name, enrichment_type, payload, created_at)
            VALUES (%s, 'author', 'spyglass_reacquire_request', %s, NOW());
            """,
            (metadata_id, json.dumps(payload))
        )

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to push back to Spyglass: {str(e)}")
        if conn: conn.close()
        return False


def send_to_dead_letter_queue(metadata_id: int, source_url: str, reason: str = "") -> bool:
    """
    Executes Option A Ingestion Remediation:
    1. Permanently logs the unacquirable URL to cargo.failed_metadata with the failure reason.
    2. Incinerates any truncated/paywall stub from the GCS bucket.
    3. Deletes foreign keys and removes the record from cargo.content_metadata and cargo.ingestion_queue.
    (Does NOT mislabel unreached content as FLOTSAM).
    """
    try:
        err_msg = reason.strip() or "[MANUAL_DEAD_LETTER] Author flagged asset as unacquirable (commercial paywall/broken)."
        res = purge_corrupted_cargo(source_url=source_url, failure_reason=err_msg)
        if res.startswith("[ERROR]"):
            st.error(res)
            return False
        return True
    except Exception as e:
        st.error(f"Failed to record dead-letter: {str(e)}")
        return False


def run_batch_triage_job(asset_list: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    """
    Invokes Cutlass on untriaged assets using the rapid-locker-triage skill and returns the detailed responses.
    """
    from core.agent_engine import AgentEngine

    xml_path = os.path.abspath("src/react_agent/agents/cutlass/cutlass.xml")
    engine = AgentEngine(agent_name="cutlass", xml_profile_path=xml_path)

    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []
    targets = asset_list[:count]

    for i, asset in enumerate(targets):
        bucket_path = asset["gcp_bucket_path"]
        title = asset["title"]
        status_text.markdown(f"**⚡ Cutlass Triaging ({i+1}/{len(targets)}):** `{title[:50]}...`")

        prompt = (
            f"Execute the rapid-locker-triage skill on the following asset:\n"
            f"Asset Path: {bucket_path}\n"
            f"Asset Title: {title}\n"
            f"Read the asset, determine the Author's acquisition intent, assign a Sail Locker "
            f"(MAINSAIL, BILGE, JIB, or DOLDRUMS if confidence < 4), log to fleet_enrichments, and report."
        )

        thread_id = f"thread_cargo_{asset['id']}"
        chat_session = engine.start_chat_session(thread_id)

        try:
            response_text = engine.execute_turn(chat_session, prompt)
            results.append({
                "id": asset["id"],
                "title": title,
                "gcp_bucket_path": bucket_path,
                "source_url": asset.get("source_url", ""),
                "response": response_text
            })
        except Exception as e:
            st.warning(f"Error triaging {title}: {str(e)}")

        progress_bar.progress((i + 1) / len(targets))

    status_text.success(f"Batch Triage Complete! Processed {len(results)} assets.")
    st.cache_data.clear()
    return results


def run_full_audit_for_asset(asset: Dict[str, Any], target_locker: str = "", learning_note: str = "") -> Optional[str]:
    """
    Executes Cutlass's full 6-section Structural Logic Audit on a single asset,
    writes writings/cargo/cargo_{metadata_id}/cutlass_audit.md, and synchronizes the
    authoritative Sail Locker with PostgreSQL.
    Re-awakens the persistent thread `cargo_{metadata_id}_cutlass` so prior context is reused.
    """
    from core.agent_engine import AgentEngine

    xml_path = os.path.abspath("src/react_agent/agents/cutlass/cutlass.xml")
    engine = AgentEngine(agent_name="cutlass", xml_profile_path=xml_path)

    bucket_path = asset["gcp_bucket_path"]
    meta_id = asset["id"]
    title = asset["title"]

    dossier_dir = os.path.abspath(os.path.join("writings", "cargo", f"cargo_{meta_id}"))
    os.makedirs(dossier_dir, exist_ok=True)
    rel_dossier_path = f"writings/cargo/cargo_{meta_id}/cutlass_audit.md"

    prompt = (
        f"COMMAND: Execute Stage 2 Epistemic & Structural Logic Audit for Asset: {bucket_path}\n"
        f"CARGO ID: cargo_{meta_id}\n"
        f"ASSET TITLE: {title}\n"
    )
    if target_locker.strip():
        prompt += f"AUTHOR ASSIGNED SAIL LOCKER: {target_locker.strip()}\n"
    if learning_note.strip():
        prompt += f"AUTHOR GUIDANCE / RATIONALE: {learning_note.strip()}\n"

    pub_title = asset.get("publication_title", "")
    pub_date = asset.get("publication_date", "")

    prompt += (
        f"\nMANDATORY INSTRUCTIONS (THE 4-SECTION FORENSIC LEDGER):\n"
        f"1. Execute `epistemic-value-audit`, `logic-audit`, and `epistemic-fallacy-scan`.\n"
        f"2. Header Format: Begin the deliverable with the standard provenance block:\n"
        f"   # Cutlass Epistemic & Structural Logic Audit: Cargo {meta_id}\n"
        f"   **Asset Title:** {title}\n"
        f"   **GCS Cargo Path:** `{bucket_path}`\n"
        f"   **Source / Provenance:** {pub_title or 'N/A'}\n"
        f"   **Publication Date:** {pub_date or 'N/A'}\n"
        f"   **Author Assigned Sail Locker:** {target_locker.strip() or 'N/A'}\n"
        f"   **Author Intent & Calibration:** {learning_note.strip() or 'N/A'}\n"
        f"3. Generate a compact, high-density deliverable using the 4-Section Forensic Ledger:\n"
        f"   ## 1. Epistemic Decoupling & Chain of Ruin (SAYS vs. IS; Stage 1, 2, or 3 diagnosis with exact text quote)\n"
        f"   ## 2. Causal Claims & Popperian Demarcation Audit (Audit causal claims; test for Popperian falsifiability, ad hoc immunizing stratagems, and inductive illusions; itemize ONLY detected fallacies)\n"
        f"   ## 3. Anti-Financial Reductionism & Sail Locker Verdict (Deconstruct labor/liability/verification evasion; derive Sail Locker strictly from Section 2; reflect Author's calibration"
        + (f" to {target_locker.strip()}" if target_locker.strip() else "") + f")\n"
        f"   ## 4. Downstream Value Evaluation:\n"
        f"       - GROG: Identify the 'Main Characters of the Epistemic Logic Chain' (unnamed spokespeople, anonymous officials, invisible data-labeling workforces, automated liability shields). Do NOT list generic proper nouns.\n"
        f"       - BILGELADLE: Conceptual tension, epistemic vulnerability, and theoretical ammunition against 'The End of Knowing' thesis. CRITICAL RULE: DO NOT ASSIGN OR RECOMMEND CHAPTER OR SECTION NUMBERS TO BILGELADLE. Chapter selection is strictly Bilgeladle's sovereign mandate.\n"
        f"       - SCALLYWAG: Specific institutional hypocrisies, misanthropic rationalizations, and rhetorical absurdities for narrative synthesis.\n"
        f"3. Write the complete audit markdown deliverable to `{rel_dossier_path}` via `write_local_file`.\n"
        f"4. Call `log_full_audit_dossier` with metadata_id={meta_id}, sail_locker (from Section 3), and dossier_path='{rel_dossier_path}'.\n"
        f"5. Report your final verdict, confidence, and primary warrant quote."
    )

    thread_id = f"cargo_{meta_id}_cutlass"
    chat_session = engine.start_chat_session(thread_id)

    try:
        response_text = engine.execute_turn(chat_session, prompt)
        return response_text
    except Exception as e:
        st.error(f"Full audit failed for #{meta_id}: {str(e)}")
        return None
    finally:
        engine.close()


# =====================================================================
# MAIN USER INTERFACE
# =====================================================================

def main():
    st.title("⛵ Cutlass Rapid Triage & Calibration Console")
    st.caption("Zero-token GCS reader, rapid sail locker classification, and active Author feedback loop.")

    # Initialize session state for batch results and selected asset
    if "latest_triage_batch" not in st.session_state:
        st.session_state["latest_triage_batch"] = None
    if "selected_asset_id" not in st.session_state:
        st.session_state["selected_asset_id"] = None
    if "active_view_mode" not in st.session_state:
        st.session_state["active_view_mode"] = "🌊 Doldrums (Needs Review)"

    # Fetch live data
    all_cargo = fetch_all_cargo_with_triage()
    if not all_cargo:
        st.warning("No cargo records found in database.")
        return

    # Counts by locker
    doldrums_items = [item for item in all_cargo if item["sail_locker"] == "DOLDRUMS"]
    untriaged_items = [item for item in all_cargo if item["sail_locker"] == "UNTRIAGED"]
    reacquiring_items = [item for item in all_cargo if item["sail_locker"] == "REACQUIRING"]
    mainsail_items = [item for item in all_cargo if item["sail_locker"] == "MAINSAIL"]
    bilge_items = [item for item in all_cargo if item["sail_locker"] == "BILGE"]
    jib_items = [item for item in all_cargo if item["sail_locker"] == "JIB"]
    flotsam_items = [item for item in all_cargo if item["sail_locker"] == "FLOTSAM"]
    wherry_items = [item for item in all_cargo if item["sail_locker"] == "WHERRY"]
    
    # Recently triaged items (sorted by triage timestamp descending)
    recently_triaged_items = sorted(
        [item for item in all_cargo if item["triaged_at"] is not None],
        key=lambda x: x["triaged_at"],
        reverse=True
    )

    # Sightings count
    all_sightings = list_fleet_sightings()
    new_sightings_count = len([s for s in all_sightings if s.get("status") == "NEW"])

    # Sidebar: Metrics & Batch Controls
    with st.sidebar:
        st.header("📊 Cargo Manifest Metrics")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Cargo", len(all_cargo))
        col_m2.metric("🌊 Doldrums", len(doldrums_items))
        col_m3, col_m4 = st.columns(2)
        col_m3.metric("⏳ Untriaged", len(untriaged_items))
        col_m4.metric("🔄 Re-acquiring", len(reacquiring_items))
        col_m5, col_m6 = st.columns(2)
        col_m5.metric("⛵ Mainsail", len(mainsail_items))
        col_m6.metric("🛢️ Bilge", len(bilge_items))
        col_m7, col_m8 = st.columns(2)
        col_m7.metric("🚩 Jib", len(jib_items))
        col_m8.metric("🛶 Wherry", len(wherry_items))
        col_m9, col_m10 = st.columns(2)
        col_m9.metric("🪵 Flotsam", len(flotsam_items))
        col_m10.metric("🔭 Sightings", len(all_sightings))

        st.divider()

        # Batch Triage Trigger
        st.subheader("⚡ Fast-Pass Triage")
        batch_size = st.number_input(
            "Batch Size", 
            min_value=1, 
            max_value=50, 
            value=1,
            help="Run rapid classification across untriaged assets"
        )
        
        if st.button("🚀 Run Fast Triage on Untriaged", disabled=(len(untriaged_items) == 0), use_container_width=True):
            batch_results = run_batch_triage_job(untriaged_items, batch_size)
            if batch_results:
                st.session_state["latest_triage_batch"] = batch_results
                # Set latest triaged asset as active selection
                st.session_state["selected_asset_id"] = batch_results[0]["id"]
                st.session_state["active_view_mode"] = f"🕒 Recently Triaged ({len(recently_triaged_items)})"
                st.rerun()

        st.divider()

        # View Mode Selector
        st.subheader("📂 Queue View")
        view_options = [
            f"🕒 Recently Triaged ({len(recently_triaged_items)})",
            f"🌊 Doldrums (Needs Review) ({len(doldrums_items)})",
            f"🔭 Sightings Ledger ({len(all_sightings)})",
            f"⏳ Untriaged ({len(untriaged_items)})",
            f"🔄 Pending Re-acquisition ({len(reacquiring_items)})",
            f"⛵ Mainsail ({len(mainsail_items)})",
            f"🛢️ Bilge ({len(bilge_items)})",
            f"🚩 Jib ({len(jib_items)})",
            f"🛶 Wherry (Agent Tools) ({len(wherry_items)})",
            f"🪵 Flotsam (Excluded) ({len(flotsam_items)})",
            f"📦 All Cargo ({len(all_cargo)})"
        ]
        
        # Match current active_view_mode to index
        current_index = 0
        for idx, opt in enumerate(view_options):
            if st.session_state["active_view_mode"].split(" ")[0] in opt:
                current_index = idx
                break

        selected_view = st.radio(
            "Select Queue to Audit:",
            view_options,
            index=current_index
        )
        st.session_state["active_view_mode"] = selected_view

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Display Top Alert if a batch was just triaged
    if st.session_state["latest_triage_batch"]:
        with st.expander("⚡ Latest Batch Triage Decisions (Click to Expand / Collapse)", expanded=True):
            for res in st.session_state["latest_triage_batch"]:
                st.markdown(f"**Asset #{res['id']}:** `{res['title']}`")
                st.markdown(res["response"])
                st.markdown("---")
            if st.button("Dismiss Batch Notice"):
                st.session_state["latest_triage_batch"] = None
                st.rerun()

    # Special View: Primary Source Sightings Ledger
    if "Sightings Ledger" in selected_view:
        st.subheader("🔭 Primary Source Sightings Ledger")
        st.caption("Aggregated inventory of upstream datasets, whitepapers, legal filings, and empirical reports sighted across cargo assets. Sighted by Grog (Turn 3), held here for human review and queue promotion.")

        if not all_sightings:
            st.info("No primary source sightings recorded yet in `writings/cargo/FLEET_SIGHTINGS_LEDGER.md`.")
            return

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Total Sightings", len(all_sightings))
        col_s2.metric("🆕 New (Unreviewed)", new_sightings_count)
        col_s3.metric("🚀 Promoted to Queue", len([s for s in all_sightings if s.get("status") == "PROMOTED"]))
        col_s4.metric("✅ In Cargo Hold", len([s for s in all_sightings if s.get("status") == "ALREADY_ACQUIRED"]))

        st.divider()

        status_filter = st.selectbox("Filter Sightings by Status:", ["All", "NEW", "PROMOTED", "ALREADY_ACQUIRED", "IN_QUEUE"])
        display_sightings = all_sightings if status_filter == "All" else [s for s in all_sightings if s.get("status") == status_filter]

        st.write(f"Showing {len(display_sightings)} sightings:")
        for s in display_sightings:
            with st.container():
                st.markdown(f"#### 📄 {s['sighted_title']}")
                c1, c2, c3 = st.columns([3, 3, 2])
                c1.markdown(f"**Source Cargo:** `{s['source_cargo_id']}` ({s['source_title']})")
                c1.markdown(f"**Type:** `{s['source_type']}` | **Sighted:** {s['sighted_at']}")
                
                c2.markdown(f"**Locator / URL:** `{s['url_or_locator']}`")
                if s.get('context_quote'):
                    c2.caption(f"*\"{s['context_quote']}\"*")
                
                stat = s.get('status', 'NEW')
                if stat == "NEW":
                    c3.markdown("<span class='badge-doldrums'>NEW SIGHTING</span>", unsafe_allow_html=True)
                    if s['url_or_locator'].startswith("http://") or s['url_or_locator'].startswith("https://"):
                        if c3.button("🚀 Promote to Queue", key=f"prom_{s['sighting_id']}"):
                            res = promote_sighting_to_queue(s['sighting_id'])
                            st.success(res)
                            st.cache_data.clear()
                            st.rerun()
                    else:
                        c3.caption("Non-URL locator (manual lookup required)")
                elif stat == "PROMOTED":
                    c3.markdown("<span class='badge-jib'>PROMOTED TO QUEUE</span>", unsafe_allow_html=True)
                elif stat == "ALREADY_ACQUIRED":
                    c3.markdown("<span class='badge-mainsail'>ALREADY IN HOLD</span>", unsafe_allow_html=True)
                elif stat == "IN_QUEUE":
                    c3.markdown("<span class='badge-reacquiring'>IN INGESTION QUEUE</span>", unsafe_allow_html=True)

                st.markdown("---")
        return

    # Determine active queue list
    if "Recently Triaged" in selected_view:
        active_list = recently_triaged_items
    elif "Doldrums" in selected_view:
        active_list = doldrums_items
    elif "Untriaged" in selected_view:
        active_list = untriaged_items
    elif "Pending Re-acquisition" in selected_view:
        active_list = reacquiring_items
    elif "Mainsail" in selected_view:
        active_list = mainsail_items
    elif "Bilge" in selected_view:
        active_list = bilge_items
    elif "Jib" in selected_view:
        active_list = jib_items
    elif "Flotsam" in selected_view:
        active_list = flotsam_items
    elif "Wherry" in selected_view:
        active_list = wherry_items
    else:
        active_list = all_cargo

    if not active_list:
        st.info(f"No assets found in category: {selected_view}")
        return

    # Asset selector dropdown with search
    options = {f"#{item['id']} | [{item['sail_locker']}] {item['title'][:65]}": item for item in active_list}
    labels = list(options.keys())

    # Find index of currently selected asset ID if present
    sel_idx = 0
    if st.session_state["selected_asset_id"]:
        for idx, label in enumerate(labels):
            if f"#{st.session_state['selected_asset_id']} " in label:
                sel_idx = idx
                break

    selected_label = st.selectbox(
        f"Select Asset to Review ({len(active_list)} in this queue):",
        labels,
        index=sel_idx
    )
    current_asset = options[selected_label]
    st.session_state["selected_asset_id"] = current_asset["id"]

    # Two-Column Layout: Left (Metadata & Actions) | Right (Full Article Reader)
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        # Asset Metadata Header
        st.subheader("📋 Asset Dossier")
        st.markdown(f"**Title:** {current_asset['title']}")
        if current_asset['source_url']:
            st.markdown(f"**Source URL:** [{current_asset['source_url']}]({current_asset['source_url']})")
        st.markdown(f"**GCS Path:** `{current_asset['gcp_bucket_path']}`")
        if current_asset['publication_title'] or current_asset['publication_date']:
            st.caption(f"Published: {current_asset['publication_title']} ({current_asset['publication_date']})")

        # Locker Badge
        locker = current_asset["sail_locker"]
        badge_class = f"badge-{locker.lower()}"
        st.markdown(f"**Current Sail Locker:** <span class='{badge_class}'>{locker}</span>", unsafe_allow_html=True)
        if current_asset["triaged_at"]:
            st.caption(f"Last Triaged: {current_asset['triaged_at']}")

        # Check for Bilgeladle Chapter Anchor & Advisory Tags
        payload_dict = current_asset.get("full_payload") or {}
        rec_locker = payload_dict.get("recommended_locker")
        needs_reacq = payload_dict.get("needs_reacquisition")
        primary_chap = payload_dict.get("primary_chapter")

        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        bilge_align_path = os.path.join(workspace_root, "writings", "cargo", f"cargo_{current_asset['id']}", "bilgeladle_alignment.md")
        if os.path.exists(bilge_align_path):
            try:
                with open(bilge_align_path, "r", encoding="utf-8", errors="replace") as bf:
                    b_text = bf.read()
                    if not rec_locker:
                        r_match = re.search(r"Recommended Locker:\s*(FLOTSAM|WHERRY|None)", b_text, re.IGNORECASE)
                        if r_match: rec_locker = r_match.group(1).upper()
                    if needs_reacq is None:
                        n_match = re.search(r"Needs Reacquisition:\s*(TRUE|FALSE)", b_text, re.IGNORECASE)
                        if n_match: needs_reacq = (n_match.group(1).upper() == "TRUE")
                    if not primary_chap:
                        c_match = re.search(r"Primary Chapter Anchor:\s*([^\n]+)", b_text)
                        if c_match: primary_chap = c_match.group(1).strip()
            except Exception:
                pass

        if primary_chap and primary_chap != "NONE":
            st.markdown(f"**⚓ Primary Chapter Anchor:** `{primary_chap}`")

        if rec_locker == "FLOTSAM":
            st.warning("⚠️ **Bilgeladle Advisory: Recommended FLOTSAM** (Suspected non-research cargo, spam, or marketing puffery)")
        elif rec_locker == "WHERRY":
            st.info("🛶 **Bilgeladle Advisory: Recommended WHERRY** (Suspected developer tooling, library docs, or agent infrastructure)")

        if needs_reacq:
            st.error("🔄 **Bilgeladle Alert: Needs Reacquisition** (Truncated paywall preview, 403 block, or empty video shell)")

        # Cutlass Triage Card
        if current_asset["sail_locker"] != "UNTRIAGED":
            st.markdown("---")
            st.markdown("### 🤖 Cutlass Assessment")
            st.markdown(f"**Confidence:** ⭐ {current_asset['confidence']} / 5")
            if current_asset["rationale"]:
                st.info(f"**Author Intent Hypothesis:**\n{current_asset['rationale']}")
            if current_asset["warrant"]:
                st.caption(f"**Key Warrant Quote:** *\"{current_asset['warrant']}\"*")

        st.markdown("---")

        # Human Calibration & Action Deck
        st.markdown("### 🎯 Author Calibration & Sail Locker Triage")
        st.write("Teach Cutlass why this asset belongs in a specific locker. When calibrated to a primary locker, Cutlass re-awakens her thread to run the full 6-section audit and generate the reusable dossier:")

        learning_note = st.text_area(
            "Teach Cutlass (Rationale / Guidance):",
            placeholder="e.g. This is Bilge because the authors conflate token volume with actual productivity and deflect executive culpability...",
            height=90,
            key=f"note_{current_asset['id']}"
        )

        auto_audit = st.checkbox(
            "⚡ Automatically run Complete Intake Pipeline (Bilgeladle -> Cutlass -> Grog + Sightings)",
            value=True,
            help="When checked, clicking MAINSAIL, BILGE, or JIB immediately records the human calibration, trains learned rules, and executes the complete 3-turn inverted pipeline (Bilgeladle -> Cutlass -> Grog) in one pass."
        )

        st.markdown("##### ⛵ Primary Research Sail Lockers (Core Intellectual Cargo)")
        pri_c1, pri_c2, pri_c3 = st.columns(3)

        if pri_c1.button("⛵ MAINSAIL", use_container_width=True, type="primary" if locker != "MAINSAIL" else "secondary", help="Primary Thesis Alignment: Direct evidence of epistemic corruption, institutional decay, or core thesis proof."):
            record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "MAINSAIL", learning_note, current_asset["title"])
            if auto_audit:
                with st.spinner(f"Running Inverted Shared-Thread Intake (Bilgeladle -> Cutlass -> Grog) for MAINSAIL..."):
                    res = run_cargo_intake(
                        metadata_id=current_asset["id"],
                        force_turn2_3=True,
                        author_locker="MAINSAIL",
                        author_note=learning_note
                    )
                    if res.get("status") in ("COMPLETED", "HALTED_DOLDRUMS", "HALTED_DOLDRUMS_AFTER_CUTLASS"):
                        st.success(f"Asset #{current_asset['id']} calibrated as MAINSAIL! Full dossiers & primary source sightings generated in one pass.")
                    else:
                        st.warning(f"Locker updated to MAINSAIL, but intake pipeline encountered an issue: {res.get('message', res.get('status'))}")
            else:
                st.success(f"Asset #{current_asset['id']} categorized as MAINSAIL with learning note recorded.")
            st.cache_data.clear()
            st.rerun()

        if pri_c2.button("🛢️ BILGE", use_container_width=True, type="primary" if locker != "BILGE" else "secondary", help="Toxic Epistemic Waste: Unverifiable hype, computational truthiness, bureaucratic stenography, and deceptive rationalizations."):
            record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "BILGE", learning_note, current_asset["title"])
            if auto_audit:
                with st.spinner(f"Running Inverted Shared-Thread Intake (Bilgeladle -> Cutlass -> Grog) for BILGE..."):
                    res = run_cargo_intake(
                        metadata_id=current_asset["id"],
                        force_turn2_3=True,
                        author_locker="BILGE",
                        author_note=learning_note
                    )
                    if res.get("status") in ("COMPLETED", "HALTED_DOLDRUMS", "HALTED_DOLDRUMS_AFTER_CUTLASS"):
                        st.success(f"Asset #{current_asset['id']} calibrated as BILGE! Full dossiers & primary source sightings generated in one pass.")
                    else:
                        st.warning(f"Locker updated to BILGE, but intake pipeline encountered an issue: {res.get('message', res.get('status'))}")
            else:
                st.success(f"Asset #{current_asset['id']} categorized as BILGE with learning note recorded.")
            st.cache_data.clear()
            st.rerun()

        if pri_c3.button("🚩 JIB", use_container_width=True, type="primary" if locker != "JIB" else "secondary", help="Counter-Arguments & Orthogonal Angles: Critical friction, alternative frameworks, or nuanced methodological pushback."):
            record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "JIB", learning_note, current_asset["title"])
            if auto_audit:
                with st.spinner(f"Running Inverted Shared-Thread Intake (Bilgeladle -> Cutlass -> Grog) for JIB..."):
                    res = run_cargo_intake(
                        metadata_id=current_asset["id"],
                        force_turn2_3=True,
                        author_locker="JIB",
                        author_note=learning_note
                    )
                    if res.get("status") in ("COMPLETED", "HALTED_DOLDRUMS", "HALTED_DOLDRUMS_AFTER_CUTLASS"):
                        st.success(f"Asset #{current_asset['id']} calibrated as JIB! Full dossiers & primary source sightings generated in one pass.")
                    else:
                        st.warning(f"Locker updated to JIB, but intake pipeline encountered an issue: {res.get('message', res.get('status'))}")
            else:
                st.success(f"Asset #{current_asset['id']} categorized as JIB with learning note recorded.")
            st.cache_data.clear()
            st.rerun()

        st.markdown("##### 📦 Administrative & Quarantine Lockers (Non-Research Cargo)")
        sec_c1, sec_c2, sec_c3 = st.columns(3)

        if sec_c1.button("🌊 DOLDRUMS", use_container_width=True, type="primary" if locker != "DOLDRUMS" else "secondary", help="Hold for Review: Asset requires further human inspection or clarification before assigning a research locker."):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "DOLDRUMS", learning_note, current_asset["title"]):
                st.info(f"Asset #{current_asset['id']} kept in DOLDRUMS with learning note.")
                st.cache_data.clear()
                st.rerun()

        if sec_c2.button("🪵 FLOTSAM", use_container_width=True, type="primary" if locker != "FLOTSAM" else "secondary", help="Quarantine Asset: Corrupted text, marketing spam, or non-signal. Excludes permanently from vector embeddings and research workflows."):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "FLOTSAM", learning_note, current_asset["title"]):
                st.warning(f"Asset #{current_asset['id']} moved to FLOTSAM (Quarantined from workflows & vector index).")
                st.cache_data.clear()
                st.rerun()

        if sec_c3.button("🛶 WHERRY", use_container_width=True, type="primary" if locker != "WHERRY" else "secondary", help="Agent Tooling & Infrastructure: Technical docs, API specs, or agent utilities. Excluded from manuscript research workflows."):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "WHERRY", learning_note, current_asset["title"]):
                st.warning(f"Asset #{current_asset['id']} moved to WHERRY (Agent Tooling - Excluded from workflows & vector index).")
                st.cache_data.clear()
                st.rerun()

        # ADR-015 Permanent Dossiers & Deliverables
        cargo_folder = os.path.join(workspace_root, "writings", "cargo", f"cargo_{current_asset['id']}")
        bilge_path = os.path.join(cargo_folder, "bilgeladle_alignment.md")
        cutlass_path = current_asset.get("dossier_path") or os.path.join(cargo_folder, "cutlass_audit.md")
        if not os.path.isabs(cutlass_path):
            cutlass_path = os.path.abspath(cutlass_path)
        grog_path = os.path.join(cargo_folder, "grog_extraction.md")

        st.markdown("---")
        st.markdown("### 🏛️ ADR-015 Reusable Cargo Deliverables")

        if os.path.exists(bilge_path):
            with st.expander("📄 View Bilgeladle Chapter Alignment Deliverable (Turn 1)", expanded=False):
                try:
                    with open(bilge_path, "r", encoding="utf-8", errors="replace") as bf:
                        st.markdown(bf.read())
                except Exception as de:
                    st.error(f"Error reading Bilgeladle deliverable: {str(de)}")

        if os.path.exists(cutlass_path):
            with st.expander("📄 View Cutlass Forensic Logic Audit Deliverable (Turn 2)", expanded=False):
                try:
                    with open(cutlass_path, "r", encoding="utf-8", errors="replace") as cf:
                        st.markdown(cf.read())
                except Exception as de:
                    st.error(f"Error reading Cutlass deliverable: {str(de)}")

        if os.path.exists(grog_path):
            with st.expander("📄 View Grog Straight Summary & Sightings (Turn 3)", expanded=False):
                try:
                    with open(grog_path, "r", encoding="utf-8", errors="replace") as gf:
                        st.markdown(gf.read())
                except Exception as de:
                    st.error(f"Error reading Grog deliverable: {str(de)}")

        if not (os.path.exists(bilge_path) or os.path.exists(cutlass_path) or os.path.exists(grog_path)):
            st.info("ℹ️ No permanent multi-agent deliverables exist yet for this asset.")

        st.markdown("##### 🚀 Shared-Thread Intake Pipeline")
        if st.button("⚡ Run Inverted Intake Pipeline (Bilgeladle -> Cutlass -> Grog)", use_container_width=True, type="primary"):
            with st.spinner(f"Running Inverted Shared-Thread Pipeline on cargo_{current_asset['id']}..."):
                res = run_cargo_intake(metadata_id=current_asset["id"])
                if res.get("status") in ("COMPLETED", "HALTED_DOLDRUMS", "HALTED_DOLDRUMS_AFTER_CUTLASS"):
                    st.success(f"Pipeline executed! Status: {res.get('status')}. Chapter Anchor: {res.get('primary_chapter', 'N/A')}. Locker: {res.get('sail_locker')}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"Pipeline execution issue: {res.get('message', res.get('status'))}")

        # Re-acquisition Escalation Deck
        st.markdown("---")
        st.markdown("### 🔭 Ingestion Remediation")
        st.caption("Remediate defective or paywalled assets:")
        
        rem_c1, rem_c2 = st.columns(2)
        if rem_c1.button("🔄 Push to Spyglass", use_container_width=True, help="Re-queues URL in cargo.ingestion_queue for Spyglass retry."):
            if not current_asset.get("source_url"):
                st.error("Cannot re-acquire: Asset has no source URL recorded.")
            else:
                if push_back_to_spyglass(current_asset["id"], current_asset["source_url"], learning_note):
                    st.success(f"Asset #{current_asset['id']} re-queued for Spyglass acquisition!")
                    st.cache_data.clear()
                    st.rerun()

        if rem_c2.button("💀 Dead-Letter Queue", use_container_width=True, help="Incinerates truncated stub from GCS, deletes metadata row, and logs permanent dead-letter in cargo.failed_metadata."):
            if not current_asset.get("source_url"):
                st.error("Cannot dead-letter: Asset has no source URL recorded.")
            else:
                if send_to_dead_letter_queue(current_asset["id"], current_asset["source_url"], learning_note):
                    st.warning(f"Asset #{current_asset['id']} incinerated from Cargo Hold & permanently logged to Dead-Letter Queue!")
                    st.cache_data.clear()
                    st.rerun()

    with col_right:
        st.subheader("📖 Full Asset Raw Text (0 LLM Tokens)")
        raw_text = get_cached_raw_content(current_asset["gcp_bucket_path"])

        if raw_text.startswith("[ERROR]") or raw_text.startswith("[No GCS"):
            st.error(raw_text)
        else:
            word_count = len(raw_text.split())
            char_count = len(raw_text)
            st.caption(f"Payload Size: {char_count:,} characters ({word_count:,} words)")

            # Scrollable reader container
            with st.container(height=650):
                st.text(raw_text)


if __name__ == "__main__":
    main()
