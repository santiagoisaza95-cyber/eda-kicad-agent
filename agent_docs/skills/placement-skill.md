# Component Placement Skill

Rules and best practices for placing components on a KiCad PCB.

**MANDATORY:** Before placing ANY component, read `agent_docs/rules/clearance-rules.md`. Every placement must satisfy those clearance tables. Violations caught later are expensive to fix — get it right during placement.

---

## Coordinate System

- **Origin**: Top-left corner of the board
- **X axis**: Increases to the RIGHT
- **Y axis**: Increases DOWNWARD
- **Units**: Always millimeters (use `FromMM()` for all positions)
- **Grid**: Snap to 0.5mm grid for component placement

```
(0,0) ──────────── X+ ────────────►
  │
  │
  Y+
  │
  │
  ▼
```

---

## Placement Workflow (follow this order exactly)

### Phase 1: Mechanicals First
Place position-constrained items first. These define the available board area.

1. **Mounting holes** — fixed positions from enclosure or mating board
2. **Connectors** (USB, pin headers, card-edge) — at board edges. Edge-mounted connectors sit flush; leave 1.5mm clearance between connector and any other component.
3. **Switches and buttons** — at board edges, accessible. Leave 1.5mm clearance to neighbours.
4. **LEDs** — visible locations

### Phase 2: ICs
5. **MCU / Main IC** — place at or near board center, pin 1 at top-left. Leave at least 1.5mm clearance on all 4 sides (QFP/QFN rule from clearance-rules.md). Leave 2.0mm on at least two sides for probe access during debug.
6. **Voltage regulators** — near power input connector. Leave 0.8mm clearance to neighbours (SOT-223/SOT-23 rule).

### Phase 3: Critical Passives
7. **Decoupling capacitors** — within 2mm of IC power pins. One cap per VDD pin minimum. Must still maintain 0.5mm courtyard gap to IC and 0.5mm to each other (SMD-to-SMD 0402-0805 rule).
8. **Crystal / Oscillator** — within 5mm of MCU clock pins. Keep traces short and symmetric. No other signals between crystal and MCU. Leave 0.8mm clearance (Crystal_SMD is typically 1206+ size).
9. **Analog filter components** (ferrite beads, VDDA caps) — near analog supply pins.

### Phase 4: Remaining Passives
10. **Pull-up / Pull-down Resistors** — near the pin they service. NRST pull-up near NRST, I2C pull-ups near connector or IC.
11. **Other passives** — grouped by function. Maintain consistent orientation. 0.5mm minimum gap between same-group SMD 0402-0805 components.

### Phase 5: Verify Before Routing
12. **Run courtyard-overlap DRC** — fix any overlaps NOW, before routing.
13. **Visual inspection** — zoom to 1:1 scale. If two features look uncomfortably close, they ARE too close.

---

## Clearance Quick Reference (from clearance-rules.md)

| Component Pair | Min Courtyard Gap |
|----------------|-------------------|
| SMD to SMD (0402-0805) | 0.5mm |
| SMD to SMD (1206+, SOT-23, SOT-223) | 0.8mm |
| SMD to through-hole pad | 1.0mm |
| Through-hole to through-hole | 1.0mm |
| Any component to connector | 1.5mm |
| Any component to switch | 1.5mm |
| QFP/QFN/BGA to nearest neighbour | 1.5mm |
| SMD pads to board edge | 1.0mm |
| Through-hole pads to board edge | 1.5mm |

If the board is too small to meet these, STOP and flag the constraint conflict. Do NOT silently shrink gaps.

---

## Target Clearance vs Functional Clearance

"Close to IC pins" does NOT mean "touching the IC pads":
- **Decoupling cap within 2mm of VDD pin** = the cap's nearest pad is within 2mm of the IC power pad, measured centre-to-centre. But the courtyard gap between cap and IC must still be >= 0.5mm (0402-0805) or >= 1.5mm (if adjacent to QFP/QFN body).
- **Crystal within 5mm of clock pins** = crystal body centre within 5mm of HSE_IN/OUT pads. Courtyard gap to MCU must still be >= 0.8mm.

These two requirements (proximity AND clearance) are both satisfied by placing components near — not on top of — their target pins.

---

## Example Layout — Simple MCU Board (50x40mm)

```
(0,0)
  ┌──────────────────────────────────────────────────┐
  │                                                    │
  │   [Y1 Crystal]     [U1 STM32 MCU]                │
  │      (15,12)           (25,20)                     │
  │                    [C1] [C2]                       │
  │                   (22,15)(28,15)                    │
  │                                                    │
  │   [R1 Pull-up]                                     │
  │      (15,25)                                       │
  │                                                    │
  │           [J1 USB Micro-B]                         │
  │              (25,38)  ← at bottom edge             │
  └──────────────────────────────────────────────────┘
                                              (50,40)
```

---

## Position Setting in Code

```python
import pcbnew

# Set component position (always use FromMM)
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25), pcbnew.FromMM(20)))

# Rotate component (in tenths of a degree in KiCad 7, EDA_ANGLE in KiCad 9)
# UNVERIFIED — check api_manifest.json for EDA_ANGLE
fp.SetOrientation(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))  # 90° rotation
```

---

## Placement Checklist

Before moving to routing, ALL of these must be true:
- [ ] All contract components are placed on the board
- [ ] MCU is centered with >= 1.5mm clearance on all sides
- [ ] Decoupling caps within 2mm of IC power pins AND >= 0.5mm courtyard gap
- [ ] Crystal within 5mm of clock pins AND >= 0.8mm courtyard gap
- [ ] Connectors at board edges with >= 1.5mm clearance to other components
- [ ] No courtyard overlaps (run DRC courtyard check)
- [ ] All SMD pads >= 1.0mm from board edge
- [ ] All through-hole pads >= 1.5mm from board edge
- [ ] All components on 0.5mm grid
- [ ] Reference designators match contract
- [ ] Visual inspection at 1:1 — nothing looks impossible to solder
