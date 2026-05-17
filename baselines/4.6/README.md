# Baselines: 4.6 (Blue Pill, Round 2)

## What these are

Round 2 build output from Opus 4.6 — the Blue Pill STM32 board produced during
the v1 era. These files are frozen historical record from **2026-03-06**.

## Provenance

- **Produced by:** `build_blue_pill.py` + `route_blue_pill.py` running under
  Opus 4.6.
- **Date frozen:** 2026-03-06
- **Commit at time of freeze:** `4787d57 — "feat: Blue Pill STM32 board — 54/54 tests passing"`
- **Workflow:** 4.6 wrote board-specific scripts, ran them, iterated until tests + DRC went green.

## Files manifest

| File | What it is |
|---|---|
| `build_blue_pill.py` | 4.6's hardcoded builder for the Blue Pill board (~370 LOC) |
| `route_blue_pill.py` | 4.6's hardcoded router for the Blue Pill (~390 LOC, explicit waypoints) |
| `blue_pill.kicad_pcb` | The Round 2 PCB artifact, DRC-clean |
| `blue_pill.kicad_pro` | KiCad project file |
| `blue_pill.kicad_prl` | KiCad local project state |

## Test status at time of freeze

`pytest tests/test_blue_pill.py` reported **54/54 tests passing** at commit `4787d57`.

## DRC at time of freeze

`drc_report.json` showed **0/0** (zero errors, zero unconnected items) — clean.

## Owner's verdict

Goal **NOT achieved** — owner-judged **goal-failed** despite the green
numbers. The board passed the contract checklist mechanically, but owner
inspection determined the visual layout was not credible — components placed
in a flat row with right-angle traces, no hierarchical grouping, no visual
coherence. Owner suspects 4.6's visual reasoning was the bottleneck:
contract-driven design without a render-and-look loop produced "tests-pass"
output that an experienced PCB designer would reject at a glance. This is the
failure that motivated the v2 redesign.

## Used for

**Stage 3 stretch comparison.** v2 retries the Blue Pill and compares the
result visually against this baseline. The baseline is the bar-to-beat for
the v2-vs-4.6 visual comparison stretch test.

## DO NOT MODIFY

These files are immutable historical record. Do **not**:

- Edit `build_blue_pill.py` or `route_blue_pill.py` — they encode 4.6's exact
  output. Modifying them invalidates the comparison.
- Re-run `build_blue_pill.py` or `route_blue_pill.py` against these artifacts —
  doing so replays 4.6's output and overwrites the frozen baseline.
- Open `blue_pill.kicad_pcb` in pcbnew and save it — KiCad may rewrite the
  file, breaking byte-for-byte historical comparison.
- Treat these scripts as templates for v2 work. v2 uses **generic** primitives
  (`routing_cli.py`, `render_board.py`, supplier profiles) — never
  board-specific build/route scripts. That's the architectural change.

If you need a fresh artifact, use the v2 toolchain to produce a new one in
`output/`, not `baselines/4.6/`.
