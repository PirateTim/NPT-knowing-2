"""
NPT Fleet: Ingestion Queue Inspector
Description: Queries and displays all items currently registered in cargo.ingestion_queue.
"""

import os
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

def list_queue():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        return

    url = urlparse(conn_string)
    db_name = url.path[1:]

    try:
        conn = pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=db_name,
        )
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT queue_id, target_url, status, attempt_count, last_attempted_at, added_at
            FROM cargo.ingestion_queue
            ORDER BY queue_id ASC;
            """
        )
        rows = cursor.fetchall()

        print(f"\n================================================================================")
        print(f"                   CARGO INGESTION QUEUE MANIFEST ({len(rows)} TOTAL)")
        print(f"================================================================================")

        if not rows:
            print("[NOTICE] cargo.ingestion_queue is currently empty.")
        else:
            for row in rows:
                qid, target_url, status, attempts, last_attempt, added = row
                print(f"[{qid:03d}] [{status:<10}] Attempts: {attempts:<2} | {target_url}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[FATAL ERROR] Failed to query cargo.ingestion_queue: {e}")

if __name__ == "__main__":
    list_queue()
