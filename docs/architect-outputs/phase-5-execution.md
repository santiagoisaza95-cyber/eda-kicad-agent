# Phase 5: Execution Planning — LIGHT TOUCH
Date: 2026-05-16
Project: eda-kicad-agent v2 (redesign)

## Decisions
1. **Batch composition** — done in stage docs. See `docs/stages/stage-{1,2,3}-foundation-200k.md`. 12 batches total (4 in Stage 1, 4 in Stage 2, 3 in Stage 3 with batch 3.3 hard-gated on 3.2 pass).
2. **Light Phase 5** — owner's original brief: "NO IMPLEMENTATION until owner signs off on the architecture doc." Full HIL stage-contract creation + orchestration choreography is therefore **deferred until cto-executor is invoked** for v2 implementation. Phase 5 here captures the rule set + choreography sketch the future CTO will consume; full contracts are draft-time, not architect-time.
3. **Architect deliverable shifts to Phase 6** — the unified `architecture_v2_proposal.md` handover doc is the owner-review surface, not a 12-stage-contract corpus.

## Raw Outputs

### Batch Summary (cross-stage)

| Stage | Batches | Validation gate |
|---|---|---|
| Stage 1 | 1.1 Render pipeline / 1.2 Supplier DRC / 1.3 555 contract / 1.4 Baselines + manifest + routing-primitives doc | Per-batch pytest checkpoints; all 4 batches green = Stage 1 done |
| Stage 2 | 2.1 Three skills + tests / 2.2 pcb-design rewrite + journal + inline reviewer / 2.3 CLAUDE.md + /review-board / 2.4 Stub-contract dry-run | Per-batch checkpoint; stub-contract dry-run = Stage 2 done |
| Stage 3 | 3.1 555 audition execution / 3.2 Audition outcome doc [HARD GATE] / 3.3 STRETCH Blue Pill v2 + comparison | Owner's "credible 555" verdict gates Batch 3.3; owner's "v2 unblocks goal" verdict is ultimate v2 verdict |

### Rule Set Identification (CTO-Orchestration)

