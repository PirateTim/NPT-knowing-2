import os
import json
import datetime
import html
import requests
import pg8000.dbapi
import trafilatura
import urllib.request
import urllib.error
from urllib.parse import urlparse

def get_cargo_db_connection():
    """Extracts connection parameters specifically targeting our content database warehouse."""
    try:
        conn_string = os.getenv("CONTENT_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not conn_string:
            return None
        url = urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
    except Exception as e:
        print(f"[CARGO DB ERROR] Connection drop: {e}")
        return None

def fetch_html_fallback_bytes(url: str) -> bytes:
    """TIER 2 FALLBACK: Fetches raw HTML bytes using standard urllib and realistic browser headers."""
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()

def clean_string_metadata(text_str: str) -> str:
    """Resolves standard HTML entities and normalizes string layout to clean UTF-8 text."""
    if not text_str:
        return text_str
    unescaped_text = html.unescape(text_str)
    return unescaped_text.encode('utf-8', errors='ignore').decode('utf-8')


def acquire_content(url: str) -> dict:
    """
    Acquires purified text content and metadata from any standard URL.
    Natively drops back to Tier 2 browser-header scraping if Tier 1 requests fail.
    """
    target_url = url.strip().replace('"', '').replace("'", "").replace('\r', '').replace('\n', '')
    gcp_bucket_name = os.getenv("GCP_CARGO_BUCKET", "npt-fleet-cargo-hold")
    results = {"url": target_url, "status": "pending", "tier_executed": 1}
    
    # Quick, cost-effective pre-check on known failures before burning compute cycles
    # (Pre-assume db_conn handle availability inside tool contexts)
    
    # 1. Deduplication Check
    db_conn = get_cargo_db_connection()
    existing_record = None
    
    if db_conn:
        try:
            cursor = db_conn.cursor()
            cursor.execute('SELECT title, gcp_bucket_path, publication_date FROM cargo.content_metadata WHERE source_url = %s;', (target_url,))
            existing_record = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(f"[DEDUPLICATION WARNING] Metadata check skipped: {e}")
        finally:
            try:
                db_conn.close()
            except Exception:
                pass

    # FIXED: Ensure a solid, bulletproof dictionary payload is returned IMMEDIATELY on cache hits
    if existing_record:
        print(f"[DEDUPLICATION HIT] Asset already exists for: {target_url}")
        return {
            "url": target_url, 
            "status": "cached", 
            "title": str(existing_record[0]),
            "gcp_path": str(existing_record[1]), 
            "publication_date": str(existing_record[2])
        }

    # 2. Extract Data (Tier 1 vs Tier 2 Execution)
    html_bytes = None
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200:
            html_bytes = response.content
        else:
            print(f"[PIPELINE NOTICE] Tier 1 hit HTTP Status {response.status_code}. Deploying Tier 2 Fallback...")
            html_bytes = fetch_html_fallback_bytes(target_url)
            results["tier_executed"] = 2
    except Exception as e:
        print(f"[PIPELINE NOTICE] Tier 1 extraction exception: {str(e)}. Deploying Tier 2 Fallback...")
        try:
            html_bytes = fetch_html_fallback_bytes(target_url)
            results["tier_executed"] = 2
        except Exception as fallback_err:
            return {"url": target_url, "status": "failed", "error": f"Tier 2 Fallback crashed: {str(fallback_err)}"}

    # 3. Parse Extracted Bytes Natively
# =====================================================================
    # 3. Parse Extracted Bytes Natively
    # =====================================================================
    # FIXED: Convert raw binary bytes to a clean UTF-8 string FIRST to prevent trafilatura from mis-guessing
    html_string = ""
    if html_bytes:
        try:
            # Enforce strict UTF-8 decoding, replacing unaligned anomalies defensively
            html_string = html_bytes.decode('utf-8', errors='replace')
        except Exception:
            # Emergency fallback if the site used a hard legacy Windows encoding
            html_string = html_bytes.decode('latin-1', errors='replace')

    # Pass the pre-decoded string to trafilatura instead of raw bytes
    clean_content = trafilatura.extract(html_string)
    if not clean_content:
        clean_content = html_string[:10000]

    page_title = f"Harvested Content: {target_url}"
    pub_date = datetime.datetime.now().strftime("%Y-%m-%d")
    native_abstract = None
    native_categories = []

    # Extract metadata using the stable string layout
    res_metadata = trafilatura.extract_metadata(html_string)
    if res_metadata:
        if hasattr(res_metadata, 'title') and res_metadata.title:
            page_title = res_metadata.title
        if hasattr(res_metadata, 'date') and res_metadata.date:
            pub_date = str(res_metadata.date)
        if hasattr(res_metadata, 'description') and res_metadata.description:
            native_abstract = res_metadata.description
        if hasattr(res_metadata, 'categories') and res_metadata.categories:
            native_categories = res_metadata.categories

    # Sanitize strings cleanly via our top-level module function
    clean_content = clean_string_metadata(clean_content)
    page_title = clean_string_metadata(page_title)
    native_abstract = clean_string_metadata(native_abstract)
    derived_domain = urlparse(target_url).netloc

    metadata = {
        "ItemType": "webpage",
        "Title": page_title,
        "Domain": derived_domain,
        "Authors": [res_metadata.author] if (res_metadata and hasattr(res_metadata, 'author') and res_metadata.author) else [],
        "Abstract": native_abstract,
        "PublicationTitle": "Web Platform Data",
        "Date": pub_date,
        "URL": target_url,
        "AccessDate": datetime.datetime.now().strftime("%Y-%m-%d"),
        "Keywords": native_categories,
        "Rights": "Unknown"
    }

    # 4. Format Document Header
    header_lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, list):
            header_lines.append(f"{key}:")
            for item in value: 
                header_lines.append(f"  - {item}")
        else:
            header_lines.append(f"{key}: { 'null' if value is None else str(value) }")
    header_lines.append("---")
    full_file_content = "\n".join(header_lines) + "\n\n" + clean_content
    
    # 5. Stream File to GCP Storage Bucket
    gcp_path = f"acquisitions/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_acquired.txt"
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcp_bucket_name)
        blob = bucket.blob(gcp_path)
        blob.upload_from_string(full_file_content)
        results["gcp_upload"] = "success"
    except Exception as e:
        results["gcp_upload"] = f"failed: {str(e)}"

    # 6. Commit Index Metadata Row to Cloud SQL Database
    db_conn = get_cargo_db_connection()
    if db_conn:
        try:
            cursor = db_conn.cursor()
            cursor.execute('''
                INSERT INTO cargo.content_metadata 
                (source_url, item_type, title, authors, abstract, publication_title, publication_date, keywords, rights, gcp_bucket_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO UPDATE SET
                    title = EXCLUDED.title, 
                    gcp_bucket_path = EXCLUDED.gcp_bucket_path, 
                    created_at = NOW();
            ''', (
                target_url, metadata.get("ItemType"), metadata.get("Title"), json.dumps(metadata.get("Authors", [])),
                metadata.get("Abstract"), metadata.get("PublicationTitle"), metadata.get("Date"),
                json.dumps(metadata.get("Keywords", [])), metadata.get("Rights"), f"{gcp_bucket_name}/{gcp_path}"
            ))
            db_conn.commit()

            # IF CONTENT SECURELY STORED: Clean up the dead-letter records instantly
            cursor.execute(
                "DELETE FROM cargo.failed_metadata WHERE source_url = %s",
                (target_url,)
            )

            cursor.close()
            results["db_insert"] = "success"
        except Exception as e:
            results["db_insert"] = f"failed: {str(e)}"
        finally:

            db_conn.close()
    else:
        results["db_insert"] = "failed: connection unavailable"

    results["status"] = "completed"
    results["gcp_path"] = f"{gcp_bucket_name}/{gcp_path}"
    results["title" \
    ""] = page_title
    return results