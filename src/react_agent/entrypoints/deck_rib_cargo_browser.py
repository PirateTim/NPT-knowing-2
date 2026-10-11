"""
NPT Fleet: Deck Rib & Cargo Cluster Browser & Relationship Map
Entrypoint: src/react_agent/entrypoints/deck_rib_cargo_browser.py
Architecture: Streamlit + Ship Deck Plans (140 Section Ribs) + Bronze+ Tier + Cargo Clusters (100 Clusters / 3,666 Docs) + 297 M:N Edges

Features:
1. Shows the Section Rib metadata (Actor, Enabler, Qualifier, Chain Stage, Doom Point, Warrants).
2. Shows the Bronze+ verbatim manuscript section prose and verified vector nodes.
3. Shows the Cargo Cluster definition (Cluster Label, Top Keywords, Document Count).
4. Displays hyperlinked cargo items with direct links to live source URLs and cloud-hosted GCS copies (+ in-app GCS text streaming).
5. Two-Way Coordinated Navigation: Selecting a Rib updates the associated Clusters; selecting a Cluster updates associated Ribs.
6. Classification Relationship Map: Interactive visualizations, heatmaps, Sankey diagrams, and metrics proving and exploring the Many-to-Many (M:N) mesh.

Execution Law:
  uv run streamlit run src/react_agent/entrypoints/deck_rib_cargo_browser.py --server.port 8504
"""
import os
import sys
import json
import urllib.parse
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pg8000.dbapi
from dotenv import load_dotenv

# Ensure root imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.react_agent.tools.folksonomy_bridge import FolksonomyDeckPlanBridge

load_dotenv(override=True)

