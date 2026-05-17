# Supplier DRC Rules (MANDATORY)

Every board built by this agent is fabricated by a specific PCB supplier. Generic DRC defaults (KiCad's 0.1 mm net-class clearance, hand-picked via drills, no annular-ring rule) are **not enough** — they pass DRC but fail the supplier's DFM screen or trigger cost premiums. This rule binds every routing run to a supplier-anchored DRU file.

**"DRC clean ≠ JLCPCB clean."** A design that passes KiCad's defaults still violates JLCPCB's 0.15 mm annular-ring floor, silk-on-pad screening, or via-tier cost line. The supplier profile makes the difference explicit and enforceable.

## Sequencing

Before ANY routing CLI invocation (`scripts/routing_cli.py`) on a new board:

1. **Pick the supplier.** Read the board's contract front-matter. The `supplier:` field is the authority. If absent, default to `jlcpcb` (documented fallback).
2. **Load the profile.**
   ```python
   from scripts.supplier_drc import load_supplier_profile
   profile = load_supplier_profile(supplier_name)
   ```
3. **Emit the DRU.**
   ```python
   from pathlib import Path
   from scripts.supplier_drc import emit_kicad_dru
   dru_path = emit_kicad_dru(profile, Path("output") / f"{board_name}.kicad_dru")
   ```
4. **Save the DRU next to the `.kicad_pcb`.** KiCad picks up `<board>.kicad_dru` automatically when running DRC against `<board>.kicad_pcb`.
5. **Block routing if the DRU is absent.** If `output/<board>.kicad_dru` does not exist when the routing CLI starts, STOP and emit it before continuing. Do not route against KiCad defaults.

## The 5 risk axes (from research)

These are the supplier-DRC axes the agent must internalise — they are the ones automated designers miss the most. Severity is from `research/supplier_drc_research.md` Risk Callouts section.

| Risk | Severity | Why agents miss it | Mitigation |
|------|----------|--------------------|------------|
| Annular ring undershoot | **HIGH** | Pad auto-sized from drill; agent never validates `(pad − drill)/2`. | DRU `annular_width` constraint + post-route check. |
| Silk-on-pad | **MEDIUM** | Auto-placed reference designators overlap SMD pads. | DRU silk-to-pad clearance + visual inspection of render. |
| Trace-to-via spacing | **MEDIUM** | Generic clearance != via-specific. | Explicit via-trace clearance rule. |
| Copper-to-edge after auto-outline | **MEDIUM** | Outline regeneration invalidates earlier checks. | Re-validate after outline finalise; 0.5 mm safety buffer. |
| Solder mask web < 0.1 mm | **LOW** | Dense pads create slivers. | Post-route validator (`scripts/supplier_drc/validators.py`). |

## Contract integration

Every board contract MUST declare its supplier in front-matter:

```yaml
---
supplier: jlcpcb
layer_count: 2
board_dimensions: 20x30 mm
fr4_thickness: 1.6 mm
copper_weight: 1 oz
surface_finish: HASL (lead-free)
---
```

The board cannot enter the routing phase until the matching `.kicad_dru` is on disk.

## Documented gaps

The DRU covers 7 of the 10 axes the supplier defines. Three are not DRU-expressible and are surfaced as inline `#` comments at the top of the emitted `.kicad_dru`:

- **Solder mask clearance** — KiCad UI-only setting; configure in `Board Setup -> Solder Mask`.
- **Non-plated hole minimum** — external check, v2.x (`scripts/supplier_drc/validators.py::check_non_plated_holes`).
- **Board thickness / copper weight** — metadata only; carried in the contract for the fabrication order, not DRC-checkable.

See `docs/context/supplier-drc.context.md` for the module boundary.
