# Stage 3: Audition — Detailed Reference (1M)

**Status:** AS PROPOSED (owner approved at architecture level in Phase 4; operational expansion below)
**Date:** 2026-05-16
**Project:** eda-kicad-agent v2
**Context budget:** 1M (Opus 4.7)

## Purpose
Execute the v2 pipeline end-to-end on the 555 LED blinker, with owner judging at the 3 milestones + final verdict. Document outcome in an audition record. Stretch: retry Blue Pill under v2 architecture and produce a side-by-side comparison against the 4.6 baseline to test whether v2 unblocks the original goal that Round 2 failed.

## Architecture
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Stage 3: Audition                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │  Batch 3.1: 555 audition execution                                   │    │
│   │                                                                      │    │
│   │  Fresh Opus 4.7 session                                              │    │
│   │  └─► load contracts/blinker_555_contract.md                          │    │
│   │  └─► load supplier profile, emit DRU (Stage 1 primitive)             │    │
│   │  └─► execute 8 checkpoints (Stage 2 loop)                            │    │
│   │       ├─ Checkpoint 1: board_outline                                 │    │
│   │       ├─ Checkpoint 2: mechanical_placement                          │    │
│   │       ├─ Checkpoint 3: ic_placement                                  │    │
│   │       ├─ Checkpoint 4: critical_passive_placement                    │    │
│   │       │     ├─ inline design-reviewer                                │    │
│   │       │     └─ AskUserQuestion (milestone 1)                         │    │
│   │       ├─ Checkpoint 5: remaining_passive_placement                   │    │
│   │       │     └─ AskUserQuestion (milestone 2)                         │    │
│   │       ├─ Checkpoint 6: power_routing                                 │    │
│   │       │     └─ inline design-reviewer                                │    │
│   │       ├─ Checkpoint 7: signal_routing                                │    │
│   │       │     └─ AskUserQuestion (milestone 3)                         │    │
│   │       └─ Checkpoint 8: ground_zone_and_stitching                     │    │
│   │  └─► final DRC against DRU → 0/0                                     │    │
│   │  └─► pytest tests/test_blinker_555.py -v → green                     │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                           │
│                                  ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐    │
│   │  Batch 3.2: Audition outcome documentation [HARD GATE]               │    │
│   │                                                                      │    │
│   │  docs/auditions/blinker_555_run1.md                                  │    │
│   │  └─► contract summary + toolchain versions                           │    │
│   │  └─► final renders embedded                                          │    │
│   │  └─► 3 milestone exchanges                                           │    │
│   │  └─► final verdict (owner: "credible 555" pass/fail)                 │    │
│   │  └─► journal excerpt + lessons for v2.x                              │    │
│   │                                                                      │    │
│   │  Owner reads doc + opens output/blinker_555_full.png                 │    │
│   │  Declares: credible 555 PASS / FAIL                                  │    │
│   │  ↓                                                                   │    │
│   │  HARD GATE: Batch 3.3 only proceeds if PASS                          │    │
│   └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                           │
│                  ┌───────────────┴───────────────┐                           │
│                  │                               │                           │
│                  ▼ (PASS)                        ▼ (FAIL)                    │
│   ┌─────────────────────────────────────┐  ┌──────────────────────────┐      │
│   │  Batch 3.3: Blue Pill v2 + 4.6 cmp  │  │  Stop. Record lessons    │      │
│   │                                      │  │  in run1.md → v2.x       │      │
│   │  Fresh Opus 4.7 session              │  │  scope.                  │      │
│   │  └─► contracts/blue_pill_contract.md │  └──────────────────────────┘      │
│   │  └─► 8 checkpoints again             │                                   │
│   │  └─► pytest tests/test_blue_pill.py  │                                   │
│   │  └─► render baselines/4.6/blue_pill  │                                   │
│   │       via scripts/render_board.py    │                                   │
│   │  └─► comparison doc                  │                                   │
│   │       docs/auditions/blue_pill_v2    │                                   │
│   │       _vs_4.6_comparison.md          │                                   │
│   │                                      │                                   │
│   │  Owner: "v2 unblocks Blue Pill goal" │                                   │
│   │  PASS / PARTIAL / FAIL               │                                   │
│   │  ← ULTIMATE v2 VERDICT               │                                   │
│   └─────────────────────────────────────┘                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Deliverables
| # | Deliverable | Key Files | Validation | Notes |
|---|-------------|-----------|------------|-------|
| 1 | 555 blinker board built end-to-end | `output/blinker_555.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`) | DRC 0/0 against emitted `output/blinker_555.kicad_dru`; all nets connected; board ≤20×30 mm | Built through full 8-checkpoint v2 loop; first proof v2 architecture works |
| 2 | Per-checkpoint renders (×8 × 2 views) | `output/blinker_555_full.png`, `output/blinker_555_copper.png` (final); `output/checkpoints/blinker_555_<N>_<name>_full.png` | Files exist after every checkpoint; final pair shows DRC-clean board with credible visual | 16 intermediate PNGs + 2 final = 18 PNG files |
| 3 | Reflexion journal | `output/blinker_555_journal.md` | Populated after every checkpoint; contains decisions + issues + lessons | Markdown append-only; structure per Stage 2 protocol |
| 4 | Inline reviewer outputs | `review/blinker_555_inline_4.md`, `review/blinker_555_inline_6.md` | Each contains design-reviewer subagent verdict; no unresolved CRITICAL at audition end | One after critical_passive_placement (4), one after power_routing (6) |
| 5 | Milestone records | (Embedded in audition doc Deliverable 6) | 3 AskUserQuestion exchanges captured with owner's decisions (proceed / rework / abort) at milestones 1/2/3 | Verbatim quote of owner's selection + any rework specification |
| 6 | Final audition outcome doc | `docs/auditions/blinker_555_run1.md` | Owner-readable: contract reference + final PNG embed + 3 milestone exchanges + final verdict + journal excerpt + lessons for v2.x | The audition deliverable — owner reads this + opens PNG to declare verdict |
| 7 | Test suite passes | `tests/test_blinker_555.py` | `pytest tests/test_blinker_555.py -v` green against `output/blinker_555.kicad_pcb` | All 5 tests from Stage 1 batch 1.3 must be green |
| 8 | Optional final adversarial pass | `review/blinker_555_review.md`, `review/blinker_555_defense.md`, `review/blinker_555_verdict.md` | If `/review-board blinker_555` invoked: all 3 files generated; verdict referenced in audition doc | Optional — owner's choice whether to run after audition completes |
| 9 | STRETCH: Blue Pill v2 build | `output/blue_pill_v2.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`) | ONLY IF Batch 3.2 hard gate passes; built end-to-end through v2 pipeline using `contracts/blue_pill_contract.md`; DRC 0/0; `tests/test_blue_pill.py` green | The "did v2 unblock the original goal" test |
| 10 | STRETCH: 4.6 vs v2 comparison | `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` | Side-by-side: visual PNG pair, checklist (4.6 owner-failed → v2 fixes), journal excerpts, owner's credibility judgment | The ultimate v2 verdict artifact |

