# Stage 2: Iterative Build Architecture — Detailed Reference (1M)

**Status:** AS PROPOSED (owner approved at architecture level in Phase 4; operational expansion below)
**Date:** 2026-05-16
**Project:** eda-kicad-agent v2
**Context budget:** 1M (Opus 4.7)

## Purpose
Encode the 8-checkpoint iterative build loop into agent skills, routing, and protocols — Self-Refine per-checkpoint critique, Reflexion within-session episodic memory, inline `design-reviewer` gates at checkpoints 4 + 6, AskUserQuestion milestone protocol at the 3 owner touchpoints, and `/review-board` repurposed as an optional final adversarial pass — so Stage 3 can execute the 555 audition end-to-end.

## Architecture
```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Stage 2: Iterative Build Architecture                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌────────────────────┐       ┌────────────────────────────────┐          │
│   │  Batch 2.1         │       │  Batch 2.2                     │          │
│   │  3 new skills +    │       │  pcb-design-skill rewrite +    │          │
│   │  structural tests  │       │  journal + inline reviewer +   │          │
│   │                    │       │  agent-skills.context.md       │          │
│   │ visual-review      │──────►│                                │          │
│   │ iterative-refine   │       │  pcb-design (8 checkpoints,    │          │
│   │ self-critique      │       │   render→critique loop,        │          │
│   │ test_×3            │       │   journal append, reviewer     │          │
│   │                    │       │   at 4+6, AUQ at 3 milestones) │          │
│   └────────────────────┘       └────────────────────────────────┘          │
│            │                            │                                  │
│            └────────────┬───────────────┘                                  │
│                         ▼                                                  │
│           ┌────────────────────────────────────────┐                       │
│           │  Batch 2.3                             │                       │
│           │  CLAUDE.md routing update +            │                       │
│           │  /review-board repurpose               │                       │
│           │                                        │                       │
│           │  4 new routing rows                    │                       │
│           │  visual-loop gate + supplier-DRC gate  │                       │
│           │  /review-board → final-pass only       │                       │
│           └────────────────────────────────────────┘                       │
│                         │                                                  │
│                         ▼                                                  │
│           ┌────────────────────────────────────────┐                       │
│           │  Batch 2.4                             │                       │
│           │  Stub-contract dry run                 │                       │
│           │                                        │                       │
│           │  Synthetic 5-component contract        │                       │
│           │  Walk all 8 checkpoints                │                       │
│           │  Verify: journal, reviewer at 4+6,     │                       │
│           │  AUQ at 1/2/3, DRU emitted             │                       │
│           └────────────────────────────────────────┘                       │
│                         │                                                  │
│                         ▼                                                  │
│           ┌────────────────────────────────────────┐                       │
│           │  Stage 2 Complete                      │                       │
│           │  → Stage 3 audition can execute        │                       │
│           └────────────────────────────────────────┘                       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Per-checkpoint runtime loop (encoded by Stage 2 skills, executed in Stage 3):
  ┌─────────────────────────────────────────────────────────────────────┐
  │  START Checkpoint N (8 total)                                       │
  │     │                                                               │
  │     ├─► Execute checkpoint actions (place/route/zone/etc.)          │
  │     │                                                               │
  │     ├─► render_board() → full + copper PNGs                         │
  │     │                                                               │
  │     ├─► visual-review-skill: structured JSON critique               │
  │     │      { pass_fail, confidence, issues[], recommendation }      │
  │     │                                                               │
  │     ├─► self-critique-skill: posture check, anti-pattern detect     │
  │     │                                                               │
  │     ├─► iterative-refinement-skill: proceed / rework / escalate?    │
  │     │      ├─► PROCEED (conf ≥0.85) → checkpoint N+1                │
  │     │      ├─► REWORK (iter<3, conf>0.5) → re-enter execute step    │
  │     │      └─► ESCALATE (iter≥2, conf<0.5) → AskUserQuestion        │
  │     │                                                               │
  │     ├─► [N==4 OR N==6] inline design-reviewer subagent fires        │
  │     │      → review/<board>_inline_<N>.md                           │
  │     │      → CRITICAL findings re-enter rework loop                 │
  │     │                                                               │
  │     ├─► [N==4 OR N==5 OR N==7] AskUserQuestion milestone            │
  │     │      → owner: proceed / rework / abort                        │
  │     │                                                               │
  │     └─► Append to output/<board>_journal.md (Reflexion memory)      │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘
```

