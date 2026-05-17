# Iterative Refinement Skill

Drives the per-checkpoint Self-Refine loop. Reads the JSON critique from `visual-review-skill.md` and decides one of three outcomes: **proceed** to the next checkpoint, **rework** the current checkpoint, or **escalate** to the human via `AskUserQuestion`.

**When to invoke:** after every `visual-review-skill.md` emission. This skill is the per-checkpoint decision authority. It runs in concert with `self-critique-skill.md` (which audits the critique for anti-patterns) and `pcb-design-skill.md` (which holds the checkpoint state machine).

**Cap:** max 3 iterations per checkpoint. ~12K tokens per critique cycle. Both numbers are firm — see "Loop Limits" below.

---

## Decision Tree

Input: a `visual-review-skill` JSON critique, the current iteration counter `N`, the journal lessons learned so far, and (optionally) the prior critique for trajectory analysis.

Output: `{ "decision": "proceed" | "rework" | "escalate", "reasoning": str, "next_action": str, "rework_scope": [...] }`.

```
                  ┌─────────────────────────────────────────────────────┐
                  │  Input: critique JSON, iteration N, prior_critique  │
                  └────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────────┐
                  │ STEP 1: Apply hard ceilings (highest priority)      │
                  └────────────────────────┬────────────────────────────┘
                                           │
                  ┌────────────────────────┴────────────────────────┐
                  │  If N >= 3 AND issues still present:            │
                  │      → ESCALATE ("max 3 iterations reached")    │
                  │  If confidence < 0.5 AND N >= 2:                │
                  │      → ESCALATE ("agent doesn't know what's wrong")│
                  │  If oscillation detected (same net 3+ rework):  │
                  │      → ESCALATE ("thrashing")                   │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────────┐
                  │ STEP 2: Apply pass criteria                         │
                  └────────────────────────┬────────────────────────────┘
                                           │
                  ┌────────────────────────┴────────────────────────┐
                  │  If pass_fail == "pass" AND confidence >= 0.85: │
                  │      → PROCEED                                  │
                  └────────────────────────┬────────────────────────┘
                                           │
                                           ▼
                  ┌─────────────────────────────────────────────────────┐
                  │ STEP 3: Apply severity triage                       │
                  └────────────────────────┬────────────────────────────┘
                                           │
                  ┌────────────────────────┴────────────────────────┐
                  │  If any issue.severity == "CRITICAL":           │
                  │      → REWORK (scope = CRITICAL + MAJOR only)   │
                  │  If only MAJOR issues:                          │
                  │      → REWORK (scope = MAJOR)                   │
                  │  If only MINOR issues AND confidence >= 0.85:   │
                  │      → PROCEED (record MINOR in journal)        │
                  │  If only MINOR AND confidence < 0.85:           │
                  │      → REWORK (top-3 MINOR by score)            │
                  └─────────────────────────────────────────────────┘
```

Pseudocode (canonical):

```python
def decide(critique, N, prior_critique=None, journal=None):
    # STEP 1: hard ceilings (override all other logic)
    if N >= 3 and critique["issues"]:
        return {"decision": "escalate", "reasoning": "max 3 iterations reached, issues persist"}
    if critique["confidence"] < 0.5 and N >= 2:
        return {"decision": "escalate", "reasoning": "confidence below 0.5 threshold after iter 2"}
    if detect_oscillation(journal):
        return {"decision": "escalate", "reasoning": "thrashing — same net modified 3+ times"}

    # STEP 2: pass criteria
    if critique["pass_fail"] == "pass" and critique["confidence"] >= 0.85:
        return {"decision": "proceed", "reasoning": "all pass_criteria met, confidence >= 0.85"}

    # STEP 3: severity triage
    severities = {i["severity"] for i in critique["issues"]}
    if "CRITICAL" in severities:
        scope = [i for i in critique["issues"] if i["severity"] in ("CRITICAL", "MAJOR")]
        return {"decision": "rework", "rework_scope": scope, "reasoning": "CRITICAL findings"}
    if "MAJOR" in severities:
        return {"decision": "rework", "rework_scope": [i for i in critique["issues"] if i["severity"] == "MAJOR"]}
    if critique["confidence"] >= 0.85:
        return {"decision": "proceed", "reasoning": "MINOR only, confidence threshold met"}
    return {"decision": "rework", "rework_scope": critique["issues"][:3], "reasoning": "MINOR cluster, confidence below 0.85"}
```

