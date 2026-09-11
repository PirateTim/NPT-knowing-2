"""
NPT Fleet Tools: Cargo Vector Indexing & Semantic Search Operations
Architecture: Multi-Index Vector Retrieval & Provenance Linkage (ADR-003 & ADR-013)
"""
import os
import re
import json
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import pg8000.dbapi
from dotenv import load_dotenv
from google.genai import Client, types

load_dotenv(os.path.abspath(".env"))

def _get_strict_cargo_connection():
    """Establishes connection to Content/Cargo warehouse (CONTENT_DATABASE_URL)."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        raise ValueError("[ERROR] CONTENT_DATABASE_URL environment variable is not set.")
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        database=url.path[1:]
    )

def _get_genai_client() -> Client:
    """Instantiates Google GenAI client for embeddings."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("[ERROR] GEMINI_API_KEY environment variable is not set.")
    return Client(api_key=api_key)

def embed_cargo_index(index_scope: str = "all-cargo", batch_limit: Optional[int] = None) -> str:
    """
    Agent Tool & Skill Harness: Cargo Vector Indexer.
    Purpose: Reads acquired cargo text assets from local acquisitions/ or GCS bucket,
    chunks text into paragraph units, generates 1536-dim embeddings via Google GenAI,
    and populates cargo.content_vectors under the specified index_scope.
    Invoked By: GROG (The Quartermaster).
    """
    conn = _get_strict_cargo_connection()
    genai_client = _get_genai_client()
    cursor = conn.cursor()

    try:
        # 1. Fetch metadata records based on index scope
        if index_scope == "only-mainsail":
            query = """
                SELECT DISTINCT m.id, m.source_url, m.title, m.authors, m.publication_date, m.gcp_bucket_path
                FROM cargo.content_metadata m
                JOIN cargo.fleet_enrichments e ON m.id = e.metadata_id
                WHERE e.payload->>'sail_locker' = 'MAINSAIL';
            """
        else: # default: all-cargo (excludes quarantined FLOTSAM)
            query = """
                SELECT m.id, m.source_url, m.title, m.authors, m.publication_date, m.gcp_bucket_path
                FROM cargo.content_metadata m
                WHERE m.id NOT IN (
                    SELECT DISTINCT metadata_id
                    FROM cargo.fleet_enrichments
                    WHERE payload->>'sail_locker' IN ('FLOTSAM', 'WHERRY')
                )
                ORDER BY m.id ASC;
            """
            
        cursor.execute(query)
        metadata_rows = cursor.fetchall()

        if batch_limit:
            metadata_rows = metadata_rows[:batch_limit]

        total_assets = len(metadata_rows)
        upserted_chunks = 0
        skipped_chunks = 0
        failed_assets = 0

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        local_acq_dir = os.path.join(project_root, "acquisitions")

        for meta_id, source_url, title, authors, pub_date, gcp_path in metadata_rows:
            raw_text = None

            # Attempt 1: Try reading local file in acquisitions/
            if gcp_path:
                filename = os.path.basename(gcp_path)
                local_path = os.path.join(local_acq_dir, filename)
                if os.path.exists(local_path):
                    try:
                        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                            raw_text = f.read()
                    except Exception:
                        pass

            # Attempt 2: Download from GCS if local not found
            if not raw_text and gcp_path and gcp_path.startswith("gs://"):
                try:
                    from google.cloud import storage
                    storage_client = storage.Client()
                    bucket_name = "npt-fleet-cargo-hold"
                    blob_name = gcp_path.replace(f"gs://{bucket_name}/", "").replace("acquisitions/", "")
                    bucket = storage_client.bucket(bucket_name)
                    blob = bucket.blob(f"acquisitions/{blob_name}")
                    if blob.exists():
                        raw_text = blob.download_as_text(encoding="utf-8")
                except Exception as e:
                    print(f"[GCS WARNING] Failed to read GCS blob for ID #{meta_id}: {str(e)}")

            if not raw_text:
                failed_assets += 1
                continue

            # Strip acquisition header boilerplate if present
            content_body = raw_text
            if "===========================================================" in raw_text:
                parts = raw_text.split("===========================================================")
                content_body = parts[-1].strip()

            # Paragraph chunking logic (~500 - 1500 chars)
            paragraphs = [p.strip() for p in content_body.split("\n\n") if len(p.strip()) > 80]
            if not paragraphs:
                paragraphs = [content_body[i:i+1000] for i in range(0, len(content_body), 1000)]

            chunk_idx = 0
            for p_text in paragraphs:
                chunk_idx += 1
                chunk_id = f"chunk_{meta_id}_{chunk_idx:03d}"

                # Check if chunk vector already exists
                cursor.execute(
                    "SELECT vector_id FROM cargo.content_vectors WHERE chunk_id = %s AND index_scope = %s;",
                    (chunk_id, index_scope)
                )
                if cursor.fetchone():
                    skipped_chunks += 1
                    continue

                # Generate 1536-dim embedding
                try:
                    response = genai_client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=p_text,
                        config=types.EmbedContentConfig(output_dimensionality=1536)
                    )
                    embedding = response.embeddings[0].values
                except Exception as embed_err:
                    print(f"[EMBED ERROR] Chunk {chunk_id} failed embedding: {str(embed_err)}")
                    continue

                authors_json = json.dumps(authors) if authors else "[]"
                
                cursor.execute(
                    """
                    INSERT INTO cargo.content_vectors (
                        chunk_id, metadata_id, index_scope, source_url, title, authors,
                        publication_date, chunk_index, chunk_text, vector_embedding, gcp_bucket_path
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        chunk_text = EXCLUDED.chunk_text,
                        vector_embedding = EXCLUDED.vector_embedding,
                        created_at = NOW();
                    """,
                    (
                        chunk_id, meta_id, index_scope, source_url, title, authors_json,
                        pub_date, chunk_idx, p_text, str(list(embedding)), gcp_path
                    )
                )
                upserted_chunks += 1

            conn.commit()

        cursor.close()
        conn.close()
        return (
            f"[INDEXING COMPLETE] Scope: '{index_scope}'. Total Assets Processed: {total_assets}. "
            f"Upserted Chunks: {upserted_chunks}, Skipped: {skipped_chunks}, Failed Assets: {failed_assets}."
        )

    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        return f"[ERROR] Cargo vector indexer failed: {str(e)}"


