"""
NPT Fleet: Cognitive Thread State Manager

How to run:
    uv run python helper_scripts/manage_threads.py

What it does:
    Lists, inspects, and manually manages short-term conversational threads stored in agent_state.checkpoints.

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
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

# 1. Environment Initialization
load_dotenv()

def get_db():
    """
    Establishes a connection to the state database.
    Note: This strictly uses DATABASE_URL, which targets the cognitive/state schema,
    respecting the strict database segregation outlined in ADR-003.
    """
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing DATABASE_URL in .env")
        sys.exit(1)
        
    url = urlparse(conn_string)
    # Using the app user for standard read/write execution
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def list_threads():
    """Queries the checkpoints table to list all active thread IDs and their last update time."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Sorts by most recently active so the architect can easily spot their current or crashed session
    cursor.execute("SELECT thread_id, updated_at FROM agent_state.checkpoints ORDER BY updated_at DESC;")
    rows = cursor.fetchall()
    
    print("\n=== ACTIVE AGENT THREADS ===")
    if not rows: 
        print("No threads found. The state database is clean.")
        
    for row in rows: 
        # row[0] is thread_id, row[1] is updated_at
        print(f"- {row[0]} (Last Active: {row[1]})")
        
    cursor.close()
    conn.close()

def delete_thread(thread_id):
    """Surgically removes a specific thread's history from the Postgres database."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Uses parameterized queries (%s) to prevent SQL injection, even on internal scripts
    cursor.execute("DELETE FROM agent_state.checkpoints WHERE thread_id = %s;", (thread_id,))
    
    # Must commit because we are altering the table
    conn.commit()
    print(f"\n[SUCCESS] Thread '{thread_id}' and all its associated memory permanently deleted.")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # 2. Command Line Argument Router
    # Provides a simple CLI interface for the human architect
    if len(sys.argv) == 1 or sys.argv[1] == "list":
        list_threads()
    elif sys.argv[1] == "delete" and len(sys.argv) == 3:
        delete_thread(sys.argv[2])
    else:
        # Failsafe instructions if typed incorrectly
        print("Usage: python manage_threads.py list")
        print("       python manage_threads.py delete <thread_id>")