## Deliverables
| # | Deliverable | Key Files | Validation | Notes |
|---|-------------|-----------|------------|-------|
| 1 | Visual-review skill | `agent_docs/skills/visual-review-skill.md` (~250 LOC md) | Loads via CLAUDE.md routing; structured JSON output schema documented; rubric covers PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC; 10-entry failure-mode catalog | Per-checkpoint visual rubric; consumes `render_board()` output paths; produces JSON critique |
| 2 | Iterative-refinement skill | `agent_docs/skills/iterative-refinement-skill.md` (~220 LOC md) | Decision tree (proceed/rework/escalate) + loop limits (max 3 iter, ~12K tokens/cycle) + routing CLI coordination + escalation protocol | Drives the loop; thresholds documented; calls visual-review + self-critique |
| 3 | Self-critique meta-skill | `agent_docs/skills/self-critique-skill.md` (~200 LOC md) | 5 anti-patterns + mitigations; convergence metrics; per-checkpoint exit criteria with confidence thresholds | Meta-skill — tells agent WHEN to invoke visual-review vs iterative-refinement; anti-pattern detection |
| 4 | Rewritten pcb-design-skill | `agent_docs/skills/pcb-design-skill.md` (~320 LOC md, REWRITTEN) | 12-step monolithic workflow replaced with 8-checkpoint iterative architecture; references new skills + supplier-drc-rules.md | Embeds: journal protocol, inline reviewer wiring, AskUserQuestion milestone harness, DRC-per-checkpoint gate |
| 5 | Updated CLAUDE.md routing | `CLAUDE.md` (UPDATED) | 4 new routing rows added; visual-loop gate + supplier-DRC gate added to "Before ANY Coding" section | Preserves all v1 rows; adds rows for visual-review, iterative-refinement, self-critique, supplier-drc |
| 6 | Reflexion journal protocol | (Embedded in pcb-design-skill.md + iterative-refinement-skill.md) | Journal file format documented; agent writes to `output/<board>_journal.md` after every checkpoint; cross-checkpoint lessons retrieved on next checkpoint | Markdown append-only within session; section headers `## Checkpoint N: <name>`; cross-session persistence DEFERRED to v2.x |
| 7 | Inline reviewer gate integration | (Embedded in pcb-design-skill.md) | Checkpoints 4 (after critical_passive_placement) + 6 (after power_routing) explicitly invoke `design-reviewer` subagent on rendered PNG | Output → `review/<board>_inline_<N>.md`; CRITICAL findings re-enter rework loop before milestone or proceed |
| 8 | AskUserQuestion milestone harness | (Embedded in pcb-design-skill.md + iterative-refinement-skill.md) | 3 milestones defined; each fires AUQ with render path + critique summary + 3 options | Milestone 1: after critical_passive_placement (coord-frame sanity); Milestone 2: after remaining_passive_placement (full placement review); Milestone 3: after signal_routing (final review before audition verdict) |
| 9 | /review-board repurposed | `.claude/commands/review-board.md` (UPDATED) | Final-pass adversarial mode; preserves 3 subagents (reviewer/defender/referee); precondition requires completed board + PNG | Removes during-build invocation; clarifies "post-audition only"; refuses if `output/<board>.kicad_pcb` or `output/<board>_full.png` missing |
| 10 | Three skill structural tests | `tests/test_visual_review_skill.py`, `tests/test_iterative_refinement_skill.py`, `tests/test_self_critique_skill.py` | Each validates documented sections + JSON schemas in its target skill file; structural-only (no execution) | Symmetric coverage (one test per new skill); reads markdown file, asserts named headings + table presence + JSON schema parseable |
| 11 | Context doc for agent skills | `docs/context/agent-skills.context.md` | Orientation for 4 surviving + 3 new skills; routing relationships; load order; when each is invoked | The 6th `.context.md` file (1–5 produced by Stage 1) |

## Technology
| Component | Choice | Why | Alternatives Considered |
|-----------|--------|-----|------------------------|
| Critique loop pattern | Self-Refine (Madaan 2023) per-checkpoint | Empirically ~20% improvement over single-shot; best-fit for render→critique→refine flow; well-documented agentic pattern | Vision-Guided Iterative Refinement (very close; chosen Self-Refine for broader literature); Constitutional AI (less effective for spatial reasoning); Devil's Advocate alone (insufficient for proactive refinement) |
| Cross-checkpoint memory | Reflexion (Shinn 2023) within-session episodic memory | Lessons at outline-done inform decisions at placement-done; well-documented; persistence cleanly deferable to v2.x | Persistent vector store (overkill for single-audition); per-checkpoint state-machine (loses lesson context); pure stateless (loses cross-checkpoint learning) |
| Verification pattern | CoVe (Chain of Verification) | Independent "what could fail?" questions before commit | Single-shot self-review (less rigorous); external validator only (loses agent reasoning context) |
| Loop ceiling | Max 3 iterations per checkpoint | Iter 1 catches 70–80%; iter 2 cascading; iter 3 plateau; iter 4+ thrashing (Self-Refine literature) | 2 iter (too tight, misses cascading fixes); 5 iter (thrashing risk + token cost); unbounded (catastrophic) |
| Token budget per cycle | ~12K | 3K critique + 4K rework + 2K tool exec + 3K re-render + 1K buffer | 6K (insufficient for rework planning); 24K (wasteful, no quality gain) |
| Confidence threshold (proceed) | ≥0.85 | Below this, rework or escalate; literature precedent | 0.7 (too permissive, lets borderline through); 0.95 (too strict, triggers excessive rework) |
| Confidence threshold (escalate) | <0.5 after iter 2 | Agent doesn't know what's wrong; human needed | <0.3 (waits too long, wastes iter 3 cycles); <0.7 (escalates prematurely) |
| Convergence rule | Monotonic issue count ↓ AND monotonic confidence ↑ | Any reversal indicates thrashing → escalate | Pure issue count (misses confidence regression); pure confidence (misses issue regression) |
| Anti-pattern detection | 5 named patterns + explicit detection rules | Catches the 5 named failure modes (rubber-stamping, thrashing, over-correction, early escalation, local optimum trap) before they burn cycles | Generic "looks wrong" heuristic (too vague); no detection at all (allows pathology) |
| Milestone pause UX | `AskUserQuestion` native tool call | Blocks cleanly; no file polling; consistent with v1 conversational UX | File-based pause (requires polling loop, fragile); HTTP webhook (overkill, network dep); session-restart (loses context) |
| Journal storage | `output/<board>_journal.md` (markdown, append-only within session) | Human-readable; matches v1 `output/` convention; gitignored by default | SQLite (heavyweight for single-session); JSONL (less readable); separate file per checkpoint (cross-checkpoint retrieval friction) |
| Inline reviewer | `design-reviewer` subagent (v1, unchanged) | Existing 3-agent pipeline survives; only invocation pattern changes (now inline at 4+6 instead of only on /review-board) | Custom inline reviewer (duplicates existing subagent); structural-only checker (no semantic critique) |

## Data Models / Schemas

