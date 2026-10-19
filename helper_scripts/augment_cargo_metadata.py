"""
NPT Fleet: Metadata Augmentation Sweeper

How to run:
    uv run python helper_scripts/augment_cargo_metadata.py

What it does:
    Scans acquired cargo records and extracts missing publication dates, authors, and canonical titles using lightweight LLM extraction.

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
import re
import json
import urllib.parse
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.react_agent.tools.cargo_db_tools import _get_strict_cargo_connection


# High-frequency domain to publisher map
DOMAIN_MAP = {
    "futurism.com": "Futurism",
    "theverge.com": "The Verge",
    "wired.com": "Wired",
    "techcrunch.com": "TechCrunch",
    "arxiv.org": "arXiv",
    "nytimes.com": "The New York Times",
    "wsj.com": "The Wall Street Journal",
    "bloomberg.com": "Bloomberg",
    "theguardian.com": "The Guardian",
    "reuters.com": "Reuters",
    "washingtonpost.com": "The Washington Post",
    "arstechnica.com": "Ars Technica",
    "404media.co": "404 Media",
    "eff.org": "Electronic Frontier Foundation",
    "prospectmagazine.co.uk": "Prospect Magazine",
    "theatlantic.com": "The Atlantic",
    "axios.com": "Axios",
    "androidpolice.com": "Android Police",
    "androidheadlines.com": "Android Headlines",
    "the-decoder.com": "The Decoder",
    "newyorker.com": "The New Yorker",
    "scientificamerican.com": "Scientific American",
    "nature.com": "Nature",
    "science.org": "Science",
    "github.com": "GitHub",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "fortune.com": "Fortune",
    "cnbc.com": "CNBC",
    "theregister.com": "The Register",
    "platformer.news": "Platformer",
    "sfchronicle.com": "San Francisco Chronicle",
    "pcmag.com": "PCMag",
    "thedailybeast.com": "The Daily Beast",
    "technologyreview.com": "MIT Technology Review",
    "medium.com": "Medium",
    "substack.com": "Substack"
}


def extract_structural_metadata(url: str) -> tuple[str, str | None]:
    """Tier 1: Fast URL-based publisher and publication date extraction."""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    
    # Publisher resolution
    pub_title = DOMAIN_MAP.get(domain)
    if not pub_title:
        parts = domain.split(".")
        if len(parts) >= 2:
            pub_title = parts[-2].title()
        else:
            pub_title = domain.title()

    date_str = None
    # 1. YYYY/MM/DD
    m1 = re.search(r'/(202[0-9])/(0[1-9]|1[0-2])/(0[1-9]|[12][0-9]|3[01])(/|$)', parsed.path)
    if m1:
        date_str = f"{m1.group(1)}-{m1.group(2)}-{m1.group(3)}"
    else:
        # 2. YYYY-MM-DD
        m2 = re.search(r'/(202[0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(/|$|\.|\-)', parsed.path)
        if m2:
            date_str = f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
        else:
            # 3. YYYY/MM
            m3 = re.search(r'/(202[0-9])/(0[1-9]|1[0-2])(/|$)', parsed.path)
            if m3:
                date_str = f"{m3.group(1)}-{m3.group(2)}"
            elif "arxiv.org" in domain:
                m_ar = re.search(r'/(\d{2})(\d{2})\.', parsed.path)
                if m_ar:
                    yy, mm = m_ar.group(1), m_ar.group(2)
                    date_str = f"20{yy}-{mm}"

    return pub_title, date_str


def fetch_live_html_metadata(url: str) -> tuple[str | None, str | None]:
    """Tier 2: Lightweight HTML header extraction."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code != 200:
            return None, None
        soup = BeautifulSoup(r.text, 'html.parser')
        
        extracted_date = None
        extracted_author = None
        
        # 1. Time tags
        t = soup.find('time')
        if t and t.get('datetime'):
            dt = t.get('datetime')[:10]
            if re.match(r'^\d{4}-\d{2}-\d{2}$', dt):
                extracted_date = dt

        # 2. Meta tags
        if not extracted_date:
            meta_pub = soup.find('meta', property='article:published_time') or soup.find('meta', property='og:published_time') or soup.find('meta', attrs={'name': 'date'})
            if meta_pub and meta_pub.get('content'):
                dt = meta_pub.get('content')[:10]
                if re.match(r'^\d{4}-\d{2}-\d{2}$', dt):
                    extracted_date = dt

        # 3. Author meta
        meta_auth = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', property='article:author')
        if meta_auth and meta_auth.get('content'):
            auth_val = meta_auth.get('content').strip()
            if auth_val and not auth_val.startswith('http') and len(auth_val) < 60:
                extracted_author = auth_val

        # 4. JSON-LD fallback
        if not extracted_date or not extracted_author:
            for s in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(s.string)
                    items = data.get('@graph', [data]) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    for it in items:
                        if isinstance(it, dict):
                            if not extracted_date and 'datePublished' in it:
                                dt = str(it['datePublished'])[:10]
                                if re.match(r'^\d{4}-\d{2}-\d{2}$', dt):
                                    extracted_date = dt
                            if not extracted_author and 'author' in it:
                                auth_data = it['author']
                                if isinstance(auth_data, dict) and 'name' in auth_data:
                                    extracted_author = auth_data['name']
                                elif isinstance(auth_data, list) and len(auth_data) > 0 and isinstance(auth_data[0], dict):
                                    extracted_author = auth_data[0].get('name')
                except Exception:
                    pass

        return extracted_date, extracted_author
    except Exception:
        return None, None


