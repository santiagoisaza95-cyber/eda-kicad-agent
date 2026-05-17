# PCB Design Skill (v2 — 8-checkpoint iterative)

The orchestrator skill for every PCB build. Replaces v1's monolithic 12-step workflow with an **8-checkpoint iterative architecture**: each checkpoint executes its actions, renders the board, applies the visual critique loop (Self-Refine), and either proceeds, reworks, or escalates. Reflexion-style journaling preserves cross-checkpoint lessons within the session. Inline `design-reviewer` gates fire at checkpoints 4 + 6. `AskUserQuestion` milestones fire at the boundaries of checkpoints 4, 5, and 7.

**This skill does NOT do the visual critique itself.** It owns the checkpoint state machine and the journal protocol. The actual critique work is delegated to `visual-review-skill.md`, the decision is made by `iterative-refinement-skill.md`, and the meta-posture is audited by `self-critique-skill.md`. This skill wires them together.

---

## When to Invoke

You are designing a PCB from a contract. The contract has `supplier:` metadata. You will walk 8 checkpoints in order, rendering and critiquing after each, with a Self-Refine loop capped at 3 iterations per checkpoint. You will pause at 3 owner milestones via `AskUserQuestion`. You will write every iteration's outcome to a journal so downstream checkpoints inherit the lessons.

If the task is anything other than "build a PCB from a contract" — STOP. Find the right skill in CLAUDE.md routing.

---

## Required Reading (in order)

1. The contract you were given (e.g. `contracts/blinker_555_contract.md`)
2. `agent_docs/rules/coding-rules.md` (general — always)
3. `agent_docs/rules/supplier-drc-rules.md` (MANDATORY before any routing checkpoint)
4. `agent_docs/skills/visual-review-skill.md` (rubric + JSON output schema)
5. `agent_docs/skills/iterative-refinement-skill.md` (decision tree + loop limits)
6. `agent_docs/skills/self-critique-skill.md` (anti-pattern detection + posture)
7. `agent_docs/skills/placement-skill.md` (survives from v1 — placement primitives)
8. `agent_docs/skills/routing-skill.md` (survives from v1 — routing primitives; **MCP routing BANNED**)
9. `agent_docs/skills/kicad-api-skill.md` (referenced when uncertain about pcbnew functions)

---

## Preconditions Before First Checkpoint

Do ALL of these before invoking checkpoint 1. If any fails, STOP and resolve before continuing.

| # | Precondition | How to verify |
|---|--------------|---------------|
| 1 | Contract loaded; supplier identified | Read `contracts/<board>.md` front-matter; confirm `supplier:` field present (default: `jlcpcb`) |
| 2 | `python scripts/verify_mcp.py` exits 0 | Gate 0 in `CLAUDE.md` |
| 3 | `python scripts/verify_toolchain.py` exits 0 | KiCad CLI + bundled Python reachable |
| 4 | Supplier profile loaded; DRU emitted | `load_supplier_profile(name)` then `emit_kicad_dru(profile, output/<board>.kicad_dru)` per `supplier-drc-rules.md` |
| 5 | `output/<board>.kicad_dru` on disk | `test -f output/<board>.kicad_dru` |
| 6 | `scripts/render_board.py` callable | `python scripts/render_board.py --help` |
| 7 | Journal file created | Write the header `# Build Journal — <board>` to `output/<board>_journal.md` |
| 8 | `output/` + `review/` directories exist | Create if missing |

**DRU emission MUST precede any routing action.** This is the supplier-DRC gate from `supplier-drc-rules.md`. If you have not emitted the DRU, you are not allowed past checkpoint 5.

---

## The 8 Checkpoints

