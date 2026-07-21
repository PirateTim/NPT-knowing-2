"""
NPT Fleet Tools: Content Acquisition & Extraction Primitives
Architecture: Tiered HTTP Fallbacks & Strict UTF-8 Sanitization
"""
import os
import json
import requests
import urllib.request
import trafilatura
import html
from pathlib import Path
import pypdf
import uuid
from bs4 import BeautifulSoup
from botasaurus.browser import browser, Driver


# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

@browser(headless=True)
def botasaurus_fetch(driver: Driver, data: dict):
    """
    Internal Helper: Botasaurus Anti-Detect Engine.
    Purpose: Acts as the heavy Tier 2 fallback to bypass Cloudflare/PerimeterX 
    barriers when standard requests fail. Returns the fully rendered DOM.
    Invoked By: Called internally by download_url.
    """
    url = data.get("url")
    driver.get(url)
    return driver.page_html

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

        # OpenGraph
        elif prop == 'og:title' and meta["title"] == target_url: meta["title"] = content
        elif prop == 'og:site_name' and meta["publisher"] == "UNKNOWN": meta["publisher"] = content
        elif prop == 'article:author' and not meta["authors"]: meta["authors"].append(content)
        elif prop == 'article:published_time' and meta["published_date"] == "UNKNOWN": meta["published_date"] = content
        elif prop == 'og:type':
            if content in ['article', 'journal']: meta["item_type"] = "journalArticle"
            elif content in ['video', 'video.other']: meta["item_type"] = "videoRecording"

    if highwire_authors: meta["authors"] = highwire_authors
    elif dc_authors and not meta["authors"]: meta["authors"] = dc_authors

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
                
                if 'author' in item and not meta["authors"]:
                    authors = item['author']
                    if isinstance(authors, dict): meta["authors"] = [authors.get('name')]
                    elif isinstance(authors, list): meta["authors"] = [a.get('name') for a in authors if isinstance(a, dict)]
        except Exception:
            continue

    # 4. Domain & URL Overrides
    lower_url = target_url.lower()
    if 'youtube.com' in lower_url or 'youtu.be' in lower_url:
        meta["item_type"] = "videoRecording"
    elif 'arxiv.org' in lower_url or 'biorxiv.org' in lower_url or 'medrxiv.org' in lower_url:
        meta["item_type"] = "preprint"

    return meta


# =====================================================================
# AGENT TOOLS (Exposed via tool_dispatcher.py)
# =====================================================================

def download_remote_pdf(url: str, cookies: str = "", custom_headers: str = "") -> str:
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
                pdf_title = reader.metadata.get('/Title', '') or ""
                pdf_author = reader.metadata.get('/Author', '') or ""

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(f"--- PAGE {i+1} ---\n{page_text}")

        try:
            os.remove(temp_pdf_path)
        except Exception:
            pass

        if not text_pages:
            return f"[ERROR] PDF downloaded successfully from {target_url}, but no extractable text found (Scanned Image PDF suspected)."

        clean_content = "\n\n".join(text_pages)
        title = pdf_title if pdf_title else target_url.split('/')[-1]
        authors = [pdf_author] if pdf_author else []

        cache_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cargo_cache"))
        os.makedirs(cache_dir, exist_ok=True)
        temp_filename = f"temp_acquire_{uuid.uuid4().hex[:8]}.txt"
        temp_filepath = os.path.join(cache_dir, temp_filename)

        formatted_payload = (
            f"=== ACQUISITION INDEX ===\n"
            f"SOURCE: {target_url}\n"
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


def download_url(url: str, cookies: str = "", custom_headers: str = "") -> str:
    """
    Agent Tool: Standard Web Ingestion & Fallback Router.
    Purpose: Executes Tier 1 (requests) -> Tier 2 (Botasaurus) extraction with auto-routing
    for arXiv and remote PDFs. Accepts optional cookies and custom headers.
    Invoked By: SPYGLASS (The Ingestion Engine).
    """
    target_url = url.strip().replace('"', '').replace("'", "")
    lower_target = target_url.lower()

    # 1. STRICT arXiv ROUTING GUARDRAIL
    if "arxiv.org" in lower_target:
        print(f"  -> [SPYGLASS ROUTING] arXiv URL detected ({target_url}). Forwarding to acquire_arxiv_document...")
        return acquire_arxiv_document(target_url)

    # 2. REMOTE PDF AUTO-DETECTION
    if lower_target.endswith(".pdf"):
        print(f"  -> [SPYGLASS ROUTING] Direct PDF URL detected ({target_url}). Forwarding to download_remote_pdf...")
        return download_remote_pdf(target_url, cookies=cookies, custom_headers=custom_headers)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    custom_headers_dict, cookies_dict = _parse_headers_and_cookies(cookies, custom_headers)
    headers.update(custom_headers_dict)

    html_string = None
    
    # TIER 1: Standard Requests
    try:
        response = requests.get(target_url, headers=headers, cookies=cookies_dict, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/pdf" in content_type:
                print(f"  -> [SPYGLASS ROUTING] Server returned application/pdf for {target_url}. Forwarding to download_remote_pdf...")
                return download_remote_pdf(target_url, cookies=cookies, custom_headers=custom_headers)

            html_string = response.content.decode('utf-8', errors='replace')
            
            import trafilatura
            temp_clean = trafilatura.extract(html_string)
            if not temp_clean or len(temp_clean) < 800:
                raise ValueError("Extracted text is suspiciously short (Paywall or JS-Wall suspected).")
                
        else: raise ValueError(f"HTTP {response.status_code}")
        
    except Exception as e1:
        print(f"  -> [SPYGLASS TIER 1 FAILED] Reason: {str(e1)}. Triggering Botasaurus...")
        try:
            bota_result = botasaurus_fetch([{"url": target_url}])
            if bota_result and bota_result[0]:
                html_string = bota_result[0]
            else: raise ValueError("Botasaurus returned empty DOM.")
        except Exception as e2:
            return f"[ACCESS BARRIER] Both extraction tiers failed. Tier 2 Error: {str(e2)}"

    if not html_string: return f"[ERROR] Failed to acquire HTML."
    
    clean_content = trafilatura.extract(html_string) or BeautifulSoup(html_string, 'html.parser').get_text(separator='\n', strip=True)[:10000]
    rich_meta = _extract_rich_metadata(html_string, target_url)
    
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
            body_text = "[CONTENT WARNING] Full HTML text is not yet available for this paper. The author has not compiled the LaTeX to HTML, or it is a legacy paper. Only the Abstract is provided above."
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