When the owner later invokes `/cto-executor` to build v2, the applicable rule set from `C:\Users\santi\.claude\rules\cto-orchestration\`:

| Role | Rule files | Notes |
|---|---|---|
| All teammates | `team/communication.md`, `team/compaction-recovery.md`, `team/shutdown-protocol.md`, `team/task-dependency.md` | Always included |
| CTO | `cto/audit-gate.md`, `cto/blocker-protocol.md`, `cto/delegation-protocol.md`, `cto/fresh-team-per-stage.md`, `cto/neutral-prompts.md`, `cto/no-donkey-work.md`, `cto/session-handover.md` | Fresh team between stages = mandatory at Stage 1→2 and Stage 2→3 |
| Worker (implementation) | `worker/completion-protocol.md`, `worker/contract-compliance.md`, `worker/idle-until-green.md`, `worker/no-test-modification.md` | Per-batch self-verification + idle-on-block |
| Tester | `tester/feasibility-check.md`, `tester/result-reporting.md`, `tester/test-execution.md`, `tester/telemetry-verification.md` (advisory — TELEMETRY: EXEMPT here) | Telemetry advisory because no WebSocket layer; standard pytest only |
| Auditor | `auditor/contract-authority.md`, `auditor/independence.md`, `auditor/project-summary-verify.md`, `auditor/report-dont-fix.md`, `auditor/test-file-integrity.md`, `auditor/telemetry-audit.md` (advisory), `auditor/verdict-protocol.md` | Auditor checks test-file integrity (no worker tampering with tests) + green/red verdicts |
| Scribe | `scribe/append-only.md`, `scribe/crash-marker.md`, `scribe/timestamp-protocol.md` | `project_summary.md` maintenance |

**Project-specific rules to add (suggested):**
- `rules/eda-kicad/no-mcp-routing.md` — codify the v1→v2 mandate: MCP route_trace/route_pad_to_pad/route_differential_pair are BANNED; always use `scripts/routing_cli.py`. Already in CLAUDE.md but worth codifying as a rule for auditor enforcement.
- `rules/eda-kicad/kipython-only-for-pcbnew.md` — scripts that import pcbnew must run under `"C:\Program Files\KiCad\9.0\bin\python.exe"` (kipython), not the venv python.

### Orchestration Choreography Sketch

| Stage | Team composition | Task dependency template | Fresh team boundary |
|---|---|---|---|
| Stage 1 | 1 worker (per batch sequential is fine; or 4 workers parallel for 1.1/1.2/1.3/1.4 since batches are largely independent) + 1 tester + 1 auditor + 1 scribe | 1.1 ⊥ 1.2 ⊥ 1.3 ⊥ 1.4 (all independent batches; can parallelize). Each batch completes → tester verifies → auditor green-lights → next batch unblocked | Fresh team before Stage 2 starts |
| Stage 2 | 1 worker for the heavy rewrite batches (2.1, 2.2) since they touch a lot of text and benefit from coherent authorship; 1 worker for 2.3 (CLAUDE.md + review-board updates) + 1 tester + 1 auditor + 1 scribe | 2.1 → 2.2 → 2.3 → 2.4 (mostly sequential because 2.2 references 2.1's skills + 2.3 references all). 2.4 dry-run gates Stage 3 | Fresh team before Stage 3 starts |
| Stage 3 | NO worker team — this is a session-driven audition by the owner with Opus 4.7 directly. Scribe optional for `project_summary.md` updates | 3.1 → 3.2 → [HARD GATE] → 3.3 | N/A (audition = single session, not CTO-orchestrated build) |

### Validation Checkpoints — already in stage docs

Each batch in `docs/stages/stage-{1,2,3}-foundation-200k.md` ends with a concrete `**Checkpoint**:` line specifying exact commands and expected pass criteria. These ARE the validation contracts the CTO + auditor will enforce.

### Anti-Scaffolding Audit Notes

For v2 implementation, particular anti-scaffolding traps to watch:
- `scripts/render_board.py` must actually render a real PCB, not stub PNG files
- `supplier_profiles/jlcpcb.yaml` must contain real JLCPCB values (cross-check against `research/supplier_drc_research.md`), not placeholder zeros
- `contracts/blinker_555_contract.md` must have a real component table + netlist, not "TBD"
- Each of the 3 new skill files must contain actionable rubrics + JSON schemas, not just headings
- The Reflexion journal protocol must be exercised by the dry-run in Batch 2.4, not just documented in text
- Stage 3 audition must produce a real built board, not a contract walkthrough

## User Feedback
*(N/A — light Phase 5 by design; owner's brief precludes implementation contracts at this stage.)*

## Cross-Phase Consistency Check
✓ Batch composition matches Phase 3 Essential v2.0 / Stage 1+2+3 deliverables. No orphan tasks.
✓ Rule set respects TELEMETRY: EXEMPT (Phase 4) — telemetry rules marked advisory.
✓ Project-specific rule suggestions align with v1 hard constraints surviving to v2 (no MCP routing, kipython required).
✓ Fresh team boundaries match Phase 0 size classification (3 stages → fresh between each).
✓ Hard gate on Batch 3.3 (Phase 4 + Plan agent's #7 reconciliation) preserved.
✓ Stage 3 noted as session-driven not CTO-orchestrated; matches the "Opus 4.7 audition" intent.
✓ No contradictions found.

## Deferred to v2 Implementation Time
- Full HIL stage-contract creation (one `contracts/stage-1.contract.md` / `stage-2.contract.md` / `stage-3.contract.md` with interface signatures, verification commands, completion checklists). When `/cto-executor` is invoked, draft these from the stage docs.
- Specific team assignments + worker names (depends on cto-executor's instantiation).
- `project_summary.md` initial state for v2 (scribe writes this on day 1 of implementation).
- Detailed dependency graph nodes (current sketch above is sufficient for owner review; CTO will materialize the TaskCreate task graph on invocation).
