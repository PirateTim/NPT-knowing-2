"""
NPT Fleet Tools: Content Acquisition & Extraction Primitives
Architecture: Tiered HTTP Fallbacks & Strict UTF-8 Sanitization
"""
import os
import re
import json
import requests
import urllib.request
import trafilatura
import html
from pathlib import Path
from typing import Optional, List, Dict, Any
import pypdf
import uuid
from bs4 import BeautifulSoup
from botasaurus.browser import browser, Driver


# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

# ---------------------------------------------------------------------
# BOTASAURUS BROWSER CONFIGURATION & DEBUG MODE TOGGLING:
# - Automated Batch Runs (Default): headless=True, close_on_crash=True, block_images=True
#   This ensures the browser runs invisibly and terminates immediately on timeout/crash
#   without halting batch execution or pausing for user input ("Press 'Enter' to close").
#
# - How to Turn Visible Browser Debug Mode ON:
#   Option A (Environment Variable): Set BOTASAURUS_HEADLESS=false and BOTASAURUS_CLOSE_ON_CRASH=false in .env
#   Option B (Code Toggle): Change defaults below to headless=False, close_on_crash=False
#   When visible mode is ON, Botasaurus will render the Chrome UI on your desktop and pause
#   on captcha/DOM crashes so you can inspect Cloudflare challenges interactively.
# ---------------------------------------------------------------------
_BOTASAURUS_HEADLESS = os.getenv("BOTASAURUS_HEADLESS", "true").lower() in ("true", "1", "yes")
_BOTASAURUS_CLOSE_ON_CRASH = os.getenv("BOTASAURUS_CLOSE_ON_CRASH", "true").lower() in ("true", "1", "yes")

@browser(headless=_BOTASAURUS_HEADLESS, close_on_crash=_BOTASAURUS_CLOSE_ON_CRASH, block_images=True)
def botasaurus_fetch(driver: Driver, data: dict):
    """
    Internal Helper: Anti-Detect Engine.
    Purpose: Acts as the heavy Tier 2 fallback to bypass Cloudflare/PerimeterX 
    barriers when standard requests fail. Returns the fully rendered DOM.
    Invoked By: Called internally by download_url.
    """
    url = data.get("url")
    try:
        driver.get(url)
        return driver.page_html
    except Exception as e:
        print(f"  -> [BOTASAURUS INNER EXCEPTION] Timeout or freeze on URL: {url}. Error: {str(e)}")
        return f"[BOTASAURUS_TIMEOUT] {str(e)}"

def _clean_string_metadata(text_str: str) -> str:
    """
    Internal Helper: UTF-8 Sanitization.
    Purpose: Resolves standard HTML entities and normalizes string layout to clean text.
    Invoked By: Called internally by extraction tools.
    """
    if not text_str:
        return ""
    unescaped_text = html.unescape(text_str)
    return unescaped_text.encode('utf-8', errors='ignore').decode('utf-8')

def _parse_headers_and_cookies(cookies: str = "", custom_headers: str = "") -> tuple[dict, dict]:
    """
    Internal Helper: Parses cookie and custom header inputs (JSON strings or k=v / k:v formats)
    into Python dictionaries.
    """
    headers_dict = {}
    cookies_dict = {}

    if custom_headers:
        try:
            headers_dict = json.loads(custom_headers)
        except Exception:
            for line in custom_headers.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers_dict[k.strip()] = v.strip()

    if cookies:
        try:
            cookies_dict = json.loads(cookies)
        except Exception:
            for item in cookies.replace(";", "\n").splitlines():
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies_dict[k.strip()] = v.strip()

    return headers_dict, cookies_dict

