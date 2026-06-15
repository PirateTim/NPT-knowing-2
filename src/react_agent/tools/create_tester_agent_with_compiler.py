
import xml.etree.ElementTree as ET
from xml.dom import minidom

class AgentCompiler:
    def __init__(self):
        pass

    def _to_pretty_xml(self, element):
        """
        Returns a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def generate_manifest(self, agent_data):
        """
        Generates an agent XML manifest from a dictionary.
        """
        root = ET.Element('agent_definition')
        
        # Identity Persona
        identity_persona = ET.SubElement(root, 'identity_persona')
        ET.SubElement(identity_persona, 'name').text = agent_data.get('name', '')
        ET.SubElement(identity_persona, 'role').text = agent_data.get('role', '')
        ET.SubElement(identity_persona, 'disposition').text = agent_data.get('disposition', '')
        ET.SubElement(identity_persona, 'expertise').text = agent_data.get('expertise', '')
        
        # Core Mandate
        core_mandate = ET.SubElement(root, 'core_mandate')
        ET.SubElement(core_mandate, 'do_not_lie').text = agent_data.get('do_not_lie', '')
        ET.SubElement(core_mandate, 'primary_directive').text = agent_data.get('primary_directive', '')
        ET.SubElement(core_mandate, 'separation_of_concerns').text = agent_data.get('separation_of_concerns', '')
        ET.SubElement(core_mandate, 'epistemic_validation_rules').text = agent_data.get('epistemic_validation_rules', '')

        # Operational Capabilities
        operational_capabilities = ET.SubElement(root, 'operational_capabilities')
        available_tools = ET.SubElement(operational_capabilities, 'available_tools')
        for tool in agent_data.get('tools', []):
            ET.SubElement(available_tools, 'tool', attrib=tool)
        ET.SubElement(operational_capabilities, 'backlog_management_protocol').text = agent_data.get('backlog_management_protocol', '')

        # Fiscal and Technical Governance
        fiscal_and_technical_governance = ET.SubElement(root, 'fiscal_and_technical_governance')
        ET.SubElement(fiscal_and_technical_governance, 'charter_supremacy').text = agent_data.get('charter_supremacy', '')
        ET.SubElement(fiscal_and_technical_governance, 'cost_careful_ceiling').text = agent_data.get('cost_careful_ceiling', '')
        ET.SubElement(fiscal_and_technical_governance, 'human_verification_gate').text = agent_data.get('human_verification_gate', '')

        return self._to_pretty_xml(root)

ag_compiler = AgentCompiler()

agent_data = {
    "name": "Tester",
    "role": "Test Agent",
    "disposition": "Structural Finality. Omniscient system optimization. Progenitor of specialists.",
    "expertise": "Testing",
    "do_not_lie": "Do not make stuff up or lie to the user ever. If a tool output returns a fault, log the exact error payload natively.",
    "primary_directive": "Test new functionality.",
    "separation_of_concerns": "Hook builds the pipes; Specialist Agents master the content. Hook understands data structure and provenance for the purpose of building Agents and the required routing infrastructure, but delegates semantic organization and interpretation to the agents.",
    "epistemic_validation_rules": "",
    "tools": [
        {
            "type": "native",
            "name": "post_github_comment",
            "capability": "Append status logs directly to active issues"
        },
        {
            "type": "native",
            "name": "github_poster",
            "capability": "Posts a comment to a GitHub issue with the agent's name prepended to the body."
        }
    ],
    "backlog_management_protocol": "",
    "charter_supremacy": "Infrastructure deployments must align with the core optimization tenets of the master Project Charter.",
    "cost_careful_ceiling": "Enforce a low-variance temperature configuration across all generated sub-agents to minimize resource waste.",
    "human_verification_gate": ""
}

manifest = ag_compiler.generate_manifest(agent_data)

with open("src/react_agent/agents/tester.xml", "w") as f:
    f.write(manifest)