| # | Checkpoint | Entry criterion | Exit criterion | Gates |
|---|------------|-----------------|----------------|-------|
| 1 | `board_outline` | preconditions complete | closed Edge_Cuts polygon at contract dims (±0.1 mm) | render → critique (PLACEMENT rubric) |
| 2 | `mechanical_placement` | outline done | mounting holes + connectors + switches placed at edges; ≥3 mm edge clearance | render → critique |
| 3 | `ic_placement` | mechanical done | all ICs on F.Cu, pin-1 oriented per convention; no overlap; DRC clean | render → critique → DRC |
| 4 | `critical_passive_placement` | IC placement done | decoupling caps within 5 mm of IC power pins; crystal within 5 mm of clock pins; analog filter caps adjacent to VDDA | render → critique → DRC → **inline reviewer (design-reviewer)** → **milestone 1 (AskUserQuestion)** |
| 5 | `remaining_passive_placement` | critical passives placed | all contract components placed; no overlap; pull-ups near pin they service | render → critique → DRC → **milestone 2 (AskUserQuestion)** |
| 6 | `power_routing` | placement complete; DRU emitted | VCC + GND traces ≥0.5 mm; every power pin reached; star topology preferred; DRC clean against supplier DRU | render → critique → DRC → **inline reviewer (design-reviewer)** |
| 7 | `signal_routing` | power routed | all signal nets routed; no unconnected; diff pairs length-matched within 10%; 45° angles only; DRC clean | render → critique → DRC → **milestone 3 (AskUserQuestion)** |
| 8 | `ground_zone_and_stitching` | signals routed | GND zone on B.Cu covers board; F.Cu remnants filled; stitching vias on 5 mm grid; zero ground plane islands; final DRC 0/0 | render → critique → DRC → final |

---

## Per-Checkpoint Loop (Self-Refine)

For EACH of the 8 checkpoints, execute this loop. The loop body is identical across checkpoints; only the actions in step 2 and the rubric flavor (PLACEMENT / POWER_ROUTING / SIGNAL_ROUTING / GROUND_PLANE / DRC) change.

```
START Checkpoint N:
  1. Re-read journal lessons-so-far from output/<board>_journal.md
     (Reflexion: apply lessons from prior checkpoints without being told again)
  2. Execute checkpoint actions (see "Per-Checkpoint Actions" below).
     - Use placement-skill.md primitives for checkpoints 1-5
     - Use routing-skill.md + scripts/routing_cli.py for checkpoints 6-7
     - Use scripts/routing_cli.py --action zone / fill_zones for checkpoint 8
  3. Render: python scripts/render_board.py output/<board>.kicad_pcb
     → {full, copper, svg} paths
  4. DRC (checkpoints 3-8): scripts/routing_cli.py --action drc
     - If violations > 0 OR unconnected_items > 0: re-enter rework (do NOT
       advance until DRC is 0/0)
  5. Critique: invoke visual-review-skill.md with
     {render_paths, checkpoint=N, iteration=I, prior_critique=...}
     → structured JSON critique
  6. Meta-check: invoke self-critique-skill.md on the critique
     → flags any of the 5 anti-patterns
  7. Decide: invoke iterative-refinement-skill.md with critique + N + journal
     → "proceed" | "rework" | "escalate"
  8. Branch:
     - PROCEED → append journal entry; advance to checkpoint N+1
     - REWORK (iter < 3) → apply rework scope; iter += 1; go to step 3
     - ESCALATE → state dump + AskUserQuestion (per iterative-refinement-skill)
  9. (Conditional gates) — checkpoints 4 + 6:
     → inline reviewer (design-reviewer subagent) — see "Inline Reviewer Gates"
  10. (Conditional milestones) — boundary of checkpoints 4 / 5 / 7:
     → AskUserQuestion milestone — see "AskUserQuestion Milestones"
  11. Append journal entry (always, regardless of outcome).
END Checkpoint N → advance to N+1 (or terminate if N == 8).
```

**Loop budget per checkpoint:** max 3 iterations, ~12K tokens per cycle. Both are firm — see `iterative-refinement-skill.md` → Loop Limits. Iter 4+ is thrashing; escalate at iter 3.

---

## Per-Checkpoint Actions

### Checkpoint 1: board_outline

