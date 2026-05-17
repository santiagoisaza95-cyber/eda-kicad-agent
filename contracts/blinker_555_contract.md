---
supplier: jlcpcb
layer_count: 2
board_dimensions: 20x30 mm
fr4_thickness: 1.6 mm
copper_weight: 1 oz
surface_finish: HASL (lead-free)
---

# Contract: 555 LED Blinker (v2 Audition Board)

**Version:** 1.0
**Board Name:** blinker_555
**Output File:** `output/blinker_555.kicad_pcb`
**Purpose:** First credible-design audition under the v2 architecture. Small, classic, judge-by-eye.

---

## DESIGN FROM THIS CONTRACT ONLY

**For this board, you MUST NOT:**
- Use `WebSearch` or `WebFetch` to look up 555 astable schematics, reference boards, or pinouts
- Read any files in the `reference/` directory
- Browse GitHub or any website for existing 555 blinker designs
- Search for "NE555 pinout," "555 astable layout," or similar queries online
- Open or read `baselines/4.6/blue_pill.kicad_pcb` for "inspiration" on placement style

**You MUST design entirely from:**
- This contract (components table + netlist + placement guidance below)
- The skills in `agent_docs/skills/`
- The rules in `agent_docs/rules/` — especially `agent_docs/rules/supplier-drc-rules.md`
- The supplier profile at `supplier_profiles/jlcpcb.yaml` (loaded automatically via the `supplier: jlcpcb` metadata above; emits `output/blinker_555.kicad_dru` before routing)
- The API manifest in `api_manifest.json`
- The MCP tools for placement, DRC, export, library search (NOT for routing — use `scripts/routing_cli.py` per `routing-skill.md`)

This is a controlled audition. The v2 hypothesis is that visual feedback + iterative checkpoints + supplier-anchored DRC + Opus 4.7 is enough — **without crutches** — to produce a board the owner judges as credible. Everything you need to succeed is in this contract and the rules/skills it points at.

---

## Board Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 20.0 mm × 30.0 mm (rectangle; minor rounding tolerated within the 0.5 mm test slack) |
| Layers | 2 (F.Cu = signal, B.Cu = GND zone) |
| Thickness | 1.6 mm FR4 |
| Copper weight | 1 oz (35 µm) |
| Surface finish | HASL (lead-free) |
| Min hole-to-edge | per JLCPCB profile (≥ 0.3 mm copper-to-edge) |

The board is intentionally small. A 5–7-component 555 astable has more empty FR4 than copper. Placement quality and silk legibility are the visual-judgment axes here; complexity is not.

---

## Design Rules — Reference, Don't Duplicate

**The authoritative source for trace widths, clearances, via dimensions, annular ring, silk, and copper-to-edge is the JLCPCB supplier profile**, loaded from `supplier_profiles/jlcpcb.yaml` and emitted to `output/blinker_555.kicad_dru` by `scripts/supplier_drc/loader.py::emit_kicad_dru`. Do **not** hand-pick clearance numbers in build code or here — that was a v1 failure mode (DRC clean ≠ JLCPCB clean).

**Mandatory rule:** Per `agent_docs/rules/supplier-drc-rules.md`, you MUST:
1. Call `load_supplier_profile("jlcpcb")` as your first build action.
2. Call `emit_kicad_dru(profile, Path("output/blinker_555.kicad_dru"))` before any trace is placed.
3. Run DRC against the emitted DRU at every checkpoint that produces copper.

**Suggested working trace widths** (within JLCPCB minimums, generous on this small board):
- Signal traces (TRIG, THR, DISCH, OUT): 0.25 mm
- Power traces (VCC, GND on F.Cu): 0.5 mm
- B.Cu GND zone fills any remaining ground return; minimum copper-to-edge clearance per the DRU.

If a working value conflicts with the DRU, the DRU wins — adjust the build, not the rules.

---

## Components (8 items, 7 component rows)

