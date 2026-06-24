import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from google import genai
from google.genai import types
import sys
import pg8000.dbapi
from dotenv import load_dotenv
import uuid
from urllib.parse import urlparse

load_dotenv()
from tool_dispatcher import ToolDispatcher

# =====================================================================
# STATE SAVER: FIXED ARCHITECTURE (Pure JSON Text Persistence)
# =====================================================================

def get_db_connection():
    """Establishes a reliable data connection to our Cloud SQL instance."""
    try:
        url = urlparse(os.getenv("DATABASE_URL"))
        return pg8000.dbapi.connect(
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
            database=url.path[1:]
        )
    except Exception as e:
        print(f"[DB ERROR] Connectivity failure: {e}", file=sys.stderr)
        return None

def get_latest_checkpoint(conn, thread_id: str) -> List[types.Content]:
    """Retrieves and deserializes the JSON state history into GenAI types."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT checkpoint FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    
    historical_messages = []
    if result and result[0]:
        try:
            if isinstance(result[0], list):
                raw_history = result[0]
            elif isinstance(result[0], str):
                raw_history = json.loads(result[0])
            else:
                raw_history = json.loads(result[0].decode('utf-8'))
                
            for turn in raw_history:
                historical_messages.append(
                    types.Content(
                        role=turn["role"],
                        parts=[types.Part.from_text(text=part["text"]) for part in turn["parts"]]
                    )
                )
        except Exception as e:
            print(f"[WARN] Failed deserializing JSON thread history: {e}", file=sys.stderr)
    return historical_messages

def save_checkpoint(conn, thread_id: str, history: List[types.Content]):
    """Commits active text-dialogue checkpoints as clean, human-readable JSON."""
    cursor = conn.cursor()
    new_checkpoint_id = str(uuid.uuid4())
    
    cursor.execute(
        "SELECT checkpoint_id FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    parent_row = cursor.fetchone()
    parent_checkpoint_id = parent_row[0] if parent_row else None

    serializable_history = []
    for msg in history:
        if msg.role in ["user", "model"]:
            text_parts = []
            if msg.parts:
                for part in msg.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append({"text": part.text})
            if text_parts:
                serializable_history.append({"role": msg.role, "parts": text_parts})

    if serializable_history:
        json_str = json.dumps(serializable_history)
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint) VALUES (%s, %s, %s, %s)",
            (thread_id, new_checkpoint_id, parent_checkpoint_id, json_str)
        )
        conn.commit()
    cursor.close()


class AgentEngineFactory:
    """
    The master native factory for the NPT Progeny Fleet.
    Implements the Two-Tier Memory Store (Short-Term Thread History + Long-Term JSON Vault).
    """
    
    def __init__(self):
        self.client = genai.Client()
        self.dispatcher = ToolDispatcher()

    def _load_agent_memory_vault(self, agent_name: str) -> Dict[str, Any]:
        """Reads the agent's permanent, cross-thread JSON storage directory and XML profile."""
        base_path = f"src/react_agent/agents/{agent_name.lower()}"
        profile = {"mandate": "", "lens": {}, "rules": [], "exemplars": [], "requested_tools": []}
        
        # 1. Load XML Profile
        xml_path = f"{base_path}/{agent_name.lower()}.xml"
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            mandate_elem = root.find(".//core_mandate")
            if mandate_elem is not None:
                profile["mandate"] = "".join(mandate_elem.itertext()).strip()
                
            tools_elem = root.find(".//available_tools")
            if tools_elem is not None:
                for tool_node in tools_elem.findall("tool"):
                    t_name = tool_node.get("name")
                    if t_name:
                        profile["requested_tools"].append(t_name)
                
        # 2. Load Cognitive Lens
        lens_path = f"{base_path}/cognitive_lens.json"
        if os.path.exists(lens_path):
            with open(lens_path, 'r') as f:
                profile["lens"] = json.load(f)
                
        # 3. Load Learned Rules
        rules_path = f"{base_path}/learned_rules.json"
        if os.path.exists(rules_path):
            with open(rules_path, 'r') as f:
                profile["rules"] = json.load(f)
                
        # 4. Load Few-Shot Exemplars
        exemplars_path = f"{base_path}/few_shot_exemplars.json"
        if os.path.exists(exemplars_path):
            with open(exemplars_path, 'r') as f:
                profile["exemplars"] = json.load(f)
                
        return profile

    def _build_dynamic_system_prompt(self, agent_name: str, memory: Dict[str, Any]) -> str:
        """Constructs the immutable system instruction block injected at runtime boot."""
        prompt = f"You are {agent_name}.\n\n"

        # =====================================================================
        # DYNAMIC INJECTION: Pull down the system glossary from npt_cargo_db
        # =====================================================================
        try:
            from tool_dispatcher import query_system_glossary
            glossary_text = query_system_glossary()
            if glossary_text:
                prompt += glossary_text + "\n\n"
        except Exception as e:
            prompt += f"[WARN] Glossary wire offline: {str(e)}\n\n"

        if memory.get("mandate"):
            prompt += "=== CORE MANDATE ===\n"
            prompt += memory["mandate"] + "\n\n"
        
        lens = memory.get("lens", {})
        if lens:
            prompt += "=== COGNITIVE LENS & DOMAIN BIAS ===\n"
            prompt += lens.get("domain_bias", "") + "\n\n"
            lexicon = lens.get("strict_lexicon", {})
            if lexicon.get("prioritize"):
                prompt += "PRIORITIZE TERMS: " + ", ".join(lexicon["prioritize"]) + "\n"
            if lexicon.get("reject"):
                prompt += "REJECT TERMS: " + ", ".join(lexicon["reject"]) + "\n\n"
                
        rules = memory.get("rules", [])
        if rules:
            prompt += "=== LEARNED RULES (PERMANENT ALIGNMENT) ===\n"
            for rule in rules:
                prompt += f"- {rule.get('rule_directive', '')} (Source: {rule.get('source_context', '')})\n"
            prompt += "\n"
            
        exemplars = memory.get("exemplars", [])
        if exemplars:
            prompt += "=== FEW-SHOT EXEMPLARS ===\n"
            for ex in exemplars:
                prompt += f"Input Context: {ex.get('input_context', '')}\n"
                prompt += f"Ideal Output: {ex.get('ideal_output', '')}\n"
                prompt += f"Rationale: {ex.get('rationale', '')}\n\n"
                
        return prompt

    def compile_agent_session(self, agent_name: str, thread_id: str, db_conn):
        """Assembles the native Gemini chat session for the specific agent with clean tool constraints."""
        memory = self._load_agent_memory_vault(agent_name)
        system_prompt = self._build_dynamic_system_prompt(agent_name, memory)
        
        requested_tools = memory.get("requested_tools", [])
        bound_tools = []
        
        for tool_block in self.dispatcher.tools:
            if hasattr(tool_block, 'function_declarations') and tool_block.function_declarations:
                matching_decls = [
                    decl for decl in tool_block.function_declarations 
                    if decl.name in requested_tools
                ]
                if matching_decls:
                    bound_tools.append(types.Tool(function_declarations=matching_decls))
        
        tool_config = None
        if bound_tools:
            tool_config = types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(mode="AUTO")
            )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            tools=bound_tools,
            tool_config=tool_config
        )
        
        history = get_latest_checkpoint(db_conn, thread_id)
        return self.client.chats.create(
            model="gemini-2.5-pro",
            config=config,
            history=history if history else []
        )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_engine.py <agent_name> [thread_suffix]")
        sys.exit(1)

    agent_name = sys.argv[1]
    if len(sys.argv) >= 3:
        thread_suffix = sys.argv[2].lower().strip()
        thread_id = f"thread_{agent_name.lower()}_{thread_suffix}"
    else:
        thread_id = f"thread_{agent_name.lower()}_production_sprint"

    db_conn = get_db_connection()
    if not db_conn:
        sys.exit(1)

    factory = AgentEngineFactory()
    chat_session = factory.compile_agent_session(agent_name, thread_id, db_conn)

    initial_memory = factory._load_agent_memory_vault(agent_name)
    initial_system_prompt = factory._build_dynamic_system_prompt(agent_name, initial_memory)

    # =====================================================================
    # GROUNDING AUDIT LOG: Dump the absolute ground-truth system prompt
    # =====================================================================
    with open("src/react_agent/active_system_prompt_compiled.log", "w", encoding="utf-8") as f:
        f.write(initial_system_prompt)
    print(f"[OBSERVABILITY] Compiled system instruction written to active_system_prompt_compiled.log")
    
    requested_tools = initial_memory.get("requested_tools", [])
    bound_tools = []
    for tool_block in factory.dispatcher.tools:
        if hasattr(tool_block, 'function_declarations') and tool_block.function_declarations:
            matching_decls = [d for d in tool_block.function_declarations if d.name in requested_tools]
            if matching_decls:
                bound_tools.append(types.Tool(function_declarations=matching_decls))
            
    tool_config = types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(mode="AUTO")
    ) if bound_tools else None

    active_config = types.GenerateContentConfig(
        system_instruction=initial_system_prompt,
        temperature=0.1,
        tools=bound_tools,
        tool_config=tool_config
    )

    print(f"\n[BOOT] {agent_name.upper()} runtime session synchronized with cloud persistence layer.")
    print(f"[TRACKING REGISTER] Active Thread Context: {thread_id}")
    print("Type 'exit' or 'quit' to end the session block.\n")

    try:
        while True:
            user_input = input(f"({agent_name.upper()}) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break
            
            response = chat_session.send_message(user_input, config=active_config)
            
            while response.function_calls:
                tool_responses = []
                
                for call in response.function_calls:
                    print(f"[{agent_name.upper()} TOOL CALL] Invoking workspace wire: {call.name}...")
                    
                    if hasattr(call, 'args') and 'url' in call.args:
                        clean_url = str(call.args['url']).strip().replace('"', '').replace("'", "").replace('\r', '').replace('\n', '')
                        call.args['url'] = clean_url
                        
                    tool_output_string = factory.dispatcher.dispatch(call)
                    
                    if call.name == "reload_agent_memory_vault":
                        fresh_memory = factory._load_agent_memory_vault(agent_name)
                        fresh_system_prompt = factory._build_dynamic_system_prompt(agent_name, fresh_memory)
                        active_config.system_instruction = fresh_system_prompt
                        print(f"[HOT-RELOAD SUCCESS] Fresh ontology rules successfully injected into {agent_name}'s system prompt.")

                    tool_responses.append(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": tool_output_string}
                        )
                    )
                
                response = chat_session.send_message(tool_responses, config=active_config)
            
            print(f"\n{agent_name.upper()} RESPONSE:\n{response.text}\n")
            save_checkpoint(db_conn, thread_id, chat_session.get_history())

    finally:
        db_conn.close()
        print("[SHUTDOWN] Connection handles successfully released.")