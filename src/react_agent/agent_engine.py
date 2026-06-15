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
    # Pull the binary/text array directly from your provisioned checkpoints schema
    cursor.execute(
        "SELECT checkpoint FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1",
        (thread_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    
    historical_messages = []
    if result and result[0]:
        try:
            # Decode the JSON string array back into type-safe SDK Content blocks
            raw_history = json.loads(result[0] if isinstance(result[0], str) else result[0].decode('utf-8'))
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
        # Keep it as a pure text string! pg8000 maps Python strings seamlessly to PostgreSQL JSONB
        json_str = json.dumps(serializable_history)
        
        cursor.execute(
            "INSERT INTO checkpoints (thread_id, checkpoint_id, parent_checkpoint_id, checkpoint) VALUES (%s, %s, %s, %s)",
            (thread_id, new_checkpoint_id, parent_checkpoint_id, json_str)
        )
        conn.commit()
    cursor.close()
# [... Keeping AgentEngineFactory class code exactly as Hook authored it ...]

class AgentEngineFactory:
    """
    The master native factory for the NPT Progeny Fleet.
    Implements the Two-Tier Memory Store (Short-Term Thread History + Long-Term JSON Vault).
    Utilizes the native google-genai SDK, eliminating LangChain/LangGraph bloat.
    """
    
    def __init__(self):
        """
        Initializes the factory with the native Gemini client and centralized ToolDispatcher.
        """
        self.client = genai.Client()
        self.dispatcher = ToolDispatcher()

    def _load_agent_memory_vault(self, agent_name: str) -> Dict[str, Any]:
        """
        Reads the agent's permanent, cross-thread JSON storage directory and XML profile.
        """
        base_path = f"src/react_agent/agents/{agent_name.lower()}"
        profile = {"mandate": "", "lens": {}, "rules": [], "exemplars": [], "requested_tools": []}
        
        # 1. Load XML Profile (Core Mandate & Tools)
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
                
        # 3. Load Learned Rules (The Teaching Loop)
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
        """
        Constructs the immutable system instruction block injected at runtime boot.
        This prevents cognitive drift by anchoring the model to the human-taught rules.
        """
        prompt = f"You are {agent_name}.\n\n"
        
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

    def _filter_tools(self, requested_tool_names: list[str]) -> list[types.Tool]:
        """
        Filters the master ToolDispatcher list to only include tools requested by the agent's XML.
        """
        filtered_tools = []
        for tool_block in self.dispatcher.tools:
            matching_decls = [
                decl for decl in tool_block.function_declarations 
                if decl.name in requested_tool_names
            ]
            if matching_decls:
                filtered_tools.append(types.Tool(function_declarations=matching_decls))
        return filtered_tools

    def compile_agent_session(self, agent_name: str, thread_id: str, db_conn):
        """
        The Factory Compiler. Assembles the native Gemini chat session for the specific agent.
        """
        # 1. Load Long-Term Memory Vault & Requested Tools
        memory = self._load_agent_memory_vault(agent_name)
        
        # 2. Build the Anti-Drift System Prompt
        system_prompt = self._build_dynamic_system_prompt(agent_name, memory)
        
        # 3. Filter Tools natively
        requested_tools = memory.get("requested_tools", [])
        bound_tools = self._filter_tools(requested_tools)
        
        # 4. Configure the Native Client (Cost-Careful Ceiling Enforced)
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            tools=bound_tools
        )
        
        # 5. Initialize the Native Chat Session
        history = get_latest_checkpoint(db_conn, thread_id)
        
        chat_session = self.client.chats.create(
            model="gemini-2.5-pro",
            config=config,
            history=history if history else []
        )
        
        return chat_session
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agent_engine.py <agent_name>")
        sys.exit(1)

    agent_name = sys.argv[1]
    thread_id = f"thread_{agent_name.lower()}_production_sprint"

    db_conn = get_db_connection()
    if not db_conn:
        sys.exit(1)

    factory = AgentEngineFactory()
    chat_session = factory.compile_agent_session(agent_name, thread_id, db_conn)

    print(f"\n[BOOT] {agent_name} runtime session synchronized with cloud persistence layer.")
    print("Type 'exit' or 'quit' to end the session block.\n")

    try:
        while True:
            user_input = input("({agent_name}) > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break
            
            response = chat_session.send_message(user_input)
            
            # FIXED: Added missing automatic function execution routing block
            while response.function_calls:
                for call in response.function_calls:
                    print(f"[{agent_name} TOOL CALL] Invoking workspace wire: {call.name}...")
                    tool_result = factory.dispatcher.dispatch(call)
                    response = chat_session.send_message(tool_result)
            
            print(f"\n{agent_name.upper()} RESPONSE:\n{response.text}\n")
            
            # FIXED: Updated to use the correct SDK history getter method
            save_checkpoint(db_conn, thread_id, chat_session.get_history())

    finally:
        db_conn.close()
        print("[SHUTDOWN] Connection handles successfully released.")