### visual-review-skill structured JSON output
```json
{
  "checkpoint": "critical_passive_placement",
  "iteration": 1,
  "pass_fail": "pass" | "fail",
  "confidence": 0.92,
  "issues": [
    {
      "severity": "CRITICAL" | "MAJOR" | "MINOR",
      "type": "PLACEMENT" | "POWER_ROUTING" | "SIGNAL_ROUTING" | "GROUND_PLANE" | "DRC",
      "failure_mode_id": 4,
      "description": "Decoupling cap C2 is 12mm from U1 pin 8; should be <5mm.",
      "location": { "ref": "C2", "x_mm": 14.2, "y_mm": 5.1 },
      "fix_hint": "Re-place C2 within 5mm of U1.8; rotate 90° if needed for trace approach."
    }
  ],
  "pass_criteria_met": {
    "all_critical_passives_within_5mm_of_ic_power_pins": false,
    "no_component_overlap": true,
    "components_on_correct_layer": true
  },
  "recommendation": "rework" | "proceed" | "escalate",
  "notes": "Cap placement looks good except C2. Single-issue rework."
}
```

### iterative-refinement-skill decision tree
```
Input: visual-review JSON output, current iteration N, journal lessons-so-far
Output: { decision: "proceed" | "rework" | "escalate", reasoning, next_action }

1. If pass_fail == "pass" AND confidence >= 0.85:
     decision = "proceed"
2. If N >= 3:
     decision = "escalate"
     reason = "max iterations reached"
3. If confidence < 0.5 AND N >= 2:
     decision = "escalate"
     reason = "agent does not know what's wrong"
4. If any issue.severity == "CRITICAL":
     decision = "rework"
     scope = filter(issues, severity in ["CRITICAL", "MAJOR"])
5. Else (only MINOR issues):
     If confidence >= 0.85:
       decision = "proceed"
     Else:
       decision = "rework"
       scope = minor_fixes_subset (limit by token budget)

Anti-pattern overrides:
  - If same net modified 3+ times → "escalate" (thrashing)
  - If 2+ consecutive iters with zero issues → adversarial mode iter 2 (rubber-stamping)
  - If new CRITICAL after rework → re-enter visual-review (over-correction)
```

### Reflexion journal structure
```markdown
# Build Journal — <board name>

## Checkpoint 1: board_outline
**Started**: 2026-05-16 14:23
**Iterations**: 1
### Decisions
- Outline drawn at 20×30 mm per contract
- Corners: 4-point rectangle (no rounded corners for v2.0)
### Issues found
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
### Issues found
- Iter 1: J1 too close to outline (2mm < 3mm safety); MAJOR
- Iter 2: resolved by moving J1 to 5mm from edge
### Lessons for downstream checkpoints
- "When placing connectors, default to ≥5mm from outline; 3mm is the JLCPCB minimum but margin matters"
**Confidence**: 0.90
**Outcome**: proceed

## Checkpoint N: <name>
...
```

### Inline reviewer output (`review/<board>_inline_<N>.md`)
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

### AskUserQuestion milestone payload (3 options pattern)
```python
# Embedded in pcb-design-skill.md — milestone protocol
AskUserQuestion(
    question=f"Milestone {M} — {milestone_name}: review the render before proceeding.",
    context={
        "render_path_full": "output/blinker_555_full.png",
        "render_path_copper": "output/blinker_555_copper.png",
        "checkpoint_just_completed": "critical_passive_placement",
        "critique_summary": "...3-line summary of visual-review-skill output...",
        "iterations_used": 1,
        "next_checkpoint": "remaining_passive_placement",
    },
    options=[
        {"id": "proceed", "label": "Looks good — proceed to next checkpoint"},
        {"id": "rework_specific", "label": "Rework specific issue (specify)"},
        {"id": "abort", "label": "Abort audition — record verdict"},
    ],
)
```

## API Contracts

### Skill invocation patterns (from CLAUDE.md routing)
```
| If you are...                       | Read this file                                    |
|-------------------------------------|---------------------------------------------------|
| Reviewing a rendered checkpoint     | `agent_docs/skills/visual-review-skill.md`        |
| Deciding proceed/rework/escalate    | `agent_docs/skills/iterative-refinement-skill.md` |
| Self-checking critique posture      | `agent_docs/skills/self-critique-skill.md`        |
| Loading supplier DRC profile        | `agent_docs/rules/supplier-drc-rules.md`          |
```

### "Before ANY Coding" gates (CLAUDE.md additions)
```markdown
## Before ANY Coding (UPDATED for v2)
1. Read `agent_docs/rules/coding-rules.md` first.
2. **NEW (v2): Visual-loop gate.** If the task is a PCB build, you MUST use the
   8-checkpoint iterative loop. After every checkpoint, call `scripts/render_board.py`
   and consult `visual-review-skill.md`. Do NOT do monolithic builds.
3. **NEW (v2): Supplier-DRC gate.** If the contract has a `supplier:` metadata field,
   you MUST `load_supplier_profile()` and `emit_kicad_dru()` BEFORE any routing
   actions. See `agent_docs/rules/supplier-drc-rules.md`.
```

### /review-board updated precondition
```markdown
# /review-board <board_name>

## v2 Repurpose
Runs ONLY after a full audition completes. Inline reviewer gates (Stage 2 batch 2.2)
handle in-build catches. Use /review-board for the optional final adversarial pass.

## Precondition (hard refuse if missing)
- `output/<board_name>.kicad_pcb` must exist
- `output/<board_name>_full.png` must exist

## Flow (unchanged from v1)
1. design-reviewer reads board + render → review/<board>_review.md
2. design-defender reads review → review/<board>_defense.md
3. design-referee reads both → review/<board>_verdict.md
```

## Batches

