# eda-kicad-agent v2 — Architecture Proposal

**Status:** READY FOR OWNER REVIEW (no implementation has begun)
**Date:** 2026-05-16
**Author:** Claude Opus 4.7, via the project-architect skill
**Owner:** Santiago Isaza

This document is the single end-to-end handover for the v2 redesign of `eda-kicad-agent`. It is the deliverable from the audit-and-redesign task. **No implementation will start until you sign off below.**

If you only have 5 minutes, read **[The TL;DR](#the-tldr)** and **[Decision Timeline](#decision-timeline)**, then jump to **[Sign-Off](#sign-off)**.

---

## Table of Contents

1. [The TL;DR](#the-tldr)
2. [Why v1 Failed (and Why "DRC Clean" Was Misleading)](#why-v1-failed)
3. [The v2 Hypothesis](#the-v2-hypothesis)
4. [Eight Architectural Changes (P1–P8)](#eight-architectural-changes)
5. [Three-Stage Build Plan](#three-stage-build-plan)
6. [The Audition Protocol](#the-audition-protocol)
7. [Supplier-Anchored DRC (P8)](#supplier-anchored-drc-p8)
8. [Visual Feedback Loop (P1)](#visual-feedback-loop-p1)
9. [Critique Loop Design (P2, P4, P6)](#critique-loop-design)
10. [What Survives Unchanged from v1](#what-survives-unchanged-from-v1)
11. [What Gets Demoted to `baselines/4.6/`](#what-gets-demoted)
12. [Decision Timeline](#decision-timeline)
13. [Open Risks](#open-risks)
14. [Sign-Off](#sign-off)
15. [Reference Documents](#reference-documents)

---

## The TL;DR

**The original goal of `eda-kicad-agent` was to prove Claude could autonomously produce credible PCB designs from a contract alone.** Round 2 under Opus 4.6 produced a STM32 Blue Pill design that was DRC-clean and passed 54/54 tests — but you judged it as not having achieved the goal. You diagnosed the bottleneck as 4.6's visual reasoning.

**v2 fixes this with Opus 4.7 + six architectural changes:**

1. **Visual feedback loop** — agent renders the PCB after every checkpoint and reasons over the image (4.6's blind spot)
2. **Iterative checkpoint architecture** — 8 discrete phases with render → critique → rework loops, not one monolithic build
3. **Hardcoded board scripts demoted** — `build_blue_pill.py` and `route_blue_pill.py` move to `baselines/4.6/`; nothing in `scripts/` is board-specific anymore
4. **Review pipeline becomes inline gates** — `design-reviewer` subagent fires at checkpoints 4 + 6, not just at the end via `/review-board`
5. **Meta-skills** — three new skill files teach the agent *how* to self-critique, refine iteratively, and avoid 5 named anti-patterns
6. **Smaller audition board first** — 555 LED blinker proves v2 works before retrying Blue Pill

Plus one new constraint you added during architecture review:

7. **Supplier-anchored DRC** — JLCPCB profile becomes the mandatory DRC source-of-truth, replacing v1's hand-picked rules. Schema is extensible so PCBWay, OSH Park, etc. plug in later.

**Audition flow:** 8 checkpoints, agent self-critiques after each (max 3 iter per checkpoint), owner judges at 3 milestones (after critical-passives, after all-placement, after signal-routing), final verdict on whether the 555 blinker is "credible." If yes → stretch test on Blue Pill, compare to the 4.6 baseline.

**Effort estimate:** ~3 stages of implementation work + 1 audition session with owner present at 3 milestone touchpoints. Stage 1 + 2 can run as CTO-orchestrated batches; Stage 3 is a single live session with you.

---

## Why v1 Failed

### The artifacts looked right

- `output/blue_pill.kicad_pcb` — 28 components, 18 nets, 128 traces, 43 vias, GND zone
- `output/drc_report.json` — `"violations": []`, `"unconnected_items": []` (2026-03-06)
- `pytest -v` — 54/54 passing (per commit `4787d57 — "feat: Blue Pill STM32 board — 54/54 tests passing"`)
- `git log --oneline` — a clean Round 2 fix series

### But the goal was different from what got measured

The contract had a checklist (board outline, component placement, DRC clean, all nets routed, etc.) — all green. But your subjective bar was "would a domain expert find this credible as a Blue Pill?" That bar is not captured by any of: tests, DRC, contract checklist.

The v1 architecture had no mechanism to assess "credible." It had:
- A monolithic build (`build_blue_pill.py` runs once top-to-bottom)
- A monolithic route (`route_blue_pill.py` lays down all 128 traces in one pass)
- A perception layer that returns JSON (`scripts/routing/perception.py`)
- A review pipeline (`/review-board` with reviewer → defender → referee) **that was never run on blue_pill**
- Tests that check numbers, not aesthetics

The architecture forced 4.6 to reason about a 2D spatial layout *purely from numbers in JSON*. No rendered image. No iterative "look at it, fix the bad parts" loop. The model could not engage its visual reasoning at all.

### The smoking gun

`drc_err.json` in the output folder has 146 errors logged from 2026-03-06 13:01 — two minutes BEFORE `drc_report.json` shows 0/0 (13:03). So the workflow was: build → fail DRC → fix → re-run DRC → clean. The "clean" state is real, but it was achieved by iterating on the *numerical* DRC, never on the *visual* design. A board can be DRC-clean and still look wrong.

### "DRC clean ≠ JLCPCB clean" (the supplier insight)

v1's contract specifies 0.2 mm clearance and 0.7 mm vias. Neither matches JLCPCB (5 mil / 0.127 mm clearance, 0.6 mm via pad / 0.3 mm drill). The numbers are reasonable but they're hand-picked — not anchored to any real supplier. Even if v1 had produced a credible-looking board, sending it to a fab would have either rejected on annular ring (v1 doesn't check it) or charged premiums for over-conservative via diameter.

This is the bottom of why P8 (supplier-anchored DRC) is in v2: the agent should be designing to *manufacturable* rules, not arbitrary ones.

---

## The v2 Hypothesis

> **If we add a visual feedback loop + iterative checkpoint architecture + supplier-anchored DRC + Opus 4.7's improved visual reasoning, the agent will produce a board that you (the domain expert) judge as credible.**

This is a falsifiable hypothesis. v2's purpose is to test it.

The **555 LED blinker audition** is the first test. If it passes (you judge the 555 as credible), we retry Blue Pill under v2 architecture and compare visually to the 4.6 baseline. If THAT also passes credible, the original Blue Pill goal is achieved.

If the 555 fails credible, we have a clear signal that the architecture changes weren't sufficient — and the journal + per-checkpoint renders give us evidence to debug *what specifically* the agent got wrong. v1 had no such evidence.

---

## Eight Architectural Changes

| # | Change | What it fixes |
|---|---|---|
| **P1** | Visual feedback loop: render PCB to PNG after every checkpoint; feed image to agent | 4.6's visual reasoning was unused because the agent only saw JSON. P1 unblocks 4.7's improved vision capability. |
| **P2** | 8-checkpoint iterative architecture (vs monolithic build) | Lets the agent course-correct between phases instead of one-shotting a 28-component layout. Self-Refine pattern (Madaan 2023). |
| **P3** | Demote hardcoded board scripts to `baselines/4.6/` | `build_blue_pill.py` and `route_blue_pill.py` ARE frozen 4.6 output. Re-running them just replays 4.6's choices. v2 has NO board-specific scripts — only generic primitives. |
| **P4** | Inline reviewer gates at checkpoints 4 + 6 (during build, not just at end) | v1's reviewer/defender/referee pipeline was only available via `/review-board` after a full build. v2 fires `design-reviewer` mid-build so issues are caught when cheap to fix. |
| **P5** | Three new meta-skills: `visual-review-skill.md`, `iterative-refinement-skill.md`, `self-critique-skill.md` | v1 had `placement-skill.md` (what good placement looks like) but no skill teaching the agent *how to look at its own output and improve it*. P5 fills this gap. |
| **P6** | 555 LED blinker audition FIRST, Blue Pill stretch SECOND | Avoid re-running v1's failure case as the first test of v2. 555 = ~30 min iteration. Blue Pill = hours. Get signal fast. |
| **P7** | Reference image in contracts — **DEFERRED** | Original v1 constraint was "DESIGN FROM THIS CONTRACT ONLY." You kept this; no visual reference in v2.0 contracts. Preserves the autonomy purity of the test. |
| **P8** | Supplier-anchored DRC (JLCPCB profile, extensible schema for PCBWay/OSH Park/Eurocircuits) | v1 used hand-picked rules. v2 reads `supplier_profiles/jlcpcb.yaml`, emits `.kicad_dru`, blocks routing until DRU loaded. "DRC clean" now means "fab-clean." |

---

## Three-Stage Build Plan

### Stage 1: Foundation (Essential v2.0)

**Purpose:** Build the v2 substrate — render primitive, supplier DRC, audition contract, baselines.

**Deliverables (14):**
- `scripts/render_board.py` — kicad-cli SVG → cairosvg PNG, dark background, <2 s per render, returns `{full, copper, svg}` paths
- `supplier_profiles/{schema.py, jlcpcb.yaml, README.md}` — Pydantic v2 models + populated JLCPCB profile
- `scripts/supplier_drc/{__init__.py, loader.py, validators.py}` — `load_supplier_profile()` + `emit_kicad_dru()` + stub for v2.x external checks
- `agent_docs/rules/supplier-drc-rules.md` — new mandatory rule
- `contracts/blinker_555_contract.md` — 555 LED blinker audition contract, supplier metadata, "DESIGN FROM THIS CONTRACT ONLY" clause
- `tests/{test_blinker_555.py, test_render_board.py, test_supplier_drc.py}` — three new test files
- `baselines/4.6/{README.md, build_blue_pill.py, route_blue_pill.py, blue_pill.{kicad_pcb,kicad_pro,kicad_prl}}` — demoted v1 artifacts with provenance README
- `api_manifest.json` refreshed (re-run `discover_api.py` against KiCad 9.0.7)
- `scripts/verify_toolchain.py` extended (check cairosvg + lxml + GTK3 runtime)
- `requirements.txt` updated (+ `cairosvg>=2.7.0`, `lxml>=5.0.0`)
- 5 `.context.md` files in `docs/context/`: render-pipeline, supplier-drc, contracts, baselines, routing-primitives

**Independent validation:** `pytest tests/test_render_board.py tests/test_supplier_drc.py -v` green; `python scripts/render_board.py output/blue_pill.kicad_pcb` produces a PNG in <2 s (proves the render works on real input).

**4 batches (mostly parallelizable).** Full operational detail in `docs/stages/stage-1-foundation-200k.md`.

### Stage 2: Iterative Build Architecture (Essential v2.0)

**Purpose:** Encode the 8-checkpoint iterative build loop into agent skills + CLAUDE.md routing.

**Deliverables (11):**
- `agent_docs/skills/visual-review-skill.md` — per-checkpoint visual rubric (PLACEMENT, POWER_ROUTING, SIGNAL_ROUTING, GROUND_PLANE, DRC) + 10-entry failure-mode catalog + structured JSON output schema
- `agent_docs/skills/iterative-refinement-skill.md` — decision tree (proceed/rework/escalate) + rework scope targeting + max-3-iter loop ceiling + ~12K-token-per-cycle budget + escalation protocol
- `agent_docs/skills/self-critique-skill.md` (meta-skill) — 5 named anti-patterns + convergence-tracking metrics + per-checkpoint exit criteria with confidence thresholds
- `agent_docs/skills/pcb-design-skill.md` REWRITTEN — replaces v1's 12-step monolithic workflow with the 8-checkpoint iterative architecture; references new skills + supplier-drc-rules.md
- `CLAUDE.md` updated — 4 new routing rows, visual-loop gate + supplier-DRC gate added to "Before ANY Coding"
- Reflexion journal protocol — `output/<board>_journal.md`, append-only within-session, structure documented in pcb-design-skill.md
- Inline reviewer gates — `design-reviewer` subagent invoked at checkpoints 4 + 6, writes to `review/<board>_inline_<N>.md`, CRITICAL findings re-enter rework loop
- `AskUserQuestion` milestone harness — 3 milestones (after critical_passive_placement, after remaining_passive_placement, after signal_routing), each pauses with render path + critique summary + 3 options (proceed / rework specific / abort)
- `.claude/commands/review-board.md` updated — final-pass mode only (post-audition); preserves 3 review subagents
- `tests/{test_visual_review_skill.py, test_iterative_refinement_skill.py, test_self_critique_skill.py}` — structural tests for each new skill (parse markdown, validate sections + JSON schema)
- `docs/context/agent-skills.context.md` — orientation for 4 surviving + 3 new skills

**Independent validation:** Dry-run on a stub contract; all 8 checkpoints execute, journal populated, inline reviewer fires at 4 + 6, AskUserQuestion fires at 3 milestones, supplier DRU emitted before routing.

**4 batches.** Full operational detail in `docs/stages/stage-2-iterative-build-200k.md`.

### Stage 3: Audition (Essential v2.0 + stretch)

**Purpose:** Execute v2 pipeline on 555 LED blinker, owner judges. Stretch: retry Blue Pill, compare to baseline.

**Deliverables (10):**
- `output/blinker_555.kicad_pcb` — built end-to-end through v2
- Per-checkpoint renders (×8 × 2 views) — `output/checkpoints/blinker_555_<N>_<name>_*.png`
- `output/blinker_555_journal.md` — Reflexion journal populated incrementally
- `review/blinker_555_inline_{4,6}.md` — inline reviewer outputs
- 3 AskUserQuestion exchanges captured (with your proceed/rework/abort decisions)
- `docs/auditions/blinker_555_run1.md` — final audition outcome doc (you read this + the final PNG to declare credible pass/fail)
- `pytest tests/test_blinker_555.py -v` green
- Optionally: `/review-board blinker_555` adversarial pass → 3 review files
- **STRETCH:** `output/blue_pill_v2.kicad_pcb` + 4.6 comparison doc (gated on 555 pass)

**Validation:** Owner's "credible 555" verdict (hard gate); owner's "v2 unblocks Blue Pill goal" verdict (ultimate v2 verdict).

**3 batches with hard gate** between 3.2 and 3.3. Full detail in `docs/stages/stage-3-audition-200k.md`.

---

## The Audition Protocol

The 555 LED blinker audition is the moment of truth. Here's what happens, in order:

1. **Pre-flight (you run):** `python scripts/verify_mcp.py && python scripts/verify_toolchain.py && pytest -v` — confirm Stage 1 + 2 are clean. Commit any uncommitted work.
2. **Invoke the agent** — fresh Opus 4.7 session, point it at `contracts/blinker_555_contract.md`. Per `agent_docs/rules/supplier-drc-rules.md`, the agent loads `supplier_profiles/jlcpcb.yaml` and emits `output/blinker_555.kicad_dru` as its first act.
3. **Checkpoint 1: `board_outline`** — agent draws Edge_Cuts polygon, renders, self-critiques, proceeds if pass.
4. **Checkpoint 2: `mechanical_placement`** — power header, mounting hole (if any) at edges.
5. **Checkpoint 3: `ic_placement`** — NE555 center.
6. **Checkpoint 4: `critical_passive_placement`** — timing cap + resistors near 555 pins. **Inline reviewer fires.** Then **milestone 1: you eyeball coord-frame sanity.** You decide: proceed / rework specific issue / abort.
7. **Checkpoint 5: `remaining_passive_placement`** — LED + current-limit resistor + bypass cap. **Milestone 2: you eyeball full placement before routing locks it in.**
8. **Checkpoint 6: `power_routing`** — VCC + GND at 0.5+ mm. **Inline reviewer fires.**
9. **Checkpoint 7: `signal_routing`** — TRIG, THR, DISCH, OUT. **Milestone 3: you eyeball final routing before zones.**
10. **Checkpoint 8: `ground_zone_and_stitching`** — B.Cu GND zone, F.Cu fill, stitching vias.
11. **Final DRC** against the JLCPCB DRU — must be 0/0.
12. **`pytest tests/test_blinker_555.py -v`** — must be green.
13. **Final renders + audition doc:** agent writes `docs/auditions/blinker_555_run1.md`.
14. **You read it + open `output/blinker_555_full.png`.** Declare: credible 555 or not.

Total agent work: ~30 min if no major reworks. You're present at steps 6, 7, 9 (the 3 milestones). Each pause is ~5 min of your time = ~15 min total.

**If credible passes:** stretch test on Blue Pill. Fresh session, same flow, `contracts/blue_pill_contract.md`. Then render the 4.6 baseline through `scripts/render_board.py` and produce `docs/auditions/blue_pill_v2_vs_4.6_comparison.md` side-by-side. That comparison is the ultimate verdict on whether v2 unblocked the original goal.

---

## Supplier-Anchored DRC (P8)

The supplier-DRC subsystem is the biggest single addition to v2. Three parts:

### 1. Schema (extensible)

`supplier_profiles/schema.py` defines Pydantic v2 models:

```python
class SupplierProfile(BaseModel):
    metadata: SupplierMetadata
    design_rules: DesignRules

class DesignRules(BaseModel):
    trace_rules: TraceRules
    via_rules: ViaRules
    pad_rules: PadRules
    solder_mask_rules: SolderMaskRules
    silkscreen_rules: SilkscreenRules
    board_rules: BoardRules
    cost_premiums: dict[str, CostPremium]
```

Each rule has explicit units (`mm`/`mil`), optional `recommended` value, and a `comment` field for context like "JLCPCB charges +++ below 0.3mm trace."

### 2. JLCPCB profile (populated)

`supplier_profiles/jlcpcb.yaml` captures (selected values; full table in `research/supplier_drc_research.md`):

| Axis | JLCPCB value |
|---|---|
| Min trace width | 0.127 mm (5 mil) |
| Min trace-to-trace clearance | 0.127 mm (5 mil) |
| Copper-to-edge | 0.3 mm |
| Min via pad diameter | 0.6 mm |
| Min via drill | 0.3 mm |
| Min annular ring | 0.15 mm (recommended 0.2) |
| Min silk line width | 0.15 mm |
| Min silk text height | 1.0 mm |
| Solder mask clearance | 0.05 mm/side |
| Board thickness std | 1.6 mm |
| Copper weight | 1 oz |
| Surface finish | HASL (lead-free) |

### 3. KiCad DRU emission

`scripts/supplier_drc/loader.py` provides `emit_kicad_dru(profile, out_path)` that writes `.kicad_dru` text using native KiCad rule syntax:

```lisp
(version 1)
(rule "Min Trace Width" (constraint track_width (min 0.127mm)))
(rule "Min Clearance" (constraint clearance (min 0.127mm)) (condition "A.Type == 'track' && B.Type == 'track'"))
(rule "Min Edge Clearance" (constraint edge_clearance (min 0.3mm)))
(rule "Min Annular Ring (JLCPCB)" (constraint annular_width (min 0.15mm)) (condition "A.Type == 'via'"))
(rule "Min Silkscreen Line Width" (constraint silk_line_width (min 0.15mm)))
(rule "Min Silkscreen Text Height" (constraint silk_text_height (min 1.0mm)))
;; ...
```

**Known DRU gaps** (documented in `agent_docs/rules/supplier-drc-rules.md`):
- Solder mask clearance is a global UI-only setting in KiCad, not a DRU constraint. Handle via `BOARD_DESIGN_SETTINGS` write.
- Non-plated hole minimum is not enforceable in DRU. Defer to a v2.x external Python validator.
- Board thickness and copper weight are documentation only, not DRC-checkable.

### 4. Risk callouts for the agent

The supplier-drc research highlights 5 axes most-often-violated by automated designers:

1. **Annular ring** (HIGH) — KiCad's default via auto-sizing can undershoot 0.15 mm ring. Custom DRU + post-route check.
2. **Silk-on-pad** (MEDIUM) — auto-placed designators overlap pads. Custom DRU clearance rule.
3. **Trace-to-via** (MEDIUM) — generic clearance ≠ via-specific.
4. **Copper-to-edge after outline regen** (MEDIUM) — outline changes invalidate earlier checks.
5. **Solder mask web < 0.1 mm** (LOW) — dense pads create slivers.

The agent loads these as awareness during the build, not just at final DRC.

---

## Visual Feedback Loop (P1)

`scripts/render_board.py` is the new keystone primitive. Function signature:

```python
def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True
) -> dict[str, Path]:
    """Returns {'full': PNG path, 'copper': PNG path | None, 'svg': SVG path}"""
```

**Pipeline:**
1. Subprocess `kicad-cli pcb export svg --mode-single --layers Edge_Cuts,B.Cu,F.Cu,F.Mask,F.SilkS --output board_render.svg <pcb>`
2. Parse SVG with `lxml.etree`, inject `<rect width=100% height=100% fill=#1a1a1a>` at z-order 0 (dark BG for vision-model contrast)
3. `cairosvg.svg2png(bytestring=..., scale=dpi/96, write_to=...)`
4. (If `generate_variants`) Repeat for copper-only (F.Cu + B.Cu) — second PNG

**Speed budget (measured per research):** ~300–400 ms kicad-cli + ~50–100 ms lxml + ~600–900 ms cairosvg = ~1.0–1.4 s for full render; ~2.0 s for full + copper. **Under the <2 s target.**

**Layer composition** (selected for signal-to-noise):
- `Edge_Cuts` — board outline, critical for shape judgment
- `B.Cu` — back copper (default blue) — bottom of z-order
- `F.Cu` — front copper (default red)
- `F.Mask` — front solder mask (pad visibility)
- `F.SilkS` — front silkscreen (text/refs) on top

KiCad's default palette already differentiates these — no custom theme needed.

**Why not PLOT_CONTROLLER (pcbnew Python alternative)?** Considered. Requires kipython, plots layer-by-layer (need post-composite), no speed win on Windows. Defer to v2.x if mid-render color injection becomes a need.

**Dependencies to add:** `cairosvg>=2.7.0`, `lxml>=5.0.0` (pip), `gtk3-runtime-bin-x64` (Chocolatey, system).

---

## Critique Loop Design

Per-checkpoint loop pattern: **Self-Refine** (Madaan et al. 2023).

```
START checkpoint N
    │
    ├─► Execute checkpoint actions (place/route/zone/etc.)
    │
    ├─► render_board() → full + copper PNGs
    │
    ├─► visual-review-skill.md: structured JSON critique
    │     { pass_fail, confidence, issues[], recommendation }
    │
    ├─► self-critique-skill.md: posture check, anti-pattern detection
    │
    ├─► iterative-refinement-skill.md: proceed / rework / escalate?
    │     │
    │     ├─► PROCEED → checkpoint N+1
    │     ├─► REWORK (iter <3, confidence >0.7) → re-enter execute step
    │     └─► ESCALATE → AskUserQuestion to owner OR halt with state dump
    │
    └─► Append to output/<board>_journal.md (Reflexion memory)

(At checkpoints 4 + 6: inline `design-reviewer` subagent fires first; its findings join the critique)
(At checkpoints 4, 5, 7 boundaries: AskUserQuestion to owner — milestone pause)
```

### Loop ceiling (with justification)

| Parameter | Value | Source |
|---|---|---|
| Max iterations per checkpoint | 3 | Iter 1 catches 70-80%; iter 2 cascading; iter 3 plateau; iter 4+ thrashing (Self-Refine literature) |
| Token budget per cycle | ~12K | 3K critique + 4K rework + 2K tool exec + 3K re-render + 1K buffer |
| Confidence threshold (proceed) | ≥0.85 | Below this, rework |
| Confidence threshold (escalate) | <0.5 after iter 2 | Agent doesn't know what's wrong; human needed |
| Convergence rule | Monotonic issue↓ AND confidence↑ | Any reversal = thrashing → escalate |

### 5 anti-patterns + detection

| Anti-pattern | Detection signal | Mitigation |
|---|---|---|
| Rubber-stamping | Zero issues for 2+ consecutive iter | Force adversarial mode iter 2; escalate if persists |
| Thrashing | Same net modified 3+ times with oscillating values | "Do not undo" memory; escalate on oscillation |
| Over-correction | New CRITICAL ≥1 after rework | Dry-run; validate routing impact pre-commit |
| Early escalation | Escalates iter 1 with all-MINOR issues | Require 2+ iter; only escalate if confidence <0.5 |
| Local optimum trap | MINOR reworked while CRITICAL unchanged | Triage: CRITICAL → MAJOR → MINOR; skip MINOR if CRITICAL remain |

### Reflexion memory

Within-session episodic memory in `output/<board>_journal.md`. Per checkpoint:

```markdown
## Checkpoint N: <name>
### Decisions
- ...
### Issues found
- Iter 1: ...
- Iter 2: ... (resolved)
### Lessons for downstream checkpoints
- "When placing decoupling caps near U1, prefer <strategy> because <reason from iter 1 failure>"
```

Agent re-reads journal at start of each new checkpoint to retrieve lessons. Cross-session memory persistence deferred to v2.x.

---

## What Survives Unchanged from v1

The redesign explicitly **preserves** the parts of v1 that work. Re-using these is half the value of "redesign" vs "rewrite":

| Asset | Why preserved |
|---|---|
| `scripts/routing_cli.py` | A* iterative router with JSON I/O — exactly the primitive v2 needs. The 45° angle validator is a hard constraint that stays. |
| `scripts/routing/` (actions.py, perception.py, pathfinder.py) | Supports routing_cli; perception module is what visual-review-skill builds on |
| `tools/KiCAD-MCP-Server/` (60+ MCP tools) | All tools EXCEPT routing (`route_trace`, `route_pad_to_pad`, `route_differential_pair`) survive. Routing tools stay banned. |
| `.claude/agents/design-{reviewer,defender,referee}.md` | The 3 review subagents fire inline in v2 (P4); no change to their definitions |
| `.claude/agents/api-researcher.md` | `/research-api` still routes here when uncertain about pcbnew API |
| `agent_docs/rules/{coding,clearance,drc,testing,test-failing}-rules.md` | All 5 hard rules survive verbatim |
| `agent_docs/skills/{placement,kicad-api,routing}-skill.md` | Skills survive; pcb-design-skill is the only one that gets rewritten |
| `contracts/EXAMPLE_CONTRACT.md`, `contracts/blue_pill_contract.md` | Templates + the Blue Pill spec (used by Stage 3 stretch test) |
| `api_manifest.json` | Refreshed once at Stage 1 start; structure unchanged |
| `scripts/{discover_api, scaffold, verify_mcp, setup_mcp, strip_silk, generate_docs_pdf}.py` | All unchanged |
| `tests/{test_pathfinder, test_perception, test_route_actions, test_routing_cli, test_workbench_integration, test_example_board}.py` | All unchanged; new tests are additive |
| `tests/test_blue_pill.py` | Unchanged; becomes the Stage 3 stretch-test finish-line check |
| `config.json` | Unchanged (KiCad path, footprint library path) |
| `CLAUDE.md` | Updated additively (4 new routing rows, 2 new gates); structure stays |
| `.claude/commands/{new-board, research-api}.md` | Unchanged; `/review-board` gets its scope clarified |

---

## What Gets Demoted

Three files leave `scripts/` and `output/` to live in `baselines/4.6/` with a README explaining provenance:

| File | What it was | Why demoted |
|---|---|---|
| `scripts/build_blue_pill.py` | 4.6's hardcoded builder for blue_pill (~370 LOC) | It's frozen agent output, not generic infra. v2 has NO board-specific scripts. |
| `scripts/route_blue_pill.py` | 4.6's hardcoded router for blue_pill (~390 LOC, explicit waypoints) | Same. routing_cli.py is the generic primitive; route_blue_pill is a snapshot. |
| `output/blue_pill.kicad_pcb` + `.kicad_pro` + `.kicad_prl` | The DRC-clean Round 2 artifacts | Kept as the baseline-to-beat for Stage 3 stretch comparison. |

`baselines/4.6/README.md` documents: produced 2026-03-06 under Opus 4.6, "54/54 tests passing" but owner-judged goal-failed, used for Stage 3 v2-vs-4.6 visual comparison.

---

## Decision Timeline

| Decision | Value | Phase | What would change this |
|---|---|---|---|
| Model | Opus 4.7 (1M context) | Phase 0 | Owner switches to a different model line; current 4.7 is the v2 target |
| Project size | Medium (3 stages) | Phase 0 | Major scope addition (e.g. full GUI redesign) would push to Large |
| Render mechanism | `kicad-cli SVG` + `cairosvg PNG` + `lxml` dark BG | Phase 1 | Speed budget violation (>2 s) or quality issues; PLOT_CONTROLLER is the v2.x fallback |
| Visual judge | Hybrid — agent self-critique every checkpoint + owner at 3 milestones | Phase 1 | Owner unavailable for milestones → pure self-critique with longer escalation |
| Supplier scope | JLCPCB primary, schema-first | Phase 1 | Owner ships boards to other fab; that supplier's profile becomes mandatory next |
| Reference image in contract | NO (pure contract-only) | Phase 1 | Owner decides realism > purity; reference-image variant of contracts is the v2.x extension |
| Render dependencies | `cairosvg>=2.7.0`, `lxml>=5.0.0`, GTK3 runtime | Phase 2 | Chocolatey unavailable on owner's machine → document manual GTK install or switch to Wand |
| Supplier schema format | YAML + Pydantic v2 | Phase 2 | If Pydantic v2 incompatibility surfaces → fall back to JSON Schema |
| Critique pattern | Self-Refine + Reflexion + CoVe hybrid | Phase 2 | If 3-iter ceiling proves too tight → bump to 4 in v2.x |
| Loop ceiling | 3 iter/checkpoint, ~12K tokens/cycle | Phase 2 | Audition shows thrashing at 2 iter → tighten to 2 |
| Audition board | 555 LED blinker (5–7 components, ~6 nets) | Phase 3 | Audition reveals 555 is too trivial → switch to RP2040 minimal breakout in v2.1 |
| Checkpoint count | 8 (board_outline → ground_zone) | Phase 3 | Audition reveals one checkpoint is too dense → split it |
| Milestone count | 3 (post-critical-passive, post-all-placement, post-signal-routing) | Phase 3 | Audition reveals owner needs more touchpoints → add one |
| Milestone UX | `AskUserQuestion` native call | Phase 3 | Harness UX issues → switch to file-based pause |
| `/review-board` fate | Repurposed as optional final adversarial pass | Phase 3 | Owner never invokes it → drop in v2.1 |
| Reflexion memory | Within-session only | Phase 3 (default) | Cross-session lessons would help → promote to v2.x persistent store |
| DRC enforcement | Block at each checkpoint | Phase 3 (default) | False-positive cascade → defer to end-of-stage only |
| v1 `test_blue_pill.py` | Kept unchanged | Phase 3 (default) | Becomes obsolete after Stage 3 stretch test |
| Audition success criteria | Owner subjective + contract checklist | Phase 3 (default) | If subjective verdict is too noisy → add quantitative criteria (component density, trace length, etc.) |
| 3-stage structure | Stage 1 Foundation, Stage 2 Iterative Build, Stage 3 Audition | Phase 4 | Scope creep would split Stage 2 into 2a/2b |
| TELEMETRY classification | EXEMPT (agent system, no backend+frontend split) | Phase 4 | If a web UI is added → reclassify to YES |
| Anti-scaffolding watch | Listed 6 specific traps | Phase 5 | If any trap triggers in implementation → rule added in v2.x |
| Full HIL stage contracts | Deferred to cto-executor invocation time | Phase 5 | Owner invokes `/cto-executor` for v2 → draft contracts then |

---

## Open Risks

Honest risks I'd flag before you sign off:

1. **GTK3 install on owner's machine.** cairosvg needs the GTK3 runtime. Chocolatey is the easy path (`choco install gtk3-runtime-bin-x64`) but if Chocolatey isn't on the owner's machine, manual GTK binary install is finicky on Windows. Stage 1 verify_toolchain.py should fail loudly with a clear remediation message.

2. **The 555 might be too easy.** A 5-component design has minimal placement complexity. If 4.7 nails it, that's not proof v2 will handle Blue Pill (28 components, 18 nets). Risk: false positive on 555 → still fail on Blue Pill. Mitigation: the Stage 3 stretch comparison against the 4.6 baseline gives us the real signal.

3. **JLCPCB annular ring is documentation-ambiguous.** Multiple sources cite 0.15 mm; community KiCad rule sets use 0.2–0.25 mm. We set the schema's `recommended` to 0.2 mm. Audition output might still cause a JLCPCB DFM rejection if their internal rule is stricter than published. Low probability — but a fab order test would be the only definitive proof.

4. **Reflexion within-session might not be enough.** If the audition fails and we want to retry, cross-session memory would help the second run avoid the first run's mistakes. v2.0 doesn't have it. If audition needs >1 attempt, we may need to promote cross-session memory to v2.0 mid-flight.

5. **`AskUserQuestion` at 3 milestones depends on owner availability.** If owner is unavailable mid-build, the agent halts and the session may drop without completion. No graceful recovery built in v2.0; the dry-run in Stage 2 Batch 2.4 will surface this if it's a real issue.

6. **Token budget per audition is generous but not unlimited.** Per Phase 2 estimate: ~350K tokens for a full 8-checkpoint audition with 1 escalation per 2 checkpoints. Opus 4.7's 1M context is fine; Sonnet 4.6's 200K would be tight. Audition is Opus-only by design.

7. **The auditor verdict gap that exists in v1 (review pipeline never ran) still exists in v2.0** for the audition board. Inline reviewer gates fire at checkpoints 4 + 6, but the FULL 3-agent reviewer/defender/referee pipeline is optional (post-audition `/review-board`). If you want stricter quality, v2.0 could promote `/review-board` to mandatory at audition end. Not in current scope — flag for decision.

---

## Sign-Off

If you approve this proposal as written, I'll prepare to hand off to `/cto-executor` for Stage 1 implementation (when you're ready to start building).

**Specific sign-off needed:**

- [ ] Diagnosis of why v1/4.6 failed is accurate
- [ ] 8 architectural changes (P1–P8) are the right ones
- [ ] 3-stage structure (Foundation → Iterative Build → Audition) is the right scope
- [ ] 555 LED blinker as audition board is acceptable
- [ ] 8 checkpoints + 3 milestones is the right granularity
- [ ] JLCPCB as primary supplier with schema-first extensibility is correct
- [ ] No reference image in contracts is correct (autonomy-purity preserved)
- [ ] Risks listed are acceptable; mitigations are reasonable

**Or push back on any of:**
- A diagnosis point (something I got wrong about why v1 failed)
- A P pillar (one of P1–P8 is wrong or missing)
- The audition board (555 isn't the right test case)
- The supplier choice (JLCPCB isn't where you'd actually ship)
- The risk register (something important not flagged)

---

## Reference Documents

This proposal is the summary. Each section has a deeper backing artifact:

| Artifact | Purpose |
|---|---|
| `docs/architect-outputs/phase-0-classification.md` | Project size + initial state |
| `docs/architect-outputs/phase-1-critical-path.md` | Four critical-path Q&As verbatim |
| `docs/architect-outputs/phase-2-tech-mapping.md` | Technology Mapping Report with capability scores |
| `docs/architect-outputs/phase-3-scope.md` | Scope tiers (Essential / Valuable / Future) + low-impact defaults |
| `docs/architect-outputs/phase-4-architecture.md` | Token budget + directory tree + dependency graph + .context.md placement |
| `docs/architect-outputs/phase-5-execution.md` | Batch summary + rule set + orchestration sketch |
| `docs/stages/stage-1-foundation-200k.md` | Stage 1 batches with explicit checkpoints |
| `docs/stages/stage-2-iterative-build-200k.md` | Stage 2 batches with explicit checkpoints |
| `docs/stages/stage-3-audition-200k.md` | Stage 3 audition execution + outcome doc |
| `research/supplier_drc_research.md` | JLCPCB rules table + YAML schema + KiCad DRU mapping + supplier comparator + risk callouts |
| `research/rendering_toolchain_research.md` | kicad-cli + cairosvg pipeline + speed budget + alternative paths |
| `research/self_critique_patterns_research.md` | Self-Refine + Reflexion + CoVe research + skill scaffolding + anti-patterns |
| `baselines/4.6/README.md` (to be authored in Stage 1 Batch 1.4) | What 4.6 produced, when, owner's verdict |

---

*End of proposal. Awaiting owner sign-off.*
