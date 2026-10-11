"""
Test Suite: Skills Single Source of Truth (SSOT) Validation
Codified under GEMINI.md Section 2, Section 3.K & SOP-01.

Enforces:
1. Every `<skill_ref>` in every Agent XML must physically exist on disk.
2. Every physical skill in `src/react_agent/skills/` must be referenced by at least one agent XML.
3. No `SKILL.md` file may contain an 'agents:' field in frontmatter (SSOT anti-drift law).
4. Core shared skills are shared across multiple agents.
"""

import os
import unittest
import xml.etree.ElementTree as ET

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENTS_DIR = os.path.join(WORKSPACE_ROOT, "src", "react_agent", "agents")
SKILLS_DIR = os.path.join(WORKSPACE_ROOT, "src", "react_agent", "skills")


def get_all_agents():
    agents = []
    if os.path.exists(AGENTS_DIR):
        for entry in sorted(os.listdir(AGENTS_DIR)):
            xml_path = os.path.join(AGENTS_DIR, entry, f"{entry}.xml")
            if os.path.isfile(xml_path):
                agents.append(entry)
    return agents


def get_xml_skills(agent_name):
    xml_path = os.path.join(AGENTS_DIR, agent_name, f"{agent_name}.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    skills = []
    skills_elem = root.find(".//skills")
    if skills_elem is not None:
        for ref in skills_elem.findall("skill_ref"):
            name = ref.get("name")
            path = ref.get("path")
            skills.append((name, path))
    return skills


class TestSkillsSSOT(unittest.TestCase):

    def test_all_xml_skill_refs_exist_on_disk(self):
        """Verify that every <skill_ref> declared in an agent XML points to an existing SKILL.md."""
        agents = get_all_agents()
        self.assertGreater(len(agents), 0, "No agent XML profiles found.")

        broken_refs = []
        for agent in agents:
            refs = get_xml_skills(agent)
            for s_name, s_path in refs:
                full_path = os.path.join(WORKSPACE_ROOT, s_path)
                if not os.path.isfile(full_path):
                    broken_refs.append(f"Agent [{agent}] references nonexistent skill [{s_name}] at path: {s_path}")

        self.assertFalse(broken_refs, "\n".join(broken_refs))

    def test_no_orphaned_skills_on_disk(self):
        """Verify that every skill directory on disk is referenced by at least one agent XML."""
        agents = get_all_agents()
        referenced_skills = set()
        for agent in agents:
            for s_name, _ in get_xml_skills(agent):
                referenced_skills.add(s_name.replace("_", "-").lower())

        disk_skills = set()
        for entry in os.listdir(SKILLS_DIR):
            skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                disk_skills.add(entry.replace("_", "-").lower())

        orphaned = disk_skills - referenced_skills
        self.assertFalse(orphaned, f"Found orphaned skills on disk not referenced by any agent XML: {orphaned}")

    def test_no_agents_field_in_skill_md_frontmatter(self):
        """Enforce that SKILL.md frontmatters do not contain an 'agents:' field (Anti-Drift Law)."""
        violating_skills = []
        for entry in sorted(os.listdir(SKILLS_DIR)):
            skill_md = os.path.join(SKILLS_DIR, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = parts[1]
                        for line in frontmatter.splitlines():
                            if line.strip().startswith("agents:"):
                                violating_skills.append(entry)
                                break

        self.assertFalse(violating_skills, f"Found 'agents:' field in SKILL.md frontmatter for: {violating_skills}")

    def test_shared_skills_are_shared_across_multiple_agents(self):
        """Verify that core shared skills (e.g. epistemic-value-audit, logic-audit) are shared across multiple agents."""
        skill_agent_map = {}
        agents = get_all_agents()
        for agent in agents:
            for s_name, _ in get_xml_skills(agent):
                norm = s_name.replace("_", "-").lower()
                skill_agent_map.setdefault(norm, []).append(agent)

        critical_shared_skills = [
            "epistemic-value-audit",
            "logic-audit",
            "ship-deck-plans-alignment",
            "audit-academic-crossref-evidence",
            "audit-cargo-seized-evidence",
            "doldrums-breakout",
            "formulate-learned-rule",
        ]

        under_shared = []
        for skill in critical_shared_skills:
            authorized = skill_agent_map.get(skill, [])
            if len(authorized) < 2:
                under_shared.append(f"Skill [{skill}] only assigned to {authorized}, expected multiple agents.")

        self.assertFalse(under_shared, "\n".join(under_shared))


if __name__ == "__main__":
    unittest.main()