def _extract_rich_metadata(html_string: str, target_url: str) -> dict:
    """
    Internal Helper: Comprehensive Zotero-Ready Metadata Extraction.
    Hunts for Highwire Press, Dublin Core, OpenGraph, and JSON-LD metadata blocks
    in the HTML to extract citation attributes and infer dynamic item_type.
    """
    meta = {
        "title": target_url, 
        "authors": [], 
        "published_date": "UNKNOWN", 
        "publisher": "UNKNOWN", 
        "journal_title": "",
        "doi": "",
        "volume": "",
        "issue": "",
        "pages": "",
        "abstract": "",
        "item_type": "webpage",
        "raw_json_ld": []
    }
    
    # 1. Trafilatura Baseline
    traf_meta = trafilatura.extract_metadata(html_string)
    if traf_meta:
        if traf_meta.title: meta["title"] = traf_meta.title
        if traf_meta.author: meta["authors"] = [a.strip() for a in traf_meta.author.split(';')]
        if traf_meta.date: meta["published_date"] = traf_meta.date
        if traf_meta.sitename: meta["publisher"] = traf_meta.sitename
        if traf_meta.description: meta["abstract"] = traf_meta.description

    # 2. BeautifulSoup Meta Tag Scraping (Highwire, Dublin Core, OpenGraph)
    soup = BeautifulSoup(html_string, 'html.parser')
    
    highwire_authors = []
    dc_authors = []
    general_meta_authors = []

    for tag in soup.find_all('meta'):
        name = tag.get('name', '').lower()
        prop = tag.get('property', '').lower()
        content = tag.get('content', '').strip()
        if not content: continue

        # Highwire Press (Academic standard)
        if name == 'citation_title': meta["title"] = content
        elif name == 'citation_author': highwire_authors.append(content)
        elif name in ['citation_date', 'citation_publication_date']: meta["published_date"] = content
        elif name == 'citation_journal_title':
            meta["journal_title"] = content
            meta["publisher"] = content
            meta["item_type"] = "journalArticle"
        elif name == 'citation_doi':
            meta["doi"] = content
            meta["item_type"] = "journalArticle"
        elif name == 'citation_volume': meta["volume"] = content
        elif name == 'citation_issue': meta["issue"] = content
        elif name == 'citation_firstpage':
            meta["pages"] = content
            if soup.find('meta', attrs={'name': 'citation_lastpage'}):
                last = soup.find('meta', attrs={'name': 'citation_lastpage'}).get('content', '')
                if last: meta["pages"] = f"{content}-{last}"
        elif name == 'citation_abstract': meta["abstract"] = content

        # Dublin Core
        elif name in ['dc.title', 'dcterms.title']: meta["title"] = content
        elif name in ['dc.creator', 'dcterms.creator']: dc_authors.append(content)
        elif name in ['dc.date', 'dcterms.issued', 'dcterms.created']: meta["published_date"] = content
        elif name in ['dc.publisher', 'dcterms.publisher']: meta["publisher"] = content
        elif name in ['dc.identifier', 'dcterms.identifier'] and content.startswith('10.'): meta["doi"] = content

        # Standard Author & OpenGraph
        elif name == 'author' or prop == 'article:author':
            if not content.startswith('http') and len(content) < 80:
                parts = [p.strip() for p in re.split(r'\s*(?:,|&|\band\b)\s*', content) if p.strip()]
                for p in parts:
                    if p not in general_meta_authors and not any(w in p.lower() for w in ['archive', 'staff', 'editor', 'photo']):
                        general_meta_authors.append(p)
        elif prop == 'og:title' and meta["title"] == target_url: meta["title"] = content
        elif prop == 'og:site_name' and meta["publisher"] == "UNKNOWN": meta["publisher"] = content
        elif prop == 'article:published_time' and meta["published_date"] == "UNKNOWN": meta["published_date"] = content
        elif prop == 'og:type':
            if content in ['article', 'journal']: meta["item_type"] = "journalArticle"
            elif content in ['video', 'video.other']: meta["item_type"] = "videoRecording"

    if highwire_authors: meta["authors"] = highwire_authors
    elif dc_authors and len(dc_authors) > len(meta["authors"]): meta["authors"] = dc_authors
    elif general_meta_authors and len(general_meta_authors) > len(meta["authors"]): meta["authors"] = general_meta_authors

    # 3. JSON-LD Extraction & Type Mapping
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            ld_data = json.loads(script.string)
            meta["raw_json_ld"].append(ld_data) 
            
            if isinstance(ld_data, dict) and '@graph' in ld_data:
                items = ld_data['@graph']
            elif isinstance(ld_data, list):
                items = ld_data
            else:
                items = [ld_data]

            for item in items:
                item_type_ld = item.get('@type', '')
                if item_type_ld in ['ScholarlyArticle', 'JournalArticle']:
                    meta["item_type"] = "journalArticle"
                elif item_type_ld in ['NewsArticle', 'BlogPosting']:
                    if meta["item_type"] == "webpage": meta["item_type"] = "blogPost"
                elif item_type_ld in ['Report', 'TechReport']:
                    if meta["item_type"] == "webpage": meta["item_type"] = "report"
                elif item_type_ld in ['VideoObject']:
                    meta["item_type"] = "videoRecording"

                if 'headline' in item and meta["title"] == target_url: meta["title"] = item['headline']
                if 'datePublished' in item and meta["published_date"] == "UNKNOWN": meta["published_date"] = item['datePublished']
                if 'publisher' in item and isinstance(item['publisher'], dict):
                    meta["publisher"] = item['publisher'].get('name', meta['publisher'])
                if 'description' in item and not meta["abstract"]:
                    meta["abstract"] = item['description']
                
                # Robust JSON-LD Author extraction
                ld_author_field = item.get('author') or item.get('creator')
                if ld_author_field:
                    ld_authors = []
                    if isinstance(ld_author_field, dict) and ld_author_field.get('name'):
                        ld_authors.append(ld_author_field.get('name'))
                    elif isinstance(ld_author_field, list):
                        for a in ld_author_field:
                            if isinstance(a, dict) and a.get('name'):
                                ld_authors.append(a.get('name'))
                            elif isinstance(a, str):
                                ld_authors.append(a.strip())
                    elif isinstance(ld_author_field, str):
                        ld_authors.append(ld_author_field.strip())
                    
                    if len(ld_authors) > len(meta["authors"]):
                        meta["authors"] = ld_authors
        except Exception:
            continue

    # 4. DOM Byline Extraction (Discovers co-authors when CMS/JSON-LD only lists primary author)
    byline_candidates = []
    byline_elems = soup.find_all(attrs={'class': re.compile(r'\b(byline|contentFooter__byline|author-name|entry-author|c-byline)\b', re.I)})
    for b in byline_elems:
        for al in b.find_all(['a', 'span', 'li'], attrs={'class': re.compile(r'author|name', re.I)}):
            atxt = al.get_text(strip=True).replace('archive page', '').strip()
            if atxt and 3 <= len(atxt) <= 40 and not any(w in atxt.lower() for w in ['by', 'archive', 'photo', 'share', 'view', 'read', 'post']):
                if atxt not in byline_candidates:
                    byline_candidates.append(atxt)
        if len(byline_candidates) >= 2:
            break
        # Also check for "By X & Y" text
        b_text = b.get_text(separator=' ', strip=True)
        if re.search(r'\bby\s+([A-Z][a-zA-Z\.\s]+)\s+(&|and)\s+([A-Z][a-zA-Z\.\s]+)', b_text, re.I):
            m_by = re.search(r'\bby\s+(.+)', b_text, re.I)
            if m_by:
                by_raw = m_by.group(1).replace('archive page', '').strip()
                parts = [p.strip() for p in re.split(r'\s*(?:&|\band\b|,)\s*', by_raw) if p.strip()]
                cleaned_parts = [p for p in parts if len(p) <= 40 and not any(w in p.lower() for w in ['archive', 'staff', 'photo', 'editor'])]
                if len(cleaned_parts) > len(byline_candidates):
                    byline_candidates = cleaned_parts

    if len(byline_candidates) > len(meta["authors"]):
        meta["authors"] = byline_candidates

    # 5. Clean up title string
    if meta.get("title") and isinstance(meta["title"], str):
        meta["title"] = meta["title"].replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"').strip()

    # 6. Domain & URL Overrides
    lower_url = target_url.lower()
    if 'youtube.com' in lower_url or 'youtu.be' in lower_url:
        meta["item_type"] = "videoRecording"
    elif 'arxiv.org' in lower_url or 'biorxiv.org' in lower_url or 'medrxiv.org' in lower_url:
        meta["item_type"] = "preprint"

    return meta


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def download_remote_pdf(url: str, cookies: str = "", custom_headers: str = "", original_source_url: str = "") -> str:
    """
    Agent Tool: Remote PDF Ingestion Engine.
    Purpose: Downloads PDF binary streams from direct URLs, parses text via pypdf,
    extracts metadata headers, and writes a local disk payload returning a JSON receipt.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    target_url = url.strip().replace('"', '').replace("'", "")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    custom_headers_dict, cookies_dict = _parse_headers_and_cookies(cookies, custom_headers)
    headers.update(custom_headers_dict)

    try:
        response = requests.get(target_url, headers=headers, cookies=cookies_dict, timeout=30, stream=True)
        if response.status_code != 200:
            return f"[ACCESS BARRIER] HTTP download failed with status code {response.status_code}"

        temp_pdf_path = os.path.join(os.environ.get("TEMP", "."), f"temp_download_{uuid.uuid4().hex[:8]}.pdf")
        with open(temp_pdf_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)

        text_pages = []
        pdf_title = ""
        pdf_author = ""
        
        with open(temp_pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            if reader.metadata:
                try:
                    raw_t = reader.metadata.title or reader.metadata.get('/Title', '') or ""
                    pdf_title = str(raw_t).strip()
                except Exception:
                    pdf_title = ""
                try:
                    raw_a = reader.metadata.author or reader.metadata.get('/Author', '') or ""
                    pdf_author = str(raw_a).strip()
                except Exception:
                    pdf_author = ""

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(f"--- PAGE {i+1} ---\n{page_text}")

        try:
            os.remove(temp_pdf_path)
        except Exception:
            pass

        if not text_pages or len("\n\n".join(text_pages).strip()) < 200:
            return f"[ERROR] PDF downloaded successfully from {target_url}, but no extractable text found (Scanned Image PDF suspected or content too short)."

        clean_content = "\n\n".join(text_pages)
        title = pdf_title if pdf_title else target_url.split('/')[-1]
        authors = [pdf_author] if pdf_author else []

        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
        os.makedirs(cache_dir, exist_ok=True)
        temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
        temp_filepath = os.path.join(cache_dir, temp_filename)

        source_line = f"SOURCE: {original_source_url if original_source_url else target_url}\n"
        if original_source_url:
            source_line += f"ARCHIVE_SOURCE: {target_url}\n"

        formatted_payload = (
            f"=== ACQUISITION INDEX ===\n"
            f"{source_line}"
            f"TITLE: {title}\n"
            f"AUTHORS: {', '.join(authors) if authors else 'UNKNOWN'}\n"
            f"PUBLISHED: UNKNOWN\n"
            f"PUBLISHER: UNKNOWN\n"
            f"ITEM_TYPE: report\n"
            f"===========================================================\n\n"
            f"{clean_content}"
        )

        with open(temp_filepath, "w", encoding="utf-8") as f:
            f.write(formatted_payload)

        receipt = {
            "status": "SUCCESS",
            "metadata": {
                "title": title,
                "authors": authors,
                "published_date": "UNKNOWN",
                "publisher": "UNKNOWN",
                "item_type": "report"
            },
            "local_cache_path": temp_filepath,
            "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
        }
        return json.dumps(receipt, indent=2)

    except Exception as e:
        return f"[ERROR] Execution of download_remote_pdf failed: {str(e)}"


def _canonicalize_url_for_archives(url: str) -> str:
    """
    Helper: Canonical URL Normalizer for Web Archives.
    Strips ephemeral tracking tokens, affiliate codes, and subscriber gift link parameters
    (e.g., unlocked_article_code, smid, utm_*, ref, fbclid, gclid) so Wayback and Archive.today
    lookups query the permanent canonical snapshot rather than failing on unique session strings.
    """
    from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
    parsed = urlparse(url.strip())
    if not parsed.query:
        return url.strip()
    
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    clean_params = []
    drop_keys = {'unlocked_article_code', 'smid', 'ref', 'fbclid', 'gclid', 'share_token', 'gift_code', 'gift_link'}
    
    # For major news publications where the path is the complete article identifier:
    is_major_news = any(d in parsed.netloc.lower() for d in [
        'nytimes.com', 'wsj.com', 'theinformation.com', 'economist.com', 
        'bloomberg.com', 'ft.com', 'theatlantic.com', 'washingtonpost.com', 'wired.com'
    ])
    
    for k, v in query_params:
        k_lower = k.lower()
        if k_lower in drop_keys or k_lower.startswith('utm_'):
            continue
        if is_major_news:
            # Drop all session/tracking parameters for known news domains
            continue
        clean_params.append((k, v))
        
    new_query = urlencode(clean_params)
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ''))
    return clean_url


def acquire_gift_article(target_url: str) -> Optional[str]:
    """
    Agent Sub-Tool: High-Fidelity Headless Renderer for Fresh Gift Article Links.
    Purpose: Recovers subscriber gift articles (NYT unlocked_article_code, etc.)
    that fail under raw Python requests due to DataDome/Akamai TLS client checks.
    Runs an offscreen Chromium instance to execute the client JavaScript and render full prose.
    Invoked By: SPYGLASS (download_url auto-routing).
    """
    try:
        from playwright.sync_api import sync_playwright
        import trafilatura
        from bs4 import BeautifulSoup
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--window-position=-2400,-2400', '--window-size=1920,1080']
            )
            page = browser.new_page()
            page.goto(target_url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(3500)
            
            html_content = page.content()
            browser.close()
            
            clean_text = trafilatura.extract(html_content)
            if not clean_text or len(clean_text.strip()) < 500:
                return None
                
            rich_meta = _extract_rich_metadata(html_content, target_url)
            if not rich_meta.get("title") or rich_meta["title"] == target_url:
                soup = BeautifulSoup(html_content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag and title_tag.text:
                    rich_meta["title"] = title_tag.text.strip().split(" - ")[0].split(" | ")[0]
                    
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
            os.makedirs(cache_dir, exist_ok=True)
            temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
            temp_filepath = os.path.join(cache_dir, temp_filename)
            
            formatted_payload = (
                f"=== ACQUISITION INDEX ===\n"
                f"SOURCE: {target_url}\n"
                f"ACQUISITION_METHOD: GIFT_LINK_PLAYWRIGHT_RENDER\n"
                f"TITLE: {rich_meta.get('title', 'Gift Article')}\n"
                f"AUTHORS: {', '.join(rich_meta['authors']) if rich_meta.get('authors') else 'UNKNOWN'}\n"
                f"PUBLISHED: {rich_meta.get('published_date', 'UNKNOWN')}\n"
                f"PUBLISHER: {rich_meta.get('publisher', 'The New York Times' if 'nytimes.com' in target_url else 'UNKNOWN')}\n"
                f"ITEM_TYPE: {rich_meta.get('item_type', 'webpage')}\n"
                f"===========================================================\n\n"
                f"{clean_text}"
            )
            
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(formatted_payload)
                
            receipt = {
                "status": "SUCCESS",
                "metadata": rich_meta,
                "local_cache_path": temp_filepath,
                "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
            }
            return json.dumps(receipt, indent=2)
    except Exception as e:
        print(f"  -> [GIFT LINK RENDER ERROR] {str(e)}")
        return None


def download_url(url: str, cookies: str = "", custom_headers: str = "") -> str:
    """
    Agent Tool: Standard Web Ingestion & Fallback Router.
    Purpose: Executes Tier 1 (requests) -> Tier 2 (Botasaurus) extraction with auto-routing
    for arXiv and remote PDFs. Accepts optional cookies and custom headers.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    target_url = url.strip().replace('"', '').replace("'", "")
    
    # 0. CMS PREVIEW & STAGING PARAMETER SANITIZER (SPYGLASS-HEURISTIC-011)
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed_u = urlparse(target_url)
    if any(p in parsed_u.query.lower() for p in ["x-craft-preview", "preview_token", "preview_id", "wp-preview"]):
        clean_qs = {k: v for k, v in parse_qs(parsed_u.query).items() if not any(p in k.lower() for p in ["x-craft-preview", "preview_token", "preview_id", "wp-preview", "token"])}
        clean_query = urlencode(clean_qs, doseq=True)
        sanitized_url = urlunparse((parsed_u.scheme, parsed_u.netloc, parsed_u.path, parsed_u.params, clean_query, parsed_u.fragment))
        print(f"  -> [URL SANITIZER] Stripped CMS preview query parameters: '{target_url}' -> '{sanitized_url}'")
        target_url = sanitized_url

    lower_target = target_url.lower()

    # 1. STRICT arXiv ROUTING GUARDRAIL
    if "arxiv.org" in lower_target:
        print(f"  -> [SPYGLASS ROUTING] arXiv URL detected ({target_url}). Forwarding to acquire_arxiv_document...")
        return acquire_arxiv_document(target_url)

    # 2. REMOTE PDF AUTO-DETECTION (Path-based to handle trailing query parameters)
    parsed_path = urlparse(lower_target).path
    if parsed_path.endswith(".pdf") or lower_target.endswith(".pdf"):
        print(f"  -> [SPYGLASS ROUTING] Direct PDF URL detected ({target_url}). Forwarding to download_remote_pdf...")
        return download_remote_pdf(target_url, cookies=cookies, custom_headers=custom_headers)

    # 3. GOOGLE DOCS & DRIVE AUTO-DETECTION
    if "docs.google.com/document/d/" in lower_target or "drive.google.com/drive/folders/" in lower_target or "drive.google.com/file/d/" in lower_target:
        print(f"  -> [SPYGLASS ROUTING] Google Docs/Drive URL detected ({target_url}). Forwarding to acquire_google_doc...")
        return acquire_google_doc(target_url)

    # 4. YOUTUBE VIDEO AUTO-DETECTION
    if "youtube.com/watch" in lower_target or "youtu.be/" in lower_target or "youtube.com/shorts/" in lower_target or "youtube.com/live/" in lower_target:
        print(f"  -> [SPYGLASS ROUTING] YouTube Video URL detected ({target_url}). Forwarding to extract_youtube_transcript...")
        from tools.youtube_tools import extract_youtube_transcript
        return extract_youtube_transcript(target_url)

    # 5. SUBSCRIBER GIFT LINK AUTO-DETECTION (NYT, etc.)
    if any(k in lower_target for k in ["unlocked_article_code", "gift_code", "share_token", "gift_link"]):
        print(f"  -> [SPYGLASS ROUTING] Subscriber gift link detected ({target_url}). Attempting headless rendering...")
        gift_receipt = acquire_gift_article(target_url)
        if gift_receipt:
            print(f"  -> [SPYGLASS SUCCESS] Successfully retrieved full gift article via headless renderer.")
            return gift_receipt
        else:
            print(f"  -> [SPYGLASS NOTICE] Gift link rendering returned insufficient prose. Falling back to standard pipeline...")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    custom_headers_dict, cookies_dict = _parse_headers_and_cookies(cookies, custom_headers)
    headers.update(custom_headers_dict)

    html_string = None
    clean_content = None
    jina_meta = None
    
    import trafilatura
    
    # TIER 1: Standard Requests
    try:
        response = requests.get(target_url, headers=headers, cookies=cookies_dict, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/pdf" in content_type:
                print(f"  -> [SPYGLASS ROUTING] Server returned application/pdf for {target_url}. Forwarding to download_remote_pdf...")
                return download_remote_pdf(target_url, cookies=cookies, custom_headers=custom_headers)

            html_string = response.content.decode('utf-8', errors='replace')
            temp_clean = trafilatura.extract(html_string)
            if not temp_clean or len(temp_clean) < 800:
                raise ValueError("Extracted text is suspiciously short (Paywall or JS-Wall suspected).")
            clean_content = temp_clean
        else:
            raise ValueError(f"HTTP {response.status_code}")
            
    except Exception as e1:
        lower_target = target_url.lower()
        # Fast-track known hard paywalls straight to Wayback Machine to avoid 20s Botasaurus stalls
        is_known_paywall = any(d in lower_target for d in [
            "wsj.com", "nytimes.com", "theinformation.com", "economist.com", "bloomberg.com", "ft.com", "barrons.com"
        ])
        if is_known_paywall:
            print(f"  -> [SPYGLASS PAYWALL FAST-PATH] Known subscription domain detected. Bypassing Botasaurus to query Web Archive...")
            try:
                arch_receipt_raw = acquire_archive_snapshot(target_url)
                arch_json = json.loads(arch_receipt_raw)
                if arch_json.get("status") == "SUCCESS":
                    print(f"  -> [SPYGLASS FAST ARCHIVE SUCCESS] Ingested paywalled article via Web Archive.")
                    return arch_receipt_raw
            except Exception as e_fast:
                print(f"  -> [SPYGLASS FAST ARCHIVE FAILED] {str(e_fast)}")

        # TIER 2: Botasaurus (DEPRECATED & BYPASSED per empirical data: 0% recovery, prevents 30-60s local browser freezes)
        # Proceeding directly to Tier 3 / Tier 4 fallbacks.
        jina_key = os.getenv("JINA_API_KEY")
        if jina_key:
            # TIER 3: Jina Reader (Only attempted if JINA_API_KEY is configured)
            try:
                jina_url = f"https://r.jina.ai/{target_url}"
                jina_headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Authorization": f"Bearer {jina_key}",
                    "Accept": "application/json"
                }
                jina_response = requests.get(jina_url, headers=jina_headers, timeout=15)
                if jina_response.status_code == 200:
                    jina_json = jina_response.json().get("data", {})
                    jina_text = jina_json.get("content", "")
                    jina_title = jina_json.get("title", "") or target_url.split('/')[-1]
                    jina_pub = jina_json.get("publishedTime", "UNKNOWN")
                    
                    low_title = jina_title.lower()
                    if any(stub in low_title for stub in ["verification required", "just a moment", "attention required", "cloudflare"]) or len(jina_text.strip()) < 800:
                        raise ValueError(f"Jina returned a paywall/verification stub: '{jina_title}'")

                    clean_content = jina_text
                    html_string = f"<html><body>{jina_text}</body></html>"
                    jina_meta = {
                        "title": jina_title,
                        "published_date": jina_pub
                    }
                    print(f"  -> [SPYGLASS TIER 3 SUCCESS] Ingested URL via Jina Reader. Title: '{jina_title}'")
            except Exception as e3:
                print(f"  -> [SPYGLASS TIER 3 FAILED] Reason: {str(e3)}. Checking Academic OA and Web Archive snapshots...")

        if not clean_content:
            # TIER 4: Fast Fallbacks (Academic OA and Web Archive)

                # TIER 4A: Check for Academic DOI / Open Access PDF
                import re
                if any(ad in lower_target for ad in [
                    "sciencedirect.com", "wiley.com", "springer.com", "nature.com",
                    "ieee.org", "jstor.org", "utppublishing.com", "doi.org", "tandfonline.com"
                ]) or re.search(r'10\.\d{4,9}/', lower_target):
                    try:
                        oa_receipt_raw = resolve_open_access_pdf(target_url)
                        oa_json = json.loads(oa_receipt_raw)
                        if oa_json.get("status") == "SUCCESS":
                            print(f"  -> [SPYGLASS TIER 4 SUCCESS] Ingested academic paper via Open Access PDF resolver.")
                            return oa_receipt_raw
                    except Exception as e_oa:
                        print(f"  -> [SPYGLASS OA RESOLVER FAILED] {str(e_oa)}")

                # TIER 4B: Check for Web Archive Snapshot (Wayback Machine)
                try:
                    arch_receipt_raw = acquire_archive_snapshot(target_url)
                    arch_json = json.loads(arch_receipt_raw)
                    if arch_json.get("status") == "SUCCESS":
                        print(f"  -> [SPYGLASS TIER 4 SUCCESS] Ingested paywalled article via Wayback Machine Archive snapshot.")
                        return arch_receipt_raw
                except Exception as e_arch:
                    print(f"  -> [SPYGLASS ARCHIVE FAILED] {str(e_arch)}")

                # TIER 5: Zotero Translation Server (Metadata & Abstract Fallback for Academic Domains)
                if any(ad in lower_target for ad in ["doi.org", "sciencedirect.com", "nature.com", "springer.com", "wiley.com", "jstor.org", "ieee.org"]) or re.search(r'10\.\d{4,9}/', lower_target):
                    print(f"  -> [SPYGLASS TIER 4 FAILED]. Triggering Tier 5 (Zotero Translation Server)...")
                    try:
                        zotero_endpoint = os.getenv("ZOTERO_TRANSLATOR_URL", "https://zotero-translator-809652732702.us-central1.run.app/web")
                        zotero_resp = requests.post(zotero_endpoint, data=target_url, headers={"Content-Type": "text/plain"}, timeout=12)
                        if zotero_resp.status_code == 200:
                            z_items = zotero_resp.json()
                            if z_items and isinstance(z_items, list) and len(z_items) > 0:
                                z_item = z_items[0]
                                z_title = z_item.get("title") or target_url.split('/')[-1]
                                z_creators = []
                                for c in z_item.get("creators", []):
                                    name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or c.get("name", "")
                                    if name:
                                        z_creators.append(name)
                                
                                z_abstract = z_item.get("abstractNote") or ""
                                clean_content = f"Title: {z_title}\n\nAbstract:\n{z_abstract}\n\nPublication: {z_item.get('publicationTitle', '')}\nDOI: {z_item.get('DOI', '')}"
                                html_string = f"<html><body><h1>{z_title}</h1><p>{z_abstract}</p></body></html>"
                                
                                jina_meta = {
                                    "title": z_title,
                                    "authors": z_creators,
                                    "published_date": z_item.get("date", "UNKNOWN"),
                                    "publisher": z_item.get("publisher") or z_item.get("publicationTitle") or "UNKNOWN",
                                    "item_type": z_item.get("itemType", "journalArticle"),
                                    "doi": z_item.get("DOI", ""),
                                    "journal_title": z_item.get("publicationTitle", ""),
                                    "volume": z_item.get("volume", ""),
                                    "issue": z_item.get("issue", ""),
                                    "pages": z_item.get("pages", ""),
                                    "abstract": z_abstract
                                }
                                print(f"  -> [SPYGLASS TIER 5 SUCCESS] Ingested URL via Zotero Translation Server. Title: '{z_title}'")
                    except Exception as e_zot:
                        print(f"  -> [SPYGLASS TIER 5 FAILED] Zotero translation server error: {str(e_zot)}")

                if not clean_content:
                    e1_msg = str(e1) if 'e1' in locals() else 'HTTP extraction failed'
                    receipt = {
                        "status": "FAILED",
                        "reason": f"[ACCESS BARRIER] Ingestion failed across all active tiers. Tier 1: {e1_msg}"
                    }
                    return json.dumps(receipt, indent=2)

    # Secondary check to guarantee content safety
    if (not clean_content or len(clean_content.strip()) < 200) and not (jina_meta and jina_meta.get("doi")):
        receipt = {
            "status": "FAILED",
            "reason": f"[ACCESS BARRIER] Ingestion succeeded but extracted content density was too low ({len(clean_content.strip()) if clean_content else 0} chars)."
        }
        return json.dumps(receipt, indent=2)

    rich_meta = _extract_rich_metadata(html_string, target_url)
    if jina_meta:
        rich_meta.update(jina_meta)
    
    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
    temp_filepath = os.path.join(cache_dir, temp_filename)
    
    raw_json_string = json.dumps(rich_meta.get("raw_json_ld", []), indent=2)
    
    formatted_payload = (
        f"=== ACQUISITION INDEX ===\n"
        f"SOURCE: {target_url}\n"
        f"TITLE: {rich_meta['title']}\n"
        f"AUTHORS: {', '.join(rich_meta['authors']) if rich_meta['authors'] else 'UNKNOWN'}\n"
        f"PUBLISHED: {rich_meta['published_date']}\n"
        f"PUBLISHER: {rich_meta['publisher']}\n"
        f"ITEM_TYPE: {rich_meta['item_type']}\n"
        f"JOURNAL: {rich_meta['journal_title']}\n"
        f"DOI: {rich_meta['doi']}\n"
        f"VOLUME: {rich_meta['volume']}\n"
        f"ISSUE: {rich_meta['issue']}\n"
        f"PAGES: {rich_meta['pages']}\n"
        f"=== RAW JSON-LD DUMP (FOR FUTURE ONTOLOGY SPECIALIST) ===\n"
        f"{raw_json_string}\n"
        f"===========================================================\n\n"
        f"{clean_content}"
    )
    
    with open(temp_filepath, "w", encoding="utf-8") as f:
        f.write(formatted_payload)

    receipt = {
        "status": "SUCCESS",
        "metadata": {
            "title": rich_meta["title"],
            "authors": rich_meta["authors"],
            "published_date": rich_meta["published_date"],
            "publisher": rich_meta["publisher"],
            "item_type": rich_meta["item_type"],
            "journal_title": rich_meta["journal_title"],
            "doi": rich_meta["doi"],
            "abstract": rich_meta["abstract"]
        },
        "local_cache_path": temp_filepath,
        "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
    }
    return json.dumps(receipt, indent=2)