- **Purpose:** Author the Edge_Cuts polygon at contract dimensions. Establishes the coordinate frame for everything downstream.
- **Preconditions:** all preconditions complete; journal initialized.
- **Actions:**
  1. Read contract `board_dimensions` (e.g., `20x30 mm`).
  2. Draw a closed polygon on `Edge_Cuts` layer using `PCB_SHAPE` (see `kicad-api-skill.md` → Board Outline section).
  3. Verify the polygon is closed (no gaps in the cuts layer).
- **Render:** `python scripts/render_board.py output/<board>.kicad_pcb` — primary critique target is the `full` PNG.
- **Critique:** invoke `visual-review-skill.md` with `checkpoint="board_outline"`. Rubric flavor: PLACEMENT (item 1: outline closure).
- **Decision:** per `iterative-refinement-skill.md` decision tree. Proceed at confidence ≥0.85 AND `pass_fail == "pass"`.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 1: board_outline` entry.

### Checkpoint 2: mechanical_placement

- **Purpose:** Place position-constrained items (mounting holes, connectors, switches, LEDs) at board edges. Defines the available interior area.
- **Preconditions:** outline done; coordinate frame established.
- **Actions:** Follow `placement-skill.md` Phase 1 (Mechanicals First). Connectors at edges with mating face outward; mounting holes at corners/fixed positions; switches accessible; ≥1.5 mm clearance to neighbors.
- **Render + Critique + Decision:** same loop pattern, PLACEMENT rubric.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 2: mechanical_placement` entry.

### Checkpoint 3: ic_placement

- **Purpose:** Place all ICs on F.Cu. Main IC centered; LDO/regulator near power input.
- **Preconditions:** mechanical done.
- **Actions:** Follow `placement-skill.md` Phase 2 (ICs). Main IC at board center with ≥1.5 mm clearance on all sides; voltage regulators near power input connector; pin-1 oriented per convention (top-left or marked dot visible).
- **Render + Critique + Decision:** PLACEMENT rubric; DRC starts here (run after every iter, must be 0/0 before proceed).
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 3: ic_placement` entry.

### Checkpoint 4: critical_passive_placement [INLINE REVIEWER + MILESTONE 1]

- **Purpose:** Place decoupling caps (within 5 mm of IC power pins), crystal (within 5 mm of MCU clock pins), ferrite + analog filter caps (adjacent to VDDA if applicable).
- **Preconditions:** IC placement done.
- **Actions:** Follow `placement-skill.md` Phase 3 (Critical Passives). One decap per VDD pin minimum; crystal symmetric layout; analog supply through ferrite bead.
- **Render + Critique + Decision:** PLACEMENT rubric; mandatory DRC check.
- **Inline Reviewer Gate:** after the visual-review verdict, invoke the `design-reviewer` subagent on the rendered PNG. Output → `review/<board>_inline_4.md`. CRITICAL findings re-enter the rework loop (count against the iteration budget). MAJOR findings logged. MINOR findings logged only. See **Inline Reviewer Gates** below.
- **Milestone 1 (AskUserQuestion):** at checkpoint boundary, fire `AskUserQuestion` with render paths + critique summary + 3 options. See **AskUserQuestion Milestones** below.
- **Loop budget:** max 3 iterations (inline reviewer rework counts against it).
- **Journal:** append `## Checkpoint 4: critical_passive_placement` entry.

### Checkpoint 5: remaining_passive_placement [MILESTONE 2]

