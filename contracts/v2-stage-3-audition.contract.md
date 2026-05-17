# Stage Contract: Stage 3 — Audition (v2.0)

**CRITICAL RULE:** Workers are NOT allowed to mark tasks complete until the relevant batch checklist is fulfilled. Only the Auditor can declare this contract complete.

**Operational expansion**: see `docs/stages/stage-3-audition-1m.md`. This contract is the interface + verification surface; the stage doc is the operational guide consulted during the audition.

**NON-STANDARD STAGE — NO WORKER TEAM.** Stage 3 is NOT executed by CTO-spawned implementation workers. The "tasks" within each batch are the agent's runtime steps during a live audition session with the owner. The CTO's role for Stage 3 is to (a) verify Stage 1 + 2 are complete, (b) optionally spawn a scribe to keep `project_summary.md` current, (c) hand off to the owner for the audition session, (d) record the outcome.

## Stage Overview
- **Scope**: Execute the v2 pipeline end-to-end on the 555 LED blinker with owner judging at 3 milestones + final verdict; document outcome in `docs/auditions/blinker_555_run1.md`; STRETCH (gated on 555 pass): retry Blue Pill under v2, produce 4.6-vs-v2 comparison doc.
- **Depends on**: Stage 1 + Stage 2 complete (all integration criteria green per their contracts).
- **Produces**: Audition verdict — the answer to the v2 hypothesis: "did visual loop + iterative checkpoints + supplier DRC + Opus 4.7 break through where 4.6 + monolithic build failed?" Lessons for v2.x scope. If stretch passes: validated v2 architecture against the original Blue Pill failure case + side-by-side comparison artifact.
- **Team composition**: NO implementation worker team. The audition is a single live Claude Code session with Opus 4.7, owner present at 3 milestone touchpoints. Optional scribe (1) for `project_summary.md` updates. Optional auditor (1) for final stage sign-off (verifies the audition outcome doc and stretch comparison doc are complete and accurate). No tester (the agent runs `pytest tests/test_blinker_555.py -v` itself during Batch 3.1).

---

## Batch 3.1: 555 audition execution

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Pre-flight verification | Owner | (verification step, no new file) | `verify_mcp.py` + `verify_toolchain.py` + `pytest -v` all green |
| Agent reads contract, loads supplier profile, emits DRU | Agent (Opus 4.7) | `output/blinker_555.kicad_dru` | DRU file exists, parses in KiCad |
| Execute 8 checkpoints with per-checkpoint render + critique + journal | Agent | `output/blinker_555.kicad_pcb`, `output/blinker_555_journal.md`, `output/checkpoints/blinker_555_*.png` (16 files) | Each checkpoint advances only on critique pass |
| Inline reviewer fires at checkpoints 4 + 6 | Agent | `review/blinker_555_inline_4.md`, `review/blinker_555_inline_6.md` | Both files exist; no unresolved CRITICAL at audition end |
| AskUserQuestion fires at milestones 1 / 2 / 3 | Agent + Owner | (decisions captured for audition doc in Batch 3.2) | 3 AUQ exchanges; owner selects proceed/rework/abort each time |
| Final DRC against DRU | Agent | (recorded in journal) | 0 violations, 0 unconnected |
| Test suite execution | Agent | (recorded in journal + audition doc) | `pytest tests/test_blinker_555.py -v` 5/5 green |
| Final renders | Agent | `output/blinker_555_full.png`, `output/blinker_555_copper.png` | Both PNGs exist, non-zero |

### Interface Contract
**Pre-flight commands (run by owner):**
```bash
python scripts/verify_mcp.py        # must exit 0
python scripts/verify_toolchain.py   # must exit 0
pytest -v                            # baseline green (all v1 + Stage 1 + Stage 2 tests pass)
git status                           # commit any uncommitted work before audition
```

**Agent first action (per `agent_docs/rules/supplier-drc-rules.md`):**
```python
from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru
profile = load_supplier_profile("jlcpcb")  # parsed from contract metadata
emit_kicad_dru(profile, Path("output/blinker_555.kicad_dru"))
```

