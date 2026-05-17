# Phase 0: Classification — AGREED
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions
1. **Project type:** Redesign of an existing Claude-driven KiCad PCB design agent. Not a greenfield project — significant existing infrastructure (KiCad MCP server, agent_docs router pattern, contract framework, 3-agent review pipeline definitions, routing CLI primitives) survives into v2. The redesign replaces the build/route flow + adds new subsystems (visual perception, supplier DRC).
2. **Project size:** **Medium (3 stages)**. The redesign has three distinct workstreams with natural integration points:
   - Stage 1: Foundation (visual perception primitives + supplier DRC profile + audition contract)
   - Stage 2: Iterative build architecture (checkpointed loop + inline review gates + meta-skills)
   - Stage 3: Audition + Blue Pill retry (run new architecture on small board, then scale to Blue Pill)
3. **Initial state captured:** v1 architecture, scripts, blue_pill outputs (Mar 6 2026, DRC-clean but goal-failed), Round 2 git history. MCP server healthy (verify_mcp.py exits 0 today). Reference folder absent locally. api_manifest 72 days old but 100% verified against KiCad 9.0.7.

## Raw Outputs

### Project description
> Redesign of `eda-kicad-agent` (C:\Users\santi\Desktop\Source\eda-kicad-agent). Original goal: prove Claude can autonomously produce credible existing-PCB-replica designs (e.g. STM32 Blue Pill) from a contract alone. Owner's verdict on Round 2 (Opus 4.6, 2026-03-06): goal NOT achieved despite 54/54 tests passing and DRC 0/0. Suspected causes: (1) 4.6's visual reasoning limitations, (2) architectural blockers — no visual feedback loop, monolithic build, hardcoded board scripts, detached review pipeline, missing meta-skills, no supplier-anchored DRC. v2 targets Opus 4.7 + restructured architecture (visual loop, checkpointed iterative build, inline review gates, supplier DRC) to break through.

### Size classification table
| Size | Stages | Fit |
|------|--------|-----|
| Small | 1-2 | Too tight — visual perception infra alone is non-trivial |
| **Medium** | **3** | **Selected — three coherent workstreams with clear integration boundaries** |
| Large | 5 | Over-decomposed — the workstreams aren't enterprise-scale and stages would feel artificial |

### Surviving v1 assets
- KiCAD-MCP-Server installation (`tools/`, 60+ tools)
- agent_docs router pattern (CLAUDE.md + rules/ + skills/)
- Contract framework (`contracts/`)
- 3-agent review pipeline definitions (`.claude/agents/`)
- Slash commands (`/new-board`, `/review-board`, `/research-api`)
- Routing CLI primitive (`scripts/routing_cli.py` — A* pathfinder, JSON I/O)
- Test infrastructure (`tests/conftest.py` fixtures)
- API safety manifest (`api_manifest.json`)
- Toolchain verifier (`scripts/verify_toolchain.py`)
- MCP setup/verifier scripts

### Assets being demoted to baselines/4.6/
- `scripts/build_blue_pill.py` (hardcoded 4.6 output)
- `scripts/route_blue_pill.py` (hardcoded 4.6 output)
- `output/blue_pill.*` (kept as baseline-to-beat)

## User Feedback
- Owner explicitly approved the diagnosis (P1–P7) and added P8 (supplier-anchored DRC) as mandatory.
- Owner's energy: "max effort", "go for it" — wants meaningful momentum, not endless Q&A.
- Owner is the domain expert who will judge the audition output. Reviews happen with him in the loop.
