# Visual Review Skill

Per-checkpoint structured visual critique of a rendered PCB. Consumes the PNG paths returned by `scripts/render_board.py`, applies a checkpoint-specific rubric, walks the 10-entry failure-mode catalog, and emits a JSON critique that drives the iterative refinement loop.

**When to invoke:** after every one of the 8 checkpoints in `pcb-design-skill.md`. The render → critique → decide loop is non-negotiable for v2 builds.

**Posture:** adversarial-but-honest. You are looking for what's WRONG, not collecting evidence that the design is fine. If you find nothing wrong on 2+ consecutive iterations, you are rubber-stamping — see `self-critique-skill.md`.

---

## Input Contract

You receive:

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `render_paths` | `dict[str, Path]` | `render_board()` return value | Keys: `full`, `copper`, `svg`. The `full` PNG is the primary critique target. |
| `checkpoint` | `str` | Caller (pcb-design-skill) | One of: `board_outline`, `mechanical_placement`, `ic_placement`, `critical_passive_placement`, `remaining_passive_placement`, `power_routing`, `signal_routing`, `ground_zone_and_stitching`. Maps to a rubric section below. |
| `iteration` | `int` | Caller (iterative-refinement-skill) | 1, 2, or 3. Iteration 1 critiques fresh; iterations 2-3 critique a re-rendered post-rework board against the prior critique. |
| `prior_critique` | `dict \| None` | Caller (optional) | The previous JSON critique if this is iteration ≥ 2. Use it to verify the prior issues were actually fixed and to detect over-correction (new CRITICAL appears). |
| `perception_json` | `dict \| None` | Optional | `scripts/routing_cli.py --action summary` output if available. Provides netlist + pad positions + obstacle map for cross-referencing the render. |

You produce: a single JSON object matching the **Output Format** schema below. Nothing else. No prose summary; the recommendation field carries the verdict.

---

## Per-Checkpoint Rubric

The rubric maps each of the 8 checkpoints to one of 5 visual categories: PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC. Checkpoints 1-5 are PLACEMENT-flavored, 6 is POWER_ROUTING, 7 is SIGNAL_ROUTING, 8 is GROUND_PLANE. DRC runs as an overlay starting at checkpoint 3.

### PLACEMENT (checkpoints 1-5: board_outline, mechanical_placement, ic_placement, critical_passive_placement, remaining_passive_placement)

Visual checks (walk all 7 every iteration):

1. **Outline closure.** Board outline forms a closed polygon. No gaps in the cuts layer.
2. **Component overlap.** No two footprint courtyards share opaque pixels in the render. Overlapping silkscreen is a CRITICAL placement defect.
3. **Layer correctness.** All ICs and SMD components on F.Cu (top-side, visible in `full` render). Anything mis-layered shows as ghosted/dim in the copper variant.
4. **Decoupling proximity (checkpoint 4 onward).** Every decoupling cap is within 5 mm of its IC's power pin. Measure visually against the silkscreen scale; >10 mm is a hard fail (failure mode 4).
5. **Edge clearance.** All component pads ≥1 mm from board outline (SMD) or ≥1.5 mm (through-hole). Components hanging off the board edge are CRITICAL.
6. **Pin-1 orientation.** ICs oriented per pin-1 convention (top-left or marked dot visible). Inconsistent rotation across same-family parts is MAJOR.
7. **Connector access.** Connectors at board edges with their mating face oriented outward. Inboard connectors are CRITICAL — the user can't plug them in.

### POWER_ROUTING (checkpoint 6: power_routing)

Visual checks:

1. **Trace width sufficiency.** VCC + GND power traces ≥0.5 mm. Thin (≤0.25 mm) traces on a power net are failure mode 3 — CRITICAL when current > 1 A.
2. **Full routing.** Every power pin has a trace reaching its source (regulator or input connector). Floating power pins are CRITICAL.
3. **Star topology preferred.** Power fans out from a single regulator node, not daisy-chained through loads. Daisy-chain is MAJOR.
4. **Decoupling loop integrity.** Each decap's VDD trace is short (<5 mm); the cap's GND is via'd directly to B.Cu plane. Long decap loops are MAJOR.
5. **Analog/digital supply separation.** If contract specifies VDDA, it must come through a ferrite bead, NOT a direct connection to digital VCC. Missing ferrite is MAJOR.
6. **No 90° bends.** Power traces use 45° angles only. 90° bends are MINOR but flagged for fix.
7. **Plane-piercing minimized.** Each power trace adds at most 1-2 vias. Excess vias in power paths are MAJOR (impedance + plane fragmentation).

### SIGNAL_ROUTING (checkpoint 7: signal_routing)

Visual checks:

1. **All nets routed.** Every contract-specified net has continuous copper between its endpoints. Unrouted islands are failure mode 2 — CRITICAL.
2. **Differential pair integrity.** USB / LVDS / any explicit diff pair: parallel, length-matched within 10%, equal spacing. Skew is failure mode 8 — MAJOR.
3. **45° angles.** No 90° bends in any signal trace. Failure mode (acid trap risk) — MINOR.
4. **Trace-to-pad clearance.** No trace passes within <4 mil of a non-net pad. Failure mode 10 — CRITICAL.
5. **Via stub minimization.** Signal traces transition layers at most once between endpoints. Failure mode 5 (via stub resonance) — MAJOR for high-speed nets.
6. **Crystal isolation.** HSE traces have no other signals running underneath/adjacent within 2 mm. MAJOR if violated.
7. **No traces under ICs.** Routing under QFN/BGA pads on the same layer is MAJOR (manufacturability + assembly).

### GROUND_PLANE (checkpoint 8: ground_zone_and_stitching)

Visual checks:

1. **B.Cu zone covers the board.** GND zone fills B.Cu to within the supplier's copper-to-edge clearance. Gaps in the plane are MAJOR.
2. **No ground plane islands.** No isolated GND polygons disconnected from the main plane. Failure mode 6 — CRITICAL (radiates EMI).
3. **Stitching via grid.** Stitching vias placed on a 5 mm grid along board perimeter. Missing is failure mode 9 — MAJOR.
4. **IC ground pin stitching.** Every IC GND pin has a stitching via within 1 mm. Missing is MAJOR.
5. **No splits under high-speed signals.** GND plane is unbroken directly beneath every USB / clock trace. Splits cause return-path detour — CRITICAL for high-speed.
6. **Crystal guard ring.** Crystal area enclosed by a F.Cu GND ring stitched to B.Cu every 2-3 mm. Missing is MAJOR.
7. **F.Cu remnant copper filled.** All unused F.Cu space filled with GND zone (priority 1, B.Cu is priority 0). Empty F.Cu remnants are MINOR.

### DRC (overlay from checkpoint 3 onward)

After every checkpoint that adds copper, the render is cross-checked against `scripts/routing_cli.py --action drc` output. Visual checks:

1. **Silk-on-pad.** No silkscreen text overlapping pads or vias. Failure mode 7 — MINOR but auditor-visible.
2. **Trace-to-pad clearance.** As in SIGNAL_ROUTING — failure mode 10 — CRITICAL.
3. **Annular ring sufficiency.** Every via shows visible copper donut around its drill. Missing annular ring is CRITICAL (supplier-specific minimum from `agent_docs/rules/supplier-drc-rules.md`).
4. **Mask web slivers.** No solder mask slivers thinner than supplier minimum between pads. MAJOR.
5. **Hole-to-hole spacing.** Through-holes ≥0.5 mm apart (supplier-specific). CRITICAL if violated.

---

## Failure Mode Catalog

Walk all 10 entries every iteration. If you cannot rule out a mode, list it as an issue. Do NOT skip entries because "it looks fine."

| # | Failure mode | Visual signature | Checkpoint | Fix hint |
|---|---|---|---|---|
| 1 | Component overlap | Outlines share opaque pixels | PLACEMENT | Increase spacing; lock heavies first |
| 2 | Unrouted net island | Disconnected copper region | SIGNAL_ROUTING | Manual seed point; decompose net |
| 3 | Thin power trace | <5 mil width on >1A net | POWER_ROUTING | 1A/0.5mm rule; widen 3x |
| 4 | Decap too far | >10 mm from IC power pin | PLACEMENT | Re-place cap <5 mm from pin |
| 5 | Via stub resonance | Barrel extends >50 mil past signal layer | SIGNAL_ROUTING | Minimize layer transitions; back-drill |
| 6 | Ground plane island | Isolated polygon not on GND net | GROUND_PLANE | Bridge with trace/via; verify net |
| 7 | Silk-on-pad | Text overlaps pad/via | DRC | Offset silk ≥5 mil from pad |
| 8 | Diff pair skew | Lengths differ >10%, spacing unequal | SIGNAL_ROUTING | Serpentine shorter trace; tighten pair |
| 9 | Missing via stitching | Plane edge has no GND vias | GROUND_PLANE | 5 mm grid along boundaries |
| 10 | Trace-to-pad clearance | <4 mil from adjacent pad/via | DRC / SIGNAL_ROUTING | Widen spacing or different layer |

---

## Output Format

You emit exactly one JSON object. No prose before or after. The JSON must validate against this schema:

```json
{
  "checkpoint": "critical_passive_placement",
  "iteration": 1,
  "pass_fail": "fail",
  "confidence": 0.78,
  "issues": [
    {
      "severity": "CRITICAL",
      "type": "PLACEMENT",
      "failure_mode_id": 4,
      "description": "Decoupling cap C2 is 12 mm from U1 pin 8; should be <5 mm.",
      "location": { "ref": "C2", "x_mm": 14.2, "y_mm": 5.1 },
      "fix_hint": "Re-place C2 within 5 mm of U1.8; rotate 90° if needed for trace approach."
    },
    {
      "severity": "MINOR",
      "type": "PLACEMENT",
      "failure_mode_id": 1,
      "description": "Silkscreen for R3 reference designator overlaps C5 silkscreen.",
      "location": { "ref": "R3", "x_mm": 22.1, "y_mm": 8.4 },
      "fix_hint": "Hide R3 designator or move silk text to component side."
    }
  ],
  "pass_criteria": {
    "all_critical_passives_within_5mm_of_ic_power_pins": false,
    "no_component_overlap": true,
    "components_on_correct_layer": true,
    "edge_clearance_satisfied": true
  },
  "recommendation": "rework",
  "notes": "Cap placement is mostly good; C2 is the only critical issue. Single-issue rework should resolve."
}
```

