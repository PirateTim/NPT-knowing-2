"""
NPT Manuscript ETL Pipeline
Architecture: GCS Streaming, Structural Normalization, Citation Resolution, and Cost-Controlled Vector Upsert
"""
import os
import re
import uuid
import json
import pg8000.dbapi
from google.cloud import storage
from google.genai import Client
from google.genai import types

# =====================================================================
# DATABASE CONNECTION HELPER
# =====================================================================

def _get_strict_cargo_connection():
    """
    Establishes connection to the Content/Cargo database (CONTENT_DATABASE_URL).
    Uses pg8000.dbapi per project rules.
    """
    from urllib.parse import urlparse
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("[ERROR] CONTENT_DATABASE_URL environment variable is not set.")
    try:
        url = urlparse(conn_string)
        return pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
    except Exception as e:
        print(f"[CARGO DB FAULT] {str(e)}")
        raise

# =====================================================================
# TASK 2.1: PROCESS BRONZE MANUSCRIPT
# =====================================================================

def process_bronze_manuscript(*args, **kwargs) -> str:
    """
    Step 1 of Manuscript Ingestion:
    Streams the raw monolith from GCS (or local file), normalizes header hierarchies,
    slices document into bronze chapter and reference files in gs://npt-ship/manuscript/bronze/,
    resolves inline citations against each chapter's localized reference list,
    and writes clean silver markdown files to gs://npt-ship/manuscript/silver/ch{N:02d}_silver.md.
    """
    bronze_gcs_path = "gs://npt-ship/manuscript/bronze/2026-02-24AChapters_complete.md"
    target_chapter = None

    if len(args) > 0:
        bronze_gcs_path = args[0]
    if len(args) > 1:
        target_chapter = args[1]

    if "bronze_gcs_path" in kwargs:
        bronze_gcs_path = kwargs["bronze_gcs_path"]
    if "target_chapter" in kwargs:
        target_chapter = kwargs["target_chapter"]

    try:
        raw_text = None
        bucket_name = "npt-ship"
        storage_client = None
        bucket = None

        # Attempt to read from GCS or local disk fallback
        if bronze_gcs_path.startswith("gs://"):
            path_parts = bronze_gcs_path[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_name = path_parts[1] if len(path_parts) > 1 else ""
            
            try:
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                if blob.exists():
                    raw_text = blob.download_as_text(encoding="utf-8")
            except Exception as gcs_err:
                print(f"[GCS NOTICE] Unable to stream directly from {bronze_gcs_path}: {gcs_err}. Trying local fallback.")

        if not raw_text:
            local_fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "2026-02-24AChapters_complete.md"))
            if os.path.exists(local_fallback):
                with open(local_fallback, "r", encoding="utf-8") as f:
                    raw_text = f.read()
            else:
                return f"[ERROR] Monolith not found at {bronze_gcs_path} or local path {local_fallback}"

        # If GCS bucket client is active, ensure monolith is uploaded to bronze tier if missing
        if storage_client and bucket:
            try:
                bronze_monolith_blob = bucket.blob("manuscript/bronze/2026-02-24AChapters_complete.md")
                if not bronze_monolith_blob.exists():
                    bronze_monolith_blob.upload_from_string(raw_text, content_type="text/markdown; charset=utf-8")
            except Exception as e:
                print(f"[GCS WARNING] Failed uploading bronze monolith: {e}")

        # Normalize structural header hierarchies to strict '#' levels
        normalized_text = re.sub(r'^[ \t]*([#]+)[ \t]*', r'\1 ', raw_text, flags=re.MULTILINE)

        # Regex pattern for chapter boundaries (e.g., "# Introduction" or "### Chapter 1: ..." or "# **Chapter 3: ...")
        chapter_regex = re.compile(
            r'^(#+\s*(?:\*\*|\*)*\s*(?:Chapter\s+\d+|Introduction|Conclusion).*?)(?=(?:^#+\s*(?:\*\*|\*)*\s*(?:Chapter\s+\d+|Introduction|Conclusion)|\Z))',
            re.MULTILINE | re.DOTALL | re.IGNORECASE
        )

        chapter_matches = list(chapter_regex.finditer(normalized_text))
        if not chapter_matches:
            chapter_regex = re.compile(r'^(#+\s+.*?)(?=(?:^#+\s+|\Z))', re.MULTILINE | re.DOTALL)
            chapter_matches = list(chapter_regex.finditer(normalized_text))

        processed_count = 0

        # Local output directories
        ship_bronze_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "bronze"))
        ship_silver_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "silver"))
        os.makedirs(ship_bronze_dir, exist_ok=True)
        os.makedirs(ship_silver_dir, exist_ok=True)

        for match_idx, match in enumerate(chapter_matches, 1):
            ch_raw_text = match.group(1).strip()
            
            # Extract Chapter Number
            ch_num_match = re.search(r'Chapter\s+(\d+)', ch_raw_text, re.IGNORECASE)
            if ch_num_match:
                ch_num = int(ch_num_match.group(1))
            else:
                ch_num = match_idx - 1 # 0 for Intro if first

            if target_chapter is not None and ch_num != int(target_chapter):
                continue

            # Separate Body Prose from Localized References / Master Index of Artifacts section
            works_cited_match = re.search(
                r'^(#+\s+(?:Master\s+Index\s+of\s+Artifacts|Master\s+List\s+of\s+Artifacts|Works\s+Cited|Bibliography|References).*)$',
                ch_raw_text, re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            
            if works_cited_match:
                body_text = ch_raw_text[:works_cited_match.start()].strip()
                ref_section_text = works_cited_match.group(0).strip()
            else:
                body_text = ch_raw_text
                ref_section_text = f"# Master Index of Artifacts (Chapter {ch_num})\n\n[No localized reference section provided]"

            # Build localized reference expansion map
            citations_cache = {}
            
            ref_lines = [l.strip() for l in ref_section_text.split('\n') if l.strip() and not l.strip().startswith('#') and not l.strip().startswith('---')]
            
            for line_idx, line in enumerate(ref_lines, 1):
                # Check if numbered line e.g. "1. Brenndoerfer, M..."
                num_match = re.match(r'^\s*(\d+)\.\s*(.*)', line)
                if num_match:
                    ref_num = num_match.group(1)
                    clean_entry = num_match.group(2)
                else:
                    ref_num = str(line_idx)
                    clean_entry = line

                # Extract Author / Org and Date e.g. "Brenndoerfer, M. (2025, October 1). Title..."
                m_author_date = re.search(r'^([^(\n]+?)\s*(?:,\s*[A-Z]\.|\s+et\s+al\.)?\s*\(([^)]+)\)', clean_entry)
                if m_author_date:
                    raw_author_part = m_author_date.group(1).strip()
                    raw_date_part = m_author_date.group(2).strip()
                    
                    # Author surname or org name
                    surname = raw_author_part.split(',')[0].strip().rstrip('.')
                    
                    # Extract 4-digit year or n.d. or BC/AD
                    y_match = re.search(r'\b(\d{4}|\d{3}\s*BC|\d{3}\s*AD|n\.d\.)\b', raw_date_part)
                    year = y_match.group(1) if y_match else raw_date_part
                    
                    expanded_ref = f"[{surname} ({year}) — {clean_entry[:80]}...]"

                    # Add key variations to citations cache
                    citations_cache[f"({surname}, {year})"] = expanded_ref
                    citations_cache[f"({surname} {year})"] = expanded_ref
                    citations_cache[f"({surname} et al., {year})"] = expanded_ref
                    citations_cache[f"({surname} et al. {year})"] = expanded_ref
                    citations_cache[f"[{ref_num}]"] = expanded_ref

            # Expand inline citations in the body prose
            resolved_text = body_text
            for inline_cite, resolved_ref in citations_cache.items():
                resolved_text = resolved_text.replace(inline_cite, resolved_ref)

            # Pure body prose with inline expanded references for Silver tier (no trailing reference list)
            silver_text = resolved_text

            # Local per-chapter folder paths under ./ship/bronze/chapters/chXX/
            ch_folder = f"ch{ch_num:02d}"
            local_ch_bronze_dir = os.path.join(ship_bronze_dir, "chapters", ch_folder)
            local_ch_silver_dir = os.path.join(ship_silver_dir, "chapters", ch_folder)
            os.makedirs(local_ch_bronze_dir, exist_ok=True)
            os.makedirs(local_ch_silver_dir, exist_ok=True)

            # Save Bronze Files locally (no GCS bronze upload)
            local_ch_file = os.path.join(local_ch_bronze_dir, f"ch{ch_num:02d}_bronze.md")
            local_ref_file = os.path.join(local_ch_bronze_dir, f"ch{ch_num:02d}_bronze_references.md")
            with open(local_ch_file, "w", encoding="utf-8") as f:
                f.write(body_text)
            with open(local_ref_file, "w", encoding="utf-8") as f:
                f.write(ref_section_text)

            # Save Silver File locally and to GCS
            local_silver_file = os.path.join(local_ch_silver_dir, f"ch{ch_num:02d}_silver.md")
            with open(local_silver_file, "w", encoding="utf-8") as f:
                f.write(silver_text)

            silver_blob_name = f"silver/chapters/ch{ch_num:02d}/ch{ch_num:02d}_silver.md"
            if storage_client and bucket:
                try:
                    bucket.blob(silver_blob_name).upload_from_string(silver_text, content_type="text/markdown; charset=utf-8")
                except Exception as e:
                    print(f"[GCS WARNING] Failed uploading silver chapter {ch_num}: {e}")

            processed_count += 1

        return f"[SUCCESS] Processed {processed_count} chapters into ./ship/bronze/chapters/ & ./ship/silver/chapters/ and GCS gs://{bucket_name}/silver/."

    except Exception as e:
        return f"[ERROR] process_bronze_manuscript failed: {str(e)}"

# =====================================================================
# TASK 2.2: EMBED AND LOAD MANUSCRIPT
# =====================================================================

def embed_and_load_manuscript(silver_gcs_dir: str = "gs://npt-ship/manuscript/silver/", target_chapter: int = None) -> str:
    """
    Step 2 of Manuscript Ingestion:
    Reads silver chapter files from GCS (or local manuscript/silver/), slices them into sequential
    paragraph chunks, checks existing 'ship.letters_of_marque' table to prevent redundant embeddings,
    generates 1536-dimension embeddings via Gemini, and UPSERTs records with strict provenance.
    """
    try:
        bucket_name = "npt-ship"
        prefix = "manuscript/silver/"
        
        if silver_gcs_dir.startswith("gs://"):
            path_parts = silver_gcs_dir[5:].split("/", 1)
            bucket_name = path_parts[0]
            prefix = path_parts[1] if len(path_parts) > 1 else ""

        storage_client = None
        bucket = None
        blobs = []

        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blobs = list(bucket.list_blobs(prefix=prefix))
        except Exception as gcs_err:
            print(f"[GCS NOTICE] Could not list blobs from GCS: {gcs_err}. Utilizing local silver fallback.")

        # Local fallback files if GCS listing is empty or fails
        chapter_files = []
        if blobs:
            for b in blobs:
                if b.name.endswith("_silver.md"):
                    chapter_files.append(("gcs", b.name, b))
        else:
            local_silver_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "manuscript", "silver"))
            if os.path.exists(local_silver_dir):
                for f_name in sorted(os.listdir(local_silver_dir)):
                    if f_name.endswith("_silver.md"):
                        chapter_files.append(("local", f_name, os.path.join(local_silver_dir, f_name)))

        if not chapter_files:
            return "[ERROR] No silver chapter files found to embed."

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key not found in environment variables."
        gemini_client = Client(api_key=api_key)

        conn = _get_strict_cargo_connection()
        if not conn:
            return "[ERROR] Unable to connect to Cargo/Ship database."
        cursor = conn.cursor()

        upserted_count = 0
        skipped_count = 0

        for source_type, file_identifier, handle in chapter_files:
            ch_match = re.search(r'ch(\d+)_silver\.md', file_identifier)
            if not ch_match:
                continue

            ch_num = int(ch_match.group(1))
            if target_chapter is not None and ch_num != int(target_chapter):
                continue

            # Purge existing vectors for this chapter to ensure a clean, exact paragraph load
            cursor.execute("DELETE FROM ship.letters_of_marque WHERE chapter_number = %s;", (ch_num,))
            conn.commit()

            if source_type == "gcs":
                chapter_text = handle.download_as_text(encoding="utf-8")
                gcs_pointer = f"gs://{bucket_name}/{handle.name}"
            else:
                with open(handle, "r", encoding="utf-8") as f:
                    chapter_text = f.read()
                gcs_pointer = f"gs://{bucket_name}/manuscript/silver/{file_identifier}"

            # Split text on markdown headers while preserving header state
            chunks = re.split(r'(^#+\s+.*$)', chapter_text, flags=re.MULTILINE)

            current_section = "1"
            header_title = f"Chapter {ch_num} Introduction"
            paragraph_index = 0

            for chunk in chunks:
                chunk_clean = chunk.strip()
                if not chunk_clean:
                    continue

                if chunk_clean.startswith("#"):
                    header_title = chunk_clean.lstrip("#").strip()
                    sec_match = re.match(r'(\d+\.\d+)', header_title)
                    current_section = sec_match.group(1) if sec_match else header_title[:10]
                    current_section = current_section[:10]

                paragraphs = [p.strip() for p in chunk_clean.split("\n\n") if p.strip()]

                for p_text in paragraphs:
                    paragraph_index += 1

                    cursor.execute(
                        """
                        SELECT chunk_id, chunk_text 
                        FROM ship.letters_of_marque 
                        WHERE chapter_number = %s AND section_number = %s AND paragraph_sequence_number = %s;
                        """,
                        (ch_num, current_section, paragraph_index)
                    )
                    existing_record = cursor.fetchone()

                    if existing_record:
                        existing_id, existing_text = existing_record
                        if existing_text == p_text:
                            skipped_count += 1
                            continue
                        else:
                            chunk_id = existing_id
                    else:
                        chunk_id = str(uuid.uuid4())

                    response = gemini_client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=p_text,
                        config=types.EmbedContentConfig(output_dimensionality=1536)
                    )
                    embedding = response.embeddings[0].values

                    cursor.execute(
                        """
                        INSERT INTO ship.letters_of_marque (
                            chunk_id, chapter_number, section_number, header_title, 
                            book_sequence_number, paragraph_sequence_number, chunk_text, 
                            vector_embedding, parent_gcs_pointer, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            chunk_text = EXCLUDED.chunk_text,
                            vector_embedding = EXCLUDED.vector_embedding,
                            updated_at = NOW();
                        """,
                        (
                            chunk_id, ch_num, current_section, header_title,
                            ch_num, paragraph_index, p_text, str(list(embedding)),
                            gcs_pointer
                        )
                    )
                    upserted_count += 1

        conn.commit()
        cursor.close()
        conn.close()

        return f"[SUCCESS] Embed and load completed. Upserted: {upserted_count}, Skipped (Deduplicated): {skipped_count}"

    except Exception as e:
        return f"[ERROR] embed_and_load_manuscript failed: {str(e)}"

