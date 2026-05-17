# Stage Contract: Stage 2 — Iterative Build Architecture (v2.0)

**CRITICAL RULE:** Workers are NOT allowed to mark tasks complete until the relevant batch checklist is fulfilled. Only the Auditor can declare this contract complete.

**Operational expansion**: see `docs/stages/stage-2-iterative-build-1m.md`. This contract is the interface + verification surface; the stage doc is the operational guide workers consult during implementation.

## Stage Overview
- **Scope**: Encode the 8-checkpoint iterative build loop into agent skills, routing, and protocols — Self-Refine per-checkpoint critique, Reflexion within-session episodic memory, inline `design-reviewer` gates at checkpoints 4 + 6, AskUserQuestion milestone protocol at the 3 owner touchpoints, `/review-board` repurposed as optional final adversarial pass. Produce the 6th `.context.md` file (agent-skills).
- **Depends on**: Stage 1 complete — `scripts/render_board.py` callable (consumed by visual-review-skill via PNG paths), `scripts/supplier_drc/` package (consumed by pcb-design-skill before routing), `contracts/blinker_555_contract.md` exists, `agent_docs/rules/supplier-drc-rules.md` exists (Stage 2 wires it into CLAUDE.md routing), `api_manifest.json` refreshed, `baselines/4.6/` populated, 5 of 6 `.context.md` files in place.
- **Produces**: Operational iterative build loop ready for Stage 3 audition execution — 3 new skill files (visual-review, iterative-refinement, self-critique), rewritten pcb-design-skill (8-checkpoint iterative), updated CLAUDE.md routing with 2 new "Before ANY Coding" gates, journal + inline-review + milestone protocols documented in skills, `/review-board` repurposed with hard preconditions, `docs/context/agent-skills.context.md` (6th .context.md).
- **Team composition**: 1 worker for the heavy authoring batches 2.1 + 2.2 (coherent voice across the 3 new skills + rewritten pcb-design-skill matters), 1 worker for batch 2.3 (CLAUDE.md + /review-board updates), + 1 tester + 1 auditor + 1 scribe. Batches are mostly sequential (2.1 → 2.2 → 2.3 → 2.4) because 2.2 references 2.1's skills and 2.3 references all. CTO must spawn the auditor LAST or serialize TaskCreate-then-spawn to avoid the premature-audit race.

---

## Batch 2.1: Three new skill files + structural tests

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Author visual-review-skill.md | Worker | `agent_docs/skills/visual-review-skill.md` (new, ~250 LOC md) | `tests/test_visual_review_skill.py` |
| Author iterative-refinement-skill.md | Worker | `agent_docs/skills/iterative-refinement-skill.md` (new, ~220 LOC md) | `tests/test_iterative_refinement_skill.py` |
| Author self-critique-skill.md | Worker | `agent_docs/skills/self-critique-skill.md` (new, ~200 LOC md) | `tests/test_self_critique_skill.py` |
| Author test_visual_review_skill.py | Worker | `tests/test_visual_review_skill.py` (new) | `pytest tests/test_visual_review_skill.py -v` green |
| Author test_iterative_refinement_skill.py | Worker | `tests/test_iterative_refinement_skill.py` (new) | `pytest tests/test_iterative_refinement_skill.py -v` green |
| Author test_self_critique_skill.py | Worker | `tests/test_self_critique_skill.py` (new) | `pytest tests/test_self_critique_skill.py -v` green |

### Interface Contract
**`agent_docs/skills/visual-review-skill.md` required sections** (markdown `## Section` headings):
- "Input Contract" — documents that skill consumes render_board return-dict + checkpoint name + iteration counter + optional prior critique
- "Per-Checkpoint Rubric" — covers PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC
- "Failure Mode Catalog" — exactly 10 entries in a table with columns: number, failure mode, visual signature, checkpoint, fix hint (entries 1–10 from `research/self_critique_patterns_research.md`)
- "Output Format" — JSON schema with required fields: `checkpoint`, `iteration`, `pass_fail`, `confidence`, `issues[]`, `recommendation`
- "Anti-Pattern Guard Rails" — explicit guardrails on critique quality

