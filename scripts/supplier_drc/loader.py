"""Supplier-profile loader and KiCad `.kicad_dru` emitter.

Public surface:

- `load_supplier_profile(name)` reads `supplier_profiles/<name>.yaml`, validates
  it via Pydantic, and returns a `SupplierProfile` model.
- `emit_kicad_dru(profile, out_path)` writes a KiCad 9.x design-rule file
  containing the 7 DRU-expressible rules (track width, clearance, edge
  clearance, annular ring, via drill, silkscreen line width, silkscreen text
  height) and inline `#` comments documenting the gaps (solder mask clearance,
  non-plated hole minimum, board metadata).

The DRU expression syntax follows
`research/supplier_drc_research.md` "KiCad DRU Mapping" Section.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

import yaml

from supplier_profiles.schema import SupplierProfile

# Repo-root-relative path used to resolve profile YAML files.
PROFILES_DIR = Path(__file__).resolve().parents[2] / "supplier_profiles"


def load_supplier_profile(name: str) -> SupplierProfile:
    """Load and validate `supplier_profiles/<name>.yaml`.

    Args:
        name: Profile name without extension, e.g. ``"jlcpcb"``.

    Returns:
        Validated `SupplierProfile` model.

    Raises:
        FileNotFoundError: If `supplier_profiles/<name>.yaml` does not exist.
        pydantic.ValidationError: If the YAML is malformed against the schema.
    """
    yaml_path = PROFILES_DIR / f"{name}.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(
            f"Supplier profile '{name}' not found at {yaml_path}. "
            f"Available: {sorted(p.stem for p in PROFILES_DIR.glob('*.yaml'))}"
        )
    with yaml_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return SupplierProfile.model_validate(raw)


def _fmt_mm(value: float) -> str:
    """Format a millimetre value the way KiCad's DRU parser expects.

    Trim trailing zeros but always keep at least one digit after the decimal so
    the result reads naturally (e.g. ``0.127mm``, ``0.3mm``, ``1.0mm``).
    """
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    if "." not in text:
        text = f"{text}.0"
    return f"{text}mm"


def _emit_rule(
    fh: TextIO,
    name: str,
    constraint: str,
    value: float,
    condition: str | None = None,
    layer: str | None = None,
    comment: str | None = None,
) -> None:
    """Write one ``(rule ...)`` block to the DRU file."""
    if comment:
        fh.write(f"# {comment}\n")
    fh.write(f'(rule "{name}"\n')
    fh.write(f"    (constraint {constraint} (min {_fmt_mm(value)}))\n")
    if layer is not None:
        fh.write(f'    (layer "{layer}")\n')
    if condition is not None:
        fh.write(f'    (condition "{condition}")\n')
    fh.write(")\n\n")


def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path:
    """Emit a KiCad 9.x `.kicad_dru` file derived from a supplier profile.

    Writes the 7 DRU-expressible rules:

    - track_width            (min trace width)
    - clearance              (min trace-to-trace spacing, scoped to tracks)
    - edge_clearance         (copper-to-edge)
    - annular_width          (min annular ring, scoped to vias)
    - via_diameter           (min via drill, scoped to vias)
    - silk_line_width        (min silkscreen line width)
    - silk_text_height       (min silkscreen text height)

    Documents 3 gaps inline as ``#`` comments at the top of the file:

    - Solder mask clearance is a board-wide UI setting (no DRU equivalent).
    - Non-plated hole minimum is enforced via external validator
      (`scripts/supplier_drc/validators.py::check_non_plated_holes`).
    - Board thickness and copper weight are metadata only — not DRC-checkable.

    Args:
        profile: Validated `SupplierProfile`.
        out_path: Destination `.kicad_dru` file path.

    Returns:
        `out_path` (for caller chaining).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rules = profile.design_rules
    meta = profile.metadata
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with out_path.open("w", encoding="utf-8") as fh:
        # ----- Header --------------------------------------------------------
        fh.write("(version 1)\n\n")
        fh.write(f"# Auto-generated from supplier profile: {meta.name}\n")
        fh.write(f"# Capability tier: {meta.capability_tier}\n")
        fh.write(f"# Source: {meta.source_url}\n")
        fh.write(f"# Profile last updated: {meta.last_updated}\n")
        fh.write(f"# Emitted: {timestamp}\n")
        fh.write("#\n")
        fh.write("# DOCUMENTED GAPS (NOT enforceable as DRU rules):\n")
        fh.write(
            f"#   - Solder mask clearance ({_fmt_mm(rules.solder_mask_rules.min_mask_clearance.value)}, "
            f"{rules.solder_mask_rules.min_mask_clearance.direction or 'per_side'}): native KiCad UI setting only.\n"
        )
        fh.write(
            f"#   - Solder mask web ({_fmt_mm(rules.solder_mask_rules.min_mask_web.value)}): "
            "post-route validator, see scripts/supplier_drc/validators.py.\n"
        )
        fh.write(
            f"#   - Non-plated hole minimum ({_fmt_mm(rules.via_rules.non_plated_hole_min.value)}): "
            "external script check, see scripts/supplier_drc/validators.py.\n"
        )
        fh.write(
            f"#   - Board thickness ({rules.board_rules.thickness.standard} mm) "
            f"and copper weight ({rules.board_rules.copper_weight.standard} oz): "
            "metadata only, not DRC-checkable.\n"
        )
        fh.write("\n")

        # ----- 1. Track width ------------------------------------------------
        _emit_rule(
            fh,
            name="Min Trace Width",
            constraint="track_width",
            value=rules.trace_rules.min_trace_width.value,
            comment=f"Min trace width ({meta.name} {meta.capability_tier})",
        )

        # ----- 2. Trace-to-trace clearance -----------------------------------
        _emit_rule(
            fh,
            name="Min Trace Clearance",
            constraint="clearance",
            value=rules.trace_rules.min_trace_spacing.value,
            condition="A.Type=='track' && B.Type=='track'",
            comment="Trace-to-trace spacing",
        )

        # ----- 3. Copper-to-edge --------------------------------------------
        _emit_rule(
            fh,
            name="Copper To Edge",
            constraint="edge_clearance",
            value=rules.trace_rules.copper_to_edge.value,
            comment="Copper-to-edge keepout",
        )

        # ----- 4. Annular ring (HIGH risk per research) ---------------------
        _emit_rule(
            fh,
            name="Min Annular Ring",
            constraint="annular_width",
            value=rules.via_rules.min_annular_ring.value,
            condition="A.Type=='via'",
            comment="Min annular ring on vias (HIGH risk axis)",
        )

        # ----- 5. Via drill (via diameter constraint in KiCad DRU) ----------
        _emit_rule(
            fh,
            name="Min Via Drill",
            constraint="via_diameter",
            value=rules.via_rules.min_via_drill.value,
            condition="A.Type=='via'",
            comment="Min via drill (premium tier offers smaller at +cost)",
        )

        # ----- 6. Silkscreen line width -------------------------------------
        _emit_rule(
            fh,
            name="Min Silk Line Width",
            constraint="silk_line_width",
            value=rules.silkscreen_rules.min_line_width.value,
            comment="Min silkscreen line width",
        )

        # ----- 7. Silkscreen text height ------------------------------------
        _emit_rule(
            fh,
            name="Min Silk Text Height",
            constraint="silk_text_height",
            value=rules.silkscreen_rules.min_text_height.value,
            comment="Min silkscreen text height (legibility floor)",
        )

    return out_path
