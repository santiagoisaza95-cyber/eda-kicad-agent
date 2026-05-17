# Self-Critique Skill (meta-skill)

This is a META-SKILL. It does NOT critique a PCB. It critiques the **critique loop itself** — the agent's posture, the convergence trajectory across iterations, and the decision to invoke `visual-review-skill.md`, `iterative-refinement-skill.md`, or `AskUserQuestion`. Its job is to catch the loop's pathological behaviors before they burn cycles.

**When to invoke:** between `visual-review-skill.md` and `iterative-refinement-skill.md` on every iteration. Also: any time the agent is about to escalate, the agent must self-check whether the escalation is genuine or premature.

**Cross-references:** see [`visual-review-skill.md`](visual-review-skill.md) and [`iterative-refinement-skill.md`](iterative-refinement-skill.md).

---

## Posture

You are an **adversarial but honest** reviewer of your own work.

- **Adversarial:** assume the current design state is broken until proven otherwise. Default stance is doubt, not approval. If you find nothing wrong, your second thought is "what did I miss?", not "great, ship it."
- **But honest:** you do not fabricate issues to look thorough. If the design genuinely satisfies the rubric and the catalog walk turns up nothing, return `pass_fail: "pass"` with `confidence >= 0.85` and let the convergence trajectory speak for itself.

The asymmetry: false-positive issues (fabricated MINOR) waste a few rework cycles. False-negative misses (CRITICAL slipped past as `pass`) waste the entire audition. Lean toward false-positive, but only WITHIN the failure-mode catalog — never invent new failure categories.

Confidence is **earned, not assumed**. A `confidence: 0.95` claim must be backed by every `pass_criteria` item being `true` AND the catalog walk turning up nothing. If those conditions don't hold, the claim is rubber-stamping.

---

## Five Anti-Patterns + Mitigations

These five pathologies are the failure modes of self-critique. Each has a specific detection signal and a specific mitigation. If your loop matches a detection signal, apply the mitigation immediately — do not advance the iteration counter.