- **Purpose:** Place all other passives (pull-ups, signal conditioning, LEDs + current-limit resistors, bypass caps).
- **Preconditions:** critical passives placed.
- **Actions:** Follow `placement-skill.md` Phase 4 (Remaining Passives). Pull-ups near the pin they service; resistors grouped by function with consistent orientation.
- **Render + Critique + Decision:** PLACEMENT rubric; DRC; per `placement-skill.md` Phase 5 (Verify Before Routing) — fix any courtyard overlaps NOW.
- **Milestone 2 (AskUserQuestion):** at boundary, fire `AskUserQuestion` — full-placement review before routing locks anything in.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 5: remaining_passive_placement` entry.

### Checkpoint 6: power_routing [INLINE REVIEWER]

- **Purpose:** Route GND, +3.3V (or VCC), VBUS at 0.5+ mm widths. Star topology from regulator output to each VDD pin.
- **Preconditions:** placement complete; DRU emitted (`output/<board>.kicad_dru` exists).
- **Actions:** Use `scripts/routing_cli.py` (NOT MCP routing tools — see CLAUDE.md). Route per `routing-skill.md` Priority 6 (Power Traces). One net at a time:
  ```bash
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action net_pads --net VCC
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action find_path --start <pad1> --end <pad2> --width 0.5
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action route --net VCC --waypoints "..." --width 0.5 --layer F.Cu
  ```
  Repeat for each power net. Analog supply (VDDA/3.3VA) goes through ferrite bead.
- **Render + Critique + Decision:** POWER_ROUTING rubric (7 items: trace width, full routing, star topology, decoupling loop integrity, analog/digital separation, no 90° bends, plane-piercing minimized); DRC must be 0/0 against the supplier DRU.
- **Inline Reviewer Gate:** invoke `design-reviewer` on the rendered PNG. Output → `review/<board>_inline_6.md`. CRITICAL findings re-enter rework. See **Inline Reviewer Gates**.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 6: power_routing` entry.

### Checkpoint 7: signal_routing [MILESTONE 3]

- **Purpose:** Route all signal nets at 0.3 mm (or 0.25 mm per `routing-skill.md` Trace Width Table). Diff pairs length-matched within 10%; 45° angles only.
- **Preconditions:** power routed; DRU emitted.
- **Actions:** Use `scripts/routing_cli.py` iteratively. Routing priority per `routing-skill.md`: crystal first (HSE_IN, HSE_OUT) → USB diff pair → NRST → I2C → USART → remaining signals. One net at a time:
  ```bash
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action unrouted
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action find_path --start <pad1> --end <pad2> --width 0.25
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action route --net <name> --waypoints "..." --width 0.25 --layer F.Cu
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action drc
  ```
- **Render + Critique + Decision:** SIGNAL_ROUTING rubric (7 items: all nets routed, diff pair integrity, 45° angles, trace-to-pad clearance, via stub minimization, crystal isolation, no traces under ICs); DRC must be 0/0.
- **Milestone 3 (AskUserQuestion):** at boundary, fire `AskUserQuestion` — final routing review before zones.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 7: signal_routing` entry.

### Checkpoint 8: ground_zone_and_stitching

- **Purpose:** Place B.Cu full-board GND zone (priority 0), F.Cu GND zone filling remaining space (priority 1), stitching vias on 5 mm grid along perimeter + near IC GND pins + crystal guard ring.
- **Preconditions:** signals routed.
- **Actions:** Use `scripts/routing_cli.py`:
  ```bash
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action zone --net GND --layer B.Cu --priority 0
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action zone --net GND --layer F.Cu --priority 1
  # Stitching vias (loop over grid):
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action via --net GND --pos <x>,<y>
  # ... repeat for each stitching position ...
  "<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action fill_zones
  ```
  Stitching grid: every 10-15 mm around perimeter; every IC VSS pin (within 1 mm); crystal guard ring every 2-3 mm.
- **Render + Critique + Decision:** GROUND_PLANE rubric (7 items: B.Cu zone covers board, no ground plane islands, stitching via grid, IC GND pin stitching, no splits under high-speed, crystal guard ring, F.Cu remnants filled); **final DRC must be 0/0** against the supplier DRU.
- **Loop budget:** max 3 iterations.
- **Journal:** append `## Checkpoint 8: ground_zone_and_stitching` entry.

---

## Reflexion Journal Protocol

Every checkpoint (including each iteration within a checkpoint) appends a structured entry to `output/<board>_journal.md`. The journal is the within-session Reflexion memory — at the start of each new checkpoint, re-read it to inherit lessons.

### File location

`output/<board>_journal.md` — created during preconditions (precondition 7).

### File structure

