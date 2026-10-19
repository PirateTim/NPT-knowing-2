"""
NPT Fleet: Comprehensive Cargo Landscape Clusterer

How to run:
    uv run python helper_scripts/cluster_cargo_landscape.py

What it does:
    Analyzes the entire cargo warehouse landscape, calculating cluster densities, outliers, and inter-cluster cosine similarities.

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
import json
import time
import urllib.parse
from datetime import datetime, timezone
import numpy as np
import pg8000.dbapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD, PCA
from sklearn.preprocessing import normalize
from sklearn.cluster import KMeans
from sklearn.cluster._kmeans import kmeans_plusplus
from dotenv import load_dotenv

load_dotenv(override=True)

DOMAIN_STOPWORDS = {
    # Standard English functional stopwords
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by',
    'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'of', 'in', 'on', 'off', 'over', 'under', 'again', 'further',
    'once', 'here', 'there', 'all', 'any', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're',
    've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
    'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
    'does', 'did', 'doing', 'this', 'that', 'these', 'those', 'it', 'its', 'as', 'we', 'our',
    'us', 'they', 'them', 'their', 'he', 'him', 'his', 'she', 'her', 'i', 'me', 'my', 'you',
    'your', 'which', 'who', 'whom', 'whose', 'what', 'how', 'why', 'where',
    
    # Generic academic & document framing
    'abstract', 'article', 'paper', 'study', 'research', 'published', 'publishing', 'publisher',
    'journal', 'doi', 'http', 'https', 'org', 'com', 'www', 'rights', 'reserved', 'copyright',
    'author', 'authors', 'university', 'press', 'elsevier', 'springer', 'wiley', 'ieee',
    'results', 'methods', 'data', 'using', 'used', 'based', 'approach', 'model', 'models',
    'analysis', 'presents', 'discusses', 'provides', 'also', 'well', 'one', 'two', 'three',
    'four', 'five', 'new', 'like', 'year', 'years', 'time', 'first', 'second', 'even',
    'could', 'may', 'way', 'ways', 'since', 'including', 'included', 'number', 'part',

    # Publishers, Mastheads & Outlets (prevents publisher-based clusters)
    'times', 'york', 'new york', 'york times', 'verge', 'the verge', 'bloomberg', 'reuters',
    'guardian', 'the guardian', 'financial times', 'ft', 'washington', 'post', 'washington post',
    'wsj', 'wall street', 'wall street journal', 'wired', 'techcrunch', 'substack', 'vox',
    'atlantic', 'the atlantic', 'axios', 'ap', 'associated press', 'politico', 'cnbc', 'bbc',
    'cnn', 'forbes', 'fortune', 'ars technica', 'the information', '404 media', 'bellingcat',
    'intercept', 'economist', 'propublica', 'semafor', 'rolling stone', 'daily', 'tribune',

    # Journalistic boilerplate & web scaffolding
    'opinion', 'newsletter', 'subscribe', 'subscription', 'sign up', 'sign in', 'cookie',
    'cookies', 'privacy', 'policy', 'terms', 'service', 'advertisement', 'advertising',
    'photo', 'image', 'images', 'credit', 'caption', 'read more', 'continue reading',
    'click here', 'source', 'en', 'pdf', 'link', 'editor', 'reporter', 'correspondent',
    'bylines', 'bylined', 'follow', 'share', 'posted', 'updated', 'comment', 'comments',
    'audio', 'listen', 'video', 'watch', 'gift', 'gift article', 'unlocked', 'subscriber',

    # Monograph, Book & Chapter artifacts
    'chapter', 'introduction', 'preface', 'epilogue', 'conclusion', 'prologue', 'volume',
    'edition', 'index', 'isbn', 'page', 'pages', 'reich', 'nerd reich', 'nerd',

    # Conversational and general filler words (eliminates the central origin sink)
    'people', 'world', 'human', 'digital', 'work', 'working', 'make', 'making', 'get',
    'getting', 'see', 'seeing', 'know', 'knowing', 'think', 'thinking', 'thought', 'look',
    'looking', 'come', 'coming', 'go', 'going', 'take', 'taking', 'want', 'need', 'needs',
    'good', 'great', 'many', 'much', 'thing', 'things', 'day', 'days', 'week', 'weeks',
    'month', 'months', 'said', 'told', 'asked', 'wrote', 'reported', 'added', 'noted',
    'pointed', 'explained', 'according', 'system', 'systems', 'state', 'states', 'case',
    'cases', 'fact', 'point', 'help', 'set', 'show', 'shows', 'around', 'back', 'still',
    'really', 'something', 'going', 'across', 'often', 'without', 'though', 'however',
    'must', 'down', 'up', 'out', 'says', 'everything', 'anything', 'nothing', 'find',
    'found', 'war', 'better', 'best', 'always', 'never', 'ever', 'might', 'almost'
}

# 50 Atomic Seed Topics (Strict SHARED-HEURISTIC-022 Compliance: Zero '&', 'and', 'vs')
ATOMIC_SEEDS = {
    "Legal Malpractice": "lawyers fake citations sanctions hallucinated precedents disbarment court judge legal liability malpractice",
    "Copyright Litigation": "copyright fair use licensing training data scraping author lawsuits publisher pirated books infringement",
    "Antitrust Enforcement": "antitrust monopoly lina khan ftc justice department anti competitive acquisition lock in market abuse",
    "Federal Regulation": "executive order regulation commerce department compliance nist federal safety institute policy standards",
    "Surveillance Capitalism": "surveillance tracking data harvesting wiretapping spying unauthorized collection privacy warrant",
    "Cognitive Atrophy": "handwriting literacy skills memory cognition reading brain gen z writing skills atrophy decline",
    "Companion Chatbots": "companion emotional attachment intimacy chatbot virtual romantic relationship friendship loneliness",
    "Social Isolation": "isolation human disconnection replacement friends social bonds lonely withdrawal mental health",
    "Platform Enshittification": "enshittification algorithmic decay feed degradation synthetic spam ad load cory doctorow junk",
    "Synthetic Slop": "slop low quality automated content spam farms filler gibberish auto generated garbage",
    "Academic Cheating": "cheating plagiarism honor code student essay bot trace grading homework university exam",
    "Journalistic Disruption": "publisher traffic loss referral collapse newsroom cuts zero click search journalism revenue media",
    "Nuclear Energy": "nuclear energy reactor restarts constellation three mile island baseload contracts utility power plant",
    "Grid Overload": "power grid electricity demand utility bottlenecks substation shortages megawatts energy consumption",
    "Water Consumption": "cooling towers aquifer depletion community drought disputes gallons water usage data center cooling",
    "Zoning Conflicts": "zoning local resident opposition noise pollution land use disputes municipal community pushback",
    "Semiconductor Fabrication": "semiconductors chips tsmc nvidia foundry wafers packaging hardware supply chain asml gpu",
    "Agentic Workflows": "autonomous agents tool use computer use execution loops api execution rogue execution multi agent",
    "MCP Architecture": "model context protocol mcp server tools repository integration context architecture client server",
    "Open Weights": "open weights open source model weights llama mistral deepseek weights release local execution",
    "Reasoning Distillation": "reasoning models chain of thought test time compute synthetic datasets distillation o1 r1",
    "Assembly Optimization": "assembly programming low level systems kernel code compiler efficiency performance c assembly",
    "Prompt Injection": "prompt injection jailbreaks guardrail exploits adversarial attacks red teaming system prompt leak",
    "Financial Speculation": "venture capital bubble circular revenue overvaluation crash investment wall street valuation disaster",
    "White Collar Displacement": "entry level hiring freeze paralegal cuts job replacement automation career white collar employment",
    "Consultant Overbilling": "consultants clawbacks fraudulent deliverables client billing disputes accounting fraud expert fees",
    "Corporate Mergers": "acquisitions talent absorption anti competitive buyouts startup acquihire consolidation deal",
    "Autonomous Driving": "autonomous vehicles robotaxis driverless safety traffic violations waymo cruise tesla self driving",
    "Military Targeting": "military battlefield algorithms lethal drone strikes defense contracts project maven warfare targeting",
    "Biometric Identification": "facial recognition public surveillance police databases facial scans biometrics identification",
    "Audio Deepfakes": "voice cloning audio deepfakes executive impersonation phone scams audio spoofing voice synthesis",
    "Model Jailbreaking": "jailbreak safety filters bypass alignment red team refusal suppression token manipulation",
    "Search Overviews": "search engine google overviews search query zero click web traffic publisher disruption",
    "Algorithmic Bias": "algorithmic discrimination bias fairness disparate impact hiring algorithms demographic disparities",
    "Medical Diagnostics": "clinical diagnostics radiology pathology doctors healthcare patient diagnostic imaging medical",
    "Drug Discovery": "alphafold protein folding drug discovery molecular docking biology pharmacology therapeutics",
    "Election Interference": "election manipulation bot farms voter suppression microtargeting political ads deepfakes",
    "Cloud Hyperscalers": "hyperscalers aws google cloud microsoft azure infrastructure cloud compute data centers",
    "Enterprise SaaS": "enterprise software workflows corporate integration roi pilot compliance security audit b2b",
    "Cyber Defense": "cybersecurity malware detection zero day vulnerability automated patching threat intelligence",
    "Social Media Algorithms": "recommendation algorithms engagement maximizing outrage doomscrolling feed ranking viral",
    "Content Moderation": "trust safety content moderation hate speech automated takedowns platform censorship",
    "Cryptocurrency Mining": "crypto blockchain bitcoin mining energy consumption proof of work hash rate",
    "Robotics Hardware": "humanoid robots actuators manipulation physical embodied robotics boston dynamics tesla bot",
    "Voice Assistants": "smart speakers voice assistants alexa siri conversational speech recognition",
    "EdTech Platforms": "educational technology personalized learning tutoring software classroom student tracking",
    "E Discovery Litigation": "document review electronic discovery subpoena privilege log litigation legal tech",
    "Digital Ad Fraud": "ad fraud bot traffic click farm impression fraud programmatic advertising ad arbitrage",
    "Biosecurity Hazards": "pathogen synthesis biosecurity dual use research viral genome engineering biological threat",
    "Chip Geopolitics": "export controls entity list chip embargo taiwan strait chip sovereignty national security trade"
}

def get_db_connection():
    db_url = os.getenv("CONTENT_DATABASE_URL")
    if not db_url:
        raise ValueError("CONTENT_DATABASE_URL not set.")
    res = urllib.parse.urlparse(db_url)
    conn = pg8000.dbapi.connect(
        user=res.username,
        password=res.password,
        host=res.hostname,
        port=res.port or 5432,
        database=res.path.lstrip('/')
    )
    conn.autocommit = True
    return conn

def format_cluster_label(top_terms):
    """Formats top cluster terms into a clean, human-readable title without redundant sub-phrases."""
    selected = []
    for term in top_terms:
        clean = term.strip().lower()
        if not clean:
            continue
        is_sub = False
        for s in selected:
            s_clean = s.strip().lower()
            if clean in s_clean.split() or s_clean in clean.split() or clean == s_clean:
                is_sub = True
                break
        if not is_sub:
            selected.append(term.replace('_', ' ').title())
        if len(selected) >= 3:
            break
    if not selected:
        selected = [t.replace('_', ' ').title() for t in top_terms[:3]]
    return " • ".join(selected)

def main():
    start_time = time.time()
    print("=" * 70)
    print("NPT FLEET: APPROACH B - HYBRID GUIDED CLUSTERING (100 CLUSTERS)")
    print("50 Pure Atomic Seeds + 50 Emergent k-means++ Slots")
    print("Cost: $0.00 (Zero LLM Tokens)")
    print("=" * 70)

    # 1. Fetch all documents from PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, title, abstract, publication_title, publication_date, source_url, gcp_bucket_path
            FROM cargo.content_metadata
            ORDER BY id ASC;
        """)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    total_docs = len(rows)
    print(f"[*] Fetched {total_docs} documents from cargo.content_metadata.")

    # 2. Assemble corpus text
    doc_ids = []
    corpus_texts = []
    metadata_records = []

    for r in rows:
        mid, title, abstract, pub_title, pub_date, url, gcp_path = r
        title_str = (title or "").strip()
        abstract_str = (abstract or "").strip()
        
        combined = f"{title_str}. {abstract_str}" if abstract_str else title_str
        doc_ids.append(mid)
        corpus_texts.append(combined)
        metadata_records.append({
            "id": mid,
            "title": title_str,
            "publisher": pub_title or "Unknown Source",
            "date": str(pub_date) if pub_date else "",
            "url": url or "",
            "gcp_path": gcp_path or ""
        })

    # 3. TF-IDF Feature Extraction with Domain Stopwords
    print("[*] Vectorizing corpus with TF-IDF (unigrams & bigrams + domain stopwords)...")
    vectorizer = TfidfVectorizer(
        max_df=0.35,
        min_df=3,
        ngram_range=(1, 2),
        sublinear_tf=True,
        stop_words=list(DOMAIN_STOPWORDS)
    )
    tfidf_matrix = vectorizer.fit_transform(corpus_texts)
    vocab = vectorizer.get_feature_names_out()
    print(f"    -> TF-IDF Matrix shape: {tfidf_matrix.shape} (Vocabulary size: {len(vocab):,})")

    # 4. Latent Semantic Analysis (TruncatedSVD with 100 components)
    n_components = 100
    print(f"[*] Reducing dimensions with TruncatedSVD ({n_components} components)...")
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    lsa_matrix = svd.fit_transform(tfidf_matrix)

    # Spherical Normalization: L2 normalize all document vectors so they reside on the unit hypersphere
    # This completely eliminates the central origin sink that caused 600+ document catch-all clusters
    print("[*] Normalizing LSA vectors to unit hypersphere (Spherical / Cosine Space)...")
    lsa_norm = normalize(lsa_matrix)

    # 5. 2D Spatial Projection (PCA) for Galaxy Scatter Plot
    print("[*] Projecting 2D spatial coordinates (X, Y) via PCA...")
    pca_2d = PCA(n_components=2, random_state=42)
    coords_2d = pca_2d.fit_transform(lsa_norm)

    # 6. Hybrid Guided Centroid Construction: 50 Atomic Seeds + 50 Emergent Centers
    seed_keys = list(ATOMIC_SEEDS.keys())
    seed_texts = list(ATOMIC_SEEDS.values())
    num_seeds = len(seed_keys)
    num_emergent = 50
    num_clusters = num_seeds + num_emergent

    print(f"[*] Projecting {num_seeds} Atomic Seeds into latent space...")
    seed_tfidf = vectorizer.transform(seed_texts)
    seed_lsa = svd.transform(seed_tfidf)
    seed_lsa_normalized = normalize(seed_lsa)

    # Sample 50 emergent centers using kmeans++ on normalized spherical vectors
    print(f"[*] Sampling {num_emergent} emergent initial centers via kmeans++...")
    emergent_centers, _ = kmeans_plusplus(lsa_norm, n_clusters=num_emergent, random_state=42)

    initial_centers = np.vstack([seed_lsa_normalized, emergent_centers])
    print(f"    -> Initialized Hybrid Centroid Matrix: {initial_centers.shape}")

    # 7. Execute Spherical Guided K-Means
    print(f"[*] Executing Guided Spherical K-Means ({num_clusters} clusters)...")
    kmeans = KMeans(n_clusters=num_clusters, init=initial_centers, n_init=1, max_iter=300, random_state=42)
    cluster_assignments = kmeans.fit_predict(lsa_norm)

    # 8. Extract Top Distinctive Keywords per Cluster from Original TF-IDF Space
    print("[*] Extracting distinctive cluster centroid keywords...")
    cluster_centers_in_tfidf = svd.inverse_transform(kmeans.cluster_centers_)
    
    cluster_info = {}
    for i in range(num_clusters):
        top_indices = cluster_centers_in_tfidf[i].argsort()[::-1][:8]
        top_keywords = [vocab[ind] for ind in top_indices]
        
        # If it was an atomic seed, anchor the title with the seed name
        if i < num_seeds:
            seed_name = seed_keys[i]
            cluster_label = f"{seed_name} • {format_cluster_label(top_keywords[:2])}"
        else:
            cluster_label = format_cluster_label(top_keywords)

        cluster_info[i] = {
            "cluster_id": i,
            "cluster_label": cluster_label,
            "top_keywords": top_keywords,
            "doc_count": int(np.sum(cluster_assignments == i))
        }

    # 9. Print Discovered Clusters
    print("\n" + "=" * 70)
    print("HYBRID GUIDED CLUSTERS DISCOVERED (TOP 25 BY VOLUME):")
    print("=" * 70)
    sorted_clusters = sorted(cluster_info.items(), key=lambda x: x[1]['doc_count'], reverse=True)
    for c_id, c_data in sorted_clusters[:25]:
        print(f"Cluster {c_id:2d} ({c_data['doc_count']:>4} docs) : {c_data['cluster_label']}")
        print(f"   Keywords: {', '.join(c_data['top_keywords'][:6])}")

    # 10. Save JSON Artifact
    os.makedirs("cargo_ontology", exist_ok=True)
    cluster_json_path = "cargo_ontology/cargo_clusters.json"

    documents_payload = []
    for idx, mid in enumerate(doc_ids):
        c_id = int(cluster_assignments[idx])
        c_meta = cluster_info[c_id]
        x_val = round(float(coords_2d[idx, 0]), 4)
        y_val = round(float(coords_2d[idx, 1]), 4)

        doc_entry = {
            "id": mid,
            "cluster_id": c_id,
            "cluster_label": c_meta["cluster_label"],
            "keywords": c_meta["top_keywords"],
            "coord_x": x_val,
            "coord_y": y_val
        }
        documents_payload.append(doc_entry)

    out_data = {
        "metadata": {
            "total_documents": total_docs,
            "num_clusters": num_clusters,
            "clustered_at": datetime.now(timezone.utc).isoformat(),
            "method": f"TF-IDF + TruncatedSVD({n_components}) + HybridSeededKMeans({num_clusters}) + PCA(2)"
        },
        "clusters": list(cluster_info.values()),
        "documents": documents_payload
    }

    with open(cluster_json_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Wrote cluster model to {cluster_json_path}")

    # 11. Persist Cluster Assignments to PostgreSQL in Fast Batches
    print("[*] Committing cluster assignments to PostgreSQL (cargo.fleet_enrichments) in fast batches...")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM cargo.fleet_enrichments WHERE enrichment_type = 'cluster';")
        
        batch_size = 400
        records = []
        for doc in documents_payload:
            payload = {
                "cluster_id": doc["cluster_id"],
                "cluster_label": doc["cluster_label"],
                "keywords": doc["keywords"],
                "coord_x": doc["coord_x"],
                "coord_y": doc["coord_y"]
            }
            records.append((doc["id"], json.dumps(payload)))

        for i in range(0, len(records), batch_size):
            chunk = records[i:i + batch_size]
            placeholders = ", ".join(["(%s, 'scikit-learn', 'cluster', %s, NOW())"] * len(chunk))
            flat_params = [item for sub in chunk for item in sub]
            cursor.execute(f"""
                INSERT INTO cargo.fleet_enrichments 
                (metadata_id, agent_name, enrichment_type, payload, created_at)
                VALUES {placeholders};
            """, flat_params)

        print(f"[+] Successfully committed {len(records)} cluster enrichments to PostgreSQL.")
    finally:
        cursor.close()
        conn.close()

    elapsed = time.time() - start_time
    print("=" * 70)
    print(f"[SUCCESS] Hybrid Guided Clustering complete in {elapsed:.2f} seconds!")
    print(f"Total Documents: {total_docs} | Clusters: {num_clusters} | Total Spend: $0.00")
    print("=" * 70)

if __name__ == "__main__":
    main()
