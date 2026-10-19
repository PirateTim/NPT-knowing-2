"""
NPT Fleet: Cargo Landscape Inspector & Cluster Metrics

How to run:
    uv run python helper_scripts/inspect_cargo_landscape.py

What it does:
    Generates statistical distributions, sector breakdowns, and cluster assignment metrics across all active cargo.

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
import re
import json
import collections
import urllib.parse
from datetime import datetime
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by',
    'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'of', 'in', 'on', 'off', 'over', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're',
    've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
    'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'this', 'that', 'these', 'those', 'it', 'its', 'as', 'we', 'our',
    'us', 'they', 'them', 'their', 'he', 'him', 'his', 'she', 'her', 'i', 'me', 'my', 'you',
    'your', 'which', 'who', 'whom', 'whose', 'what', 'how', 'why', 'where',
    # Domain boilerplate
    'abstract', 'paper', 'article', 'study', 'research', 'author', 'authors', 'published',
    'publishing', 'publisher', 'journal', 'doi', 'http', 'https', 'org', 'com', 'www', 'rights',
    'reserved', 'copyright', 'elsevier', 'springer', 'wiley', 'ieee', 'press', 'university',
    'results', 'methods', 'data', 'using', 'used', 'based', 'approach', 'model', 'models',
    'analysis', 'presents', 'discusses', 'provides', 'also', 'well', 'one', 'two', 'new'
}

def get_db_connection():
    db_url = os.getenv("CONTENT_DATABASE_URL")
    if not db_url:
        raise ValueError("CONTENT_DATABASE_URL not set in environment.")
    res = urllib.parse.urlparse(db_url)
    return pg8000.dbapi.connect(
        user=res.username,
        password=res.password,
        host=res.hostname,
        port=res.port or 5432,
        database=res.path.lstrip('/')
    )

def extract_tokens(text: str):
    # Normalize and extract alpha words
    words = re.findall(r'[bB]?[a-zA-Z]{3,}', text.lower())
    return [w for w in words if w not in STOPWORDS]

def extract_ngrams(words, n):
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

def extract_entities(text: str):
    # Regex heuristic for capitalized proper multi-word nouns or known acronyms
    entities = []
    # Pattern: 2-3 capitalized words e.g. "Federal Trade Commission", "Constellation Energy"
    matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', text)
    for m in matches:
        m_lower = m.lower()
        if not any(sw in m_lower.split() for sw in ['the', 'this', 'that', 'with', 'from', 'when']):
            entities.append(m)
    # Acronyms (e.g., LLM, AI, FTC, DOJ, SEC, GPU, SMR, AGI)
    acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
    for acr in acronyms:
        if acr not in {'AND', 'THE', 'FOR', 'NOT', 'ARE', 'BUT', 'ALL', 'CAN', 'HAS', 'HAD', 'NEW'}:
            entities.append(acr)
    return entities

def main():
    print("=" * 70)
    print("NPT FLEET: SURFACE MINING CARGO HOLD (Zero-Cost Landscape Analysis)")
    print("=" * 70)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, abstract, publication_title, publication_date, source_url
            FROM cargo.content_metadata
            ORDER BY id ASC;
        """)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    total_assets = len(rows)
    print(f"[*] Fetched {total_assets} assets from cargo.content_metadata.")

    unigrams = collections.Counter()
    bigrams = collections.Counter()
    trigrams = collections.Counter()
    publishers = collections.Counter()
    entities = collections.Counter()
    years = collections.Counter()
    abstract_count = 0

    for row in rows:
        meta_id, title, abstract, pub_title, pub_date, url = row
        title_str = title or ""
        abstract_str = abstract or ""
        
        if abstract_str.strip() and len(abstract_str.strip()) > 20:
            abstract_count += 1
            full_text = f"{title_str} . {abstract_str}"
        else:
            full_text = title_str

        # Publishers
        if pub_title and pub_title.strip():
            publishers[pub_title.strip()] += 1
        elif url:
            domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
            publishers[domain] += 1

        # Dates / Years
        if pub_date:
            year_match = re.search(r'\b(19\d\d|20\d\d)\b', str(pub_date))
            if year_match:
                years[year_match.group(1)] += 1
        elif abstract_str:
            year_match = re.search(r'\b(19\d\d|20\d\d)\b', abstract_str[:200])
            if year_match:
                years[year_match.group(1)] += 1

        # Tokens
        tokens = extract_tokens(full_text)
        unigrams.update(tokens)
        bigrams.update(extract_ngrams(tokens, 2))
        trigrams.update(extract_ngrams(tokens, 3))
        
        # Entity candidates from original case text
        ents = extract_entities(full_text)
        entities.update(ents)

    # Filter out entities that appear only once or are generic
    filtered_entities = {k: v for k, v in entities.items() if v >= 3 and len(k) > 2}

    os.makedirs("cargo_ontology", exist_ok=True)
    out_file = "cargo_ontology/corpus_surface_matrix.json"
    
    matrix_data = {
        "metadata": {
            "total_assets": total_assets,
            "assets_with_abstracts": abstract_count,
            "abstract_coverage_pct": round((abstract_count / total_assets) * 100, 2) if total_assets else 0,
            "analyzed_at": datetime.utcnow().isoformat() + "Z"
        },
        "top_unigrams": unigrams.most_common(200),
        "top_bigrams": bigrams.most_common(200),
        "top_trigrams": trigrams.most_common(150),
        "top_publishers": publishers.most_common(100),
        "top_entities": collections.Counter(filtered_entities).most_common(150),
        "year_distribution": sorted(years.items(), key=lambda x: x[0])
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matrix_data, f, indent=2, ensure_ascii=False)

    print(f"[+] Successfully wrote corpus matrix to {out_file}")
    print("\n--- CORPUS LANDSCAPE SUMMARY ---")
    print(f"Total Cargo Assets:       {total_assets}")
    print(f"Rich Abstracts Found:     {abstract_count} ({matrix_data['metadata']['abstract_coverage_pct']}%)")
    print(f"Distinct Publishers/Sites: {len(publishers)}")
    
    print("\n--- TOP 20 BIGRAM PHRASES (Thematic Vectors) ---")
    for phrase, count in bigrams.most_common(20):
        print(f"  {phrase:<35} : {count:>5}")

    print("\n--- TOP 15 TRIGRAM PHRASES ---")
    for phrase, count in trigrams.most_common(15):
        print(f"  {phrase:<40} : {count:>5}")

    print("\n--- TOP 15 ENTITIES & ACRONYMS ---")
    for ent, count in collections.Counter(filtered_entities).most_common(15):
        print(f"  {ent:<30} : {count:>5}")

    print("\n--- TOP 10 PUBLISHERS / SOURCES ---")
    for pub, count in publishers.most_common(10):
        print(f"  {pub[:40]:<42} : {count:>5}")

    print("\n--- TOP PUBLICATION YEARS ---")
    top_years = sorted(years.items(), key=lambda x: x[1], reverse=True)[:8]
    for yr, count in sorted(top_years, key=lambda x: x[0]):
        print(f"  {yr} : {count}")

    print("=" * 70)

if __name__ == "__main__":
    main()