```markdown
# Build Journal — <board name>

## Checkpoint 1: board_outline
**Started**: 2026-05-16 14:23
**Iterations**: 1
### Decisions
- Outline drawn at 20×30 mm per contract
- Corners: 4-point rectangle (no rounded corners for v2.0)
### Issues found (iter 1..3)
- Iter 1: none
### Lessons for downstream checkpoints
- (none yet)
**Confidence**: 0.95
**Outcome**: proceed

## Checkpoint 2: mechanical_placement
**Started**: 2026-05-16 14:25
**Iterations**: 2
### Decisions
- J1 (power header) at left edge, 5mm from outline (clearance + connector access)
### Issues found (iter 1..3)
- Iter 1: J1 too close to outline (2mm < 3mm safety); MAJOR
- Iter 2: resolved by moving J1 to 5mm from edge
### Lessons for downstream checkpoints
- "When placing connectors, default to ≥5mm from outline; 3mm is the JLCPCB minimum but margin matters"
**Confidence**: 0.90
**Outcome**: proceed

## Checkpoint N: <name>
...
```

### Per-entry required fields

- `## Checkpoint N: <name>` — the H2 header (use the exact checkpoint name)
- `**Started**: <ISO timestamp>`
- `**Iterations**: <count>`
- `### Decisions` — bullet list of significant choices made this checkpoint
- `### Issues found (iter 1..3)` — one bullet per iteration listing issues + outcome
- `### Lessons for downstream checkpoints` — distilled wisdom to apply at checkpoint N+1 onward (this is the Reflexion payload)
- `**Confidence**: <final confidence after last iteration>`
- `**Outcome**: proceed | escalated | aborted`

### Append-only within a session

NEVER edit a prior checkpoint's journal entry. If you discover later that a checkpoint-3 decision was wrong, write a `### Correction note` block in the CURRENT checkpoint's entry — never modify the past entry.

### Re-read at start of each checkpoint

At the START of checkpoints 2-8, before executing actions, re-read `output/<board>_journal.md` and apply any `### Lessons for downstream checkpoints` from prior entries that bear on the current checkpoint. This is how Reflexion works without an explicit memory store: the file IS the memory.

### Escalation entries

If `iterative-refinement-skill.md` returns `escalate`, append a `## Escalation` block under the current checkpoint's entry with: iteration number, last 3 critiques' summaries, unresolved issues, escalation reason. Per `iterative-refinement-skill.md` → Escalation Protocol.

---

## Inline Reviewer Gates

At checkpoints **4** and **6**, after the visual-review verdict but before any milestone or proceed, invoke the `design-reviewer` subagent (from `.claude/agents/design-reviewer.md`) on the rendered PNG. The subagent is unchanged from v1; only the *invocation pattern* is new — v2 calls it inline at 4 + 6, not just at the end via `/review-board`.

### Protocol

1. **Pre-check.** Confirm `output/<board>_full.png` exists (it should, from the visual-review step). If missing, re-render first.
2. **Invoke.** Launch `design-reviewer` subagent. Pass it the PCB path + render path. Its output is a markdown findings document.
3. **Write to disk.** The subagent writes to `review/<board>_inline_<N>.md` where N is the checkpoint number (4 or 6).
4. **Parse findings by severity.**
   - **CRITICAL findings** → re-enter the rework loop. The iteration counter advances (CRITICAL inline-reviewer findings count against the 3-iter budget). Do NOT advance to the milestone or next checkpoint until cleared.
   - **MAJOR findings** → logged in the journal under `### Issues found`; reworked if the cycle has budget remaining; otherwise documented and carried forward.
   - **MINOR findings** → logged only; do not gate progress.
5. **Re-render + re-critique after rework.** Any CRITICAL fix triggers re-render + re-critique via the standard per-checkpoint loop.

### Output file format (`review/<board>_inline_<N>.md`)