def precision_html_extract(url: str, include_css: str = "", exclude_css: str = "") -> str:
    """
    Agent Tool: Surgical CSS Scraper.
    Purpose: Used when standard download_url fails or extracts too much noise. 
    Allows explicit inclusion of specific blocks or destruction of noise (like comments) via CSS selectors.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    import urllib.request
    from bs4 import BeautifulSoup

    target_url = url.strip().replace('"', '').replace("'", "").replace('\r', '').replace('\n', '')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    html_bytes = None
    
    # Tier 1 & 2 Fetch Logic
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200: html_bytes = response.content
        else: raise ValueError(f"HTTP {response.status_code}")
    except Exception:
        try:
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html_bytes = response.read()
        except Exception as e2:
            return f"[ACCESS BARRIER] Fetch failed: {str(e2)}"

    if not html_bytes:
        return "[ERROR] Could not acquire bytes."

    soup = BeautifulSoup(html_bytes, "html.parser")

    # 1. Strip out unwanted elements (e.g., comments, ads)
    if exclude_css:
        for element in soup.select(exclude_css):
            element.decompose()

    # 2. Extract only targeted elements (or fallback to body)
    if include_css:
        targeted_elements = soup.select(include_css)
        extracted_text = "\n\n".join([el.get_text(separator="\n", strip=True) for el in targeted_elements])
    else:
        # Clean standard script/style tags if we are taking the whole body
        for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            script.decompose()
        extracted_text = soup.get_text(separator="\n", strip=True)

    native_title = soup.title.string if soup.title else target_url
    purified_text = _clean_string_metadata(extracted_text)

    return f"=== TITLE: {native_title} ===\n=== RAW TEXT ACQUIRED FROM {target_url} ===\n\n{purified_text}"


def acquire_arxiv_document(url: str) -> str:
    """
    Agent Tool: arXiv API Bypass.
    Purpose: Standard web scrapers fail on arXiv PDFs. This tool bypasses scrapers, 
    extracts the canonical ID from the URL, hits the official API for perfect metadata, 
    and fetches the raw HTML body text.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    import re
    import urllib.request
    import urllib.error
    import xml.etree.ElementTree as ET
    from bs4 import BeautifulSoup

    # 1. Isolate the ArXiv ID using Regex (handles post-2007 and legacy formats)
    target_url = url.strip().replace('"', '').replace("'", "")
    id_match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?\/\d{7}(?:v\d+)?)", target_url)
    
    if not id_match:
        return f"[ERROR] Could not extract a valid arXiv ID from the provided URL: {target_url}"
    
    arxiv_id = id_match.group(1)
    
    # 2. Fetch Perfect Metadata from the Official API
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    metadata_block = []
    
    try:
        with urllib.request.urlopen(api_url, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # ArXiv uses the Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entry = root.find('atom:entry', ns)
            
            if entry is not None:
                title = entry.find('atom:title', ns).text.replace('\n', ' ').strip()
                published = entry.find('atom:published', ns).text
                abstract = entry.find('atom:summary', ns).text.strip()
                authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
                
                metadata_block.append(f"=== TITLE: {title} ===")
                metadata_block.append(f"=== AUTHORS: {', '.join(authors)} ===")
                metadata_block.append(f"=== PUBLISHED: {published} ===")
                metadata_block.append(f"=== ARXIV ID: {arxiv_id} ===")
                metadata_block.append(f"=== ABSTRACT ===\n{abstract}\n")
            else:
                metadata_block.append(f"=== ARXIV ID: {arxiv_id} (Metadata not found in API) ===")
    except Exception as e:
        metadata_block.append(f"[METADATA API ERROR] {str(e)}")

    # 3. Fetch Full Body Text from the /html/ endpoint
    html_url = f"https://arxiv.org/html/{arxiv_id}"
    body_text = ""
    
    try:
        req = urllib.request.Request(html_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            html_bytes = response.read()
            soup = BeautifulSoup(html_bytes, "html.parser")
            
            # Clean out scripts, styles, and the standard arXiv navigation headers
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()
            
            # Find the main article body (arXiv HTML usually puts content in 'article' or 'ltx_document')
            article = soup.find("article") or soup.find(class_="ltx_document")
            if article:
                body_text = article.get_text(separator="\n\n", strip=True)
            else:
                body_text = soup.get_text(separator="\n", strip=True)
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  -> [ARXIV HTML 404] HTML version not available for ID {arxiv_id}. Falling back to PDF extraction...")
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            try:
                pdf_req = urllib.request.Request(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(pdf_req, timeout=30) as pdf_response:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(pdf_response.read())
                        temp_path = temp_file.name
                    
                    try:
                        text_pages = []
                        with open(temp_path, "rb") as f:
                            reader = pypdf.PdfReader(f)
                            for i, page in enumerate(reader.pages):
                                page_text = page.extract_text()
                                if page_text:
                                    text_pages.append(f"--- PAGE {i+1} ---\n{page_text}")
                        
                        if text_pages:
                            body_text = "\n\n".join(text_pages)
                        else:
                            body_text = "[CONTENT WARNING] PDF extracted successfully, but yielded 0 text characters."
                    finally:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
            except Exception as pdf_error:
                body_text = f"[CONTENT WARNING] Both HTML and PDF fallbacks failed for arXiv ID {arxiv_id}. PDF error: {str(pdf_error)}"
        else:
            body_text = f"[ACCESS BARRIER] HTML fetch failed: HTTP {e.code}"
    except Exception as e:
        body_text = f"[HTML PARSE ERROR] {str(e)}"

    return "\n".join(metadata_block) + "\n=== FULL TEXT ===\n" + body_text

def extract_local_pdf(zotero_storage_key: str) -> str:
    """
    Agent Tool: Local Zotero PDF Extractor.
    Purpose: Used when cloud firewalls completely block scraping. 
    Allows the agent to extract binary text directly from the local Zotero storage path.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    try:
        user_profile = os.environ.get('USERPROFILE', '')
        if not user_profile: return "[ERROR] USERPROFILE path not found."
            
        zotero_storage_base = Path(user_profile) / "Zotero" / "storage" / zotero_storage_key
        if not zotero_storage_base.exists(): return f"[ERROR] Storage folder not found: {zotero_storage_key}"
            
        pdf_files = list(zotero_storage_base.glob("*.pdf"))
        if not pdf_files: return f"[ERROR] No PDFs found in vault: {zotero_storage_key}"
            
        target_pdf = pdf_files[0]
        text_accumulator = []
        
        with open(target_pdf, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text: text_accumulator.append(page_text)
                    
        return f"=== BINARY EXTRACTION SUCCESS: {target_pdf.name} ===\n\n" + "\n".join(text_accumulator)
    except Exception as e:
        return f"[ERROR] Local binary parsing failed: {str(e)}"


def call_zotero_translator(target_url: str) -> str:
    """
    Agent Tool: Cloud Run Zotero Translation Server.
    Purpose: Resolves paywalled academic papers, journals, and complex metadata 
    by invoking official Zotero translators deployed to Google Cloud Run (Serverless).
    Bypasses paywalls for Nature, ScienceDirect, IEEE, JSTOR, Springer, Wiley, etc.
    Invoked By: SPYGLASS (The Ingestion Engine), PLANK (Zotero Specialist).
    """
    endpoint = os.getenv("ZOTERO_TRANSLATOR_URL", "https://zotero-translator-809652732702.us-central1.run.app/web")
    try:
        headers = {"Content-Type": "text/plain"}
        response = requests.post(endpoint, data=target_url, headers=headers, timeout=45)
        if response.status_code == 200:
            items = response.json()
            if items and isinstance(items, list) and len(items) > 0:
                item = items[0]
                title = item.get("title") or target_url.split('/')[-1]
                authors = []
                for c in item.get("creators", []):
                    name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or c.get("name", "")
                    if name:
                        authors.append(name)
                
                abstract = item.get("abstractNote") or ""
                clean_body = f"Title: {title}\n\nAbstract:\n{abstract}\n\nPublication: {item.get('publicationTitle', '')}\nDOI: {item.get('DOI', '')}"
                
                rich_meta = {
                    "title": title,
                    "authors": authors,
                    "published_date": item.get("date", "UNKNOWN"),
                    "publisher": item.get("publisher") or item.get("publicationTitle") or "UNKNOWN",
                    "item_type": item.get("itemType", "journalArticle"),
                    "journal_title": item.get("publicationTitle", ""),
                    "doi": item.get("DOI", ""),
                    "volume": item.get("volume", ""),
                    "issue": item.get("issue", ""),
                    "pages": item.get("pages", ""),
                    "abstract": abstract,
                    "raw_json_ld": items
                }
                
                cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
                os.makedirs(cache_dir, exist_ok=True)
                temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
                temp_filepath = os.path.join(cache_dir, temp_filename)
                
                formatted_payload = (
                    f"=== ACQUISITION INDEX ===\n"
                    f"SOURCE: {target_url}\n"
                    f"TITLE: {rich_meta['title']}\n"
                    f"AUTHORS: {', '.join(rich_meta['authors']) if rich_meta['authors'] else 'UNKNOWN'}\n"
                    f"PUBLISHED: {rich_meta['published_date']}\n"
                    f"PUBLISHER: {rich_meta['publisher']}\n"
                    f"ITEM_TYPE: {rich_meta['item_type']}\n"
                    f"JOURNAL: {rich_meta['journal_title']}\n"
                    f"DOI: {rich_meta['doi']}\n"
                    f"VOLUME: {rich_meta['volume']}\n"
                    f"ISSUE: {rich_meta['issue']}\n"
                    f"PAGES: {rich_meta['pages']}\n"
                    f"=== RAW JSON-LD DUMP (FOR FUTURE ONTOLOGY SPECIALIST) ===\n"
                    f"{json.dumps(items, indent=2)}\n"
                    f"===========================================================\n\n"
                    f"{clean_body}"
                )
                
                with open(temp_filepath, "w", encoding="utf-8") as f:
                    f.write(formatted_payload)
                    
                receipt = {
                    "status": "SUCCESS",
                    "metadata": rich_meta,
                    "local_cache_path": temp_filepath,
                    "message": f"Successfully translated by Cloud Run Zotero Server. Saved to {temp_filename}"
                }
                return json.dumps(receipt, indent=2)
            else:
                return json.dumps({
                    "status": "FAILED",
                    "reason": "Zotero translation server returned 0 items for this URL."
                }, indent=2)
        else:
            return json.dumps({
                "status": "FAILED",
                "reason": f"Zotero translation server returned HTTP {response.status_code}: {response.text[:200]}"
            }, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "reason": f"Failed to connect to Zotero translation server: {str(e)}"
        }, indent=2)


def acquire_archive_snapshot(target_url: str) -> str:
    """
    Agent Tool: Web Archive Ingestion Engine.
    Purpose: Recovers full-text articles blocked by commercial hard paywalls 
    (WSJ, NYT, Financial Times, Bloomberg, The Information, Economist) by querying 
    the Wayback Machine (archive.org) Availability API. Extracts full prose via trafilatura.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    clean_url = target_url.strip().replace('"', '').replace("'", "")
    canonical_url = _canonicalize_url_for_archives(clean_url)
    if canonical_url != clean_url:
        print(f"  -> [URL CANONICALIZER] Sanitized for Web Archives: '{clean_url}' -> '{canonical_url}'")

    # Wayback Machine Availability API requires the URL query parameter literally unencoded
    wayback_api = f"https://archive.org/wayback/available?url={canonical_url}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}

    try:
        resp = requests.get(wayback_api, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            snapshots = data.get("archived_snapshots", {})
            closest = snapshots.get("closest", {})
            if closest.get("available") and closest.get("url"):
                snapshot_url = closest["url"]
                print(f"  -> [ARCHIVE SNAPSHOT FOUND] Fetching from Wayback: {snapshot_url}")
                snap_resp = requests.get(snapshot_url, headers=headers, timeout=25)
                if snap_resp.status_code == 200:
                    content_type = snap_resp.headers.get("content-type", "").lower()
                    if "application/pdf" in content_type or snap_resp.content.startswith(b"%PDF") or clean_url.lower().endswith(".pdf"):
                        print(f"  -> [ARCHIVE PDF DETECTED] Processing archived PDF payload from {snapshot_url}...")
                        return download_remote_pdf(snapshot_url, original_source_url=clean_url)

                    html_content = snap_resp.text
                    clean_text = trafilatura.extract(html_content)
                    if clean_text and len(clean_text.strip()) >= 300:
                        rich_meta = _extract_rich_metadata(html_content, clean_url)
                        if not rich_meta.get("title") or rich_meta["title"] == clean_url:
                            soup = BeautifulSoup(html_content, 'html.parser')
                            title_tag = soup.find('title')
                            if title_tag and title_tag.text:
                                rich_meta["title"] = title_tag.text.strip().split(" - ")[0].split(" | ")[0]

                        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
                        os.makedirs(cache_dir, exist_ok=True)
                        temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
                        temp_filepath = os.path.join(cache_dir, temp_filename)

                        formatted_payload = (
                            f"=== ACQUISITION INDEX ===\n"
                            f"SOURCE: {clean_url}\n"
                            f"ARCHIVE_SOURCE: {snapshot_url}\n"
                            f"TITLE: {rich_meta.get('title', 'Archived Article')}\n"
                            f"AUTHORS: {', '.join(rich_meta['authors']) if rich_meta.get('authors') else 'UNKNOWN'}\n"
                            f"PUBLISHED: {rich_meta.get('published_date', 'UNKNOWN')}\n"
                            f"PUBLISHER: {rich_meta.get('publisher', 'UNKNOWN')}\n"
                            f"ITEM_TYPE: {rich_meta.get('item_type', 'webpage')}\n"
                            f"===========================================================\n\n"
                            f"{clean_text}"
                        )

                        with open(temp_filepath, "w", encoding="utf-8") as f:
                            f.write(formatted_payload)

                        receipt = {
                            "status": "SUCCESS",
                            "metadata": rich_meta,
                            "local_cache_path": temp_filepath,
                            "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
                        }
                        return json.dumps(receipt, indent=2)

        # 2. FALLBACK ARCHIVE: Query archive.today / archive.ph mirrors
        # First query using canonical URL; fallback to clean_url if different
        urls_to_try = [canonical_url]
        if clean_url != canonical_url:
            urls_to_try.append(clean_url)

        for gw_url in urls_to_try:
            for gateway in ["https://archive.ph", "https://archive.today", "https://archive.is"]:
                try:
                    today_url = f"{gateway}/newest/{gw_url}"
                    today_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    snap_today = requests.get(today_url, headers=today_headers, timeout=8, allow_redirects=True)
                    if snap_today.status_code == 200 and len(snap_today.text) > 1000:
                        html_content = snap_today.text
                        clean_text = trafilatura.extract(html_content)
                        if clean_text and len(clean_text.strip()) >= 500 and not any(w in clean_text.lower() for w in ["no results", "search archive", "archive.today"]):
                            print(f"  -> [ARCHIVE SNAPSHOT FOUND] Rescued article from {gateway}: {snap_today.url}")
                            rich_meta = _extract_rich_metadata(html_content, clean_url)
                            if not rich_meta.get("title") or rich_meta["title"] == clean_url:
                                soup = BeautifulSoup(html_content, 'html.parser')
                                title_tag = soup.find('title')
                                if title_tag and title_tag.text:
                                    rich_meta["title"] = title_tag.text.strip().split(" - ")[0].split(" | ")[0]

                            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
                            os.makedirs(cache_dir, exist_ok=True)
                            temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
                            temp_filepath = os.path.join(cache_dir, temp_filename)

                            formatted_payload = (
                                f"=== ACQUISITION INDEX ===\n"
                                f"SOURCE: {clean_url}\n"
                                f"ARCHIVE_SOURCE: {snap_today.url}\n"
                                f"TITLE: {rich_meta.get('title', 'Archived Article')}\n"
                                f"AUTHORS: {', '.join(rich_meta['authors']) if rich_meta.get('authors') else 'UNKNOWN'}\n"
                                f"PUBLISHED: {rich_meta.get('published_date', 'UNKNOWN')}\n"
                                f"PUBLISHER: {rich_meta.get('publisher', 'UNKNOWN')}\n"
                                f"ITEM_TYPE: {rich_meta.get('item_type', 'webpage')}\n"
                                f"===========================================================\n\n"
                                f"{clean_text}"
                            )

                            with open(temp_filepath, "w", encoding="utf-8") as f:
                                f.write(formatted_payload)

                            receipt = {
                                "status": "SUCCESS",
                                "metadata": rich_meta,
                                "local_cache_path": temp_filepath,
                                "action_required": "Pass 'local_cache_path' to upsert_knowledge_artifact."
                            }
                            return json.dumps(receipt, indent=2)
                except Exception:
                    continue

        return json.dumps({
            "status": "FAILED",
            "reason": f"[NO_ARCHIVE_SNAPSHOT] No valid snapshot available on archive.org or archive.today for {clean_url}"
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[ARCHIVE_ERROR] Failed to query Web Archives: {str(e)}"
        }, indent=2)


def resolve_open_access_pdf(url_or_doi: str) -> str:
    """
    Agent Tool: Open Access Academic PDF Resolver.
    Purpose: Resolves paywalled academic landing pages (ScienceDirect, Wiley, Springer, JSTOR, Nature)
    by extracting the DOI and querying the Unpaywall REST API for legal open-access copies, preprints,
    and institutional repository PDFs. If found, automatically streams the PDF via download_remote_pdf.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    import re
    target = url_or_doi.strip().replace('"', '').replace("'", "")
    doi = ""

    doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)', target)
    if doi_match:
        doi = doi_match.group(1).rstrip('.,;:)')

    if not doi:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[NO_DOI_FOUND] Could not extract DOI from target: {target}"
        }, indent=2)

    print(f"  -> [UNPAYWALL RESOLVER] Extracted DOI: {doi}. Querying Unpaywall API...")
    headers = {"User-Agent": "NPT-Fleet-Bot/1.0 (contact: npt-fleet@reckoning.org)"}
    unpaywall_endpoint = f"https://api.unpaywall.org/v2/{doi}?email=npt-fleet@reckoning.org"

    try:
        resp = requests.get(unpaywall_endpoint, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # Collect all candidate PDF URLs, prioritizing repository/PMC copies over publisher landing stubs
            candidate_pdfs = []
            best_oa = data.get("best_oa_location") or {}
            if best_oa.get("url_for_pdf"):
                candidate_pdfs.append(best_oa["url_for_pdf"])

            for loc in data.get("oa_locations", []):
                p_url = loc.get("url_for_pdf")
                if p_url and p_url not in candidate_pdfs:
                    candidate_pdfs.append(p_url)

            if not candidate_pdfs:
                return json.dumps({
                    "status": "FAILED",
                    "reason": f"[NO_OPEN_ACCESS_PDF] Paper with DOI {doi} is recorded as not Open Access or has no direct PDF link."
                }, indent=2)

            # Try candidate PDFs in sequence until one succeeds
            last_err = ""
            for pdf_url in candidate_pdfs:
                print(f"  -> [UNPAYWALL ATTEMPT] Trying candidate PDF: {pdf_url}...")
                res_receipt = download_remote_pdf(pdf_url)
                try:
                    receipt_json = json.loads(res_receipt)
                    if receipt_json.get("status") == "SUCCESS":
                        if data.get("title"):
                            receipt_json["metadata"]["title"] = data.get("title")
                        receipt_json["metadata"]["doi"] = doi
                        receipt_json["metadata"]["item_type"] = "journalArticle"
                        if data.get("published_date"):
                            receipt_json["metadata"]["published_date"] = data.get("published_date")
                        return json.dumps(receipt_json, indent=2)
                    else:
                        last_err = receipt_json.get("reason", "")
                except Exception as e_parse:
                    last_err = str(res_receipt)

            return json.dumps({
                "status": "FAILED",
                "reason": f"[OA_PDF_DOWNLOAD_FAILED] Attempted {len(candidate_pdfs)} candidate OA links. Last error: {last_err[:150]}"
            }, indent=2)
        else:
            return json.dumps({
                "status": "FAILED",
                "reason": f"[UNPAYWALL_HTTP_ERROR] Unpaywall API returned status {resp.status_code}"
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[UNPAYWALL_ERROR] Failed querying Unpaywall: {str(e)}"
        }, indent=2)


def acquire_google_doc(url: str) -> str:
    """
    Agent Tool: Google Docs Ingestion Engine.
    Purpose: Ingests Google Docs via Google Drive API using npt-fleet-manager service account
    (for documents/folders shared with npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com),
    with an automatic fallback to public plaintext HTTP export for link-shared docs.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    import re, os, uuid, json, urllib.parse
    target_url = url.strip().replace('"', '').replace("'", "")
    
    # Locate Service Account Key
    key_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "credentials", "npt-service-key.json")),
        r"C:\Users\timot\Agentic-Book-Team\npt-service-key.json",
        r"C:\Users\timot\npt-core-agent\npt-service-key.json"
    ]
    key_path = None
    for cand in key_candidates:
        if os.path.exists(cand):
            key_path = cand
            break

    # 1. GOOGLE DRIVE FOLDER ENUMERATION & INGESTION
    match_folder = re.search(r"/drive/folders/([a-zA-Z0-9-_]+)", target_url)
    if match_folder:
        folder_id = match_folder.group(1)
        if not key_path:
            return json.dumps({
                "status": "FAILED",
                "reason": "[ERROR] Google Drive folder ingestion requires service account key in credentials/npt-service-key.json."
            }, indent=2)
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
            drive_service = build('drive', 'v3', credentials=creds)
            
            folder_meta = drive_service.files().get(fileId=folder_id, fields='id, name').execute()
            folder_name = folder_meta.get('name', 'Google Drive Folder')
            
            query = f"'{folder_id}' in parents and trashed=false"
            results = drive_service.files().list(q=query, fields='files(id, name, mimeType, createdTime)').execute()
            files = results.get('files', [])
            files.sort(key=lambda x: x.get('name', ''))
            
            if not files:
                return json.dumps({
                    "status": "FAILED",
                    "reason": f"No files found inside Google Drive folder '{folder_name}' ({folder_id})."
                }, indent=2)
                
            dossier_sections = []
            for f in files:
                fid = f['id']
                fname = f.get('name', 'Untitled Doc')
                fmime = f.get('mimeType', '')
                if 'document' in fmime or 'text' in fmime:
                    try:
                        c = drive_service.files().export(fileId=fid, mimeType='text/plain').execute()
                        t = c.decode('utf-8-sig', errors='replace').strip()
                        dossier_sections.append(f"===========================================================\n=== DOCUMENT: {fname} (ID: {fid}) ===\n===========================================================\n\n{t}\n\n")
                    except Exception as ex:
                        print(f"Error exporting file {fname}: {ex}")
                        
            if not dossier_sections:
                return json.dumps({
                    "status": "FAILED",
                    "reason": f"No readable documents could be exported from folder '{folder_name}'."
                }, indent=2)
                
            combined_text = "\n".join(dossier_sections)
            cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
            os.makedirs(cache_dir, exist_ok=True)
            temp_filename = f"temp_acquire_folder_{folder_id[:8]}.txt"
            temp_filepath = os.path.join(cache_dir, temp_filename)
            
            rich_meta = {
                "title": f"{folder_name} (Collection of {len(dossier_sections)} Documents)",
                "authors": ["Google Drive Folder Collection"],
                "published_date": "UNKNOWN",
                "publisher": "Google Drive",
                "item_type": "manuscript_collection",
                "journal_title": "",
                "doi": "",
                "volume": "",
                "issue": "",
                "pages": "",
                "abstract": f"Complete aggregated dossier of {len(dossier_sections)} research documents from Google Drive folder '{folder_name}'."
            }
            
            formatted_payload = (
                f"=== ACQUISITION INDEX ===\n"
                f"SOURCE: {target_url}\n"
                f"TITLE: {rich_meta['title']}\n"
                f"AUTHORS: {', '.join(rich_meta['authors'])}\n"
                f"PUBLISHED: {rich_meta['published_date']}\n"
                f"PUBLISHER: {rich_meta['publisher']}\n"
                f"ITEM_TYPE: {rich_meta['item_type']}\n"
                f"===========================================================\n\n"
                f"{combined_text}"
            )
            
            with open(temp_filepath, "w", encoding="utf-8") as f:
                f.write(formatted_payload)
                
            receipt = {
                "status": "SUCCESS",
                "metadata": rich_meta,
                "local_cache_path": temp_filepath,
                "message": f"Successfully exported folder '{folder_name}' with {len(dossier_sections)} documents. Saved to {temp_filename}"
            }
            print(f"  -> [SPYGLASS SERVICE ACCOUNT SUCCESS] Ingested Google Drive folder '{folder_name}' ({len(dossier_sections)} docs).")
            return json.dumps(receipt, indent=2)
        except Exception as f_err:
            return json.dumps({
                "status": "FAILED",
                "reason": f"[ERROR] Failed to export Google Drive folder: {str(f_err)}"
            }, indent=2)

    # 2. INDIVIDUAL GOOGLE DOC OR FILE EXTRACTION
    match_doc = re.search(r"/(?:document|file)/d/([a-zA-Z0-9-_]+)", target_url)
    if not match_doc:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[ERROR] Could not extract a valid Google Doc/Drive ID from URL: {target_url}"
        }, indent=2)
        
    doc_id = match_doc.group(1)

    doc_text = None
    title = None
    created_time = "UNKNOWN"
    
    # 1. ATTEMPT SERVICE ACCOUNT INGESTION VIA GOOGLE DRIVE API
    if key_path:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            scopes = ['https://www.googleapis.com/auth/drive.readonly']
            creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Fetch file metadata
            meta = drive_service.files().get(fileId=doc_id, fields='id, name, createdTime, modifiedTime').execute()
            title = meta.get('name')
            created_time = meta.get('createdTime', 'UNKNOWN')
            
            # Export plaintext
            content = drive_service.files().export(fileId=doc_id, mimeType='text/plain').execute()
            doc_text = content.decode('utf-8-sig', errors='replace').strip()
            print(f"  -> [SPYGLASS SERVICE ACCOUNT SUCCESS] Ingested Google Doc '{title}' via Drive API.")
        except Exception as sa_err:
            print(f"  -> [SPYGLASS SERVICE ACCOUNT NOTICE] Drive API attempt on doc {doc_id}: {str(sa_err)}. Trying HTTP export fallback...")

    # 2. ATTEMPT PUBLIC HTTP EXPORT FALLBACK (If Drive API not used or failed)
    if not doc_text:
        export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            response = requests.get(export_url, headers=headers, timeout=20, allow_redirects=True)
            if "accounts.google.com" in response.url or response.status_code in [401, 403]:
                return json.dumps({
                    "status": "FAILED",
                    "reason": (
                        "[ACCESS BARRIER] Google Doc is private (Restricted) and not shared with npt-fleet-manager service account. "
                        "To grant access, share the doc/folder with 'npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com' (Viewer) "
                        "or change General Access to 'Anyone with the link'."
                    )
                }, indent=2)
                
            if response.status_code != 200:
                return json.dumps({
                    "status": "FAILED",
                    "reason": f"[ACCESS BARRIER] Google Docs export failed with HTTP {response.status_code}"
                }, indent=2)
                
            doc_text = response.content.decode("utf-8-sig", errors="replace").strip()
            
            # Parse title from Content-Disposition if not yet found
            if not title:
                cd = response.headers.get("Content-Disposition", "")
                if "filename*=" in cd:
                    try:
                        fn_star = cd.split("filename*=")[1].split(";")[0].strip()
                        if "''" in fn_star:
                            encoding, encoded_title = fn_star.split("''", 1)
                            title = urllib.parse.unquote(encoded_title)
                    except Exception:
                        pass
                elif "filename=" in cd:
                    try:
                        raw_fn = cd.split("filename=")[1].split(";")[0].strip(' "')
                        title = raw_fn[:-4] if raw_fn.endswith(".txt") else raw_fn
                    except Exception:
                        pass
        except Exception as http_err:
            return json.dumps({
                "status": "FAILED",
                "reason": f"[ERROR] Failed to export Google Doc: {str(http_err)}"
            }, indent=2)

    if not doc_text or len(doc_text) < 10:
        return json.dumps({
            "status": "FAILED",
            "reason": "[ACCESS BARRIER] Google Doc exported empty or insufficient content."
        }, indent=2)

    if not title:
        title = f"Google Doc {doc_id[:8]}"
        first_line = doc_text.split("\n")[0].strip()
        if first_line and len(first_line) < 100:
            title = first_line

    cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
    os.makedirs(cache_dir, exist_ok=True)
    temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
    temp_filepath = os.path.join(cache_dir, temp_filename)
    
    rich_meta = {
        "title": title,
        "authors": ["Google Doc Export"],
        "published_date": created_time,
        "publisher": "Google Docs",
        "item_type": "manuscript",
        "journal_title": "",
        "doi": "",
        "volume": "",
        "issue": "",
        "pages": "",
        "abstract": doc_text[:300]
    }
    
    formatted_payload = (
        f"=== ACQUISITION INDEX ===\n"
        f"SOURCE: {target_url}\n"
        f"TITLE: {rich_meta['title']}\n"
        f"AUTHORS: {', '.join(rich_meta['authors'])}\n"
        f"PUBLISHED: {rich_meta['published_date']}\n"
        f"PUBLISHER: {rich_meta['publisher']}\n"
        f"ITEM_TYPE: {rich_meta['item_type']}\n"
        f"JOURNAL: \n"
        f"DOI: \n"
        f"VOLUME: \n"
        f"ISSUE: \n"
        f"PAGES: \n"
        f"=== RAW JSON-LD DUMP (FOR FUTURE ONTOLOGY SPECIALIST) ===\n"
        f"[]\n"
        f"===========================================================\n\n"
        f"{doc_text}"
    )
    
    with open(temp_filepath, "w", encoding="utf-8") as f:
        f.write(formatted_payload)
        
    receipt = {
        "status": "SUCCESS",
        "metadata": rich_meta,
        "local_cache_path": temp_filepath,
        "message": f"Successfully exported Google Doc '{title}'. Saved to {temp_filename}"
    }
    return json.dumps(receipt, indent=2)