| Ref | Value | Footprint | Purpose |
|-----|-------|-----------|---------|
| U1 | NE555 | Package_DIP:DIP-8_W7.62mm | Astable timer (through-hole DIP-8 for visibility) |
| R1 | 1k | Resistor_SMD:R_0603_1608Metric | Charge resistor (VCC → DISCH/pin 7) |
| R2 | 10k | Resistor_SMD:R_0603_1608Metric | Discharge resistor (DISCH/pin 7 → THR/pin 6) |
| R3 | 470 | Resistor_SMD:R_0603_1608Metric | LED current-limit (OUT/pin 3 → LED anode) |
| C1 | 10u | Capacitor_SMD:C_0805_2012Metric | Timing capacitor (THR/pin 6 → GND) |
| C2 | 100n | Capacitor_SMD:C_0603_1608Metric | VCC decoupling (pin 8 to GND) |
| D1 | LED | LED_SMD:LED_0603_1608Metric | Visible blink indicator |
| J1 | PWR | Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical | 2-pin power header (VCC, GND) for 9 V battery clip |

**Component count:** 8 footprints total (U1, R1, R2, R3, C1, C2, D1, J1). `test_component_count` asserts ≥ 8 footprints on the board.

**Why these values:**
- R1=1k, R2=10k, C1=10 µF gives an astable frequency around f ≈ 1.44 / ((R1 + 2R2) × C1) ≈ 6.8 Hz with duty cycle (R1 + R2)/(R1 + 2R2) ≈ 52% — visibly blinking, biased slightly toward "on" so the LED is easy to see.
- R3=470 Ω at 9 V supply with a ~2 V LED forward voltage gives ~15 mA through D1 (well under the 555's 200 mA OUT drive and the LED's 20 mA rating).
- C2=100 nF VCC-to-GND right at U1 pin 8 suppresses the rail glitch on each output transition.
- DIP-8 is chosen over SOIC-8 so the audition board reads clearly under the rendered PNG; the goal is judge-by-eye, not maximum density.

---

## Netlist (6 nets)

| Net Name | Connected Pins |
|----------|----------------|
| VCC | J1.1, U1.8 (VCC), U1.4 (RESET — tied high), R1.1, C2.1 |
| GND | J1.2, U1.1 (GND), C1.2, C2.2, D1.2 (cathode) |
| TRIG | U1.2 (TRIG), U1.6 (THR), C1.1, R2.2 |
| THR | (alias of TRIG — physically the same junction at U1.2 / U1.6 / C1.1 / R2.2; documented as a distinct net name for traceability per the v2 stage contract) |
| DISCH | U1.7 (DISCH), R1.2, R2.1 |
| OUT | U1.3 (OUT), R3.1 |
| OUT_LED | R3.2, D1.1 (anode) |