### Batch 2.1: Three new skill files + structural tests
**Objective**: Author the 3 meta-skills + 3 structural tests; the skills are the operational guidance that drives Stage 3's audition loop.

#### Task 2.1.1: Author visual-review-skill.md
- **Files**: Create `agent_docs/skills/visual-review-skill.md` (~250 LOC md)
- **Pattern**: 5 sections per `research/self_critique_patterns_research.md` scaffolding — (1) Input contract (rendered PNG + checkpoint type + iteration counter), (2) Per-checkpoint visual rubric (PLACEMENT/POWER_ROUTING/SIGNAL_ROUTING/GROUND_PLANE/DRC), (3) Failure-mode catalog (10 entries from research), (4) Structured JSON output schema, (5) Anti-pattern guard rails
```markdown
# Visual Review Skill

## Input Contract
You receive:
- Rendered PNG path(s) from `scripts/render_board.py` (full + copper)
- Checkpoint name (one of 8)
- Current iteration (1, 2, or 3)
- Optional: prior critique JSON (if rework iteration)

## Per-Checkpoint Rubric
### PLACEMENT
- All ICs on F.Cu
- No component overlap (footprint courtyards do not intersect)
- Decoupling caps within 5mm of IC power pins
...
### POWER_ROUTING
- Power traces ≥0.5mm (vs signal default)
...

## Failure Mode Catalog (10 entries)
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

## Output Format (JSON)
{ ... see "Data Models / Schemas" section ... }

## Anti-Pattern Guard Rails
- Do NOT return "looks fine" without listing what you checked
- Do NOT return confidence >0.85 unless all pass_criteria_met == true
- Do NOT skip the failure-mode catalog walk
```
- **Test**: `pytest tests/test_visual_review_skill.py -v` validates this file's structure (next task)

#### Task 2.1.2: Author iterative-refinement-skill.md
- **Files**: Create `agent_docs/skills/iterative-refinement-skill.md` (~220 LOC md)
- **Pattern**: 6 sections per research — (1) Decision tree (proceed/rework/escalate), (2) Rework scope targeting (issue → action → routing CLI command mapping), (3) Loop limits & escalation (max 3 iter, ~12K tokens/cycle, escalation triggers), (4) Coordination with routing CLI (concrete pcb_status, pcb_route, pcb_render, pcb_drc commands), (5) Escalation protocol (state dump, render, structured handover message), (6) Anti-patterns to avoid
```markdown
# Iterative Refinement Skill

## Decision Tree
[See "Data Models / Schemas" → iterative-refinement-skill decision tree]

## Rework Scope Targeting
| Issue type | Action | Tool |
|-----------|--------|------|
| Component overlap | Move component | `pcb_move_component` (via MCP) |
| Decap too far | Re-place + re-route | MCP move + `routing_cli.py` re-route net |
| Thin power trace | Widen trace via net class change | `routing_cli.py --net-class power` |
| Unrouted net island | Manual seed point | `routing_cli.py --seed <x,y>` |
| Silk-on-pad | Offset silk | KiCad API silk edit |

## Loop Limits
- Max 3 iterations per checkpoint
- ~12K tokens per critique cycle (3K critique + 4K rework + 2K tool exec + 3K re-render + 1K buffer)
- Convergence rule: monotonic issue↓ AND monotonic confidence↑

## Escalation Protocol
When escalating:
1. Dump current board state to journal
2. Re-render via `scripts/render_board.py` for fresh PNG
3. Call AskUserQuestion with:
   - Render paths (full + copper)
   - Last 3 iterations' critique summaries
   - The unresolved issue list
   - 3 options: provide hint / abort checkpoint / abort audition

## Anti-Patterns to Avoid
- Local optimum trap: reworking MINOR while CRITICAL unchanged → triage CRITICAL first
- Thrashing: same net modified 3+ times → escalate
- Token explosion: cycle >15K tokens → reduce critique scope to top-3 issues
```
- **Test**: `pytest tests/test_iterative_refinement_skill.py -v`

#### Task 2.1.3: Author self-critique-skill.md
- **Files**: Create `agent_docs/skills/self-critique-skill.md` (~200 LOC md)
- **Pattern**: 6 meta-skill sections per research — (1) Critique posture ("adversarial but honest"), (2) Five anti-patterns + mitigations, (3) Decision tree (when to invoke which skill), (4) Convergence metrics, (5) Guard rails, (6) Per-checkpoint exit criteria with explicit confidence thresholds
```markdown
# Self-Critique Skill (meta-skill)

## Posture
You are NOT cheerleading your own work. You are an adversarial reviewer asking
"what would a domain expert catch in this?" Confidence is earned, not assumed.

## Five Anti-Patterns
| Anti-pattern | Detection signal | Mitigation |
|---|---|---|
| Rubber-stamping | Zero issues for 2+ consecutive iter | Force adversarial mode iter 2; escalate if persists |
| Thrashing | Same net modified 3+ times with oscillating values | "Do not undo" memory; escalate on oscillation |
| Over-correction | New CRITICAL ≥1 after rework | Dry-run rework; validate routing impact pre-commit |
| Early escalation | Escalates iter 1 with all-MINOR issues | Require 2+ iter; only escalate if confidence <0.5 |
| Local optimum trap | MINOR reworked while CRITICAL unchanged | Triage: CRITICAL → MAJOR → MINOR; skip MINOR if CRITICAL remain |

## Decision Tree (when to invoke which skill)
- Just finished a checkpoint? → visual-review-skill
- Got JSON critique? → iterative-refinement-skill (proceed/rework/escalate)
- About to escalate? → self-critique-skill (am I rubber-stamping or thrashing? am I early-escalating?)
- At a milestone (4/5/7)? → AskUserQuestion

## Convergence Tracking
Per checkpoint, track:
- iteration_depth (1..3)
- issue_count_trajectory (descending = good)
- confidence_trajectory (ascending = good)
- modifications_applied (counts per net)
- new_issues_introduced (over-correction signal)

## Per-Checkpoint Exit Criteria
| Checkpoint | Required confidence | Required pass_criteria |
|---|---|---|
| board_outline | ≥0.85 | outline closed, dimensions match contract |
| mechanical_placement | ≥0.85 | all non-electrical components placed, ≥3mm edge clearance |
| ic_placement | ≥0.90 | ICs on F.Cu, centered, oriented per pin-1 convention |
| critical_passive_placement | ≥0.90 | decaps within 5mm of IC power pins |
| remaining_passive_placement | ≥0.85 | all components placed, no overlap |
| power_routing | ≥0.90 | VCC + GND traces ≥0.5mm width |
| signal_routing | ≥0.85 | all nets routed, no unconnected |
| ground_zone_and_stitching | ≥0.90 | GND zones on B.Cu, stitching vias on 5mm grid |
```
- **Test**: `pytest tests/test_self_critique_skill.py -v`

