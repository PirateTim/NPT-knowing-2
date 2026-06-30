"""
NPT Fleet Tools: Content Acquisition & Extraction Primitives
Architecture: Tiered HTTP Fallbacks & Strict UTF-8 Sanitization
"""
import os
import requests
import urllib.request
import trafilatura
import html
from pathlib import Path
import pypdf

def _clean_string_metadata(text_str: str) -> str:
    """Resolves standard HTML entities and normalizes string layout to clean UTF-8 text."""
    if not text_str:
        return ""
    unescaped_text = html.unescape(text_str)
    return unescaped_text.encode('utf-8', errors='ignore').decode('utf-8')

def download_url(url: str) -> str:
    """
    Downloads raw HTML using a Tier 1 (Requests) -> Tier 2 (Urllib) fallback sequence.
    Extracts and purifies text via Trafilatura.
    """
    target_url = url.strip().replace('"', '').replace("'", "").replace('\r', '').replace('\n', '')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    html_bytes = None
    
    # TIER 1: Standard Requests
    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        if response.status_code == 200:
            html_bytes = response.content
        else:
            raise ValueError(f"HTTP {response.status_code}")
    except Exception as e1:
        # TIER 2: Urllib Fallback
        try:
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html_bytes = response.read()
        except Exception as e2:
            return f"[ACCESS BARRIER] Both extraction tiers failed for {target_url}. Error: {str(e2)}"

    # Parse and Clean
    if html_bytes:
        try:
            html_string = html_bytes.decode('utf-8', errors='replace')
        except Exception:
            html_string = html_bytes.decode('latin-1', errors='replace')
            
        clean_content = trafilatura.extract(html_string)
        if not clean_content:
            clean_content = html_string[:10000] # Fallback to raw string if Trafilatura fails
            
        purified_text = _clean_string_metadata(clean_content)
        
        # Extract basic native title for context
        native_title = target_url
        metadata = trafilatura.extract_metadata(html_string)
        if metadata and hasattr(metadata, 'title') and metadata.title:
            native_title = _clean_string_metadata(metadata.title)
            
        return f"=== TITLE: {native_title} ===\n=== RAW TEXT ACQUIRED FROM {target_url} ===\n\n{purified_text}"
        
    return f"[ERROR] Failed to acquire readable bytes from {target_url}."


def precision_html_extract(url: str, include_css: str = "", exclude_css: str = "") -> str:
    """
    Surgically extracts HTML using CSS selectors. 
    Allows explicit inclusion of specific blocks or exclusion of noise (like comments).
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
    Extracts the canonical arXiv ID from any arXiv URL variant (abs/pdf/html),
    queries the official API for structured metadata, and fetches the full HTML text.
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
    """Bypasses cloud firewalls by extracting binary text from local Zotero PDFs."""
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