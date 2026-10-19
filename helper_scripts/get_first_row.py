"""
NPT Fleet Diagnostic: First Row Inspector

How to run:
    uv run python helper_scripts/get_first_row.py

What it does:
    Quick verification script to inspect the first row of ship.letters_of_marque and verify column formatting.

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
from urllib.parse import urlparse
import pg8000.dbapi

def get_first_row():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("CONTENT_DATABASE_URL not set")
        return
    url = urlparse(conn_string)
    conn = pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ship.letters_of_marque LIMIT 1;")
        row = cursor.fetchone()
        colnames = [desc[0] for desc in cursor.description]
        if row:
            for col, val in zip(colnames, row):
                # Truncate long values like embeddings or text for readability
                val_str = str(val)
                if len(val_str) > 150:
                    val_str = val_str[:150] + "... [TRUNCATED]"
                print(f"{col}: {val_str}")
        else:
            print("No rows found in ship.letters_of_marque.")
        cursor.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    get_first_row()
