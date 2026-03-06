# CLAUDE.md — Agent Router

## GATE 0: MCP Server Check (MANDATORY)
Before doing ANY work, run this command:
```
python scripts/verify_mcp.py
```
If it exits with code 1 (MCP NOT READY), you MUST:
1. **STOP all work immediately**
2. Tell the user: "The KiCAD MCP Server is not installed or not working. Run `python scripts/setup_mcp.py` to install it, then restart Claude Code."
3. Do NOT proceed with any PCB design task until the MCP check passes

If it exits with code 0 (MCP READY), proceed normally.

## First Rule
After every compaction event, STOP. Re-read your current task plan and the relevant source files listed below. Never assume context — always re-read.

## Before ANY Coding
Read `agent_docs/rules/coding-rules.md` first. No exceptions.

## Machine Config
Read `config.json` for interpreter path, footprint library path, and KiCad version. Never hardcode machine-specific paths.

## KiCAD MCP Server
This project integrates the [mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server) as an MCP tool provider. When the MCP is active, you have access to 60+ KiCad tools for project management, component placement, DRC, schematic design, JLCPCB parts search, and Gerber export.

**MCP BYPASS FOR ROUTING:** Do NOT use MCP `route_trace`, `route_pad_to_pad`, or `route_differential_pair` tools. They create only single straight-line segments with no pathfinding or clearance checks. For all trace routing, via placement, and zone creation, use **direct pcbnew SWIG API** via Python scripts. See `routing-skill.md` for details.

Use MCP for: placement, DRC, export, library search, JLCPCB | Bypass MCP for: routing, vias, zones

Setup: `python scripts/setup_mcp.py` | Verify: `python scripts/verify_mcp.py`

## Task Routing

| If you are...                  | Read this file                              |
|--------------------------------|---------------------------------------------|
| Designing a PCB                | `agent_docs/skills/pcb-design-skill.md`     |
| Placing components             | `agent_docs/skills/placement-skill.md`      |
| Checking clearances            | `agent_docs/rules/clearance-rules.md`       |
| Working with KiCad API         | `agent_docs/skills/kicad-api-skill.md`      |
| Routing traces                 | `agent_docs/skills/routing-skill.md`        |
| Routing traces interactively      | `scripts/routing_cli.py` (see routing-skill.md) |
| Running DRC                    | `agent_docs/rules/drc-rules.md`             |
| Writing tests                  | `agent_docs/rules/testing-rules.md`         |
| Tests are failing              | `agent_docs/rules/test-failing-rules.md`    |
| Unsure about a KiCad API call  | Use `/research-api` command — do NOT guess  |

## Contract Enforcement
Every task MUST have a contract in `contracts/`. You are NOT allowed to terminate the session until ALL contract checklist items are fulfilled. If a checklist item fails, fix it and re-verify.

## No External References (when contract says so)
If a contract contains a "DESIGN FROM THIS CONTRACT ONLY" constraint, you MUST NOT use WebSearch, WebFetch, or read any files in the `reference/` directory. Design entirely from the contract + skills + rules + api_manifest. This tests whether the infrastructure works without crutches.

## API Safety
Before using any pcbnew function, check `api_manifest.json`. If the function is listed as missing or unverified, use `/research-api` to confirm before proceeding.
