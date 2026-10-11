"""
Unit Test: Folksonomy-to-DeckPlans Bridge & Dynamic Resolver
Verifies that the normalized bridge correctly indexes edges and joins live metadata
from ship_deck_plans.json and fleet_folksonomy.json.
"""
import os
import sys
import json
import tempfile

# Ensure src/react_agent is on path
sys.path.append(os.path.abspath("src/react_agent"))

from tools.folksonomy_bridge import FolksonomyDeckPlanBridge, query_folksonomy_deckplan_bridge

def test_bridge_dynamic_resolution():
    print("=" * 60)
    print("TEST: FolksonomyDeckPlanBridge Dynamic Resolution")
    print("=" * 60)

    # Create a temporary edges file for testing
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tmp:
        sample_payload = {
            "version": "1.0-test",
            "edge_count": 3,
            "edges": [
                {
                    "tag": "#early_childhood_literacy",
                    "section_id": "10.5",
                    "score": 0.95,
                    "warrant": "Exemplifies Coleman's 70/30 mandate liquidating narrative literacy."
                },
                {
                    "tag": "#early_childhood_literacy",
                    "section_id": "10.6",
                    "score": 0.88,
                    "warrant": "Connects early reading pedagogy to the loss of recursive syntax."
                },
                {
                    "tag": "#fair_use_doctrine",
                    "section_id": "6.1",
                    "score": 0.97,
                    "warrant": "Exemplifies the judicial destruction of fair use as a legal shield."
                }
            ],
            "unmapped_tags": [
                {
                    "tag": "#international_criminal_court",
                    "reason": "Outside manuscript scope."
                }
            ]
        }
        json.dump(sample_payload, tmp, indent=2)
        tmp_path = tmp.name

    try:
        bridge = FolksonomyDeckPlanBridge(edges_path=tmp_path)
        
        # 1. Test get_sections_for_tag
        sec_results = bridge.get_sections_for_tag("#early_childhood_literacy")
        assert len(sec_results) == 2, f"Expected 2 sections, got {len(sec_results)}"
        assert sec_results[0]["section_id"] == "10.5"
        assert sec_results[0]["chapter_number"] == 10
        assert "David Coleman" in sec_results[0]["operative_actor"]
        assert sec_results[0]["relevance_score"] == 0.95
        print(f"  [PASS] get_sections_for_tag('#early_childhood_literacy') -> Matched {len(sec_results)} sections:")
        for s in sec_results:
            print(f"         - Sec {s['section_id']}: '{s['section_title'][:45]}...' (Score: {s['relevance_score']})")

        # 2. Test get_tags_for_section
        tag_results = bridge.get_tags_for_section("10.5")
        assert len(tag_results) == 1, f"Expected 1 tag, got {len(tag_results)}"
        assert tag_results[0]["tag"] == "#early_childhood_literacy"
        assert tag_results[0]["theme_id"] == "child_cognitive_development"
        assert tag_results[0]["theme_name"] == "Child Cognitive Development"
        print(f"  [PASS] get_tags_for_section('10.5') -> Matched {len(tag_results)} tags:")
        for t in tag_results:
            print(f"         - Tag: {t['tag']} | Theme: {t['theme_name']} (Score: {t['relevance_score']})")

        # 3. Test get_chapter_tags
        ch_results = bridge.get_chapter_tags(10)
        assert ch_results["chapter_number"] == 10
        assert ch_results["total_associated_tags"] >= 1
        print(f"  [PASS] get_chapter_tags(10) -> Found {ch_results['total_associated_tags']} unique tags in Chapter 10.")

        # 4. Test tool function
        tool_out = query_folksonomy_deckplan_bridge("tag", "#fair_use_doctrine")
        parsed_tool = json.loads(tool_out)
        # Note: tool function uses default edges path, but function loads properly without crash
        assert "match_count" in parsed_tool or "error" not in parsed_tool
        print(f"  [PASS] query_folksonomy_deckplan_bridge callable returned valid JSON.")

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    print("\nALL UNIT TESTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    test_bridge_dynamic_resolution()
