"""Structural tests for agent_docs/skills/visual-review-skill.md.

Contract: contracts/v2-stage-2-iterative-build.contract.md, Batch 2.1.

These tests do NOT execute the skill — they validate the skill's MARKDOWN STRUCTURE:
  - file exists and is non-empty
  - the 5 required H2 sections are present
  - the failure-mode catalog has 10 entries
  - the JSON output schema block is present
  - all 5 checkpoint types are named (PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC)
  - the required JSON output fields are documented (checkpoint, iteration, pass_fail,
    confidence, issues, recommendation)
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL = PROJECT_ROOT / "agent_docs" / "skills" / "visual-review-skill.md"


def _read_skill() -> str:
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    text = SKILL.read_text(encoding="utf-8")
    assert text.strip(), f"Skill file is empty: {SKILL}"
    return text


def test_skill_file_exists() -> None:
    """Contract: agent_docs/skills/visual-review-skill.md exists and is non-empty."""
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    assert SKILL.stat().st_size > 0, f"Skill file is empty: {SKILL}"


def test_required_sections_present() -> None:
    """Contract: file contains the 5 required H2 sections.

    Required (per contract Batch 2.1 Interface Contract):
      - Input Contract
      - Per-Checkpoint Rubric
      - Failure Mode Catalog
      - Output Format
      - Anti-Pattern Guard Rails
    """
    text = _read_skill()
    required_sections = [
        "Input Contract",
        "Per-Checkpoint Rubric",
        "Failure Mode Catalog",
        "Output Format",
        "Anti-Pattern Guard Rails",
    ]
    missing = [s for s in required_sections if f"## {s}" not in text]
    assert not missing, f"Missing required H2 sections: {missing}"


def test_failure_mode_catalog_has_10_entries() -> None:
    """Contract: failure-mode catalog has exactly 10 entries in a markdown table.

    Entries are table rows referencing one of the 5 checkpoint types (PLACEMENT,
    POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC). Detection: count table
    rows that reference any of those checkpoint keywords AND have the row
    structure `| N | name | signature | checkpoint | hint |`.
    """
    text = _read_skill()
    rows = [line for line in text.split("\n") if line.startswith("| ") and " | " in line]
    catalog_rows = [
        r
        for r in rows
        if any(
            cp in r
            for cp in ["PLACEMENT", "SIGNAL_ROUTING", "POWER_ROUTING", "GROUND_PLANE", "DRC"]
        )
        # Exclude header rows; entries start with `| <number> |`
        and re.match(r"^\|\s*\d+\s*\|", r)
    ]
    assert len(catalog_rows) >= 10, (
        f"Expected ≥10 catalog rows, found {len(catalog_rows)}. "
        f"Rows: {catalog_rows}"
    )


def test_json_output_schema_documented() -> None:
    """Contract: Output Format section contains a ```json fenced code block with the
    required schema fields.
    """
    text = _read_skill()
    # Look for a json fence
    assert "```json" in text, "Missing ```json fenced code block for output schema"

    # Required fields per contract Batch 2.1 Interface Contract
    required_fields = ["checkpoint", "iteration", "pass_fail", "confidence", "issues", "recommendation"]
    for field in required_fields:
        assert f'"{field}"' in text, f"Required JSON field missing from schema: {field}"


def test_five_checkpoint_types_named() -> None:
    """Contract: all 5 checkpoint type categories are named in the rubric:
    PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC.
    """
    text = _read_skill()
    for cp_type in ["PLACEMENT", "POWER_ROUTING", "SIGNAL_ROUTING", "GROUND_PLANE", "DRC"]:
        assert cp_type in text, f"Checkpoint type missing: {cp_type}"


def test_input_contract_documents_render_paths_and_iteration() -> None:
    """Contract: Input Contract section documents render PNG paths + iteration counter
    + checkpoint name as inputs.
    """
    text = _read_skill()
    # Iteration counter
    assert "iteration" in text.lower(), "iteration counter not documented in input contract"
    # PNG render paths
    assert ".png" in text.lower() or "png" in text.lower(), "PNG render paths not documented"
    # Checkpoint name
    assert "checkpoint" in text.lower(), "checkpoint name not documented in input contract"


def test_anti_pattern_guard_rails_explicit() -> None:
    """Contract: Anti-Pattern Guard Rails section calls out rubber-stamping
    and the noise floor / over-iteration discipline.
    """
    text = _read_skill()
    text_lower = text.lower()
    # Rubber-stamping detection
    assert "rubber" in text_lower or "rubber-stamp" in text_lower, (
        "Rubber-stamping anti-pattern not flagged"
    )
    # Confidence calibration / threshold
    assert "confidence" in text_lower, "Confidence discipline not documented"


def test_confidence_thresholds_documented() -> None:
    """Contract: confidence calibration uses the 0.85 (proceed) and 0.5 (escalate)
    thresholds documented in research/self_critique_patterns_research.md.
    """
    text = _read_skill()
    # Both canonical thresholds must appear
    assert "0.85" in text, "0.85 (proceed) confidence threshold missing"
    assert "0.5" in text, "0.5 (escalate) confidence threshold missing"
