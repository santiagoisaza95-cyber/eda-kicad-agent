# Phase 3: Scope Refinement — AGREED
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions

1. **Audition board:** 555 timer LED blinker — 5–7 components, ~6 nets. Recognizable, fast iteration (~30 min per full cycle). Becomes `contracts/blinker_555_contract.md` + `tests/test_blinker_555.py`. Owner judges "credible" at end.
2. **Build loop = 8 checkpoints + 3 human milestones** (approved as proposed):
   - Checkpoints: `board_outline` → `mechanical_placement` → `ic_placement` → `critical_passive_placement` → `remaining_passive_placement` → `power_routing` → `signal_routing` → `ground_zone_and_stitching`
   - Human milestones at: after `critical_passive_placement` (coord-frame sanity), after `remaining_passive_placement` (full placement review), after `signal_routing` (final review before audition verdict)
   - After each checkpoint: render → self-critique → proceed/rework loop (max 3 iter)
3. **Milestone pause UX:** `AskUserQuestion` tool call. Agent presents render path + critique summary + 3 options (proceed / rework specific issue / abort) at each milestone. Blocks cleanly with no polling logic.
4. **`/review-board` fate:** Repurposed as **optional final adversarial pass**. Inline reviewer gates catch issues during build; `/review-board` becomes the on-demand red-team after a full audition completes. The 3 review subagents (reviewer, defender, referee) survive into v2 unchanged; only the slash command's role shifts.

## Raw Outputs

### Numbered ambiguities resolved

| # | Ambiguity | Resolution | Architectural impact |
|---|---|---|---|
| 1 | Audition board | 555 LED blinker | Drives Stage 1 contract content + Stage 3 success criteria |
| 2 | Checkpoint list | 8 phases as proposed | Drives Stage 2 skill content + contract template + routing CLI usage pattern |
| 3 | Milestone count + placement | 3 milestones at the 3 boundaries shown | Drives AskUserQuestion integration points in the build flow |
| 4 | Milestone pause UX | AskUserQuestion native call | Removes need for file-based polling or session-restart workflow |
| 5 | /review-board fate | Repurpose as final pass | Preserves the 3 review subagents; clarifies slash-command UX |

### Remaining low-impact ambiguities (defaults applied, not user-blocked)

| # | Ambiguity | Default applied | Why default works |
|---|---|---|---|
| 6 | Reflexion memory persistence | **Within-session only** for v2.0 | Cross-session memory is a deferred capability; within-session works for a single audition |
| 7 | api_manifest.json refresh | **Refresh once at Stage 1 start**, trust thereafter | Manifest is 72 days old but 100% verified; one refresh on v2 start is sufficient |
| 8 | Continuous-DRC during build | **Block on DRC failure at each checkpoint** (not at end only) | Aligns with Self-Refine pattern; catches violations early when they're cheapest to fix |
| 9 | v1 tests during transition | **Keep `test_blue_pill.py` unchanged**; don't gate on it until Stage 3 stretch | Tests become a finish-line check, not an ongoing gate |
| 10 | Failure escalation channel | **In-conversation AskUserQuestion** with full state dump | Same channel as milestones; consistent UX |
| 11 | "Credible" success criteria | **Owner subjective + documented checklist** in audition contract | Same approach as v1 contract checklist, but augmented with visual-judgment items |

### Scope Tiers

#### Essential v2.0 — must ship to audition

**Stage 1 — Foundation**
- `scripts/render_board.py` — kicad-cli + cairosvg + lxml dark BG, returns `{full, copper, svg}` paths
- `requirements.txt` updates: `cairosvg>=2.7.0`, `lxml>=5.0.0`
- System dep docs: Chocolatey GTK3 runtime install path + manual fallback
- `supplier_profiles/schema.py` — Pydantic models for supplier profile schema
- `supplier_profiles/jlcpcb.yaml` — JLCPCB populated profile
- `scripts/supplier_drc/loader.py` — `load_supplier_profile(name) -> SupplierProfile`, `emit_kicad_dru(profile, path) -> Path`
- `agent_docs/rules/supplier-drc-rules.md` — new mandatory rule
- `contracts/blinker_555_contract.md` — 555 LED blinker audition contract
- `tests/test_blinker_555.py` — audition test suite
- **Demote 4.6 artifacts:** move `scripts/build_blue_pill.py`, `scripts/route_blue_pill.py`, `output/blue_pill.kicad_pcb` (+ `.pro`, `.prl`) to `baselines/4.6/`. The blue_pill contract stays in `contracts/`.
- Refresh `api_manifest.json` at Stage 1 start (run `kipython scripts/discover_api.py`)

