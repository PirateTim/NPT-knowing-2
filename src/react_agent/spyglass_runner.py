import os
import sys
import json
import uuid
from urllib.parse import urlparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

load_dotenv()

# Force path tracing for relative package modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.acquire_content import acquire_content
from tool_dispatcher import read_local_file, write_local_file

# =====================================================================
# PERSISTENCE & CHECKPOINT LAYER (Direct pg8000 Wiring)
# =====================================================================

def get_db_connection():
    """Establishes a connection to the primary tracking instance."""
    try:
        url = urlparse(os.getenv("DATABASE_URL"))
        return pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
    except Exception as e:
        print(f"[DB ERROR] Configuration mismatch: {e}", file=sys.stderr)
        return None

def get_latest_checkpoint(conn, thread_id: str) -> List[dict]:
    """Retrieves standard serializable message arrays from the database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT checkpoint FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    
    if result and result[0]:
        if isinstance(result[0], list):
            return result[0]
        elif isinstance(result[0], str):
            return json.loads(result[0])
    return []

def save_checkpoint(conn, thread_id: str, history: List[dict]):
    """Commits clean text turns to the long-term state log."""
    cursor = conn.cursor()
    new_checkpoint_id = str(uuid.uuid4())
    
    cursor.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    parent_row = cursor.fetchone()
    parent_id = parent_row[0] if parent_row else None

    if history:
        json_str = json.dumps(history)
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint) VALUES (%s, %s, %s, %s)",
            (thread_id, new_checkpoint_id, parent_id, json_str)
        )
        conn.commit()
    cursor.close()

# =====================================================================
# MANIFEST RUNTIME EXECUTION LOOP
# =====================================================================

def run_agent_loop(agent_name: str, thread_suffix: str):
    db_conn = get_db_connection()
    if not db_conn:
        sys.exit(1)

    thread_id = f"thread_{agent_name.lower()}_{thread_suffix}"
    system_instruction = "You are Spyglass. Ingestion Engine. You do not summarize content. You blindly use tools."
    
    client = genai.Client()
    
    print(f"\n[BOOT] {agent_name.upper()} runner activated via direct execution wires.")
    print(f"[TRACKING REGISTER] Thread: {thread_id}")
    print("Type 'exit' or 'quit' to terminate.\n")

    try:
        while True:
            user_input = input(f"({agent_name.upper()}) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break

            is_url = user_input.startswith("http://") or user_input.startswith("https://")
            if is_url:
                print(f"\n[SPYGLASS PIPELINE] Processing URL Target: {user_input}")
                tool_result = acquire_content(user_input)
                current_status = tool_result.get("status", "failed")
                
                # if current_status == "failed":
                    # user_payload = f"SYSTEM NOTICE: Ingestion pipeline execution failed entirely for target. Error: {tool_result.get('error')}"
                if current_status == "failed":
                    # Hard logging direct pipeline execution failures
                    try:
                        cursor = db_conn.cursor()
                        derived_dom = urlparse(user_input).netloc
                        cursor.execute(
                            """
                            INSERT INTO cargo.failed_metadata 
                            (source_url, derived_domain, tier_1_executed, tier_2_executed, method_3_tried, error_state)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (source_url) DO UPDATE 
                            SET error_state = EXCLUDED.error_state, logged_at = CURRENT_TIMESTAMP
                            """,
                            (user_input, derived_dom, True, True, False, str(tool_result.get("error", "Unknown Scraper Crash")))
                        )
                        db_conn.commit()
                        cursor.close()
                    except Exception as db_err:
                        print(f"[LOG FAULT] Could not commit failure log: {db_err}", file=sys.stderr)

                    user_payload = f"SYSTEM NOTICE: Ingestion pipeline execution failed entirely for target. Error: {tool_result.get('error')}"
                elif current_status == "cached":
                    user_payload = (
                        f"SYSTEM ACQUISITION VERIFICATION LOG:\n"
                        f"URL: {user_input}\n"
                        f"Status: CACHED (Asset already verified in storage archive)\n"
                        f"Storage Path: {str(tool_result.get('gcp_path', 'None'))}\n"
                        f"Metadata Title: {str(tool_result.get('title', 'Unknown'))}"
                    )
                else:
                    print(f"[SPYGLASS SYSTEM NOTICE] Storage Operations Complete (Tier {tool_result.get('tier_executed', 1)}).")
                    print(f" -> DB Insert Status: {tool_result.get('db_insert')}")
                    print(f" -> GCP Bucket Upload: {tool_result.get('gcp_upload')}")
                    
                    user_payload = (
                        f"SYSTEM ACQUISITION VERIFICATION LOG:\n"
                        f"URL: {user_input}\n"
                        f"Status: COMPLETED (Tier {tool_result.get('tier_executed', 1)} Extraction)\n"
                        f"Storage Path: {str(tool_result.get('gcp_path', 'None'))}\n"
                        f"Metadata Title: {str(tool_result.get('title', 'Unknown Title'))}"
                    )
            else:
                user_payload = user_input

            if not user_payload or str(user_payload).strip() == "":
                user_payload = f"Processed Interaction Turn for: {user_input}"               

            history = get_latest_checkpoint(db_conn, thread_id)
            history.append({"role": "user", "parts": [{"text": user_payload}]})

            contents_input = []
            for turn in history:
                valid_parts = []
                for p in turn.get("parts", []):
                    if "text" in p and str(p["text"]).strip() != "":
                        valid_parts.append(types.Part.from_text(text=str(p["text"])))
                
                if valid_parts:
                    contents_input.append(types.Content(role=turn["role"], parts=valid_parts))

            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=contents_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1
                )
            )

            print(f"\n{agent_name.upper()} RESPONSE:\n{response.text}\n")
            
            history.append({"role": "model", "parts": [{"text": response.text}]})
            save_checkpoint(db_conn, thread_id, history)

    finally:
        db_conn.close()
        print("[SHUTDOWN] Connection handles successfully released.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_runner.py <agent_name> [thread_suffix]")
        sys.exit(1)
        
    name = sys.argv[1]
    suffix = sys.argv[2] if len(sys.argv) >= 3 else f"prod_sprint_{str(uuid.uuid4())[:4]}"
    run_agent_loop(name, suffix)