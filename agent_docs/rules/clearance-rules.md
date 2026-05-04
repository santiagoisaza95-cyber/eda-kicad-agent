# PCB Clearance & Manufacturability Rules

These rules prevent component crowding, drill-to-pad shorts, and board-edge damage. They are MANDATORY for every placement step. Violations must be fixed before routing begins.

---

## Rule 1 — Component-to-Component Courtyard Clearance

All clearances are measured courtyard-edge to courtyard-edge. If a footprint has no courtyard defined, add one using IPC-7351B nominal or greater.

| Component Pair | Minimum Gap |
|----------------|-------------|
| SMD to SMD (0402-0805) | 0.5mm |
| SMD to SMD (1206+, SOT-23, SOT-223) | 0.8mm |
| SMD pad to through-hole pad | 1.0mm |
| Through-hole to through-hole | 1.0mm |
| Any component to connector footprint | 1.5mm |
| Any component to mechanical switch | 1.5mm |
| QFP/QFN/BGA to nearest neighbour | 1.5mm |

If the board area is too small to meet these clearances, STOP and flag it as a constraint conflict. Do NOT silently reduce spacing.

---

## Rule 2 — Drill Hole to Pad Clearance

Clearance is measured from the drill edge (drill_diameter / 2 from centre), NOT from the hole centre.

| Feature Pair | Minimum Clearance |
|-------------|-------------------|
| Non-plated mounting hole edge to nearest pad | 1.0mm |
| Plated mounting hole edge to nearest pad | 0.8mm |
| Via barrel edge to SMD pad edge | 0.3mm |
| Via barrel edge to through-hole pad edge | 0.5mm |

---

## Rule 3 — Board Edge Keepout

Edge-mounted connectors (USB, card-edge) are exempt but must follow the manufacturer's recommended footprint exactly.

| Feature | Minimum Distance from Board Edge |
|---------|----------------------------------|
| SMD pads | 1.0mm |
| Through-hole pads | 1.5mm |
| Copper pour | 0.5mm |
| Components on V-score panels | 2.0mm from score line |

---

## Rule 4 — Courtyard Enforcement

- Every footprint MUST have a fabrication courtyard layer defined.
- Courtyard overlaps between any two components are ALWAYS a violation — no exceptions.
- Run a courtyard-overlap DRC check BEFORE routing. Fix overlaps by adjusting placement.

---

## Rule 5 — Thermal and Debug Access

- Leave at least 2.0mm clearance on at least two sides of every IC for probe access during debug.
- Decoupling caps must be close to IC supply pins but NEVER closer than the courtyard gap from Rule 1.
- If hand soldering is anticipated, add +0.3mm to all SMD-to-SMD clearances above the table values.

---

## DRC Configuration Checklist

Before finalising placement, verify ALL of these DRC settings are active:

- [ ] Courtyard overlap check: Enabled, Error severity
- [ ] Pad-to-pad clearance: >= 0.2mm (copper-to-copper)
- [ ] Drill-to-pad clearance: matches Rule 2 values
- [ ] Silk-to-pad clearance: >= 0.15mm
- [ ] Board-edge clearance: matches Rule 3 values
- [ ] Unconnected net check: Enabled, Error severity
- [ ] Minimum annular ring: >= 0.15mm (standard), >= 0.25mm (preferred)

NEVER suppress or downgrade DRC violations to warnings. Fix the layout.

---

## Common Mistakes to Reject

- Pushing components together until DRC "just barely passes" — no manufacturing margin.
- Placing mounting holes first then squeezing components around them without checking drill-to-pad clearance.
- Using footprints without courtyard layers, bypassing overlap checks.
- Ignoring the physical space a mating connector plug occupies above the board.
- Treating DRC minimum clearance as a target instead of a hard floor — always aim for greater than minimum.
- Placing passives between IC pads in the thermal pad zone of QFN/QFP packages.