**Stage 2 — Iterative Build Architecture**
- `agent_docs/skills/visual-review-skill.md` — per-checkpoint visual rubric + failure-mode catalog + structured JSON output
- `agent_docs/skills/iterative-refinement-skill.md` — decision tree + rework targeting + loop limits + escalation protocol
- `agent_docs/skills/self-critique-skill.md` — meta-skill: posture + 5 anti-patterns + convergence tracking + exit criteria
- Update `agent_docs/skills/pcb-design-skill.md` — replace 12-step monolithic workflow with 8-checkpoint iterative architecture; add references to new skills + new rule
- CLAUDE.md update — add routing entries for new skills + rule; add visual-loop gate to "Before ANY Coding" section
- Reflexion-style episodic memory **within-session**: agent maintains `output/<board>_journal.md` during build, appending lessons learned per checkpoint
- Inline reviewer gate at checkpoints 4 + 6 (after critical_passive_placement, after power_routing) — invokes `design-reviewer` subagent on the rendered output
- Milestone protocol: at the 3 human-milestone boundaries, agent invokes `AskUserQuestion` with render path + critique summary + 3 options

**Stage 3 — Audition**
- Run `blinker_555` end-to-end through the v2 pipeline
- Owner judges at 3 milestones + final
- Audition result documented in `docs/auditions/blinker_555_run1.md`
- **Stretch:** if 555 audition passes, retry `blue_pill` under v2 architecture; compare against `baselines/4.6/blue_pill.kicad_pcb`

#### Valuable v2.x — deferred, useful next

- Additional supplier profiles: PCBWay, OSH Park, Eurocircuits populated YAMLs
- `/review-board` fully repurposed as 3-agent pipeline (reviewer → defender → referee) running on completed boards with structured verdict output
- Reflexion memory persistence **across sessions** — promote `<board>_journal.md` into a persistent learning store
- Component-only render variant (3rd PNG view: F.SilkS + Edge_Cuts)
- Refresh policy for `api_manifest.json` automated (auto-run discover_api.py if file >30 days old)
- Cost-premium warnings during build (flag JLCPCB +++ triggers like trace <3 mil)
- Solder mask clearance enforcement via external Python checker (DRU gap)
- Non-plated hole validator (external Python check)
- Better escalation surfaces (file-based log, web hook for remote monitoring)
- Multi-board project support (a "project" containing multiple `.kicad_pcb` artifacts under one contract)
- Layer stack metadata validation (1.6 mm, 1 oz copper, HASL finish — surface mismatch warnings)

#### Possible Future — not committed

- 4-layer board support (additional layer pairs in render, inner-layer routing in routing_cli)
- BGA / fine-pitch support
- RF / impedance-matched routing (with TDR + length-match constraints)
- Custom footprint generation from datasheet PDFs
- Generative-design exploration (multiple layout candidates, owner picks)
- Multi-supplier optimization (auto-pick cheapest fab that meets requirements)
- Schematic capture (not just PCB layout)
- Integration with non-KiCad EDA suites (Altium, OrCAD export)

## User Feedback
- All four critical ambiguities accepted at "Recommended" default. No pushback.
- Low-impact defaults (#6–#11 above) applied without raising; will be confirmed implicitly when Phase 4 architecture renders them concrete.

## Cross-Phase Consistency Check
✓ Phase 0 Medium-size classification (3 stages) — the scope tiers now map 1:1 to Stage 1 / Stage 2 / Stage 3 Essential work. Consistent.
✓ Phase 1 decisions all surface in Essential v2.0:
  - SVG → PNG via cairosvg → Stage 1 `render_board.py` ✓
  - Hybrid judge (agent self-critique + 3 human milestones) → Stage 2 three skill files + AskUserQuestion at milestones ✓
  - JLCPCB profile + schema for extensibility → Stage 1 `supplier_profiles/` + Stage 1 `supplier-drc-rules.md` ✓
  - No reference image → audition contract template makes no image mention ✓
✓ Phase 2 tech selections all map to Stage 1 / Stage 2 deliverables. No tech orphaned.
✓ Audition board (Phase 3) = 555 blinker matches the "smaller-than-Blue-Pill" intent from Phase 1.
✓ 8-checkpoint structure (Phase 3) is the operational expansion of "checkpoint architecture" pillar from owner-approved diagnosis.
✓ Inline reviewer gates (Phase 3) preserve the v1 review subagents (.claude/agents/) — no orphan code from v1.
✓ `/review-board` repurposing keeps v1's adversarial-review apparatus alive in a clarified role.
✓ No contradictions found.

## Revision History
(none yet)