**`agent_docs/skills/iterative-refinement-skill.md` required sections:**
- "Decision Tree" — proceed/rework/escalate rules
- "Rework Scope Targeting" — issue→action→tool mapping table
- "Loop Limits" — must include "3 iterations" (or "max 3") AND "12K" (or "12,000") token budget reference
- "Escalation Protocol" — must reference `AskUserQuestion`; must include confidence threshold 0.5
- "Anti-Patterns" — listed and detected

**`agent_docs/skills/self-critique-skill.md` required sections:**
- 5 named anti-patterns from research: "Rubber-stamping", "Thrashing", "Over-correction", "Early escalation", "Local optimum trap"
- 8 named checkpoints (entry criteria): board_outline, mechanical_placement, ic_placement, critical_passive_placement, remaining_passive_placement, power_routing, signal_routing, ground_zone_and_stitching
- "Convergence Tracking" or equivalent section mentioning `confidence` + `trajectory`

**Test files contract**: each is a structural-only test (no execution) that:
- Reads the corresponding skill markdown file
- Asserts required section headings present
- Asserts named entities (checkpoints, anti-patterns, JSON fields) present
- Asserts numerical thresholds (3 iter, 12K tokens, 0.5/0.85 confidence) documented

### Verification Commands
```
$ pytest tests/test_visual_review_skill.py -v
Expected: all assertions pass — file exists, 5 required sections, 10-entry catalog, JSON schema fields
Failure means: skill file missing a section or required entity. Re-author the skill, do NOT modify the test.

$ pytest tests/test_iterative_refinement_skill.py -v
Expected: all assertions pass — file exists, decision tree, loop ceiling (3 iter + 12K), escalation triggers
Failure means: same — re-author skill.

$ pytest tests/test_self_critique_skill.py -v
Expected: all assertions pass — file exists, 5 anti-patterns, 8 checkpoints, convergence metrics
Failure means: same — re-author skill.

$ pytest tests/test_visual_review_skill.py tests/test_iterative_refinement_skill.py tests/test_self_critique_skill.py -v
Expected: combined run, all green
Failure means: investigate by individual test file.
```

### Batch Completion Criteria
- [ ] `agent_docs/skills/visual-review-skill.md` exists; all 5 required sections present; 10-entry failure-mode catalog; JSON output schema documents `checkpoint`, `iteration`, `pass_fail`, `confidence`, `issues[]`, `recommendation`
- [ ] `agent_docs/skills/iterative-refinement-skill.md` exists; decision tree, rework scope targeting, loop limits (3 iter + 12K tokens), escalation protocol (AskUserQuestion + 0.5 confidence threshold), anti-patterns sections all present
- [ ] `agent_docs/skills/self-critique-skill.md` exists; 5 anti-patterns named (Rubber-stamping, Thrashing, Over-correction, Early escalation, Local optimum trap); 8 checkpoints named (with entry criteria); convergence-tracking metrics documented
- [ ] `tests/test_visual_review_skill.py` exists; structural test for visual-review-skill.md
- [ ] `tests/test_iterative_refinement_skill.py` exists; structural test for iterative-refinement-skill.md
- [ ] `tests/test_self_critique_skill.py` exists; structural test for self-critique-skill.md
- [ ] `pytest tests/test_visual_review_skill.py tests/test_iterative_refinement_skill.py tests/test_self_critique_skill.py -v` all green
- [ ] Worker did NOT edit test files to make them pass (auditor verifies via diff against task assignment)
- [ ] No new ruff/lint violations introduced

---