**Per-checkpoint loop (8 iterations):**
1. Execute checkpoint actions (place / route / zone)
2. `result = render_board(Path("output/blinker_555.kicad_pcb"))` → consumed by visual-review-skill
3. visual-review-skill → JSON critique
4. self-critique-skill → anti-pattern check
5. iterative-refinement-skill → proceed / rework / escalate decision
6. If checkpoint ∈ {4, 6}: invoke `design-reviewer` subagent on `result["full"]`
7. If checkpoint boundary ∈ {4, 5, 7}: `AskUserQuestion` with render path + critique summary + 3 options
8. Append journal entry per Reflexion protocol

**Artifact path invariants:**
- `output/blinker_555.kicad_pcb` exists at audition end (the built board)
- `output/blinker_555.kicad_dru` exists from agent first action (before any routing checkpoint)
- `output/blinker_555_journal.md` exists with 8 `## Checkpoint N: <name>` sections
- `output/checkpoints/` contains exactly 16 PNGs (8 checkpoints × 2 views: full + copper)
- `output/blinker_555_full.png` + `output/blinker_555_copper.png` are the final renders
- `review/blinker_555_inline_4.md` + `review/blinker_555_inline_6.md` exist

### Verification Commands
```
$ python scripts/verify_mcp.py
Expected: exit 0
Failure means: MCP not ready. Run `python scripts/setup_mcp.py` and restart Claude Code BEFORE audition.

$ python scripts/verify_toolchain.py
Expected: exit 0
Failure means: cairosvg / lxml / GTK3 not installed. Fix per error message before audition.

$ pytest -v
Expected: full baseline green (existing tests, no regressions from Stage 1 + 2)
Failure means: regression. Investigate and fix BEFORE starting audition.

$ ls output/blinker_555.kicad_pcb output/blinker_555.kicad_dru output/blinker_555_full.png output/blinker_555_copper.png output/blinker_555_journal.md
Expected: all 5 files exist after Batch 3.1
Failure means: audition incomplete. Re-enter checkpoint loop or escalate.

$ ls output/checkpoints/blinker_555_*.png | wc -l
Expected: 16 (8 checkpoints × 2 views)
Failure means: per-checkpoint renders incomplete.

$ ls review/blinker_555_inline_4.md review/blinker_555_inline_6.md
Expected: both files exist
Failure means: inline reviewer gates did not fire — wiring regression from Stage 2 batch 2.2.

$ pytest tests/test_blinker_555.py -v
Expected: 5 passed (test_component_count, test_nets_routed, test_drc_zero, test_dimensions, test_components_on_f_cu)
Failure means: board defect. Fix the underlying issue (NOT the test) and re-run.

Manual: open output/blinker_555_journal.md, verify 8 ## Checkpoint sections present.
Manual: open output/blinker_555_full.png, verify visual rendering is sensible (not blank, not corrupted).
```

### Batch Completion Criteria
- [ ] Pre-flight: `verify_mcp.py` exits 0, `verify_toolchain.py` exits 0, `pytest -v` baseline green
- [ ] Pre-flight: `git status` clean (Stage 1 + 2 work committed)
- [ ] `output/blinker_555.kicad_dru` emitted BEFORE any routing checkpoint
- [ ] `output/blinker_555.kicad_pcb` exists at audition end
- [ ] `output/blinker_555_journal.md` exists with 8 `## Checkpoint N: <name>` sections
- [ ] `output/checkpoints/` contains 16 PNGs (per-checkpoint renders × full + copper)
- [ ] `output/blinker_555_full.png` + `output/blinker_555_copper.png` exist as final renders
- [ ] `review/blinker_555_inline_4.md` exists (inline reviewer fired at checkpoint 4)
- [ ] `review/blinker_555_inline_6.md` exists (inline reviewer fired at checkpoint 6)
- [ ] No unresolved CRITICAL findings in either inline review file
- [ ] AskUserQuestion fired at milestones 1 / 2 / 3 (boundary of checkpoints 4 / 5 / 7); owner selected "proceed" for all 3 (rework_specific allowed mid-flight; abort terminates audition)
- [ ] Final DRC against `output/blinker_555.kicad_dru`: 0 violations, 0 unconnected items
- [ ] `pytest tests/test_blinker_555.py -v` 5/5 green
- [ ] Test files (`tests/test_blinker_555.py`) NOT modified by agent during audition
- [ ] No new ruff/lint violations introduced

---

