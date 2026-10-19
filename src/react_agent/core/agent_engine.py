"""
NPT-Cloud-Agents: Master Progeny Runtime Engine
Architecture: Pure Class Library with Dynamic Vault & Telemetry
Description: Manages the ReAct execution loop, token circuit-breakers, 
and Postgres-backed checkpoint memory for all agents in the fleet.
HOOK TEMPLATE NOTICE: Refer to SOP-06. This file MUST remain devoid of 
any `while True:` terminal loops or argparse CLI elements.
"""

"""
What is it for?
This is the Beating Heart of the Fleet. It is the pure class library that implements the ReAct (Reasoning and Acting) execution loop. It dynamically compiles the agent's brain by injecting the XML persona, JSON cognitive lenses, and learned skills into the system_instruction. It handles token circuit-breakers, prevents infinite tool loops, and manages the LangGraph-style checkpointing to the Postgres agent_state database.
How does it run?
It is instantiated by the specific agent entrypoints (e.g., cutlass_runner.py). It adheres strictly to SOP-06 (The "Pure Engine" Execution Pattern), remaining completely isolated from terminal loops or user inputs.
"""

import os
import sys
import json
import re
import datetime
import xml.etree.ElementTree as ET
import copy
from urllib.parse import urlparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

load_dotenv(override=True)

# Mounts the root src directory to ensure absolute module imports function correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.tool_dispatcher import ToolDispatcher
from core.cost_tracker import CostTracker, SpendingCapExceededException

load_dotenv(override=True)

