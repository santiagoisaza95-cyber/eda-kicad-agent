# CLAUDE.md — Agent Router

## First Rule
After every compaction event, STOP. Re-read your current task plan and the relevant source files listed below. Never assume context — always re-read.

## Before ANY Coding
Read `agent_docs/rules/coding-rules.md` first. No exceptions.

## Machine Config
Read `config.json` for interpreter path, footprint library path, and KiCad version. Never hardcode machine-specific paths.

## Task Routing

| If you are...                  | Read this file                              |
|--------------------------------|---------------------------------------------|
| Designing a PCB                | `agent_docs/skills/pcb-design-skill.md`     |
| Placing components             | `agent_docs/skills/placement-skill.md`      |
| Working with KiCad API         | `agent_docs/skills/kicad-api-skill.md`      |
| Routing traces                 | `agent_docs/skills/routing-skill.md`        |
| Running DRC                    | `agent_docs/rules/drc-rules.md`             |
| Writing tests                  | `agent_docs/rules/testing-rules.md`         |
| Tests are failing              | `agent_docs/rules/test-failing-rules.md`    |
| Unsure about a KiCad API call  | Use `/research-api` command — do NOT guess  |

## Contract Enforcement
Every task MUST have a contract in `contracts/`. You are NOT allowed to terminate the session until ALL contract checklist items are fulfilled. If a checklist item fails, fix it and re-verify.

## API Safety
Before using any pcbnew function, check `api_manifest.json`. If the function is listed as missing or unverified, use `/research-api` to confirm before proceeding.