#### Task 2.1.4: Author test_visual_review_skill.py
- **Files**: Create `tests/test_visual_review_skill.py`
- **Pattern**: Structural test — parses skill markdown, finds required sections, validates documented JSON schema
```python
from pathlib import Path
SKILL = Path("agent_docs/skills/visual-review-skill.md")

def test_skill_file_exists():
    assert SKILL.exists()

def test_required_sections():
    text = SKILL.read_text()
    for section in ["Input Contract", "Per-Checkpoint Rubric", "Failure Mode Catalog",
                     "Output Format", "Anti-Pattern Guard Rails"]:
        assert f"## {section}" in text, f"Missing section: {section}"

def test_failure_mode_catalog_has_10_entries():
    text = SKILL.read_text()
    # Look for table rows with severity/checkpoint/fix-hint structure
    rows = [line for line in text.split("\n") if line.startswith("| ") and " | " in line]
    catalog_rows = [r for r in rows if any(cp in r for cp in ["PLACEMENT", "SIGNAL_ROUTING",
                                                                "POWER_ROUTING", "GROUND_PLANE", "DRC"])]
    assert len(catalog_rows) >= 10

def test_json_schema_documented():
    text = SKILL.read_text()
    for field in ["checkpoint", "iteration", "pass_fail", "confidence",
                   "issues", "recommendation"]:
        assert field in text
```

#### Task 2.1.5: Author test_iterative_refinement_skill.py
- **Files**: Create `tests/test_iterative_refinement_skill.py`
- **Pattern**: Same structural style; validates decision-tree + escalation-protocol sections exist
```python
SKILL = Path("agent_docs/skills/iterative-refinement-skill.md")

def test_required_sections():
    text = SKILL.read_text()
    for section in ["Decision Tree", "Rework Scope Targeting", "Loop Limits",
                     "Escalation Protocol", "Anti-Patterns"]:
        assert f"## {section}" in text

def test_loop_ceiling_documented():
    text = SKILL.read_text()
    assert "3 iterations" in text or "max 3" in text.lower()
    assert "12K" in text or "12,000" in text  # token budget

def test_escalation_triggers_documented():
    text = SKILL.read_text()
    assert "AskUserQuestion" in text
    assert "confidence" in text and "0.5" in text
```

#### Task 2.1.6: Author test_self_critique_skill.py
- **Files**: Create `tests/test_self_critique_skill.py`
- **Pattern**: Validates 5 anti-patterns named + exit-criteria table present
```python
SKILL = Path("agent_docs/skills/self-critique-skill.md")

def test_five_anti_patterns():
    text = SKILL.read_text()
    for ap in ["Rubber-stamping", "Thrashing", "Over-correction",
                "Early escalation", "Local optimum trap"]:
        assert ap in text or ap.replace("-", " ") in text

def test_per_checkpoint_exit_criteria():
    text = SKILL.read_text()
    for cp in ["board_outline", "mechanical_placement", "ic_placement",
                "critical_passive_placement", "remaining_passive_placement",
                "power_routing", "signal_routing", "ground_zone_and_stitching"]:
        assert cp in text

def test_convergence_metrics():
    text = SKILL.read_text()
    assert "confidence" in text and "trajectory" in text
```

#### Validation Checkpoint — Batch 2.1
```bash
pytest tests/test_visual_review_skill.py tests/test_iterative_refinement_skill.py tests/test_self_critique_skill.py -v
# Expected: all 3 files green; section/JSON/anti-pattern checks pass

# Manual readability test: open each skill file; an agent reading it can identify
# what it's for and how to invoke it in under 30 seconds.
```

### Batch 2.2: pcb-design-skill rewrite + journal protocol + inline reviewer gates + agent-skills.context.md
**Objective**: Replace v1's monolithic 12-step workflow with the 8-checkpoint iterative architecture; embed journal protocol, inline reviewer gates, AskUserQuestion milestone harness; produce the 6th `.context.md` file.

