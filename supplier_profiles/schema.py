"""Pydantic v2 schema for supplier DRC profiles.

A `SupplierProfile` captures one PCB manufacturer's design rule envelope for a
specific capability tier (e.g. JLCPCB 2-layer FR4). The schema is the contract
between the YAML files in `supplier_profiles/` and the loader/emitter in
`scripts/supplier_drc/`.

Rule values are modelled with explicit `unit` fields so future suppliers using
imperial units don't silently coexist with metric ones. Each numeric rule may
optionally carry a `recommended` value (a safer margin than the absolute
minimum) and a free-form `comment` field for traceability.

Reference: `research/supplier_drc_research.md` "Schema Design Notes" section.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Reusable atomic rule shapes
# ---------------------------------------------------------------------------


class RuleValue(BaseModel):
    """A single numeric rule axis (e.g. min trace width).

    Every rule MUST declare its unit explicitly. Optional `recommended` lets the
    YAML record a safer margin than the absolute minimum; the loader exposes both
    and the DRU emitter uses `value` (the floor). `mil_equiv` is informational
    only — not validated against `value`.
    """

    model_config = ConfigDict(extra="forbid")

    value: float = Field(..., description="Numeric floor / canonical value.")
    unit: Literal["mm", "mil", "oz", "in"] = Field(..., description="Unit of measure.")
    mil_equiv: Optional[float] = Field(
        None, description="Mil equivalent (informational; not auto-derived)."
    )
    recommended: Optional[float] = Field(
        None, description="Safer margin above `value` (optional)."
    )
    cost_grade: Optional[Literal["standard", "premium", "high-premium"]] = Field(
        None, description="Tier label that may incur a cost premium."
    )
    direction: Optional[Literal["per_side", "total"]] = Field(
        None, description="For clearance rules where directionality matters."
    )
    comment: Optional[str] = Field(None, description="Free-form note for traceability.")


class HoleRange(BaseModel):
    """Range constraint for plated/non-plated hole diameters."""

    model_config = ConfigDict(extra="forbid")

    min: float
    max: float
    unit: Literal["mm", "mil"]
    increment: Optional[float] = Field(
        None, description="Smallest fabricator-supported step."
    )
    tolerance: Optional[float] = Field(None, description="+/- tolerance.")
    comment: Optional[str] = None


class BoardDimension(BaseModel):
    """X/Y dimension pair for board size constraints."""

    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    unit: Literal["mm", "mil", "in"]


class ThicknessSpec(BaseModel):
    """Board thickness specification: standard + supported range."""

    model_config = ConfigDict(extra="forbid")

    standard: float
    range: list[float] = Field(..., min_length=2, max_length=2)
    unit: Literal["mm", "mil"]


class CopperWeightSpec(BaseModel):
    """Copper weight specification."""

    model_config = ConfigDict(extra="forbid")

    standard: int
    options: list[int]
    unit: Literal["oz"]


class SurfaceFinishSpec(BaseModel):
    """Surface finish specification."""

    model_config = ConfigDict(extra="forbid")

    standard: str
    options: list[str]


# ---------------------------------------------------------------------------
# 7 nested rule sections
# ---------------------------------------------------------------------------


class TraceRules(BaseModel):
    """Track widths and trace-to-trace spacing, plus copper-to-edge."""

    model_config = ConfigDict(extra="forbid")

    min_trace_width: RuleValue
    min_trace_spacing: RuleValue
    copper_to_edge: RuleValue


class ViaRules(BaseModel):
    """Vias: drill, pad diameter, annular ring, via-to-via, hole ranges."""

    model_config = ConfigDict(extra="forbid")

    min_via_drill: RuleValue
    min_via_pad_diameter: RuleValue
    min_annular_ring: RuleValue
    via_to_via_clearance: RuleValue
    plated_hole_range: HoleRange
    non_plated_hole_min: RuleValue


class PadRules(BaseModel):
    """Pad-to-pad and SMD-specific clearances."""

    model_config = ConfigDict(extra="forbid")

    min_pad_to_pad: RuleValue
    min_smd_clearance: RuleValue


class SolderMaskRules(BaseModel):
    """Solder mask clearance from copper, and minimum web (bridge) width."""

    model_config = ConfigDict(extra="forbid")

    min_mask_clearance: RuleValue
    min_mask_web: RuleValue


class SilkscreenRules(BaseModel):
    """Silkscreen line width, text height, and pad clearance."""

    model_config = ConfigDict(extra="forbid")

    min_line_width: RuleValue
    min_text_height: RuleValue
    clearance_from_pad: RuleValue


class BoardRules(BaseModel):
    """Board-level metadata: thickness, copper weight, size envelope, finish."""

    model_config = ConfigDict(extra="forbid")

    thickness: ThicknessSpec
    copper_weight: CopperWeightSpec
    size_min: BoardDimension
    size_max: BoardDimension
    surface_finish: SurfaceFinishSpec


class DesignRules(BaseModel):
    """Aggregate of the 6 enforceable rule sections."""

    model_config = ConfigDict(extra="forbid")

    trace_rules: TraceRules
    via_rules: ViaRules
    pad_rules: PadRules
    solder_mask_rules: SolderMaskRules
    silkscreen_rules: SilkscreenRules
    board_rules: BoardRules


# ---------------------------------------------------------------------------
# Cost premiums (informational, not enforced as DRU)
# ---------------------------------------------------------------------------


class CostPremium(BaseModel):
    """A single cost-premium trigger."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., description="Human-readable trigger expression.")
    cost_impact: str = Field(..., description='Symbolic cost like "+", "++", "+++".')


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class SupplierMetadata(BaseModel):
    """Identity of the supplier capability profile."""

    model_config = ConfigDict(extra="forbid")

    name: str
    capability_tier: str = Field(
        ..., description="e.g. 'standard-2layer-fr4', 'premium-4layer'."
    )
    last_updated: str = Field(..., description="ISO date the profile was refreshed.")
    source_url: str


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------


class SupplierProfile(BaseModel):
    """One supplier's full DRC envelope.

    YAML files in `supplier_profiles/` deserialize into this model. Pydantic
    enforces presence of every required field and rejects unknown keys at every
    nested level (`extra="forbid"`), which catches typos at load time.
    """

    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., description="Schema version (e.g. '1.0').")
    metadata: SupplierMetadata
    design_rules: DesignRules
    cost_premiums: dict[str, CostPremium] = Field(default_factory=dict)
