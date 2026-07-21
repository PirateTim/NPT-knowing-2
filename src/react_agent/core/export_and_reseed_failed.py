"""
NPT Fleet: Dead-Letter Queue Exporter & Reseeder
Architecture: Disaggregates playlist URLs and resets failed targets to PENDING in cargo.ingestion_queue
"""
import os
import sys
import re
import requests
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()

def get_cargo_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        print("[FATAL] Missing CONTENT_DATABASE_URL in .env")
        sys.exit(1)
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def extract_playlist_videos(playlist_url: str) -> list[str]:
    """Scrapes individual YouTube video URLs from a playlist page."""
    print(f"  -> Disaggregating playlist: {playlist_url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(playlist_url, headers=headers, timeout=15)
        video_ids = list(dict.fromkeys(re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)))
        video_urls = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]
        print(f"  -> Disaggregated {len(video_urls)} individual video URLs from playlist.")
        return video_urls
    except Exception as e:
        print(f"  -> [ERROR] Failed to extract playlist videos: {e}")
        return []

def main():
    print("=========================================================")
    print(" NPT FLEET: DEAD-LETTER RESEEDER & PLAYLIST DISAGGREGATOR")
    print("=========================================================\n")

    conn = get_cargo_connection()
    cursor = conn.cursor()

    # 1. Query all failed URLs
    cursor.execute("SELECT source_url FROM cargo.failed_metadata ORDER BY failed_at DESC;")
    failed_rows = cursor.fetchall()
    
    if not failed_rows:
        print("[NOTICE] No failed URLs found in cargo.failed_metadata.")
        return

    retry_urls = []
    
    for (source_url,) in failed_rows:
        if "list=" in source_url.lower() or "/playlist" in source_url.lower():
            playlist_vids = extract_playlist_videos(source_url)
            retry_urls.extend(playlist_vids)
        else:
            retry_urls.append(source_url)

    # Remove duplicates while preserving order
    retry_urls = list(dict.fromkeys(retry_urls))

    # 2. Write to text file
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "content_lists"))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "failed_retry_targets.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(retry_urls))

    print(f"[SUCCESS] Exported {len(retry_urls)} retry URLs to: {output_file}")

    # 3. Reseed cargo.ingestion_queue as PENDING
    upsert_sql = """
        INSERT INTO cargo.ingestion_queue (target_url, status, source_requestor, added_at)
        VALUES (%s, 'PENDING', 'dead_letter_reseed', NOW())
        ON CONFLICT (target_url) 
        DO UPDATE SET status = 'PENDING', last_attempted_at = NULL;
    """

    seeded_count = 0
    for url_str in retry_urls:
        cursor.execute(upsert_sql, (url_str,))
        seeded_count += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"[SUCCESS] Reseeded {seeded_count} URLs into cargo.ingestion_queue with status='PENDING'.")

if __name__ == "__main__":
    main()