def stevedore_local_epub(epub_path: str = "") -> str:
    """
    Agent Tool: Local EPUB Stevedore & Book Partition Engine.
    Purpose: Unpacks full-length book EPUBs from the local inbox (cargo_cache/inbox/), 
    extracts metadata and reading spine, segments the endnote dossier by chapter,
    generates self-contained chapter assets with complete parent book provenance back-pointers
    and attached citations, uploads to GCS (acquisitions/*.txt), and registers both 
    a Master Book Reference (item_type='book') and Chapter Assets (item_type='bookSection') 
    in cargo.content_metadata.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    import zipfile
    import glob
    import unicodedata
    import xml.etree.ElementTree as ET
    from bs4 import BeautifulSoup
    from .cloud_knowledge_tools import _get_bucket
    from .cargo_db_tools import _get_strict_cargo_connection

    def _slugify(text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()
        text = re.sub(r'[\'\"]', '', text)
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')

    target_file = (epub_path or "").strip().replace('"', '').replace("'", "")
    if not target_file:
        inbox_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache", "inbox"))
        epubs = glob.glob(os.path.join(inbox_dir, "*.epub"))
        if not epubs:
            return json.dumps({
                "status": "FAILED",
                "reason": f"[NO_EPUB_FOUND] No EPUB files found in {inbox_dir}. Drop an .epub into cargo_cache/inbox/ first."
            }, indent=2)
        target_file = epubs[0]

    if not os.path.exists(target_file):
        return json.dumps({
            "status": "FAILED",
            "reason": f"[FILE_NOT_FOUND] Target EPUB does not exist: {target_file}"
        }, indent=2)

    try:
        bucket = _get_bucket()
        conn = _get_strict_cargo_connection()
        if not conn:
            return json.dumps({"status": "FAILED", "reason": "[DATABASE_ERROR] Cannot connect to cargo database."}, indent=2)

        with zipfile.ZipFile(target_file, 'r') as z:
            file_list = z.namelist()

            # Locate OPF
            container_xml = z.read("META-INF/container.xml")
            c_root = ET.fromstring(container_xml)
            rootfile = c_root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
            opf_path = rootfile.attrib.get("full-path") if rootfile is not None else None
            if not opf_path:
                for f in file_list:
                    if f.endswith(".opf"):
                        opf_path = f
                        break

            opf_data = z.read(opf_path)
            opf_dir = os.path.dirname(opf_path)
            opf_root = ET.fromstring(opf_data)

            ns = {'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
            
            # Extract Metadata
            title_el = opf_root.find(".//dc:title", ns)
            creator_el = opf_root.find(".//dc:creator", ns)
            pub_el = opf_root.find(".//dc:publisher", ns)
            date_el = opf_root.find(".//dc:date", ns)
            
            book_title = title_el.text.strip() if title_el is not None and title_el.text else "Unknown Book"
            book_author = creator_el.text.strip() if creator_el is not None and creator_el.text else "Unknown Author"
            book_pub = pub_el.text.strip() if pub_el is not None and pub_el.text else "Unknown Publisher"
            book_date = date_el.text.strip() if date_el is not None and date_el.text else str(datetime.now().year)
            
            book_isbn = "UNKNOWN"
            for id_elem in opf_root.findall(".//dc:identifier", ns):
                txt = id_elem.text or ""
                if "isbn" in txt.lower() or id_elem.attrib.get("{http://www.idpf.org/2007/opf}scheme", "").lower() == "isbn":
                    clean_isbn = re.sub(r'[^0-9X]', '', txt.upper())
                    if clean_isbn:
                        book_isbn = clean_isbn
                        break
                elif re.match(r'^\d{10}(\d{3})?$', txt.strip()):
                    book_isbn = txt.strip()

            # Manifest & Spine
            manifest = {}
            for item in opf_root.findall(".//opf:item", ns):
                manifest[item.attrib.get("id")] = (item.attrib.get("href"), item.attrib.get("media-type"))

            spine_hrefs = []
            for itemref in opf_root.findall(".//opf:itemref", ns):
                idref = itemref.attrib.get("idref")
                if idref in manifest:
                    spine_hrefs.append(manifest[idref][0])

            # Endnotes segmentation
            endnotes_map = {}
            for href in spine_hrefs:
                if "endnote" in href.lower() or "note" in href.lower():
                    full_href = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
                    if full_href in file_list:
                        raw_notes = z.read(full_href).decode('utf-8', errors='ignore')
                        soup_notes = BeautifulSoup(raw_notes, 'html.parser')
                        for h2 in soup_notes.find_all('h2'):
                            header_key = h2.get_text(strip=True).upper()
                            sibs = []
                            curr = h2.next_sibling
                            while curr:
                                if getattr(curr, 'name', None) == 'h2':
                                    break
                                txt = curr.get_text(strip=True) if hasattr(curr, 'get_text') else str(curr).strip()
                                if txt:
                                    sibs.append(txt)
                                curr = curr.next_sibling
                            endnotes_map[header_key] = "\n\n".join(sibs)
                        break

            master_slug = f"{_slugify(book_title)}-{_slugify(book_author)}-{book_date[:4]}"
            book_basename = os.path.basename(target_file)
            
            all_sections_prose = []
            chapter_receipts = []
            chapter_idx = 0
            cur = conn.cursor()

            for href in spine_hrefs:
                full_href = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
                if full_href not in file_list or not (full_href.endswith('.xhtml') or full_href.endswith('.html')):
                    continue

                raw_bytes = z.read(full_href)
                soup = BeautifulSoup(raw_bytes.decode('utf-8', errors='ignore'), 'html.parser')
                
                body = soup.body if soup.body else soup
                md_lines = []
                chapter_heading = ""
                
                for tag in body.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'blockquote', 'ul', 'ol']):
                    txt = tag.get_text(strip=True)
                    if not txt: continue
                    if tag.name == 'h1':
                        if not chapter_heading: chapter_heading = txt
                        md_lines.append(f"\n# {txt}\n")
                    elif tag.name == 'h2':
                        if not chapter_heading: chapter_heading = txt
                        md_lines.append(f"\n## {txt}\n")
                    elif tag.name == 'h3': md_lines.append(f"\n### {txt}\n")
                    elif tag.name == 'blockquote': md_lines.append(f"\n> {txt}\n")
                    elif tag.name in ['ul', 'ol']:
                        for li in tag.find_all('li'):
                            li_txt = li.get_text(strip=True)
                            if li_txt: md_lines.append(f"* {li_txt}")
                        md_lines.append("")
                    elif tag.name == 'p': md_lines.append(f"{txt}\n")
                    
                prose = "\n".join(md_lines).strip()
                if len(prose) < 600 and not any(k in href.lower() for k in ['epigraph', 'intro']):
                    continue
                all_sections_prose.append(prose)

                is_intro = "intro" in href.lower()
                is_chapter = "ch" in href.lower() or "chapter" in href.lower()

                if is_intro or is_chapter:
                    chapter_idx += 1 if is_chapter else 0
                    if is_intro:
                        sec_num = 0
                        sec_title = "Introduction"
                        ch_slug = f"{_slugify(book_title)}-intro-{_slugify(book_author)}-{book_date[:4]}"
                    else:
                        sec_num = chapter_idx
                        clean_h = re.sub(r'^CHAPTER\s*\d+\s*', '', chapter_heading, flags=re.IGNORECASE).strip()
                        sec_title = clean_h if clean_h else f"Chapter {chapter_idx}"
                        ch_slug = f"{_slugify(book_title)}-ch{sec_num:02d}-{_slugify(sec_title)}-{_slugify(book_author)}-{book_date[:4]}"

                    # Match endnotes
                    matched_notes = ""
                    if is_intro:
                        for k, v in endnotes_map.items():
                            if "INTRO" in k: matched_notes = v; break
                    else:
                        for k, v in endnotes_map.items():
                            if f"CHAPTER {sec_num}" in k: matched_notes = v; break

                    full_ch_title = f"{book_title}: {('Introduction' if is_intro else f'Chapter {sec_num}')} — {sec_title}"
                    src_url = f"local://cargo_cache/inbox/{book_basename}#{href}"
                    
                    ch_payload = (
                        f"=== ACQUISITION INDEX ===\n"
                        f"SOURCE: {src_url}\n"
                        f"TITLE: {full_ch_title}\n"
                        f"AUTHORS: {book_author}\n"
                        f"PUBLISHED: {book_date}\n"
                        f"PUBLISHER: {book_pub}\n"
                        f"ITEM_TYPE: bookSection\n"
                        f"BOOK_TITLE: {book_title}\n"
                        f"BOOK_AUTHORS: {book_author}\n"
                        f"BOOK_PUBLISHER: {book_pub}\n"
                        f"BOOK_PUBLISHED: {book_date}\n"
                        f"BOOK_ISBN: {book_isbn}\n"
                        f"CHAPTER_NUMBER: {sec_num}\n"
                        f"CHAPTER_TITLE: {sec_title}\n"
                        f"PARENT_BOOK_SLUG: {master_slug}\n"
                        f"===========================================================\n\n"
                        f"{prose}\n"
                    )
                    if matched_notes:
                        ch_payload += f"\n\n## CHAPTER ENDNOTES & SOURCE CITATIONS\n\n{matched_notes}\n"

                    gcs_path = f"gs://{bucket.name}/acquisitions/{ch_slug}.txt"
                    blob = bucket.blob(f"acquisitions/{ch_slug}.txt")
                    blob.upload_from_string(ch_payload, content_type="text/plain; charset=utf-8")

                    cur.execute("SELECT id FROM cargo.content_metadata WHERE source_url = %s;", (src_url,))
                    existing = cur.fetchone()
                    authors_json = json.dumps([book_author])
                    kw_json = json.dumps({
                        "parent_book_title": book_title,
                        "parent_book_slug": master_slug,
                        "isbn": book_isbn,
                        "chapter_number": sec_num,
                        "chapter_title": sec_title,
                        "endnotes_attached": bool(matched_notes)
                    })

                    if existing:
                        ch_id = existing[0]
                        cur.execute("""
                            UPDATE cargo.content_metadata
                            SET item_type = 'bookSection', title = %s, authors = %s, publication_title = %s,
                                publication_date = %s, keywords = %s, gcp_bucket_path = %s
                            WHERE id = %s;
                        """, (full_ch_title, authors_json, book_title, book_date, kw_json, gcs_path, ch_id))
                    else:
                        cur.execute("""
                            INSERT INTO cargo.content_metadata (
                                source_url, item_type, title, authors, publication_title, publication_date,
                                keywords, rights, gcp_bucket_path, created_at
                            ) VALUES (%s, 'bookSection', %s, %s, %s, %s, %s, 'All Rights Reserved', %s, NOW())
                            RETURNING id;
                        """, (src_url, full_ch_title, authors_json, book_title, book_date, kw_json, gcs_path))
                        ch_id = cur.fetchone()[0]
                    conn.commit()

                    chapter_receipts.append({
                        "id": ch_id,
                        "chapter_number": sec_num,
                        "title": full_ch_title,
                        "slug": ch_slug,
                        "gcs_path": gcs_path,
                        "size_chars": len(ch_payload)
                    })

            # Master Book Reference
            master_src_url = f"local://cargo_cache/inbox/{book_basename}"
            master_payload = (
                f"=== ACQUISITION INDEX ===\n"
                f"SOURCE: {master_src_url}\n"
                f"TITLE: {book_title}\n"
                f"AUTHORS: {book_author}\n"
                f"PUBLISHED: {book_date}\n"
                f"PUBLISHER: {book_pub}\n"
                f"ITEM_TYPE: book\n"
                f"BOOK_ISBN: {book_isbn}\n"
                f"ROLE: MASTER_BOOK_REFERENCE_ONLY (Do not ingest into VDB or single-agent audit)\n"
                f"TOTAL_CHAPTERS_EXTRACTED: {len(chapter_receipts)}\n"
                f"===========================================================\n\n"
                + "\n\n---\n\n".join(all_sections_prose)
            )
            master_gcs = f"gs://{bucket.name}/acquisitions/{master_slug}.txt"
            blob_master = bucket.blob(f"acquisitions/{master_slug}.txt")
            blob_master.upload_from_string(master_payload, content_type="text/plain; charset=utf-8")

            cur.execute("SELECT id FROM cargo.content_metadata WHERE source_url = %s;", (master_src_url,))
            existing_master = cur.fetchone()
            master_kw = json.dumps({"isbn": book_isbn, "role": "master_reference", "chapters_count": len(chapter_receipts)})
            if existing_master:
                master_id = existing_master[0]
                cur.execute("""
                    UPDATE cargo.content_metadata
                    SET item_type = 'book', title = %s, authors = %s, publication_title = %s,
                        publication_date = %s, keywords = %s, gcp_bucket_path = %s
                    WHERE id = %s;
                """, (book_title, json.dumps([book_author]), book_pub, book_date, master_kw, master_gcs, master_id))
            else:
                cur.execute("""
                    INSERT INTO cargo.content_metadata (
                        source_url, item_type, title, authors, publication_title, publication_date,
                        keywords, rights, gcp_bucket_path, created_at
                    ) VALUES (%s, 'book', %s, %s, %s, %s, %s, 'All Rights Reserved', %s, NOW())
                    RETURNING id;
                """, (master_src_url, book_title, json.dumps([book_author]), book_pub, book_date, master_kw, master_gcs))
                master_id = cur.fetchone()[0]
            conn.commit()
            conn.close()

            return json.dumps({
                "status": "SUCCESS",
                "book_title": book_title,
                "author": book_author,
                "isbn": book_isbn,
                "master_asset_id": master_id,
                "master_slug": master_slug,
                "total_chapters_stevedored": len(chapter_receipts),
                "chapters": chapter_receipts
            }, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "FAILED",
            "reason": f"[EPUB_STEVEDORE_ERROR] Failed to stevedore EPUB: {str(e)}"
        }, indent=2)