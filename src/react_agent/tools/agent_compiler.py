
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

    def validate_manifest(self, xml_string):
        """
        Validates an XML manifest against the TDD schema.
        Returns True if valid, otherwise raises a ValueError.
        """
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {e}")

        if root.tag != 'agent_definition':
            raise ValueError("Root tag must be 'agent_definition'")

        required_tags = ['identity_persona', 'core_mandate', 'operational_capabilities', 'fiscal_and_technical_governance']
        for tag in required_tags:
            if root.find(tag) is None:
                raise ValueError(f"Missing required tag: '{tag}'")

        return True
