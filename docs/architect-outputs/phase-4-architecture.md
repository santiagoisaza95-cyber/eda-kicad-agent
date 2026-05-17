# Phase 4: Staged Architecture — AGREED
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions
1. **3 stages** as proposed: Stage 1 Foundation, Stage 2 Iterative Build Architecture, Stage 3 Audition.
2. **Directory tree** approved (see 4e below). Demotion path for 4.6 artifacts confirmed.
3. **Dependency graph** approved: Stage 1 → Stage 2 → Stage 3 strict, with skill-content parallelism allowed in Stage 2.
4. **6 `.context.md` files** placed: render-pipeline, supplier-drc, agent-skills, contracts, routing-primitives, baselines. Stage 1 produces 5; Stage 2 produces agent-skills.
5. **TELEMETRY: EXEMPT** — agent system uses journal + visual renders + AskUserQuestion as observability surfaces (not WebSocket+JSONL).
6. **Token budget** confirmed comfortable for 1M context (Opus 4.7).

## Raw Outputs

### 4a. Token Budget

Assumed context window: 1M (Opus 4.7). Skill rule: fixed + variable ≤ 40% of context (so ≥60% remains for code).

| Document | Est. tokens | Type |
|---|---|---|
| CLAUDE.md (v2 updated) | ~2,500 | Fixed |
| Domain context (`docs/context/domain.md` if created) | ~3,000 | Fixed |
| `.context.md` files (6 modules × ~1,000) | ~6,000 | Fixed |
| Active stage doc (200K version) | ~3,000 | Variable |
| Active contract (e.g. `blinker_555_contract.md`) | ~2,000 | Variable |
| Active rule + skill set (top 3-4 relevant files × ~800) | ~3,000 | Variable |
| Task prompt | ~1,000 | Variable |
| **Total** | **~20,500** | |
| **% of 1M** | **~2%** | Way under 40% cap |
| **% of 200K (if Sonnet)** | **~10%** | Under 40% cap |

**Verdict:** Well within budget. Even under 200K-context Sonnet, fixed+variable = 10% leaves 90% for code. The 1M Opus 4.7 budget is comfortable. No need to compress docs.

### 4b. Observability Architecture

**`TELEMETRY: EXEMPT`** — this project does NOT have a backend+frontend split. It's an agent system with three observability surfaces already built in:

1. **In-session journal** — `output/<board>_journal.md` updated at every checkpoint (Reflexion-style, Phase 2 decision)
2. **Visual telemetry** — PNG renders per checkpoint serve as the visual log
3. **Human-pause channel** — `AskUserQuestion` at the 3 milestones surfaces state to the owner

These together provide the debugging visibility the skill's "TELEMETRY: YES" pattern would deliver via WebSocket+JSONL. The agent-system pattern doesn't need WebSocket because there's no separate frontend to broadcast to — the owner IS the observer at milestones.

Documented in Decision Timeline (Phase 6e).

### 4c. Staged Structure

3 stages, each independently testable:

| Stage | Purpose | Deliverables (high level) | Independent test |
|---|---|---|---|
| **Stage 1: Foundation** | Build the v2 substrate: visual render pipeline + supplier-anchored DRC + audition contract + 4.6 baseline preservation | `render_board.py`, `supplier_profiles/`, `supplier_drc/loader.py`, `supplier-drc-rules.md`, `blinker_555_contract.md`, `tests/test_blinker_555.py`, `baselines/4.6/`, refreshed `api_manifest.json`, updated `requirements.txt` + `verify_toolchain.py` | `pytest tests/test_render_board.py tests/test_supplier_drc.py -v`. Bonus: `render_board.py output/blue_pill.kicad_pcb` should produce a PNG of the v1 board (proves render works against real input). |
| **Stage 2: Iterative Build Architecture** | Encode the 8-checkpoint iterative build loop into agent skills + CLAUDE.md routing + Reflexion journal + inline reviewer gates + milestone protocol | 3 new skills, updated `pcb-design-skill.md`, updated `CLAUDE.md`, journal protocol, inline reviewer gate integration, AskUserQuestion milestone harness | `pytest tests/test_visual_review_skill.py -v` + dry-run the build flow on a stub contract; verify all skills load, all gates invoke correctly, AskUserQuestion fires at the right 3 points. |
| **Stage 3: Audition** | Execute the v2 pipeline on the 555 LED blinker; owner judges. Stretch: retry Blue Pill, compare to 4.6 baseline | `output/blinker_555.kicad_pcb`, `docs/auditions/blinker_555_run1.md` with verdict, screenshots, journal excerpt. Stretch: `output/blue_pill_v2.kicad_pcb` + comparison artifact. | Owner reads the audition doc + opens the PNG; declares "credible 555" pass/fail. Hard pass: 3 milestones approved, final design judged credible. |

