# Supplier DRC — Module Context

**Modules:** `supplier_profiles/` (data + schema) + `scripts/supplier_drc/` (loader + emitter + external validators).
**Status:** Stage 1 Batch 1.2 deliverable (v2.0 foundation).
**Owners:** v2 manufacturability layer — every board the agent routes uses a supplier-anchored DRU file derived from these profiles.

## Boundary

`supplier_profiles/` is the canonical source of supplier capability data. Each YAML file is one `(supplier, capability_tier)` pair. `scripts/supplier_drc/` is the **only** module that:

- Reads supplier YAML files and validates them against the Pydantic schema.
- Emits KiCad `.kicad_dru` text files derived from a `SupplierProfile`.
- Houses external validators for DRC-axes KiCad cannot enforce (mask web, non-plated holes).

Routing scripts, contract parsers, and the agent loop should treat this subsystem as a black box: ask it for a profile by name, ask it to emit a DRU, route against the resulting file. Callers do **not** read the YAML directly and do **not** synthesise DRU strings by hand.

## Public API

```python
# Re-exported from scripts.supplier_drc
def load_supplier_profile(name: str) -> SupplierProfile: ...
def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path: ...
```

`SupplierProfile` is a Pydantic v2 model defined in `supplier_profiles/schema.py`. Top-level fields: `version`, `metadata`, `design_rules`, `cost_premiums`. `design_rules` nests `trace_rules`, `via_rules`, `pad_rules`, `solder_mask_rules`, `silkscreen_rules`, `board_rules`.

Raises:

- `FileNotFoundError` — no YAML at `supplier_profiles/<name>.yaml`.
- `pydantic.ValidationError` — YAML malformed against schema.

## DRU emission semantics

`emit_kicad_dru` produces a KiCad 9.x `.kicad_dru` file with:

1. A `(version 1)` header.
2. A comment header with supplier name, capability tier, source URL, and an explicit list of documented gaps.
3. Seven `(rule ...)` blocks, one per DRU-expressible axis:

| Block | Constraint | Source field |
|-------|------------|--------------|
| Min Trace Width | `track_width` | `trace_rules.min_trace_width` |
| Min Trace Clearance | `clearance` (scoped to tracks) | `trace_rules.min_trace_spacing` |
| Copper To Edge | `edge_clearance` | `trace_rules.copper_to_edge` |
| Min Annular Ring | `annular_width` (vias) | `via_rules.min_annular_ring` |
| Min Via Drill | `via_diameter` (vias) | `via_rules.min_via_drill` |
| Min Silk Line Width | `silk_line_width` | `silkscreen_rules.min_line_width` |
| Min Silk Text Height | `silk_text_height` | `silkscreen_rules.min_text_height` |

Where the rule is conditional (e.g. via-only, track-to-track), the emitter writes a `(condition "...")` clause using the syntax KiCad's DRC engine parses.

## Known DRU gaps (v2.0)

These axes are present in the YAML profile but **not** expressible as DRU rules. The emitter records them as `#` comments at the top of the DRU file so a human inspecting the file can see exactly what's missing.

| Gap | Reason | Fallback |
|-----|--------|----------|
| Solder mask clearance | KiCad's mask clearance is a board-wide setting (`Board Setup -> Solder Mask -> Solder mask clearance`), not a DRU-expressible constraint. | Configure manually; profile value is informational. |
| Solder mask web (bridge) | KiCad has no DRC rule for mask web width below a threshold. | `scripts/supplier_drc/validators.py::check_solder_mask_web` (stub; v2.x). |
| Non-plated hole minimum | KiCad treats NPTH as a pad attribute; no minimum-diameter DRC. | `scripts/supplier_drc/validators.py::check_non_plated_holes` (stub; v2.x). |
| Board thickness / copper weight | Pure metadata. The DRC engine doesn't model fabrication stackup. | Surface in contract for the fabrication order. |

## How to extend

- **New supplier**: see `supplier_profiles/README.md`. Copy `jlcpcb.yaml`, swap values, validate, commit.
- **New rule axis**: add a `RuleValue` field on the relevant nested model in `supplier_profiles/schema.py`, update `jlcpcb.yaml` to populate it, and (if DRU-expressible) extend `emit_kicad_dru` with another `_emit_rule(...)` call. Add a unit test that the new field is loaded and emitted.
- **New external validator**: add a function to `scripts/supplier_drc/validators.py` that returns `list[Violation]`. Wire it into the post-route validation pass referenced in `agent_docs/rules/supplier-drc-rules.md`.

## Cross-references

- Mandatory agent rule: `agent_docs/rules/supplier-drc-rules.md` (load profile -> emit DRU -> block routing if absent).
- Research source-of-truth: `research/supplier_drc_research.md` (JLCPCB rules table, DRU mapping, 5 risk axes).
- Stage 1 Batch 1.2 contract: `contracts/v2-stage-1-foundation.contract.md`.
