"""
NPT Fleet: Hybrid EPUB Stevedore Pipeline
Extracts structured full-length books into high-fidelity prose assets.
Generates:
  1. A Master Reference Asset (pristine full volume, item_type='book').
  2. Individual Chapter-Level Assets (with attached endnotes, item_type='bookSection').
Strictly complies with ADR-003, ADR-006, and PEP-249 (pg8000.dbapi).
"""

import os
import sys
import glob
import json
import zipfile
import re
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.react_agent.tools.cargo_db_tools import _get_strict_cargo_connection
from src.react_agent.tools.cloud_knowledge_tools import _get_bucket


import unicodedata

def slugify(text: str) -> str:
    """Convert text to deterministic kebab-case slug, cleanly normalizing diacritics."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    text = re.sub(r'[\'\"]', '', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def extract_epub_metadata(opf_root, ns) -> dict:
    """Extract standard Dublin Core metadata from OPF XML."""
    title_elem = opf_root.find(".//dc:title", ns)
    creator_elem = opf_root.find(".//dc:creator", ns)
    pub_elem = opf_root.find(".//dc:publisher", ns)
    date_elem = opf_root.find(".//dc:date", ns)
    
    # Try finding ISBN in dc:identifier
    isbn = "UNKNOWN"
    for id_elem in opf_root.findall(".//dc:identifier", ns):
        txt = id_elem.text or ""
        if "isbn" in txt.lower() or id_elem.attrib.get("{http://www.idpf.org/2007/opf}scheme", "").lower() == "isbn":
            clean_isbn = re.sub(r'[^0-9X]', '', txt.upper())
            if clean_isbn:
                isbn = clean_isbn
                break
        elif re.match(r'^\d{10}(\d{3})?$', txt.strip()):
            isbn = txt.strip()

    title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Unknown Book"
    creator = creator_elem.text.strip() if creator_elem is not None and creator_elem.text else "Unknown Author"
    publisher = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else "Unknown Publisher"
    pub_date = date_elem.text.strip() if date_elem is not None and date_elem.text else str(datetime.now().year)

    return {
        "title": title,
        "author": creator,
        "publisher": publisher,
        "published_date": pub_date,
        "isbn": isbn
    }


def parse_xhtml_to_markdown(html_bytes: bytes) -> tuple[str, str, str]:
    """
    Parses chapter XHTML and converts to clean Markdown.
    Returns: (chapter_title, chapter_heading, clean_markdown)
    """
    raw_html = html_bytes.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # Extract title
    page_title = soup.title.string.strip() if soup.title and soup.title.string else ""
    
    # Locate main body
    body = soup.body if soup.body else soup
    
    markdown_lines = []
    chapter_heading = ""
    
    # Iterate direct children or semantic tags
    for tag in body.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'blockquote', 'ul', 'ol']):
        txt = tag.get_text(strip=True)
        if not txt:
            continue
            
        if tag.name == 'h1':
            if not chapter_heading:
                chapter_heading = txt
            markdown_lines.append(f"\n# {txt}\n")
        elif tag.name == 'h2':
            if not chapter_heading:
                chapter_heading = txt
            markdown_lines.append(f"\n## {txt}\n")
        elif tag.name == 'h3':
            markdown_lines.append(f"\n### {txt}\n")
        elif tag.name == 'blockquote':
            markdown_lines.append(f"\n> {txt}\n")
        elif tag.name in ['ul', 'ol']:
            for li in tag.find_all('li'):
                li_txt = li.get_text(strip=True)
                if li_txt:
                    markdown_lines.append(f"* {li_txt}")
            markdown_lines.append("")
        elif tag.name == 'p':
            markdown_lines.append(f"{txt}\n")
            
    prose = "\n".join(markdown_lines).strip()
    return page_title, chapter_heading, prose


def parse_endnotes(endnotes_bytes: bytes) -> dict[str, str]:
    """
    Segments endnotes.xhtml by h2 headings and returns a dictionary of:
    { "INTRODUCTION": "...notes...", "CHAPTER 1": "...notes...", ... }
    """
    raw_html = endnotes_bytes.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    notes_by_chapter = {}
    h2s = soup.find_all('h2')
    
    for h2 in h2s:
        header_text = h2.get_text(strip=True).upper()
        # Collect siblings until next h2
        siblings = []
        curr = h2.next_sibling
        while curr:
            if getattr(curr, 'name', None) == 'h2':
                break
            txt = curr.get_text(strip=True) if hasattr(curr, 'get_text') else str(curr).strip()
            if txt:
                siblings.append(txt)
            curr = curr.next_sibling
        
        joined_notes = "\n\n".join(siblings)
        notes_by_chapter[header_text] = joined_notes
        
    return notes_by_chapter


def match_endnotes_for_chapter(chapter_num: int, chapter_title: str, is_intro: bool, endnotes_map: dict[str, str]) -> str:
    """Finds the matching endnotes string for a given chapter."""
    if is_intro:
        for k, v in endnotes_map.items():
            if "INTRO" in k:
                return v
        return ""
        
    # Match by chapter number (e.g. "CHAPTER 1" or "CH 1")
    target_pattern = f"CHAPTER {chapter_num}"
    for k, v in endnotes_map.items():
        if target_pattern in k:
            return v
            
    # Match by key words in chapter title
    title_words = [w for w in re.split(r'[^A-Z0-9]', chapter_title.upper()) if len(w) > 3]
    for k, v in endnotes_map.items():
        if any(w in k for w in title_words):
            return v
            
    return ""


def upload_to_gcs_and_catalog(
    slug: str,
    payload: str,
    meta: dict,
    bucket,
    conn
) -> int:
    """
    Uploads the payload to GCS acquisitions/{slug}.txt and registers in cargo.content_metadata.
    Returns the database record ID.
    """
    blob_name = f"acquisitions/{slug}.txt"
    gcp_path = f"gs://{bucket.name}/{blob_name}"
    
    # 1. Upload to GCS
    print(f"  -> Uploading to GCS: {gcp_path} ({len(payload):,} chars)...")
    blob = bucket.blob(blob_name)
    blob.upload_from_string(payload, content_type="text/plain; charset=utf-8")
    
    # 2. Upsert to Postgres cargo.content_metadata
    cur = conn.cursor()
    source_url = meta["source_url"]
    
    cur.execute("SELECT id FROM cargo.content_metadata WHERE source_url = %s;", (source_url,))
    existing = cur.fetchone()
    
    authors_json = json.dumps([meta["author"]])
    keywords_json = json.dumps(meta.get("keywords", {}))
    
    if existing:
        asset_id = existing[0]
        cur.execute("""
            UPDATE cargo.content_metadata
            SET item_type = %s,
                title = %s,
                authors = %s,
                abstract = %s,
                publication_title = %s,
                publication_date = %s,
                keywords = %s,
                rights = %s,
                gcp_bucket_path = %s
            WHERE id = %s;
        """, (
            meta["item_type"],
            meta["title"],
            authors_json,
            meta.get("abstract", ""),
            meta["publication_title"],
            meta["published_date"],
            keywords_json,
            meta.get("rights", "All Rights Reserved"),
            gcp_path,
            asset_id
        ))
        conn.commit()
        print(f"  -> Updated cargo.content_metadata row ID: {asset_id}")
        return asset_id
    else:
        cur.execute("""
            INSERT INTO cargo.content_metadata (
                source_url, item_type, title, authors, abstract,
                publication_title, publication_date, keywords, rights,
                gcp_bucket_path, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id;
        """, (
            source_url,
            meta["item_type"],
            meta["title"],
            authors_json,
            meta.get("abstract", ""),
            meta["publication_title"],
            meta["published_date"],
            keywords_json,
            meta.get("rights", "All Rights Reserved"),
            gcp_path
        ))
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"  -> Inserted new cargo.content_metadata row ID: {new_id}")
        return new_id


def process_epub(epub_path: str):
    """Main stevedoring workflow for a single EPUB file."""
    print("=" * 70)
    print(f" NPT FLEET: EPUB STEVEDORE PIPELINE")
    print(f" Target File: {os.path.basename(epub_path)}")
    print("=" * 70)
    
    if not os.path.exists(epub_path):
        print(f"[ERROR] EPUB file does not exist: {epub_path}")
        return

    bucket = _get_bucket()
    conn = _get_strict_cargo_connection()
    if not conn:
        print("[ERROR] Cannot connect to cargo database!")
        return

    with zipfile.ZipFile(epub_path, 'r') as z:
        file_list = z.namelist()
        
        # 1. Locate and parse OPF
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

        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        book_meta = extract_epub_metadata(opf_root, ns)
        print(f"\n[BOOK METADATA]")
        print(f"  Title:     {book_meta['title']}")
        print(f"  Author:    {book_meta['author']}")
        print(f"  Publisher: {book_meta['publisher']}")
        print(f"  Date:      {book_meta['published_date']}")
        print(f"  ISBN:      {book_meta['isbn']}")

        # 2. Build Manifest & Spine
        manifest = {}
        for item in opf_root.findall(".//opf:item", ns):
            manifest[item.attrib.get("id")] = (item.attrib.get("href"), item.attrib.get("media-type"))

        spine_hrefs = []
        for itemref in opf_root.findall(".//opf:itemref", ns):
            idref = itemref.attrib.get("idref")
            if idref in manifest:
                spine_hrefs.append(manifest[idref][0])

        # 3. Locate Endnotes
        endnotes_map = {}
        for href in spine_hrefs:
            if "endnote" in href.lower() or "note" in href.lower():
                full_href = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
                if full_href in file_list:
                    print(f"\n[ENDNOTES FOUND] Parsing {full_href}...")
                    endnotes_map = parse_endnotes(z.read(full_href))
                    print(f"  Extracted endnotes for {len(endnotes_map)} sections.")
                    break

        # 4. Extract Spine Sections
        master_slug = f"{slugify(book_meta['title'])}-{slugify(book_meta['author'])}-{book_meta['published_date'][:4]}"
        book_epub_basename = os.path.basename(epub_path)
        
        all_sections_prose = []
        chapter_assets_created = []
        
        chapter_idx = 0
        for href in spine_hrefs:
            full_href = os.path.normpath(os.path.join(opf_dir, href)).replace("\\", "/")
            if full_href not in file_list or not (full_href.endswith('.xhtml') or full_href.endswith('.html')):
                continue
                
            raw_bytes = z.read(full_href)
            page_title, chapter_heading, prose = parse_xhtml_to_markdown(raw_bytes)
            
            # Skip trivial boilerplate pages (e.g. signup pages, 1-line back matter)
            if len(prose) < 600 and not any(k in href.lower() for k in ['epigraph', 'intro']):
                continue
                
            all_sections_prose.append(prose)
            
            # Determine if this is a chapter or intro for active slicing
            is_intro = "intro" in href.lower()
            is_chapter = "ch" in href.lower() or "chapter" in href.lower()
            
            if is_intro or is_chapter:
                chapter_idx += 1 if is_chapter else 0
                
                if is_intro:
                    sec_number = 0
                    sec_title = "Introduction"
                    ch_slug = f"{slugify(book_meta['title'])}-intro-{slugify(book_meta['author'])}-{book_meta['published_date'][:4]}"
                else:
                    sec_number = chapter_idx
                    # Clean title e.g. "CHAPTER 1THE SOVEREIGN INDIVIDUAL" -> "The Sovereign Individual"
                    clean_h = re.sub(r'^CHAPTER\s*\d+\s*', '', chapter_heading, flags=re.IGNORECASE).strip()
                    sec_title = clean_h if clean_h else f"Chapter {chapter_idx}"
                    ch_slug = f"{slugify(book_meta['title'])}-ch{sec_number:02d}-{slugify(sec_title)}-{slugify(book_meta['author'])}-{book_meta['published_date'][:4]}"
                
                # Fetch matching endnotes
                matched_notes = match_endnotes_for_chapter(sec_number, sec_title, is_intro, endnotes_map)
                
                # Build Chapter Acquisition Payload
                full_chapter_title = f"{book_meta['title']}: {('Introduction' if is_intro else f'Chapter {sec_number}')} — {sec_title}"
                source_url_pointer = f"local://cargo_cache/inbox/{book_epub_basename}#{href}"
                
                ch_payload = (
                    f"=== ACQUISITION INDEX ===\n"
                    f"SOURCE: {source_url_pointer}\n"
                    f"TITLE: {full_chapter_title}\n"
                    f"AUTHORS: {book_meta['author']}\n"
                    f"PUBLISHED: {book_meta['published_date']}\n"
                    f"PUBLISHER: {book_meta['publisher']}\n"
                    f"ITEM_TYPE: bookSection\n"
                    f"BOOK_TITLE: {book_meta['title']}\n"
                    f"BOOK_AUTHORS: {book_meta['author']}\n"
                    f"BOOK_PUBLISHER: {book_meta['publisher']}\n"
                    f"BOOK_PUBLISHED: {book_meta['published_date']}\n"
                    f"BOOK_ISBN: {book_meta['isbn']}\n"
                    f"CHAPTER_NUMBER: {sec_number}\n"
                    f"CHAPTER_TITLE: {sec_title}\n"
                    f"PARENT_BOOK_SLUG: {master_slug}\n"
                    f"===========================================================\n\n"
                    f"{prose}\n"
                )
                
                if matched_notes:
                    ch_payload += f"\n\n## CHAPTER ENDNOTES & SOURCE CITATIONS\n\n{matched_notes}\n"
                    
                ch_meta = {
                    "source_url": source_url_pointer,
                    "item_type": "bookSection",
                    "title": full_chapter_title,
                    "author": book_meta["author"],
                    "publication_title": book_meta["title"],
                    "published_date": book_meta["published_date"],
                    "keywords": {
                        "parent_book_title": book_meta["title"],
                        "parent_book_slug": master_slug,
                        "isbn": book_meta["isbn"],
                        "chapter_number": sec_number,
                        "chapter_title": sec_title,
                        "endnotes_attached": bool(matched_notes)
                    }
                }
                
                print(f"\n[PROCESSING CHAPTER] {full_chapter_title}...")
                print(f"  Prose: {len(prose):,} chars | Endnotes: {len(matched_notes):,} chars")
                asset_id = upload_to_gcs_and_catalog(ch_slug, ch_payload, ch_meta, bucket, conn)
                chapter_assets_created.append((sec_number, sec_title, ch_slug, asset_id))

        # 5. Build Master Book Asset (Complete Unabridged Volume)
        print(f"\n[BUILDING MASTER BOOK ASSET] {book_meta['title']}...")
        master_source_url = f"local://cargo_cache/inbox/{book_epub_basename}"
        master_payload = (
            f"=== ACQUISITION INDEX ===\n"
            f"SOURCE: {master_source_url}\n"
            f"TITLE: {book_meta['title']}\n"
            f"AUTHORS: {book_meta['author']}\n"
            f"PUBLISHED: {book_meta['published_date']}\n"
            f"PUBLISHER: {book_meta['publisher']}\n"
            f"ITEM_TYPE: book\n"
            f"BOOK_ISBN: {book_meta['isbn']}\n"
            f"ROLE: MASTER_BOOK_REFERENCE_ONLY (Do not ingest into VDB or single-agent audit)\n"
            f"TOTAL_CHAPTERS_EXTRACTED: {len(chapter_assets_created)}\n"
            f"===========================================================\n\n"
            + "\n\n---\n\n".join(all_sections_prose)
        )
        
        master_meta = {
            "source_url": master_source_url,
            "item_type": "book",
            "title": book_meta["title"],
            "author": book_meta["author"],
            "publication_title": book_meta["publisher"],
            "published_date": book_meta["published_date"],
            "keywords": {
                "isbn": book_meta["isbn"],
                "role": "master_reference",
                "chapters_count": len(chapter_assets_created)
            }
        }
        
        master_asset_id = upload_to_gcs_and_catalog(master_slug, master_payload, master_meta, bucket, conn)

    conn.close()
    
    print("\n" + "=" * 70)
    print(" STEVEDORE PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print(f"Master Asset ID: {master_asset_id} -> {master_slug}.txt")
    print(f"Total Chapter Assets Created: {len(chapter_assets_created)}")
    for num, title, c_slug, c_id in chapter_assets_created:
        print(f"  [{c_id:04d}] Chapter {num:02d}: {title[:40]:40s} -> {c_slug}.txt")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stevedore an EPUB into NPT Fleet Cargo Hold.")
    parser.add_argument("--file", help="Path to specific EPUB file. If omitted, scans cargo_cache/inbox/*.epub.")
    args = parser.parse_args()

    target_file = args.file
    if not target_file:
        inbox_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cargo_cache", "inbox"))
        epubs = glob.glob(os.path.join(inbox_dir, "*.epub"))
        if not epubs:
            print(f"[ERROR] No EPUB files found in {inbox_dir}")
            sys.exit(1)
        target_file = epubs[0]

    process_epub(target_file)
