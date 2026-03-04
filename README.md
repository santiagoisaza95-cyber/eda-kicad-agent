# EDA KiCad Agent

Automated KiCad 9.x PCB design using Claude Code, Python, and the KiCad pcbnew SWIG API.

## Architecture

```text
Engineer → Claude Code (Opus 4.6) → Python → KiCad Python API (pcbnew) → KiCad 9.x
```

## Toolchain Setup

This project uses a specific setup for Windows to bridge system Python and KiCad's internal Python environment. 

1. Install KiCad 9.x from [kicad.org](https://www.kicad.org/download/windows/).
2. Create a Python virtual environment: `python -m venv .venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt` (includes `pytest`, `kigadgets`, `kicad-python`).
4. Run the verification script: `python scripts/verify_toolchain.py`.

*Note for Linux/macOS users: The paths in `config.json` will need to be adjusted for your system. `kicad-cli` and `pcbnew` are typically available in system paths.*

## Slash Commands Reference

| Command | Description |
|---|---|
| `/new-board` | Interactive contract creation. Generates contract and pytest test stubs. |
| `/review-board {name}` | Orchestrates the 3-agent review pipeline (reviewer → defender → referee) on a design. |
| `/research-api {topic}` | Delegates to the `api-researcher` agent for read-only exploration of the pcbnew API. |

## Project Structure

| Path | Description |
|---|---|
| `CLAUDE.md` | Primary agent routing directory. |
| `config.json` | Local machine-specific paths and interpreter configuration. |
| `api_manifest.json` | Verified KiCad 9.x SWIG API surface. |
| `.claude/` | Subagent definitions and slash commands. |
| `agent_docs/` | System rules and PCB design skills. |
| `contracts/` | Project completion criteria and design contracts. |
| `scripts/` | Toolchain verification and environment scaffolding. |
| `tests/` | pytest infrastructure (`conftest.py`) and design tests. |

## Design Philosophy

This agent follows the strict principles of "How To Be A World-Class Agentic Engineer":
- **Contract-Driven**: A design is not complete until every item in the contract is verified. Tests are milestones.
- **Adversarial Review**: Self-correction via a separate Reviewer, Defender, and Referee pipeline.
- **Fact over Assumption**: The KiCad SWIG API changes frequently; this agent validates the actual API surface programmatically before writing skill documentation.
- **Fail Early**: Environment checks and DRC are zero-tolerance gates.
