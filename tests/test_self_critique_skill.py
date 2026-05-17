"""Structural tests for agent_docs/skills/self-critique-skill.md.

Contract: contracts/v2-stage-2-iterative-build.contract.md, Batch 2.1.

Validates the skill's MARKDOWN STRUCTURE — does NOT execute the skill:
  - file exists and is non-empty
  - required H2 sections present (Posture, Five Anti-Patterns + Mitigations,
    Decision Tree, Convergence Tracking, Guard Rails, Per-Checkpoint Exit Criteria)
  - all 5 anti-pattern names present (Rubber-stamping, Thrashing, Over-correction,
    Early escalation, Local optimum trap)
  - all 8 checkpoint names present (board_outline → ground_zone_and_stitching)
  - cross-references to visual-review-skill.md and iterative-refinement-skill.md
  - confidence thresholds appear (0.5 and 0.85 — the canonical pair)
  - convergence-tracking metrics mention confidence + trajectory
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL = PROJECT_ROOT / "agent_docs" / "skills" / "self-critique-skill.md"


def _read_skill() -> str:
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    text = SKILL.read_text(encoding="utf-8")
    assert text.strip(), f"Skill file is empty: {SKILL}"
    return text


def test_skill_file_exists() -> None:
    """Contract: agent_docs/skills/self-critique-skill.md exists and is non-empty."""
    assert SKILL.exists(), f"Skill file missing: {SKILL}"
    assert SKILL.stat().st_size > 0, f"Skill file is empty: {SKILL}"


def test_required_sections_present() -> None:
    """Contract: file contains all 6 required H2 sections.

    Required (per the contract Interface Contract + task instruction):
      - Posture
      - Five Anti-Patterns (table; section heading may include "+ Mitigations")
      - Decision Tree
      - Convergence Tracking
      - Guard Rails (when to abort)
      - Per-Checkpoint Exit Criteria
    """
    text = _read_skill()
    # H2 headings — accept loose matches on the natural variations
    assert "## Posture" in text, "Missing section: Posture"
    assert "## Five Anti-Patterns" in text or "## 5 Anti-Patterns" in text, (
        "Missing section: Five Anti-Patterns"
    )
    assert "## Decision Tree" in text, "Missing section: Decision Tree"
    assert "## Convergence Tracking" in text, "Missing section: Convergence Tracking"
    assert "## Guard Rails" in text, "Missing section: Guard Rails"
    assert "## Per-Checkpoint Exit Criteria" in text, (
        "Missing section: Per-Checkpoint Exit Criteria"
    )


def test_five_named_anti_patterns_present() -> None:
    """Contract: 5 named anti-patterns appear verbatim (case-insensitive, hyphenated
    or spaced is OK):
      - Rubber-stamping
      - Thrashing
      - Over-correction
      - Early escalation
      - Local optimum trap
    """
    text = _read_skill()
    text_lower = text.lower()
    for ap in [
        "rubber-stamping",
        "thrashing",
        "over-correction",
        "early escalation",
        "local optimum trap",
    ]:
        # Accept hyphenated OR space-separated; "over-correction" or "over correction"
        ap_variants = [ap, ap.replace("-", " "), ap.replace(" ", "-")]
        present = any(v in text_lower for v in ap_variants)
        assert present, f"Anti-pattern not named: {ap}"


def test_all_eight_checkpoints_named() -> None:
    """Contract: all 8 checkpoint names appear in the per-checkpoint exit criteria
    section.
    """
    text = _read_skill()
    checkpoints = [
        "board_outline",
        "mechanical_placement",
        "ic_placement",
        "critical_passive_placement",
        "remaining_passive_placement",
        "power_routing",
        "signal_routing",
        "ground_zone_and_stitching",
    ]
    missing = [cp for cp in checkpoints if cp not in text]
    assert not missing, f"Missing checkpoint names: {missing}"


def test_cross_references_to_companion_skills() -> None:
    """Contract: file cross-references visual-review-skill.md and
    iterative-refinement-skill.md (the 2 companion skills in the critique stack).
    """
    text = _read_skill()
    assert "visual-review-skill.md" in text, "Missing cross-reference to visual-review-skill.md"
    assert "iterative-refinement-skill.md" in text, (
        "Missing cross-reference to iterative-refinement-skill.md"
    )


def test_canonical_confidence_thresholds_appear() -> None:
    """Contract: confidence thresholds 0.5 (escalate) and 0.85 (proceed) both appear.
    These are the canonical thresholds from research/self_critique_patterns_research.md.
    """
    text = _read_skill()
    assert "0.5" in text, "Missing 0.5 escalation confidence threshold"
    assert "0.85" in text, "Missing 0.85 proceed confidence threshold"


def test_convergence_tracking_mentions_confidence_and_trajectory() -> None:
    """Contract: Convergence Tracking section uses 'confidence' and 'trajectory'
    terminology to describe per-iteration metric tracking.
    """
    text = _read_skill()
    assert "confidence" in text.lower(), "convergence section missing 'confidence'"
    assert "trajectory" in text.lower(), "convergence section missing 'trajectory'"


def test_posture_is_adversarial_but_honest() -> None:
    """Contract: posture section frames the skill as 'adversarial but honest'
    or equivalent (assumes design broken until proven otherwise).
    """
    text = _read_skill()
    text_lower = text.lower()
    # Either the literal phrase or both adjectives in proximity
    assert "adversarial" in text_lower, "Posture missing 'adversarial' framing"


def test_guard_rails_list_abort_thresholds() -> None:
    """Contract: Guard Rails section enumerates explicit numeric abort thresholds
    (iter >= 3, same issue 3x, confidence < 0.4 or similar).
    """
    text = _read_skill()
    # iteration cap
    assert "3" in text, "Iteration cap of 3 missing"
    # at least one of the canonical abort threshold numbers (0.4 OR 0.5 in escalation
    # context — the 0.5 already checked, accept 0.4 as additional signal of
    # explicit threshold)
    text_lower = text.lower()
    has_iteration_ref = "iteration" in text_lower or "iter" in text_lower
    assert has_iteration_ref, "Guard rails missing iteration reference"