## Batch 2.2: pcb-design-skill rewrite + journal protocol + inline reviewer gates + agent-skills.context.md

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| REWRITE pcb-design-skill.md to 8-checkpoint iterative architecture | Worker | `agent_docs/skills/pcb-design-skill.md` (rewritten, ~320 LOC md) | Manual walk-through; structural tests still green |
| Document Reflexion journal protocol inside pcb-design-skill.md | Worker | Embedded in pcb-design-skill.md | Manual: protocol structure documented |
| Document inline reviewer gates at checkpoints 4 + 6 inside pcb-design-skill.md | Worker | Embedded in pcb-design-skill.md | Manual: gates documented at correct checkpoints |
| Document AskUserQuestion milestone protocol inside pcb-design-skill.md + iterative-refinement-skill.md | Worker | Embedded in both files | Manual: milestones documented at boundaries of checkpoints 4 / 5 / 7 |
| Author agent-skills.context.md (6th .context.md file) | Worker | `docs/context/agent-skills.context.md` (new) | Manual readable; orients 4 v1 survivors + 3 new skills |

### Interface Contract
**`agent_docs/skills/pcb-design-skill.md` (REWRITTEN) required content:**
- Section: "When to Invoke" + "Required Reading" (in order: contract, supplier-drc-rules, visual-review, iterative-refinement, self-critique, placement-skill, routing-skill)
- Section: "The 8 Checkpoints" with a table containing all 8 checkpoint names + entry/exit criteria + gates column:
  1. board_outline
  2. mechanical_placement
  3. ic_placement
  4. critical_passive_placement (with `inline reviewer` + `milestone 1` markers)
  5. remaining_passive_placement (with `milestone 2` marker)
  6. power_routing (with `inline reviewer` marker)
  7. signal_routing (with `milestone 3` marker)
  8. ground_zone_and_stitching
- Section: "Per-Checkpoint Loop" — Self-Refine loop (render → critique → proceed/rework/escalate) with the iterative-refinement decision tree referenced
- Section: "Reflexion Journal Protocol" — markdown structure for `output/<board>_journal.md` with `## Checkpoint N: <name>` + `### Decisions` + `### Issues found` + `### Lessons for downstream checkpoints` + `**Confidence**` + `**Outcome**`
- Section: "Inline Reviewer Gates" — invokes `design-reviewer` subagent at checkpoints 4 and 6; output → `review/<board>_inline_<N>.md`; CRITICAL findings re-enter rework loop
- Section: "AskUserQuestion Milestones" — fires at boundary of checkpoints 4, 5, 7; payload structure (render_path_full, render_path_copper, checkpoint_just_completed, critique_summary, iterations_used, 3 options: proceed / rework_specific / abort)
- Section: "DRC Enforcement (Per Checkpoint)" — ZERO violations or no advance, starting at checkpoint 3 (when copper is added)

**`docs/context/agent-skills.context.md` required content:**
- Names all 7 skills: 4 v1 survivors (`placement-skill.md`, `kicad-api-skill.md`, `routing-skill.md`, `pcb-design-skill.md` [now rewritten]) + 3 new (`visual-review-skill.md`, `iterative-refinement-skill.md`, `self-critique-skill.md`)
- Routing relationships (which skill cross-references which)
- Load order during a build
- When each is invoked