### 4d. Architecture Agent (dispatched separately)

A `Plan` agent will produce the dual-resolution stage docs (200K version primarily; 1M version deferred). See dispatched agent in the conversation log.

### 4e. Directory Tree (v2 target)

```
eda-kicad-agent/
├── CLAUDE.md                              ← UPDATED v2 routing (+ visual-loop gate, + supplier-DRC gate, + 3 new skills)
├── README.md                              ← updated overview + v2 quickstart
├── requirements.txt                       ← + cairosvg>=2.7.0, lxml>=5.0.0
├── config.json                            ← unchanged
├── api_manifest.json                      ← refreshed at Stage 1 start
├── architecture_v2_proposal.md            ← NEW (Phase 6 deliverable, owner reads first)
│
├── .claude/
│   ├── agents/                            ← unchanged (4 review subagents survive)
│   └── commands/                          ← /review-board UPDATED (final-pass mode)
│
├── agent_docs/
│   ├── rules/
│   │   ├── coding-rules.md                ← unchanged
│   │   ├── clearance-rules.md             ← unchanged
│   │   ├── drc-rules.md                   ← unchanged
│   │   ├── testing-rules.md               ← unchanged
│   │   ├── test-failing-rules.md          ← unchanged
│   │   └── supplier-drc-rules.md          ← NEW (Stage 1)
│   └── skills/
│       ├── pcb-design-skill.md            ← REWRITTEN (Stage 2): 8-checkpoint iterative
│       ├── placement-skill.md             ← unchanged
│       ├── kicad-api-skill.md             ← unchanged
│       ├── routing-skill.md               ← unchanged
│       ├── visual-review-skill.md         ← NEW (Stage 2)
│       ├── iterative-refinement-skill.md  ← NEW (Stage 2)
│       └── self-critique-skill.md         ← NEW (Stage 2)
│
├── contracts/
│   ├── EXAMPLE_CONTRACT.md                ← unchanged
│   ├── blue_pill_contract.md              ← unchanged (Stage 3 stretch target)
│   └── blinker_555_contract.md            ← NEW (Stage 1)
│
├── supplier_profiles/                     ← NEW DIRECTORY (Stage 1)
│   ├── README.md                          ← schema + extensibility docs
│   ├── schema.py                          ← Pydantic models
│   └── jlcpcb.yaml                        ← JLCPCB populated profile
│
├── scripts/
│   ├── render_board.py                    ← NEW (Stage 1)
│   ├── supplier_drc/                      ← NEW PACKAGE (Stage 1)
│   │   ├── __init__.py
│   │   ├── loader.py                      ← load_supplier_profile, emit_kicad_dru
│   │   └── validators.py                  ← stub for v2.x external checks
│   ├── routing_cli.py                     ← unchanged (still THE primitive)
│   ├── routing/                           ← unchanged
│   │   ├── __init__.py
│   │   ├── actions.py
│   │   ├── perception.py
│   │   └── pathfinder.py
│   ├── discover_api.py                    ← unchanged
│   ├── scaffold.py                        ← unchanged
│   ├── verify_toolchain.py                ← UPDATED (also check cairosvg + GTK3 runtime)
│   ├── verify_mcp.py                      ← unchanged
│   ├── setup_mcp.py                       ← unchanged
│   ├── strip_silk.py                      ← unchanged
│   └── generate_docs_pdf.py               ← unchanged
│
├── tests/
│   ├── conftest.py                        ← may add fixtures (render_board, supplier_profile)
│   ├── test_blue_pill.py                  ← unchanged (Stage 3 stretch gate)
│   ├── test_blinker_555.py                ← NEW (Stage 1)
│   ├── test_render_board.py               ← NEW (Stage 1)
│   ├── test_supplier_drc.py               ← NEW (Stage 1)
│   ├── test_visual_review_skill.py        ← NEW (Stage 2) — schema/structure test
│   ├── test_pathfinder.py                 ← unchanged
│   ├── test_perception.py                 ← unchanged
│   ├── test_route_actions.py              ← unchanged
│   ├── test_routing_cli.py                ← unchanged
│   ├── test_workbench_integration.py      ← unchanged
│   └── test_example_board.py              ← unchanged
│
├── output/                                ← runtime artifacts (gitignored mostly)
│   └── <board>_journal.md                 ← Reflexion journal per build session
│
├── baselines/                             ← NEW (Stage 1)
│   └── 4.6/
│       ├── README.md                      ← what these are, when produced
│       ├── build_blue_pill.py             ← demoted from scripts/
│       ├── route_blue_pill.py             ← demoted from scripts/
│       ├── blue_pill.kicad_pcb            ← demoted from output/
│       ├── blue_pill.kicad_pro            ← demoted
│       └── blue_pill.kicad_prl            ← demoted
│
├── research/                              ← Phase 2 outputs (preserved as references)
│   ├── supplier_drc_research.md
│   ├── rendering_toolchain_research.md
│   └── self_critique_patterns_research.md
│
├── review/                                ← runtime (review pipeline outputs)
│
├── tools/KiCAD-MCP-Server/                ← unchanged
│
├── docs/
│   ├── architect-outputs/                 ← Phase 0–6 checkpoints (this folder)
│   ├── stages/                            ← Stage docs (200K + 1M variants)
│   │   ├── stage-1-foundation-200k.md
│   │   ├── stage-2-iterative-build-200k.md
│   │   └── stage-3-audition-200k.md
│   ├── context/                           ← 6 .context.md files
│   │   ├── render-pipeline.context.md
│   │   ├── supplier-drc.context.md
│   │   ├── agent-skills.context.md
│   │   ├── contracts.context.md
│   │   ├── routing-primitives.context.md
│   │   └── baselines.context.md
│   ├── decisions/                         ← Decision timeline, tech mapping
│   │   ├── decision-timeline.md
│   │   └── tech-mapping-report.md
│   └── auditions/                         ← Stage 3 audition outcomes
│       └── blinker_555_run1.md            ← Stage 3 deliverable
│
└── Prompt/
    └── BOOTSTRAP_PROMPT.md                ← unchanged (historical)
```

