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
import datetime
import xml.etree.ElementTree as ET
import copy
from urllib.parse import urlparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

# Mounts the root src directory to ensure absolute module imports function correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.tool_dispatcher import ToolDispatcher

load_dotenv()

class AgentEngine:

    def __init__(self, agent_name: str, xml_profile_path: str, model_override: str = None):
        """
        Initializes the Engine, loads the agent's specific memory vault, 
        and binds the requested tools to the Gemini SDK.
        """
        self.agent_name = agent_name.lower()
        self.xml_profile_path = xml_profile_path
        self.client = genai.Client()
        self.dispatcher = ToolDispatcher()
        
        # Connects to the State DB (agent_state schema) to manage memory checkpoints
        self.db_conn = self._get_db_connection()
        
        # Compiles the cognitive state from local JSON and XML files
        self.memory_vault = self._load_agent_memory_vault()
        
        # Determines the specific Vertex AI model to utilize (e.g., gemini-3.5-flash)
        self.model_name = model_override or self.memory_vault.get("model_target", "gemini-3.5-flash")
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
        profile = {"mandate": "", "lens": {}, "skills": [], "rules": [], "exemplars": [], "requested_tools": {}}
        
        if os.path.exists(self.xml_profile_path):
            tree = ET.parse(self.xml_profile_path)
            root = tree.getroot()
            mandate_elem = root.find(".//core_mandate")
            if mandate_elem is not None:
                profile["mandate"] = "".join(mandate_elem.itertext()).strip()
            
            tools_elem = root.find(".//available_tools")
            if tools_elem is not None:
                for tool_node in tools_elem.findall("tool"):
                    t_name = tool_node.get("name")
                    if t_name:
                        profile["requested_tools"][t_name] = "".join(tool_node.itertext()).strip()

            model_elem = root.find(".//model")
            profile["model_target"] = model_elem.text.strip() if model_elem is not None else "gemini-3.5-flash"

            # Parse specialized operational execution skills
            skills_elem = root.find(".//skills")
            if skills_elem is not None:
                for skill_node in skills_elem.findall("skill"):
                    s_name = skill_node.get("name", "UNNAMED_SKILL")
                    s_desc = skill_node.findtext("description", default="").strip()
                    s_exec = skill_node.findtext("execution_protocol", default="").strip()
                    profile["skills"].append({
                        "name": s_name,
                        "description": s_desc,
                        "protocol": s_exec
                    })

        # Load the philosophical ontology
        lens_path = os.path.join(base_path, "cognitive_lens.json")
        if os.path.exists(lens_path):
            with open(lens_path, 'r', encoding='utf-8') as f:
                profile["lens"] = json.load(f)
                
        # Load permanent behavioral corrections
        rules_path = os.path.join(base_path, "learned_rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, 'r', encoding='utf-8') as f:
                profile["rules"] = json.load(f)
                
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
            
        lens = memory.get("lens", {})
        if lens:
            prompt += "=== COGNITIVE LENS & DOMAIN BIAS ===\n"
            prompt += lens.get("domain_bias", "") + "\n\n"

        skills = memory.get("skills", [])
        if skills:
            prompt += "=== ACTIVE SKILLS & EXECUTION PROTOCOLS ===\n"
            for s in skills:
                prompt += f"SKILL: {s['name']}\n"
                prompt += f"DESCRIPTION: {s['description']}\n"
                prompt += f"PROTOCOL:\n{s['protocol']}\n\n"
            
        rules = memory.get("rules", [])
        if rules:
            prompt += "=== LEARNED RULES (PERMANENT ALIGNMENT) ===\n"
            for idx, rule in enumerate(rules, 1):
                rule_text = rule.get('rule_directive') or rule.get('rule') or str(rule)
                source_info = rule.get('source_context') or rule.get('timestamp') or 'Learned Rule'
                prompt += f"{idx}. {rule_text} (Source: {source_info})\n"
            prompt += "\n"
            
        exemplars = memory.get("exemplars", [])
        if exemplars:
            prompt += "=== FEW-SHOT EXEMPLARS ===\n"
            for ex in exemplars:
                prompt += f"Input Context: {ex.get('input_context', '')}\nIdeal Output: {ex.get('ideal_output', '')}\n\n"
                
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

    def get_latest_checkpoint(self, thread_id: str, max_turns: int = 10) -> List[types.Content]:
        """
        Retrieves the conversational history for a specific thread from Postgres.
        Implements a rolling window (truncation) to prevent Token Bloat.
        """
        if not self.db_conn: return []
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT state_payload FROM agent_state.checkpoints WHERE thread_id = %s ORDER BY updated_at DESC LIMIT 1", (thread_id,))
        row = cursor.fetchone()
        cursor.close()
        
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
        """Persists the updated conversational history array back to Postgres."""
        if not self.db_conn: return
        serializable_history = []
        for content in history:
            parts = [{"text": part.text} for part in content.parts if part.text]
            if parts: serializable_history.append({"role": content.role, "parts": parts})
                
        cursor = self.db_conn.cursor()
        # Uses UPSERT logic to maintain a single row per thread
        cursor.execute(
            """
            INSERT INTO agent_state.checkpoints (thread_id, state_payload, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (thread_id) DO UPDATE SET state_payload = EXCLUDED.state_payload, updated_at = NOW();
            """,
            (thread_id, json.dumps(serializable_history))
        )
        self.db_conn.commit()
        cursor.close()

    def start_chat_session(self, thread_id: str):
        """Initializes the SDK Chat Session object using the retrieved history."""
        history = self.get_latest_checkpoint(thread_id)
        config = self._get_active_config()
        return self.client.chats.create(model=self.model_name, config=config, history=history)

    def _get_active_config(self):
        tool_config = types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode="AUTO")) if self.bound_tools else None
        return types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            temperature=0.1, # Extremely low temperature enforces highly deterministic, logical outputs
            tools=self.bound_tools,
            tool_config=tool_config
        )

    def execute_turn(self, chat_session, prompt: str) -> str:
        """
        The ReAct (Reasoning and Acting) execution loop.
        Handles the conversational ping-pong of Tool Calling and Observation.
        """
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

        # =====================================================================
        # 2. STANDARD EXECUTION & TOOL LOOP
        # =====================================================================
        active_config = self._get_active_config()
        response = chat_session.send_message(prompt, config=active_config)
        
        tool_loop_count = 0
        MAX_TOOL_LOOPS = 8  # Hard cap on consecutive tool calls per turn to prevent Panic Loops

        while response.function_calls:
            tool_loop_count += 1
            if tool_loop_count > MAX_TOOL_LOOPS:
                print("  -> [SYSTEM WARNING] Infinite tool loop detected. Aborting turn.")
                return "[SYSTEM ERROR] Agent entered an infinite Action-Observation loop. Execution halted."

            tool_responses = []
            for call in response.function_calls:
                print(f"  -> [SYSTEM] {self.agent_name.upper()} executing tool: {call.name}...")
                
                # Execute and Trace
                call_args = dict(call.args) if hasattr(call, 'args') and call.args else {}
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
            response = chat_session.send_message(tool_responses, config=active_config)
            
        final_text = response.text
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