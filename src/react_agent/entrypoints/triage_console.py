"""
NPT Fleet: Cutlass Rapid Triage & Sail Locker Calibration Console
Streamlit Web Application for zero-token asset inspection, batch fast-triage, and human-in-the-loop learning.
"""

import os
import sys
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
from tools.cargo_db_tools import _get_strict_cargo_connection

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
            fe.payload AS full_payload,
            fe.created_at AS triaged_at
        FROM cargo.content_metadata cm
        LEFT JOIN cargo.fleet_enrichments fe 
            ON cm.id = fe.metadata_id 
            AND fe.agent_name IN ('cutlass', 'author', 'cutlass_calibrated')
            AND fe.enrichment_type IN ('triage', 'triage_quick', 'triage_human_override')
        ORDER BY cm.id, fe.created_at DESC;
    """
    items = []
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for r in rows:
            (mid, title, url, itype, pub_title, pub_date, bucket_path, created_at,
             locker, conf, hyp, warrant, overview, full_payload, triaged_at) = r

            # Determine canonical locker
            assigned_locker = (locker or "").upper().strip()
            if not assigned_locker:
                status = "UNTRIAGED"
            elif assigned_locker in ("MAINSAIL", "BILGE", "JIB", "DOLDRUMS", "FLOTSAM", "WHERRY"):
                status = assigned_locker
            else:
                status = "DOLDRUMS"

            # Parse hypothesis or fallback
            rationale_text = hyp or overview or ""
            if not rationale_text and isinstance(full_payload, dict):
                rationale_text = full_payload.get("rationale") or full_payload.get("author_intent_hypothesis") or ""

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


def record_human_reclassification(metadata_id: int, gcp_bucket_path: str, new_locker: str, learning_note: str, asset_title: str) -> bool:
    """
    Commits an Author human override to cargo.fleet_enrichments and records a learned rule in learned_rules.json.
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

        # Update Cutlass learned_rules.json memory vault if a learning note was provided
        if learning_note.strip():
            rules_path = os.path.abspath("src/react_agent/agents/cutlass/learned_rules.json")
            if os.path.exists(rules_path):
                with open(rules_path, "r", encoding="utf-8") as f:
                    rules_data = json.load(f)

                new_rule = {
                    "rule_directive": f"Sail Locker Calibration ({new_locker}): When evaluating assets similar to '{asset_title}', assign '{new_locker}'. Rationale: {learning_note.strip()}",
                    "source_context": f"Author Triage Override on {gcp_bucket_path} ({datetime.date.today().isoformat()})"
                }
                rules_data.append(new_rule)

                with open(rules_path, "w", encoding="utf-8") as f:
                    json.dump(rules_data, f, indent=4)

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

        # 2. Record enrichment explaining why it was pushed back
        payload = {
            "sail_locker": "DOLDRUMS",
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

        thread_id = f"thread_quick_triage_{asset['id']}_{datetime.datetime.now().strftime('%H%M%S')}"
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

    # Sidebar: Metrics & Batch Controls
    with st.sidebar:
        st.header("📊 Cargo Manifest Metrics")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total Cargo", len(all_cargo))
        col_m2.metric("🌊 Doldrums", len(doldrums_items))
        col_m3, col_m4 = st.columns(2)
        col_m3.metric("⏳ Untriaged", len(untriaged_items))
        col_m4.metric("⛵ Mainsail", len(mainsail_items))
        col_m5, col_m6 = st.columns(2)
        col_m5.metric("🛢️ Bilge", len(bilge_items))
        col_m6.metric("🚩 Jib", len(jib_items))
        col_m7, col_m8 = st.columns(2)
        col_m7.metric("🪵 Flotsam", len(flotsam_items))
        col_m8.metric("🛶 Wherry", len(wherry_items))

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
            f"⏳ Untriaged ({len(untriaged_items)})",
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

    # Determine active queue list
    if "Recently Triaged" in selected_view:
        active_list = recently_triaged_items
    elif "Doldrums" in selected_view:
        active_list = doldrums_items
    elif "Untriaged" in selected_view:
        active_list = untriaged_items
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
        st.markdown("### 🎯 Human Calibration & Reclassification")
        st.write("Confirm or move this asset to its authentic Sail Locker, and teach Cutlass the rationale:")

        learning_note = st.text_area(
            "Teach Cutlass (Why does this belong here?):",
            placeholder="e.g. This is Bilge because the executive is deflecting blame for labor downsizing onto AI tokens...",
            height=90,
            key=f"note_{current_asset['id']}"
        )

        btn_c1, btn_c2, btn_c3, btn_c4, btn_c5, btn_c6 = st.columns(6)

        if btn_c1.button("⛵ MAINSAIL", use_container_width=True, type="primary" if locker != "MAINSAIL" else "secondary"):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "MAINSAIL", learning_note, current_asset["title"]):
                st.success(f"Asset #{current_asset['id']} categorized as MAINSAIL with learning note!")
                st.cache_data.clear()
                st.rerun()

        if btn_c2.button("🛢️ BILGE", use_container_width=True, type="primary" if locker != "BILGE" else "secondary"):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "BILGE", learning_note, current_asset["title"]):
                st.success(f"Asset #{current_asset['id']} categorized as BILGE with learning note!")
                st.cache_data.clear()
                st.rerun()

        if btn_c3.button("🚩 JIB", use_container_width=True, type="primary" if locker != "JIB" else "secondary"):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "JIB", learning_note, current_asset["title"]):
                st.success(f"Asset #{current_asset['id']} categorized as JIB with learning note!")
                st.cache_data.clear()
                st.rerun()

        if btn_c4.button("🌊 DOLDRUMS", use_container_width=True, type="primary" if locker != "DOLDRUMS" else "secondary"):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "DOLDRUMS", learning_note, current_asset["title"]):
                st.info(f"Asset #{current_asset['id']} kept in DOLDRUMS with learning note.")
                st.cache_data.clear()
                st.rerun()

        if btn_c5.button("🪵 FLOTSAM", use_container_width=True, type="primary" if locker != "FLOTSAM" else "secondary", help="Quarantine asset. Excludes permanently from vector embeddings and research workflows."):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "FLOTSAM", learning_note, current_asset["title"]):
                st.warning(f"Asset #{current_asset['id']} moved to FLOTSAM (Quarantined from workflows & vector index).")
                st.cache_data.clear()
                st.rerun()

        if btn_c6.button("🛶 WHERRY", use_container_width=True, type="primary" if locker != "WHERRY" else "secondary", help="Agentic tools & infrastructure cargo. Excludes permanently from vector embeddings and manuscript research workflows."):
            if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], "WHERRY", learning_note, current_asset["title"]):
                st.warning(f"Asset #{current_asset['id']} moved to WHERRY (Agent Tooling - Excluded from workflows & vector index).")
                st.cache_data.clear()
                st.rerun()

        if locker != "UNTRIAGED" and learning_note.strip():
            st.markdown("")
            if st.button(f"💾 Confirm {locker} & Save Learning Note", use_container_width=True, type="primary"):
                if record_human_reclassification(current_asset["id"], current_asset["gcp_bucket_path"], locker, learning_note, current_asset["title"]):
                    st.success(f"Learning note added to {locker} for Asset #{current_asset['id']}!")
                    st.cache_data.clear()
                    st.rerun()

        # Re-acquisition Escalation Deck
        st.markdown("---")
        st.markdown("### 🔭 Ingestion Remediation")
        st.caption("If this asset is defective, incomplete, or a metadata shell, push it back to Spyglass for re-acquisition:")
        if st.button("🔄 Push Back to Spyglass to Re-Acquire", use_container_width=True):
            if not current_asset.get("source_url"):
                st.error("Cannot re-acquire: Asset has no source URL recorded.")
            else:
                if push_back_to_spyglass(current_asset["id"], current_asset["source_url"], learning_note):
                    st.success(f"Asset #{current_asset['id']} re-queued for Spyglass acquisition!")
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
