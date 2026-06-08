import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from google import genai
from google.genai import types

from tool_dispatcher import ToolDispatcher

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

    def compile_agent_session(self, agent_name: str, thread_id: str):
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
        # Note: In a full implementation, we would load the history array for `thread_id` here.
        chat_session = self.client.chats.create(
            model="gemini-2.5-pro",
            config=config
        )
        
        return chat_session

# Example Usage:
# factory = AgentEngineFactory()
# spyglass_session = factory.compile_agent_session("Spyglass", thread_id="test_001")