```markdown
# Inline Design Review — Checkpoint <N> (<name>)
**Board**: <board>
**Reviewer**: design-reviewer subagent (Stage 2 inline gate)
**Render**: output/<board>_full.png

## Findings
| Severity | Description | Location | Recommendation |
|----------|-------------|----------|----------------|
| CRITICAL | ... | ... | ... |
| MAJOR | ... | ... | ... |
| MINOR | ... | ... | ... |

## Verdict
- [ ] No CRITICAL findings — proceed to milestone
- [ ] CRITICAL findings present — re-enter rework loop
```

### Why only checkpoints 4 + 6

Checkpoint 4 is the first point where the layout has enough committed structure (IC + critical passives) to catch coord-frame and proximity bugs. Checkpoint 6 is the first point where copper exists (power routing) and the layered structure can be reviewed for EMC / topology issues. Earlier inline gates would catch too little; later ones would catch issues too late to fix cheaply.

---

## AskUserQuestion Milestones

At the **boundary** of checkpoints **4, 5, and 7**, after all critique loops + (for 4 + 6) inline reviewer gates have cleared, fire `AskUserQuestion` to pause for owner review. The owner makes the final advance decision at each of these 3 touchpoints.

### Milestone touchpoints

| Milestone | Boundary | Purpose |
|-----------|----------|---------|
| 1 | after checkpoint 4 (critical_passive_placement) | Coord-frame sanity — owner verifies the early layout makes sense before more components commit |
| 2 | after checkpoint 5 (remaining_passive_placement) | Full-placement review — owner approves the placement before routing locks anything in |
| 3 | after checkpoint 7 (signal_routing) | Final routing review — owner approves before zones (zones are hard to revisit) |

### AskUserQuestion payload

```python
AskUserQuestion(
    question=f"Milestone {M} — checkpoint '{checkpoint_name}' complete. Review the render and choose.",
    context={
        "render_path_full": "output/<board>_full.png",
        "render_path_copper": "output/<board>_copper.png",
        "checkpoint_just_completed": "critical_passive_placement",
        "critique_summary": "...3-5 bullets distilled from the last visual-review JSON...",
        "iterations_used": 1,
        "next_checkpoint": "remaining_passive_placement",
    },
    options=[
        {"id": "proceed", "label": "Looks good — proceed to next checkpoint"},
        {"id": "rework_specific", "label": "Rework a specific issue (specify which)"},
        {"id": "abort", "label": "Abort the audition — record verdict and exit cleanly"},
    ],
)
```

### Owner choice → next action

- **proceed** → append journal entry with `**Outcome**: proceed`, advance to next checkpoint.
- **rework_specific** → owner specifies the issue in their response. Re-enter the rework loop with owner-supplied focus. Iteration counter resets to 1 under owner guidance (a fresh attempt, not iter 4). Update the journal with the owner's specified focus.
- **abort** → write final state dump to journal (`**Outcome**: aborted` + reason). Render one last full PNG. Exit with a structured handover message: which checkpoint reached, why aborted, where the artifacts live (`output/<board>.kicad_pcb`, `output/<board>_full.png`, `output/<board>_journal.md`).

### Critique summary requirement

The `critique_summary` passed to AskUserQuestion is 3-5 bullets distilled from the last `visual-review-skill.md` JSON emission. It is NOT the raw JSON. Format:

```
- All decoupling caps placed within 5 mm of IC power pins
- Crystal Y1 at (15, 12); 4.2 mm from MCU clock pins (within budget)
- 1 MINOR silk overlap (R3 designator) — fix queued for checkpoint 8
- Confidence 0.91; no CRITICAL or MAJOR issues from visual-review or inline reviewer
```

---

## DRC Enforcement (Per Checkpoint)

After every checkpoint that touches copper (3 onward), run DRC against the emitted supplier DRU before allowing proceed.

### Mechanism

```bash
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action drc
```

The output is JSON with `violations` (list) + `unconnected_items` (list). Both lists must be empty before the checkpoint exits.

### Rule

