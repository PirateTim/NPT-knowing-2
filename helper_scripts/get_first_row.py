"""
Helper Script: Inspect First Row in `ship.letters_of_marque`
Usage:
    python helper_scripts/get_first_row.py
"""
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
