"""
NPT Fleet Tools: Persistent Memory & Glossary Operations
Architecture: Split-Brain Storage (Local JSON Vaults vs. Global Postgres Schema)
"""

"""
It is completely understandable that this file caused some confusion. The architecture here relies on a "Split-Brain" memory model, and it is crucial that the documentation reflects this explicitly so Hook (and future human developers) understand the difference.
Here is the architectural breakdown:
Agent-Specific Memory (Local JSON): Things that make an agent unique (its personal rules, its specific examples, its unique worldview) are stored in local JSON files inside its specific directory. This keeps the agent "portable" and prevents its specific instructions from polluting the rest of the fleet.
Fleet-Wide Knowledge (PostgreSQL): Facts, definitions, and the project's official terminology are stored in the cargo.system_glossary database so that every agent has access to the exact same definitions.
Here is the heavily documented memory_tools.py file with the storage mechanisms explicitly defined in the docstrings. I did not change any of your executable code.
"""

import os
from urllib.parse import urlparse
import pg8000.dbapi
import json
import datetime

# =====================================================================
# INTERNAL HELPER FUNCTIONS (Not directly callable by Agents)
# =====================================================================

def _get_state_connection():
    """Internal Helper: Connects to the agent_state PostgreSQL schema."""
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

def _get_cargo_connection():
    """Internal Helper: Connects to the cargo PostgreSQL schema."""
    conn_string = os.getenv("CONTENT_DATABASE_URL")
    if not conn_string: return None
    url = urlparse(conn_string)
    return pg8000.dbapi.connect(
        user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
    )

#===================================================================
# SECTION 1: AGENT-SPECIFIC MEMORY (LOCAL JSON VAULTS)
#===================================================================

""" def record_learned_ontology_rule(agent_name: str, rule: str) -> str:
    #Saves a permanent behavioral rule to the database for future agent boots.
    conn = _get_state_connection()
    if not conn: return "[ERROR] State database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_state.ontology_rules (scope, directive) VALUES (%s, %s);",
            (agent_name.lower(), rule)
        )
        conn.commit()
        cursor.close()
        return f"[MEMORY COMMITTED] Rule permanently added to {agent_name.lower()}'s ontology."
    except Exception as e:
        return f"[ERROR] Failed to save rule: {str(e)}"
    finally:
        conn.close() """
        