## Batch 3.2: Audition outcome documentation [HARD GATE]

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Author audition outcome doc | Agent + Owner | `docs/auditions/blinker_555_run1.md` (new) | Manual: all 9 required sections + owner verdict |
| Optional: invoke `/review-board blinker_555` for final adversarial pass | Owner (optional) | `review/blinker_555_review.md`, `review/blinker_555_defense.md`, `review/blinker_555_verdict.md` (3 files, if invoked) | If invoked: all 3 files exist; verdict referenced in audition doc |
| Owner declares verdict | Owner | "FINAL VERDICT" section of audition doc filled | PASS or FAIL declared |

### Interface Contract
**`docs/auditions/blinker_555_run1.md` required sections:**
1. "Metadata" — date, agent (Opus 4.7), contract path, supplier, toolchain versions (KiCad 9.0.7, cairosvg, lxml, Python)
2. "Contract Summary" — 1-paragraph restatement of 555 contract goal + key constraints
3. "Build Artifacts" — list of paths (board, renders, per-checkpoint renders, journal, inline reviews)
4. "Milestone Exchanges" — 3 subsections (Milestone 1 / 2 / 3) with: render path shown, critique summary, iterations used, owner decision (proceed / rework_specific / abort), if rework_specific the exact issue
5. "Test Results" — verbatim output of `pytest tests/test_blinker_555.py -v` (5 passed)
6. "DRC Result" — 0 violations / 0 unconnected; DRU file reference
7. "Optional /review-board Result" — if invoked: links to 3 review files + 1-line verdict; else: "Not invoked."
8. "FINAL VERDICT — Owner's Judgment" — PASS or FAIL declaration + 1–3 paragraph free-form owner notes
9. "Journal Excerpts" + "Lessons for v2.x" — pulled from journal's per-checkpoint "Lessons for downstream checkpoints" sections; v2.x suggestions

**Hard gate criterion**: `FINAL VERDICT` must be one of:
- **PASS** — All 3 milestones owner-approved AND final design owner-judged credible as a 555 LED blinker
- **FAIL** — Any milestone aborted OR final design owner-judged not credible

If PASS: Batch 3.3 proceeds.
If FAIL: Stage 3 stops here. Record lessons in `Lessons for v2.x`. Auditor signs off on Stage 3 outcome as FAIL.

### Verification Commands
```
$ test -f docs/auditions/blinker_555_run1.md && echo OK
Expected: OK
Failure means: audition doc not authored.

$ grep -cE "^## (Metadata|Contract Summary|Build Artifacts|Milestone Exchanges|Test Results|DRC Result|Optional|FINAL VERDICT|Journal Excerpts|Lessons for v2.x)" docs/auditions/blinker_555_run1.md
Expected: ≥9 matches (one per required section)
Failure means: required section missing — auditor should flag specific section.

$ grep -E "^### Milestone (1|2|3)" docs/auditions/blinker_555_run1.md
Expected: 3 matches (subsections for each milestone)
Failure means: milestone exchanges not fully recorded.

$ grep -E "FINAL VERDICT.*\b(PASS|FAIL)\b" docs/auditions/blinker_555_run1.md
Expected: exactly one match (either PASS or FAIL declared)
Failure means: owner has not declared verdict — audition incomplete.

# Hard gate check (for Batch 3.3 unblock):
$ grep -E "FINAL VERDICT.*\bPASS\b" docs/auditions/blinker_555_run1.md && echo "GATE_OPEN" || echo "GATE_CLOSED"
Expected: GATE_OPEN if 555 audition passed; GATE_CLOSED if failed (Stage 3 stops at Batch 3.2)
```

### Batch Completion Criteria
- [ ] `docs/auditions/blinker_555_run1.md` exists; contains all 9 required `## Section` headings
- [ ] All 3 milestone exchange subsections (`### Milestone 1`, `### Milestone 2`, `### Milestone 3`) present
- [ ] Each milestone subsection records: render path shown, critique summary, iterations used, owner decision
- [ ] Test results section contains verbatim pytest output (5 passed)
- [ ] DRC result section declares 0 violations / 0 unconnected
- [ ] Final verdict section contains exactly one of PASS or FAIL (not both, not neither)
- [ ] Final verdict section contains 1–3 paragraph owner notes (not empty)
- [ ] Journal excerpts section quotes at least 3 "Lessons for downstream checkpoints" from journal
- [ ] Lessons for v2.x section populated (not "TBD")
- [ ] If `/review-board` was invoked: 3 review files exist AND verdict referenced in audition doc
- [ ] No new ruff/lint violations introduced
- [ ] **HARD GATE**: If verdict == PASS, Batch 3.3 is unblocked. If verdict == FAIL, Stage 3 terminates at this batch.