class AgentEngine:

    def __init__(self, agent_name: str, xml_profile_path: str, model_override: str = None, cost_tracker: CostTracker = None, spending_cap_usd: float = None):
        """
        Initializes the Engine, loads the agent's specific memory vault, 
        and binds the requested tools to the Gemini SDK.
        """
        self.agent_name = agent_name.lower()
        self.xml_profile_path = xml_profile_path
        self.client = genai.Client()
        self.dispatcher = ToolDispatcher()
        
        # Financial Governor & Token Telemetry (ADR-018)
        self.cost_tracker = cost_tracker or CostTracker(spending_cap_usd=spending_cap_usd)
        
        # Database connection is acquired on-demand per checkpoint operation to prevent pool exhaustion (ADR-003)
        self.db_conn = None
        
        # Compiles the cognitive state from local JSON and XML files
        self.memory_vault = self._load_agent_memory_vault()
        
        # Determines the specific Vertex AI model to utilize using strict 3-level hierarchy:
        # 1. CLI Override (`model_override`)
        # 2. XML Profile Override (`xml_model_target`)
        # 3. .env Default (`DEFAULT_MODEL`)
        default_sys_model = os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")
        xml_model = self.memory_vault.get("xml_model_target")
        self.model_name = model_override or xml_model or default_sys_model
        print(f"  -> [ENGINE BOOT] Routed Cognitive Model: {self.model_name.upper()}")

        # Compiles the massive System Prompt used to anchor the model
        self.system_instruction = self._build_dynamic_system_prompt(self.memory_vault)
        
        # Binds only the specific tools requested in the agent's XML manifest
        self.bound_tools = self._bind_requested_tools(self.memory_vault.get("requested_tools", {}))
        
        # Dumps the compiled prompt to disk for human observability
        self._dump_system_prompt()

    def _get_db_connection(self):
        """Establishes connection exclusively to the cognitive state schema (ADR-003)."""
        try:
            url = urlparse(os.getenv("DATABASE_URL"))
            return pg8000.dbapi.connect(
                user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
            )
        except Exception as e:
            print(f"[DB ERROR] Connectivity failure: {e}", file=sys.stderr)
            return None

    def _load_agent_memory_vault(self) -> Dict[str, Any]:
        """
        The Genetic Sequencer. 
        Parses the agent's XML mandate, available tools, and local JSON brain files 
        into a unified dictionary representing the agent's complete operational state.
        """
        base_path = os.path.dirname(self.xml_profile_path)
        profile = {"mandate": "", "lens": {}, "skills": [], "rules": [], "exemplars": [], "requested_tools": {}, "model_target": os.getenv("DEFAULT_MODEL", "gemini-3.8-flash")}
        
        if os.path.exists(self.xml_profile_path):
            tree = ET.parse(self.xml_profile_path)
            root = tree.getroot()
            
            # Parse mandate or system_instructions
            sys_inst_elem = root.find(".//system_instructions")
            mandate_elem = root.find(".//core_mandate")
            if sys_inst_elem is not None:
                profile["mandate"] = "".join(sys_inst_elem.itertext()).strip()
            elif mandate_elem is not None:
                profile["mandate"] = "".join(mandate_elem.itertext()).strip()
            
            # Parse fleet roster if present (e.g. for Pegleg)
            roster_elem = root.find(".//fleet_roster")
            if roster_elem is not None:
                profile["fleet_roster"] = []
                for a_node in roster_elem.findall("agent"):
                    aname = a_node.get("name", "")
                    arole = a_node.findtext("role", default="").strip()
                    acap = a_node.findtext("capabilities", default="").strip()
                    profile["fleet_roster"].append({"name": aname, "role": arole, "capabilities": acap})

            tools_elem = root.find(".//available_tools")
            if tools_elem is not None:
                for tool_node in tools_elem.findall("tool"):
                    t_name = tool_node.get("name")
                    if t_name:
                        profile["requested_tools"][t_name] = "".join(tool_node.itertext()).strip()

            # Parse model target from XML if explicitly configured
            model_elem = root.find(".//model")
            if model_elem is not None and model_elem.text and model_elem.text.strip():
                profile["xml_model_target"] = model_elem.text.strip()
            else:
                profile["xml_model_target"] = None

            # Parse specialized operational execution skills and skill references from XML
            allowed_skill_names = set()
            skills_elem = root.find(".//skills")
            if skills_elem is not None:
                # 1. Collect declared skill references (<skill_ref name="..."/>)
                for ref_node in skills_elem.findall("skill_ref"):
                    r_name = ref_node.get("name")
                    if r_name:
                        allowed_skill_names.add(r_name.replace("_", "-").lower())

                # 2. Collect inline skills (<skill name="..."><description>...</description></skill>)
                for skill_node in skills_elem.findall("skill"):
                    s_name = skill_node.get("name", "UNNAMED_SKILL")
                    s_desc = skill_node.findtext("description", default="").strip()
                    s_exec = skill_node.findtext("execution_protocol", default="").strip()
                    s_slug = s_name.replace("_", "-").lower()
                    allowed_skill_names.add(s_slug)
                    profile["skills"].append({
                        "name": s_name,
                        "description": s_desc,
                        "protocol": s_exec
                    })

        # Load standalone SKILL.md files from central skills repository ONLY if authorized for this agent
        central_skills_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "skills"
        ))
        if os.path.exists(central_skills_dir):
            for skill_dir in os.listdir(central_skills_dir):
                s_slug = skill_dir.replace("_", "-").lower()
                
                # Scope check: Only load skill if explicitly referenced in XML firmware
                if s_slug not in allowed_skill_names:
                    continue

                skill_md_path = os.path.join(central_skills_dir, skill_dir, "SKILL.md")
                if os.path.isfile(skill_md_path):
                    with open(skill_md_path, 'r', encoding='utf-8') as sf:
                        content = sf.read()
                        # Extract frontmatter if present
                        s_name = skill_dir
                        s_desc = f"Modular skill: {skill_dir}"
                        s_protocol = content
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                frontmatter = parts[1]
                                s_protocol = parts[2].strip()
                                for line in frontmatter.splitlines():
                                    if line.startswith("name:"):
                                        s_name = line.split("name:", 1)[1].strip()
                                    elif line.startswith("description:"):
                                        s_desc = line.split("description:", 1)[1].strip()
                        
                        # Append if not already present (comparing normalized kebab-case slug)
                        s_norm = s_name.replace("_", "-").lower()
                        if not any(existing['name'].replace("_", "-").lower() == s_norm for existing in profile["skills"]):
                            profile["skills"].append({
                                "name": s_norm,
                                "description": s_desc,
                                "protocol": s_protocol
                            })

        # Load the philosophical ontology
        lens_path = os.path.join(base_path, "cognitive_lens.json")
        if os.path.exists(lens_path):
            with open(lens_path, 'r', encoding='utf-8') as f:
                profile["lens"] = json.load(f)
                
        # Parse XML rules, guardrails, and legacy heuristics
        xml_rules = []
        if os.path.exists(self.xml_profile_path):
            tree = ET.parse(self.xml_profile_path)
            root = tree.getroot()
            
            # Parse <guardrails>
            g_elem = root.find(".//guardrails")
            if g_elem is not None:
                for r_node in g_elem.findall("rule"):
                    r_name = r_node.findtext("name", default=r_node.get("id", "GUARDRAIL")).strip()
                    r_desc = r_node.findtext("directive", default=r_node.findtext("description", default="")).strip()
                    r_ctx = r_node.findtext("rationale", default="").strip()
                    xml_rules.append({"rule_id": f"GUARDRAIL: {r_name}", "rule_directive": r_desc, "source_context": r_ctx})

            # Parse <rules>
            rules_elem = root.find(".//rules")
            if rules_elem is not None:
                for r_node in rules_elem.findall("rule"):
                    r_name = r_node.findtext("name", default=r_node.get("id", "RULE")).strip()
                    r_desc = r_node.findtext("directive", default=r_node.findtext("description", default="")).strip()
                    r_ctx = r_node.findtext("rationale", default="").strip()
                    xml_rules.append({"rule_id": r_name, "rule_directive": r_desc, "source_context": r_ctx})
                    
            # Parse <heuristics> (Legacy fallback)
            heur_elem = root.find(".//heuristics")
            if heur_elem is not None:
                for h_node in heur_elem.findall("rule"):
                    h_name = h_node.findtext("name", default="HEURISTIC").strip()
                    h_desc = h_node.findtext("description", default="").strip()
                    xml_rules.append({"rule_id": h_name, "rule_directive": h_desc, "source_context": "XML Heuristic Directive"})

        # Load universal shared fleet rules (Core Knowledge Vault)
        shared_vault_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "core_knowledge_vault", "shared_fleet_rules.json"
        ))
        combined_rules = xml_rules
        if os.path.exists(shared_vault_path):
            with open(shared_vault_path, 'r', encoding='utf-8') as sf:
                try:
                    s_rules = json.load(sf)
                    for r in s_rules:
                        # Exclude technical System Architecture / ADR rules for non-hook agents
                        cat = r.get("category", "")
                        if "System Architecture" in cat or "ADR" in cat:
                            if self.agent_name != "hook":
                                continue
                        combined_rules.append(r)
                except Exception:
                    pass

        # Load agent-specific permanent behavioral corrections
        rules_path = os.path.join(base_path, "learned_rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                try:
                    local_rules = json.load(f)
                    combined_rules.extend(local_rules)
                except Exception:
                    pass
                    
        profile["rules"] = combined_rules
                
        # Load architectural response templates
        exemplars_path = os.path.join(base_path, "few_shot_exemplars.json")
        if os.path.exists(exemplars_path):
            with open(exemplars_path, 'r', encoding='utf-8') as f:
                profile["exemplars"] = json.load(f)
                
        return profile

    def _build_dynamic_system_prompt(self, memory: Dict[str, Any]) -> str:
        """Translates the structured memory vault into the raw text System Instruction block."""
        prompt = f"You are {self.agent_name.upper()}.\n\n"
        
        if memory.get("mandate"):
            prompt += f"=== CORE MANDATE ===\n{memory['mandate']}\n\n"

        roster = memory.get("fleet_roster", [])
        if roster:
            prompt += "=== FLEET CREW ROSTER (AUTHORIZED SUBAGENTS) ===\n"
            for member in roster:
                prompt += f"• AGENT: {member['name'].upper()}\n  Role: {member['role']}\n  Capabilities: {member['capabilities']}\n"
            prompt += "\n"
            
        lens = memory.get("lens")
        if lens:
            prompt += "=== COGNITIVE LENS & PHILOSOPHICAL FRAMEWORKS ===\n"
            lens_items = lens if isinstance(lens, list) else [lens]
            for item in lens_items:
                if not isinstance(item, dict):
                    continue
                if "domain_bias" in item and item["domain_bias"]:
                    prompt += f"--- DOMAIN BIAS & CONSTITUTION ---\n{item['domain_bias']}\n\n"
                if "strict_lexicon" in item and isinstance(item["strict_lexicon"], dict):
                    lex = item["strict_lexicon"]
                    prompt += "--- STRICT LEXICON CONSTRAINTS ---\n"
                    if "prioritize" in lex and lex["prioritize"]:
                        prompt += f"• Prioritize Concepts: {', '.join(lex['prioritize'])}\n"
                    if "reject" in lex and lex["reject"]:
                        prompt += f"• Reject Concepts: {', '.join(lex['reject'])}\n"
                    prompt += "\n"
                if "analytical_frameworks" in item and isinstance(item["analytical_frameworks"], list):
                    prompt += "--- ANALYTICAL FRAMEWORKS & EPISTEMIC LENSES ---\n"
                    for f_idx, af in enumerate(item["analytical_frameworks"], 1):
                        name = af.get("lens_name") or af.get("title") or f"Framework {f_idx}"
                        desc = af.get("perspective") or af.get("thesis") or str(af)
                        prompt += f"{f_idx}. [{name}]\n   {desc}\n\n"
                for k, v in item.items():
                    if k in ["agent_name", "domain_bias", "strict_lexicon", "analytical_frameworks"]:
                        continue
                    if isinstance(v, dict):
                        title = v.get("title", k)
                        thesis = v.get("thesis") or v.get("perspective") or str(v)
                        prompt += f"• [{title}]: {thesis}\n\n"
                    elif isinstance(v, str):
                        prompt += f"• [{k}]: {v}\n\n"

        skills = memory.get("skills", [])
        if skills:
            prompt += "=== AUTHORIZED SKILLS & CAPABILITIES ===\n"
            prompt += "You have access to the following specialized skills. To inspect or execute a skill's full protocol, invoke `read_skill_protocol(skill_name)` on-demand:\n"
            for s in skills:
                prompt += f"• `{s['name']}`: {s['description']}\n"
            prompt += "\n"
            
        rules = memory.get("rules", [])
        if rules:
            prompt += "=== OPERATIONAL HEURISTICS & LEARNED PRINCIPLES ===\n"
            for idx, rule in enumerate(rules, 1):
                if isinstance(rule, dict):
                    rid = rule.get('heuristic_id') or rule.get('learning_id') or rule.get('rule_id') or rule.get('id') or f'HEURISTIC-{idx:03d}'
                    rdir = rule.get('generalized_heuristic') or rule.get('rule_directive') or rule.get('directive') or rule.get('description') or str(rule)
                    mech = rule.get('underlying_mechanism', '')
                    ctx = rule.get('incident_context') or rule.get('source_context', '')
                    
                    details = []
                    if mech:
                        details.append(f"   Mechanism: {mech}")
                    if ctx:
                        details.append(f"   Context: {ctx}")
                    detail_str = ("\n" + "\n".join(details)) if details else ""
                    prompt += f"{idx}. [{rid}]\n   Heuristic: {rdir}{detail_str}\n"
                else:
                    prompt += f"{idx}. {str(rule)}\n"
            prompt += "\n"
            
        tools = memory.get("requested_tools", {})
        if tools:
            prompt += "=== AUTHORIZED TOOLS & XML CAPABILITIES ===\n"
            for t_name, t_purpose in tools.items():
                purpose_str = f": {t_purpose}" if t_purpose else ""
                prompt += f"• `{t_name}`{purpose_str}\n"
            prompt += "\n"

        exemplars = memory.get("exemplars", [])
        if exemplars:
            prompt += "=== FEW-SHOT EXEMPLARS ===\n"
            for ex in exemplars:
                prompt += f"Input Context: {ex.get('input_context', '')}\nIdeal Output: {ex.get('ideal_output', '')}\n\n"

        # Note: GEMINI.md contains Antigravity IDE and repository laws for human/IDE pair-programming.
        # It is no longer injected into fleet subagent runtime prompts to save ~8,000 tokens per turn.

        # Ingest Master Ship Deck Plans (Macro-Backbones & Section Ribs) for Bilgeladle
        if self.agent_name.lower() == "bilgeladle":
            deck_plans_candidates = [
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "SHIP_DECK_PLANS.md")),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ship", "CHAPTER_BACKBONES.md")),
            ]
            deck_plans_text = ""
            for dp_path in deck_plans_candidates:
                if os.path.exists(dp_path):
                    try:
                        with open(dp_path, "r", encoding="utf-8") as dpf:
                            deck_plans_text = dpf.read()
                            break
                    except Exception:
                        pass

            if deck_plans_text:
                prompt += (
                    "=== SHIP DECK PLANS (THE END OF KNOWING - MASTER CHAPTER BACKBONES & SECTION RIBS) ===\n"
                    "The following is the canonical structural blueprint ('Ship Deck Plans') containing all 13 "
                    "macro-chapter backbones and 140 calibrated individual section ribs. You must use this structural "
                    "skeleton for epistemic triage to lock the Primary Chapter Anchor and candidate section ribs. "
                    "When full chapter context or verbatim text is required, call read_manuscript_chapter(chapter_number) "
                    "or vector_search_manuscript:\n\n"
                    f"{deck_plans_text}\n"
                    "================================================================================\n\n"
                )
                
        return prompt

    def _bind_requested_tools(self, requested_tools: Dict[str, str]) -> List[types.Tool]:
        """Filters the master tool registry to only expose tools authorized in the agent's XML."""
        bound_tools = []
        for decl in self.dispatcher.tool_definitions:
            if decl.name in requested_tools:
                isolated_decl = copy.deepcopy(decl)
                custom_purpose = requested_tools[decl.name]
                if custom_purpose:
                    isolated_decl.description = custom_purpose
                bound_tools.append(isolated_decl)
                
        if bound_tools:
            return [types.Tool(function_declarations=bound_tools)]
        return []

    def close(self):
        """Closes any open cognitive state DB connection to prevent connection pool exhaustion."""
        if hasattr(self, "db_conn") and self.db_conn:
            try:
                self.db_conn.close()
            except Exception:
                pass
            self.db_conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

    def get_latest_checkpoint(self, thread_id: str, max_turns: int = 20) -> List[types.Content]:
        """
        Retrieves the conversational history for a specific thread from Postgres.
        Implements a rolling window (truncation) to prevent Token Bloat.
        Uses on-demand connection handling to prevent connection pool leaks.
        """
        conn = self._get_db_connection()
        if not conn:
            return []
        
        row = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT state_payload FROM agent_state.checkpoints WHERE thread_id = %s ORDER BY updated_at DESC LIMIT 1", (thread_id,))
            row = cursor.fetchone()
            cursor.close()
        except Exception as e:
            print(f"[CHECKPOINT READ ERROR] {e}", file=sys.stderr)
            return []
        finally:
            try:
                conn.close()
            except Exception:
                pass
        
        history = []
        if row and row[0]:
            raw_history = row[0] if isinstance(row[0], list) else json.loads(row[0])
            
            # SAFEGUARD: Enforce the rolling window. A 'turn' is one USER msg and one MODEL msg.
            if len(raw_history) > (max_turns * 2):
                raw_history = raw_history[-(max_turns * 2):]
                print(f"  -> [SYSTEM] Context window truncated. Retaining last {max_turns} turns.")

            for msg in raw_history:
                parts = [types.Part.from_text(text=p.get("text", "")) for p in msg.get("parts", [])]
                history.append(types.Content(role=msg.get("role"), parts=parts))
        return history

    def save_checkpoint(self, thread_id: str, history: List[types.Content]):
        """Persists the updated conversational history array back to Postgres with on-demand connection handling."""
        conn = self._get_db_connection()
        if not conn:
            return
            
        serializable_history = []
        for content in history:
            parts = [{"text": part.text} for part in content.parts if part.text]
            if parts: serializable_history.append({"role": content.role, "parts": parts})
                
        try:
            cursor = conn.cursor()
            # Uses UPSERT logic to maintain a single row per thread
            cursor.execute(
                """
                INSERT INTO agent_state.checkpoints (thread_id, state_payload, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (thread_id) DO UPDATE SET state_payload = EXCLUDED.state_payload, updated_at = NOW();
                """,
                (thread_id, json.dumps(serializable_history))
            )
            conn.commit()
            cursor.close()
        except Exception as e:
            print(f"[CHECKPOINT WRITE ERROR] {e}", file=sys.stderr)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def start_chat_session(self, thread_id: str):
        """Initializes the SDK Chat Session object using the retrieved history."""
        self.active_thread_id = thread_id
        history = self.get_latest_checkpoint(thread_id)
        config = self._get_active_config()
        return self.client.chats.create(model=self.model_name, config=config, history=history)

    def _get_active_config(self):
        tool_config = types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="AUTO")) if self.bound_tools else None
        
        # Instate active thread context so agents never hallucinate divergent folder names
        active_instruction = self.system_instruction
        if hasattr(self, "active_thread_id") and self.active_thread_id:
            cargo_match = re.search(r"cargo_(\d+)", self.active_thread_id)
            if cargo_match:
                cargo_id = cargo_match.group(1)
                active_instruction += (
                    f"\n\n=== ACTIVE SESSION THREAD & MANDATORY DIRECTORY BINDING ===\n"
                    f"ACTIVE_THREAD_ID: {self.active_thread_id}\n"
                    f"CARGO_ID: {cargo_id}\n"
                    f"CRITICAL DIRECTIVE: The cargo dossier workspace directory for this session is strictly \"writings/cargo/cargo_{cargo_id}/\". "
                    f"All asset evaluations, audits, and extractions MUST be written directly inside \"writings/cargo/cargo_{cargo_id}/\".\n"
                )
            else:
                chase_id = getattr(self, "chase_id", None)
                if not chase_id:
                    chase_id = re.sub(r"^thread_(?:spyglass|cutlass|grog|plank|bilgeladle|scallywag|landlubber|hook|pegleg)_", "", self.active_thread_id)
                    
                active_instruction += (
                    f"\n\n=== ACTIVE SESSION THREAD & MANDATORY DIRECTORY BINDING ===\n"
                    f"ACTIVE_THREAD_ID: {self.active_thread_id}\n"
                    f"CHASE_WORKSPACE_ID: {chase_id}\n"
                    f"CRITICAL DIRECTIVE: The root chase workspace directory for this session is strictly \"writings/chases/{chase_id}/\". "
                    f"All stage outputs, audits, extractions, essays, and status tracking MUST be written directly inside \"writings/chases/{chase_id}/\". "
                    f"You are STRICTLY FORBIDDEN from creating or inventing subagent-specific folder prefixes (e.g. do NOT write to 'writings/chases/thread_{self.agent_name}_{chase_id}/').\n"
                )

        return types.GenerateContentConfig(
            system_instruction=active_instruction,
            temperature=0.1, # Extremely low temperature enforces highly deterministic, logical outputs
            tools=self.bound_tools,
            tool_config=tool_config
        )

    def execute_turn(self, chat_session, prompt: str = None, prompt_file: str = None) -> str:
        """
        The ReAct (Reasoning and Acting) execution loop.
        Handles the conversational ping-pong of Tool Calling and Observation.
        Supports passing raw prompt string or reading from a prompt_file.
        """
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as pf:
                prompt = pf.read()
        elif prompt and os.path.exists(prompt) and (prompt.endswith(".md") or prompt.endswith(".txt")):
            # Auto-detect if prompt argument itself is a valid file path
            with open(prompt, "r", encoding="utf-8") as pf:
                prompt = pf.read()

        if not prompt:
            raise ValueError("execute_turn requires a non-empty prompt or a valid prompt_file.")

        # Check for user-declared spending cap in prompt if not already set (ADR-018)
        if self.cost_tracker.spending_cap_usd is None:
            detected_cap = CostTracker.parse_spending_cap(prompt)
            if detected_cap is not None:
                self.cost_tracker.spending_cap_usd = detected_cap
                print(f"  -> [FINANCIAL GOVERNOR] User spending cap detected and locked: ${detected_cap:.2f}")

        history = chat_session.get_history()
        
        # =====================================================================
        # 1. THE TOKEN-BASED CIRCUIT BREAKER
        # Prevents runaway costs and API failures by monitoring payload size
        # =====================================================================
        MAX_TOKENS = 60000 
        
        try:
            # Query the Google API for exact token weight
            token_response = self.client.models.count_tokens(
                model=self.model_name,
                contents=history
            )
            current_tokens = token_response.total_tokens
        except Exception as e:
            # Fallback estimation if the API check fails (approx 4 chars per token)
            current_tokens = len(str(history)) // 4 
            
        if current_tokens > MAX_TOKENS:
            command = prompt.strip().upper()
            if command == "OVERRIDE":
                print(f"  -> [SYSTEM] Context limit overridden. Current load: {current_tokens} tokens.")
                prompt = "[SYSTEM NOTE: Author overridden context limit. Proceed.]"
            elif command == "HANDOFF":
                print("  -> [SYSTEM] Generating Thread Handoff Document...")
                prompt = "[SYSTEM COMMAND: Context window saturated. Generate a 'Thread Handoff Document' summarizing our state.]"
            elif not prompt.startswith("[SYSTEM"):
                # Halt execution and return control to the Human Architect
                return (f"\n[SYSTEM ALERT] Cognitive Limit Reached ({current_tokens} / {MAX_TOKENS} tokens).\n"
                        f"OPTIONS:\n"
                        f"1. Type 'HANDOFF' to generate a state-transfer summary.\n"
                        f"2. Type 'OVERRIDE' to force context expansion.")

        # Helper for resilient send_message with exponential backoff
        def _send_with_retry(msg, cfg, max_retries=2):
            import time
            for attempt in range(1, max_retries + 1):
                try:
                    return chat_session.send_message(msg, config=cfg)
                except Exception as e:
                    err_str = str(e)
                    if attempt < max_retries and any(c in err_str for c in ["503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "high demand"]):
                        sleep_s = 25 * attempt
                        print(f"  -> [API RETRY] Transient Google API error ({err_str[:60]}...). Retrying in {sleep_s}s (Attempt {attempt}/{max_retries})...")
                        time.sleep(sleep_s)
                    else:
                        raise e

        # =====================================================================
        # 2. STANDARD EXECUTION & TOOL LOOP
        # =====================================================================
        active_config = self._get_active_config()
        try:
            response = _send_with_retry(prompt, active_config)
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                summary = self.cost_tracker.record_turn_usage(response.usage_metadata, self.model_name)
                print(self.cost_tracker.get_telemetry_string(summary))
        except SpendingCapExceededException as sce:
            print(f"\n{sce}\n")
            alert_msg = f"[FINANCIAL CIRCUIT BREAKER TRIGGERED] {str(sce)}"
            self._log_interaction(prompt, alert_msg)
            return alert_msg
        
        tool_loop_count = 0
        # DAG orchestrators (e.g. Pegleg) coordinate multi-stage pipelines; ingestion agents (Spyglass) need at most 4 turns
        MAX_TOOL_LOOPS = 60 if self.agent_name == "pegleg" else 4 if self.agent_name == "spyglass" else 20

        while response.function_calls:
            tool_loop_count += 1
            if tool_loop_count > MAX_TOOL_LOOPS:
                print(f"  -> [CIRCUIT BREAKER TRIGGERED] {self.agent_name.upper()} exceeded max tool limit ({MAX_TOOL_LOOPS}). Halting workflow execution.")
                return f"[CIRCUIT BREAKER TRIGGERED] Agent '{self.agent_name}' reached maximum allowable tool turns ({MAX_TOOL_LOOPS}). Execution safety halt enforced."

            tool_responses = []
            for call in response.function_calls:
                call_args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                
                # Format descriptive argument summary for real-time terminal observability
                arg_summary = ""
                if "file_path" in call_args:
                    arg_summary = f" (file: {call_args['file_path']})"
                elif "target_path" in call_args:
                    arg_summary = f" (target: {call_args['target_path']})"
                elif "asset_path" in call_args:
                    arg_summary = f" (asset: {call_args['asset_path']})"
                elif "subagent_name" in call_args:
                    sub_thread = f", thread: {call_args.get('subagent_thread_id', '')}" if call_args.get('subagent_thread_id') else ""
                    arg_summary = f" (subagent: {str(call_args['subagent_name']).upper()}{sub_thread})"
                elif "target_url" in call_args:
                    arg_summary = f" (url: {call_args['target_url']})"
                elif "url" in call_args:
                    arg_summary = f" (url: {call_args['url']})"
                elif "issue_number" in call_args:
                    arg_summary = f" (issue: #{call_args['issue_number']})"
                elif "enrichment_type" in call_args:
                    meta_id = f", metadata_id: {call_args.get('metadata_id', '')}" if call_args.get('metadata_id') else ""
                    arg_summary = f" (type: {call_args['enrichment_type']}{meta_id})"
                elif "skill_name" in call_args:
                    arg_summary = f" (skill: {call_args['skill_name']})"
                elif "query" in call_args:
                    arg_summary = f" (query: '{call_args['query']}')"
                elif "term" in call_args:
                    arg_summary = f" (term: '{call_args['term']}')"
                elif call_args:
                    first_k, first_v = next(iter(call_args.items()))
                    v_str = str(first_v)[:50]
                    arg_summary = f" ({first_k}: {v_str})"

                print(f"  -> [SYSTEM] {self.agent_name.upper()} executing tool: {call.name}{arg_summary}...")
                
                # Execute and Trace
                result_str = self.dispatcher.execute_tool_call(call)
                self._log_tool_trace(call.name, call_args, result_str)
                
                # --- The Hot-Reload Hook ---
                # Allows the agent to instantly integrate new memory updates mid-turn
                if call.name == "reload_agent_memory_vault":
                    self.memory_vault = self._load_agent_memory_vault()
                    self.system_instruction = self._build_dynamic_system_prompt(self.memory_vault)
                    active_config = self._get_active_config()
                    print(f"  -> [HOT-RELOAD] Rules and Lexicon successfully refreshed.")
                
                tool_responses.append(types.Part.from_function_response(
                    name=call.name,
                    response={"result": result_str}
                ))
            
            # Send tool observation data back to the model for the next step of reasoning
            try:
                response = _send_with_retry(tool_responses, active_config)
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    summary = self.cost_tracker.record_turn_usage(response.usage_metadata, self.model_name)
                    print(self.cost_tracker.get_telemetry_string(summary))
            except SpendingCapExceededException as sce:
                print(f"\n{sce}\n")
                alert_msg = f"[FINANCIAL CIRCUIT BREAKER TRIGGERED] {str(sce)}"
                self._log_interaction(prompt, alert_msg)
                return alert_msg
            
        final_text = getattr(response, "text", "") or ""
        self._log_interaction(prompt, final_text)
        return final_text

    # =====================================================================
    # OFFLINE TELEMETRY LOGGING
    # See ADR-004: Continuous File Telemetry over Cloud Logging
    # =====================================================================
    def _dump_system_prompt(self):
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, f"{self.agent_name}_system_prompt_compiled.log"), "w", encoding="utf-8") as f:
            f.write(self.system_instruction)

    def _log_interaction(self, prompt: str, response_text: str):
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(os.path.join(log_dir, f"{self.agent_name}_interactions.log"), "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n[{ts}] INPUT -> {self.agent_name.upper()}\n{'='*60}\n{prompt}\n")
            f.write(f"\n[{ts}] OUTPUT <- {self.agent_name.upper()}\n{'-'*60}\n{response_text}\n")

    def _log_tool_trace(self, tool_name: str, args: dict, result: str):
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Safely truncate massive payloads (like raw HTML) from the trace logs
        safe_args = {}
        for k, v in args.items():
            if isinstance(v, str) and len(v) > 500:
                safe_args[k] = v[:500] + f"\n... [TRUNCATED: Payload was {len(v)} characters]"
            else:
                safe_args[k] = v
                
        # Force result to string to prevent NoneType len() crashes
        result_str = str(result)
        safe_result = result_str if len(result_str) < 1000 else result_str[:1000] + f"\n... [TRUNCATED: Result was {len(result_str)} characters]"

        log_entry = (f"=== TOOL TRACE: {ts} ===\nWire Target: {tool_name}\n"
                     f"Args: {json.dumps(safe_args, indent=2)}\nOutput:\n{safe_result}\n{'='*40}\n\n")
        
        with open(os.path.join(log_dir, f"active_tool_execution_trace.log"), "a", encoding="utf-8") as f:
            f.write(log_entry)