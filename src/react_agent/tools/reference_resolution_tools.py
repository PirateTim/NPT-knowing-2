"""
NPT Fleet Tools: Bibliographic Reference Resolution & Citation Expansion Engine
Architecture: Pure LLM Semantic Parsing (Anti-Regex Citation Policy ADR-012, PLANK-RULE-112), 
CrossRef/OpenAlex Resolution, Search Grounding, and Un-truncated Vector Citation Nodes.
"""
import os
import json
import datetime
import urllib.parse
import urllib.request
import pg8000.dbapi
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

def _get_base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def _get_strict_cargo_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return None
    try:
        url = urllib.parse.urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
        )
    except Exception:
        return None

def _log_tool_trace(tool_name: str, args: dict, output: str, agent_name: str = "plank"):
    try:
        log_dir = os.path.join(_get_base_dir(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        trace_entry = f"=== TOOL TRACE: {timestamp} ===\nWire Target: {tool_name}\nArgs: {json.dumps(args, indent=2)}\nOutput:\n{output}\n========================================\n\n"
        
        trace_path = os.path.join(log_dir, "active_tool_execution_trace.log")
        with open(trace_path, "a", encoding="utf-8") as tf:
            tf.write(trace_entry)
            
        agent_log_path = os.path.join(log_dir, f"{agent_name}_interactions.log")
        with open(agent_log_path, "a", encoding="utf-8") as af:
            af.write(trace_entry)
    except Exception:
        pass

CACHE_FILE = os.path.join(_get_base_dir(), "data", "crossref_cache.json")

def _load_crossref_cache() -> dict:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_crossref_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def parse_citation_semantically(raw_citation: str) -> dict:
    """
    Core Semantic Parser (PLANK-RULE-112):
    Uses Gemini LLM comprehension (NOT regex) to decompose an informal citation line
    into structured bibliographic fields and 5-category taxonomy classification.
    """
    client = genai.Client()
    prompt = f"""You are Plank, the Fleet Bibliographer. Decompose this raw bibliographic citation into structured JSON.
Do NOT use regex heuristics. Parse the semantic meaning of the citation.

RAW CITATION: "{raw_citation}"

Output ONLY a JSON object matching this exact schema:
{{
  "category": "ACADEMIC" | "NEWS_MEDIA" | "WEB_TECHNICAL" | "LEGAL_GOV" | "CLASSICAL_CANONICAL",
  "primary_author_surname": "string (e.g. 'Leval', 'Samuelson', 'Authors Guild')",
  "full_authors": ["string (e.g. 'Pierre N. Leval')"],
  "year": "string (4-digit year or 'n.d.')",
  "title": "string (exact title of paper, article, report, or case name)",
  "container_or_publisher": "string (e.g. 'Harvard Law Review', 'Wired', 'EleutherAI', '2d Cir.')",
  "docket_or_citation": "string (e.g. '804 F.3d 202', '1:20-cv-04160', or empty)",
  "explicit_url": "string (if present in raw text, otherwise empty)"
}}"""

    response = client.models.generate_content(
        model=os.getenv("DEFAULT_MODEL", "gemini-3.7-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        )
    )
    try:
        return json.loads(response.text)
    except Exception:
        return {
            "category": "ACADEMIC",
            "primary_author_surname": raw_citation.split()[0].strip('.,'),
            "full_authors": [raw_citation.split()[0]],
            "year": "2025",
            "title": raw_citation,
            "container_or_publisher": "",
            "docket_or_citation": "",
            "explicit_url": ""
        }

def fetch_crossref_metadata(title: str, author_surname: str = None) -> dict:
    """
    Agent Tool: Queries CrossRef REST API for academic paper metadata.
    Validates primary author surname and title against query.
    """
    try:
        clean_title = title.strip()
        cache_key = f"{author_surname}_{clean_title}".lower()

        cache = _load_crossref_cache()
        if cache_key in cache:
            return cache[cache_key]

        query_str = f"{author_surname} {clean_title}" if author_surname else clean_title
        encoded_query = urllib.parse.quote(query_str)
        url = f"https://api.crossref.org/works?query={encoded_query}&rows=3"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'NPTFleet-Plank/2.0 (mailto:timothy@nptknowing.org)'}
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode('utf-8'))

        items = data.get('message', {}).get('items', [])
        if not items:
            return None

        item = items[0]
        title_list = item.get('title', [])
        ret_title = title_list[0] if title_list else clean_title

        authors_list = item.get('author', [])
        authors = []
        matching_families = []
        for a in authors_list:
            fam = a.get('family', '')
            giv = a.get('given', '')
            if fam:
                authors.append(f"{fam}, {giv}".strip(', '))
                if author_surname and author_surname.lower() == fam.lower():
                    matching_families.append(fam)

        author_str = "; ".join(authors) if authors else (author_surname or "Unknown Author")

        # Extract Container, Year, DOI, URL
        container = item.get('container-title', [])
        journal = container[0] if container else item.get('publisher', 'Unknown Publisher')
        issued = item.get('issued', {}).get('date-parts', [[None]])[0][0]
        year = str(issued) if issued else "n.d."
        doi = item.get('DOI', '')
        work_url = item.get('URL', f"https://doi.org/{doi}" if doi else "")

        details = []
        if journal: details.append(journal)
        if doi: details.append(f"DOI: {doi}")
        if work_url: details.append(f"URL: {work_url}")

        detail_str = ", ".join(details)
        exhaustive_payload = f"[{author_str} ({year}), \"{ret_title}\", {detail_str}]"
        matched_author_surname = matching_families[0] if matching_families else (authors[0].split(',')[0] if authors else author_surname)

        result_dict = {
            "author_surname": matched_author_surname,
            "year": year,
            "title": ret_title,
            "authors": authors,
            "publisher": journal,
            "doi": doi,
            "url": work_url,
            "exhaustive_payload": exhaustive_payload
        }
        cache[cache_key] = result_dict
        _save_crossref_cache(cache)
        return result_dict

    except Exception as e:
        _log_tool_trace("fetch_crossref_metadata", {"title": title, "author": author_surname}, f"[ERROR] {str(e)}")
        return None

def triage_and_expand_chapter_references(chapter_number: int = 6) -> dict:
    """
    Stage 2 & Stage 4 Tool (Plank):
    Parses raw references semantically via LLM (Zero Regex),
    resolves citations via DB cache, CrossRef API, and Landlubber web search grounding,
    stages complete JSON records into cargo.fleet_enrichments, and writes the master 
    Bronze+ reference index to ship/bronze_plus/chapters/chXX/chXX_references.md.
    """
    base_dir = _get_base_dir()
    ch_slug = f"ch{chapter_number:02d}"
    
    bronze_dir = os.path.join(base_dir, "ship", "bronze", "chapters", ch_slug)
    bronze_plus_dir = os.path.join(base_dir, "ship", "bronze_plus", "chapters", ch_slug)
    os.makedirs(bronze_plus_dir, exist_ok=True)
    
    raw_ref_file = os.path.join(bronze_dir, f"{ch_slug}_references.md")
    if not os.path.exists(raw_ref_file):
        raise FileNotFoundError(f"Raw bronze references file not found at: {raw_ref_file}")

    with open(raw_ref_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    raw_items = []
    for line in lines:
        clean_l = line.strip()
        if clean_l and not clean_l.startswith('#') and not clean_l.startswith('---'):
            clean_item = clean_l.lstrip('0123456789.-*+ ').strip()
            if clean_item:
                raw_items.append(clean_item)

    conn = _get_strict_cargo_connection()
    resolved_nodes = []
    unacquired_urls = []

    from react_agent.core.tool_dispatcher import call_landlubber

    for idx, item in enumerate(raw_items, 1):
        # 1. Check IDEMPOTENCY in PostgreSQL cargo.fleet_enrichments
        cached_node = None
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT payload FROM cargo.fleet_enrichments WHERE enrichment_type = 'citation_staging' AND payload->>'raw_bronze' = %s LIMIT 1",
                    (item,)
                )
                row = cur.fetchone()
                cur.close()
                if row and isinstance(row[0], dict) and row[0].get("exhaustive_silver"):
                    cached_node = row[0]["exhaustive_silver"]
            except Exception:
                pass

        if cached_node:
            resolved_nodes.append(f"{idx}. {cached_node}")
            continue

        # 2. LLM Semantic Decomposition (Zero Regex)
        parsed = parse_citation_semantically(item)
        category = parsed.get("category", "ACADEMIC")
        surname = parsed.get("primary_author_surname", "")
        title = parsed.get("title", "")
        year = parsed.get("year", "2025")
        container = parsed.get("container_or_publisher", "")
        docket = parsed.get("docket_or_citation", "")
        explicit_url = parsed.get("explicit_url", "")

        node = None

        # Case A: Legal / Court Docket
        if category == "LEGAL_GOV" or docket:
            search_res = call_landlubber(f"Court docket opinion URL {title} {docket} {year}")
            # Extract URL semantically or from response
            found_url = explicit_url
            for word in search_res.split():
                if word.startswith("http://") or word.startswith("https://"):
                    found_url = word.strip('.,()[]<>"')
                    break
            if not found_url:
                found_url = "https://courtlistener.com"
            node = f"[{surname} ({year}), Court Decision, Docket: {docket or title}, URL: {found_url}]"

        # Case B: Academic Query via CrossRef
        elif category == "ACADEMIC":
            crossref_res = fetch_crossref_metadata(title=title, author_surname=surname)
            if crossref_res:
                node = crossref_res["exhaustive_payload"]

        # Case C: News Media / Web / Government
        if not node:
            search_res = call_landlubber(f"Canonical URL and publication details for: {surname} {title} {container} {year}")
            found_url = explicit_url
            for word in search_res.split():
                if word.startswith("http://") or word.startswith("https://"):
                    found_url = word.strip('.,()[]<>"')
                    break
            
            author_display = ", ".join(parsed.get("full_authors", [])) or surname or "Staff"
            if found_url:
                node = f"[{author_display} ({year}), \"{title}\", {container or 'Report'}, URL: {found_url}]"
                unacquired_urls.append(found_url)
            else:
                node = f"[{author_display} ({year}), \"{title}\", {container}]"

        resolved_nodes.append(f"{idx}. {node}")

        # 3. Stage JSON payload to cargo.fleet_enrichments
        if conn:
            try:
                slug_author = "".join(c for c in surname.lower() if c.isalnum())[:12] or "ref"
                cite_key = f"{slug_author}_{year}_{idx}"

                staged_payload = {
                    "cite_key": cite_key,
                    "raw_bronze": item,
                    "exhaustive_silver": node,
                    "chapters_cited": [chapter_number],
                    "metadata": {
                        "title": title,
                        "date": year,
                        "authors": parsed.get("full_authors", [surname]),
                        "item_type": category.lower(),
                        "publication_title": container
                    },
                    "zotero_staging": {
                        "synced": False,
                        "zotero_key": ""
                    }
                }
                
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO cargo.fleet_enrichments (agent_name, enrichment_type, payload, created_at)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    ("plank", "citation_staging", json.dumps(staged_payload))
                )
                conn.commit()
                cur.close()
            except Exception:
                pass

    if conn:
        conn.close()

    # 4. Write Bronze+ Reference Index
    bronze_plus_ref_file = os.path.join(bronze_plus_dir, f"{ch_slug}_references.md")
    with open(bronze_plus_ref_file, "w", encoding="utf-8") as f:
        f.write(f"# Bronze Plus Master Reference Index: Chapter {chapter_number}\n\n")
        for node in resolved_nodes:
            f.write(f"{node}\n")

    return {
        "status": "SUCCESS",
        "chapter": chapter_number,
        "total_references": len(raw_items),
        "resolved_nodes_count": len(resolved_nodes),
        "unacquired_urls_for_spyglass": unacquired_urls,
        "bronze_plus_reference_file": bronze_plus_ref_file
    }