### Verification Commands
```
$ test -f agent_docs/skills/pcb-design-skill.md && echo OK
Expected: OK
Failure means: rewrite not done.

$ grep -E "^## (When to Invoke|Required Reading|The 8 Checkpoints|Per-Checkpoint Loop|Reflexion Journal Protocol|Inline Reviewer Gates|AskUserQuestion Milestones|DRC Enforcement)" agent_docs/skills/pcb-design-skill.md
Expected: 8 section heading matches
Failure means: required section missing.

$ grep -cE "board_outline|mechanical_placement|ic_placement|critical_passive_placement|remaining_passive_placement|power_routing|signal_routing|ground_zone_and_stitching" agent_docs/skills/pcb-design-skill.md
Expected: ≥8 matches (each checkpoint name mentioned at least once)
Failure means: checkpoint name missing or misspelled.

$ grep "design-reviewer" agent_docs/skills/pcb-design-skill.md
Expected: at least one match (in inline reviewer gates section)
Failure means: inline reviewer gate not wired in skill.

$ grep "AskUserQuestion" agent_docs/skills/pcb-design-skill.md
Expected: at least one match
Failure means: milestone protocol not documented in pcb-design-skill.

$ test -f docs/context/agent-skills.context.md && echo OK
Expected: OK
Failure means: 6th .context.md not authored.

$ ls docs/context/ | wc -l
Expected: 6 (render-pipeline, supplier-drc, contracts, baselines, routing-primitives, agent-skills)
Failure means: wrong file count — investigate.

$ pytest tests/test_visual_review_skill.py tests/test_iterative_refinement_skill.py tests/test_self_critique_skill.py -v
Expected: still green (no regressions from Batch 2.1)
Failure means: 2.2 work broke 2.1 invariants.
```

### Batch Completion Criteria
- [ ] `agent_docs/skills/pcb-design-skill.md` rewritten; contains all 8 required `##` section headings
- [ ] 8 checkpoint names present in skill (verified by grep)
- [ ] `design-reviewer` invocation documented at checkpoints 4 and 6 (inline reviewer gates section)
- [ ] `AskUserQuestion` invocation documented at boundary of checkpoints 4, 5, 7 (milestone protocol section)
- [ ] Reflexion journal markdown structure documented with `## Checkpoint N: <name>` + `### Decisions` + `### Issues found` + `### Lessons for downstream checkpoints`
- [ ] DRC enforcement per checkpoint documented (starting at checkpoint 3)
- [ ] `docs/context/agent-skills.context.md` exists; names all 7 skills (4 survivors + 3 new); documents routing relationships + load order
- [ ] `docs/context/` contains exactly 6 files
- [ ] All Batch 2.1 structural tests still green (no regressions)
- [ ] Worker did NOT edit Batch 2.1 test files
- [ ] No new ruff/lint violations introduced

---

## Batch 2.3: CLAUDE.md routing update + /review-board repurpose

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Update CLAUDE.md with 4 new routing rows | Worker | `CLAUDE.md` (modified) | grep verifies all 4 rows present |
| Add visual-loop gate + supplier-DRC gate to "Before ANY Coding" | Worker | `CLAUDE.md` (modified) | grep verifies both gates present |
| Update /review-board command for final-pass-only role | Worker | `.claude/commands/review-board.md` (modified) | grep verifies precondition section |

### Interface Contract
**`CLAUDE.md` required additions:**
- 4 new rows in the "Task Routing" table for:
  - "Reviewing a rendered checkpoint" → `agent_docs/skills/visual-review-skill.md`
  - "Deciding proceed/rework/escalate" → `agent_docs/skills/iterative-refinement-skill.md`
  - "Self-checking critique posture" → `agent_docs/skills/self-critique-skill.md`
  - "Loading supplier DRC profile" → `agent_docs/rules/supplier-drc-rules.md`
- 2 new gate items in the "Before ANY Coding" section:
  - "Visual-loop gate (v2)": references 8-checkpoint loop + `scripts/render_board.py` + `visual-review-skill.md`
  - "Supplier-DRC gate (v2)": references contract `supplier:` metadata + `load_supplier_profile()` + `emit_kicad_dru()` + `agent_docs/rules/supplier-drc-rules.md`

**`.claude/commands/review-board.md` required updates:**
- Clarification that `/review-board` runs ONLY after a full audition completes (post-build only)
- Preconditions section: refuses if `output/<board_name>.kicad_pcb` or `output/<board_name>_full.png` missing
- Preserves the 3-subagent flow (design-reviewer → design-defender → design-referee)
- Preserves output artifacts: `review/<board>_review.md`, `review/<board>_defense.md`, `review/<board>_verdict.md`