st.set_page_config(
    page_title="NPT Fleet: Deck Rib & Cargo Cluster Browser",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .rib-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #E2E8F0;
        margin-bottom: 1rem;
    }
    .stage-badge-1 {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stage-badge-2 {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stage-badge-3 {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .cluster-box {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 1rem;
    }
    .doc-link {
        font-size: 1.05rem;
        font-weight: 600;
        color: #2563EB;
        text-decoration: none;
    }
    .doc-link:hover {
        text-decoration: underline;
    }
    .gcs-link {
        color: #0284C7;
        font-weight: 600;
        text-decoration: none;
    }
    .gcs-link:hover {
        text-decoration: underline;
    }
    .keyword-pill {
        display: inline-block;
        background-color: #E2E8F0;
        color: #334155;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8rem;
        margin: 2px;
    }
    .metric-badge {
        display: inline-block;
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        padding: 6px 12px;
        margin-right: 8px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Loaders & Helpers
# ---------------------------------------------------------------------------

@st.cache_resource
def get_bridge():
    return FolksonomyDeckPlanBridge()

@st.cache_data(ttl=120)
def load_db_cargo_documents():
    """Loads clustered documents from cargo.v_cargo_clusters with source URLs, GCS paths, and abstracts."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return pd.DataFrame()
    try:
        url = urllib.parse.urlparse(conn_string)
        conn = pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port or 5432,
            database=url.path.lstrip('/'),
            ssl_context=True
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                v.metadata_id,
                v.title,
                v.source_url,
                v.publication_date,
                v.publisher,
                v.gcp_bucket_path,
                v.cluster_id,
                v.cluster_label,
                v.cluster_keywords,
                cm.abstract AS excerpt
            FROM cargo.v_cargo_clusters v
            LEFT JOIN cargo.content_metadata cm ON cm.id = v.metadata_id
            ORDER BY v.cluster_id ASC, v.metadata_id ASC;
        """)
        rows = cur.fetchall()
        cols = [
            "metadata_id", "title", "source_url", "publication_date", "publisher",
            "gcp_bucket_path", "cluster_id", "cluster_label", "cluster_keywords", "excerpt"
        ]
        df = pd.DataFrame(rows, columns=cols)
        cur.close()
        conn.close()
        return df
    except Exception as e:
        # Fallback to local JSON
        json_path = os.path.abspath("cargo_ontology/cargo_clusters.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return pd.DataFrame(d.get("documents", []))
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_edges_dataframe():
    """Flattens the 297 cluster-rib edges into a queryable DataFrame."""
    edges_path = os.path.abspath("cargo_ontology/cluster_deckplan_edges.json")
    if not os.path.exists(edges_path):
        return pd.DataFrame()
    with open(edges_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rows = []
    c2r = data.get("cluster_to_ribs", {})
    for cid_str, c_info in c2r.items():
        cid = int(cid_str)
        c_label = c_info.get("cluster_label", f"Cluster {cid}")
        doc_count = c_info.get("doc_count", 0)
        for rib in c_info.get("matched_ribs", []):
            ch_num = rib.get("chapter_number")
            rows.append({
                "cluster_id": cid,
                "cluster_label": c_label,
                "cluster_docs": doc_count,
                "section_id": str(rib.get("section_id", "")).strip().lstrip("sec_"),
                "section_title": rib.get("section_title", ""),
                "chapter_number": ch_num,
                "chapter_label": f"Ch {ch_num:02d}" if ch_num is not None else "Unknown",
                "similarity_score": round(float(rib.get("similarity_score", 0.0)), 4)
            })
    return pd.DataFrame(rows)

def make_gcs_console_url(gcp_path: str) -> str:
    """Generates the direct Google Cloud Console URL for a GCS bucket path."""
    if not gcp_path or not str(gcp_path).startswith("gs://"):
        return "#"
    clean = str(gcp_path)[5:]
    parts = clean.split("/", 1)
    bucket = parts[0]
    blob = parts[1] if len(parts) > 1 else ""
    return f"https://console.cloud.google.com/storage/browser/_details/{bucket}/{blob}"

@st.cache_data(ttl=600)
def fetch_gcs_text_preview(gcp_path: str, max_chars: int = 5000) -> str:
    """Streams text directly from GCS without local disk dependency."""
    if not gcp_path or not str(gcp_path).startswith("gs://"):
        return "No valid GCS storage path provided."
    try:
        from google.cloud import storage
        clean = str(gcp_path)[5:]
        parts = clean.split("/", 1)
        bucket_name = parts[0]
        blob_name = parts[1] if len(parts) > 1 else ""
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_text()
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n... [Truncated. Showing first {max_chars} of {len(content)} characters]"
        return content
    except Exception as e:
        return f"[GCS Read Error]: {str(e)}"

# Initialize state and data
bridge = get_bridge()
df_docs = load_db_cargo_documents()
df_edges = load_edges_dataframe()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="main-title">🧭 NPT Fleet: Deck Rib & Cargo Cluster Browser</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Synthesizing Bilgeladle\'s 140 Manuscript Section Ribs with Grog\'s 100 Empirical Cargo Clusters and 3,666 Acquired Documents</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Top Tabs: Coordinated Browser vs. Relationship Map
# ---------------------------------------------------------------------------
tab_browser, tab_relationship_map = st.tabs([
    "🧭 Two-Way Coordinated Browser (Rib ⟷ Cluster)",
    "🗺️ Classification Relationship Map (Many-to-Many M:N Topology)"
])

# ===========================================================================
# TAB 1: TWO-WAY COORDINATED BROWSER (RIB ⟷ CLUSTER)
# ===========================================================================
with tab_browser:
    # Sidebar Navigation Controls
    st.sidebar.markdown("### 🎛️ Navigation Direction")
    nav_mode = st.sidebar.radio(
        "Select primary entry point:",
        ["📖 Manuscript Rib First (Top-Down)", "📦 Cargo Cluster First (Bottom-Up Empirical)"],
        index=0
    )

    chapters_dict = bridge.deck_plans.get("chapters", {})
    all_clusters = bridge.list_all_clusters()

    if nav_mode == "📖 Manuscript Rib First (Top-Down)":
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📖 Step 1: Select Manuscript Rib")
        
        chapter_options = []
        for k in sorted(chapters_dict.keys(), key=lambda x: chapters_dict[x].get("chapter_number", 0)):
            ch_info = chapters_dict[k]
            chapter_options.append(f"Chapter {ch_info.get('chapter_number')}: {ch_info.get('chapter_title')}")
        
        selected_ch_str = st.sidebar.selectbox("Manuscript Chapter", chapter_options, index=1 if len(chapter_options) > 1 else 0)
        ch_num_selected = int(selected_ch_str.split(":")[0].replace("Chapter", "").strip())
        ch_key = f"chapter_{ch_num_selected}"
        ch_data = chapters_dict.get(ch_key, {})
        
        section_ribs_dict = ch_data.get("section_ribs", {})
        rib_options = []
        for s_k, s_v in section_ribs_dict.items():
            rib_options.append(f"Section {s_v.get('section_id')}: {s_v.get('section_title')}")
        
        selected_rib_str = st.sidebar.selectbox("Section Rib", rib_options, index=0)
        selected_sec_id = selected_rib_str.split(":")[0].replace("Section", "").strip()
        current_rib = bridge.get_section_rib(selected_sec_id) or {}

        # Look up associated clusters for this rib
        associated_clusters = bridge.get_clusters_for_rib(selected_sec_id, min_score=0.5)

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 📦 Step 2: Associated Clusters ({len(associated_clusters)} found)")
        
        cluster_override = st.sidebar.checkbox("Browse unlinked / all 100 clusters", value=False)
        
        if not cluster_override and associated_clusters:
            cluster_choice_opts = [
                f"Cluster {c['cluster_id']}: {c['cluster_label']} ({c.get('doc_count', 0)} docs | Sim: {c.get('similarity_score', 0):.2f})"
                for c in associated_clusters
            ]
            selected_cluster_choice = st.sidebar.selectbox("Select Matched Cluster", cluster_choice_opts, index=0)
            selected_cluster_id = int(selected_cluster_choice.split(":")[0].replace("Cluster", "").strip())
        else:
            if not associated_clusters:
                st.sidebar.info(f"No direct vector matches for Section {selected_sec_id} above threshold. Showing all 100 clusters:")
            cluster_options = [f"Cluster {c['cluster_id']}: {c['cluster_label']} ({c.get('doc_count', 0)} docs)" for c in all_clusters]
            selected_cluster_str = st.sidebar.selectbox("All Cargo Clusters", cluster_options, index=0)
            selected_cluster_id = int(selected_cluster_str.split(":")[0].replace("Cluster", "").strip())

        current_cluster = bridge.get_cluster(selected_cluster_id) or {}

    else:
        # Cargo Cluster First
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📦 Step 1: Select Cargo Cluster")
        cluster_options = [f"Cluster {c['cluster_id']}: {c['cluster_label']} ({c.get('doc_count', 0)} docs)" for c in all_clusters]
        selected_cluster_str = st.sidebar.selectbox("Cargo Cluster", cluster_options, index=0)
        selected_cluster_id = int(selected_cluster_str.split(":")[0].replace("Cluster", "").strip())
        current_cluster = bridge.get_cluster(selected_cluster_id) or {}

        # Look up associated Section Ribs for this cluster
        associated_ribs = bridge.get_ribs_for_cluster(selected_cluster_id, min_score=0.5)

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### 📖 Step 2: Associated Ribs ({len(associated_ribs)} found)")
        rib_override = st.sidebar.checkbox("Browse unlinked / all ribs", value=False)

        if not rib_override and associated_ribs:
            rib_choice_opts = [
                f"Section {r['section_id']}: {r['section_title']} (Ch {r.get('chapter_number')} | Sim: {r.get('similarity_score', 0):.2f})"
                for r in associated_ribs
            ]
            selected_rib_choice = st.sidebar.selectbox("Select Matched Section Rib", rib_choice_opts, index=0)
            selected_sec_id = selected_rib_choice.split(":")[0].replace("Section", "").strip()
            current_rib = bridge.get_section_rib(selected_sec_id) or {}
            ch_num_selected = current_rib.get("chapter_number", 1)
        else:
            if not associated_ribs:
                st.sidebar.info(f"No direct vector matches for Cluster {selected_cluster_id} above threshold. Showing full selector:")
            chapter_options = [f"Chapter {chapters_dict[k].get('chapter_number')}: {chapters_dict[k].get('chapter_title')}" for k in sorted(chapters_dict.keys(), key=lambda x: chapters_dict[x].get("chapter_number", 0))]
            selected_ch_str = st.sidebar.selectbox("Manuscript Chapter", chapter_options, index=0)
            ch_num_selected = int(selected_ch_str.split(":")[0].replace("Chapter", "").strip())
            ch_data = chapters_dict.get(f"chapter_{ch_num_selected}", {})
            section_ribs_dict = ch_data.get("section_ribs", {})
            rib_options = [f"Section {s_v.get('section_id')}: {s_v.get('section_title')}" for s_k, s_v in section_ribs_dict.items()]
            selected_rib_str = st.sidebar.selectbox("Section Rib", rib_options, index=0)
            selected_sec_id = selected_rib_str.split(":")[0].replace("Section", "").strip()
            current_rib = bridge.get_section_rib(selected_sec_id) or {}

    # ---------------------------------------------------------------------------
    # Main Split View (Coordinated Columns)
    # ---------------------------------------------------------------------------
    col_manuscript, col_cargo = st.columns([1, 1], gap="large")

    # ===========================================================================
    # LEFT COLUMN: THE MANUSCRIPT GROUND TRUTH (RIB & BRONZE+)
    # ===========================================================================
    with col_manuscript:
        # Chapter Mast Banner (Author's Direct Intent & Primary Vector of Destruction)
        ch_meta = chapters_dict.get(f"chapter_{current_rib.get('chapter_number', ch_num_selected)}", {})
        mast_note = ch_meta.get("mast_author_note")
        mast_vector = ch_meta.get("mast_vector_of_destruction")
        
        if mast_vector:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: #F8FAFC; border-radius: 8px; padding: 14px 18px; margin-bottom: 1rem; border-left: 5px solid #F59E0B;">
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #F59E0B; font-weight: 700; margin-bottom: 4px;">
                    ⚓ Chapter {current_rib.get('chapter_number', ch_num_selected)}: Primary Vector of Destruction (The Mast)
                </div>
                <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 6px; color: #FFFFFF;">
                    "{mast_vector}"
                </div>
                <div style="font-size: 0.85rem; color: #CBD5E1; font-style: italic; line-height: 1.4;">
                    <strong>Author's Intent:</strong> "{mast_note}"
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.subheader(f"📖 1. Section Rib: {current_rib.get('section_id')} — {current_rib.get('section_title')}")
        
        # 1: SHOW THE RIB METADATA
        with st.container():
            chain_stage = current_rib.get("chain_stage", "Unspecified Stage")
            stage_class = "stage-badge-2"
            if "Stage 1" in str(chain_stage): stage_class = "stage-badge-1"
            elif "Stage 3" in str(chain_stage): stage_class = "stage-badge-3"
            
            st.markdown(f"""
            <div class="rib-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #1E293B;">Chapter {current_rib.get('chapter_number')}: {current_rib.get('chapter_title')}</span>
                    <span class="{stage_class}">{chain_stage}</span>
                </div>
                <p><strong>👤 Operative Actor:</strong> {current_rib.get('operative_actor') or 'Not specified'}</p>
                <p><strong>🏛️ Upstream Enabler:</strong> {current_rib.get('upstream_enabler') or 'Not specified'}</p>
                <p><strong>⚡ Behavioral Qualifier:</strong> <em>"{current_rib.get('behavioral_qualifier') or 'N/A'}"</em></p>
                <p><strong>💥 Specific Doom Point:</strong> <span style="color: #991B1B;">{current_rib.get('specific_doom_point') or 'N/A'}</span></p>
                <p><strong>📜 Witness Warrants:</strong> <span style="color: #475569;">{current_rib.get('witness_warrants') or 'N/A'}</span></p>
            </div>
            """, unsafe_allow_html=True)

        # 2: SHOW THE BRONZE PLUS SECTION ASSOCIATED WITH THE RIB
        st.subheader(f"📄 2. Bronze+ Verbatim Manuscript Text")
        bronze_plus_text = bridge.get_bronze_plus_content(selected_sec_id)
        
        if bronze_plus_text:
            ch_folder = f"ch{ch_num_selected:02d}"
            file_name = f"{ch_folder}_sec{selected_sec_id}_bronze_plus.md"
            st.caption(f"Physical Source: `ship/bronze_plus/chapters/{ch_folder}/{file_name}` ({len(bronze_plus_text.split())} words)")
            
            with st.expander("Expand Verbatim Section Prose & Verified Vector Nodes", expanded=True):
                st.markdown(bronze_plus_text)
        else:
            st.info(f"No standalone Bronze+ text file found for Section {selected_sec_id}.")

    # ===========================================================================
    # RIGHT COLUMN: THE REAL-WORLD CARGO HOLD (CLUSTERS & DOCUMENTS)
    # ===========================================================================
    with col_cargo:
        # 3: SHOW THE CARGO CLUSTER NAME AND DEFINITION
        st.subheader(f"🏷️ 3. Cargo Cluster Definition: Cluster {current_cluster.get('cluster_id')}")
        
        with st.container():
            keywords = current_cluster.get("top_keywords", [])
            keywords_html = "".join([f'<span class="keyword-pill">{kw}</span>' for kw in keywords])
            doc_count = current_cluster.get("doc_count", 0)
            
            st.markdown(f"""
            <div class="cluster-box">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-size: 1.25rem; font-weight: 700; color: #166534;">{current_cluster.get('cluster_label')}</span>
                    <span style="background-color: #DCFCE7; color: #15803D; font-weight: 700; padding: 4px 12px; border-radius: 12px;">{doc_count} Documents</span>
                </div>
                <div style="margin-top: 8px;">
                    <strong>Top Empirical Keywords:</strong><br/>
                    {keywords_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 4: HYPERLINKED LIST OF THE CARGO ITEMS IN THE CLUSTER
        st.subheader(f"🔗 4. Hyperlinked Cargo Documents ({doc_count} Items)")
        
        # Filter documents for this cluster
        if not df_docs.empty and "cluster_id" in df_docs.columns:
            cluster_docs = df_docs[df_docs["cluster_id"] == selected_cluster_id]
        else:
            cluster_docs = pd.DataFrame(bridge.get_cluster_documents(selected_cluster_id))
        
        if not cluster_docs.empty:
            # Search filter within cluster
            search_kw = st.text_input("Filter documents in this cluster by keyword/title:", "", placeholder="Type title keyword...")
            if search_kw:
                cluster_docs = cluster_docs[cluster_docs["title"].str.contains(search_kw, case=False, na=False)]
                st.caption(f"Showing {len(cluster_docs)} matching documents.")
                
            # Document list container
            doc_container = st.container(height=650)
            with doc_container:
                for idx, (_, row) in enumerate(cluster_docs.iterrows(), start=1):
                    doc_id = row.get("metadata_id") or row.get("id")
                    title = row.get("title") or f"Cargo Item #{doc_id}"
                    source_url = row.get("source_url") or "#"
                    pub_date = row.get("publication_date") or "Date Unknown"
                    publisher = row.get("publisher") or "Unknown Publisher"
                    gcp_path = row.get("gcp_bucket_path") or ""
                    gcs_console_url = make_gcs_console_url(gcp_path)
                    
                    st.markdown(f"""
                    <div style="padding: 10px; margin-bottom: 8px; background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px;">
                        <span style="color: #64748B; font-size: 0.82rem; font-weight: 700;">#{doc_id} • {pub_date} • {publisher}</span><br/>
                        <a href="{source_url}" target="_blank" class="doc-link">🌐 {title} ↗</a><br/>
                        <span style="font-size: 0.82rem; color: #0284C7;">
                            ☁️ Cloud Copy: <a href="{gcs_console_url}" target="_blank" class="gcs-link">{gcp_path} ↗</a>
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Expandable details with abstract and in-app GCS reader
                    with st.expander(f"Metadata Details & GCS Reader for Doc #{doc_id}", expanded=False):
                        excerpt = row.get("excerpt") or ""
                        if excerpt and len(str(excerpt).strip()) > 0:
                            st.markdown(f"**📝 Excerpt / Abstract:**\n> *{str(excerpt).strip()}*\n")
                        st.markdown(f"- **Live Web Source:** [{source_url}]({source_url})")
                        st.markdown(f"- **Cloud Archive Console:** [{gcs_console_url}]({gcs_console_url})")
                        st.markdown(f"- **GCS Object Path:** `{gcp_path}`")
                        
                        keywords_raw = row.get("cluster_keywords") or row.get("keywords")
                        if keywords_raw:
                            st.markdown(f"- **Keywords:** `{keywords_raw}`")
                        
                        # In-app GCS text viewer
                        if st.checkbox(f"📖 Read Full Cloud Copy (Stream from GCS)", key=f"stream_view_{doc_id}_{idx}"):
                            with st.spinner("Streaming verbatim text from Cloud Storage..."):
                                cloud_text = fetch_gcs_text_preview(gcp_path)
                                st.text_area("Cloud Text Payload", cloud_text, height=280)
        else:
            st.warning(f"No documents currently indexed under Cluster {selected_cluster_id}.")


# ===========================================================================
# TAB 2: CLASSIFICATION RELATIONSHIP MAP (MANY-TO-MANY M:N TOPOLOGY)
# ===========================================================================
with tab_relationship_map:
    st.subheader("🗺️ The Dual Classification Relationship Map")
    
    st.markdown("""
    > [!IMPORTANT]
    > **Is there a 1-to-1 match from manuscript rib to cargo cluster?**  
    > **No — it is definitively a Many-to-Many (M:N) Relationship Mesh.**  
    > A single empirical cargo cluster (e.g. *Legal Malpractice & Liability*) provides grounding evidence across multiple chapters (Mata v. Avianca in Ch 1, Madisonian IP in Ch 6). Conversely, a single manuscript section rib (e.g. *Section 12.4: The Surveillance Apparatus*) synthesizes empirical evidence across multiple cargo clusters (*Palantir Surveillance*, *ICE Data Tracking*, *Federal Information Control*).
    """)

    # Metric Cards Bar
    if not df_edges.empty:
        total_clusters_mapped = df_edges["cluster_id"].nunique()
        total_ribs_mapped = df_edges["section_id"].nunique()
        total_edges_count = len(df_edges)
        total_docs_represented = df_edges.drop_duplicates(subset=["cluster_id"])["cluster_docs"].sum()

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Empirical Cargo Clusters", f"{total_clusters_mapped} / 100", "100% Clustered")
        col_m2.metric("Connected Section Ribs", f"{total_ribs_mapped} / 140", "99 Ribs with Edges")
        col_m3.metric("Multi-Directional Edges", f"{total_edges_count}", "Avg 3.0 Links / Node")
        col_m4.metric("Cargo Docs Represented", f"{total_docs_represented:,}", "100% of Fleet Cargo")
        
        st.markdown("---")

        # ---------------------------------------------------------------------------
        # Section A: Chapter x Cluster Heatmap Matrix
        # ---------------------------------------------------------------------------
        st.markdown("### 1. Cross-Classification Density Matrix (Chapters ⟷ Clusters)")
        st.caption("Shows how empirical cargo clusters intersect with the 13 manuscript chapters. Darker blocks indicate heavy evidence concentration.")

        # Aggregate counts by chapter and cluster
        heatmap_data = df_edges.groupby(["chapter_label", "cluster_id"]).size().reset_index(name="edge_count")
        pivot_table = heatmap_data.pivot(index="chapter_label", columns="cluster_id", values="edge_count").fillna(0)
        
        # Sort chapters numerically
        sorted_ch_labels = sorted(pivot_table.index, key=lambda x: int(x.replace("Ch", "").strip()) if x.replace("Ch", "").strip().isdigit() else 99)
        pivot_table = pivot_table.reindex(sorted_ch_labels)

        fig_heat = px.imshow(
            pivot_table,
            labels=dict(x="Cargo Cluster ID (0 to 99)", y="Manuscript Chapter", color="Edges"),
            x=pivot_table.columns,
            y=pivot_table.index,
            color_continuous_scale="YlGnBu",
            aspect="auto",
            title="Evidence Density: Manuscript Chapter vs. Empirical Cargo Cluster ID"
        )
        fig_heat.update_layout(height=420, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig_heat, use_container_width=True)

        # ---------------------------------------------------------------------------
        # Section B: Multi-Hub Analysis
        # ---------------------------------------------------------------------------
        st.markdown("### 2. Hub Analysis: Cross-Cutting Clusters & High-Gravity Ribs")
        col_hub1, col_hub2 = st.columns(2)

        with col_hub1:
            st.markdown("#### 🌐 Top Systemic Clusters (Spanning Multiple Chapters)")
            st.caption("Empirical cargo topics that provide grounding across 3 or more distinct chapters.")
            
            cluster_ch_span = df_edges.groupby(["cluster_id", "cluster_label"]).agg(
                chapters_spanned=("chapter_number", "nunique"),
                ribs_matched=("section_id", "nunique"),
                doc_count=("cluster_docs", "first")
            ).reset_index().sort_values(by=["chapters_spanned", "ribs_matched"], ascending=[False, False])
            
            st.dataframe(
                cluster_ch_span.head(15).rename(columns={
                    "cluster_id": "Cluster ID",
                    "cluster_label": "Cluster Topic",
                    "chapters_spanned": "Ch Spanned",
                    "ribs_matched": "Ribs Matched",
                    "doc_count": "Docs"
                }),
                hide_index=True,
                use_container_width=True
            )

        with col_hub2:
            st.markdown("#### ⚓ High-Gravity Section Ribs (Highest Cargo Backing)")
            st.caption("Manuscript Section Ribs supported by the largest total volume of acquired real-world cargo.")
            
            rib_cargo_vol = df_edges.groupby(["section_id", "section_title", "chapter_label"]).agg(
                clusters_connected=("cluster_id", "nunique"),
                total_cargo_docs=("cluster_docs", "sum"),
                max_similarity=("similarity_score", "max")
            ).reset_index().sort_values(by="total_cargo_docs", ascending=False)
            
            st.dataframe(
                rib_cargo_vol.head(15).rename(columns={
                    "section_id": "Section",
                    "section_title": "Rib Title",
                    "chapter_label": "Chapter",
                    "clusters_connected": "Clusters",
                    "total_cargo_docs": "Total Docs",
                    "max_similarity": "Top Sim"
                }),
                hide_index=True,
                use_container_width=True
            )

        # ---------------------------------------------------------------------------
        # Section C: Interactive Relationship Explorer Table
        # ---------------------------------------------------------------------------
        st.markdown("---")
        st.markdown("### 3. Master Edge Directory (All 297 Relationships)")
        st.caption("Search, filter, and inspect the specific mathematical vector associations between the two systems.")
        
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            filter_ch = st.selectbox(
                "Filter by Chapter:",
                ["All Chapters"] + sorted(list(df_edges["chapter_label"].unique()))
            )
        with col_f2:
            search_edge = st.text_input("Search Rib Title or Cluster Topic:", "")
        
        filtered_edges = df_edges.copy()
        if filter_ch != "All Chapters":
            filtered_edges = filtered_edges[filtered_edges["chapter_label"] == filter_ch]
        if search_edge:
            mask = (
                filtered_edges["section_title"].str.contains(search_edge, case=False, na=False) |
                filtered_edges["cluster_label"].str.contains(search_edge, case=False, na=False)
            )
            filtered_edges = filtered_edges[mask]
        
        st.dataframe(
            filtered_edges[[
                "chapter_label", "section_id", "section_title",
                "cluster_id", "cluster_label", "cluster_docs", "similarity_score"
            ]].sort_values(by=["chapter_label", "similarity_score"], ascending=[True, False]).rename(columns={
                "chapter_label": "Chapter",
                "section_id": "Section",
                "section_title": "Section Title",
                "cluster_id": "Cluster ID",
                "cluster_label": "Cluster Label",
                "cluster_docs": "Cluster Docs",
                "similarity_score": "Cosine Sim"
            }),
            hide_index=True,
            use_container_width=True,
            height=400
        )
    else:
        st.warning("No relationship edges loaded from `cargo_ontology/cluster_deckplan_edges.json`.")

st.markdown("---")
st.caption("NPT Fleet Intelligence Console • Bilgeladle Thesis Alignment Engine • Single Source of Truth (GCS/Ship)")