**Required fields** (every emission must contain all six):

- `checkpoint` — string, one of the 8 checkpoint names
- `iteration` — int, 1-3
- `pass_fail` — string, `"pass"` or `"fail"`
- `confidence` — float in [0, 1]. See thresholds below.
- `issues` — array of issue objects (may be empty if `pass_fail == "pass"`); each issue has `severity` (`CRITICAL`|`MAJOR`|`MINOR`), `type` (one of the 5 rubric categories), `failure_mode_id` (1-10 from catalog above, or `null` if not in catalog), `description`, `location` (`{ref, x_mm, y_mm}` or `{x_mm, y_mm}` if no ref), `fix_hint`
- `recommendation` — string, one of `"proceed"`, `"rework"`, `"escalate"`. This field is advisory; the final proceed/rework/escalate decision is made by `iterative-refinement-skill.md` using the JSON as input.

Optional fields: `pass_criteria` (dict of per-rubric-item booleans), `notes` (≤3 sentence summary).

### Confidence calibration

- **0.85-1.00** — clean render, all rubric items pass, no issues in the catalog walk. Recommend `proceed`.
- **0.70-0.84** — minor issues only, none CRITICAL. Recommend `rework` only if MINOR count ≥3.
- **0.50-0.69** — at least one MAJOR or CRITICAL issue. Recommend `rework`.
- **0.30-0.49** — multiple CRITICAL issues OR uncertain what's wrong. After iteration 2, recommend `escalate` per `iterative-refinement-skill.md` threshold (0.5).
- **<0.30** — the render is unparseable or the checkpoint state is incoherent. Recommend `escalate` immediately.

---

## Anti-Pattern Guard Rails

Apply these rules to your OWN output before emitting it. Self-checking the critique posture is part of the critique.

1. **Do NOT return `"pass_fail": "pass"` with zero issues for 2+ consecutive iterations on the same checkpoint.** That's rubber-stamping. Force adversarial mode on iter 2: re-walk the failure-mode catalog and list anything you cannot affirmatively rule out, even at MINOR severity.

2. **Do NOT return `confidence >= 0.85` unless every `pass_criteria` item is `true`.** Confidence is earned by criteria satisfaction, not by absence of obvious flaws.

3. **Do NOT skip the failure-mode catalog walk.** Even if you've identified a CRITICAL on entry 1, walk all 10 entries. Multi-issue checkpoints are common; reporting one issue and stopping makes downstream rework inefficient.

4. **Do NOT recommend `proceed` if any issue has `"severity": "CRITICAL"`.** A single CRITICAL blocks advance, regardless of confidence number.

5. **Do NOT recommend `escalate` on iteration 1.** Escalation is reserved for iteration ≥2 with confidence <0.5. Iteration-1 escalation is early-escalation (anti-pattern); recommend `rework` instead and let iterative-refinement decide.

6. **Do NOT invent issues to look adversarial.** If the render genuinely passes the rubric, return `pass_fail: "pass"` with `confidence >= 0.85` and let downstream skills detect rubber-stamping via the convergence trajectory, not via fabricated MINOR issues.

7. **Noise floor.** Ignore visual artifacts <5% of board area (e.g., a single anti-aliased silkscreen pixel). They are render artifacts, not design issues.

8. **Over-iteration awareness.** If `iteration == 3` and you still find issues, set `recommendation: "escalate"` and let the loop ceiling fire. Do not silently signal `rework` on iteration 3 — that's the cue for `iterative-refinement-skill.md` to escalate.

---

## Required Reading

- `agent_docs/skills/iterative-refinement-skill.md` — consumes your JSON output and decides proceed/rework/escalate
- `agent_docs/skills/self-critique-skill.md` — meta-skill that detects rubber-stamping in your output
- `agent_docs/rules/clearance-rules.md` — supplies the numerical thresholds for the rubric (5 mm decap, 1.5 mm edge, etc.)
- `agent_docs/rules/supplier-drc-rules.md` — supplies the DRC-overlay thresholds (annular ring, mask web, etc.)
- `scripts/render_board.py` — produces the PNGs you consume

---

## Example Invocation Sequence (one checkpoint)

```
1. pcb-design-skill: finishes checkpoint 4 actions (decoupling caps placed)
2. pcb-design-skill: calls scripts/render_board.py → gets {full, copper, svg} paths
3. visual-review-skill: walks PLACEMENT rubric (7 items) + 10-entry catalog
4. visual-review-skill: emits JSON critique (above schema)
5. self-critique-skill: detects no rubber-stamping; passes through
6. iterative-refinement-skill: reads recommendation + confidence; decides proceed/rework/escalate
7. (if rework) → step 1 with rework scope; iteration += 1
8. (if proceed) → checkpoint 5
9. (if escalate) → AskUserQuestion with state dump
```