### Verification Commands
```
$ grep -cE "(visual-review-skill\.md|iterative-refinement-skill\.md|self-critique-skill\.md|supplier-drc-rules\.md)" CLAUDE.md
Expected: ≥4 matches
Failure means: at least one new routing entry missing from CLAUDE.md.

$ grep -E "(Visual-loop gate|Supplier-DRC gate)" CLAUDE.md
Expected: both gates present
Failure means: "Before ANY Coding" section not updated.

$ grep -E "(Precondition|Preconditions)" .claude/commands/review-board.md
Expected: at least one match (precondition section present)
Failure means: /review-board precondition not documented.

$ grep -E "(output/.*\.kicad_pcb|_full\.png)" .claude/commands/review-board.md
Expected: matches for the required-file preconditions
Failure means: hard refuse condition not documented.

$ pytest -v
Expected: full suite green (no regressions from CLAUDE.md or /review-board updates)
Failure means: investigate which test broke and why CLAUDE.md change affected it.
```

### Batch Completion Criteria
- [ ] `CLAUDE.md` Task Routing table contains all 4 new rows (visual-review, iterative-refinement, self-critique, supplier-drc)
- [ ] `CLAUDE.md` "Before ANY Coding" section contains "Visual-loop gate" item with references to 8-checkpoint loop + render_board + visual-review-skill
- [ ] `CLAUDE.md` "Before ANY Coding" section contains "Supplier-DRC gate" item with references to load_supplier_profile + emit_kicad_dru + supplier-drc-rules
- [ ] `.claude/commands/review-board.md` clarifies post-audition-only role
- [ ] `.claude/commands/review-board.md` has Preconditions section requiring `output/<board>.kicad_pcb` AND `output/<board>_full.png`
- [ ] `.claude/commands/review-board.md` preserves 3-subagent flow (reviewer → defender → referee)
- [ ] Full `pytest -v` test suite still green (no regressions)
- [ ] No new ruff/lint violations introduced

---

## Batch 2.4: Integration verification (end-to-end dry run)

### Deliverables Table
| Task | Owner | Output | Test |
|------|-------|--------|------|
| Author stub contract for dry run | Worker | `contracts/_dryrun_stub.md` (new; `_` prefix flags non-production) | Manual: 5-component, 3-net dummy parseable |
| Execute dry run on stub contract | Worker | Runtime artifacts in `output/` + `review/` | (verified via 5 named criteria below) |
| Author dryrun log | Worker | `docs/auditions/_stage2_dryrun_log.md` (new) | Manual: each of (a)–(e) recorded with PASS/FAIL |

### Interface Contract
**`contracts/_dryrun_stub.md` required content:**
- YAML front-matter with `supplier: jlcpcb` + layer_count + dimensions
- 5 dummy components, 3 dummy nets
- "DESIGN FROM THIS CONTRACT ONLY" clause
- Minimal but parseable by the same agent invocation pattern as `blinker_555_contract.md`

