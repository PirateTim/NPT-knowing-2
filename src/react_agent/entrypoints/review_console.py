"""
NPT Fleet Content Review Console
Web Server & Dashboard for reviewing acquired content from GCS, metadata DB rows, and generated agent markdowns.
"""

import os
import sys
import json
import re
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import pg8000.dbapi
from dotenv import load_dotenv
from google.cloud import storage

# Ensure system paths and UTF-8 encoding
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(override=True)

# In-memory cache for GCS blobs to make UI instant on repeat views
GCS_CACHE = {}

def get_cargo_connection():
    """Establishes connection to the Postgres content database."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return None
    try:
        url = urllib.parse.urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
    except Exception as e:
        print(f"[DB ERROR] Connection failed: {e}")
        return None

def fetch_all_items():
    """Fetches list of all acquired content metadata items with enrichment status."""
    conn = get_cargo_connection()
    if not conn:
        return []
    items = []
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                m.id, 
                m.title, 
                m.source_url, 
                m.item_type, 
                m.publication_title, 
                m.publication_date, 
                m.gcp_bucket_path,
                m.created_at,
                (
                    SELECT payload->>'sail_locker' 
                    FROM cargo.fleet_enrichments 
                    WHERE metadata_id = m.id AND agent_name = 'cutlass' 
                    LIMIT 1
                ) as sail_locker
            FROM cargo.content_metadata m
            ORDER BY m.id DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        for row in rows:
            mid, title, url_str, itype, pub_title, pub_date, bucket_path, created_at, locker = row
            items.append({
                "id": mid,
                "title": title or "Untitled Asset",
                "source_url": url_str,
                "item_type": itype or "document",
                "publication_title": pub_title or "",
                "publication_date": pub_date or "",
                "gcp_bucket_path": bucket_path or "",
                "created_at": str(created_at) if created_at else "",
                "sail_locker": locker or "UNASSIGNED"
            })
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] fetch_all_items: {e}")
        if conn: conn.close()
    return items

def fetch_raw_content_from_gcs_or_local(gcp_bucket_path: str) -> str:
    """Retrieves full acquired raw content from GCS bucket or local filesystem."""
    if not gcp_bucket_path:
        return "[NO GCS BUCKET PATH RECORDED IN DB]"

    if gcp_bucket_path in GCS_CACHE:
        return GCS_CACHE[gcp_bucket_path]

    # Parse bucket name and blob path from gs:// URI or raw path
    bucket_name = os.getenv("GCP_BUCKET_NAME", "npt-fleet-cargo-hold")
    blob_path = gcp_bucket_path

    if gcp_bucket_path.startswith("gs://"):
        parts = gcp_bucket_path[5:].split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

    # 1. Try local acquisitions/ directory first if cached
    filename = os.path.basename(blob_path)
    if filename:
        local_path = os.path.abspath(os.path.join(os.getcwd(), "acquisitions", filename))
        if os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    GCS_CACHE[gcp_bucket_path] = content
                    return content
            except Exception:
                pass

    # 2. Fetch directly from Google Cloud Storage Bucket
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        if blob.exists():
            content = blob.download_as_text()
            GCS_CACHE[gcp_bucket_path] = content
            return content
        else:
            return f"[GCS BLOB NOT FOUND IN BUCKET '{bucket_name}': {blob_path}]"
    except Exception as e:
        return f"[ERROR FETCHING FROM GCS BUCKET '{bucket_name}': {str(e)}]"

def fetch_item_detail(item_id: int):
    """Fetches comprehensive item detail: DB row, GCS raw content, markdowns, and enrichments."""
    conn = get_cargo_connection()
    if not conn:
        return None

    detail = {}
    try:
        cursor = conn.cursor()
        # 1. Fetch metadata row
        cursor.execute("SELECT id, source_url, item_type, title, authors, abstract, publication_title, publication_date, keywords, rights, gcp_bucket_path, created_at FROM cargo.content_metadata WHERE id = %s;", (item_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return None

        mid, source_url, item_type, title, authors, abstract, pub_title, pub_date, keywords, rights, bucket_path, created_at = row
        
        # Parse JSON fields safely
        def safe_json(val):
            if isinstance(val, (dict, list)): return val
            if isinstance(val, str) and val.strip():
                try: return json.loads(val)
                except: return val
            return val

        detail["metadata"] = {
            "id": mid,
            "source_url": source_url,
            "item_type": item_type,
            "title": title,
            "authors": safe_json(authors),
            "abstract": abstract,
            "publication_title": pub_title,
            "publication_date": pub_date,
            "keywords": safe_json(keywords),
            "rights": rights,
            "gcp_bucket_path": bucket_path,
            "created_at": str(created_at) if created_at else ""
        }

        # 2. Fetch fleet enrichments
        cursor.execute("SELECT id, agent_name, enrichment_type, payload, created_at FROM cargo.fleet_enrichments WHERE metadata_id = %s ORDER BY created_at ASC;", (item_id,))
        enrichment_rows = cursor.fetchall()
        enrichments = []
        sail_locker = "UNASSIGNED"
        for erow in enrichment_rows:
            eid, agent_name, enrichment_type, payload, ecreated = erow
            payload_data = safe_json(payload)
            if agent_name == "cutlass" and isinstance(payload_data, dict):
                sail_locker = payload_data.get("sail_locker", sail_locker)
            enrichments.append({
                "id": eid,
                "agent_name": agent_name,
                "enrichment_type": enrichment_type,
                "payload": payload_data,
                "created_at": str(ecreated) if ecreated else ""
            })
        detail["sail_locker"] = sail_locker
        detail["enrichments"] = enrichments

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] fetch_item_detail: {e}")
        if conn: conn.close()
        return None

    # 3. Fetch full raw content from GCS bucket
    raw_content = fetch_raw_content_from_gcs_or_local(detail["metadata"].get("gcp_bucket_path"))
    detail["raw_content"] = raw_content
    detail["raw_stats"] = {
        "words": len(raw_content.split()),
        "characters": len(raw_content),
        "lines": len(raw_content.splitlines())
    }

    # 4. Resolve generated report files from fleet enrichments
    reports = {"cutlass": None, "grog": None, "bilgeladle": None}
    
    for enc in detail["enrichments"]:
        agent = enc.get("agent_name")
        pdata = enc.get("payload") or {}
        if isinstance(pdata, dict) and agent in reports:
            # Check for file pointers in the enrichment payload
            fpath = pdata.get("review_path") or pdata.get("review_file") or pdata.get("file_path") or pdata.get("extraction_path")
            if fpath and os.path.exists(fpath):
                reports[agent] = _read_report_file(fpath, os.path.basename(fpath))
            elif not reports[agent]:
                # Fallback: Render JSON payload as pretty markdown if no separate file exists
                reports[agent] = {
                    "filename": f"{agent}_enrichment_{enc.get('enrichment_type')}.json",
                    "filepath": f"cargo.fleet_enrichments (ID: {enc.get('id')})",
                    "content": f"```json\n{json.dumps(pdata, indent=2, default=str)}\n```",
                    "size_bytes": len(json.dumps(pdata))
                }

    detail["reports"] = reports
    return detail

def _read_report_file(filepath, filename):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "filename": filename,
            "filepath": filepath.replace("\\", "/"),
            "content": content,
            "size_bytes": os.path.getsize(filepath)
        }
    except Exception as e:
        return {"filename": filename, "content": f"[ERROR READING FILE: {e}]", "size_bytes": 0}

def fetch_stats():
    """Fetches high-level metrics across the content database."""
    conn = get_cargo_connection()
    if not conn:
        return {}
    stats = {}
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cargo.content_metadata;")
        stats["total_content_items"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM cargo.fleet_enrichments;")
        stats["total_enrichments"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cargo.failed_metadata;")
        stats["total_failed_metadata"] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT payload->>'sail_locker' as locker, COUNT(*) 
            FROM cargo.fleet_enrichments 
            WHERE agent_name = 'cutlass' AND payload->>'sail_locker' IS NOT NULL 
            GROUP BY payload->>'sail_locker';
        """)
        lockers = {r[0]: r[1] for r in cursor.fetchall()}
        stats["sail_lockers"] = lockers
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB ERROR] fetch_stats: {e}")
        if conn: conn.close()
    return stats