def _load_valid_fleet_agents() -> list:
    """Internal Helper: Dynamically retrieves valid fleet agent names directly from fleet_roster.json (no hardcoding)."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    roster_path = os.path.join(base_dir, "core", "fleet_roster.json")
    if os.path.exists(roster_path):
        with open(roster_path, "r", encoding="utf-8") as rf:
            roster_data = json.load(rf).get("fleet_agents", {})
            return list(roster_data.keys())
    return []

def record_fleet_learning(agent_name: str, learning: str) -> str:
    """
    Agent Tool: Generalized Fleet Learning & Heuristic Recorder.
    Storage Mechanism: LOCAL AGENT JSON FILE (`learned_rules.json`).
    Purpose: Records a durable, generalized cognitive heuristic extracted from an operational incident
    or correction. Employs intelligent deduplication to update existing heuristics rather than creating bloat.
    Invoked By: HOOK, PEGLEG, CUTLASS, PLANK, BILGELADLE, GROG, SCALLYWAG, SPYGLASS.
    """
    return _record_learning_internal(agent_name, learning)

def record_learned_rule(agent_name: str, rule: str) -> str:
    """
    Agent Tool: Behavioral Heuristic Recorder (Backward-compatible alias for record_fleet_learning).
    """
    return _record_learning_internal(agent_name, rule)

def record_learned_ontology_rule(agent_name: str, rule: str) -> str:
    """
    Agent Tool: Behavioral Heuristic Recorder (Backward-compatible legacy alias).
    """
    return _record_learning_internal(agent_name, rule)

def _normalize_text_for_comparison(text: str) -> set:
    """Helper: Converts text into a set of lowercased alphanumeric keywords for semantic overlap check."""
    import re
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    stop_words = {"the", "a", "an", "and", "or", "to", "in", "of", "for", "with", "on", "at", "by", "from", "is", "must", "always", "never"}
    return {w for w in cleaned.split() if w and w not in stop_words}

def _calculate_similarity(words1: set, words2: set) -> float:
    """Calculates Jaccard similarity between two word sets."""
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union) if union else 0.0

def _record_learning_internal(agent_name: str, payload: str) -> str:
    """
    Core implementation for recording structured, generalized heuristics to local JSON vaults.
    Extracts underlying mechanisms, prevents duplicate bloat, and updates existing heuristics in-place.
    """
    agent_lower = agent_name.lower().strip()
    valid_agents = _load_valid_fleet_agents()
    if valid_agents and agent_lower not in valid_agents:
        return f"[MEMORY ERROR] Agent '{agent_name}' not found in fleet_roster.json. Dynamic roster agents: {valid_agents}"

    try:
        data_dict = {}
        if isinstance(payload, dict):
            data_dict = payload
        elif isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    data_dict = parsed
                else:
                    data_dict = {"generalized_heuristic": str(payload)}
            except Exception:
                data_dict = {"generalized_heuristic": str(payload)}

        # Parse generalized heuristic / directive
        heuristic = (
            data_dict.get("generalized_heuristic")
            or data_dict.get("heuristic")
            or data_dict.get("rule_directive")
            or data_dict.get("directive")
            or data_dict.get("description", "")
        ).strip()

        if not heuristic:
            return "[MEMORY ERROR] Cannot record learning: 'generalized_heuristic' must not be empty."

        category = (data_dict.get("category") or "Operational Protocol").strip()
        scope = (data_dict.get("scope") or f"{agent_lower.upper()}_LOCAL").strip()
        incident_ctx = (
            data_dict.get("incident_context")
            or data_dict.get("trigger")
            or data_dict.get("source_context")
            or data_dict.get("rationale", "Observed during active content operations.")
        ).strip()
        mechanism = (
            data_dict.get("underlying_mechanism")
            or data_dict.get("mechanism")
            or data_dict.get("source_context", "")
        ).strip()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_lower, "learned_rules.json"
        ))

        existing_entries = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_entries = json.load(f)
            except Exception:
                existing_entries = []

        new_id = data_dict.get("heuristic_id") or data_dict.get("learning_id") or data_dict.get("rule_id")
        
        # -------------------------------------------------------------
        # Deduplication & In-Place Update Logic
        # -------------------------------------------------------------
        new_words = _normalize_text_for_comparison(heuristic)
        matched_idx = None

        for idx, entry in enumerate(existing_entries):
            # Check ID match
            e_id = entry.get("heuristic_id") or entry.get("rule_id") or entry.get("learning_id")
            if new_id and e_id and new_id.lower().strip() == e_id.lower().strip():
                matched_idx = idx
                break

            # Check semantic word overlap in same category
            e_text = (
                entry.get("generalized_heuristic") 
                or entry.get("rule_directive") 
                or entry.get("directive", "")
            )
            e_words = _normalize_text_for_comparison(e_text)
            sim = _calculate_similarity(new_words, e_words)
            
            # If >60% word overlap in same category or exact prefix match
            if sim >= 0.60 or (len(heuristic) > 30 and heuristic[:40].lower() == e_text[:40].lower()):
                matched_idx = idx
                break

        if matched_idx is not None:
            # Update existing entry in-place
            target_entry = existing_entries[matched_idx]
            target_id = target_entry.get("heuristic_id") or target_entry.get("rule_id") or f"{agent_lower.upper()}-HEURISTIC-{matched_idx + 1:03d}"
            
            target_entry["heuristic_id"] = target_id
            target_entry["scope"] = scope
            target_entry["category"] = category
            target_entry["generalized_heuristic"] = heuristic
            target_entry["incident_context"] = incident_ctx
            target_entry["underlying_mechanism"] = mechanism or target_entry.get("underlying_mechanism", "")
            target_entry["last_updated_utc"] = timestamp
            
            # Clean up legacy key names if present
            target_entry.pop("rule_directive", None)
            target_entry.pop("source_context", None)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_entries, f, indent=2)

            return f"[MEMORY REFINED] Existing heuristic '{target_id}' ({category}) updated in-place for {agent_lower} to prevent duplication."
        else:
            # Create brand new heuristic entry
            if not new_id:
                new_id = f"{agent_lower.upper()}-HEURISTIC-{len(existing_entries) + 1:03d}"
            
            new_entry = {
                "heuristic_id": new_id,
                "scope": scope,
                "category": category,
                "generalized_heuristic": heuristic,
                "underlying_mechanism": mechanism,
                "incident_context": incident_ctx,
                "timestamp_utc": timestamp
            }
            existing_entries.append(new_entry)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_entries, f, indent=2)

            return f"[MEMORY COMMITTED] Generalized heuristic '{new_id}' ({category}) permanently recorded in {agent_lower}'s memory vault."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to record learning: {str(e)}"

def record_few_shot_exemplar(agent_name: str, user_input: str, model_response: str) -> str:
    """
    Agent Tool: Output Template Anchor.
    Storage Mechanism: LOCAL JSON FILE.
    Purpose: Appends a specific, perfected input/output example to the agent's 
    `few_shot_exemplars.json` file to rigidly structure its future formatting.
    Invoked By: CUTLASS, PLANK.
    """
    agent_lower = agent_name.lower().strip()
    valid_agents = _load_valid_fleet_agents()
    if valid_agents and agent_lower not in valid_agents:
        return f"[MEMORY ERROR] Agent '{agent_name}' not found in fleet_roster.json. Dynamic roster agents: {valid_agents}"

    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_lower, "few_shot_exemplars.json"
        ))

        exemplars = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    exemplars = json.load(f)
            except json.JSONDecodeError:
                exemplars = []

        exemplars.append({
            "input_context": user_input,
            "ideal_output": model_response,
            "rationale": "Auto-recorded via active terminal correction.",
            "timestamp": timestamp
        })

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(exemplars, f, indent=2)

        return "[MEMORY COMMITTED] Exact exemplar permanently appended to local JSON vault."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to write exemplar to JSON: {str(e)}"

def update_cognitive_lens(agent_name: str, lens_name: str, perspective: str) -> str:
    """
    Agent Tool: Philosophical Framework Injection.
    Storage Mechanism: LOCAL JSON FILE.
    Purpose: Appends a new philosophical perspective or analytical framework to the 
    agent's `cognitive_lens.json` file.
    Invoked By: CUTLASS.
    """
    agent_lower = agent_name.lower().strip()
    valid_agents = _load_valid_fleet_agents()
    if valid_agents and agent_lower not in valid_agents:
        return f"[MEMORY ERROR] Agent '{agent_name}' not found in fleet_roster.json. Dynamic roster agents: {valid_agents}"

    try:
        file_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "agents", agent_lower, "cognitive_lens.json"
        ))

        lens_data = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lens_data = json.load(f)
            except json.JSONDecodeError:
                lens_data = {}

        if "analytical_frameworks" not in lens_data:
            lens_data["analytical_frameworks"] = []

        lens_data["analytical_frameworks"].append({
            "lens_name": lens_name,
            "perspective": perspective
        })

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(lens_data, f, indent=2)

        return f"[COGNITIVE UPGRADE] '{lens_name}' permanently added to {agent_lower}'s analytical frameworks."
    except Exception as e:
        return f"[MEMORY ERROR] Failed to update cognitive lens: {str(e)}"

def reload_agent_memory_vault(agent_name: str) -> str:
    """
    Agent Tool: The Hot-Reload Trigger.
    Purpose: Notifies the system to refresh the target agent's memory vault on the next turn.
    Invoked By: CUTLASS, PLANK, PEGLEG.
    """
    agent_lower = agent_name.lower().strip()
    return f"[SYSTEM] Memory vault reload triggered for agent '{agent_lower}'. Next engine turn will compile updated JSON vaults."

#===================================================================
# SECTION 2: FLEET-WIDE KNOWLEDGE (POSTGRESQL GLOSSARY)
#===================================================================

def query_system_glossary() -> str:
    """
    Agent Tool: Global Dictionary Fetch.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Retrieves the shared, definitive list of terms and concepts for the project.
    Invoked By: BILGELADLE, PLANK (and automatically injected at startup by `plank_runner.py` and `bilgeladle_runner.py`).
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT term, definition FROM cargo.system_glossary;")
        rows = cursor.fetchall()
        cursor.close()
        if not rows: return "Glossary is currently empty."
        return "\n".join([f"- {row[0]}: {row[1]}" for row in rows])
    except Exception as e:
        return f"[ERROR] Failed to read glossary: {str(e)}"
    finally:
        conn.close()

