"""Structural tests for agent_docs/skills/iterative-refinement-skill.md.

Contract: contracts/v2-stage-2-iterative-build.contract.md, Batch 2.1.

Validates the skill's MARKDOWN STRUCTURE — does NOT execute the skill:
  - file exists and is non-empty
  - required H2 sections present (Decision Tree, Rework Scope Targeting, Loop Limits,
    Escalation Protocol, Anti-Patterns)
  - max-iteration cap stated as 3 ("3 iterations" or "max 3")
  - token budget stated as 12K or 12,000
  - routing CLI commands referenced (pcb_status, pcb_route, pcb_via, pcb_render, pcb_drc)
  - escalation protocol contains AskUserQuestion + the 0.5 confidence threshold +
    a template/format example
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL = PROJECT_ROOT / "agent_docs" / "skills" / "iterative-refinement-skill.md"


def _read_skill() -> str:
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    text = SKILL.read_text(encoding="utf-8")
    assert text.strip(), f"Skill file is empty: {SKILL}"
    return text


def test_skill_file_exists() -> None:
    """Contract: agent_docs/skills/iterative-refinement-skill.md exists and non-empty."""
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    assert SKILL.stat().st_size > 0, f"Skill file is empty: {SKILL}"


def test_required_sections_present() -> None:
    """Contract: file contains all 5 required H2 sections."""
    text = _read_skill()
    required_sections = [
        "Decision Tree",
        "Rework Scope Targeting",
        "Loop Limits",
        "Escalation Protocol",
        "Anti-Patterns",
    ]
    missing = [s for s in required_sections if f"## {s}" not in text]
    assert not missing, f"Missing required H2 sections: {missing}"


def test_routing_cli_coordination_section_present() -> None:
    """Contract: skill has a routing CLI coordination section (concrete
    pcb_status / pcb_route / pcb_via / pcb_render / pcb_drc references).

    The section may be a distinct H2 or merged with Loop Limits/Rework Scope.
    Either way, the CLI command names below must appear.
    """
    text = _read_skill()
    text_lower = text.lower()
    for cmd in ["pcb_status", "pcb_route", "pcb_via", "pcb_render", "pcb_drc"]:
        assert cmd in text_lower, f"Routing CLI command missing: {cmd}"


def test_max_iteration_cap_documented() -> None:
    """Contract: max-iteration cap of 3 is stated explicitly.

    Acceptable phrasings: "3 iterations", "max 3", "3 (firm)", etc.
    """
    text = _read_skill()
    text_lower = text.lower()
    # The contract spec accepts "3 iterations" OR "max 3"
    assert "3 iterations" in text_lower or "max 3" in text_lower, (
        "Max-iteration cap of 3 not documented (need '3 iterations' or 'max 3')"
    )


def test_token_budget_documented() -> None:
    """Contract: ~12K token-per-cycle budget is stated.

    Acceptable phrasings: "12K", "12,000", "~12K".
    """
    text = _read_skill()
    assert "12K" in text or "12,000" in text or "12k" in text.lower(), (
        "Token budget (12K / 12,000) per cycle not documented"
    )


def test_escalation_uses_askuserquestion_and_0_5_threshold() -> None:
    """Contract: escalation protocol references AskUserQuestion AND the
    0.5 confidence threshold from research.
    """
    text = _read_skill()
    assert "AskUserQuestion" in text, "AskUserQuestion not referenced in escalation protocol"
    assert "0.5" in text, "0.5 escalation confidence threshold not documented"
    assert "confidence" in text.lower(), "confidence discipline not documented"


def test_escalation_protocol_has_template() -> None:
    """Contract: escalation protocol contains a template/format example for the
    AskUserQuestion call. Detection: a fenced code block in the same vicinity
    as the AskUserQuestion reference, OR an explicit options list with id/label
    pairs.
    """
    text = _read_skill()
    # A code fence near AskUserQuestion suggests a template
    has_fence = "```" in text
    assert has_fence, "No fenced code block in skill (escalation template expected)"
    # Options pattern: id + label (canonical AUQ option format)
    assert '"id"' in text or "'id'" in text, "AskUserQuestion options template (id field) missing"
    assert '"label"' in text or "'label'" in text, "AskUserQuestion options template (label field) missing"


def test_decision_tree_has_three_outcomes() -> None:
    """Contract: Decision Tree distinguishes proceed / rework / escalate."""
    text = _read_skill()
    text_lower = text.lower()
    assert "proceed" in text_lower, "Decision Tree missing 'proceed' outcome"
    assert "rework" in text_lower, "Decision Tree missing 'rework' outcome"
    assert "escalate" in text_lower, "Decision Tree missing 'escalate' outcome"


def test_rework_scope_targeting_is_table() -> None:
    """Contract: Rework Scope Targeting section is a markdown table mapping
    issue type → action → tool.
    """
    text = _read_skill()
    # Find the "Rework Scope Targeting" section
    section_anchor = "## Rework Scope Targeting"
    assert section_anchor in text, "Rework Scope Targeting section not found"
    # Section content should contain table separators in the immediate vicinity
    section_idx = text.find(section_anchor)
    section_body = text[section_idx : section_idx + 3000]
    assert "|" in section_body and "---" in section_body, (
        "Rework Scope Targeting section does not contain a markdown table"
    )


def test_anti_patterns_section_lists_loop_pathologies() -> None:
    """Contract: Anti-Patterns section lists at least 3 named pathologies
    from the research catalog (local optimum, thrashing, token explosion).
    """
    text = _read_skill()
    text_lower = text.lower()
    # The research's 5 anti-patterns include these
    flagged = sum(
        1
        for ap in ["local optimum", "thrashing", "token explosion", "over-correction", "early escalation"]
        if ap in text_lower
    )
    assert flagged >= 3, f"Expected ≥3 named anti-patterns, found {flagged}"