---

## Rework Scope Targeting

When `decision == "rework"`, you do NOT redo the whole checkpoint. You target the specific issues from the critique. This table maps each catalog failure mode to a single agent action plus the concrete tool invocation.

| Issue type | Action | Tool | Concrete command |
|-----------|--------|------|-------------------|
| Component overlap (mode 1) | Move offending component | MCP `pcb_move_component` | `pcb_move_component(ref="C5", x_mm=22, y_mm=8)` |
| Unrouted net island (mode 2) | Manual seed point + re-route | `scripts/routing_cli.py` | `--action find_path --start <pad1> --end <pad2> --width 0.25` then `--action route --net <name> --waypoints "..."` |
| Thin power trace (mode 3) | Rip up + re-route at wider width | `scripts/routing_cli.py` | `--action rip_up --net VCC` then `--action route --net VCC --waypoints "..." --width 0.5` |
| Decap too far (mode 4) | Re-place cap + re-route its 2 nets | MCP move + `routing_cli.py` | `pcb_move_component(ref="C2", ...)`; `--action rip_up --net VCC --pad C2.1`; `--action route ...` |
| Via stub resonance (mode 5) | Reduce layer transitions on net | `scripts/routing_cli.py` | `--action rip_up --net <high-speed>`; re-route entirely on F.Cu |
| Ground plane island (mode 6) | Place GND stitching via inside island | `scripts/routing_cli.py` | `--action via --net GND --pos <x>,<y>` then `--action fill_zones` |
| Silk-on-pad (mode 7) | Hide or offset silk reference | KiCad API silk edit | (pcbnew: `fp.Reference().SetVisible(False)` or `.SetPosition(...)`) |
| Diff pair skew (mode 8) | Serpentine shorter trace | `scripts/routing_cli.py` | `--action rip_up --net USB_D+`; re-route with adjusted waypoints to add length |
| Missing via stitching (mode 9) | Place stitching vias on 5 mm grid | `scripts/routing_cli.py` | Loop: `--action via --net GND --pos <x>,<y>` at each grid point |
| Trace-to-pad clearance (mode 10) | Re-route trace with wider clearance | `scripts/routing_cli.py` | `--action rip_up --net <offending>`; `--action find_path` with adjusted bbox |

After every rework action, you MUST re-render and re-critique. The loop is:

```
1. iterative-refinement-skill: decision = "rework", scope = [issue_A, issue_B]
2. apply_rework(issue_A)  # one of the actions above
3. apply_rework(issue_B)
4. scripts/routing_cli.py --action drc  # mid-rework safety check
5. scripts/render_board.py <pcb>  # fresh PNG
6. visual-review-skill.md  # new critique, with prior_critique passed
7. iterative-refinement-skill: decide again, N += 1
```

---

## Loop Limits

These are firm. Do not relax them.

- **Max 3 iterations per checkpoint.** Empirically (Self-Refine literature): iter 1 catches 70-80% of issues; iter 2 catches cascading effects; iter 3 plateaus. Iter 4+ thrashes — same net keeps getting modified without convergence. Hard escalation at iter 3.
- **~12K tokens per critique cycle.** Breakdown: 3K critique (visual-review JSON + walking the catalog) + 4K rework planning (this skill applying the decision tree) + 2K tool execution (routing_cli/MCP calls) + 3K re-render and re-verify + 1K buffer. If a cycle exceeds 15K tokens, the rework scope is too broad — reduce to top-3 issues by severity.
- **Convergence rule.** Across the 3 iterations on a single checkpoint, issue count must monotonically decrease AND confidence must monotonically increase. Any reversal (issue count goes up, or confidence drops) signals thrashing or over-correction → escalate immediately, do not wait for iteration 3.
- **Aggregate budget.** Full 8-checkpoint build at perfect convergence: ~288K tokens. With 1 escalation per 2 checkpoints: ~350K tokens. Both within the Opus 4.7 1M context.