**Implementation note on TRIG vs THR:**
In a standard 555 astable the TRIG (pin 2) and THR (pin 6) inputs are tied together at the top of the timing capacitor. The Stage 1 contract enumerates `TRIG` and `THR` as separate net names for documentation. Implementations may merge them into a single physical net (assign all four pins — U1.2, U1.6, C1.1, R2.2 — to one net) and name it whichever of `TRIG` or `THR` is convenient; the test suite asserts the existence of each named net, so the build script MUST create both net entries even if one is the alias of the other. (Practical approach: create both nets in the netlist; assign one to the four shared pads; leave the other as an empty named net so it exists for `GetNetItem()` lookup. Alternatively, route the connection as TRIG-to-THR through a zero-length trace under the cap pad — either satisfies `test_net_connectivity` provided both names are present in the board's net table.)

**RESET (U1.4):** Tied to VCC (active-low input, must be held high to allow oscillation). Counted as part of the VCC net.
**CTRL (U1.5):** Left floating per simplified 555 astable convention — no decoupling cap added to keep the board minimal. (If aesthetic critique flags it during audition, add a 10 nF stub under spare BOM during a rework iteration.)

---

## Placement Guidance (rough — leave room for routing optimization)

Follow `agent_docs/skills/placement-skill.md` priority order. The visual judge wants to see breathing room, clean keep-outs, and an LED visible from the edge.

1. **U1 (NE555 DIP-8)** — center of board, oriented so pin 1 faces the power header (J1 side) and the output side (pin 3) faces the LED edge.
2. **C2 (100 nF decoupling)** — within 2 mm of U1 pin 8 (VCC). Short, fat tie to the GND zone on B.Cu.
3. **R1, R2 (timing resistors)** — adjacent to U1 pins 7 (DISCH) and 6 (THR), oriented to minimize the TRIG/THR loop area.
4. **C1 (timing cap)** — close to the R2/U1.6 junction; its GND pad should drop straight into a B.Cu stitching via.
5. **R3 + D1 (LED + limit resistor)** — D1 at the board edge opposite J1 so the LED is visible "looking down at the board." R3 between U1.3 and D1.1.
6. **J1 (2-pin power header)** — at one short edge of the board (one of the 20 mm edges). Orient so the battery clip cable exits without crossing the silk.

**Keep-out / aesthetics notes:**
- All component reference designators on F.SilkS, minimum 1.0 mm text height per JLCPCB silk rules.
- No silk on pads (the auditor's per-checkpoint visual review will flag silk-on-pad as MEDIUM severity).
- Courtyards must not overlap (the agent's checkpoint 4 inline reviewer enforces this).

---

## Routing Guidance

Follow `agent_docs/skills/routing-skill.md` priority order. **Do not use MCP routing tools** (`route_trace`, `route_pad_to_pad`, `route_differential_pair`) — they place single straight segments with no pathfinding or clearance checks. Use `scripts/routing_cli.py` iteratively, one net at a time.

1. **Power first** — VCC at 0.5 mm width on F.Cu from J1.1 → R1.1 → C2.1 → U1.8 → U1.4 (RESET tie-up).
2. **Critical timing junction** — TRIG/THR junction (U1.2 + U1.6 + C1.1 + R2.2) routed tight and compact; this is the most timing-sensitive node electrically and the most visually scrutinized node on the board.
3. **DISCH** — short link U1.7 → R1.2 → R2.1.
4. **OUT path** — U1.3 → R3 → D1, kept on F.Cu, no vias.
5. **GND** — primarily as a B.Cu zone fill with stitching vias near U1 pin 1, C1.2, C2.2, D1.2, J1.2.
6. **No 90° bends** anywhere — use 45° turns per the routing skill's hard constraint.

The B.Cu copper zone on the GND net handles most ground return; per-pin GND drops on F.Cu are acceptable where they shorten the routing.

---

## Copper Zones

| Layer | Net | Priority | Purpose |
|-------|-----|----------|---------|
| B.Cu | GND | 0 | Full-board ground plane |
| F.Cu | GND | 1 | Optional secondary fill — only on space the agent's checkpoint-8 visual judges as benefiting from it |

All zones filled (`ZONE_FILLER.Fill` called) before final DRC.

---

## Success Criteria — Audition Output

This board passes audition iff **all** of the following hold:

- [ ] DRC reports **0 errors** against `output/blinker_555.kicad_dru` (emitted from the JLCPCB supplier profile — not against KiCad defaults).
- [ ] DRC reports **0 unconnected items**.
- [ ] All 8 components (U1, R1, R2, R3, C1, C2, D1, J1) are placed on `F.Cu` with correct footprints (DIP-8 through-hole for U1; SMD 0603/0805 for passives/LED; through-hole 2.54 mm header for J1).
- [ ] All 6 nets (VCC, GND, TRIG, THR, DISCH, OUT) are defined in the net table; OUT_LED may exist as a separate net or merged with OUT — both satisfy connectivity.
- [ ] Board bounding box ≤ 20.5 × 30.5 mm (within the test tolerance over the nominal 20 × 30 mm dimensions).
- [ ] No traces with 90° bends.
- [ ] No use of MCP routing tools; all traces created via `scripts/routing_cli.py` or `pcbnew` SWIG directly.
- [ ] All routing respects the JLCPCB DRU constraints (annular ring ≥ 0.15 mm, edge clearance ≥ 0.3 mm, trace clearance ≥ 0.127 mm, silk line width ≥ 0.15 mm, silk text height ≥ 1.0 mm).
- [ ] B.Cu GND zone present, filled, with at least one stitching via near U1.
- [ ] Per-checkpoint renders in `output/checkpoints/blinker_555_<N>_<name>_*.png` exist (8 full + 8 copper).
- [ ] `output/blinker_555_journal.md` populated with per-checkpoint decisions, issues, and lessons.
- [ ] `pytest tests/test_blinker_555.py -v` is **green** (every test in this contract's `tests/test_blinker_555.py` passes — no `xfail`, no `skip` other than legitimate "board not built yet" skips before audition).
- [ ] Inline `design-reviewer` invocations at checkpoints 4 and 6 wrote files to `review/blinker_555_inline_{4,6}.md` and any CRITICAL findings were resolved before proceeding.
- [ ] **Owner-credible visual judgment** at all three milestone touchpoints (post-critical-passive-placement, post-all-placement, post-signal-routing). This is the subjective hard gate that v1 lacked. Owner reads the final `output/blinker_555_full.png` and declares "credible 555" or "not credible 555."

---

## Completion Checklist (Build-Time, for the Agent)

- [ ] Loaded `supplier_profiles/jlcpcb.yaml` and emitted `output/blinker_555.kicad_dru` before placing any trace.
- [ ] Board outline drawn (20.0 × 30.0 mm rectangle on Edge_Cuts).
- [ ] All 8 components placed with correct footprints.
- [ ] All 6 nets (VCC, GND, TRIG, THR, DISCH, OUT) defined in the net table.
- [ ] Decoupling cap C2 within 2 mm of U1 pin 8.
- [ ] Timing cap C1 directly at the TRIG/THR junction.
- [ ] LED D1 visible at a board edge opposite J1.
- [ ] Pre-routing DRC clean (courtyard overlaps, edge clearance) against the emitted JLCPCB DRU.
- [ ] All traces routed using `scripts/routing_cli.py` or pcbnew SWIG (NOT MCP routing tools).
- [ ] No 90° trace bends.
- [ ] Power traces at 0.5 mm; signal traces at 0.25 mm minimum.
- [ ] GND copper zone on B.Cu (full board), filled.
- [ ] Ground stitching vias placed near U1 and C1.
- [ ] Per-checkpoint renders saved to `output/checkpoints/`.
- [ ] `output/blinker_555_journal.md` updated after each checkpoint.
- [ ] DRC passes: 0 violations AND 0 unconnected items against `output/blinker_555.kicad_dru`.
- [ ] All `pytest tests/test_blinker_555.py -v` tests pass.
- [ ] Board saved to `output/blinker_555.kicad_pcb`.

---

## Verification Commands (used by the Stage 1 auditor and the Stage 3 audition tester)

```
$ test -f contracts/blinker_555_contract.md && echo OK

$ grep "DESIGN FROM THIS CONTRACT ONLY" contracts/blinker_555_contract.md
Expected: at least one match

$ grep "supplier: jlcpcb" contracts/blinker_555_contract.md
Expected: match in YAML front-matter

$ pytest tests/test_blinker_555.py -v --collect-only
Expected: 5 tests enumerated (test_component_count, test_nets_routed,
          test_drc_zero, test_dimensions, test_components_on_f_cu);
          no import errors. Tests skip cleanly if output/blinker_555.kicad_pcb
          does not yet exist.

$ pytest tests/test_blinker_555.py -v   # after Stage 3 audition produces the board
Expected: 5/5 green
```
