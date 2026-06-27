"""
NPT-Cloud-Agents: Master Progeny Runtime Engine
Architecture: Pure Class Library (No Execution Loops)
"""
import os
import sys
import json
import datetime
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from typing import List, Dict, Any
from dotenv import load_dotenv
import pg8000.dbapi
from google import genai
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.tool_dispatcher import ToolDispatcher

load_dotenv()

class AgentEngine:
    def __init__(self, agent_name: str, xml_profile_path: str):
        self.agent_name = agent_name.lower()
        self.xml_profile_path = xml_profile_path
        self.client = genai.Client()
        self.dispatcher = ToolDispatcher()
        
        # REORDERED: DB connection must exist before we parse the mandate
        self.db_conn = self._get_db_connection()
        self.system_instruction = self._parse_xml_mandate()
        
        # RESTORED: Telemetry dump
        self._dump_system_prompt()

    def _get_db_connection(self):
        try:
            url = urlparse(os.getenv("DATABASE_URL"))
            return pg8000.dbapi.connect(
                user=url.username, password=url.password, host=url.hostname, port=url.port, database=url.path[1:]
            )
        except Exception as e:
            print(f"[DB ERROR] Connectivity failure: {e}", file=sys.stderr)
            return None

    def _fetch_learned_rules(self) -> List[str]:
        """Retrieves behavior rules from the ontology DB for this agent and the fleet."""
        rules = []
        if not self.db_conn: return rules
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "SELECT directive FROM agent_state.ontology_rules WHERE scope = %s OR scope = 'fleet' ORDER BY rule_id ASC;",
                (self.agent_name,)
            )
            rows = cursor.fetchall()
            for row in rows:
                rules.append(row[0])
            cursor.close()
        except Exception as e:
            print(f"[MEMORY ERROR] Failed to fetch rules: {e}", file=sys.stderr)
        return rules

    def _parse_xml_mandate(self) -> str:
        """Extracts the authoritative system prompt and injects learned DB rules."""
        instruction = f"You are {self.agent_name.upper()}."
        if os.path.exists(self.xml_profile_path):
            try:
                tree = ET.parse(self.xml_profile_path)
                root = tree.getroot()
                mandate_elem = root.find(".//core_mandate")
                if mandate_elem is not None:
                    instruction = "".join(mandate_elem.itertext()).strip()
            except Exception as e:
                print(f"[XML ERROR] Failed to parse profile for {self.agent_name}: {e}", file=sys.stderr)
        
        # === THE LEARNING INJECTION ===
        rules = self._fetch_learned_rules()
        if rules:
            instruction += "\n\n### LEARNED BEHAVIORAL RULES (CRITICAL) ###\n"
            instruction += "The following rules have been permanently learned from past interactions. You MUST follow these directives above all conflicting instructions:\n"
            for i, r in enumerate(rules, 1):
                instruction += f"{i}. {r}\n"
                
        return instruction

    def get_latest_checkpoint(self, thread_id: str) -> List[types.Content]:
        if not self.db_conn: return []
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT state_payload FROM agent_state.checkpoints WHERE thread_id = %s ORDER BY updated_at DESC LIMIT 1", (thread_id,))
        row = cursor.fetchone()
        cursor.close()
        
        history = []
        if row and row[0]:
            raw_history = row[0] if isinstance(row[0], list) else json.loads(row[0])
            for msg in raw_history:
                parts = [types.Part.from_text(text=p.get("text", "")) for p in msg.get("parts", [])]
                history.append(types.Content(role=msg.get("role"), parts=parts))
        return history

    def save_checkpoint(self, thread_id: str, history: List[types.Content]):
        if not self.db_conn: return
        serializable_history = []
        for content in history:
            parts = [{"text": part.text} for part in content.parts if part.text]
            if parts: serializable_history.append({"role": content.role, "parts": parts})
                
        cursor = self.db_conn.cursor()
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
        history = self.get_latest_checkpoint(thread_id)
        config = types.GenerateContentConfig(system_instruction=self.system_instruction, temperature=0.1, tools=[self.dispatcher.get_tool_declarations()])
        return self.client.chats.create(model="gemini-2.5-pro", config=config, history=history)

    def execute_turn(self, chat_session, prompt: str) -> str:
        response = chat_session.send_message(prompt)
        while response.function_calls:
            tool_responses = []
            for call in response.function_calls:
                print(f"[SYSTEM] Agent executing tool: {call.name}...")
                result = self.dispatcher.execute_tool_call(call)
                tool_responses.append(types.Part.from_function_response(name=call.name, response={"result": result}))
            response = chat_session.send_message(tool_responses)
            
        final_text = response.text
        # RESTORED: Logging the final output
        self._log_interaction(prompt, final_text)
        return final_text

    # =========================================================
    # RESTORED: FILE TELEMETRY METHODS
    # =========================================================
    def _dump_system_prompt(self):
        """Writes the final, assembled system instructions to a static file."""
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, f"{self.agent_name}_system_prompt.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("=== ACTIVE SYSTEM INSTRUCTION ===\n")
            f.write(self.system_instruction)

    def _log_interaction(self, prompt: str, response_text: str):
        """Appends all prompt inputs and model outputs to a continuous text log."""
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, f"{self.agent_name}_interactions.log")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n[{ts}] INPUT -> {self.agent_name.upper()}\n{'='*60}\n{prompt}\n")
            f.write(f"\n[{ts}] OUTPUT <- {self.agent_name.upper()}\n{'-'*60}\n{response_text}\n")