### Dependency Graph

```
Stage 1: Foundation
    │
    ├─► render_board.py        ───┐
    ├─► supplier_drc/loader.py ───┤
    ├─► supplier-drc-rules.md  ───┤
    ├─► blinker_555_contract   ───┤── Stage 2 needs these to encode skill workflows
    ├─► baselines/4.6/         ───┘
    └─► refreshed api_manifest.json
                ↓
Stage 2: Iterative Build Architecture
    │
    ├─► visual-review-skill.md          ───┐
    ├─► iterative-refinement-skill.md   ───┤
    ├─► self-critique-skill.md          ───┤── Stage 3 needs ALL of these to execute
    ├─► pcb-design-skill.md (rewritten) ───┤
    ├─► CLAUDE.md updated               ───┤
    ├─► journal protocol                ───┤
    ├─► inline reviewer gates           ───┤
    └─► AskUserQuestion milestone harness──┘
                ↓
Stage 3: Audition
    │
    ├─► blinker_555 end-to-end build
    ├─► owner judges 3 milestones + final
    ├─► docs/auditions/blinker_555_run1.md
    └─► STRETCH: blue_pill_v2 + comparison
```

**Inter-stage independence rules:**
- Stage 2 work CANNOT begin on a checkpoint that consumes render output until Stage 1 `render_board.py` is verified working.
- Stage 2 work on skill *content* CAN proceed in parallel with Stage 1 (text doesn't need executable infra), but skill *integration tests* require Stage 1 done.
- Stage 3 requires both Stages 1 and 2 fully complete + tests passing.

### 4f. .context.md Placement (6 modules)

| File | Boundary it documents | Updated after batch... |
|---|---|---|
| `docs/context/render-pipeline.context.md` | `scripts/render_board.py` + dependencies + render output schema | Stage 1 render batch |
| `docs/context/supplier-drc.context.md` | `supplier_profiles/` + `scripts/supplier_drc/` + `.kicad_dru` emission semantics | Stage 1 supplier DRC batch |
| `docs/context/agent-skills.context.md` | `agent_docs/skills/` orientation (4 surviving + 3 new) | Stage 2 skill-authoring batch |
| `docs/context/contracts.context.md` | `contracts/` template + per-board metadata expectations | Stage 1 contract batch |
| `docs/context/routing-primitives.context.md` | `scripts/routing_cli.py` + `scripts/routing/` — what survives unchanged from v1 | Stage 1 (read-only doc, no batch produces it) |
| `docs/context/baselines.context.md` | `baselines/4.6/` — what each file is, when it was produced, what to compare against | Stage 1 demotion batch |

## User Feedback
- Owner approved as recommended.
- Owner added reminder: "remember the context window is 1M". Confirmed — token budget analysis showed total overhead at ~2% of 1M (~10% of 200K). Comfortable; no compression action needed.

## Cross-Phase Consistency Check
✓ Token budget comfortably within limits at both 1M and 200K context. No compression needed.
✓ 3-stage structure (Stage 1 = Foundation, Stage 2 = Iterative Build, Stage 3 = Audition) matches Phase 0 size classification.
✓ Stage 1 deliverables = Phase 3 Essential v2.0 / Foundation items. 1:1 match.
✓ Stage 2 deliverables = Phase 3 Essential v2.0 / Iterative Build items. 1:1 match.
✓ Stage 3 deliverables = Phase 3 Essential v2.0 / Audition items + stretch. 1:1 match.
✓ Directory tree preserves all surviving v1 assets (routing_cli, routing/, review subagents, contracts, agent_docs structure).
✓ Demoted v1 assets (build_blue_pill.py, route_blue_pill.py, blue_pill outputs) tracked in `baselines/4.6/`.
✓ TELEMETRY: EXEMPT classified with reason; documented in Decision Timeline.
✓ Render mechanism (kicad-cli + cairosvg + lxml from Phase 2) maps to `scripts/render_board.py` in Stage 1.
✓ Supplier schema (Pydantic, YAML, extensible from Phase 1+2) maps to `supplier_profiles/schema.py` + `jlcpcb.yaml` + `loader.py` in Stage 1.
✓ Critique loop (Self-Refine + Reflexion from Phase 2) maps to 3 new skill files + journal protocol in Stage 2.
✓ 8 checkpoints + 3 human milestones (Phase 3) map to skill content in Stage 2 + AskUserQuestion integration.
✓ /review-board final-pass repurpose (Phase 3) maps to `.claude/commands/` update in Stage 2.
✓ No contradictions found.

## Revision History
- **2026-05-16, post-Plan-agent review:** Plan agent flagged 8 inconsistencies while drafting stage docs. Two acted on:
  - **#4 routing-primitives.context.md had no batch owner.** Fix: added to Stage 1 Batch 1.4 (with baselines + api_manifest refresh). Stage 1 deliverable #14 updated to include 5 .context.md files; Stage 2 Batch 2.2 produces the 6th (agent-skills).
  - **#8 only 1 skill had a structural test.** Fix: Stage 2 Batch 2.1 now produces 3 structural tests (`test_visual_review_skill.py`, `test_iterative_refinement_skill.py`, `test_self_critique_skill.py`) — one per new skill, symmetric coverage.
- Other 6 inconsistencies (Plan agent's #1, #2, #3, #5, #6, #7) were either reconcilable as Phase 4 supersedes Phase 2/3 wording (#2, #3) or were correct inferences by the Plan agent matching Phase 3 intent (#1, #5, #6, #7). No action required; documented here for traceability.
