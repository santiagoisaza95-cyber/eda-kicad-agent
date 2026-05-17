# /review-board {name}

## Description
Orchestrates the 3-agent adversarial review pipeline for a given board as the **OPTIONAL FINAL ADVERSARIAL PASS** after a full audition completes.

## Role in v2

**Pre-v2 (v1):** This was the primary review entrypoint. Run after a full build to catch issues.

**v2 role:** OPTIONAL FINAL ADVERSARIAL PASS. Runs only AFTER a complete audition (`agent_docs/skills/pcb-design-skill.md` completed all 8 checkpoints + 3 milestones approved by owner). Inline reviewer gates at checkpoints 4 + 6 (per `agent_docs/skills/pcb-design-skill.md`) catch in-build issues. `/review-board` runs the FULL 3-agent pipeline (design-reviewer → design-defender → design-referee) on the COMPLETED board for a one-off red-team pass.

This command is NOT for in-build checkpoints. The Stage 2 inline `design-reviewer` gates at checkpoints 4 + 6 handle in-build catches. Use `/review-board` only for a final adversarial sweep on the completed, owner-approved board.

## Preconditions (HARD REFUSE if any missing)

Before invoking any subagent, verify ALL of the following preconditions:

- `output/{name}.kicad_pcb` must exist (the audition produced a completed board)
- `output/{name}_full.png` must exist (the audition rendered the final full-board PNG)
- `output/{name}_journal.md` must exist (the audition wrote a Reflexion journal — the reviewer reads it for context)

If any precondition is missing, REFUSE to run with a message like:

> "Cannot run `/review-board {name}` — the audition has not produced the required artifacts. Missing: `output/{name}.kicad_pcb` and/or `output/{name}_full.png` and/or `output/{name}_journal.md`. Complete the audition first (run `pcb-design-skill.md` through all 8 checkpoints), then re-invoke `/review-board {name}`."

## Workflow
1. Verify all 3 Preconditions above. If any missing, REFUSE.
2. Invoke the **Design Reviewer** agent (`.claude/agents/design-reviewer.md`, unchanged from v1) to evaluate the board. The reviewer reads the board + `output/{name}_full.png` + `output/{name}_journal.md`, and writes structured findings to `review/{name}_review.md`.
3. Invoke the **Design Defender** agent (`.claude/agents/design-defender.md`, unchanged from v1) to read `review/{name}_review.md` and write its defense to `review/{name}_defense.md`.
4. Invoke the **Design Referee** agent (`.claude/agents/design-referee.md`, unchanged from v1) to read both the review and defense, and write the final verdict + action items to `review/{name}_verdict.md`.
5. Present the final action items from `review/{name}_verdict.md` directly to the user.
6. The result should be referenced in `docs/auditions/{name}_run<N>.md` (the audition run log).

## Outputs

3 files in the `review/` directory:

| File | Producer | Contents |
|------|----------|----------|
| `review/{name}_review.md` | design-reviewer | Adversarial findings against the completed board |
| `review/{name}_defense.md` | design-defender | Defense / rebuttal of the reviewer's findings |
| `review/{name}_verdict.md` | design-referee | Final judgment + action items |

The verdict + action items are surfaced into the audition run log at `docs/auditions/{name}_run<N>.md`.

## Subagent References (Preserved from v1)

- `.claude/agents/design-reviewer.md` — unchanged
- `.claude/agents/design-defender.md` — unchanged
- `.claude/agents/design-referee.md` — unchanged

Only the *invocation pattern* changes in v2: the inline reviewer gates at checkpoints 4 + 6 (in `pcb-design-skill.md`) invoke `design-reviewer` during the build; `/review-board` invokes the full 3-agent pipeline AFTER the build completes.
