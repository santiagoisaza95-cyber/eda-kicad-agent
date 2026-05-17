# Context: Routing Primitives (v1 survivors)

## Module boundary

The routing-primitives subsystem is the **mandatory** v2 path for all trace,
via, and zone work. It is preserved unchanged from v1 because it already
encodes two properties v2 cannot give up: (1) an A* iterative pathfinder with
proper clearance checks, and (2) a 45°-only bend validator. The KiCad MCP
server has nominally-equivalent tools, but they are BANNED in v2 (see "Hard
rule" below).

## What survives unchanged from v1

| File | What it is | LOC |
|---|---|---|
| `scripts/routing_cli.py` | A* iterative router with JSON I/O. **The MANDATORY routing primitive for v2.** Reads a JSON request (board path + net name + endpoints + clearance), runs the pathfinder, calls RouteActions, returns a JSON result. | ~250 |
| `scripts/routing/actions.py` | `RouteActions` class — add_trace, add_via, add_zone, fill_zones, undo_last, run_drc, save_board. Also exports `validate_trace_angles()` which enforces the **45°-only** rule (rejects 90° bends explicitly). | ~274 |
| `scripts/routing/perception.py` | `BoardPerception` class — get_board_summary, get_unrouted_nets, get_net_pads, get_obstacles_in_region, get_routed_net_summary. Visual-review-skill will build on this in v2. | ~206 |
| `scripts/routing/pathfinder.py` | A* pathfinder with `Grid` + `Obstacle` types, mm/cell conversion, clearance inflation. **No pcbnew dependency** (pure Python) — runs anywhere. | ~233 |
| `scripts/routing/__init__.py` | Empty package marker. | 0 |

## Hard rule: MCP routing tools are BANNED

The following KiCAD MCP Server tools are **forbidden** in v2:

- `route_trace`
- `route_pad_to_pad`
- `route_differential_pair`

**Why**: They create single straight-line segments with no pathfinding, no
clearance checks, no 45° validation. They produce output that passes the
nominal "trace exists" check but fails any real DRC or visual review.

**Always use** `scripts/routing_cli.py` instead. The CLI is the only routing
path that runs A* pathfinding, applies clearance constraints, validates 45°
bends, and reports DRC feedback per action. This is non-negotiable.

For non-routing work, the rest of the MCP server (60+ tools for placement,
DRC, export, library search, JLCPCB part lookup) is unrestricted.

## 45°-only validation

`validate_trace_angles(points) -> (bool, message)` lives in
`scripts/routing/actions.py`. It walks the waypoint list and rejects any
bend that:

1. Is not within ~2° of a multiple of 45° (5°, 30°, 60°, etc. → rejected)
2. Is specifically 90° (88°–92° window → explicitly rejected even though
   90° is technically a 45° multiple)

The rule encodes the PCB design convention that 90° bends cause acid-trap
manufacturing defects and visually look amateur. v2 inherits this rule
unchanged.

## When consumers use these primitives

- **Routing skill workflow** (`agent_docs/skills/routing-skill.md`, unchanged
  from v1) — the authoritative operational doc. Build the JSON request,
  invoke `scripts/routing_cli.py`, parse the JSON response, iterate.
- **Audition agents** (v2 Stage 2 / 3) — call routing_cli.py one net at a
  time. Never write a large board-specific routing script (that's the
  anti-pattern `baselines/4.6/route_blue_pill.py` represents).
- **Visual review** (v2 Stage 2) — uses `BoardPerception` to enumerate
  unrouted nets, get pad positions, identify obstacles in a region for
  reasoning about layout.

## Cross-references

- **Authoritative workflow doc:** `agent_docs/skills/routing-skill.md`
  (unchanged from v1) — operational source of truth for routing.
- **CLAUDE.md routing rules** — duplicates the "MCP routing BANNED" rule at
  the agent-router level so every session reads it before doing PCB work.
- **Cautionary example:** `baselines/4.6/route_blue_pill.py` —
  board-specific routing script v2 must NOT produce.
- **Hard rule files:** `agent_docs/rules/clearance-rules.md`,
  `agent_docs/rules/drc-rules.md` — clearance and DRC constraints the
  router enforces.