- **`violations` count > 0** → re-enter rework loop. Read the violations, fix the specific items, re-render, re-critique, re-DRC.
- **`unconnected_items` count > 0** (checkpoints 6 + 7 onward) → you have missing traces. Each unconnected item names the two pads needing copper. Route them.
- **ZERO violations AND ZERO unconnected_items required** before any checkpoint advance from checkpoint 3 onward.

### Checkpoint-by-checkpoint DRC expectations

| Checkpoint | DRC expectation |
|------------|-----------------|
| 1 | (no copper yet — DRC not run) |
| 2 | (no copper yet — DRC not run) |
| 3 | `violations == 0` (placement; courtyard + edge clearance only) |
| 4 | `violations == 0` |
| 5 | `violations == 0` |
| 6 | `violations == 0` AND power nets show as connected in `--action unrouted` |
| 7 | `violations == 0` AND all contract nets show as connected (`unrouted == []`) |
| 8 | `violations == 0` AND `unconnected_items == 0` (final) |

If DRC fails at iter 3 and rework cannot resolve it, that's an escalation per `iterative-refinement-skill.md`. Do not advance with DRC failures.

---

## Cross-Skill References

This skill orchestrates. It does not contain the rubrics or the decision logic — those live in the cross-referenced skills.

| Need | Skill |
|------|-------|
| Visual rubric per checkpoint + 10-entry failure-mode catalog + JSON output schema | [`visual-review-skill.md`](visual-review-skill.md) |
| Decide proceed/rework/escalate + rework scope targeting + loop limits + escalation protocol | [`iterative-refinement-skill.md`](iterative-refinement-skill.md) |
| Detect rubber-stamping/thrashing/over-correction/early-escalation/local-optimum-trap + convergence tracking | [`self-critique-skill.md`](self-critique-skill.md) |
| Supplier DRC profile loading + DRU emission + 5 risk axes | [`supplier-drc-rules.md`](../rules/supplier-drc-rules.md) |
| Placement primitives (5-phase workflow, clearance quick reference) | [`placement-skill.md`](placement-skill.md) |
| Routing primitives + routing CLI commands + EMC ground rules | [`routing-skill.md`](routing-skill.md) |
| pcbnew API conventions (BOARD, PCB_SHAPE, NETINFO_ITEM, etc.) | [`kicad-api-skill.md`](kicad-api-skill.md) |

---

## Abort Conditions

STOP and request owner review via `AskUserQuestion` (or terminate the audition if the owner aborts) if:

- An API function needed for the current checkpoint is missing from `api_manifest.json`
- DRC produces violations that 3 rework iterations cannot resolve (escalation per `iterative-refinement-skill.md`)
- A test fails with an unknown root cause that 1 investigation cycle cannot diagnose
- The contract is ambiguous about a specific requirement (rare — escape hatch via `AskUserQuestion` with `escalation_reason: "contract ambiguity"`)
- The owner picks `abort` at any milestone
- Token budget for the checkpoint exceeds 40K aggregate (per `self-critique-skill.md` Guard Rails)
- Oscillation detected (same net modified 3+ times)
- Over-correction with new CRITICAL count ≥2 in a single iteration's delta

Before aborting, ALWAYS:
1. Append a `**STATUS: ABORTED**` line to the current journal entry with reason
2. Re-render for a fresh PNG so the owner sees current state
3. Output a structured handover: checkpoint reached, artifacts on disk, suggested next step

---

## Anti-Scaffolding

This skill is **operational, not theoretical**. The 8 checkpoints map 1:1 to agent actions on a real `.kicad_pcb` file. No "TBD" or stub checkpoints. Every action in every checkpoint section above has a concrete `scripts/routing_cli.py` invocation or a placement-skill / kicad-api-skill primitive backing it. If you cannot perform a checkpoint's actions concretely, that's an abort condition, not an excuse to ship.

The journal is **real markdown on disk**, not a mental model. The inline reviewer **writes a real file** to `review/`. The AskUserQuestion **really pauses for owner input** — there is no "simulated" milestone. The DRC enforcement **runs the CLI and parses real output**. If any of these mechanisms is bypassed, the v2 architecture is broken — escalate.
