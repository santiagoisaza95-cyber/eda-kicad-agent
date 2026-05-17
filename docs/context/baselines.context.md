# Context: baselines/

## Module boundary

`baselines/` is the read-only archive of historical agent output preserved
across redesigns. It is **not** active infrastructure — nothing in v2's runtime
imports from `baselines/`. The directory exists so that future stages can
compare new output against frozen historical artifacts.

Each subdirectory corresponds to a model/era snapshot: `baselines/4.6/` is the
Opus 4.6 Round 2 output preserved at the v1 → v2 transition.

## What's here

`baselines/4.6/` contains:

- The two board-specific scripts 4.6 wrote (`build_blue_pill.py`,
  `route_blue_pill.py`)
- The Round 2 Blue Pill artifacts (`blue_pill.kicad_pcb`, `.kicad_pro`,
  `.kicad_prl`)
- `README.md` documenting provenance (2026-03-06, Opus 4.6, 54/54 tests passing,
  owner-judged goal-failed) — see `baselines/4.6/README.md` for the full
  narrative.

## What's NOT here

- Any v1 generic infra (routing_cli, routing/, MCP server, agent_docs,
  api_manifest) — those survive unchanged in their original locations.
- Any test files — `tests/test_blue_pill.py` stays in `tests/` because it is
  used as the Stage 3 stretch-test finish-line check.
- Any contracts — `contracts/blue_pill_contract.md` stays in `contracts/` for
  the same reason.

The split is: **what v2 still uses → stays put. What v2 demotes to historical
record → moves to `baselines/`.**

## When consumers read these files

- **Stage 3 stretch comparison.** When v2 retries the Blue Pill, the audition
  agent renders `baselines/4.6/blue_pill.kicad_pcb` via
  `scripts/render_board.py` and presents it side-by-side with the new v2
  output for the owner's visual verdict.
- **Architectural reference.** When deciding whether v2 has drifted toward
  board-specific scripts, compare against `build_blue_pill.py` /
  `route_blue_pill.py` as the cautionary example of what NOT to produce.

## What this module does NOT do

- Does not export functions. Nothing imports from `baselines/`.
- Does not run. The scripts in `baselines/4.6/` are frozen — they execute, but
  doing so replays 4.6's output and is explicitly forbidden by the README.
- Does not get extended. New baselines go into new dated subdirectories
  (e.g. `baselines/v2.0/` after Stage 3 completes), never into existing ones.

## Cross-references

- `baselines/4.6/README.md` — full provenance and DO-NOT-MODIFY clause
- `architecture_v2_proposal.md` § "What Gets Demoted" — rationale for the move
- `contracts/v2-stage-3-audition.contract.md` — Stage 3 stretch test that consumes the baseline