---

## Batch 3.3: STRETCH — Blue Pill v2 retry + 4.6 comparison (GATED on Batch 3.2 PASS)

**Precondition**: Batch 3.2 hard gate must be PASS (555 audition credible). If FAIL or PARTIAL, this batch does NOT execute.

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Fresh session: Blue Pill audition via v2 pipeline | Agent (Opus 4.7, new session) | `output/blue_pill_v2.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`), `output/blue_pill_v2_journal.md`, `output/blue_pill_v2_full.png` + `_copper.png`, `output/checkpoints/blue_pill_v2_*.png` (16 files), `review/blue_pill_v2_inline_4.md` + `_6.md` | Same artifact invariants as Batch 3.1 but for blue_pill |
| v1 test suite as finish-line check | Agent | (test output recorded in comparison doc) | `pytest tests/test_blue_pill.py -v` green against `output/blue_pill_v2.kicad_pcb` |
| Render 4.6 baseline | Agent | `output/blue_pill_4.6_full.png`, `output/blue_pill_4.6_copper.png` | Both PNGs exist (from `baselines/4.6/blue_pill.kicad_pcb` via `scripts/render_board.py`) |
| Author comparison doc | Agent + Owner | `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` (new) | All 6 required sections + ultimate verdict |
| Owner declares ultimate verdict | Owner | "ULTIMATE VERDICT" section filled | PASS / PARTIAL / FAIL declared |

### Interface Contract
**`output/blue_pill_v2.kicad_pcb` artifact invariants** (same pattern as 555):
- `output/blue_pill_v2.kicad_pcb` exists; built via v2 8-checkpoint loop
- `output/blue_pill_v2.kicad_dru` exists (same JLCPCB profile)
- `output/blue_pill_v2_journal.md` exists with 8 checkpoint sections
- `output/checkpoints/blue_pill_v2_*.png` contains 16 PNGs
- `review/blue_pill_v2_inline_4.md` + `_6.md` exist

**`docs/auditions/blue_pill_v2_vs_4.6_comparison.md` required sections:**
1. "Side-by-Side Visual" — table with 2 columns: 4.6 (Round 2, 2026-03-06) full render | v2 (Run 1, today) full render
2. "Checklist — 4.6 owner-failed → v2 fixes" — table mapping each 4.6 owner-flagged failure mode to v2 fix path and result (PASS/PARTIAL/FAIL per row)
3. "Journal Excerpts — v2 Decisions 4.6 Missed" — quotes from `output/blue_pill_v2_journal.md` showing v2 caught what 4.6 missed
4. "Test Result Parity" — both `tests/test_blue_pill.py` runs (4.6 baseline + v2 new); both should be 54/54 (or current count); v2 run output verbatim
5. "ULTIMATE VERDICT — Owner's Judgment" — "Did v2 unblock the original Blue Pill goal?" PASS / PARTIAL / FAIL + 1–3 paragraph owner notes (the answer to the v2 hypothesis)
6. "Lessons for v2.x" — joint owner + agent scope-creep prevention list, oriented to Blue Pill complexity tier

### Verification Commands
```
# Precondition gate (must be GATE_OPEN before this batch runs):
$ grep -E "FINAL VERDICT.*\bPASS\b" docs/auditions/blinker_555_run1.md && echo "GATE_OPEN"
Expected: GATE_OPEN
Failure means: Batch 3.2 did not pass; Batch 3.3 must NOT execute.

$ ls output/blue_pill_v2.kicad_pcb output/blue_pill_v2_journal.md output/blue_pill_v2_full.png output/blue_pill_v2_copper.png
Expected: all 4 files exist
Failure means: Blue Pill v2 audition incomplete.

$ ls output/checkpoints/blue_pill_v2_*.png | wc -l
Expected: 16
Failure means: per-checkpoint renders incomplete.

$ ls review/blue_pill_v2_inline_4.md review/blue_pill_v2_inline_6.md
Expected: both exist
Failure means: inline reviewer regression.

$ pytest tests/test_blue_pill.py -v
Expected: all tests green against output/blue_pill_v2.kicad_pcb
Failure means: v2 board defect — fix the board (NOT the test).

$ ls output/blue_pill_4.6_full.png output/blue_pill_4.6_copper.png
Expected: both PNGs exist (rendered from baselines/4.6/blue_pill.kicad_pcb)
Failure means: 4.6 baseline render failed.

$ test -f docs/auditions/blue_pill_v2_vs_4.6_comparison.md && echo OK
Expected: OK
Failure means: comparison doc not authored.

$ grep -cE "^## (Side-by-Side|Checklist|Journal Excerpts|Test Result|ULTIMATE VERDICT|Lessons)" docs/auditions/blue_pill_v2_vs_4.6_comparison.md
Expected: ≥6 matches
Failure means: required section missing.

$ grep -E "ULTIMATE VERDICT.*\b(PASS|PARTIAL|FAIL)\b" docs/auditions/blue_pill_v2_vs_4.6_comparison.md
Expected: exactly one match (one of the 3 verdicts declared)
Failure means: owner has not declared ultimate verdict.
```