---

## Routing CLI Coordination

When rework requires copper modifications, you coordinate with `scripts/routing_cli.py`. The CLI is single-action; you call it once per primitive. The KiCad bundled Python from `config.json` is the only interpreter that imports `pcbnew`.

Inspection commands (read board state):

```bash
# Board summary — what's placed, what's routed, unconnected count
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action summary

# Equivalent shorthand — pcb_status (same data, faster path through the CLI)
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action pcb_status

# Unrouted nets list — for verifying full coverage
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action unrouted

# Pad positions for a net — needed before find_path
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action net_pads --net HSE_IN

# Obstacles in a bbox — for collision-aware re-routing
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action obstacles --bbox 10,5,25,15
```

Action commands (modify board):

```bash
# Route a trace — pcb_route shorthand
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action pcb_route --net HSE_IN --waypoints "15,10;18,12;22,14" --width 0.25 --layer F.Cu

# Place a via — pcb_via shorthand
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action pcb_via --net GND --pos 10,12

# Rip up all traces for a net (when re-routing)
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action rip_up --net VCC

# Zone (GND pour) — typically only at checkpoint 8
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action zone --net GND --layer B.Cu --priority 0

# Re-render for next critique iteration — pcb_render shorthand
"<kicad_python>" scripts/render_board.py output/<board>.kicad_pcb
# or via routing_cli: --action pcb_render --board output/<board>.kicad_pcb

# DRC check — pcb_drc shorthand
"<kicad_python>" scripts/routing_cli.py --board output/<board>.kicad_pcb --action pcb_drc
```

Coordination protocol:

1. Before any rework: `pcb_status` to confirm current board state matches the critique's assumptions.
2. For each issue in `rework_scope`: apply the action from the targeting table.
3. After all rework: `pcb_drc` mid-rework to catch obvious regressions before re-rendering (DRC fails fast).
4. `pcb_render` to produce fresh PNGs for the next critique.
5. Re-invoke `visual-review-skill` with `iteration += 1`.

---

## Escalation Protocol

When the decision tree says `escalate`, you produce a structured handover to the human via `AskUserQuestion`. The agent does NOT silently abort; the human gets the choice.

Steps (in order, do not skip):

1. **Dump current state to the journal.** Append a `## Escalation` block to `output/<board>_journal.md` with: iteration number, last 3 critiques' summaries, the unresolved issues, the reason for escalation (max iter / low confidence / oscillation).
2. **Re-render for fresh PNG.** Call `scripts/render_board.py <pcb>` so the human sees the current state, not a stale render.
3. **Call `AskUserQuestion`.** Use this template:

```python
AskUserQuestion(
    question=f"Escalation — checkpoint '{checkpoint_name}' did not converge after {N} iterations. Review and choose.",
    context={
        "render_path_full": "output/<board>_full.png",
        "render_path_copper": "output/<board>_copper.png",
        "checkpoint": checkpoint_name,
        "iterations_used": N,
        "last_confidence": last_critique["confidence"],
        "unresolved_issues": [
            {"severity": i["severity"], "type": i["type"], "description": i["description"]}
            for i in last_critique["issues"]
        ],
        "journal_excerpt": "...last 3 iteration summaries from output/<board>_journal.md...",
        "escalation_reason": "max 3 iterations reached" | "confidence < 0.5 after iter 2" | "thrashing detected",
    },
    options=[
        {"id": "provide_hint", "label": "I'll provide a specific hint to unblock"},
        {"id": "rework_specific", "label": "Rework a specific issue (specify which)"},
        {"id": "abort_checkpoint", "label": "Abort this checkpoint, record verdict and continue"},
        {"id": "abort_audition", "label": "Abort the whole audition cleanly"},
    ],
)
```