| # | Anti-pattern | Detection signal | Mitigation |
|---|---|---|---|
| 1 | **Rubber-stamping** | `visual-review` returns zero issues for 2+ consecutive iterations on the same checkpoint, with `confidence >= 0.85` each time | Force adversarial mode on the next iteration: re-walk the failure-mode catalog and list anything you cannot affirmatively rule out at MINOR severity. If still zero after adversarial re-walk: trust the pass. |
| 2 | **Thrashing** | Same net modified 3+ times across iterations with oscillating values (left→right→left, narrow→wide→narrow) | "Do not undo" memory: scan the journal for prior-iteration actions on the same net before applying a new modification. If oscillation detected, escalate via `AskUserQuestion` — do not attempt iteration N+1. |
| 3 | **Over-correction** | A new CRITICAL appears in iteration N+1 that wasn't in iteration N. Net effect of rework was negative. | Dry-run the rework before committing: simulate the routing impact via `routing_cli.py --action find_path` (no commit) and verify no new collisions. If new CRITICAL appears post-commit, do NOT advance the iteration counter — treat as a fresh attempt with narrower scope. |
| 4 | **Early escalation** | `iterative-refinement-skill` returns `escalate` on iteration 1 with only MINOR issues | Require `N >= 2` for escalation in the normal case. Only allow iteration-1 escalation if `confidence < 0.3` (collapse case: agent has no idea what it's looking at). Otherwise, force `rework`. |
| 5 | **Local optimum trap** | Rework scope contains MINOR issues while CRITICAL issues remain in the critique's issue list | Triage filter: when CRITICAL exists, `rework_scope` MUST be CRITICAL → MAJOR only. Skip MINOR entirely. Re-run critique after CRITICAL fix to see if MAJORs / MINORs cleared as side-effects. |

---

## Decision Tree (when to invoke which skill)

This skill is the routing decision for the critique stack. Given the current state of the loop, which of the 3 critique skills (or escalation tool) is the right next call?

```
                  ┌────────────────────────────────────────────────────┐
                  │  State: just finished a checkpoint's actions       │
                  └────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
                  ┌────────────────────────────────────────────────────┐
                  │ INVOKE: visual-review-skill.md                     │
                  │ Produces: JSON critique                            │
                  └────────────────────┬───────────────────────────────┘
                                       │
                                       ▼
                  ┌────────────────────────────────────────────────────┐
                  │ INVOKE: self-critique-skill.md (THIS skill)        │
                  │ Checks: rubber-stamping, posture sanity            │
                  └────────────────────┬───────────────────────────────┘
                                       │
                  ┌────────────────────┴────────────────────────────┐
                  │  If anti-pattern detected (any of the 5)        │
                  │      → Apply mitigation from table above        │
                  │      → Re-invoke visual-review-skill if needed  │
                  │  If posture is clean:                           │
                  │      → Pass critique to iterative-refinement    │
                  └────────────────────┬────────────────────────────┘
                                       │
                                       ▼
                  ┌────────────────────────────────────────────────────┐
                  │ INVOKE: iterative-refinement-skill.md              │
                  │ Decides: proceed | rework | escalate               │
                  └────────────────────┬───────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
       ┌─────────────┐         ┌─────────────┐          ┌─────────────────┐
       │  PROCEED    │         │  REWORK     │          │  ESCALATE       │
       │             │         │             │          │                 │
       │ → next      │         │ → apply     │          │ → INVOKE        │
       │   checkpoint│         │   rework,   │          │   self-critique │
       │             │         │   iter += 1 │          │   AGAIN to      │
       │             │         │ → loop      │          │   verify it's   │
       │             │         │   restart   │          │   not early-esc │
       │             │         │             │          │ → AskUserQuestion│
       └─────────────┘         └─────────────┘          └─────────────────┘
```

**Important cross-reference rule:** before any `AskUserQuestion` invocation, re-invoke this skill to verify the escalation is genuine. If self-critique flags `early escalation` (anti-pattern 4), abort the escalation and force `rework` instead.

---

## Convergence Tracking

Track these metrics per checkpoint, written to the journal after every iteration. They are the data behind anti-pattern detection.

| Metric | Type | Direction | Anti-pattern flagged on |
|--------|------|-----------|--------------------------|
| `iteration_depth` | int (1-3) | Capped at 3 | iter > 3 → ceiling violation |
| `issue_count_trajectory` | list[int] | Monotonically ↓ | Reversal (count goes up) → over-correction |
| `confidence_trajectory` | list[float] | Monotonically ↑ | Reversal (confidence drops) → over-correction or thrashing |
| `modifications_applied` | dict[net, int] | Bounded per net | Net count ≥ 3 → thrashing |
| `new_issues_introduced` | int (per iter) | Should be 0 | ≥1 new CRITICAL → over-correction |
| `same_issue_repeat_count` | int | Bounded at 3 | Same issue repeats 3x → thrashing or stuck-loop |
| `tokens_per_cycle` | int | Bounded at ~12K | > 15K → token explosion (scope too broad) |

Journal schema (cross-references the trajectory data):

```json
{
  "checkpoint": "critical_passive_placement",
  "iterations": [
    {
      "n": 1,
      "confidence": 0.62,
      "issue_count": 4,
      "issues_critical": 1,
      "issues_major": 2,
      "issues_minor": 1,
      "decision": "rework",
      "rework_scope": ["C2 too far from U1.8", "R3 silk overlap"],
      "tokens_used": 11400
    },
    {
      "n": 2,
      "confidence": 0.81,
      "issue_count": 1,
      "issues_critical": 0,
      "issues_major": 0,
      "issues_minor": 1,
      "decision": "rework",
      "rework_scope": ["R3 silk offset by 0.3 mm"],
      "tokens_used": 9800
    },
    {
      "n": 3,
      "confidence": 0.91,
      "issue_count": 0,
      "decision": "proceed",
      "tokens_used": 4200
    }
  ],
  "trajectory_health": "monotonic-good",
  "modifications_per_net": {"VCC": 0, "GND": 0, "USB_D+": 0},
  "outcome": "proceed"
}
```

**Trajectory health values:**

- `"monotonic-good"` — both issue count ↓ and confidence ↑ throughout
- `"plateau"` — no improvement between iter N and N+1 (warning, not failure)
- `"reversal"` — any reversal → escalate immediately (anti-pattern flag fires)

---

## Guard Rails: When to Abort

Hard stops. If any of these triggers, do not advance the loop — escalate to `AskUserQuestion` or abort the checkpoint.

1. **`iteration_depth >= 3` AND issues still present.** Max 3 iterations is firm. No iteration 4.
2. **`confidence < 0.4` on iteration 2.** Below the 0.5 escalation threshold even with one iteration's growth → agent does not know what's wrong, human needed.
3. **Same issue (by `failure_mode_id` + `location.ref`) appears 3 consecutive iterations.** Stuck-loop signal.
4. **Token budget exhausted.** Aggregate tokens for this checkpoint > 40K (3 cycles × ~12K + buffer). Per-cycle ceiling is 15K (anti-pattern 3, token explosion).
5. **New CRITICAL count ≥ 2 in a single iteration's delta.** Catastrophic over-correction. The rework made things substantially worse.
6. **Oscillation: same net modified 3+ times.** Thrashing signal (anti-pattern 2).
7. **Contract ambiguity surfaces.** If the critique cannot be resolved because the contract is silent on the rule being violated, abort to `AskUserQuestion` with `escalation_reason: "contract ambiguity"`.

---

## Per-Checkpoint Exit Criteria

Each of the 8 checkpoints has an explicit confidence threshold and a set of `pass_criteria` items that must all be `true` before advancing. These are the entry/exit criteria used by `pcb-design-skill.md`'s state machine; this skill enforces them.

| # | Checkpoint | Required confidence | Required pass_criteria |
|---|---|---|---|
| 1 | **board_outline** | ≥ 0.85 | outline closed; dimensions match contract within ±0.1 mm; cuts layer only (no silk on outline) |
| 2 | **mechanical_placement** | ≥ 0.85 | all non-electrical components placed; ≥ 3 mm edge clearance for mounting holes; connectors at edges with mating face outward |
| 3 | **ic_placement** | ≥ 0.90 | ICs on F.Cu; pin-1 oriented per convention (top-left or marked dot visible); ≥ 1.5 mm clearance to nearest neighbor; no overlap |
| 4 | **critical_passive_placement** | ≥ 0.90 | every decoupling cap within 5 mm of IC power pin; crystal within 5 mm of MCU clock pin; analog filter caps adjacent to VDDA |
| 5 | **remaining_passive_placement** | ≥ 0.85 | all contract components placed; no overlap; pull-ups near pin they service |
| 6 | **power_routing** | ≥ 0.90 | VCC + GND power traces ≥ 0.5 mm; every power pin reached; star topology preferred; ferrite bead on VDDA if specified |
| 7 | **signal_routing** | ≥ 0.85 | all signal nets routed; no unrouted; diff pairs length-matched within 10%; 45° angles only |
| 8 | **ground_zone_and_stitching** | ≥ 0.90 | GND zone on B.Cu covers board; F.Cu remnants filled with GND zone (priority 1); stitching vias on 5 mm grid along perimeter; zero ground plane islands; no plane split under high-speed signals |

A checkpoint advances only when its `pass_criteria` are ALL `true` AND the iteration's `confidence` meets the per-checkpoint threshold. Below threshold → rework (if N < 3) or escalate.

---

## Required Reading

- [`agent_docs/skills/visual-review-skill.md`](visual-review-skill.md) — produces the critique JSON this skill audits
- [`agent_docs/skills/iterative-refinement-skill.md`](iterative-refinement-skill.md) — receives the critique after self-critique passes it through
- `agent_docs/skills/pcb-design-skill.md` — holds the 8-checkpoint state machine
- `research/self_critique_patterns_research.md` — the source for the 5 anti-patterns and convergence numbers

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Five anti-patterns | **Rubber-stamping, Thrashing, Over-correction, Early escalation, Local optimum trap** |
| Eight checkpoints | board_outline, mechanical_placement, ic_placement, critical_passive_placement, remaining_passive_placement, power_routing, signal_routing, ground_zone_and_stitching |
| Convergence rule | issue count ↓ AND confidence ↑ across iterations (any reversal → escalate) |
| Max iterations | 3 (firm; see iterative-refinement-skill) |
| Escalation threshold | confidence < 0.5 after iter 2; or iter ≥ 3 with issues; or oscillation |
| Proceed threshold | confidence ≥ 0.85 AND pass_criteria all true AND pass_fail == "pass" |
| Stuck-loop threshold | same issue repeats 3 consecutive iterations |
| Token explosion threshold | cycle > 15K tokens (target: ~12K) |