# HTML/CSS/JS Single Page App Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NPT Fleet Content Review Console</title>
    <!-- Google Fonts & FontAwesome -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Marked.js for Markdown Rendering -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        :root {
            --bg-base: #0a0e17;
            --bg-surface: #121826;
            --bg-card: #1a2336;
            --bg-card-hover: #222d45;
            --border-color: #2a3652;
            --border-highlight: #3b4d76;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
            --accent-primary: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
            --mainsail-color: #10b981;
            --mainsail-bg: rgba(16, 185, 129, 0.15);
            --jib-color: #06b6d4;
            --jib-bg: rgba(6, 182, 212, 0.15);
            --bilge-color: #f59e0b;
            --bilge-bg: rgba(245, 158, 11, 0.15);
            --font-heading: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-code: 'Fira Code', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html, body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: var(--font-body);
            font-size: 12px;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* Top Header */
        header {
            background-color: var(--bg-surface);
            border-bottom: 1px solid var(--border-color);
            padding: 6px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
            height: 42px;
            flex-shrink: 0;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .brand-icon {
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #0284c7, #38bdf8);
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #fff;
            box-shadow: 0 0 8px var(--accent-glow);
        }

        .brand-title {
            font-family: var(--font-heading);
            font-size: 14px;
            font-weight: 700;
            letter-spacing: -0.3px;
            background: linear-gradient(to right, #f8fafc, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-tag {
            font-size: 9px;
            background: #1e293b;
            color: var(--accent-primary);
            padding: 1px 5px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-weight: 600;
        }

        .stats-bar {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .stat-pill {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 10.5px;
            color: var(--text-muted);
            background: var(--bg-card);
            padding: 2px 8px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        .stat-pill strong {
            color: var(--text-main);
            font-weight: 700;
        }

        /* Main Workspace Container */
        .workspace {
            display: flex;
            flex: 1;
            overflow: hidden;
            height: calc(100vh - 42px);
        }

        /* Left Sidebar - Item List */
        .sidebar {
            width: 300px;
            background-color: var(--bg-surface);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex-shrink: 0;
        }

        .sidebar-search {
            padding: 8px 10px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex-shrink: 0;
        }

        .search-box {
            position: relative;
        }

        .search-box i {
            position: absolute;
            left: 8px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            font-size: 11px;
        }

        .search-box input {
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            padding: 5px 8px 5px 26px;
            border-radius: 5px;
            color: var(--text-main);
            font-size: 11.5px;
            outline: none;
            transition: all 0.2s;
        }

        .search-box input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 6px var(--accent-glow);
        }

        .filter-pills {
            display: flex;
            gap: 4px;
            overflow-x: auto;
            padding-bottom: 2px;
        }

        .filter-pill {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9.5px;
            font-weight: 600;
            cursor: pointer;
            background: var(--bg-card);
            color: var(--text-muted);
            border: 1px solid var(--border-color);
            white-space: nowrap;
            transition: all 0.15s;
        }

        .filter-pill.active, .filter-pill:hover {
            background: var(--accent-primary);
            color: #0f172a;
            border-color: var(--accent-primary);
        }

        .item-list {
            flex: 1;
            overflow-y: auto;
            padding: 6px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .item-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            padding: 6px 8px;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .item-card:hover {
            background: var(--bg-card-hover);
            border-color: var(--border-highlight);
        }

        .item-card.selected {
            background: #1e293b;
            border-color: var(--accent-primary);
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.15);
        }

        .item-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .item-id {
            font-family: var(--font-code);
            font-size: 9.5px;
            font-weight: 600;
            color: var(--accent-primary);
        }

        .locker-badge {
            font-size: 8.5px;
            font-weight: 700;
            padding: 1px 5px;
            border-radius: 8px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .locker-MAINSAIL { background: var(--mainsail-bg); color: var(--mainsail-color); border: 1px solid rgba(16,185,129,0.3); }
        .locker-JIB { background: var(--jib-bg); color: var(--jib-color); border: 1px solid rgba(6,182,212,0.3); }
        .locker-BILGE { background: var(--bilge-bg); color: var(--bilge-color); border: 1px solid rgba(245,158,11,0.3); }
        .locker-UNASSIGNED { background: #334155; color: #94a3b8; }

        .item-title {
            font-size: 11.5px;
            font-weight: 600;
            line-height: 1.3;
            color: var(--text-main);
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .item-meta-sub {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 9.5px;
            color: var(--text-dim);
        }

        /* Right Content Panel */
        .content-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-base);
            overflow: hidden;
            height: 100%;
        }

        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-dim);
            gap: 10px;
            font-size: 11.5px;
        }

        .empty-state i {
            font-size: 32px;
            color: var(--border-highlight);
        }

        /* Active Detail Banner */
        .detail-header {
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-color);
            padding: 10px 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            flex-shrink: 0;
        }

        .detail-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .detail-title-group {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .detail-title {
            font-family: var(--font-heading);
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
            line-height: 1.25;
        }

        .live-url-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: #fff;
            text-decoration: none;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 10.5px;
            font-weight: 600;
            transition: all 0.2s;
            box-shadow: 0 2px 6px rgba(2, 132, 199, 0.3);
            white-space: nowrap;
            flex-shrink: 0;
        }

        .live-url-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.4);
            background: linear-gradient(135deg, #0369a1, #075985);
        }

        .metadata-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            font-size: 10px;
            color: var(--text-muted);
        }

        .meta-chip {
            display: flex;
            align-items: center;
            gap: 4px;
            background: var(--bg-card);
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid var(--border-color);
        }

        .meta-chip i {
            color: var(--accent-primary);
        }

        /* Detail Tabs */
        .detail-tabs {
            display: flex;
            background: var(--bg-surface);
            border-bottom: 1px solid var(--border-color);
            padding: 0 14px;
            gap: 2px;
            flex-shrink: 0;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            border-bottom: 2px solid transparent;
            transition: all 0.15s;
        }

        .tab-btn:hover {
            color: var(--text-main);
            background: rgba(255,255,255,0.02);
        }

        .tab-btn.active {
            color: var(--accent-primary);
            border-bottom-color: var(--accent-primary);
        }

        .tab-badge {
            background: var(--bg-card);
            padding: 1px 4px;
            border-radius: 6px;
            font-size: 8.5px;
        }

        /* Tab Viewport - Smooth Vertical Scroll */
        .tab-viewport {
            flex: 1;
            overflow-y: auto;
            padding: 14px;
            background: var(--bg-base);
            height: 100%;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        /* Raw Text View */
        .raw-text-container {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            padding: 14px;
            font-family: var(--font-code);
            font-size: 11px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
            color: #cbd5e1;
        }

        /* Markdown Rendered Area */
        .markdown-rendered {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            padding: 18px;
            line-height: 1.55;
            font-size: 12px;
            color: var(--text-main);
        }

        .markdown-rendered h1, .markdown-rendered h2, .markdown-rendered h3 {
            font-family: var(--font-heading);
            color: #f8fafc;
            margin-top: 14px;
            margin-bottom: 6px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 3px;
        }

        .markdown-rendered h1 { font-size: 15px; color: var(--accent-primary); }
        .markdown-rendered h2 { font-size: 13.5px; }
        .markdown-rendered h3 { font-size: 12px; }

        .markdown-rendered p { margin-bottom: 10px; color: #cbd5e1; }
        .markdown-rendered ul, .markdown-rendered ol { margin-left: 16px; margin-bottom: 10px; }
        .markdown-rendered li { margin-bottom: 3px; color: #cbd5e1; }

        .markdown-rendered blockquote {
            border-left: 3px solid var(--accent-primary);
            background: var(--bg-card);
            padding: 6px 10px;
            margin-bottom: 10px;
            border-radius: 0 4px 4px 0;
            font-style: italic;
        }

        .markdown-rendered code {
            background: #0f172a;
            color: #38bdf8;
            padding: 1px 4px;
            border-radius: 3px;
            font-family: var(--font-code);
            font-size: 10.5px;
        }

        /* Database Key-Value Inspector */
        .db-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 10px;
            margin-bottom: 16px;
        }

        .db-card {
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 5px;
            padding: 8px 10px;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .db-key {
            font-family: var(--font-code);
            font-size: 9.5px;
            color: var(--accent-primary);
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }

        .db-val {
            font-size: 11.5px;
            color: var(--text-main);
            word-break: break-word;
        }

        .json-viewer {
            background: #0f172a;
            border: 1px solid var(--border-color);
            border-radius: 5px;
            padding: 12px;
            font-family: var(--font-code);
            font-size: 10.5px;
            color: #38bdf8;
            white-space: pre-wrap;
            word-break: break-word;
        }
    </style>
</head>
<body>
    <!-- Top Bar -->
    <header>
        <div class="brand">
            <div class="brand-icon"><i class="fa-solid fa-compass"></i></div>
            <div>
                <span class="brand-title">NPT FLEET CONTENT REVIEW CONSOLE</span>
            </div>
            <span class="brand-tag">LIVE GCS + DB</span>
        </div>
        <div class="stats-bar">
            <div class="stat-pill"><i class="fa-solid fa-file-invoice"></i> Items: <strong id="stat-items">...</strong></div>
            <div class="stat-pill"><i class="fa-solid fa-brain"></i> Enrichments: <strong id="stat-enrichments">...</strong></div>
            <div class="stat-pill" style="color: var(--mainsail-color);"><i class="fa-solid fa-ship"></i> Mainsail: <strong id="stat-mainsail">...</strong></div>
        </div>
    </header>

    <!-- Main Workspace -->
    <div class="workspace">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-search">
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <input type="text" id="search-input" placeholder="Filter title, domain, ID..." oninput="filterItems()">
                </div>
                <div class="filter-pills">
                    <div class="filter-pill active" onclick="setFilter('ALL', this)">ALL</div>
                    <div class="filter-pill" onclick="setFilter('MAINSAIL', this)">MAINSAIL</div>
                    <div class="filter-pill" onclick="setFilter('JIB', this)">JIB</div>
                    <div class="filter-pill" onclick="setFilter('BILGE', this)">BILGE</div>
                </div>
            </div>
            <div class="item-list" id="item-list">
                <!-- Dynamically Populated -->
            </div>
        </div>

        <!-- Right Content Panel -->
        <div class="content-panel" id="content-panel">
            <div class="empty-state">
                <i class="fa-solid fa-anchor"></i>
                <p>Select a content asset from the list to view live details and reports.</p>
            </div>
        </div>
    </div>

    <script>
        let allItems = [];
        let activeFilter = 'ALL';
        let currentItem = null;

        // Load stats & item list on boot
        window.addEventListener('DOMContentLoaded', () => {
            loadStats();
            loadItems();
        });

        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-items').innerText = data.total_content_items || 0;
                document.getElementById('stat-enrichments').innerText = data.total_enrichments || 0;
                document.getElementById('stat-mainsail').innerText = (data.sail_lockers && data.sail_lockers.MAINSAIL) || 0;
            } catch (e) {
                console.error("Failed loading stats:", e);
            }
        }

        async function loadItems() {
            try {
                const res = await fetch('/api/items');
                allItems = await res.json();
                renderItemList();
            } catch (e) {
                console.error("Failed loading items:", e);
            }
        }

        function setFilter(locker, element) {
            activeFilter = locker;
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            element.classList.add('active');
            renderItemList();
        }

        function filterItems() {
            renderItemList();
        }

        function renderItemList() {
            const query = document.getElementById('search-input').value.toLowerCase();
            const container = document.getElementById('item-list');
            container.innerHTML = '';

            const filtered = allItems.filter(item => {
                const matchesLocker = (activeFilter === 'ALL') || (item.sail_locker === activeFilter);
                const matchesQuery = !query || 
                    item.title.toLowerCase().includes(query) || 
                    item.source_url.toLowerCase().includes(query) || 
                    String(item.id).includes(query);
                return matchesLocker && matchesQuery;
            });

            filtered.forEach(item => {
                const card = document.createElement('div');
                card.className = `item-card ${currentItem && currentItem.metadata.id === item.id ? 'selected' : ''}`;
                card.onclick = () => selectItem(item.id);

                const domain = getDomain(item.source_url);

                card.innerHTML = `
                    <div class="item-card-header">
                        <span class="item-id">ID #${item.id}</span>
                        <span class="locker-badge locker-${item.sail_locker}">${item.sail_locker}</span>
                    </div>
                    <div class="item-title">${escapeHtml(item.title)}</div>
                    <div class="item-meta-sub">
                        <span><i class="fa-solid fa-globe"></i> ${domain}</span>
                        <span><i class="fa-solid fa-tag"></i> ${item.item_type}</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        async function selectItem(id) {
            try {
                const res = await fetch(`/api/item/${id}`);
                currentItem = await res.json();
                renderItemList();
                renderDetailView(currentItem);
            } catch (e) {
                console.error("Failed loading item detail:", e);
            }
        }

        function renderDetailView(data) {
            const panel = document.getElementById('content-panel');
            const meta = data.metadata;
            const domain = getDomain(meta.source_url);

            const hasCutlass = data.reports.cutlass ? true : false;
            const hasGrog = data.reports.grog ? true : false;
            const hasBilgeladle = data.reports.bilgeladle ? true : false;

            panel.innerHTML = `
                <div class="detail-header">
                    <div class="detail-top">
                        <div class="detail-title-group">
                            <div style="display:flex; gap:6px; align-items:center;">
                                <span class="item-id" style="font-size:11px;">CONTENT ID #${meta.id}</span>
                                <span class="locker-badge locker-${data.sail_locker}">${data.sail_locker}</span>
                            </div>
                            <div class="detail-title">${escapeHtml(meta.title)}</div>
                        </div>
                        <a href="${meta.source_url}" target="_blank" class="live-url-btn">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Live URL
                        </a>
                    </div>
                    <div class="metadata-chips">
                        <div class="meta-chip"><i class="fa-solid fa-globe"></i> Domain: <strong>${domain}</strong></div>
                        <div class="meta-chip"><i class="fa-solid fa-user"></i> Authors: <strong>${formatAuthors(meta.authors)}</strong></div>
                        <div class="meta-chip"><i class="fa-solid fa-calendar"></i> Date: <strong>${meta.publication_date || 'N/A'}</strong></div>
                        <div class="meta-chip"><i class="fa-solid fa-folder"></i> Publisher: <strong>${meta.publication_title || 'N/A'}</strong></div>
                        <div class="meta-chip"><i class="fa-solid fa-align-left"></i> Words: <strong>${data.raw_stats.words}</strong></div>
                    </div>
                </div>

                <div class="detail-tabs">
                    <button class="tab-btn active" onclick="switchTab('raw', this)">
                        <i class="fa-solid fa-file-lines"></i> Raw Content (GCS)
                    </button>
                    <button class="tab-btn" onclick="switchTab('cutlass', this)">
                        <i class="fa-solid fa-shield-halved"></i> Cutlass Audit
                        ${hasCutlass ? '<span class="tab-badge" style="background:#10b981; color:#fff;">READY</span>' : '<span class="tab-badge">NONE</span>'}
                    </button>
                    <button class="tab-btn" onclick="switchTab('grog', this)">
                        <i class="fa-solid fa-beer-mug-empty"></i> Grog Summary
                        ${hasGrog ? '<span class="tab-badge" style="background:#06b6d4; color:#fff;">READY</span>' : '<span class="tab-badge">NONE</span>'}
                    </button>
                    <button class="tab-btn" onclick="switchTab('bilgeladle', this)">
                        <i class="fa-solid fa-book-bookmark"></i> Bilgeladle Alignment
                        ${hasBilgeladle ? '<span class="tab-badge" style="background:#f59e0b; color:#fff;">READY</span>' : '<span class="tab-badge">NONE</span>'}
                    </button>
                    <button class="tab-btn" onclick="switchTab('db', this)">
                        <i class="fa-solid fa-database"></i> DB Metadata Row
                    </button>
                </div>

                <div class="tab-viewport">
                    <!-- Raw Content Tab -->
                    <div id="tab-raw" class="tab-content active">
                        <div class="raw-text-container">${escapeHtml(data.raw_content)}</div>
                    </div>

                    <!-- Cutlass Report -->
                    <div id="tab-cutlass" class="tab-content">
                        ${hasCutlass ? `<div class="markdown-rendered">${marked.parse(data.reports.cutlass.content)}</div>` : '<div class="empty-state"><i class="fa-solid fa-circle-exclamation"></i><p>No Cutlass forensic audit markdown found for this item.</p></div>'}
                    </div>

                    <!-- Grog Report -->
                    <div id="tab-grog" class="tab-content">
                        ${hasGrog ? `<div class="markdown-rendered">${marked.parse(data.reports.grog.content)}</div>` : '<div class="empty-state"><i class="fa-solid fa-circle-exclamation"></i><p>No Grog structural extraction markdown found for this item.</p></div>'}
                    </div>

                    <!-- Bilgeladle Report -->
                    <div id="tab-bilgeladle" class="tab-content">
                        ${hasBilgeladle ? `<div class="markdown-rendered">${marked.parse(data.reports.bilgeladle.content)}</div>` : '<div class="empty-state"><i class="fa-solid fa-circle-exclamation"></i><p>No Bilgeladle manuscript alignment markdown found for this item.</p></div>'}
                    </div>

                    <!-- Database Row Inspector Tab -->
                    <div id="tab-db" class="tab-content">
                        <h3 style="margin-bottom:10px; font-family:var(--font-heading); font-size:13px;">Database Metadata Row (cargo.content_metadata)</h3>
                        <div class="db-grid">
                            <div class="db-card"><span class="db-key">id</span><span class="db-val">${meta.id}</span></div>
                            <div class="db-card"><span class="db-key">title</span><span class="db-val">${escapeHtml(meta.title)}</span></div>
                            <div class="db-card"><span class="db-key">source_url</span><span class="db-val"><a href="${meta.source_url}" target="_blank" style="color:var(--accent-primary);">${meta.source_url}</a></span></div>
                            <div class="db-card"><span class="db-key">item_type</span><span class="db-val">${meta.item_type}</span></div>
                            <div class="db-card"><span class="db-key">publication_title</span><span class="db-val">${meta.publication_title || 'N/A'}</span></div>
                            <div class="db-card"><span class="db-key">publication_date</span><span class="db-val">${meta.publication_date || 'N/A'}</span></div>
                            <div class="db-card"><span class="db-key">gcp_bucket_path</span><span class="db-val">${meta.gcp_bucket_path}</span></div>
                            <div class="db-card"><span class="db-key">created_at</span><span class="db-val">${meta.created_at}</span></div>
                        </div>

                        <h3 style="margin-top:16px; margin-bottom:10px; font-family:var(--font-heading); font-size:13px;">Fleet Enrichments Payload (cargo.fleet_enrichments)</h3>
                        <div class="json-viewer">${escapeHtml(JSON.stringify(data.enrichments, null, 2))}</div>
                    </div>
                </div>
            `;
        }

        function switchTab(tabName, element) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        }

        function getDomain(urlStr) {
            try {
                const u = new URL(urlStr);
                return u.hostname.replace('www.', '');
            } catch (e) {
                return 'unknown';
            }
        }

        function formatAuthors(authors) {
            if (!authors) return 'Unknown';
            if (typeof authors === 'string') return authors;
            if (Array.isArray(authors)) {
                return authors.map(a => typeof a === 'object' ? `${a.firstName || ''} ${a.lastName || ''}`.trim() : String(a)).join(', ');
            }
            return String(authors);
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }
    </script>
</body>
</html>
"""

class ReviewConsoleHandler(BaseHTTPRequestHandler):
    """Custom HTTP request handler serving REST APIs and the HTML Web Console."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/stats":
            self.send_json_response(fetch_stats())
        elif path == "/api/items":
            self.send_json_response(fetch_all_items())
        elif path.startswith("/api/item/"):
            try:
                item_id = int(path.split("/")[-1])
                detail = fetch_item_detail(item_id)
                if detail:
                    self.send_json_response(detail)
                else:
                    self.send_error_response(404, "Item not found")
            except ValueError:
                self.send_error_response(400, "Invalid Item ID")
        else:
            # Serve Single Page App
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode("utf-8"))

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Threaded HTTP Server for concurrent web requests."""
    daemon_threads = True

def main():
    port = 8080
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except: pass

    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, ReviewConsoleHandler)
    print("=========================================================")
    print("      NPT FLEET: CONTENT REVIEW CONSOLE WEB SERVER       ")
    print("=========================================================")
    print(f"  -> Console URL: http://localhost:{port}")
    print("  -> Access the web console in your browser.")
    print("  -> Press Ctrl+C to terminate.")
    print("=========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Content Review Console server terminated.")
        httpd.server_close()

if __name__ == "__main__":
    main()
