"""Tests for the supplier DRC profile subsystem.

Covers:
- schema loads and is importable
- jlcpcb.yaml validates and value invariants from the contract hold
- emit_kicad_dru writes a non-empty DRU file containing the expected
  constraint kinds
- unknown supplier name raises FileNotFoundError
- malformed YAML raises pydantic.ValidationError
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

# Ensure repo root is on sys.path so absolute imports work regardless of how
# pytest is invoked.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.supplier_drc import emit_kicad_dru, load_supplier_profile  # noqa: E402
from supplier_profiles.schema import SupplierProfile  # noqa: E402


def test_schema_loads() -> None:
    """SupplierProfile schema is importable and has the documented nested sections."""
    # Surface-level check: top-level fields exist on the model.
    fields = SupplierProfile.model_fields
    assert "version" in fields
    assert "metadata" in fields
    assert "design_rules" in fields
    assert "cost_premiums" in fields

    # Design-rules contains the 6 enforceable rule sections.
    design_rules_model = SupplierProfile.model_fields["design_rules"].annotation
    design_fields = set(design_rules_model.model_fields.keys())
    expected = {
        "trace_rules",
        "via_rules",
        "pad_rules",
        "solder_mask_rules",
        "silkscreen_rules",
        "board_rules",
    }
    assert expected.issubset(design_fields), (
        f"Missing rule sections: {expected - design_fields}"
    )


def test_jlcpcb_profile_valid() -> None:
    """jlcpcb.yaml loads and value invariants from the contract hold."""
    profile = load_supplier_profile("jlcpcb")

    assert isinstance(profile, SupplierProfile)
    assert profile.metadata.name == "JLCPCB"
    assert profile.metadata.capability_tier == "standard-2layer-fr4"

    dr = profile.design_rules
    # The 12 value invariants from the Batch 1.2 contract.
    assert dr.trace_rules.min_trace_width.value == 0.127
    assert dr.trace_rules.min_trace_spacing.value == 0.127
    assert dr.trace_rules.copper_to_edge.value == 0.3
    assert dr.via_rules.min_via_drill.value == 0.3
    assert dr.via_rules.min_via_pad_diameter.value == 0.6
    assert dr.via_rules.min_annular_ring.value == 0.15
    assert dr.via_rules.min_annular_ring.recommended == 0.2
    assert dr.silkscreen_rules.min_line_width.value == 0.15
    assert dr.silkscreen_rules.min_text_height.value == 1.0
    assert dr.solder_mask_rules.min_mask_clearance.value == 0.05
    assert dr.solder_mask_rules.min_mask_clearance.direction == "per_side"
    assert dr.solder_mask_rules.min_mask_web.value == 0.1
    assert dr.board_rules.thickness.standard == 1.6
    assert dr.board_rules.copper_weight.standard == 1

    # Units must be explicit on every rule axis (spot-check three).
    assert dr.trace_rules.min_trace_width.unit == "mm"
    assert dr.via_rules.min_via_drill.unit == "mm"
    assert dr.silkscreen_rules.min_line_width.unit == "mm"


def test_emit_dru(tmp_path: Path) -> None:
    """emit_kicad_dru writes a non-empty DRU file containing the expected constraint kinds."""
    profile = load_supplier_profile("jlcpcb")
    out_path = tmp_path / "jlcpcb.kicad_dru"
    returned = emit_kicad_dru(profile, out_path)

    # Function returns the written path.
    assert returned == out_path
    assert out_path.exists()
    assert out_path.stat().st_size > 0

    content = out_path.read_text(encoding="utf-8")

    # Header
    assert content.startswith("(version 1)")
    assert "JLCPCB" in content

    # The 7 DRU-expressible constraint kinds from research Section 3.
    for constraint in (
        "track_width",
        "clearance",
        "edge_clearance",
        "annular_width",
        "via_diameter",
        "silk_line_width",
        "silk_text_height",
    ):
        assert constraint in content, f"missing constraint: {constraint}"

    # Spot-check that the JLCPCB-specific values are emitted.
    assert "0.127mm" in content  # min trace width
    assert "0.3mm" in content    # copper-to-edge / min via drill
    assert "0.15mm" in content   # min annular ring / silk line width
    assert "1.0mm" in content    # silk text height

    # Documented gaps are present as comments.
    assert "Solder mask clearance" in content
    assert "Non-plated hole" in content

    # Track-track condition is present
    assert "A.Type=='track'" in content
    # Via-scoped rules are conditioned on via type
    assert "A.Type=='via'" in content


def test_unknown_supplier_raises() -> None:
    """load_supplier_profile raises FileNotFoundError for an unknown name."""
    with pytest.raises(FileNotFoundError):
        load_supplier_profile("definitely_not_a_real_supplier_xyz")


def test_malformed_yaml_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A YAML that doesn't satisfy the schema raises pydantic.ValidationError."""
    # Point the loader at a tmp profiles dir we control.
    import scripts.supplier_drc.loader as loader_mod

    bad_dir = tmp_path / "supplier_profiles"
    bad_dir.mkdir()
    bad_yaml = bad_dir / "broken.yaml"

    # Missing required fields (no metadata, no design_rules).
    bad_yaml.write_text(
        yaml.safe_dump({"version": "1.0", "metadata": {"name": "broken"}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(loader_mod, "PROFILES_DIR", bad_dir)

    with pytest.raises(ValidationError):
        load_supplier_profile("broken")