#### Task 2.2.1: Rewrite pcb-design-skill.md
- **Files**: REWRITE `agent_docs/skills/pcb-design-skill.md` (target ~320 LOC md)
- **Pattern**: Section structure — (1) Skill purpose + when to invoke, (2) The 8 checkpoints (named, ordered, with entry/exit criteria), (3) Per-checkpoint loop (render → critique → proceed/rework), (4) Reflexion journal protocol, (5) Inline reviewer gates at checkpoints 4 + 6, (6) AskUserQuestion milestones at 4/5/7 boundaries, (7) DRC enforcement per checkpoint, (8) Required reading (rules + other skills)
```markdown
# PCB Design Skill (v2 — 8-checkpoint iterative)

## When to Invoke
You are designing a PCB from a contract. The contract has supplier metadata.
You will execute 8 checkpoints, rendering and critiquing after each. Self-Refine
loop bounded at 3 iterations per checkpoint.

## Required Reading (in order)
1. The contract you were given (e.g. `contracts/blinker_555_contract.md`)
2. `agent_docs/rules/supplier-drc-rules.md` (mandatory before routing)
3. `agent_docs/skills/visual-review-skill.md`
4. `agent_docs/skills/iterative-refinement-skill.md`
5. `agent_docs/skills/self-critique-skill.md`
6. `agent_docs/skills/placement-skill.md` (survives from v1)
7. `agent_docs/skills/routing-skill.md` (survives from v1; MCP-routing BANNED)

## The 8 Checkpoints
| # | Checkpoint | Entry criterion | Exit criterion | Gates |
|---|---|---|---|---|
| 1 | board_outline | contract loaded, supplier DRU emitted | closed outline at contract dims | render→critique |
| 2 | mechanical_placement | outline done | mounting holes + connectors placed, ≥3mm edge clearance | render→critique |
| 3 | ic_placement | mechanical done | all ICs on F.Cu, oriented per pin-1 | render→critique |
| 4 | critical_passive_placement | IC placement done | decaps within 5mm of IC power pins | render→critique → **inline reviewer** → **milestone 1 (AUQ)** |
| 5 | remaining_passive_placement | critical passives placed | all components placed, no overlap | render→critique → **milestone 2 (AUQ)** |
| 6 | power_routing | placement complete | VCC + GND traces ≥0.5mm, fully routed | render→critique → **inline reviewer** |
| 7 | signal_routing | power routed | all signal nets routed, no unconnected | render→critique → **milestone 3 (AUQ)** |
| 8 | ground_zone_and_stitching | signals routed | GND zone on B.Cu, stitching vias on 5mm grid | render→critique → final DRC |

## Per-Checkpoint Loop (Self-Refine)
After every checkpoint's actions:
1. Call `scripts/render_board.py <pcb>` → get `{full, copper, svg}` paths
2. Apply `visual-review-skill.md` → get structured JSON critique
3. Apply `self-critique-skill.md` → anti-pattern check on the critique itself
4. Apply `iterative-refinement-skill.md` → decision: proceed / rework / escalate
5. If rework AND iter < 3: re-enter step 1 with rework scope
6. If escalate: AskUserQuestion with state dump
7. If proceed: append journal entry, advance to next checkpoint

## Reflexion Journal Protocol
After EVERY checkpoint (including reworks), append to `output/<board>_journal.md`:
\`\`\`markdown
## Checkpoint N: <name>
**Started**: <timestamp>
**Iterations**: <count>
### Decisions
- <bullet list>
### Issues found
- Iter 1: <issue + outcome>
- Iter 2: <issue + outcome>
### Lessons for downstream checkpoints
- "<lesson summary>"
**Confidence**: <final>
**Outcome**: proceed | escalated | aborted
\`\`\`

At the START of each new checkpoint, re-read journal lessons-so-far. If a prior
checkpoint surfaced "decoupling caps need 0805 footprint not 0603 due to MCU pad spacing"
you should apply that lesson without being told again.

## Inline Reviewer Gates (Checkpoints 4 + 6)
After visual-review-skill verdict at checkpoints 4 and 6:
- Invoke `design-reviewer` subagent on the rendered PNG
- Output → `review/<board>_inline_<N>.md`
- If reviewer returns CRITICAL findings: re-enter rework loop (same iteration counter,
  do not advance milestone)
- If reviewer returns clean: continue to milestone (4) or proceed (6)

## AskUserQuestion Milestones (3 boundaries)
At checkpoints 4, 5, and 7 boundary, fire AskUserQuestion with:
- render_path_full + render_path_copper
- checkpoint_just_completed
- critique_summary (≤3 sentences from visual-review)
- iterations_used
- 3 options: proceed / rework_specific / abort

Owner's choice determines next action:
- proceed → advance to next checkpoint
- rework_specific → owner specifies issue; re-enter rework loop
- abort → terminate audition cleanly, record verdict

## DRC Enforcement (Per Checkpoint)
After every checkpoint that adds copper (3 onward), run DRC against the emitted
`<board>.kicad_dru`. ZERO violations or you don't advance.

## Anti-Scaffolding
- This skill is operational, NOT theoretical. The 8 checkpoints map 1:1 to
  agent actions on a real `.kicad_pcb` file. No "TBD" or stub checkpoints.
```

#### Task 2.2.2: Document journal protocol (embedded in pcb-design-skill.md)
Already embedded above in Task 2.2.1. Iterative-refinement-skill.md (Batch 2.1) cross-references the same protocol.

#### Task 2.2.3: Document inline reviewer gates (embedded in pcb-design-skill.md)
Already embedded above in Task 2.2.1.

#### Task 2.2.4: Document AskUserQuestion milestone protocol (embedded in pcb-design-skill.md + iterative-refinement-skill.md)
Embedded in 2.2.1; iterative-refinement-skill.md from Batch 2.1 cross-references with the escalation protocol.

#### Task 2.2.5: Author agent-skills.context.md
- **Files**: Create `docs/context/agent-skills.context.md` (6th and final .context.md)
- **Pattern**: Orientation doc — lists 4 v1 survivors (placement, kicad-api, routing, pcb-design-rewritten) + 3 new (visual-review, iterative-refinement, self-critique); routing relationships (which skill cross-references which); load order during a build (contract → supplier-drc rule → pcb-design → visual-review per checkpoint → iterative-refinement → self-critique on demand → AUQ at milestones); when each is invoked

