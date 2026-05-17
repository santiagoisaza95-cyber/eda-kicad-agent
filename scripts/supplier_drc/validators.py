"""External validators for rules not expressible in KiCad DRU.

These check the supplier-specific manufacturability axes that fall outside
KiCad's DRC engine. They are **stubs for v2.0**; full implementations land in
v2.x. Until then they raise `NotImplementedError` so that callers fail loudly
rather than silently treating these axes as passing.

Documented gaps:

- **Solder mask web (`check_solder_mask_web`)** — KiCad's DRC doesn't enforce a
  minimum mask "bridge" between adjacent openings. Below 0.1 mm (JLCPCB floor)
  the web tears during fabrication, leaving exposed copper between pads.
  Detection requires geometric analysis of mask polygons on `F.Mask`/`B.Mask`.

- **Non-plated holes (`check_non_plated_holes`)** — KiCad treats NPTH as a hole
  attribute on pads, but doesn't expose a minimum-diameter DRC rule. Below
  0.5 mm (JLCPCB floor) the fabricator either upcharges or rejects. Detection
  walks all footprints, filters by hole-shape + NPTH attribute, and checks
  drill diameter against `profile.design_rules.via_rules.non_plated_hole_min`.

Both functions are wired into the v2.x post-route validation pass; see
`agent_docs/rules/supplier-drc-rules.md` for sequencing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    """A single supplier-rule violation discovered by an external validator."""

    rule: str
    severity: str  # "error" | "warning"
    message: str
    location: tuple[float, float] | None = None  # (x_mm, y_mm)


def check_solder_mask_web(pcb_path: Path) -> list[Violation]:
    """Inspect F.Mask/B.Mask for sub-threshold web (bridge) widths.

    DEFERRED to v2.x. Currently raises `NotImplementedError`.

    Args:
        pcb_path: Path to a `.kicad_pcb` file.

    Returns:
        List of `Violation`s where mask web < supplier minimum.

    Raises:
        NotImplementedError: Always — implementation deferred to v2.x.
    """
    raise NotImplementedError(
        "check_solder_mask_web is deferred to v2.x; "
        "see scripts/supplier_drc/validators.py docstring for context."
    )


def check_non_plated_holes(pcb_path: Path) -> list[Violation]:
    """Inspect non-plated holes against the supplier's minimum diameter.

    DEFERRED to v2.x. Currently raises `NotImplementedError`.

    Args:
        pcb_path: Path to a `.kicad_pcb` file.

    Returns:
        List of `Violation`s where an NPTH drill < supplier floor.

    Raises:
        NotImplementedError: Always — implementation deferred to v2.x.
    """
    raise NotImplementedError(
        "check_non_plated_holes is deferred to v2.x; "
        "see scripts/supplier_drc/validators.py docstring for context."
    )