def query_cargo_vector_index(query: str, index_scope: str = "all-cargo", top_k: int = 10) -> str:
    """
    Agent Tool: Cargo Hold Vector & Hybrid Search.
    Purpose: Queries cargo.content_vectors using 1536-dim pgVector cosine similarity
    and keyword matching, returning a JSON array of matching chunks with complete provenance metadata.
    Invoked By: GROG (The Quartermaster), CUTLASS, PEGLEG.
    """
    conn = _get_strict_cargo_connection()
    genai_client = _get_genai_client()
    cursor = conn.cursor()

    try:
        # 1. Embed search query
        query_resp = genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=query,
            config=types.EmbedContentConfig(output_dimensionality=1536)
        )
        query_vector = list(query_resp.embeddings[0].values)

        # 2. Vector Cosine Similarity Query
        sql_vector = """
            SELECT 
                chunk_id, metadata_id, title, authors, publication_date, publisher,
                source_url, gcp_bucket_path, chunk_index, chunk_text,
                (1 - (vector_embedding <=> %s::vector)) AS similarity
            FROM cargo.content_vectors
            WHERE index_scope = %s
            ORDER BY similarity DESC
            LIMIT %s;
        """
        cursor.execute(sql_vector, (str(query_vector), index_scope, top_k))
        vector_rows = cursor.fetchall()

        # 3. Hybrid Keyword Search Fallback
        sql_keyword = """
            SELECT 
                chunk_id, metadata_id, title, authors, publication_date, publisher,
                source_url, gcp_bucket_path, chunk_index, chunk_text,
                0.60 AS similarity
            FROM cargo.content_vectors
            WHERE index_scope = %s AND (
                LOWER(title) LIKE %s OR LOWER(chunk_text) LIKE %s
            )
            LIMIT %s;
        """
        kw_pattern = f"%{query.lower()}%"
        cursor.execute(sql_keyword, (index_scope, kw_pattern, kw_pattern, top_k))
        keyword_rows = cursor.fetchall()

        # Deduplicate & Merge results
        seen_chunks = set()
        combined_results = []

        for row in vector_rows:
            cid = row[0]
            if cid not in seen_chunks:
                seen_chunks.add(cid)
                combined_results.append({
                    "chunk_id": row[0],
                    "metadata_id": row[1],
                    "title": row[2] or "Untitled Asset",
                    "authors": row[3],
                    "publication_date": row[4] or "n.d.",
                    "publisher": row[5] or "Unknown Publisher",
                    "source_url": row[6],
                    "gcp_bucket_path": row[7],
                    "chunk_index": row[8],
                    "chunk_text": row[9],
                    "similarity_score": round(float(row[10]), 4),
                    "search_method": "VECTOR_COSINE"
                })

        for row in keyword_rows:
            cid = row[0]
            if cid not in seen_chunks:
                seen_chunks.add(cid)
                combined_results.append({
                    "chunk_id": row[0],
                    "metadata_id": row[1],
                    "title": row[2] or "Untitled Asset",
                    "authors": row[3],
                    "publication_date": row[4] or "n.d.",
                    "publisher": row[5] or "Unknown Publisher",
                    "source_url": row[6],
                    "gcp_bucket_path": row[7],
                    "chunk_index": row[8],
                    "chunk_text": row[9],
                    "similarity_score": round(float(row[10]), 4),
                    "search_method": "KEYWORD_MATCH"
                })

        cursor.close()
        conn.close()

        if not combined_results:
            return f"[NO MATCHES] No cargo chunks matched the query '{query}' under scope '{index_scope}'."

        return json.dumps({
            "query": query,
            "index_scope": index_scope,
            "total_matches": len(combined_results),
            "results": combined_results
        }, indent=2)

    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        return f"[ERROR] Cargo vector search crashed: {str(e)}"