#### Validation Checkpoint — Batch 2.2
```bash
# Walk pcb-design-skill.md top to bottom, confirm an agent reading it can identify:
#   (a) the 8 checkpoints (names + order)
#   (b) the 3 milestone insertion points (after 4, after 5, after 7)
#   (c) the 2 inline-review insertion points (4, 6)
#   (d) the journal append protocol with structure
#   (e) the loop-ceiling rules (max 3 iter, ~12K tokens, conf thresholds)

# All 3 structural tests from Batch 2.1 still green:
pytest tests/test_visual_review_skill.py tests/test_iterative_refinement_skill.py tests/test_self_critique_skill.py -v
# Expected: all green

# Manual: open agent-skills.context.md, confirm orientation for all 7 skills (4 survive + 3 new)
ls docs/context/
# Expected: 6 files now (render-pipeline, supplier-drc, contracts, baselines, routing-primitives, agent-skills)
```

### Batch 2.3: CLAUDE.md routing update + /review-board repurpose
**Objective**: Wire the new skills into the agent's routing table; clarify `/review-board` as final-pass only.

#### Task 2.3.1: Update CLAUDE.md
- **Files**: Modify `CLAUDE.md`
- **Pattern**: Add 4 new routing rows (visual-review, iterative-refinement, self-critique, supplier-drc); add visual-loop gate + supplier-DRC gate to "Before ANY Coding" section
```markdown
## Task Routing (UPDATED)

| If you are...                       | Read this file                                    |
|-------------------------------------|---------------------------------------------------|
| Designing a PCB                     | `agent_docs/skills/pcb-design-skill.md`           |
| Placing components                  | `agent_docs/skills/placement-skill.md`            |
| Checking clearances                 | `agent_docs/rules/clearance-rules.md`             |
| Working with KiCad API              | `agent_docs/skills/kicad-api-skill.md`            |
| Routing traces                      | `agent_docs/skills/routing-skill.md`              |
| Reviewing a rendered checkpoint     | `agent_docs/skills/visual-review-skill.md`        | ← NEW
| Deciding proceed/rework/escalate    | `agent_docs/skills/iterative-refinement-skill.md` | ← NEW
| Self-checking critique posture      | `agent_docs/skills/self-critique-skill.md`        | ← NEW
| Loading supplier DRC profile        | `agent_docs/rules/supplier-drc-rules.md`          | ← NEW
| Running DRC                         | `agent_docs/rules/drc-rules.md`                   |
...

## Before ANY Coding (UPDATED)
1. Read `agent_docs/rules/coding-rules.md` first.
2. **Visual-loop gate (v2).** If task is a PCB build, use the 8-checkpoint iterative
   loop. After every checkpoint, call `scripts/render_board.py` and consult
   `visual-review-skill.md`. NO monolithic builds.
3. **Supplier-DRC gate (v2).** If contract has `supplier:` metadata, call
   `load_supplier_profile()` and `emit_kicad_dru()` BEFORE any routing. See
   `agent_docs/rules/supplier-drc-rules.md`.
```

#### Task 2.3.2: Update .claude/commands/review-board.md
- **Files**: Modify `.claude/commands/review-board.md`
- **Pattern**: Clarify final-pass-only role; preserve 3 subagents; add precondition refusing if `output/<board>.kicad_pcb` or `output/<board>_full.png` missing
```markdown
# /review-board <board_name>

## Role (v2)
Optional final adversarial pass AFTER a full audition completes. The Stage 2
inline reviewer gates (checkpoints 4 + 6) catch issues during build. Use
/review-board only for an additional adversarial sweep on the completed board.

## Preconditions (hard refuse if missing)
- `output/<board_name>.kicad_pcb` must exist
- `output/<board_name>_full.png` must exist (render the board first)
If either is missing: refuse with: "Run `scripts/render_board.py output/<board_name>.kicad_pcb` first."

## Flow (unchanged from v1)
1. design-reviewer reads board + render → `review/<board>_review.md`
2. design-defender reads review → `review/<board>_defense.md`
3. design-referee reads both → `review/<board>_verdict.md`
```

#### Validation Checkpoint — Batch 2.3
```bash
# Verify routing table contains all new entries
grep -E "(visual-review|iterative-refinement|self-critique|supplier-drc)" CLAUDE.md
# Expected: 4 routing rows referenced

# Verify gates added
grep -A 3 "Visual-loop gate\|Supplier-DRC gate" CLAUDE.md
# Expected: both gates present in "Before ANY Coding" section

# Verify /review-board precondition
grep "Preconditions" .claude/commands/review-board.md
# Expected: precondition section present

# Full test suite still green
pytest -v
# Expected: all green, no regressions
```

### Batch 2.4: Integration verification (end-to-end dry run)
**Objective**: Prove the wired-up skill system fires correctly without committing to a real audition; surfaces wiring bugs before Stage 3 burns owner time.

#### Task 2.4.1: Author stub contract
- **Files**: Create `contracts/_dryrun_stub.md` (synthetic minimal contract for dry-run only; `_` prefix flags it as non-production)
- **Pattern**: 5-component, 3-net dummy with `supplier: jlcpcb` metadata; "DESIGN FROM THIS CONTRACT ONLY" clause; minimal but parseable

#### Task 2.4.2: Execute dry run
- **Pattern**: Open fresh session; invoke pcb-design-skill against the stub contract; walk through all 8 checkpoints WITHOUT actually committing real component placements (or with permissive DRC turned off); confirm:
  - (a) `output/_dryrun_stub_journal.md` populated with all 8 checkpoint sections
  - (b) `design-reviewer` subagent invoked at checkpoints 4 + 6 → 2 inline review files
  - (c) AskUserQuestion fires at boundary of checkpoint 4 / 5 / 7
  - (d) Skill load order matches CLAUDE.md routing
  - (e) `output/_dryrun_stub.kicad_dru` emitted BEFORE any routing checkpoint