**Dry run verification — 5 named criteria** (each must PASS for batch completion):
- (a) `output/_dryrun_stub_journal.md` populated with sections for all 8 checkpoints
- (b) `review/_dryrun_stub_inline_4.md` AND `review/_dryrun_stub_inline_6.md` both exist (inline reviewer fired at checkpoints 4 + 6)
- (c) 3 AskUserQuestion exchanges captured (milestones 1 / 2 / 3 — at boundary of checkpoints 4 / 5 / 7); recorded in dryrun log
- (d) Skill load order matches CLAUDE.md routing (verifiable by reading agent's transcript for sequence of file reads)
- (e) `output/_dryrun_stub.kicad_dru` emitted BEFORE any routing checkpoint (verifiable by timestamp comparison — DRU file mtime < routing artifact mtime)

**`docs/auditions/_stage2_dryrun_log.md` required content:**
- Each of (a)–(e) listed with PASS/FAIL verdict + 1-line evidence
- Any anomalies recorded
- Suggested fixes if any FAIL

### Verification Commands
```
$ test -f contracts/_dryrun_stub.md && echo OK
Expected: OK
Failure means: stub contract not authored.

$ test -f output/_dryrun_stub_journal.md && echo OK
Expected: OK
Failure means: dry run did not produce journal — wiring broken.

$ test -f review/_dryrun_stub_inline_4.md && test -f review/_dryrun_stub_inline_6.md && echo OK
Expected: OK
Failure means: inline reviewer gates did not fire at one or both checkpoints.

$ test -f output/_dryrun_stub.kicad_dru && echo OK
Expected: OK
Failure means: supplier-DRC gate did not fire — DRU not emitted.

$ test -f docs/auditions/_stage2_dryrun_log.md && grep -c "PASS\|FAIL" docs/auditions/_stage2_dryrun_log.md
Expected: file exists; ≥5 PASS/FAIL verdicts recorded
Failure means: dryrun log incomplete.

$ grep -E "Milestone (1|2|3)" docs/auditions/_stage2_dryrun_log.md
Expected: 3 matches
Failure means: not all 3 AskUserQuestion milestones recorded.
```

### Batch Completion Criteria
- [ ] `contracts/_dryrun_stub.md` exists with required structure (front-matter, components, nets, "DESIGN FROM CONTRACT ONLY" clause)
- [ ] Dry run executed; runtime artifacts produced:
  - [ ] `output/_dryrun_stub_journal.md` (with sections for all 8 checkpoints)
  - [ ] `output/_dryrun_stub.kicad_dru` (emitted before any routing checkpoint)
  - [ ] `review/_dryrun_stub_inline_4.md` (inline reviewer fired at checkpoint 4)
  - [ ] `review/_dryrun_stub_inline_6.md` (inline reviewer fired at checkpoint 6)
- [ ] 3 AskUserQuestion milestone exchanges captured during dry run (records in dryrun log)
- [ ] Skill load order verified to match CLAUDE.md routing (visual-review-skill before iterative-refinement-skill, etc.)
- [ ] `docs/auditions/_stage2_dryrun_log.md` exists; all 5 criteria recorded with PASS/FAIL verdicts; anomalies + suggested fixes noted
- [ ] All 5 criteria recorded as PASS in dryrun log (if any FAIL: fix and re-run before batch complete)
- [ ] Full `pytest -v` test suite still green
- [ ] No new ruff/lint violations introduced

---

## Stage Integration Criteria (ALL batches done)
- [ ] All 4 batch checklists fulfilled (2.1 / 2.2 / 2.3 / 2.4)
- [ ] Full test suite green: `pytest -v` → all Stage 1 tests + 3 new structural tests + no regressions
- [ ] Cross-module: an agent reading `CLAUDE.md` can find all 3 new skills + 1 new rule via the routing table within 30 seconds
- [ ] Cross-module: an agent reading the rewritten `pcb-design-skill.md` can identify (a) the 8 checkpoints, (b) the 3 milestone insertion points, (c) the 2 inline-review insertion points, (d) the journal append protocol, (e) the loop-ceiling rules — all within a single read
- [ ] Cross-module: Batch 2.4 dry run confirms operational wiring end-to-end
- [ ] `python scripts/verify_mcp.py` still exits 0 (no MCP regressions)
- [ ] `python scripts/verify_toolchain.py` still exits 0
- [ ] `git status` shows clean working tree (all Stage 2 work committed)
- [ ] `docs/context/` contains 6 files (5 from Stage 1 + agent-skills.context.md from Stage 2)
- [ ] `project_summary.md` updated with Stage 2 completion entry (scribe responsibility)
- [ ] Auditor has signed off on all items above with GREEN verdict