4. **Wait for the response.** Do not continue the loop until the human responds. Confidence threshold for re-entering the loop after an escalation: human selects `provide_hint` or `rework_specific` → resume with iteration counter reset to 1 (under human guidance, the next loop is a fresh attempt, not iteration 4).

Escalation reasons enumerated:

- `"max 3 iterations reached"` — iter 3 complete, issues still present
- `"confidence below 0.5"` — confidence < 0.5 on iteration ≥ 2 (the canonical 0.5 threshold)
- `"thrashing detected"` — same net modified 3+ times with oscillating values
- `"over-correction detected"` — new CRITICAL appeared after a rework
- `"contract ambiguity"` — the critique can't be resolved because the contract doesn't specify (rare; escape hatch)

---

## Anti-Patterns to Avoid

These pathological loop behaviors are detected and stopped. See `self-critique-skill.md` for the full anti-pattern catalog; this section is what THIS skill checks for in its own decisions.

1. **Local optimum trap.** Reworking MINOR issues while CRITICAL ones remain unchanged. Detection: `rework_scope` contains MINOR but no CRITICAL, while critique lists CRITICAL. Mitigation: triage CRITICAL → MAJOR → MINOR in scope filter (already baked into severity triage step 3 above; never select MINOR if CRITICAL present).
2. **Thrashing.** Same net modified 3+ times across iterations with oscillating values (e.g., trace moved left, then right, then left). Detection: scan journal for `net X reworked` count ≥3. Mitigation: escalate immediately, do not attempt iteration N+1.
3. **Token explosion.** Cycle exceeds 15K tokens because rework scope is too broad. Detection: count tokens used in `apply_rework` step. Mitigation: filter `rework_scope` to top-3 issues by severity-then-impact.
4. **Over-correction.** A rework introduces a NEW CRITICAL that wasn't in the prior critique. Detection: compare current critique's CRITICAL list vs `prior_critique`. Mitigation: do NOT advance the iteration counter for over-correction; treat it as a fresh attempt, re-run rework with narrower scope.
5. **Early escalation.** Escalating on iteration 1 with all-MINOR issues. Detection: `decide()` returns `escalate` with `N == 1`. Mitigation: require `N >= 2` for escalation OR `confidence < 0.3` (collapse case only); otherwise force `rework`.

---

## Required Reading

- `agent_docs/skills/visual-review-skill.md` — produces the JSON critique this skill consumes
- `agent_docs/skills/self-critique-skill.md` — meta-skill that audits the loop posture (called between critique and decide)
- `agent_docs/skills/pcb-design-skill.md` — holds the checkpoint state machine; invokes this skill per checkpoint
- `agent_docs/skills/routing-skill.md` — the trace/via primitives and the MCP-routing-banned rule
- `scripts/routing_cli.py --help` — exact CLI surface
- `agent_docs/rules/supplier-drc-rules.md` — supplier DRC thresholds (consulted before final-iter proceed)

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Max iterations per checkpoint | **3** (firm — escalate at iter 3) |
| Token budget per cycle | **~12K** (3K critique + 4K rework + 2K exec + 3K re-render + 1K buffer) |
| Escalation confidence threshold | **0.5** (after iteration ≥ 2) |
| Proceed confidence threshold | **0.85** (combined with pass_fail == "pass") |
| Oscillation detection | Same net modified **3+ times** → escalate |
| Convergence rule | Issue count monotonically ↓ AND confidence monotonically ↑ |
| Escalation tool | **AskUserQuestion** with 4 options (provide_hint / rework_specific / abort_checkpoint / abort_audition) |