#### Task 2.4.3: Author dryrun log
- **Files**: Create `docs/auditions/_stage2_dryrun_log.md` (informal artifact)
- **Pattern**: List each of (a)–(e) above with PASS/FAIL; record any anomalies; suggested fixes

#### Validation Checkpoint — Batch 2.4
```bash
# Manual: developer confirms (a)–(e) above pass; records anomalies in dryrun log
# If all pass: Stage 2 ready for Stage 3
# If any fail: file as bugs, fix, re-run dry run, re-record

ls output/_dryrun_stub_journal.md output/_dryrun_stub.kicad_dru
# Expected: both files exist after dry run

ls review/_dryrun_stub_inline_4.md review/_dryrun_stub_inline_6.md
# Expected: both inline-reviewer outputs exist
```

## Constraints
- **Performance**: Token budget per critique cycle ~12K (3K critique + 4K rework + 2K tool exec + 3K re-render + 1K buffer); aggregate ~350K for 8 checkpoints with 1 escalation per 2 checkpoints. Well within Opus 4.7's 1M context.
- **Performance**: Loop ceiling = 3 iterations per checkpoint. Any more triggers escalate. Justified by Self-Refine literature: iter 4+ historically thrashes.
- **Security**: Inline reviewer subagent invocation does not write to `tests/` or modify contract files. Read-only on those paths.
- **Convention**: All new skill files follow the v1 skill pattern — header, purpose/when-to-invoke, sections, examples. Existing skills' style is the reference.
- **Convention**: AskUserQuestion calls always provide exactly 3 options (proceed / rework_specific / abort) for consistency across milestones.
- **Convention**: Journal entries follow the markdown structure above verbatim. No free-form journaling.
- **Convention**: `design-reviewer` subagent definitions in `.claude/agents/` are UNCHANGED in Stage 2; only the *invocation pattern* (inline at 4+6 vs only via /review-board) shifts.

## Extension Points
- **Stage 3 audition** executes pcb-design-skill against `contracts/blinker_555_contract.md`; all hooks (journal, inline reviewer, AUQ milestones, DRU gate) fire during the audition.
- **v2.x cross-session Reflexion**: promote `output/<board>_journal.md` to a persistent store (e.g. SQLite). Skills already write the structure; consumer becomes cross-session vs in-memory.
- **v2.x structured /review-board verdict**: the 3-subagent pipeline currently emits 3 markdown files. v2.x can structure them as JSON for programmatic verdict consumption.
- **v2.x additional skills**: if audition exposes a missing skill (e.g. "thermal-management-skill.md"), drop it into `agent_docs/skills/` and add a CLAUDE.md routing row. No other files need touching.
- **v2.x cost-premium warnings during build**: visual-review-skill can be extended with a `cost_warnings[]` field in the JSON output; loader already returns cost_premiums map.

## Dependencies
- **Requires**: Stage 1 complete — `scripts/render_board.py` produces PNGs (consumed by visual-review-skill); `scripts/supplier_drc/loader.py` emits DRU (consumed by pcb-design-skill before routing); `contracts/blinker_555_contract.md` exists (for Batch 2.4 dry run can use the stub or the 555 contract); `api_manifest.json` refreshed; `baselines/4.6/` in place
- **Requires (surviving v1 assets)**: `.claude/agents/design-{reviewer,defender,referee}.md` (unchanged; inline reviewer gates reference design-reviewer); `scripts/routing_cli.py` (unchanged); `agent_docs/skills/{routing,placement,kicad-api}-skill.md` (unchanged); `agent_docs/rules/{coding,clearance,drc,testing,test-failing}-rules.md` (unchanged)
- **Produces**: Operational iterative build loop encoded in skills + CLAUDE.md routing + inline reviewer wiring + AskUserQuestion milestone protocol + journal protocol; ready for Stage 3 audition execution
- **External**: None new beyond Stage 1's deps

## Scope Boundaries
- **In scope**: 3 new skill files (visual-review, iterative-refinement, self-critique) + 3 structural tests (symmetric coverage); pcb-design-skill rewrite (8-checkpoint iterative); CLAUDE.md routing update + 2 new "Before ANY Coding" gates; Reflexion journal protocol *within-session* (markdown append-only); inline reviewer gates at checkpoints 4 + 6 (via design-reviewer subagent); AskUserQuestion milestone protocol at 3 boundaries (after 4 / 5 / 7); `/review-board` repurposed as final adversarial pass with hard preconditions; agent-skills.context.md (6th .context.md file); Batch 2.4 stub-contract dry-run with anomaly log
- **Deferred to v2.x**:
  - Reflexion memory persistence *across sessions* (currently within-session markdown only)
  - `/review-board` structured-verdict JSON output upgrade (currently 3 markdown files)
  - Cost-premium warnings injected into visual-review critique
  - Component-only render variant consumed by a 3rd rubric view (PLACEMENT-only judgment)
  - Automated integration tests for the milestone harness (currently manual via dry run)
  - Persistent escalation log file or webhook (currently AskUserQuestion in-conversation only)
- **Trigger for promotion**:
  - If audition surfaces "lessons from run 1 should inform run 2" — promote cross-session Reflexion to v2.0 mid-flight
  - If `/review-board` verdicts need programmatic consumption (e.g. CI gate) — upgrade to JSON
  - If owner ever runs the loop unattended — promote AUQ milestones to file-based pause + webhook
- **Out of scope entirely**: Render primitive (Stage 1); supplier DRC primitives (Stage 1); audition execution (Stage 3); audition outcome doc (Stage 3); Blue Pill v2 retry (Stage 3 stretch); changes to v1's 3-subagent reviewer pipeline definitions
