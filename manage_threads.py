"""
NPT Fleet: Thread State Manager
Utility to View or Delete Agent Conversations.
"""
import os
import sys
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def get_db():
    conn_string = os.getenv("DATABASE_URL")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:])

def list_threads():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT thread_id, updated_at FROM agent_state.checkpoints ORDER BY updated_at DESC;")
    rows = cursor.fetchall()
    print("\n=== ACTIVE AGENT THREADS ===")
    if not rows: print("No threads found.")
    for row in rows: print(f"- {row[0]} (Last Active: {row[1]})")
    cursor.close()
    conn.close()

def delete_thread(thread_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agent_state.checkpoints WHERE thread_id = %s;", (thread_id,))
    conn.commit()
    print(f"\n[SUCCESS] Thread '{thread_id}' permanently deleted.")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "list":
        list_threads()
    elif sys.argv[1] == "delete" and len(sys.argv) == 3:
        delete_thread(sys.argv[2])
    else:
        print("Usage: python manage_threads.py list")
        print("       python manage_threads.py delete <thread_id>")