def update_system_glossary(term: str, definition: str) -> str:
    """
    Agent Tool: Global Dictionary Definition.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Adds or updates a definitive project term in the shared database.
    Invoked By: BILGELADLE (Usually while executing the `bootstrap_ingestion` skill on manuscript drafts).
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Cargo database unavailable."
    try:
        cursor = conn.cursor()
        # Fallback query since the table was created without a unique constraint on 'term' initially
        cursor.execute("DELETE FROM cargo.system_glossary WHERE term = %s;", (term,))
        cursor.execute(
            "INSERT INTO cargo.system_glossary (term, definition, last_updated) VALUES (%s, %s, NOW());",
            (term, definition)
        )
        conn.commit()
        cursor.close()
        return f"[GLOSSARY UPDATED] {term} successfully defined."
    except Exception as e:
        return f"[ERROR] Failed to update glossary: {str(e)}"
    finally:
        conn.close()

def delete_system_glossary_term(term: str) -> str:
    """
    Agent Tool: Global Dictionary Deletion.
    Storage Mechanism: POSTGRESQL DATABASE (`cargo.system_glossary`).
    Purpose: Permanently removes a redundant or obsolete term from the shared database.
    Invoked By: BILGELADLE.
    """
    conn = _get_cargo_connection()
    if not conn: return "[ERROR] Database unavailable."
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cargo.system_glossary WHERE term = %s", (term,))
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        
        if deleted_count > 0:
            return f"[SUCCESS] Term '{term}' permanently deleted from the glossary."
        return f"[NOTICE] Term '{term}' was not found in the glossary."
    except Exception as e:
        return f"[ERROR] Failed to delete term: {str(e)}"
    finally:
        conn.close()

def conduct_learned_rules_audit() -> str:
    """
    Agent Tool: Multi-Agent Learned Rules Survey & Decision Audit Engine.
    Purpose: Dispatches an agentic survey to all subagents loaded dynamically from fleet_roster.json,
    compiles a formal timestamped decision document at agent_audits/learned_rules_audit_{timestamp}.md,
    and promotes approved universal rules to shared_fleet_rules.json.
    Invoked By: PEGLEG.
    """
    import os, json, datetime
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. Load agents dynamically from fleet_roster.json (no hardcoding)
    roster_path = os.path.join(base_dir, "core", "fleet_roster.json")
    agents = []
    if os.path.exists(roster_path):
        with open(roster_path, "r", encoding="utf-8") as rf:
            agents = list(json.load(rf).get("fleet_agents", {}).keys())
    if not agents:
        agents = ["bilgeladle", "plank", "cutlass", "spyglass", "scallywag", "grog"]

    survey_results = {}
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for agent in agents:
        rule_path = os.path.join(base_dir, "agents", agent, "learned_rules.json")
        rules = []
        if os.path.exists(rule_path):
            try:
                with open(rule_path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
            except Exception as e:
                raise RuntimeError(f"[AUDIT FAILED] Unable to read learned rules for agent '{agent}': {str(e)}")
                
        if not rules:
            continue

        # Concise prompt: Agent already has its rules in its system instruction from AgentEngine
        prompt = (
            f"PEGLEG LEARNED RULES AUDIT SURVEY:\n"
            f"Review your active operational rules (loaded in your System Instruction).\n"
            f"For each rule, evaluate whether it must STAY LOCAL to your operational domain ('STAY_LOCAL') "
            f"or be PROMOTED to 'shared_fleet_rules.json' ('PROMOTE_TO_SHARED'). Provide a concise justification for each decision."
        )
        
        # Execute agent turn via core engine. HARD FAIL on exception (No silent swallowing).
        try:
            from core.agent_engine import AgentEngine
            xml_rel_path = f"src/react_agent/agents/{agent}/{agent}.xml"
            xml_abs_path = os.path.abspath(os.path.join(base_dir, "..", xml_rel_path))
            
            engine = AgentEngine(agent_name=agent, xml_profile_path=xml_abs_path)
            thread_id = f"thread_audit_survey_{agent}_{timestamp_str}"
            chat_session = engine.start_chat_session(thread_id)
            response = engine.execute_turn(chat_session, prompt)
            engine.save_checkpoint(thread_id, chat_session.get_history())

            survey_results[agent] = {
                "rules_count": len(rules),
                "agent_response": response,
                "rules": rules
            }
        except Exception as e:
            raise RuntimeError(f"[AUDIT FAILED] Learned rules audit turn failed for agent '{agent}': {str(e)}")

    # 2. Generate Timestamped Decision Document
    decision_doc = "# PEGLEG MULTI-AGENT LEARNED RULES AUDIT & DECISION REPORT\n"
    decision_doc += f"**Audit Timestamp**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    decision_doc += f"**Audit Run ID**: `audit_{timestamp_str}`\n"
    decision_doc += f"**Target Fleet Agents**: {', '.join(survey_results.keys())}\n\n"
    decision_doc += "---\n\n## 1. SUBAGENT SURVEY RESPONSES & JUSTIFICATIONS\n\n"
    
    promoted_rules = []
    
    for agent, data in survey_results.items():
        decision_doc += f"### 🤖 Agent: `{agent.upper()}` ({data['rules_count']} Local Rules Audited)\n"
        decision_doc += f"#### Agent Justification & Recommendations:\n"
        decision_doc += f"```text\n{data['agent_response']}\n```\n\n"
        
        # Collect rules flagged for promotion and prune from local JSON
        local_rules_to_keep = []
        for r in data["rules"]:
            r_scope = r.get("scope", "").upper()
            if "FLEET_UNIVERSAL" in r_scope or "SHARED" in r_scope or "PROMOTE" in r_scope:
                promoted_rules.append(r)
            else:
                local_rules_to_keep.append(r)

        # If any rules were promoted, update local learned_rules.json
        if len(local_rules_to_keep) < len(data["rules"]):
            local_rule_path = os.path.join(base_dir, "agents", agent, "learned_rules.json")
            try:
                with open(local_rule_path, "w", encoding="utf-8") as lrf:
                    json.dump(local_rules_to_keep, lrf, indent=2)
            except Exception:
                pass

    # 3. Apply Promotions to shared_fleet_rules.json
    shared_vault_path = os.path.join(base_dir, "core_knowledge_vault", "shared_fleet_rules.json")
    existing_shared = []
    if os.path.exists(shared_vault_path):
        try:
            with open(shared_vault_path, "r", encoding="utf-8") as sf:
                existing_shared = json.load(sf)
        except Exception:
            existing_shared = []

    existing_ids = {r.get("rule_id") for r in existing_shared if r.get("rule_id")}
    promoted_count = 0

    for pr in promoted_rules:
        rdir = pr.get("rule_directive", "")
        # Prevent duplicate entries by directive or ID
        if not any(rdir.strip() == ex.get("rule_directive", "").strip() for ex in existing_shared):
            promoted_count += 1
            new_id = f"SHARED-RULE-{len(existing_shared) + 1:03d}"
            pr["rule_id"] = new_id
            pr["scope"] = "FLEET_UNIVERSAL"
            existing_shared.append(pr)

    if promoted_count > 0:
        try:
            with open(shared_vault_path, "w", encoding="utf-8") as sf:
                json.dump(existing_shared, sf, indent=2)
        except Exception:
            pass

    decision_doc += "---\n\n## 2. PEGLEG FINAL AUDIT DECISIONS\n\n"
    decision_doc += f"Total Rules Audited: {sum(d['rules_count'] for d in survey_results.values())}\n"
    decision_doc += f"Rules Promoted to Shared Vault: {promoted_count}\n\n"
    
    decision_doc += "### 🏆 Rationale & Domain Boundaries\n"
    decision_doc += "- **Team of Rivals Scoping**: Domain-specific heuristics for Cutlass (epistemic audit) and Bilgeladle (thesis alignment) REMAIN LOCAL to prevent prompt bloat and preserve rival friction.\n"
    decision_doc += "- **Shared Vault Promotion**: Cross-cutting formatting rules and universal ADR directives are promoted to `shared_fleet_rules.json`.\n\n"

    # 3. Save Timestamped Report to git-ignored agent_audits/ directory
    root_dir = os.path.abspath(os.path.join(base_dir, ".."))
    audits_dir = os.path.join(root_dir, "agent_audits")
    os.makedirs(audits_dir, exist_ok=True)
    
    # Ensure agent_audits/ is in .gitignore
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as gf:
            gi_content = gf.read()
        if "agent_audits/" not in gi_content:
            with open(gitignore_path, "a", encoding="utf-8") as gf:
                gf.write("\n# Agent Audit Reports\nagent_audits/\n")
    
    decision_path = os.path.join(audits_dir, f"learned_rules_audit_{timestamp_str}.md")
    with open(decision_path, "w", encoding="utf-8") as f:
        f.write(decision_doc)

    return f"[AUDIT COMPLETE] Multi-agent survey executed across {len(survey_results)} agents. Timestamped decision report written to: [{os.path.basename(decision_path)}](file:///{decision_path})"


def compile_rules_to_turtle_ontology(agent_name: str = "grog") -> str:
    """
    Agent Tool: RDF Turtle Ontology Compiler.
    Purpose: Compiles an agent's (or all fleet agents') `learned_rules.json` memory 
    vault into a W3C RDF/OWL Turtle (.ttl) semantic graph artifact.
    Invoked By: GROG (Primary Ontologist), PEGLEG, CUTLASS, HOOK.
    """
    try:
        from rdflib import Graph, Literal, RDF, URIRef, Namespace
        from rdflib.namespace import RDFS, OWL

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        rules_path = os.path.join(base_dir, "agents", agent_name.lower(), "learned_rules.json")
        output_ttl_path = os.path.join(base_dir, "..", "acquisitions", "npt_master_ontology.ttl")

        if not os.path.exists(rules_path):
            return f"[ERROR] No rules file found for agent '{agent_name}' at {rules_path}."

        g = Graph()
        NPT = Namespace("http://schema.npt.cloud/knowing/ontology/")
        g.bind("npt", NPT)

        with open(rules_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)

        for rule in rules_data:
            directive = rule.get("rule_directive", rule.get("directive", ""))
            context = rule.get("source_context", "Taught Step")

            concept_name = directive.split(" ")[0].replace(",", "").replace(".", "").replace(":", "") if directive else "Rule"
            concept_uri = NPT[concept_name]

            if "agnotology" in directive.lower() or "ignorance" in directive.lower():
                g.add((concept_uri, RDF.type, OWL.NamedIndividual))
                g.add((concept_uri, RDF.type, NPT.AgnotologicalPhenomenon))
            else:
                g.add((concept_uri, RDF.type, OWL.NamedIndividual))
                g.add((concept_uri, RDF.type, NPT.EpistemicConcept))

            g.add((concept_uri, RDFS.label, Literal(concept_name)))
            g.add((concept_uri, RDFS.comment, Literal(f"{directive} (Verified Source: {context})")))

        os.makedirs(os.path.dirname(output_ttl_path), exist_ok=True)
        g.serialize(destination=output_ttl_path, format="turtle")
        return f"[SUCCESS] Compiled {len(rules_data)} rule patterns for '{agent_name}' into RDF Turtle graph: [{os.path.basename(output_ttl_path)}](file:///{output_ttl_path})"
    except Exception as e:
        return f"[ERROR] RDF Turtle compilation failed: {str(e)}"