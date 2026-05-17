---
supplier: jlcpcb
layer_count: 2
board_dimensions: 10x10 mm
fr4_thickness: 1.6 mm
copper_weight: 1 oz
surface_finish: HASL (lead-free)
---

# Stub Contract: _dryrun (NOT for production build)

> **NOTE:** This is a v2 integration verification stub. Do **NOT** build this board.
> It exists only to validate the Stage 2 skill wiring (journal protocol, inline
> reviewer gates at checkpoints 4 + 6, AskUserQuestion milestones at boundaries
> of checkpoints 4 / 5 / 7, skill load order, supplier-DRC gate). The leading
> underscore in `_dryrun_stub.md` flags this as a non-production artifact. The
> companion verification trace lives at `docs/auditions/_stage2_dryrun_log.md`.

**Version:** 0.1 (verification fixture)
**Board Name:** _dryrun_stub
**Output File (HYPOTHETICAL):** `output/_dryrun_stub.kicad_pcb`
**Purpose:** Wiring test fixture only. Drives a trace through `pcb-design-skill.md`'s
8-checkpoint state machine so we can verify the 5 v2 integration points fire
in the right order. NEVER touched by an actual build agent.

---

## DESIGN FROM THIS CONTRACT ONLY

If, hypothetically, an agent were to design this board, it MUST NOT:

- Use `WebSearch` or `WebFetch` to look up reference layouts
- Read any files in the `reference/` directory
- Browse GitHub or any website for existing designs
- Open or read `baselines/4.6/*.kicad_pcb` for "inspiration"

It MUST design entirely from this contract + skills in `agent_docs/skills/` +
rules in `agent_docs/rules/` (especially `supplier-drc-rules.md`) + supplier
profile at `supplier_profiles/jlcpcb.yaml` + `api_manifest.json`.

This is a controlled verification stub. The clause is kept verbatim so the
contract front-matter parser at `pcb-design-skill.md` precondition 1 finds the
expected anchor.

---

## Board Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 10.0 mm × 10.0 mm (rectangle) |
| Layers | 2 (F.Cu = signal, B.Cu = GND zone) |
| Thickness | 1.6 mm FR4 |
| Copper weight | 1 oz (35 µm) |
| Surface finish | HASL (lead-free) |
| Min hole-to-edge | per JLCPCB profile (≥ 0.3 mm copper-to-edge) |

---

## Components (5 items — minimum to exercise the 8-checkpoint flow)

| Ref | Value | Footprint | Purpose |
|-----|-------|-----------|---------|
| U1 | Generic SOT-23 IC | Package_TO_SOT_SMD:SOT-23 | Exercises checkpoint 3 (ic_placement) |
| R1 | 10k | Resistor_SMD:R_0603_1608Metric | Pull-up; VCC → OUT |
| R2 | 10k | Resistor_SMD:R_0603_1608Metric | Pull-down; OUT → GND |
| C1 | 100nF | Capacitor_SMD:C_0603_1608Metric | Bypass cap; VCC ↔ GND (exercises checkpoint 4 decoupling proximity rubric) |
| J1 | 2-pin 2.54mm header | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical | Power input (exercises checkpoint 2 mechanical_placement at edge) |

---

## Netlist (3 nets — minimum to exercise checkpoint 6 + 7)

| Net Name | Connections |
|----------|-------------|
| VCC | J1.1, R1.1, C1.1, U1.1 |
| GND | J1.2, R2.2, C1.2, U1.2 |
| OUT  | R1.2, R2.1, U1.3 |

Net summary:
- **VCC** (power, ≥0.5 mm trace) — power-routing checkpoint (CP6) target
- **GND** (power, ≥0.5 mm trace) — power-routing + GND zone (CP6 + CP8) target
- **OUT** (signal, 0.25 mm trace) — signal-routing checkpoint (CP7) target

This 3-net topology is the **minimum** that exercises:
- CP6 power_routing (VCC + GND)
- CP7 signal_routing (OUT)
- CP8 ground_zone_and_stitching (GND on B.Cu)

---

## Design Rules — Reference, Don't Duplicate

The authoritative DRC numbers come from `supplier_profiles/jlcpcb.yaml` loaded
via `scripts/supplier_drc/loader.py::load_supplier_profile("jlcpcb")` and
emitted to `output/_dryrun_stub.kicad_dru` via `emit_kicad_dru(profile, ...)`
**before** any routing checkpoint (CP6 onward). This is the Gate 2 sequence
documented in `CLAUDE.md`.

Suggested working trace widths (within JLCPCB minimums):
- Signal traces (OUT): 0.25 mm
- Power traces (VCC, GND on F.Cu): 0.5 mm
- B.Cu GND zone fills remaining ground return; copper-to-edge per the DRU.

---

## Verification Commands (HYPOTHETICAL — NOT to be run)

If this stub were ever built (which it should NOT be), verification would use:
- DRC: `kicad-cli pcb drc --output report.json output/_dryrun_stub.kicad_pcb`
- Test: no `tests/test__dryrun_stub.py` is authored (this is a wiring fixture,
  not a tested board)

---

## Completion Criteria Checklist (HYPOTHETICAL)

- [ ] Board outline closed at 10 × 10 mm (CP1)
- [ ] J1 placed at an edge with mating face outward (CP2)
- [ ] U1 placed on F.Cu, pin-1 oriented per convention (CP3)
- [ ] C1 within 5 mm of U1.1 (VCC pin) (CP4)
- [ ] All 5 components placed; no courtyard overlap (CP5)
- [ ] VCC + GND routed at ≥0.5 mm; star topology where possible (CP6)
- [ ] OUT routed at 0.25 mm; 45° angles only (CP7)
- [ ] B.Cu GND zone covers board; stitching vias on 5 mm grid (CP8)

**These criteria are not for grading a real build — they exist so the journal
trace in `docs/auditions/_stage2_dryrun_log.md` has the same shape an audition
journal would have.**
