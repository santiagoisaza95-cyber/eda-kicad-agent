# Context: Agent Skills (`agent_docs/skills/`)

## Boundary

`agent_docs/skills/` contains the **workflow** documents the agent reads to perform PCB design tasks. Skills are operational guides — they describe *how* to do something, when to invoke other skills, and what tools to use. They are NOT hard rules; hard rules live in `agent_docs/rules/` (coding-rules, clearance-rules, drc-rules, supplier-drc-rules, testing-rules, test-failing-rules). Skills cross-reference rules; they do not duplicate them.

A skill should answer: "I am at point X in a build — what do I do next, what tool do I use, and which other skill or rule do I consult?" If a document instead enforces a constraint without choice (e.g., "clearance must be ≥0.5 mm"), it belongs in `agent_docs/rules/`, not here.

## Skill Inventory

The v2 architecture has 7 skills: 4 surviving from v1 (placement, kicad-api, routing, pcb-design [now rewritten]) and 3 new in v2 Stage 2 (visual-review, iterative-refinement, self-critique).

| Skill | Purpose (1 line) | Invoked by / when in workflow | Depends on |
|-------|------------------|--------------------------------|------------|
| `pcb-design-skill.md` | **Orchestrator.** 8-checkpoint state machine for every PCB build; owns journal protocol; wires inline reviewer + AskUserQuestion milestones | Top-level when a PCB build task starts (CLAUDE.md routing: "Designing a PCB") | visual-review, iterative-refinement, self-critique, placement, routing, kicad-api, supplier-drc-rules, render_board.py, routing_cli.py |
| `visual-review-skill.md` | **Per-checkpoint visual critique.** Walks rubric + 10-entry failure-mode catalog over rendered PNG; emits structured JSON critique | After every render inside the per-checkpoint loop (8x per build minimum) | render_board.py output, clearance-rules, supplier-drc-rules, `research/self_critique_patterns_research.md` |
| `iterative-refinement-skill.md` | **Decision authority.** Reads visual-review JSON; decides proceed / rework / escalate; targets rework scope to specific routing_cli commands | After every visual-review emission; runs the Self-Refine loop | visual-review, self-critique, routing-skill, routing_cli.py, supplier-drc-rules |
| `self-critique-skill.md` | **Meta-skill.** Audits the critique loop itself for 5 anti-patterns (rubber-stamping, thrashing, over-correction, early escalation, local-optimum trap); tracks convergence | Between visual-review and iterative-refinement; also before any AskUserQuestion escalation | visual-review, iterative-refinement, `research/self_critique_patterns_research.md` |
| `placement-skill.md` (v1 survivor) | **Placement primitives.** 5-phase placement workflow (mechanicals → ICs → critical passives → remaining passives → verify); clearance quick reference | During checkpoints 1-5 inside pcb-design-skill | clearance-rules, kicad-api-skill |
| `routing-skill.md` (v1 survivor) | **Routing primitives.** Routing CLI usage (MCP banned), layer strategy, routing priority, EMC ground rules, via standards | During checkpoints 6-8 inside pcb-design-skill | routing_cli.py, drc-rules, clearance-rules |
| `kicad-api-skill.md` (v1 survivor) | **pcbnew API reference.** Verified core object patterns (BOARD, PCB_SHAPE, NETINFO_ITEM, footprint loading, save); requires `api_manifest.json` cross-check | On-demand when uncertain about a pcbnew function signature | `api_manifest.json`, `/research-api` slash command |

## Load Order During a Build

Skills are NOT all loaded eagerly at session start. The agent reads them in this order:

1. **Session start.** Agent reads `CLAUDE.md` (always). From the routing table, identifies which skill matches the user's task.
2. **Task = PCB build.** Agent reads `agent_docs/skills/pcb-design-skill.md` (the orchestrator). This skill's "Required Reading" section instructs the agent to load the contract + supplier-drc-rules next.
3. **Before any routing checkpoint.** Agent reads `agent_docs/rules/supplier-drc-rules.md` and emits `output/<board>.kicad_dru`. This is mandatory and gated.
4. **First entry into the per-checkpoint loop.** Agent reads `visual-review-skill.md`, `iterative-refinement-skill.md`, `self-critique-skill.md`. These are loaded once and re-applied at every checkpoint without re-reading.
5. **Checkpoints 1-5 actions.** Agent consults `placement-skill.md` for placement primitives.
6. **Checkpoints 6-7 actions.** Agent consults `routing-skill.md` for routing primitives.
7. **On-demand.** Agent consults `kicad-api-skill.md` only when uncertain about a specific pcbnew function. If still uncertain after reading, agent invokes the `/research-api` slash command rather than guessing.