def process_single_asset(asset_tuple: tuple) -> dict:
    """Processes a single content metadata row and returns proposed updates."""
    asset_id, url, title, existing_authors, existing_date, existing_pub = asset_tuple
    
    pub_title, date_str = extract_structural_metadata(url)
    author_str = None
    
    # Fallback to live fetch if date is still unknown and URL is live HTTP
    if not date_str and (url.startswith("http://") or url.startswith("https://")):
        live_date, live_author = fetch_live_html_metadata(url)
        if live_date:
            date_str = live_date
        if live_author and not existing_authors:
            author_str = live_author

    return {
        "id": asset_id,
        "url": url,
        "title": title,
        "new_date": date_str if date_str else existing_date,
        "new_pub": pub_title if pub_title else existing_pub,
        "new_author": author_str,
        "date_recovered": bool(date_str and not existing_date)
    }


def run_sweeper(limit: int | None = None, concurrency: int = 8):
    print("=" * 80)
    print(" NPT FLEET: METADATA AUGMENTATION SWEEPER")
    print("=" * 80)
    
    conn = _get_strict_cargo_connection()
    if not conn:
        print("[ERROR] Cannot connect to cargo database!")
        return

    cur = conn.cursor()
    query = """
        SELECT id, source_url, title, authors, publication_date, publication_title
        FROM cargo.content_metadata
        WHERE (publication_date IS NULL OR publication_date = '' OR publication_date = 'UNKNOWN')
           OR (publication_title IS NULL OR publication_title = '' OR publication_title = 'UNKNOWN')
        ORDER BY id ASC
    """
    if limit:
        query += f" LIMIT {limit}"
    query += ";"
    
    cur.execute(query)
    targets = cur.fetchall()
    print(f"Loaded {len(targets)} targets requiring metadata augmentation.")
    
    if not targets:
        print("All assets already have complete metadata!")
        conn.close()
        return

    updates_to_commit = []
    dates_found = 0
    pubs_found = 0
    
    print(f"Beginning multi-threaded augmentation (Concurrency: {concurrency})...\n")
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(process_single_asset, t): t[0] for t in targets}
        completed = 0
        
        for future in as_completed(futures):
            res = future.result()
            completed += 1
            
            if res["date_recovered"]:
                dates_found += 1
            if res["new_pub"]:
                pubs_found += 1
                
            updates_to_commit.append(res)
            
            if completed % 50 == 0 or completed == len(targets):
                print(f"[{completed}/{len(targets)}] Progress: {dates_found} dates recovered, {pubs_found} publishers resolved...")

    # Batch commit updates to PostgreSQL
    print(f"\nCommitting {len(updates_to_commit)} updates to PostgreSQL cargo.content_metadata...")
    for item in updates_to_commit:
        update_fields = []
        params = []
        
        if item["new_date"]:
            update_fields.append("publication_date = %s")
            params.append(item["new_date"])
        if item["new_pub"]:
            update_fields.append("publication_title = %s")
            params.append(item["new_pub"])
        if item["new_author"]:
            update_fields.append("authors = %s")
            params.append(json.dumps([item["new_author"]]))
            
        if update_fields:
            params.append(item["id"])
            sql = f"UPDATE cargo.content_metadata SET {', '.join(update_fields)} WHERE id = %s;"
            cur.execute(sql, tuple(params))
            
    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print(" SWEEP COMPLETED SUCCESSFULLY!")
    print(f" Total Processed:          {len(targets)}")
    print(f" Publication Dates Added:  {dates_found} ({dates_found/len(targets)*100:.1f}%)")
    print(f" Publishers Standardized:  {pubs_found}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Augment metadata across cargo.content_metadata.")
    parser.add_argument("--limit", type=int, help="Limit number of rows to process.")
    parser.add_argument("--concurrency", type=int, default=8, help="Number of concurrent worker threads.")
    args = parser.parse_args()

    run_sweeper(limit=args.limit, concurrency=args.concurrency)
