"""
NPT Fleet: Epistemic Graph Visualizer & Review Console

How to run:
    uv run streamlit run helper_scripts/graph_visualizer_console.py

What it does:
    Interactive Streamlit console for inspecting, traversing, and searching the manuscript epistemic knowledge graph.

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
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv(override=True)

PORT = 8765

def get_db_connection():
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string:
        return None
    url = urllib.parse.urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:]
    )

def fetch_graph_data(chapter_filter=None, node_type_filter=None):
    """Fetches nodes and edges from PostgreSQL for visualization."""
    conn = get_db_connection()
    if not conn:
        return {"nodes": [], "edges": []}
    
    cursor = conn.cursor()
    
    # Query nodes
    query_nodes = """
        SELECT n.node_id, n.node_type, n.label, n.description, n.chapter_anchor, n.properties,
               m.title AS cargo_title, m.source_url AS cargo_url, m.gcp_bucket_path AS cargo_bucket,
               m.publication_date AS cargo_date, m.abstract AS cargo_abstract,
               l.chunk_text AS manuscript_text, l.lexical_envelope AS manuscript_envelope
        FROM cargo.ontology_nodes n
        LEFT JOIN cargo.content_metadata m ON n.metadata_id = m.id
        LEFT JOIN ship.letters_of_marque l ON REPLACE(n.node_id, 'chunk:', '') = l.chunk_id
    """
    cursor.execute(query_nodes)
    raw_nodes = cursor.fetchall()
    
    nodes = []
    for row in raw_nodes:
        nid, ntype, label, desc, chap, props, c_title, c_url, c_bucket, c_date, c_abstract, m_text, m_env = row
        
        # Color coding by type
        color_map = {
            "CONCEPT": {"background": "#1e3a8a", "border": "#3b82f6", "highlight": "#60a5fa"}, # Deep Blue
            "MANUSCRIPT_CHUNK": {"background": "#581c87", "border": "#a855f7", "highlight": "#c084fc"}, # Purple
            "CARGO": {"background": "#064e3b", "border": "#10b981", "highlight": "#34d399"}, # Emerald Green
            "CHAPTER": {"background": "#78350f", "border": "#f59e0b", "highlight": "#fbbf24"}, # Amber
            "VIGNETTE": {"background": "#374151", "border": "#9ca3af", "highlight": "#d1d5db"} # Slate Gray
        }
        
        # Shape by type
        shape_map = {
            "CONCEPT": "diamond",
            "MANUSCRIPT_CHUNK": "box",
            "CARGO": "ellipse",
            "CHAPTER": "hexagon",
            "VIGNETTE": "dot"
        }
        
        style = color_map.get(ntype, {"background": "#374151", "border": "#6b7280", "highlight": "#9ca3af"})
        shape = shape_map.get(ntype, "ellipse")
        
        # Multi-line plain text rollover without HTML tags
        title_lines = [str(label or nid), f"Type: {ntype}", f"ID: {nid}"]
        if chap:
            title_lines.append(f"Chapter: {chap}")
        title_text = "\n".join(title_lines)

        node_obj = {
            "id": nid,
            "label": label or nid,
            "title": title_text,
            "group": ntype,
            "shape": shape,
            "color": style,
            "font": {"color": "#ffffff", "size": 13, "face": "system-ui, sans-serif"},
            "raw_data": {
                "node_id": nid,
                "node_type": ntype,
                "label": label,
                "description": desc,
                "chapter_anchor": chap,
                "properties": props or {},
                "cargo_title": c_title,
                "cargo_url": c_url,
                "cargo_bucket": c_bucket,
                "cargo_date": c_date,
                "cargo_abstract": c_abstract,
                "manuscript_text": m_text,
                "manuscript_envelope": m_env or {}
            }
        }
        nodes.append(node_obj)
        
    # Query edges
    query_edges = """
        SELECT edge_id, source_node_id, predicate, target_node_id, weight, context, properties
        FROM cargo.ontology_edges
    """
    cursor.execute(query_edges)
    raw_edges = cursor.fetchall()
    
    edges = []
    for edge_id, src, pred, tgt, wt, ctx, props in raw_edges:
        color = "#94a3b8"
        if pred == "instantiates":
            color = "#38bdf8"
        elif pred == "evidentiary_receipt_for":
            color = "#34d399"
        elif pred == "amplifies":
            color = "#f43f5e"
        elif pred == "anchors_to_chapter":
            color = "#fbbf24"
            
        edge_obj = {
            "id": f"edge_{edge_id}",
            "from": src,
            "to": tgt,
            "label": pred,
            "arrows": "to",
            "color": {"color": color, "highlight": "#f8fafc"},
            "width": max(1.5, float(wt or 1.0) * 2.5),
            "font": {"color": "#cbd5e1", "size": 11, "align": "middle", "strokeWidth": 2, "strokeColor": "#0f172a"},
            "raw_data": {
                "edge_id": edge_id,
                "source": src,
                "predicate": pred,
                "target": tgt,
                "weight": float(wt or 1.0),
                "context": ctx,
                "properties": props or {}
            }
        }
        edges.append(edge_obj)
        
    cursor.close()
    conn.close()
    return {"nodes": nodes, "edges": edges}

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>NPT Fleet Epistemic Graph Console</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #e2e8f0; display: flex; height: 100vh; overflow: hidden; }
    #sidebar { width: 440px; background: #111827; border-left: 1px solid #1f2937; display: flex; flex-direction: column; overflow: hidden; z-index: 10; box-shadow: -4px 0 20px rgba(0,0,0,0.5); }
    #main-panel { flex: 1; display: flex; flex-direction: column; position: relative; }
    #toolbar { min-height: 56px; background: #0f172a; border-bottom: 1px solid #1e293b; display: flex; align-items: center; justify-content: space-between; padding: 8px 18px; z-index: 5; flex-wrap: wrap; gap: 10px; }
    #network-container { flex: 1; height: 100%; width: 100%; background: #090d16; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .badge-concept { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
    .badge-chunk { background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }
    .badge-cargo { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
    .sidebar-header { padding: 18px 20px; border-bottom: 1px solid #1f2937; background: #131d2e; }
    .sidebar-content { flex: 1; overflow-y: auto; padding: 20px; }
    .card { background: #1a2234; border: 1px solid #2d3748; border-radius: 8px; padding: 14px; margin-bottom: 14px; }
    .card-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px; letter-spacing: 0.05em; }
    .card-body { font-size: 13px; line-height: 1.5; color: #f1f5f9; }
    .quote-box { background: #0f172a; border-left: 3px solid #8b5cf6; padding: 10px 12px; margin: 8px 0; font-size: 12px; font-style: italic; color: #cbd5e1; border-radius: 0 4px 4px 0; }
    .hook-prop { margin-bottom: 10px; }
    .hook-label { font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase; margin-bottom: 2px; }
    .hook-val { font-size: 12.5px; color: #e2e8f0; line-height: 1.4; }
    
    .control-group { display: flex; align-items: center; gap: 6px; }
    .group-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-right: 2px; }
    .pill-btn { background: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 4px 10px; border-radius: 9999px; font-size: 11.5px; font-weight: 600; cursor: pointer; transition: all 0.15s ease; display: inline-flex; align-items: center; gap: 5px; user-select: none; }
    .pill-btn:hover { background: #334155; color: #f8fafc; }
    .pill-btn.active { background: #2563eb; color: #ffffff; border-color: #60a5fa; box-shadow: 0 0 8px rgba(37, 99, 235, 0.4); }
    .pill-btn.active.type-chunk { background: #581c87; border-color: #a855f7; box-shadow: 0 0 8px rgba(168, 85, 247, 0.4); }
    .pill-btn.active.type-concept { background: #1e3a8a; border-color: #3b82f6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.4); }
    .pill-btn.active.type-cargo { background: #064e3b; border-color: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
    .pill-btn.active.type-other { background: #78350f; border-color: #f59e0b; box-shadow: 0 0 8px rgba(245, 158, 11, 0.4); }
    .divider { width: 1px; height: 22px; background: #334155; margin: 0 4px; }
    .legend-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    div.vis-tooltip {
      max-width: 320px !important;
      white-space: pre-wrap !important;
      word-break: break-word !important;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
      font-size: 12px !important;
      line-height: 1.45 !important;
      background: #0f172a !important;
      color: #e2e8f0 !important;
      border: 1px solid #334155 !important;
      border-radius: 6px !important;
      padding: 8px 12px !important;
      box-shadow: 0 4px 16px rgba(0,0,0,0.6) !important;
      z-index: 9999 !important;
    }
  </style>
</head>
<body>

  <div id="main-panel">
    <div id="toolbar">
      <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <h2 style="font-size: 15px; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; white-space: nowrap;">NPT Graph Explorer</h2>
        
        <div class="divider"></div>

        <!-- Section Multi-Select -->
        <div class="control-group">
          <span class="group-label">Sections:</span>
          <button class="pill-btn active" id="sec-81" onclick="toggleSection('8.1')">8.1</button>
          <button class="pill-btn active" id="sec-82" onclick="toggleSection('8.2')">8.2</button>
          <button class="pill-btn active" id="sec-83" onclick="toggleSection('8.3')">8.3</button>
          <button class="pill-btn active" id="sec-84" onclick="toggleSection('8.4')">8.4</button>
          <button class="pill-btn" id="sec-other" onclick="toggleSection('other')">Other</button>
          <button class="pill-btn" id="sec-all" onclick="toggleAllSections()">All</button>
        </div>

        <div class="divider"></div>

        <!-- Node Type Multi-Select -->
        <div class="control-group">
          <span class="group-label">Types:</span>
          <button class="pill-btn active type-chunk" id="type-chunk" onclick="toggleType('MANUSCRIPT_CHUNK')">
            <span class="legend-dot" style="background: #a855f7;"></span> Manuscript
          </button>
          <button class="pill-btn active type-concept" id="type-concept" onclick="toggleType('CONCEPT')">
            <span class="legend-dot" style="background: #3b82f6;"></span> Concept
          </button>
          <button class="pill-btn active type-cargo" id="type-cargo" onclick="toggleType('CARGO')">
            <span class="legend-dot" style="background: #10b981;"></span> Cargo
          </button>
          <button class="pill-btn type-other" id="type-other" onclick="toggleType('OTHER')">
            <span class="legend-dot" style="background: #f59e0b;"></span> Ch/Vignette
          </button>
        </div>
      </div>

      <div style="display: flex; align-items: center; gap: 10px;">
        <span id="stats-badge" style="font-size: 11px; color: #94a3b8; font-weight: 600; padding: 4px 8px; background: #1e293b; border-radius: 6px;">Loading...</span>
        <button class="pill-btn" onclick="resetPhysics()">Stabilize</button>
      </div>
    </div>
    <div id="network-container"></div>
  </div>

  <div id="sidebar">
    <div class="sidebar-header">
      <div id="inspector-badge" style="margin-bottom: 6px;"></div>
      <h3 id="inspector-title" style="font-size: 17px; font-weight: 700; color: #f8fafc; line-height: 1.3;">Select a Node or Edge</h3>
    </div>
    <div class="sidebar-content" id="inspector-content">
      <div style="text-align: center; color: #64748b; margin-top: 60px;">
        <svg style="width: 48px; height: 48px; margin-bottom: 12px; stroke: #475569;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <p style="font-size: 14px;">Click on any node or edge in the graph to inspect its epistemic anatomy, verbatim source text, or causal properties.</p>
      </div>
    </div>
  </div>

  <script>
    let network = null;
    let graphData = null;
    let nodeToSectionsMap = null;
    let currentFilteredNodes = [];
    let currentFilteredEdges = [];

    // Multi-select state:
    // Sections: '8.1', '8.2', '8.3', '8.4', 'other'
    let selectedSections = new Set(['8.1', '8.2', '8.3', '8.4', 'other']);
    // Types: 'MANUSCRIPT_CHUNK', 'CONCEPT', 'CARGO', 'OTHER'
    let selectedTypes = new Set(['MANUSCRIPT_CHUNK', 'CONCEPT', 'CARGO', 'OTHER']);

    function computeNodeSections(allNodes, allEdges) {
      const map = new Map();
      // 1. Tag chunks directly by section number
      allNodes.forEach(n => {
        if (n.group === 'MANUSCRIPT_CHUNK' || (n.raw_data && n.raw_data.node_type === 'MANUSCRIPT_CHUNK')) {
          const match = n.id.match(/sec(\d+\.\d+)/);
          const sec = match ? match[1] : (n.raw_data && n.raw_data.properties && n.raw_data.properties.section_number ? String(n.raw_data.properties.section_number) : 'other');
          map.set(n.id, new Set([sec]));
        }
      });

      // 2. Propagate to adjacent nodes (2 hops)
      for (let hop = 0; hop < 2; hop++) {
        allEdges.forEach(e => {
          const fromSecs = map.get(e.from);
          const toSecs = map.get(e.to);
          if (fromSecs) {
            if (!map.has(e.to)) map.set(e.to, new Set());
            fromSecs.forEach(s => map.get(e.to).add(s));
          }
          if (toSecs) {
            if (!map.has(e.from)) map.set(e.from, new Set());
            toSecs.forEach(s => map.get(e.from).add(s));
          }
        });
      }

      // 3. Untagged nodes belong to 'other'
      allNodes.forEach(n => {
        if (!map.has(n.id) || map.get(n.id).size === 0) {
          map.set(n.id, new Set(['other']));
        }
      });
      return map;
    }

    function toggleSection(sec) {
      if (selectedSections.has(sec)) {
        selectedSections.delete(sec);
      } else {
        selectedSections.add(sec);
      }
      renderGraph();
    }

    function toggleAllSections() {
      const allList = ['8.1', '8.2', '8.3', '8.4', 'other'];
      if (allList.every(s => selectedSections.has(s))) {
        selectedSections.clear();
        selectedSections.add('8.1');
        selectedSections.add('8.2');
        selectedSections.add('8.3');
        selectedSections.add('8.4');
      } else {
        selectedSections = new Set(allList);
      }
      renderGraph();
    }

    function toggleType(typeKey) {
      if (selectedTypes.has(typeKey)) {
        selectedTypes.delete(typeKey);
      } else {
        selectedTypes.add(typeKey);
      }
      renderGraph();
    }

    function updateButtonUI() {
      document.getElementById('sec-81')?.classList.toggle('active', selectedSections.has('8.1'));
      document.getElementById('sec-82')?.classList.toggle('active', selectedSections.has('8.2'));
      document.getElementById('sec-83')?.classList.toggle('active', selectedSections.has('8.3'));
      document.getElementById('sec-84')?.classList.toggle('active', selectedSections.has('8.4'));
      document.getElementById('sec-other')?.classList.toggle('active', selectedSections.has('other'));
      const isAll = ['8.1', '8.2', '8.3', '8.4', 'other'].every(s => selectedSections.has(s));
      document.getElementById('sec-all')?.classList.toggle('active', isAll);

      document.getElementById('type-chunk')?.classList.toggle('active', selectedTypes.has('MANUSCRIPT_CHUNK'));
      document.getElementById('type-concept')?.classList.toggle('active', selectedTypes.has('CONCEPT'));
      document.getElementById('type-cargo')?.classList.toggle('active', selectedTypes.has('CARGO'));
      document.getElementById('type-other')?.classList.toggle('active', selectedTypes.has('OTHER'));
    }

    async function loadDataAndInit() {
      try {
        const res = await fetch('/api/graph');
        graphData = await res.json();
        nodeToSectionsMap = computeNodeSections(graphData.nodes, graphData.edges);
        renderGraph();
      } catch (err) {
        console.error("Failed to load graph data:", err);
      }
    }

    function renderGraph() {
      updateButtonUI();
      if (!graphData) return;

      // Filter nodes
      currentFilteredNodes = graphData.nodes.filter(n => {
        // Type filter
        const group = n.group;
        let typeMatches = false;
        if (group === 'MANUSCRIPT_CHUNK' && selectedTypes.has('MANUSCRIPT_CHUNK')) typeMatches = true;
        else if (group === 'CONCEPT' && selectedTypes.has('CONCEPT')) typeMatches = true;
        else if (group === 'CARGO' && selectedTypes.has('CARGO')) typeMatches = true;
        else if ((group === 'CHAPTER' || group === 'VIGNETTE' || !['MANUSCRIPT_CHUNK','CONCEPT','CARGO'].includes(group)) && selectedTypes.has('OTHER')) typeMatches = true;
        if (!typeMatches) return false;

        // Section filter
        const nodeSecs = nodeToSectionsMap.get(n.id) || new Set(['other']);
        return [...nodeSecs].some(s => selectedSections.has(s));
      });

      const visibleNodeIds = new Set(currentFilteredNodes.map(n => n.id));
      currentFilteredEdges = graphData.edges.filter(e => visibleNodeIds.has(e.from) && visibleNodeIds.has(e.to));

      // Update badge
      const badge = document.getElementById('stats-badge');
      if (badge) {
        badge.innerText = `${currentFilteredNodes.length} nodes | ${currentFilteredEdges.length} edges`;
      }

      const container = document.getElementById('network-container');
      const data = {
        nodes: new vis.DataSet(currentFilteredNodes),
        edges: new vis.DataSet(currentFilteredEdges)
      };

      const options = {
        physics: {
          solver: 'forceAtlas2Based',
          forceAtlas2Based: {
            gravitationalConstant: -110,
            centralGravity: 0.015,
            springLength: 150,
            springConstant: 0.08
          },
          maxVelocity: 45,
          minVelocity: 0.1,
          stabilization: { iterations: 120 }
        },
        interaction: {
          hover: true,
          tooltipDelay: 100,
          zoomView: true
        },
        nodes: {
          borderWidth: 2,
          shadow: true
        },
        edges: {
          smooth: { type: 'continuous' }
        }
      };

      if (!network) {
        network = new vis.Network(container, data, options);
        network.on("click", function (params) {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = currentFilteredNodes.find(n => n.id === nodeId);
            inspectNode(node);
          } else if (params.edges.length > 0) {
            const edgeId = params.edges[0];
            const edge = currentFilteredEdges.find(e => e.id === edgeId);
            inspectEdge(edge);
          }
        });
      } else {
        network.setData(data);
      }
    }

    function inspectNode(node) {
      if (!node) return;
      const d = node.raw_data;
      const headerTitle = document.getElementById('inspector-title');
      const headerBadge = document.getElementById('inspector-badge');
      const content = document.getElementById('inspector-content');

      headerTitle.innerText = d.label || d.node_id;
      
      let badgeHtml = '';
      if (d.node_type === 'CONCEPT') badgeHtml = '<span class="badge badge-concept">CONCEPT INVARIANT</span>';
      else if (d.node_type === 'MANUSCRIPT_CHUNK') badgeHtml = '<span class="badge badge-chunk">LETTER OF MARQUE (CHUNK)</span>';
      else if (d.node_type === 'CARGO') badgeHtml = '<span class="badge badge-cargo">EXTERNAL CARGO RECEIPT</span>';
      else badgeHtml = `<span class="badge">${d.node_type}</span>`;
      headerBadge.innerHTML = badgeHtml;

      let html = '';

      // Node ID Card
      html += `
        <div class="card">
          <div class="card-title">Node ID & Anchor</div>
          <div class="card-body"><code>${d.node_id}</code> (Chapter ${d.chapter_anchor || 'N/A'})</div>
        </div>
      `;

      if (d.description) {
        html += `
          <div class="card">
            <div class="card-title">Thesis Definition</div>
            <div class="card-body">${d.description}</div>
          </div>
        `;
      }

      // If CONCEPT, render Hook 5-Part Causal Anatomy
      if (d.node_type === 'CONCEPT' && d.properties) {
        const p = d.properties;
        html += `
          <div class="card" style="border-color: #3b82f6;">
            <div class="card-title" style="color: #60a5fa;">Hook 5-Part Causal Anatomy</div>
            
            <div class="hook-prop">
              <div class="hook-label">1. Epistemic Invariant</div>
              <div class="hook-val">${p.epistemic_invariant || 'N/A'}</div>
            </div>

            <div class="hook-prop">
              <div class="hook-label">2. Non-Reified Actor Class</div>
              <div class="hook-val" style="color: #fca5a5;">${p.actor_class || 'N/A'}</div>
            </div>

            <div class="hook-prop">
              <div class="hook-label">3. Active Behavioral Qualifier</div>
              <div class="hook-val">${p.behavioral_qualifier || 'N/A'}</div>
            </div>

            <div class="hook-prop">
              <div class="hook-label">4. Exculpatory Alibi (Pretext)</div>
              <div class="hook-val" style="color: #fde047;">${p.exculpatory_alibi || 'N/A'}</div>
            </div>

            <div class="hook-prop">
              <div class="hook-label">5. Epistemic Harm</div>
              <div class="hook-val" style="color: #fdba74;">${p.epistemic_harm || 'N/A'}</div>
            </div>
          </div>
        `;
      }

      // If MANUSCRIPT CHUNK, render Chunk Text and Envelope
      if (d.node_type === 'MANUSCRIPT_CHUNK') {
        if (d.manuscript_text) {
          html += `
            <div class="card">
              <div class="card-title">Verbatim Manuscript Chunk</div>
              <div class="quote-box">${d.manuscript_text}</div>
            </div>
          `;
        }
        if (d.manuscript_envelope && d.manuscript_envelope.search_query) {
          html += `
            <div class="card" style="border-color: #a855f7;">
              <div class="card-title" style="color: #c084fc;">Discovery Search Net (Boolean)</div>
              <div class="card-body"><code style="font-size: 11px; word-break: break-all;">${d.manuscript_envelope.search_query}</code></div>
            </div>
          `;
        }
      }

      // If CARGO, render Metadata details
      if (d.node_type === 'CARGO') {
        const rawBucket = d.cargo_bucket || (d.properties && d.properties.url && d.properties.url.includes('acquisitions/') ? d.properties.url : '');
        let cleanPath = rawBucket.replace(/^gs:\/\//, '').replace(/^npt-fleet-cargo-hold\//, '');
        const gcsUrl = cleanPath ? `https://storage.cloud.google.com/npt-fleet-cargo-hold/${cleanPath}` : '';

        html += `
          <div class="card" style="border-color: #10b981;">
            <div class="card-title" style="color: #34d399;">Cargo Provenance & Receipt</div>
            <div class="card-body">
              <div style="font-weight: 600; margin-bottom: 6px;">${d.cargo_title || 'N/A'}</div>
              <div style="font-size: 12px; color: #94a3b8; margin-bottom: 6px;">Date: ${d.cargo_date || 'N/A'}</div>
              
              <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px;">
                ${d.cargo_url ? `<div><a href="${d.cargo_url}" target="_blank" rel="noopener noreferrer" style="color: #38bdf8; text-decoration: underline; font-size: 12.5px;">View Original Web Source ↗</a></div>` : ''}
                ${gcsUrl ? `<div><a href="${gcsUrl}" target="_blank" rel="noopener noreferrer" style="color: #34d399; font-weight: 600; text-decoration: underline; font-size: 12.5px;">Open In Cloud Storage (GCS) ↗</a></div>` : ''}
              </div>

              <div class="quote-box" style="border-color: #10b981;">${d.cargo_abstract || 'No abstract'}</div>
              
              <div style="font-size: 11px; color: #64748b; margin-top: 8px;">
                Bucket File: ${gcsUrl ? `<a href="${gcsUrl}" target="_blank" rel="noopener noreferrer" style="color: #10b981; text-decoration: underline;"><code>${d.cargo_bucket || cleanPath}</code> ↗</a>` : `<code>${d.cargo_bucket || 'N/A'}</code>`}
              </div>
            </div>
          </div>
        `;
      }

      content.innerHTML = html;
    }

    function inspectEdge(edge) {
      if (!edge) return;
      const d = edge.raw_data;
      const headerTitle = document.getElementById('inspector-title');
      const headerBadge = document.getElementById('inspector-badge');
      const content = document.getElementById('inspector-content');

      headerTitle.innerText = `${d.predicate}`;
      headerBadge.innerHTML = `<span class="badge" style="background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #0284c7;">ONTOLOGY EDGE (Weight: ${d.weight})</span>`;

      let html = `
        <div class="card">
          <div class="card-title">Edge Topology</div>
          <div class="card-body">
            <div style="margin-bottom: 4px;"><b>From:</b> <code>${d.source}</code></div>
            <div style="margin-bottom: 4px;"><b>Predicate:</b> <code>${d.predicate}</code></div>
            <div><b>To:</b> <code>${d.target}</code></div>
          </div>
        </div>

        <div class="card" style="border-color: #0284c7;">
          <div class="card-title" style="color: #38bdf8;">Forensic Causal Context</div>
          <div class="card-body" style="font-size: 13.5px; line-height: 1.5;">${d.context || 'No context recorded.'}</div>
        </div>
      `;

      if (d.properties && Object.keys(d.properties).length > 0) {
        html += `
          <div class="card">
            <div class="card-title">Edge Properties (JSONB)</div>
            <div class="card-body"><pre style="font-size: 11px; color: #cbd5e1; white-space: pre-wrap;">${JSON.stringify(d.properties, null, 2)}</pre></div>
          </div>
        `;
      }

      content.innerHTML = html;
    }

    function resetPhysics() {
      if (network) {
        network.fit();
      }
    }

    // Auto-load on page ready
    window.addEventListener('load', () => loadDataAndInit());
  </script>
</body>
</html>
"""

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class GraphRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            
        elif path == "/api/graph":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            data = fetch_graph_data()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            
        else:
            self.send_response(404)
            self.end_headers()

def export_standalone_html(output_path="writings/graph_viewer.html"):
    """Dumps a fully self-contained HTML file embedding current live DB data."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    data = fetch_graph_data()
    # Inject data directly into the script
    standalone_html = HTML_TEMPLATE.replace(
        "const res = await fetch('/api/graph');\n        graphData = await res.json();",
        f"graphData = {json.dumps(data)};"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(standalone_html)
    print(f"[GRAPH EXPORTER] Standalone viewer written to {output_path}")

def main():
    # 1. Export standalone HTML for offline/direct opening
    export_standalone_html()
    
    # 2. Launch HTTP server
    server = ThreadedHTTPServer(("127.0.0.1", PORT), GraphRequestHandler)
    print(f"\n==================================================================")
    print(f"  NPT FLEET EPISTEMIC GRAPH EXPLORER LIVE AT:")
    print(f"  http://localhost:{PORT}")
    print(f"  (Also exported standalone to writings/graph_viewer.html)")
    print(f"==================================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    main()