## Technology
| Component | Choice | Why | Alternatives Considered |
|-----------|--------|-----|------------------------|
| Execution agent | Claude Opus 4.7 (1M context) | The model upgrade is half the v2 hypothesis; better visual reasoning than 4.6 | Sonnet 4.6 (token budget too tight at 350K+ for 8 checkpoints); Opus 4.6 (the failing baseline); Haiku 4 (too small for visual reasoning) |
| Contract source | `contracts/blinker_555_contract.md` (Stage 1 deliverable) | Pure contract-only build; no reference image; tests v2 infrastructure end-to-end | Building from a reference image (rejected in Phase 1 — autonomy purity); building from CSV netlist (lower-level test); building from schematic file (mixes layout + capture concerns) |
| Build loop | 8 checkpoints + 3 milestones (Stage 2 skill content) | Operational expansion of owner-approved architecture pillar; per-checkpoint render + critique catches issues early | 12-step monolithic (v1's approach — failed); 4 mega-checkpoints (too coarse for course-correction); 16 micro-checkpoints (per-component, too granular, would exhaust token budget) |
| Visual feedback | `scripts/render_board.py` (Stage 1 deliverable) | <2 s per checkpoint render; dark-BG PNG matches KiCad UI | Per-action render (every component placement — too noisy); end-only render (loses iterative signal — v1's failure) |
| Critique stack | visual-review-skill + iterative-refinement-skill + self-critique-skill (Stage 2 deliverables) | Per-checkpoint Self-Refine; cross-checkpoint Reflexion; convergence-tracked; anti-pattern-detected | Single all-in-one skill (loses separation of concerns); pure JSON-rubric checker (loses semantic reasoning); manual owner critique every checkpoint (defeats agent autonomy goal) |
| Inline review | `design-reviewer` subagent at checkpoints 4 + 6 (Stage 2 wiring) | Catches issues during build before milestone pauses; existing v1 subagent reused | New inline reviewer (duplicates effort); /review-board only (catches issues too late — v1's failure mode) |
| Milestone pause | `AskUserQuestion` at milestones 1/2/3 (Stage 2 wiring) | Owner decision: proceed / rework / abort; native to harness | File-based pause (requires polling); 3 separate sessions (loses context); no milestones (owner can't course-correct) |
| DRC | `.kicad_dru` from `supplier_profiles/jlcpcb.yaml` (Stage 1 deliverable) | Supplier-anchored; matches the fab the board would actually go to | KiCad defaults (v1's mistake — hand-picked rules); no DRC during build (defeats purpose) |
| Final adversarial pass | `/review-board` repurposed (Stage 2 deliverable) | Optional; runs only after audition complete; preserves 3 v1 subagents | Mandatory final review (slows audition unnecessarily); skip entirely (loses adversarial check) |
| Stretch comparator | `baselines/4.6/blue_pill.kicad_pcb` (Stage 1 deliverable) | The Round 2 artifact owner judged goal-failed; head-to-head visual comparison | No comparator (no signal on "did v2 break through"); compare against contract checklist only (v1 already passes checklist + failed owner verdict) |

## Data Models / Schemas

### `docs/auditions/blinker_555_run1.md` structure
```markdown
# Audition: 555 LED Blinker, Run 1

## Metadata
- **Date**: 2026-05-XX
- **Agent**: Claude Opus 4.7 (1M context)
- **Contract**: contracts/blinker_555_contract.md
- **Supplier**: JLCPCB (via supplier_profiles/jlcpcb.yaml)
- **Toolchain**: KiCad 9.0.7, cairosvg 2.7.X, lxml 5.X.Y, Python 3.11

## Contract Summary
[1-paragraph restatement of the 555 contract's goal + key constraints]

## Build Artifacts
- Final board: `output/blinker_555.kicad_pcb`
- Final renders: `output/blinker_555_full.png` + `output/blinker_555_copper.png`
- Per-checkpoint renders: `output/checkpoints/blinker_555_*.png` (16 files)
- Reflexion journal: `output/blinker_555_journal.md`
- Inline reviewer outputs: `review/blinker_555_inline_4.md` + `review/blinker_555_inline_6.md`

## Milestone Exchanges

### Milestone 1 — after critical_passive_placement
- **Render shown**: `output/checkpoints/blinker_555_4_critical_passive_placement_full.png`
- **Critique summary**: [3-sentence summary from visual-review-skill]
- **Iterations used**: <N>
- **Owner decision**: proceed | rework_specific | abort
- **If rework_specific**: [exact issue owner flagged]

### Milestone 2 — after remaining_passive_placement
[Same structure]

### Milestone 3 — after signal_routing
[Same structure]

## Test Results
\`\`\`
$ pytest tests/test_blinker_555.py -v
test_component_count           PASSED
test_nets_routed               PASSED
test_drc_zero                  PASSED
test_dimensions                PASSED
test_components_on_f_cu        PASSED
========== 5 passed ==========
\`\`\`

## DRC Result
- Violations: 0
- Unconnected items: 0
- Against: `output/blinker_555.kicad_dru` (emitted from supplier_profiles/jlcpcb.yaml)

## Optional `/review-board` Result
[If invoked: link to 3 review files + 1-line verdict; else: "Not invoked."]

## FINAL VERDICT — Owner's Judgment
**Credible 555 LED Blinker?** [PASS | FAIL]

**Notes from owner** (1–3 paragraphs):
[Owner writes free-form judgment here. What looks right, what looks wrong,
 whether the architecture changes (visual loop, iterative checkpoints,
 supplier DRC) appear to have moved the needle vs 4.6 monolithic builds.]

## Journal Excerpts (lessons across checkpoints)
[Pull the "Lessons for downstream checkpoints" sections from the journal]

## Lessons for v2.x
[Owner's + agent's joint scope-creep prevention list — what showed up in this
 audition that v2.0 doesn't handle and should be considered for v2.x]
```

### `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` structure (STRETCH)
```markdown
# Comparison: Blue Pill v2 vs 4.6 Baseline

## Side-by-Side Visual
| 4.6 (Round 2, 2026-03-06) | v2 (Run 1, 2026-05-XX) |
|---|---|
| ![4.6 full](../output/blue_pill_4.6_full.png) | ![v2 full](../output/blue_pill_v2_full.png) |

## Checklist — 4.6 owner-failed → v2 fixes
| 4.6 Failure Mode | v2 Fix Path | v2 Result |
|---|---|---|
| Decoupling caps placed >10mm from MCU power pins | Checkpoint 4 visual-review-skill flags decap distance | Pass / Partial / Fail |
| GND zone fragmented (multiple islands) | Checkpoint 8 visual-review-skill flags island count | Pass / Partial / Fail |
| Silk text overlapping pads on U1 | DRU rule silk_line_width + silk_text_height | Pass / Partial / Fail |
| Crystal routing >25mm trace length | Checkpoint 7 visual-review-skill flags length-sensitive nets | Pass / Partial / Fail |
| [...more 4.6 issues from owner's verdict notes...] | [...] | [...] |

## Journal Excerpts — v2 Decisions 4.6 Missed
[Quote relevant Checkpoint N lessons from output/blue_pill_v2_journal.md]

## Test Result Parity
- 4.6: 54/54 passing (commit 4787d57)
- v2: <X>/<X> passing (output below)
\`\`\`
$ pytest tests/test_blue_pill.py -v
[output]
\`\`\`

## ULTIMATE VERDICT — Owner's Judgment
**Did v2 unblock the original Blue Pill goal?** [PASS | PARTIAL | FAIL]

**Notes from owner** (1–3 paragraphs):
[The answer to the v2 hypothesis: did the new architecture + 4.7 model break through
 where 4.6 + monolithic build failed?]

## Lessons for v2.x
[Joint scope-creep prevention list, oriented to the Blue Pill complexity tier]
```

## API Contracts
*(N/A for Stage 3 — this stage is operational, not infrastructure. The agent invokes Stage 1 and Stage 2 deliverables but does not produce new code APIs.)*

The relevant invocation patterns (consuming Stage 1 + 2 deliverables):

```python
# Pre-flight
$ python scripts/verify_mcp.py        # exit 0 = MCP ready
$ python scripts/verify_toolchain.py  # exit 0 = cairosvg + lxml + GTK3 ok
$ pytest -v                            # baseline green

# Audition entry — fresh Opus 4.7 session
# (no `/new-board blinker_555` slash command in v2.0; entry is "build me the 555
#  contract per the v2 routing" or equivalent prompt)

# Agent first action (per agent_docs/rules/supplier-drc-rules.md):
from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru
profile = load_supplier_profile("jlcpcb")  # from contract metadata
emit_kicad_dru(profile, Path("output/blinker_555.kicad_dru"))

# Per checkpoint:
from scripts.render_board import render_board
result = render_board(Path("output/blinker_555.kicad_pcb"))
# result["full"] → PNG path consumed by visual-review-skill

# Per milestone (4/5/7 boundaries):
AskUserQuestion(
    question="Milestone N — review render",
    context={ "render_path_full": str(result["full"]), ... },
    options=[
        {"id": "proceed", "label": "..."},
        {"id": "rework_specific", "label": "..."},
        {"id": "abort", "label": "..."},
    ],
)
```

## Batches

### Batch 3.1: 555 audition execution
**Objective**: Execute the v2 pipeline end-to-end on the 555 LED blinker. This is the proof-of-architecture batch.

**Note**: This batch is NOT CTO-worker-orchestrated. It is a single live session with owner present at the 3 milestones. The "tasks" below are the agent's runtime steps, not worker assignments.

#### Task 3.1.1: Pre-flight verification
- **Steps**:
  1. `python scripts/verify_mcp.py` → exit 0
  2. `python scripts/verify_toolchain.py` → exit 0
  3. `pytest -v` → baseline green (all 54 v1 tests + Stage 1 + Stage 2 tests)
  4. `git status` → commit any uncommitted Stage 1/2 work before audition starts
- **Failure means**: Audition aborted. Fix the pre-flight failure first. Do NOT start with a broken toolchain.

#### Task 3.1.2: Agent invocation
- **Pattern**: Open fresh Claude Code session on Opus 4.7. First prompt: point at `contracts/blinker_555_contract.md` and the v2 routing (CLAUDE.md). Agent reads contract, loads JLCPCB profile, emits DRU to `output/blinker_555.kicad_dru` as its first concrete action (per `agent_docs/rules/supplier-drc-rules.md`).

#### Task 3.1.3: Execute 8 checkpoints
- **Pattern**: Agent walks checkpoints 1 through 8 per `agent_docs/skills/pcb-design-skill.md`:
  1. `board_outline` — Edge_Cuts polygon → render → critique → proceed
  2. `mechanical_placement` — power header + any mounting holes → render → critique → proceed
  3. `ic_placement` — NE555 center → render → critique → proceed
  4. `critical_passive_placement` — C1 (timing) + R1/R2 near 555 pins → render → critique → **inline reviewer fires** → **milestone 1 AUQ**
  5. `remaining_passive_placement` — LED + R3 + C2 → render → critique → **milestone 2 AUQ**
  6. `power_routing` — VCC + GND ≥0.5mm → render → critique → **inline reviewer fires**
  7. `signal_routing` — TRIG, THR, DISCH, OUT → render → critique → **milestone 3 AUQ**
  8. `ground_zone_and_stitching` — B.Cu GND zone, stitching vias → render → critique
- **Artifacts produced** during each checkpoint:
  - `output/checkpoints/blinker_555_<N>_<name>_full.png` (and copper variant)
  - Append to `output/blinker_555_journal.md`
  - At 4 + 6: `review/blinker_555_inline_<N>.md`

#### Task 3.1.4: Final DRC
- **Pattern**: After checkpoint 8, run final DRC against `output/blinker_555.kicad_dru` → expect 0 violations, 0 unconnected. Record in journal.
- **Failure means**: Re-enter checkpoint 8 rework loop. Do NOT proceed to audition doc until DRC clean.

#### Task 3.1.5: Test suite
- **Pattern**: `pytest tests/test_blinker_555.py -v` against `output/blinker_555.kicad_pcb` → expect all 5 tests green.
- **Failure means**: Fix the failing test's underlying issue (board defect). Do NOT modify the test.

#### Task 3.1.6: Final renders
- **Pattern**: `python scripts/render_board.py output/blinker_555.kicad_pcb` → produces `output/blinker_555_full.png` + `output/blinker_555_copper.png`. These are the visuals owner reads at audition verdict time.

#### Validation Checkpoint — Batch 3.1
```bash
ls output/blinker_555.kicad_pcb output/blinker_555.kicad_dru output/blinker_555_full.png output/blinker_555_copper.png output/blinker_555_journal.md
# Expected: all 5 files exist

ls output/checkpoints/blinker_555_*.png | wc -l
# Expected: 16 PNGs (8 checkpoints × 2 views: full + copper)

ls review/blinker_555_inline_4.md review/blinker_555_inline_6.md
# Expected: both inline review files exist

pytest tests/test_blinker_555.py -v
# Expected: 5 passed

# All 3 milestones marked "proceed" by owner (verified via AUQ logs)
# DRC: 0/0 (verified via journal's final entry)
```

### Batch 3.2: Audition outcome documentation [HARD GATE]
**Objective**: Produce the owner-readable verdict artifact. Owner declares "credible 555" PASS or FAIL based on rendered PNG + audition doc + 3 milestone exchanges.

#### Task 3.2.1: Author blinker_555_run1.md
- **Files**: Create `docs/auditions/blinker_555_run1.md` per structure in "Data Models / Schemas" above
- **Pattern**: All 7 sections — Metadata, Contract Summary, Build Artifacts, Milestone Exchanges, Test Results, DRC Result, Final Verdict (owner fills), Journal Excerpts, Lessons for v2.x
- **Test**: Manual: owner reads it end-to-end and can answer "would I judge this credible?" without needing additional context

#### Task 3.2.2: Optional `/review-board` adversarial pass
- **Steps**: If owner wants additional adversarial check before final verdict:
  ```
  /review-board blinker_555
  ```
- **Pattern**: Repurposed slash command (Stage 2 batch 2.3 deliverable) runs the 3 review subagents (reviewer → defender → referee) against `output/blinker_555.kicad_pcb` + `output/blinker_555_full.png`; produces 3 markdown files; verdict referenced in audition doc

#### Task 3.2.3: Owner verdict
- **Pattern**: Owner reads `docs/auditions/blinker_555_run1.md` + opens `output/blinker_555_full.png` (and copper variant if useful). Declares verdict in "FINAL VERDICT" section of audition doc:
  - **PASS**: 3 milestones approved + final design judged credible as a 555 LED blinker
  - **FAIL**: any milestone aborted, OR final design judged not credible

#### Validation Checkpoint — Batch 3.2 [HARD GATE]
```bash
ls docs/auditions/blinker_555_run1.md
# Expected: file exists, all 7 sections present, owner verdict filled

# Read owner verdict
grep -A 2 "FINAL VERDICT" docs/auditions/blinker_555_run1.md
# Expected: PASS or FAIL declared

# Hard pass criterion: 3 milestones approved + final design judged credible
# Batch 3.3 only proceeds if this gate passes.
```

### Batch 3.3: STRETCH — Blue Pill v2 retry + 4.6 comparison (ONLY IF 3.2 GATE PASSES)
**Objective**: Execute v2 architecture against the Blue Pill (the original v1 failure case); produce side-by-side comparison against the 4.6 baseline. This is the ULTIMATE v2 verdict.

#### Task 3.3.1: Fresh session, Blue Pill audition
- **Pattern**: Open fresh Opus 4.7 Claude Code session. Point at `contracts/blue_pill_contract.md` (unchanged from v1). Agent walks same 8 checkpoints + 3 milestones. Owner judges.
- **Artifacts produced**:
  - `output/blue_pill_v2.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`)
  - `output/blue_pill_v2_journal.md`
  - `output/blue_pill_v2_full.png` + `output/blue_pill_v2_copper.png`
  - `output/checkpoints/blue_pill_v2_*.png` (16 files)
  - `review/blue_pill_v2_inline_4.md` + `review/blue_pill_v2_inline_6.md`

#### Task 3.3.2: v1 test suite
- **Pattern**: `pytest tests/test_blue_pill.py -v` against `output/blue_pill_v2.kicad_pcb` → expect all green. This is the v1 test suite acting as finish-line check.
- **Failure means**: Fix the failing test's underlying issue. Do NOT modify the test.

#### Task 3.3.3: Render 4.6 baseline
- **Pattern**: `python scripts/render_board.py baselines/4.6/blue_pill.kicad_pcb --output-dir output/`
- **Artifacts**: `output/blue_pill_4.6_full.png` + `output/blue_pill_4.6_copper.png`

#### Task 3.3.4: Author comparison doc
- **Files**: Create `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` per structure in "Data Models / Schemas" above
- **Pattern**: Side-by-side PNGs, checklist mapping 4.6 owner-failed dimensions to v2 fix paths, journal excerpts showing v2 decisions 4.6 missed, owner's credibility judgment

#### Task 3.3.5: Ultimate verdict
- **Pattern**: Owner declares "v2 unblocks the original Blue Pill goal" PASS / PARTIAL / FAIL in the comparison doc.

#### Validation Checkpoint — Batch 3.3
```bash
ls output/blue_pill_v2.kicad_pcb output/blue_pill_v2_full.png output/blue_pill_v2_journal.md
# Expected: all 3 files exist

ls output/blue_pill_4.6_full.png output/blue_pill_4.6_copper.png
# Expected: 4.6 baseline rendered for comparison

pytest tests/test_blue_pill.py -v
# Expected: all green (v1 test suite passes against v2 board)

ls docs/auditions/blue_pill_v2_vs_4.6_comparison.md
# Expected: file exists with owner's ultimate verdict
```

## Constraints
- **Performance**: Token budget ~350K for a full 8-checkpoint audition with 1 escalation per 2 checkpoints. Opus 4.7's 1M context is fine. If audition exceeds 500K tokens, that's a signal of severe thrashing — abort and escalate.
- **Performance**: Per-checkpoint wall time ≤5 min agent time (target); owner milestones ≤5 min each. Total wall: ~30 min agent + ~15 min owner = ~45 min for 555 audition.
- **Security**: Owner-judged. Owner is the security gate. No automated bypass of milestones.
- **Convention**: Fresh Claude Code session for each audition (555 and Blue Pill stretch). Do NOT continue from a previous audition's context.
- **Convention**: Owner must be available at milestones 1/2/3 BEFORE audition starts. If owner unavailable, defer audition. Do not run unattended in v2.0.
- **Convention**: The 4.6 baseline is read-only. Never modify `baselines/4.6/` during audition.
- **Convention**: Test files (`tests/test_blinker_555.py`, `tests/test_blue_pill.py`) are immutable during audition. Any test failure means board defect, fix the board.

## Extension Points
- **Multi-run auditions (v2.x)**: If audition fails, a re-run could benefit from cross-session Reflexion memory. Currently within-session only. Promote `output/<board>_journal.md` to persistent store if multi-run becomes the norm.
- **Quantitative credibility metrics (v2.x)**: Owner verdict is subjective. v2.x could augment with component-density / trace-length / via-count metrics for trend analysis across runs.
- **Fab order test (v2.x)**: Send `output/blinker_555.kicad_pcb` to JLCPCB for actual DFM review. Definitive proof of supplier-anchored DRC correctness.
- **Additional audition boards (v2.x)**: If 555 + Blue Pill both pass, add tier 3 audition (RP2040 minimal breakout, BeagleBone-style mid-complexity, etc.). Audition framework is reusable.
- **Automated audition (v2.x)**: Replace AUQ milestones with automated quality gates if owner trusts the auto-critique loop. Currently human-in-the-loop by design.

## Dependencies
- **Requires (Stage 1 complete)**: `scripts/render_board.py` (render primitive), `supplier_profiles/jlcpcb.yaml` + `scripts/supplier_drc/` (DRC primitives), `contracts/blinker_555_contract.md` (audition target), `baselines/4.6/blue_pill.kicad_pcb` (stretch comparator), refreshed `api_manifest.json`, `tests/test_blinker_555.py` collectible
- **Requires (Stage 2 complete)**: 3 new skills (visual-review, iterative-refinement, self-critique), rewritten `pcb-design-skill.md` (8-checkpoint iterative), updated `CLAUDE.md` routing + 2 new gates, journal + inline-review + milestone protocols wired in, `/review-board` repurposed
- **Requires (toolchain)**: `pytest -v` baseline green before audition starts; `verify_mcp.py` exit 0; `verify_toolchain.py` exit 0; KiCad 9.0.7 + cairosvg + lxml + GTK3 all working
- **Requires (owner-side)**: Owner availability at 3 milestone pauses for 555 audition (~15 min owner time); owner availability for final verdict reading (~10 min); owner availability for stretch comparison if 555 passes (~30 min)
- **Produces**: Audition verdict — the answer to the v2 hypothesis: "did visual loop + iterative checkpoints + supplier DRC + Opus 4.7 break through where 4.6 + monolithic build failed?" Lessons for v2.x scope. If stretch passes: validated v2 architecture against the original Blue Pill failure case.
- **Blocked by**: None internal. External blockers: owner time at milestones; owner time at final verdict; owner time for stretch comparison.

## Scope Boundaries
- **In scope**: End-to-end 555 audition via v2 pipeline; per-checkpoint renders + Reflexion journal + inline reviews + 3 milestone exchanges; audition outcome doc (`docs/auditions/blinker_555_run1.md`); optional final `/review-board` adversarial pass; STRETCH: Blue Pill v2 retry + 4.6 comparison doc (gated on 555 pass)
- **Deferred to v2.x**:
  - Multiple audition runs to measure variance (currently single run per board)
  - Automated audition-doc generator (currently agent + owner author manually)
  - Cross-session journal persistence (currently in-memory markdown only)
  - Fab order placement (no JLCPCB upload in v2.0; DRC against DRU is the proxy)
  - Cost-premium analysis (cost_premiums data is loaded but not surfaced in critique)
  - Multi-board audition (one audition per session)
  - Quantitative credibility metrics (subjective owner verdict only)
- **Trigger for promotion**:
  - If 555 audition needs >1 run to pass — promote cross-session Reflexion to v2.0 mid-flight
  - If owner ever asks "what does this cost at JLCPCB" — implement cost-premium surfacing
  - If a fab actually rejects an audition output — implement the deferred external DRC validators (Stage 1 stubs in `scripts/supplier_drc/validators.py`)
- **Out of scope entirely**: New supplier profiles (v2.x); new skills (v2.x); new render primitives (v2.x); architectural changes to the iterative loop (v2.x); changes to the test infrastructure; changes to the contract template
