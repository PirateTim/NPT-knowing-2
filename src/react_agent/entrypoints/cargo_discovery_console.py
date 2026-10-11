"""
NPT Fleet: Cargo Discovery & Organic Clustering Console
Entrypoint: src/react_agent/entrypoints/cargo_discovery_console.py
Architecture: Streamlit + 2D Topic Galaxy (Plotly Scatter) + Treemap + Vertex AI Search REST
Approach B: Unsupervised Mathematical Clustering ($0.00 Cost, Zero LLM Tokens)
Single Source of Truth (GCS) | Zero-Compound Categories | Part of GitHub Issue #120
"""
import os
import sys
import json
import urllib.parse
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pg8000.dbapi
from dotenv import load_dotenv

# Ensure root imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

load_dotenv(override=True)

st.set_page_config(
    page_title="NPT Fleet: Cargo Discovery & Organic Clustering",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px 18px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-lbl {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data Loaders (Database & Fallback)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_cargo_cluster_data():
    """Loads clustered cargo documents from cargo.v_cargo_clusters in Cloud SQL."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        st.error("CONTENT_DATABASE_URL not set.")
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
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                metadata_id,
                title,
                source_url,
                publication_date,
                publisher,
                gcp_bucket_path,
                cluster_id,
                cluster_label,
                cluster_keywords,
                coord_x,
                coord_y,
                clustered_at
            FROM cargo.v_cargo_clusters
            ORDER BY metadata_id ASC;
        """)
        rows = cursor.fetchall()
        cols = [
            "metadata_id", "title", "source_url", "publication_date", "publisher",
            "gcp_bucket_path", "cluster_id", "cluster_label", "cluster_keywords",
            "coord_x", "coord_y", "clustered_at"
        ]
        df = pd.DataFrame(rows, columns=cols)
        cursor.close()
        conn.close()
        return df
    except Exception as e:
        st.warning(f"Could not connect to PostgreSQL ({e}). Attempting fallback to cargo_ontology/cargo_clusters.json...")
        json_path = "cargo_ontology/cargo_clusters.json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data.get("documents", []))
            return df
        return pd.DataFrame()

@st.cache_data
def load_cluster_metadata():
    """Loads top-level cluster centroid metadata from JSON artifact."""
    json_path = "cargo_ontology/cargo_clusters.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def make_gcs_console_url(path: str) -> str:
    """Generates an active Google Cloud Storage console URL for a given blob."""
    if not path:
        return ""
    clean = str(path).replace("gs://", "").strip()
    if clean.startswith("npt-fleet-cargo-hold/"):
        clean = clean[len("npt-fleet-cargo-hold/"):]
    clean = clean.lstrip("/")
    if not clean.startswith("acquisitions/"):
        clean = f"acquisitions/{clean}"
    return f"https://console.cloud.google.com/storage/browser/_details/npt-fleet-cargo-hold/{clean}"

# ---------------------------------------------------------------------------
# Vertex AI Search Helper (With Snippet Spec Fixed)
# ---------------------------------------------------------------------------

def execute_vertex_search(query: str, page_size: int = 10):
    """Executes hybrid search over GCS documents with explicit snippetSpec for full extractive snippets."""
    try:
        import google.auth
        import google.auth.transport.requests
        import requests

        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
            "x-goog-user-project": "npt-reckoning-1"
        }
        url = "https://discoveryengine.googleapis.com/v1/projects/npt-reckoning-1/locations/global/collections/default_collection/engines/npt-cargo-search-app/servingConfigs/default_search:search"
        
        # Explicit snippetSpec ensures Vertex AI Search returns rich snippets on Standard Edition
        payload = {
            "query": query,
            "pageSize": page_size,
            "contentSearchSpec": {
                "snippetSpec": {
                    "returnSnippet": True
                }
            },
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"}
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        if resp.status_code == 200:
            return resp.json().get("results", [])
        else:
            st.error(f"Vertex Search API returned status {resp.status_code}: {resp.text}")
            return []
    except Exception as e:
        st.error(f"Vertex Search connection failed: {e}")
        return []

# ---------------------------------------------------------------------------
# Main UI Logic
# ---------------------------------------------------------------------------

df = load_cargo_cluster_data()
cluster_meta = load_cluster_metadata()

st.markdown('<div class="main-title">🌌 NPT Fleet: Cargo Discovery & Organic Clustering</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Unsupervised Mathematical Clustering (Approach B: $0.00 Spend, Zero LLM Tokens) & Sub-Second Hybrid Search over ~4,000 External Documents (GCS SSOT)</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("No data retrieved from cargo.v_cargo_clusters. Please verify the database view.")
    st.stop()

# Clean formatting of cluster labels and keywords
def clean_keywords(val):
    if isinstance(val, list):
        return ", ".join(val)
    return str(val) if val else ""

df["keywords_str"] = df["cluster_keywords"].apply(clean_keywords)
df["display_cluster"] = df.apply(lambda r: f"[{r['cluster_id']:02d}] {r['cluster_label']}", axis=1)

# Compute high-level KPIs
total_assets = len(df)
num_clusters = df["cluster_id"].nunique()
avg_docs_per_cluster = int(total_assets / num_clusters) if num_clusters else 0

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{total_assets:,}</div><div class="kpi-lbl">Total Cargo Documents</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{num_clusters}</div><div class="kpi-lbl">Organic Clusters</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-val">{avg_docs_per_cluster:,}</div><div class="kpi-lbl">Avg Docs / Cluster</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="kpi-card"><div class="kpi-val" style="color:#10B981;">$0.00</div><div class="kpi-lbl">LLM Token Spend</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown('<div class="kpi-card"><div class="kpi-val" style="color:#3B82F6;">Active</div><div class="kpi-lbl">Vertex AI Search (10k Free)</div></div>', unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------------------------------

st.sidebar.header("🔍 Organic Discovery Filters")
st.sidebar.info("🧭 **Deck Rib & Manuscript View**:\nTo browse the 140 Section Ribs and Bronze+ prose linked to these clusters, run:\n`uv run streamlit run src/react_agent/entrypoints/deck_rib_cargo_browser.py`")

# Build cluster options sorted by document count descending
cluster_counts = df["display_cluster"].value_counts()
cluster_options = ["All Clusters (All 3,666 Documents)"] + [
    f"{lbl} ({cluster_counts[lbl]} docs)" for lbl in cluster_counts.index
]

selected_cluster_option = st.sidebar.selectbox("Filter by Emergent Cluster", cluster_options)
search_filter = st.sidebar.text_input("Filter Titles, Publishers, or Keywords", "")

filtered_df = df.copy()

if selected_cluster_option != "All Clusters (All 3,666 Documents)":
    # Extract the label from the selection string
    target_label = selected_cluster_option.rsplit(" (", 1)[0]
    filtered_df = filtered_df[filtered_df["display_cluster"] == target_label]

if search_filter.strip():
    q = search_filter.strip().lower()
    filtered_df = filtered_df[
        filtered_df["title"].fillna("").str.lower().str.contains(q) |
        filtered_df["publisher"].fillna("").str.lower().str.contains(q) |
        filtered_df["keywords_str"].fillna("").str.lower().str.contains(q)
    ]

st.sidebar.markdown(f"**Filtered Subset:** {len(filtered_df):,} / {total_assets:,} assets")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Clustering Pipeline Specs:**
- **Algorithm:** TF-IDF + TruncatedSVD(100) + Spherical Hybrid KMeans(100) + PCA(2)
- **Hybrid Structure:** 50 Pure Atomic Seeds + 50 Emergent k-means++ Slots
- **Spherical Geometry:** L2 Unit Hypersphere Normalization (Cosine Metric)
- **Rule Compliance:** SHARED-HEURISTIC-022 (Zero-Compound Atomic Taxonomy)
- **Execution Cost:** $0.00 (Zero API calls)
- **Database Schema:** `cargo.fleet_enrichments` (`enrichment_type = 'cluster'`)
""")

# ---------------------------------------------------------------------------
# Tabs Architecture
# ---------------------------------------------------------------------------

tab_galaxy, tab_treemap, tab_search, tab_table = st.tabs([
    "🌌 2D Topic Galaxy (Spatial Map)",
    "📊 Organic Cluster Breakdown",
    "🔍 Vertex AI Sub-Second Search",
    "📋 Filtered Cargo Ledger"
])

# ---------------------------------------------------------------------------
# TAB 1: 2D Topic Galaxy (Interactive Spatial Scatter Map)
# ---------------------------------------------------------------------------
with tab_galaxy:
    st.subheader("🌌 2D Topic Galaxy: Mathematical Document Landscape")
    st.caption("Every point represents an empirical document projected from 50-dimensional semantic space down to 2D coordinates via PCA. Documents close to each other share vocabulary and conceptual lineages.")

    # Format hover text for Plotly
    plot_df = filtered_df.copy()
    plot_df["Hover_Title"] = plot_df["title"].apply(lambda t: str(t)[:90] + ("..." if len(str(t)) > 90 else ""))
    plot_df["Hover_Publisher"] = plot_df["publisher"].fillna("Unknown")
    plot_df["Hover_Date"] = plot_df["publication_date"].fillna("N/A")

    fig_galaxy = px.scatter(
        plot_df,
        x="coord_x",
        y="coord_y",
        color="cluster_label",
        hover_name="Hover_Title",
        hover_data={
            "coord_x": False,
            "coord_y": False,
            "cluster_label": True,
            "Hover_Publisher": True,
            "Hover_Date": True,
            "keywords_str": True
        },
        labels={
            "cluster_label": "Cluster",
            "Hover_Publisher": "Publisher",
            "Hover_Date": "Date",
            "keywords_str": "Centroid Keywords"
        },
        height=750,
        color_discrete_sequence=(
            px.colors.qualitative.Vivid +
            px.colors.qualitative.Alphabet +
            px.colors.qualitative.Light24 +
            px.colors.qualitative.Bold +
            px.colors.qualitative.Prism +
            px.colors.qualitative.Safe
        )
    )

    fig_galaxy.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC", family="Arial, sans-serif"),
        xaxis=dict(showgrid=True, gridcolor="#1E293B", zeroline=False, title="Principal Axis 1 (X)"),
        yaxis=dict(showgrid=True, gridcolor="#1E293B", zeroline=False, title="Principal Axis 2 (Y)"),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            bgcolor="#1E293B",
            bordercolor="#475569",
            borderwidth=1.5,
            font=dict(color="#FFFFFF", size=11),
            title=dict(text="<b>Cluster Key (Click to isolate or toggle)</b>", font=dict(color="#38BDF8", size=12)),
            itemsizing="constant"
        ),
        margin=dict(l=20, r=20, t=20, b=260)
    )
    fig_galaxy.update_traces(marker=dict(size=7, opacity=0.88, line=dict(width=0.5, color="#FFFFFF")))

    st.plotly_chart(fig_galaxy, use_container_width=True)

# ---------------------------------------------------------------------------
# TAB 2: Organic Cluster Treemap & Volume Breakdown
# ---------------------------------------------------------------------------
with tab_treemap:
    st.subheader("📊 Organic Cluster Volume Distribution")
    st.caption("Distribution of external cargo documents across discovered clusters. Treemap area is proportional to the number of acquired documents.")

    col_tm, col_bar = st.columns([1, 1])

    with col_tm:
        st.write("##### Cluster Area Treemap")
        treemap_summary = df.groupby(["cluster_id", "cluster_label"]).size().reset_index(name="doc_count")
        treemap_summary["Label"] = treemap_summary.apply(lambda r: f"Cluster {r['cluster_id']}: {r['cluster_label']}", axis=1)

        fig_tm = px.treemap(
            treemap_summary,
            path=["Label"],
            values="doc_count",
            height=500,
            color="doc_count",
            color_continuous_scale="Blues"
        )
        fig_tm.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig_tm, use_container_width=True)

    with col_bar:
        st.write("##### Document Count by Cluster")
        bar_df = treemap_summary.sort_values("doc_count", ascending=True)
        fig_bar = px.bar(
            bar_df,
            x="doc_count",
            y="Label",
            orientation="h",
            height=500,
            labels={"doc_count": "Document Count", "Label": "Cluster"},
            color="doc_count",
            color_continuous_scale="Viridis"
        )
        fig_bar.update_layout(margin=dict(t=10, l=10, r=10, b=10), showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.write("#### 📋 Cluster Forensic Breakdown & Centroid Keywords")

    cluster_table_rows = []
    clusters_info = cluster_meta.get("clusters", [])
    
    for c in sorted(clusters_info, key=lambda x: x["doc_count"], reverse=True):
        cid = c["cluster_id"]
        c_docs = df[df["cluster_id"] == cid]
        sample_titles = "; ".join(c_docs["title"].dropna().head(3).tolist())
        pct = (c["doc_count"] / total_assets) * 100
        cluster_table_rows.append({
            "Cluster ID": cid,
            "Cluster Name": c["cluster_label"],
            "Document Count": c["doc_count"],
            "% of Cargo Hold": f"{pct:.1f}%",
            "Top Centroid Keywords": ", ".join(c.get("top_keywords", [])),
            "Representative Sample Titles": sample_titles
        })

    st.dataframe(pd.DataFrame(cluster_table_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# TAB 3: Live Vertex AI Sub-Second Search Portal
# ---------------------------------------------------------------------------
with tab_search:
    st.subheader("🔍 Sub-Second Micro Searchlight (Vertex AI Search)")
    st.caption("Executes dense hybrid semantic + BM25 keyword search directly across ~4,000 raw text documents in gs://npt-fleet-cargo-hold/acquisitions/*.txt.")

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        search_query = st.text_input(
            "Enter hybrid semantic search query:",
            placeholder="e.g. Constellation Energy nuclear restart, copyright fair use lawsuits, deepseek reasoning",
            key="vertex_search_input"
        )
    with col_btn:
        st.write("")
        st.write("")
        run_search = st.button("🚀 Search Hold", type="primary")

    # Quick suggestion chips
    st.markdown("**Suggested Quick Inquiries:**")
    sq1, sq2, sq3, sq4 = st.columns(4)
    suggested_q = None
    if sq1.button("⚛️ Nuclear Power & AI"):
        suggested_q = "Constellation Energy nuclear restart Three Mile Island data center power"
    if sq2.button("⚖️ Copyright & Fair Use"):
        suggested_q = "New York Times OpenAI copyright fair use training data lawsuit"
    if sq3.button("🤖 Autonomous Agents"):
        suggested_q = "autonomous AI agents rogue execution computer use"
    if sq4.button("🧠 DeepSeek & Reasoning"):
        suggested_q = "DeepSeek R1 reasoning model distillation open weights"

    query_to_run = suggested_q or (search_query.strip() if run_search else None)

    if query_to_run:
        with st.spinner(f"Querying Vertex AI Search (`npt-cargo-search-app`) for '{query_to_run}'..."):
            results = execute_vertex_search(query_to_run, page_size=10)

        if not results:
            st.info("No matching documents found in Vertex AI Search.")
        else:
            st.success(f"Retrieved {len(results)} relevant documents from GCS!")
            for idx, res in enumerate(results, 1):
                doc = res.get("document", {})
                struct_data = doc.get("derivedStructData", {})
                doc_uri = struct_data.get("link", doc.get("name", "N/A"))
                title = struct_data.get("title") or doc_uri.split("/")[-1].replace(".txt", "")
                snippets = struct_data.get("snippets", [])
                
                gcs_web_url = make_gcs_console_url(doc_uri)

                with st.expander(f"#{idx} | {title}", expanded=(idx == 1)):
                    st.markdown(f"**GCS Storage Blob:** [{doc_uri}]({gcs_web_url})")
                    if snippets:
                        st.markdown("**Extractive Snippets:**")
                        for snip in snippets:
                            clean_snip = snip.get("snippet", "").replace("<b>", "**").replace("</b>", "**")
                            st.markdown(f"> {clean_snip}")
                    else:
                        st.write("No snippet returned.")

# ---------------------------------------------------------------------------
# TAB 4: Filtered Cargo Ledger (With Clickable Hyperlinks)
# ---------------------------------------------------------------------------
with tab_table:
    st.subheader("📋 Empirical Cargo Ledger")
    st.caption(f"Displaying {len(filtered_df):,} matching assets with assigned cluster identities and clickable GCS / Source hyperlinks.")

    table_df = filtered_df.copy()
    table_df["gcs_console_url"] = table_df["gcp_bucket_path"].apply(make_gcs_console_url)

    display_cols = [
        "metadata_id", "title", "display_cluster", "publisher",
        "publication_date", "keywords_str", "gcs_console_url", "source_url"
    ]
    table_view = table_df[[c for c in display_cols if c in table_df.columns]].copy()

    st.dataframe(
        table_view,
        column_config={
            "metadata_id": st.column_config.NumberColumn("ID", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "display_cluster": st.column_config.TextColumn("Emergent Cluster", width="medium"),
            "publisher": st.column_config.TextColumn("Publisher", width="medium"),
            "publication_date": st.column_config.TextColumn("Date", width="small"),
            "keywords_str": st.column_config.TextColumn("Cluster Keywords", width="medium"),
            "gcs_console_url": st.column_config.LinkColumn("GCS Blob", display_text="Open in GCS"),
            "source_url": st.column_config.LinkColumn("Source URL", display_text="Visit Source")
        },
        use_container_width=True,
        hide_index=True
    )