The 3 new v2 skills (visual-review, iterative-refinement, self-critique) are loaded **eagerly at first per-checkpoint-loop entry** because they run on every iteration. The 3 v1-survivor primitive skills (placement, routing, kicad-api) are loaded **on-demand** at the checkpoints where they're needed.

## Cross-Skill Dependency Graph

`pcb-design-skill` is the orchestrator. Every other skill is either invoked by it (during the per-checkpoint loop) or referenced by it (as a primitive source). The graph is acyclic:

```
                          ┌──────────────────────────┐
                          │   pcb-design-skill.md    │   (orchestrator)
                          │   - 8 checkpoints         │
                          │   - journal protocol     │
                          │   - inline reviewer wire │
                          │   - AskUserQuestion wire │
                          └─────┬────────────────┬───┘
                                │                │
                  per-checkpoint│                │ checkpoint-specific
                  loop (every N)│                │ primitives
                                ▼                ▼
   ┌─────────────────────────────────┐    ┌──────────────────────────┐
   │  visual-review-skill.md         │    │ placement-skill.md (CP 1-5)│
   │  - PLACEMENT/POWER_ROUTING/...  │    │ routing-skill.md   (CP 6-7)│
   │    rubric per checkpoint        │    │ kicad-api-skill.md (on-demand)│
   │  - 10-entry failure-mode catalog│    │                          │
   │  - JSON critique output         │    │ (all unchanged from v1)  │
   └──────────────┬──────────────────┘    └──────────────────────────┘
                  │ JSON critique
                  ▼
   ┌─────────────────────────────────┐
   │  self-critique-skill.md         │     ┌──────────────────────────┐
   │  - 5 anti-patterns              │ ◄──►│  supplier-drc-rules.md   │
   │  - convergence tracking         │     │  (rule, NOT skill)       │
   │  - posture audit                │     │  mandatory pre-routing   │
   └──────────────┬──────────────────┘     └──────────────────────────┘
                  │ critique passes
                  ▼
   ┌─────────────────────────────────┐
   │  iterative-refinement-skill.md  │
   │  - decision tree                │
   │  - proceed / rework / escalate  │
   │  - rework scope targeting       │
   │  - escalation protocol          │
   └──────────────┬──────────────────┘
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     proceed   rework    escalate
     (next CP) (re-loop) (AskUserQuestion)
```

**Per-checkpoint flow** (executed 8 times per build): `pcb-design-skill` runs the actions → `render_board.py` produces PNGs → `visual-review-skill` walks rubric + catalog → `self-critique-skill` audits the critique → `iterative-refinement-skill` decides → either advance (next checkpoint) or re-loop (rework) or escalate (`AskUserQuestion`).

**Supplier DRC is mandatory pre-routing.** Before any routing checkpoint (6, 7), the agent must have loaded the supplier profile and emitted the DRU per `supplier-drc-rules.md`. This is enforced by `pcb-design-skill.md` → Preconditions Before First Checkpoint, and again gated at the entry to checkpoint 6.

## Style Conventions

All skill files follow the same structure (the existing skills are the reference):

- **H1 title** (`# Skill Name`) — one line, descriptive
- **Intro paragraph** — purpose + when to invoke + posture (2-4 sentences)
- **H2 sections** — `## Section Name` for each major topic. Use the section titles required by the skill's test (the structural tests assert specific H2 headings)
- **Tables** for rubrics, catalogs, decision trees with discrete cases
- **Fenced code blocks** for CLI invocations, JSON schemas, pseudocode
- **Required Reading** section at the bottom — cross-references to other skills + rules + research docs
- **Quick Reference** table at the very bottom (for skills with numeric thresholds)
- **No emojis.** No marketing voice. Operational tone matching v1 placement-skill / routing-skill style.

## How to Add a New Skill

1. **Name.** `agent_docs/skills/<name>-skill.md` (kebab-case, ends in `-skill.md`).
2. **Author.** Follow the style conventions above. Include a When to Invoke section, a Required Reading section, and H2 sections matching whatever specific structural test (if any) is committed for the skill.
3. **CLAUDE.md routing.** Add a row to the Task Routing table in `CLAUDE.md` so the agent can find the new skill from a task description.
4. **Structural test (optional but recommended).** Add `tests/test_<name>_skill.py` that asserts the required H2 headings + any named entities (anti-patterns, checkpoints, JSON fields) are present in the markdown. Pattern: see `tests/test_visual_review_skill.py`.
5. **Update this context doc.** Add the new skill to the Skill Inventory table + the Cross-Skill Dependency Graph if it has interactions with existing skills.
6. **Update `pcb-design-skill.md` Required Reading** if the new skill is invoked from the per-checkpoint loop.

If the document is enforcing a constraint without procedural choice ("must be ≥X", "always do Y"), it is NOT a skill — it is a rule, and belongs in `agent_docs/rules/` instead. Skills describe workflows; rules enforce constraints.