### Batch Completion Criteria
- [ ] Precondition: Batch 3.2 PASS verdict confirmed before this batch runs
- [ ] Blue Pill v2 audition artifacts present:
  - [ ] `output/blue_pill_v2.kicad_pcb` (+ `.kicad_pro`, `.kicad_prl`)
  - [ ] `output/blue_pill_v2_journal.md` (8 checkpoint sections)
  - [ ] `output/blue_pill_v2_full.png` + `_copper.png` (final renders)
  - [ ] `output/checkpoints/blue_pill_v2_*.png` (16 PNGs)
  - [ ] `review/blue_pill_v2_inline_4.md` + `_6.md` (inline reviewer outputs)
- [ ] `pytest tests/test_blue_pill.py -v` green against `output/blue_pill_v2.kicad_pcb`
- [ ] Test files (`tests/test_blue_pill.py`) NOT modified by agent during stretch audition
- [ ] 4.6 baseline rendered: `output/blue_pill_4.6_full.png` + `_copper.png` exist
- [ ] `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` exists; contains all 6 required `## Section` headings
- [ ] Side-by-side visual table with both PNG references
- [ ] Checklist mapping 4.6 owner-failed dimensions to v2 fix paths with per-row PASS/PARTIAL/FAIL
- [ ] Test parity section with both test result snippets
- [ ] ULTIMATE VERDICT contains exactly one of PASS / PARTIAL / FAIL
- [ ] Ultimate verdict has 1–3 paragraph owner notes (not empty)
- [ ] Lessons for v2.x section populated (not "TBD")
- [ ] No new ruff/lint violations introduced

---

## Stage Integration Criteria (ALL batches done)
- [ ] Batch 3.1 completion criteria all green (555 audition execution complete)
- [ ] Batch 3.2 hard gate decision recorded (PASS or FAIL) — if FAIL, stage terminates here
- [ ] If Batch 3.2 PASS: Batch 3.3 completion criteria all green (stretch comparison done)
- [ ] If Batch 3.2 FAIL: lessons documented in `blinker_555_run1.md` "Lessons for v2.x" section; stage terminates with that as the outcome
- [ ] Full test suite green: `pytest -v` (no regressions; if `tests/test_blue_pill.py` was previously skipped due to missing output, it is now expected to pass against the v2 build)
- [ ] Audition outcome documented in `docs/auditions/blinker_555_run1.md`
- [ ] If stretch ran: ultimate v2 verdict documented in `docs/auditions/blue_pill_v2_vs_4.6_comparison.md`
- [ ] `project_summary.md` updated with Stage 3 outcome — including owner's "credible 555" verdict and (if applicable) "v2 unblocks original goal" ultimate verdict
- [ ] No test file tampering: `tests/test_blinker_555.py` + `tests/test_blue_pill.py` unchanged from Stage 1 + v1 baseline (auditor verifies via diff)
- [ ] Auditor has signed off on all items above with GREEN verdict

**v2 hypothesis answer recorded**: this stage's completion is the moment the project answers the falsifiable hypothesis stated in `architecture_v2_proposal.md`:
> "If we add a visual feedback loop + iterative checkpoint architecture + supplier-anchored DRC + Opus 4.7's improved visual reasoning, the agent will produce a board that you (the domain expert) judge as credible."

Final stage verdicts:
- 555 credibility: PASS / FAIL (Batch 3.2)
- Blue Pill v2 unblocks original goal: PASS / PARTIAL / FAIL / NOT_TESTED (Batch 3.3)
