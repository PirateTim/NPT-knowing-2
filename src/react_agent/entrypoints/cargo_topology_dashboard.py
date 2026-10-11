"""
NPT Fleet: Cargo Topology, Multi-Chapter Bridges & Topic Clustering Dashboard
Entrypoint: src/react_agent/entrypoints/cargo_topology_dashboard.py
Run command: uv run streamlit run src/react_agent/entrypoints/cargo_topology_dashboard.py
"""

import os
import sys
import glob
import json
import urllib.parse
from collections import defaultdict, Counter
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pg8000.dbapi
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans

# Ensure repository root is on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

load_dotenv(override=True)

st.set_page_config(
    page_title="NPT Fleet: Cargo Topology Dashboard",
    page_icon="🗺️",
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
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #2563EB;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .kpi-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
    }
    .kpi-lbl {
        font-size: 0.8rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .badge-orphan {
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-multi {
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
</style>
""", unsafe_allow_html=True)

from src.react_agent.tools.cloud_knowledge_tools import read_knowledge_artifact

@st.cache_data(show_spinner="Streaming full text from hold...", ttl=3600)
def fetch_cargo_full_text(bucket_path: str) -> str:
    if not bucket_path:
        return "No storage path recorded in cargo.content_metadata."
    return read_knowledge_artifact(bucket_path)


@st.cache_data(ttl=3600, show_spinner="Loading Cargo Hold & Chapter Census data...")
def load_all_data():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        st.error("CONTENT_DATABASE_URL is not set.")
        st.stop()

    url = urllib.parse.urlparse(conn_string)
    conn = pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
        ssl_context=True
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, abstract, source_url, gcp_bucket_path
        FROM cargo.content_metadata
        ORDER BY id ASC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    cargo_dict = {}
    for r in rows:
        cid, title, abstract, source_url, bucket_path = r
        parsed_domain = urllib.parse.urlparse(source_url).netloc.replace("www.", "") if source_url else "unknown"
        cargo_dict[cid] = {
            "id": cid,
            "title": title or "Untitled",
            "abstract": abstract or "",
            "source_url": source_url or "",
            "gcp_bucket_path": bucket_path or "",
            "domain": parsed_domain or "unknown"
        }

    # Load 12 Census Result Files
    census_files = sorted(glob.glob("ship/bronze_plus/chapters/ch*/ch*_census_results.json"))
    chapters_metadata = {}
    cargo_links = defaultdict(list)

    for fpath in census_files:
        with open(fpath, "r", encoding="utf-8") as fp:
            cdata = json.load(fp)
        
        ch_num = cdata.get("chapter_number")
        if ch_num == 0 or ch_num is None:
            continue
        
        chapters_metadata[ch_num] = {
            "chapter_number": ch_num,
            "chapter_title": cdata.get("chapter_title", f"Chapter {ch_num}"),
            "criteria": cdata.get("criteria_used", {}),
            "total_matches": cdata.get("total_matches", len(cdata.get("matches", [])))
        }

        for m in cdata.get("matches", []):
            cid = m.get("id")
            if cid in cargo_dict:
                cargo_links[cid].append({
                    "chapter_number": ch_num,
                    "chapter_title": chapters_metadata[ch_num]["chapter_title"],
                    "sail_locker": m.get("sail_locker", "MAINSAIL"),
                    "rib": m.get("rib", "General"),
                    "rationale": m.get("rationale", "")
                })

    # Build master dataframe and compute extended fleet categories
    df_rows = []
    texts_for_embedding = []
    
    jib_keywords = ["altman", "sext", "erotica", "erotic", "porn", "musk", "thiel", "tilly", "norwood", "zuckerberg", "hollywood", "entertainment", "larry summers"]
    surv_keywords = ["flock", "camera", "alpr", "license plate", "meta glass", "ray-ban", "smart glass", "waymo", "robotaxi", "driverless", "drone"]
    labor_keywords = ["jobpocalypse", "layoff", "unemployment", "hiring", "worker", "labor", "career", "job", "entry-level", "graduate"]
    doomer_keywords = ["doomer", "existential risk", "extinction", "superintelligence", "agi", "yudkowsky", "safety letter", "prohibition"]
    tech_keywords = ["arxiv", "benchmark", "parameter", "agentic", "inference", "fine-tuning", "rag", "evals"]

    for cid, cinfo in cargo_dict.items():
        links = cargo_links.get(cid, [])
        ch_list = [l["chapter_number"] for l in links]
        lockers = list(set(l["sail_locker"] for l in links))
        
        full_text = ((cinfo["title"] or "") + " " + (cinfo["abstract"] or "")).lower()
        texts_for_embedding.append(full_text)

        # Extended Category Mapping
        if len(links) >= 2:
            cat = "🌉 Multi-Chapter Keystone"
        elif len(links) == 1:
            cat = f"📘 Chapter {links[0]['chapter_number']} Evidence"
        elif any(k in full_text for k in jib_keywords):
            cat = "🟡 The Jib: CEO Spectacle & Culture"
        elif any(k in full_text for k in surv_keywords):
            cat = "🔴 Surveillance & Physical Liability"
        elif any(k in full_text for k in labor_keywords):
            cat = "🟠 The Jobpocalypse & Labor"
        elif any(k in full_text for k in doomer_keywords):
            cat = "🟢 AI Doomerism & Superintelligence"
        elif cinfo["domain"] in ["threads.net", "youtube.com", "youtu.be", "reddit.com", "twitter.com", "x.com"]:
            cat = "🟣 Raw Social Witness & Feeds"
        elif cinfo["domain"] == "arxiv.org" or any(k in full_text for k in tech_keywords):
            cat = "⚪ Technical ML & Preprints"
        else:
            cat = "⚪ Ambient Industry Flotsam"

        df_rows.append({
            "id": cid,
            "title": cinfo["title"],
            "abstract": cinfo["abstract"],
            "domain": cinfo["domain"],
            "source_url": cinfo["source_url"],
            "gcp_bucket_path": cinfo["gcp_bucket_path"],
            "chapter_count": len(links),
            "chapters": sorted(ch_list),
            "chapters_str": ", ".join(f"Ch {c}" for c in sorted(ch_list)) if ch_list else "None (Orphan)",
            "sail_lockers": ", ".join(lockers) if lockers else "None",
            "is_orphan": len(links) == 0,
            "is_multi": len(links) >= 2,
            "category": cat,
            "links": links
        })

    # Compute 2D SVD coordinates for the literal map
    tfidf = TfidfVectorizer(max_features=1200, stop_words="english", ngram_range=(1, 2))
    X_mat = tfidf.fit_transform(texts_for_embedding)
    from sklearn.decomposition import TruncatedSVD
    svd = TruncatedSVD(n_components=2, random_state=42)
    coords = svd.fit_transform(X_mat)
    for idx, r in enumerate(df_rows):
        r["x"] = float(coords[idx, 0])
        r["y"] = float(coords[idx, 1])

    df = pd.DataFrame(df_rows)
    return df, cargo_dict, chapters_metadata, cargo_links


df, cargo_dict, chapters_metadata, cargo_links = load_all_data()

# PERSISTENT TOPIC CLUSTERS STORAGE
CLUSTERS_FILE = os.path.join("writings", "cargo_clusters.json")
def load_saved_clusters():
    if os.path.exists(CLUSTERS_FILE):
        try:
            with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cluster_definition(cluster_name, doc_ids, description=""):
    os.makedirs("writings", exist_ok=True)
    clusters = load_saved_clusters()
    clusters[cluster_name] = {
        "cluster_name": cluster_name,
        "description": description,
        "doc_ids": doc_ids,
        "count": len(doc_ids)
    }
    with open(CLUSTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2)


# HEADER & MASTER KPIS
st.markdown('<div class="main-title">🗺️ NPT Fleet: Cargo Topology & Topic Galaxy</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">100% Census Complete across Chapters 1–12 (3,667 Master Hold Assets) | Multi-Chapter Bridges & Topic Clusters</div>', unsafe_allow_html=True)

total_cargo = len(df)
connected_cargo = len(df[~df["is_orphan"]])
orphan_cargo = len(df[df["is_orphan"]])
multi_cargo = len(df[df["is_multi"]])
max_conn = int(df["chapter_count"].max())

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Total Cargo Hold</div><div class="kpi-val">{total_cargo:,}</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Connected Assets</div><div class="kpi-val">{connected_cargo:,} <span style="font-size:0.9rem; color:#16A34A;">({connected_cargo/total_cargo*100:.1f}%)</span></div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card" style="border-left-color:#DC2626;"><div class="kpi-lbl">Unconnected / Orphans</div><div class="kpi-val">{orphan_cargo:,} <span style="font-size:0.9rem; color:#DC2626;">({orphan_cargo/total_cargo*100:.1f}%)</span></div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card" style="border-left-color:#9333EA;"><div class="kpi-lbl">Multi-Chapter Bridges</div><div class="kpi-val">{multi_cargo:,} <span style="font-size:0.9rem; color:#9333EA;">({multi_cargo/total_cargo*100:.1f}%)</span></div></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="kpi-card" style="border-left-color:#F59E0B;"><div class="kpi-lbl">Max Degree / Keystone</div><div class="kpi-val">{max_conn} Chapters</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# TABS NAVIGATION
tab_galaxy, tab_overview, tab_orphans, tab_bridges, tab_clustering, tab_chapters = st.tabs([
    "🌌 The 2D Cargo Galaxy Map (Literal Topology)",
    "🌐 Topology & Connectivity",
    "🏝️ Unconnected Cargo (Orphans)",
    "🌉 Multi-Chapter Bridges (Keystones)",
    "🔮 Topic Clusters & Event Discovery",
    "📚 Chapter & Rib Matrix"
])

# ==============================================================================
# TAB 0: THE 2D CARGO GALAXY MAP (LITERAL SPATIAL MAP)
# ==============================================================================
with tab_galaxy:
    st.subheader("🌌 The Literal Topology: 2D Cargo Galaxy Map")
    st.markdown(
        "Every single one of the **3,667 cargo hold items** projected onto a continuous 2D semantic plane. "
        "Notice the dense continents of **Manuscript Evidence** & **Multi-Chapter Bridges**, surrounded by the emergent archipelagos of "
        "**The Jib (CEO drama / erotica walkbacks)**, **Surveillance Hardware (Flock / Meta glasses / Waymo)**, **The Jobpocalypse**, and **AI Doomerism**."
    )

    g_col1, g_col2 = st.columns([3, 1])
    with g_col1:
        map_search = st.text_input("🔍 Highlight in Galaxy (Search Title, Abstract, or Domain):", placeholder="e.g. flock, altman, tilly, waymo, lay-off, ray-ban...")
    with g_col2:
        all_cats = sorted(df["category"].unique())
        sel_cats = st.multiselect("Filter Macro-Sectors:", all_cats, default=all_cats)

    plot_df = df[df["category"].isin(sel_cats)].copy()
    if map_search:
        ms = map_search.lower()
        plot_df["is_highlighted"] = plot_df.apply(
            lambda r: ms in (r["title"] + " " + r["abstract"] + " " + r["domain"]).lower(),
            axis=1
        )
        # Sort so highlighted are plotted on top
        plot_df = plot_df.sort_values(by="is_highlighted", ascending=True)

    fig_map = px.scatter(
        plot_df,
        x="x",
        y="y",
        color="category",
        hover_name="title",
        hover_data={
            "id": True,
            "domain": True,
            "chapters_str": True,
            "category": True,
            "x": False,
            "y": False
        },
        opacity=0.8,
        color_discrete_map={
            "🌉 Multi-Chapter Keystone": "#7C3AED",
            "🟡 The Jib: CEO Spectacle & Culture": "#EAB308",
            "🔴 Surveillance & Physical Liability": "#EF4444",
            "🟠 The Jobpocalypse & Labor": "#F97316",
            "🟢 AI Doomerism & Superintelligence": "#10B981",
            "🟣 Raw Social Witness & Feeds": "#EC4899",
            "⚪ Technical ML & Preprints": "#64748B",
            "⚪ Ambient Industry Flotsam": "#94A3B8"
        }
    )
    fig_map.update_traces(marker=dict(size=7, line=dict(width=0.5, color="white")))
    fig_map.update_layout(
        height=680,
        margin=dict(t=10, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=True, zeroline=False, showticklabels=False, title=""),
        yaxis=dict(showgrid=True, zeroline=False, showticklabels=False, title="")
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown(f"**Showing {len(plot_df):,} plotted cargo nodes in active filter:**")
    st.dataframe(
        plot_df[["id", "title", "category", "domain", "chapters_str"]].head(50),
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "category": st.column_config.TextColumn("Macro-Sector", width="medium"),
            "domain": st.column_config.TextColumn("Domain", width="small"),
            "chapters_str": st.column_config.TextColumn("Chapters", width="medium")
        },
        hide_index=True,
        use_container_width=True
    )


# ==============================================================================
# TAB 1: TOPOLOGY & CONNECTIVITY
# ==============================================================================
with tab_overview:
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Distribution of Chapter Connectivity")
        st.caption("How many chapters does each cargo item connect to?")
        deg_counts = df["chapter_count"].value_counts().sort_index().reset_index()
        deg_counts.columns = ["Chapters Connected", "Asset Count"]
        deg_counts["Percentage"] = (deg_counts["Asset Count"] / total_cargo * 100).round(1).astype(str) + "%"
        
        fig_deg = px.bar(
            deg_counts,
            x="Chapters Connected",
            y="Asset Count",
            text="Asset Count",
            color="Chapters Connected",
            color_continuous_scale="Viridis",
            labels={"Chapters Connected": "Number of Connected Chapters", "Asset Count": "Total Assets"}
        )
        fig_deg.update_traces(textposition="outside")
        fig_deg.update_layout(showlegend=False, height=380, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_deg, use_container_width=True)

    with col_b:
        st.subheader("Cargo Volume by Chapter (Total Matches)")
        st.caption("Matches per chapter across the 12 calibrated chapters")
        ch_vols = []
        for ch_num, meta in sorted(chapters_metadata.items()):
            ch_vols.append({
                "Chapter": f"Ch {ch_num:02d}",
                "Title": meta["chapter_title"][:35] + ("..." if len(meta["chapter_title"]) > 35 else ""),
                "Matches": meta["total_matches"]
            })
        df_ch_vols = pd.DataFrame(ch_vols)
        
        fig_ch = px.bar(
            df_ch_vols,
            x="Chapter",
            y="Matches",
            text="Matches",
            hover_data=["Title"],
            color="Matches",
            color_continuous_scale="Blues"
        )
        fig_ch.update_traces(textposition="outside")
        fig_ch.update_layout(showlegend=False, height=380, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_ch, use_container_width=True)

    # Chapter Co-occurrence Matrix
    st.subheader("Chapter Co-Occurrence Topology Matrix")
    st.caption("Number of cargo assets shared across any two chapters (showing cross-chapter epistemic entanglement)")
    
    matrix = np.zeros((13, 13), dtype=int)
    for _, row in df.iterrows():
        chs = row["chapters"]
        if len(chs) > 1:
            for i in range(len(chs)):
                for j in range(len(chs)):
                    if i != j:
                        matrix[chs[i]][chs[j]] += 1
    
    co_df = pd.DataFrame(matrix[1:13, 1:13], 
                         index=[f"Ch {c}" for c in range(1, 13)], 
                         columns=[f"Ch {c}" for c in range(1, 13)])
    
    fig_mat = px.imshow(
        co_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="YlGnBu",
        labels=dict(x="Chapter", y="Chapter", color="Shared Assets")
    )
    fig_mat.update_layout(height=480, margin=dict(t=30, b=30, l=30, r=30))
    st.plotly_chart(fig_mat, use_container_width=True)


# ==============================================================================
# TAB 2: UNCONNECTED CARGO (ORPHANS)
# ==============================================================================
with tab_orphans:
    st.subheader("🏝️ The Unanchored Hold: Content That Connects to Nothing")
    st.markdown(
        f"There are **{orphan_cargo:,} assets ({orphan_cargo/total_cargo*100:.1f}%)** in the hold that did not trigger any section rib across Chapters 1–12. "
        "These represent external cargo that sits outside the book's current thesis backbones—raw material for new clusters, subplots, or future manuscript extensions."
    )

    df_orphans = df[df["is_orphan"]].copy()

    col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
    with col_o1:
        search_orphan = st.text_input("🔍 Search Unanchored Cargo (Title, Abstract, or URL):", placeholder="e.g. adult, gaming, biotech, crypto...")
    with col_o2:
        top_domains = df_orphans["domain"].value_counts().head(20).index.tolist()
        sel_domain = st.selectbox("Filter by Source Domain:", ["All Domains"] + top_domains)
    with col_o3:
        sort_by = st.selectbox("Sort By:", ["ID (Ascending)", "ID (Descending)", "Title (A-Z)"])

    filtered_orphans = df_orphans
    if search_orphan:
        q = search_orphan.lower()
        filtered_orphans = filtered_orphans[
            filtered_orphans["title"].str.lower().str.contains(q) |
            filtered_orphans["abstract"].str.lower().str.contains(q) |
            filtered_orphans["source_url"].str.lower().str.contains(q)
        ]
    if sel_domain != "All Domains":
        filtered_orphans = filtered_orphans[filtered_orphans["domain"] == sel_domain]

    if sort_by == "ID (Descending)":
        filtered_orphans = filtered_orphans.sort_values(by="id", ascending=False)
    elif sort_by == "Title (A-Z)":
        filtered_orphans = filtered_orphans.sort_values(by="title", ascending=True)
    else:
        filtered_orphans = filtered_orphans.sort_values(by="id", ascending=True)

    st.markdown(f"**Showing {len(filtered_orphans):,} unanchored items:**")

    for _, item in filtered_orphans.head(50).iterrows():
        with st.expander(f"[{item['id']}] {item['title']}  •  ({item['domain']})"):
            st.markdown(f"**Source URL:** [{item['source_url']}]({item['source_url']})")
            st.markdown(f"**GCS Storage Path:** `{item['gcp_bucket_path']}`")
            if st.button(f"📖 Read Full Verbatim Text [{item['id']}]", key=f"btn_orphan_{item['id']}"):
                with st.spinner(f"Streaming full verbatim text for cargo [{item['id']}] from hold..."):
                    full_txt = fetch_cargo_full_text(item['gcp_bucket_path'])
                    st.text_area("Full Verbatim Text", full_txt, height=350)


# ==============================================================================
# TAB 3: MULTI-CHAPTER BRIDGES (KEYSTONES)
# ==============================================================================
with tab_bridges:
    st.subheader("🌉 Multi-Chapter Bridges: Epistemic Keystones")
    st.markdown(
        f"There are **{multi_cargo:,} assets ({multi_cargo/total_cargo*100:.1f}%)** connecting to 2 or more chapters simultaneously. "
        "These are the most potent forensic assets in the hold: documents that prove systemic convergence across multiple institutional sectors."
    )

    df_multi = df[df["is_multi"]].copy()

    col_b1, col_b2, col_b3 = st.columns([1, 1, 2])
    with col_b1:
        min_chapters = st.slider("Minimum Chapter Degree:", min_value=2, max_value=max_conn, value=3)
    with col_b2:
        filter_ch = st.selectbox("Must Include Chapter:", ["Any Chapter"] + [f"Chapter {c}" for c in range(1, 13)])
    with col_b3:
        search_multi = st.text_input("🔍 Search Bridge Assets:", placeholder="e.g. copyright, Google, FTC, energy...")

    filtered_multi = df_multi[df_multi["chapter_count"] >= min_chapters]
    if filter_ch != "Any Chapter":
        target_ch = int(filter_ch.split()[1])
        filtered_multi = filtered_multi[filtered_multi["chapters"].apply(lambda chs: target_ch in chs)]
    if search_multi:
        q = search_multi.lower()
        filtered_multi = filtered_multi[
            filtered_multi["title"].str.lower().str.contains(q) |
            filtered_multi["source_url"].str.lower().str.contains(q)
        ]

    filtered_multi = filtered_multi.sort_values(by="chapter_count", ascending=False)
    st.markdown(f"**Displaying {len(filtered_multi):,} keystone assets connecting to {min_chapters}+ chapters:**")

    for _, row in filtered_multi.head(30).iterrows():
        ch_badges = " ".join([f"`Ch {c}`" for c in row['chapters']])
        with st.expander(f"⭐ [{row['id']}] {row['title']} — Connected to {row['chapter_count']} Chapters ({ch_badges})"):
            st.markdown(f"**Source URL:** [{row['source_url']}]({row['source_url']})")
            st.markdown(f"**GCS Storage Path:** `{row['gcp_bucket_path']}`")
            if st.button(f"📖 Read Full Verbatim Text [{row['id']}]", key=f"btn_bridge_{row['id']}"):
                with st.spinner(f"Streaming full verbatim text for cargo [{row['id']}] from hold..."):
                    full_txt = fetch_cargo_full_text(row['gcp_bucket_path'])
                    st.text_area("Full Verbatim Text", full_txt, height=350)
            
            st.markdown("#### Chapter Forensic Evidence & Rationales:")
            for l in row["links"]:
                st.markdown(f"- **Chapter {l['chapter_number']}** ({l['chapter_title']})  |  **Rib:** `{l['rib']}`  |  **Locker:** `{l['sail_locker']}`")
                st.caption(f"↳ *Bilgeladle Rationale:* {l['rationale']}")


# ==============================================================================
# TAB 4: TOPIC CLUSTERING & EVENT DISCOVERY
# ==============================================================================
with tab_clustering:
    st.subheader("🔮 Topic Galaxy: Organic Event Discovery & Custom Clusters")
    st.markdown(
        "Explore organic clusters across the hold, discover un-modeled cultural events, "
        "or create and persist named topic clusters for pegleg and down-stream agents."
    )

    cluster_mode = st.radio("Clustering Mode:", [
        "🌟 Spotlight Event Clusters (Curated Events)",
        "🔎 Custom Keyword / Regex Cluster Builder",
        "🤖 Unsupervised TF-IDF Galaxy (Automatic)"
    ], horizontal=True)

    # --------------------------------------------------------------------------
    # SUBMODE 1: SPOTLIGHT EVENT CLUSTERS
    # --------------------------------------------------------------------------
    if cluster_mode == "🌟 Spotlight Event Clusters (Curated Events)":
        st.markdown("### Curated Micro-History Clusters")
        
        spotlight = st.selectbox("Select Spotlight Cultural / Tech Event:", [
            "🔥 The OpenAI Erotica / Adult Entertainment Pivot & Walkback",
            "🏭 The People Who Hate Data Centers & Punditry Bandwagon (Jennifer Rubin / NYT / Local Revolts)",
            "⚡ DeepSeek-V3 & The Open-Weight Commodity Shock",
            "🛡️ CrowdStrike / Microsoft Azure Infrastructure Collapse",
            "⚛️ Nuclear Renaissance: Tech Giants Buying Reactor Fleets for AI",
            "🎭 The Scarlett Johansson / OpenAI Voice Clone Scandal"
        ])

        if spotlight.startswith("🔥"):
            st.info(
                "**Context:** In late 2024 / early 2025, Sam Altman and OpenAI publicly floated allowing 'erotica for verified adults' "
                "in ChatGPT, sparking massive backlash from regulators and competitors (Microsoft AI chief distancing), "
                "followed by executive walkbacks and board scrutiny."
            )
            # Find relevant items
            keywords = ["adult", "erotica", "erotic", "porn", "sext", "moral police", "entertainment"]
            mask = df.apply(
                lambda r: ("openai" in (r["title"] + r["abstract"]).lower() or "chatgpt" in (r["title"] + r["abstract"]).lower() or "altman" in (r["title"] + r["abstract"]).lower())
                and any(kw in (r["title"] + r["abstract"]).lower() for kw in keywords),
                axis=1
            )
            spotlight_df = df[mask].copy()

        elif spotlight.startswith("🏭"):
            st.info(
                "**Context:** A rising media trend and grassroots backlash against hyperscale AI data centers. "
                "Includes prestige punditry jumping on the bandwagon (Jennifer Rubin's 'Undaunted' column [#2470], NYT's 'Americans Hate Data Centers'), "
                "local city council voter bloodbaths, Michigan farm towns fighting OpenAI/Oracle, and water/electricity price shocks."
            )
            dc_keywords = ["hate", "fight", "revolt", "protest", "oppose", "villain", "handout", "water", "electricity", "cost", "town", "council", "tax", "close to their homes", "utility", "bloodbath", "rubin", "undaunted", "rebrand", "wastewater"]
            mask = df.apply(
                lambda r: r["id"] == 2470 or (
                    ("data center" in (r["title"] + " " + r["abstract"]).lower() or "datacenter" in (r["title"] + " " + r["abstract"]).lower())
                    and any(kw in (r["title"] + " " + r["abstract"]).lower() for kw in dc_keywords)
                ),
                axis=1
            )
            spotlight_df = df[mask].copy()

        elif spotlight.startswith("⚡"):
            st.info("**Context:** DeepSeek's open-weight release challenging Silicon Valley's capex assumptions.")
            mask = df["title"].str.lower().str.contains("deepseek") | df["abstract"].str.lower().str.contains("deepseek")
            spotlight_df = df[mask].copy()

        elif spotlight.startswith("🛡️"):
            st.info("**Context:** The July 2024 CrowdStrike faulty kernel driver update taking down 8.5M Windows systems.")
            mask = df["title"].str.lower().str.contains("crowdstrike") | df["abstract"].str.lower().str.contains("crowdstrike")
            spotlight_df = df[mask].copy()

        elif spotlight.startswith("⚛️"):
            st.info("**Context:** Big Tech (Microsoft/Three Mile Island, Amazon/Talen, Google/Kairos) purchasing nuclear capacity.")
            keywords = ["nuclear", "reactor", "three mile island", "smr", "constellation"]
            mask = df.apply(lambda r: any(kw in (r["title"] + r["abstract"]).lower() for kw in keywords), axis=1)
            spotlight_df = df[mask].copy()

        else: # Scarlett Johansson
            st.info("**Context:** OpenAI copying Scarlett Johansson's voice ('Sky') after she declined their licensing offer.")
            keywords = ["scarlett", "johansson", "sky voice", "her"]
            mask = df.apply(lambda r: any(kw in (r["title"] + r["abstract"]).lower() for kw in keywords), axis=1)
            spotlight_df = df[mask].copy()

        c1, c2, c3 = st.columns([1, 1, 2])
        c1.metric("Assets in Cluster", f"{len(spotlight_df):,}")
        c2.metric("Unconnected (Orphans)", f"{len(spotlight_df[spotlight_df['is_orphan']]):,}")
        c3.metric("Multi-Chapter Bridges", f"{len(spotlight_df[spotlight_df['is_multi']]):,}")

        st.dataframe(
            spotlight_df[["id", "title", "domain", "chapter_count", "chapters_str"]],
            column_config={
                "id": st.column_config.NumberColumn("Cargo ID", width="small"),
                "title": st.column_config.TextColumn("Title", width="large"),
                "domain": st.column_config.TextColumn("Domain", width="medium"),
                "chapter_count": st.column_config.NumberColumn("Chapters", width="small"),
                "chapters_str": st.column_config.TextColumn("Assigned Chapters", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )

        with st.expander("💾 Persist this Spotlight Cluster to Writings"):
            save_name = st.text_input("Cluster Name:", value=spotlight.split(" ")[1])
            save_desc = st.text_area("Description:", value=f"Curated cluster of {len(spotlight_df)} assets.")
            if st.button("Save Cluster to writings/cargo_clusters.json"):
                save_cluster_definition(save_name, spotlight_df["id"].tolist(), save_desc)
                st.success(f"Saved cluster '{save_name}' with {len(spotlight_df)} items to writings/cargo_clusters.json!")

    # --------------------------------------------------------------------------
    # SUBMODE 2: CUSTOM KEYWORD / REGEX BUILDER
    # --------------------------------------------------------------------------
    elif cluster_mode == "🔎 Custom Keyword / Regex Cluster Builder":
        st.markdown("### Build a Custom Topic Cluster")
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            custom_query = st.text_input("Enter keywords (comma separated or space separated):", placeholder="e.g. copyright, fair use, new york times")
        with col_c2:
            scope = st.selectbox("Search Scope:", ["All Cargo (3,667)", "Unconnected Only (2,022)", "Connected Only (1,645)"])

        if custom_query:
            terms = [t.strip().lower() for t in custom_query.replace(",", " ").split() if t.strip()]
            
            target_df = df
            if scope == "Unconnected Only (2,022)":
                target_df = df[df["is_orphan"]]
            elif scope == "Connected Only (1,645)":
                target_df = df[~df["is_orphan"]]

            matched = target_df[target_df.apply(
                lambda r: all(t in (r["title"] + " " + r["abstract"]).lower() for t in terms),
                axis=1
            )]

            st.write(f"Found **{len(matched)}** assets matching `{custom_query}`:")
            st.dataframe(
                matched[["id", "title", "domain", "chapter_count", "chapters_str"]],
                hide_index=True,
                use_container_width=True
            )

            col_s1, col_s2 = st.columns([2, 1])
            with col_s1:
                new_cname = st.text_input("Save As Named Cluster:", placeholder="e.g. NYT_Copyright_Lawsuit")
            with col_s2:
                st.write("")
                st.write("")
                if st.button("💾 Save Cluster to Disk") and new_cname:
                    save_cluster_definition(new_cname, matched["id"].tolist(), f"Query: {custom_query}")
                    st.success(f"Cluster '{new_cname}' saved with {len(matched)} items!")

    # --------------------------------------------------------------------------
    # SUBMODE 3: UNSUPERVISED TF-IDF GALAXY
    # --------------------------------------------------------------------------
    else:
        st.markdown("### Unsupervised TF-IDF Clustering")
        st.caption("Mathematical clustering of documents based on textual vocabulary in titles and abstracts")
        
        num_clusters = st.slider("Number of Topic Clusters (k):", min_value=5, max_value=25, value=10)
        
        with st.spinner("Extracting TF-IDF features and computing clusters..."):
            texts = (df["title"] + " " + df["abstract"]).fillna("")
            tfidf = TfidfVectorizer(max_features=1000, stop_words="english", ngram_range=(1, 2))
            X = tfidf.fit_transform(texts)
            
            kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42, batch_size=256)
            cluster_labels = kmeans.fit_predict(X)
            df_clustered = df.copy()
            df_clustered["cluster"] = cluster_labels

            # Get top keywords per cluster
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            terms = tfidf.get_feature_names_out()
            cluster_keywords = {}
            for i in range(num_clusters):
                top_terms = [terms[ind] for ind in order_centroids[i, :5]]
                cluster_keywords[i] = ", ".join(top_terms)

        cluster_summary = []
        for i in range(num_clusters):
            c_items = df_clustered[df_clustered["cluster"] == i]
            cluster_summary.append({
                "Cluster ID": f"Cluster {i}",
                "Top Keywords": cluster_keywords[i],
                "Total Assets": len(c_items),
                "Unconnected (Orphans)": len(c_items[c_items["is_orphan"]]),
                "Multi-Chapter Bridges": len(c_items[c_items["is_multi"]])
            })
        
        st.dataframe(pd.DataFrame(cluster_summary), hide_index=True, use_container_width=True)

        selected_cl = st.selectbox("Inspect Cluster Details:", [f"Cluster {i}: {cluster_keywords[i]}" for i in range(num_clusters)])
        cl_idx = int(selected_cl.split(":")[0].split()[1])
        st.dataframe(
            df_clustered[df_clustered["cluster"] == cl_idx][["id", "title", "domain", "chapters_str"]],
            hide_index=True,
            use_container_width=True
        )


# ==============================================================================
# TAB 5: CHAPTER & RIB MATRIX
# ==============================================================================
with tab_chapters:
    st.subheader("📚 Chapter Forensic Matrix & Section Rib Inspector")
    st.caption("Deep inspection into individual chapter backbones and their associated cargo")

    sel_ch = st.selectbox("Select Chapter to Inspect:", [f"Chapter {c}: {chapters_metadata[c]['chapter_title']}" for c in range(1, 13)])
    c_num = int(sel_ch.split(":")[0].split()[1])
    c_meta = chapters_metadata[c_num]

    st.markdown(f"### {c_meta['chapter_title']}")
    st.info(f"**Mast Intent:** {c_meta['criteria'].get('mast_intent', 'N/A')}\n\n**Vector of Destruction:** {c_meta['criteria'].get('vector_of_destruction', 'N/A')}")

    # Rib Breakdown
    ch_matches = []
    for cid, links in cargo_links.items():
        for l in links:
            if l["chapter_number"] == c_num:
                ch_matches.append({
                    "id": cid,
                    "title": cargo_dict[cid]["title"],
                    "domain": cargo_dict[cid]["domain"],
                    "rib": l["rib"],
                    "sail_locker": l["sail_locker"],
                    "rationale": l["rationale"]
                })
    
    df_ch_matches = pd.DataFrame(ch_matches)
    if not df_ch_matches.empty:
        rib_counts = df_ch_matches["rib"].value_counts().reset_index()
        rib_counts.columns = ["Rib", "Assets"]
        
        c_r1, c_r2 = st.columns([1, 1])
        with c_r1:
            st.markdown("#### Rib Distribution")
            fig_rib = px.bar(rib_counts, x="Rib", y="Assets", text="Assets", color="Assets", color_continuous_scale="Purples")
            fig_rib.update_traces(textposition="outside")
            fig_rib.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_rib, use_container_width=True)

        with c_r2:
            st.markdown("#### Sail Locker Distribution")
            locker_counts = df_ch_matches["sail_locker"].value_counts().reset_index()
            locker_counts.columns = ["Locker", "Assets"]
            fig_lock = px.pie(locker_counts, names="Locker", values="Assets", hole=0.4, color="Locker",
                              color_discrete_map={"MAINSAIL": "#2563EB", "BILGE": "#DC2626", "JIB": "#F59E0B"})
            fig_lock.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_lock, use_container_width=True)

        st.markdown(f"#### Matching Cargo Documents ({len(df_ch_matches)} Assets)")
        st.dataframe(
            df_ch_matches[["id", "title", "rib", "sail_locker", "rationale"]],
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "title": st.column_config.TextColumn("Title", width="medium"),
                "rib": st.column_config.TextColumn("Section Rib", width="small"),
                "sail_locker": st.column_config.TextColumn("Locker", width="small"),
                "rationale": st.column_config.TextColumn("Forensic Rationale", width="large")
            },
            hide_index=True,
            use_container_width=True
        )
