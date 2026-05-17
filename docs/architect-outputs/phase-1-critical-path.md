# Phase 1: Critical Path Disambiguation — AGREED
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions
1. **Visual render mechanism:** `kicad-cli pcb export svg → PNG via Pillow/cairosvg`. Cross-platform, no GUI dependency, ~1–2s per render. Adds `cairosvg` (or equivalent) to `requirements.txt`. Drives Stage 1 dependencies.
2. **Visual judge:** Hybrid — agent self-critiques every checkpoint + owner eyeballs 3 milestones (outline-done, placement-done, routing-done). Forks orchestration: meta-skills must include self-critique, and the build flow must pause at three explicit human-touchpoints.
3. **Supplier DRC scope:** JLCPCB profile populated for v2.0, **but** the supplier-DRC subsystem MUST be designed as a configurable profile system from day one — schema-first so future suppliers (PCBWay, OSH Park, Eurocircuits, custom) plug in without rework. This is a critical clarification from the recommended option: not "JLCPCB only" but "JLCPCB FIRST with the abstraction ready for others."
4. **Reference image policy:** **NO** — pure contract-only. v2 keeps v1's "DESIGN FROM THIS CONTRACT ONLY" constraint intact. The audition tests the agent's ability to imagine the board purely from text + supplier-anchored rules + agent_docs. This preserves the original goal's purity.

## Raw Outputs

### Questions Asked + Verbatim Answers

**Q1. Visual render mechanism**
- User answer: *"kicad-cli pcb export svg → PNG via Pillow/cairosvg (Recommended)"*

**Q2. Visual judge**
- User answer: *"Hybrid: agent self-critiques every checkpoint + you eyeball 3 milestones (Recommended)"*

**Q3. Supplier DRC scope**
- User answer: *"i think the recommended but the skill should be prepare to validate any other dec from different supplier"*
- Interpretation: option A (JLCPCB only) selected for the populated profile, BUT with the skill/system designed to accept additional supplier profiles. Effectively a hybrid of options A + D — JLCPCB now, schema designed for extensibility.

**Q4. Reference image policy**
- User answer: *"NO — pure contract-only, keep the v1 constraint intact (Recommended)"*

### Architectural Implications

| Decision | Architectural Implication |
|---|---|
| SVG → PNG | Stage 1 deliverable: `scripts/render_board.py` wrapping `kicad-cli pcb export svg` + cairosvg. New Python dependency. |
| Hybrid judge | Stage 2 deliverable: `agent_docs/skills/visual-review-skill.md` (self-critique) AND owner-checkpoint protocol embedded in build flow. Three explicit human milestones per audition. |
| Schema-first supplier DRC | Stage 1 deliverable: `supplier_profiles/` directory with `schema.json` + `jlcpcb.yaml` (or similar). Build pipeline reads supplier profile, projects rules into KiCad DRC settings, and gates DRC against them. New rule: `agent_docs/rules/supplier-drc-rules.md`. |
| No reference image | Contract template unchanged on this dimension. The audition success metric remains "owner judges credible from contract-only build." Visual loop is intra-build self-critique, not contract-bundled reference. |

## User Feedback
- Owner clarified that "Recommended" supplier scope choice should not preclude future expansion — interpret as a directive to build extensibility into the supplier-DRC subsystem from the start, not as scope creep but as foundational design.
- All four critical-path answers align with the v2 spirit: prefer the simpler choice IF it doesn't preclude scaling.

## Cross-Phase Consistency Check
✓ Phase 0 size classification (Medium / 3 stages) remains valid:
  - Stage 1: Foundation (visual render + supplier DRC profile schema + JLCPCB rules + audition contract)
  - Stage 2: Iterative build architecture (checkpoint loop + inline review gates + meta-skills + 3 human milestones)
  - Stage 3: Audition + Blue Pill retry
✓ Phase 0 "surviving v1 assets" list still valid — no decision invalidates routing_cli.py or KiCAD-MCP-Server.
✓ Phase 0 "demote to baselines/4.6/" list still valid.
✓ No contradictions found.
