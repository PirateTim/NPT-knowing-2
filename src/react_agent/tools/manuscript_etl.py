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
    Streams the raw monolith from GCS, normalizes structural header hierarchies,
    slices the document by chapter, resolves inline citations against the chapter's
    Works Cited/Master List of Artifacts cache, and saves clean silver chapters to GCS.
    """
    # Safely extract arguments whether passed positionally or as keywords
    bronze_gcs_path = "gs://npt-ship/2026-02-24AChapters_complete.md"
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
        # Parse GCS path
        if not bronze_gcs_path.startswith("gs://"):
            return f"[ERROR] Invalid GCS path: {bronze_gcs_path}. Must start with gs://"
        
        path_parts = bronze_gcs_path[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_name = path_parts[1] if len(path_parts) > 1 else ""
        
        if not blob_name:
            return f"[ERROR] No blob name specified in GCS path: {bronze_gcs_path}"

        # Stream raw monolith from GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        
        if not blob.exists():
            return f"[ERROR] Bronze monolith not found at {bronze_gcs_path}"
            
        raw_text = blob.download_as_text(encoding="utf-8")
        
        # Normalize structural header hierarchies to strict '#' levels
        normalized_text = re.sub(r'^[ \t]*([#]+)[ \t]*', r'\1 ', raw_text, flags=re.MULTILINE)
        
        # Slice the document by chapter
        chapter_pattern = re.compile(r'^(#+\s+Chapter\s+(\d+).*?)(?=^#+\s+Chapter\s+\d+|\Z)', re.MULTILINE | re.DOTALL)
        chapters = chapter_pattern.findall(normalized_text)
        
        if not chapters:
            chapter_pattern = re.compile(r'^(#\s+.*?)(?=^#\s+|\Z)', re.MULTILINE | re.DOTALL)
            chapters = chapter_pattern.findall(normalized_text)
            
        processed_count = 0
        
        for ch_text, ch_num_str in chapters:
            try:
                ch_num = int(ch_num_str)
            except ValueError:
                ch_num = processed_count + 1
                
            if target_chapter is not None and ch_num != int(target_chapter):
                continue
                
            # Extract bibliography references (e.g., "1. Brenndoerfer, M. (2025, October 1)...")
            # Match lines starting with numbers, capturing the core Author surname and the Year
            citations_cache = {}
            
            # Find the bibliography section
            works_cited_match = re.search(r'(?:Works Cited|Master List of Artifacts|Bibliography).*$', ch_text, re.IGNORECASE | re.DOTALL)
            if works_cited_match:
                works_cited_text = works_cited_match.group(0)
                # Match lines like: 1. Brenndoerfer, M. (2025, October 1)...
                # We capture the surname (Brenndoerfer) and the year (2025)
                ref_pattern = re.compile(r'^\s*\d+\.\s+([A-Za-z\-]+),\s+[A-Z]\.\s*\(([^)]*)\)', re.MULTILINE)
                refs = ref_pattern.findall(works_cited_text)
                for surname, date_str in refs:
                    # Extract the 4-digit year from the date string (e.g., "2025, October 1" -> "2025")
                    year_match = re.search(r'\b(\d{4})\b', date_str)
                    if year_match:
                        year = year_match.group(1)
                        # Store both the exact match and a normalized key
                        citations_cache[f"({surname} {year})"] = f"{surname} ({year})"
                        citations_cache[f"({surname}, {year})"] = f"{surname} ({year})"
            
            # Replace inline citations with resolved references if found in cache
            resolved_text = ch_text
            for inline_cite, resolved_ref in citations_cache.items():
                resolved_text = resolved_text.replace(inline_cite, f"[{resolved_ref}]")
                
            # Save the clean chapter as a silver markdown file to GCS
            silver_blob_name = f"manuscript/silver/ch{ch_num:02d}_silver.md"
            silver_blob = bucket.blob(silver_blob_name)
            silver_blob.upload_from_string(resolved_text, content_type="text/markdown; charset=utf-8")
            
            processed_count += 1
            
            # If target_chapter is specified, halt processing after that chapter for a cheap dry run
            if target_chapter is not None:
                return f"[SUCCESS] Dry run completed. Processed and saved Chapter {ch_num} to gs://{bucket_name}/{silver_blob_name}"
                
        return f"[SUCCESS] Processed {processed_count} chapters and saved to gs://{bucket_name}/manuscript/silver/"
        
    except Exception as e:
        return f"[ERROR] process_bronze_manuscript failed: {str(e)}"

# =====================================================================
# TASK 2.2: EMBED AND LOAD MANUSCRIPT
# =====================================================================

def embed_and_load_manuscript(silver_gcs_dir: str = "gs://npt-ship/manuscript/silver/", target_chapter: int = None) -> str:
    """
    Reads silver chapter files from GCS, slices them into sequential paragraph chunks,
    checks the existing 'ship.letters_of_marque' table to see if the chunk already exists
    (skipping embedding if text matches), generates a 1536-dimension embedding via Gemini,
    and UPSERTs the record into 'ship.letters_of_marque' using the existing UUID key system.
    """
    try:
        if not silver_gcs_dir.startswith("gs://"):
            return f"[ERROR] Invalid GCS directory: {silver_gcs_dir}. Must start with gs://"
            
        path_parts = silver_gcs_dir[5:].split("/", 1)
        bucket_name = path_parts[0]
        prefix = path_parts[1] if len(path_parts) > 1 else ""
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Initialize Gemini Client safely using the environment API key
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "[ERROR] Gemini API key not found in environment variables."
        gemini_client = Client(api_key=api_key)
        
        conn = _get_strict_cargo_connection()
        cursor = conn.cursor()
        
        upserted_count = 0
        skipped_count = 0
        
        for blob in blobs:
            if not blob.name.endswith("_silver.md"):
                continue
                
            # Extract chapter number from filename (e.g., ch01_silver.md)
            ch_match = re.search(r'ch(\d+)_silver\.md', blob.name)
            if not ch_match:
                continue
                
            ch_num = int(ch_match.group(1))
            if target_chapter is not None and ch_num != int(target_chapter):
                continue
                
            chapter_text = blob.download_as_text(encoding="utf-8")
            
            # Split the chapter text using a regex that breaks on markdown headers while capturing them
            # This ensures headers cleanly update current_section and header_title but DO NOT skip the loop
            # if there is prose associated with them.
            chunks = re.split(r'(^#+\s+.*$)', chapter_text, flags=re.MULTILINE)
            
            current_section = "1"
            header_title = "Chapter Introduction"
            paragraph_index = 0
            
            for chunk in chunks:
                chunk_clean = chunk.strip()
                if not chunk_clean:
                    continue
                
                # If chunk is a header, update current_section and header_title
                if chunk_clean.startswith("#"):
                    header_title = chunk_clean.lstrip("#").strip()
                    current_section = header_title[:50] # Keep it short
                    # We also want to process the header itself as a chunk if it has text,
                    # or we can just let it update the state. Let's treat the header as a chunk
                    # so it gets indexed, but we don't skip it.
                
                # Split the chunk further into paragraphs if it contains multiple paragraphs
                paragraphs = [p.strip() for p in chunk_clean.split("\n\n") if p.strip()]
                
                for p_text in paragraphs:
                    paragraph_index += 1
                    
                    # Check existing 'ship.letters_of_marque' table using chapter_number, section_number, and paragraph_index
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
                            # Text matches, skip embedding API to save costs
                            skipped_count += 1
                            continue
                        else:
                            # Text modified, we will update it
                            chunk_id = existing_id
                    else:
                        # Missing, generate a new UUID chunk_id
                        chunk_id = str(uuid.uuid4())
                    
                    # Generate 1536-dimension embedding via Gemini
                    response = gemini_client.models.embed_content(
                        model="text-embedding-004",
                        contents=p_text,
                        config=types.EmbedContentConfig(output_dimensionality=1536)
                    )
                    embedding = response.embeddings[0].values
                    
                    # UPSERT the record into 'ship.letters_of_marque'
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
                            ch_num, paragraph_index, p_text, embedding,
                            f"gs://{bucket_name}/{blob.name}"
                        )
                    )
                    upserted_count += 1
                
        conn.commit()
        cursor.close()
        conn.close()
        
        return f"[SUCCESS] Embed and load completed. Upserted: {upserted_count}, Skipped (Deduplicated): {skipped_count}"
        
    except Exception as e:
        return f"[ERROR] embed_and_load_manuscript failed: {str(e)}"
