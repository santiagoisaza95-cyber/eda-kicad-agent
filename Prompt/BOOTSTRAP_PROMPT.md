## PROMPT — Paste into Claude Code (start in Plan mode: Shift+Tab twice)

---

you are working in reporsitory `eda-kicad-agent`.

This repository is a complete EDA (Electronic Design Automation) project that automates KiCad 9.x PCB design using Claude Code, Python, and the KiCad pcbnew SWIG API.

The architecture is:
```
Engineer → Claude Code (Opus 4.6) → Python → KiCad Python API (pcbnew) → KiCad 9.x
```

The project has two phases: install the toolchain, then build the agent architecture. Do both in order.

---

## PHASE 1: Toolchain Installation

### Step 1: Install KiCad 9.x

Detect my OS and install KiCad 9 stable:

- **Linux (Ubuntu/Debian):** `sudo add-apt-repository ppa:kicad/kicad-9.0-releases && sudo apt update && sudo apt install kicad`
- **macOS:** `brew install --cask kicad`
- **Windows:** Tell me to download from https://www.kicad.org/download/windows/ and come back.

Verify: `kicad-cli version`

### Step 2: Set up Python with pcbnew access

The critical piece is getting Python to `import pcbnew` headlessly (outside the KiCad GUI).

- **Linux** — pcbnew installs to system dist-packages automatically. Test: `python3 -c "import pcbnew; print(pcbnew.Version())"`
- **macOS/Windows** — needs kigadgets for headless access:
  ```bash
  pip install kigadgets
  python -m kigadgets
  kipython -c "import pcbnew; print(pcbnew.Version())"
  ```

Also install:
```bash
pip install kicad-python pytest
```

### Step 3: Detect footprint library path

Run: `find / -name "Package_QFP.pretty" -type d 2>/dev/null | head -1`

Save the result — it goes into the agent skills config.

### Step 4: Create a verification script at `scripts/verify_toolchain.py`

This script checks everything works: Python 3.11+, kicad-cli found, `import pcbnew` succeeds, pytest installed, footprint libraries located. Print a clear pass/fail summary. Run it and show me the output.

### Step 5: Configure Opus 4.6

Check model with `claude config get model`. If not opus, set it with `claude model opus`.

---

## PHASE 2: Agent Architecture

Inside the `eda-kicad-agent` repo, create this exact file tree:

```
eda-kicad-agent/
├── CLAUDE.md
├── README.md
├── .gitignore
├── requirements.txt
├── scripts/
│   └── verify_toolchain.py
├── .claude/
│   ├── agents/
│   │   ├── api-researcher.md
│   │   ├── design-reviewer.md
│   │   ├── design-defender.md
│   │   └── design-referee.md
│   └── commands/
│       ├── new-board.md
│       ├── review-board.md
│       └── research-api.md
├── agent_docs/
│   ├── rules/
│   │   ├── coding-rules.md
│   │   ├── drc-rules.md
│   │   ├── testing-rules.md
│   │   └── test-failing-rules.md
│   └── skills/
│       ├── kicad-api-skill.md
│       ├── pcb-design-skill.md
│       ├── placement-skill.md
│       └── routing-skill.md
├── contracts/
│   └── EXAMPLE_CONTRACT.md
├── tests/
├── output/
├── research/
└── review/
```

### File contents — follow these principles strictly:

**1. CLAUDE.md — THIN routing file (max 50 lines)**

This is ONLY an IF-ELSE directory. Zero implementation details. Zero API code. Just:
- A "First Rule" that says: after every compaction, re-read your task plan and relevant source files. Never assume or fill in gaps.
- Routing logic: "if designing a PCB → read agent_docs/skills/pcb-design-skill.md", "if placing components → read placement-skill.md", "if working with KiCad API → read kicad-api-skill.md", "if routing traces → read routing-skill.md", "if running DRC → read rules/drc-rules.md", "if writing tests → read rules/testing-rules.md", "if tests failing → read rules/test-failing-rules.md", "before ANY coding → read rules/coding-rules.md".
- A note that every task needs a contract in `contracts/` and the agent cannot terminate until all contract items are fulfilled.

**2. Rules (agent_docs/rules/) — encode preferences**

- `coding-rules.md` — Python 3.11+, type hints, no wildcard imports, error handling, naming conventions, self-check checklist before marking complete.
- `drc-rules.md` — always run DRC before saving, 0 errors required, how to run DRC via kicad-cli (`kicad-cli pcb drc --output report.json board.kicad_pcb`), what to do if DRC fails.
- `testing-rules.md` — every board needs pytest tests (structure, components, nets, DRC). Tests are THE milestone. Task is NOT complete until all pass. NEVER edit tests to make them pass.
- `test-failing-rules.md` — read the error, re-read source files, isolate the failing test, fix the implementation NOT the test, run full suite after.

**3. Skills (agent_docs/skills/) — encode recipes**

- `kicad-api-skill.md` — KiCad 9.x pcbnew SWIG patterns: BOARD(), LoadBoard, SaveBoard, FromMM/ToMM, footprint loading via PCB_IO_KICAD_SEXPR, NETINFO_ITEM for nets, pad.SetNet, PCB_TRACK for traces, PCB_SHAPE on Edge_Cuts for board outline, PCB_TEXT on F_SilkS for silkscreen. Use the ACTUAL footprint library path detected in Phase 1. Mark every snippet: "verify against your KiCad 9 installation — SWIG names change between versions." Include a CRITICAL rule: if unsure about any API function, STOP and use the /research-api command before implementing.
- `pcb-design-skill.md` — ordered workflow: read contract → create board → set outline → place components → define nets → assign pads → route traces → add silkscreen → run DRC → run tests → save.
- `placement-skill.md` — placement order (MCU first, decoupling caps near IC power pins, crystal near clock pins, connectors at edges, passives grouped by function). Coordinate system: origin top-left, X right, Y down, all mm, 0.5mm grid.
- `routing-skill.md` — priority: power first, clocks, then signals. Trace width table (0.25mm signal, 0.5mm power, 1.0mm high current). Via rules. Ground plane strategy for 2-layer boards (B.Cu copper pour).

**4. Contracts (contracts/) — define task completion**

`EXAMPLE_CONTRACT.md` — template for a "Simple MCU Board v1.0": 50×40mm, 2-layer, STM32 in TQFP-32_7x7mm_P0.8mm, 2× bypass caps (C_0402), pull-up resistor (R_0402), USB Micro-B connector, 8MHz crystal. Include: components table (ref/component/footprint/position), netlist table (VCC, GND, NRST, USB_DP, USB_DM, OSC_IN, OSC_OUT), design rules, and a completion criteria checklist with checkboxes for structure, components, connectivity, routing, quality (DRC passes), and tests (all pytest pass). Note at top: "You are NOT allowed to terminate this session until ALL items are fulfilled."

**5. Subagents (.claude/agents/) — adversarial review pattern**

- `api-researcher.md` — RESEARCH ONLY. Tools: Read, Grep, Glob, Bash, WebFetch, WebSearch. Cannot write implementation code. Outputs to `research/`. Job: verify KiCad API functions exist before anyone uses them.
- `design-reviewer.md` — aggressive bug finder. Scoring: +1 cosmetic, +5 design, +10 critical. Reviews structure, components, connectivity, routing, manufacturing. Outputs issues to `review/`.
- `design-defender.md` — tries to DISPROVE each bug. Earns bug's score for successful disproves, loses 2× for wrong disproves. Outputs defense to `review/`.
- `design-referee.md` — judges reviewer vs defender. Tell it: "I have the actual ground truth — +1 per correct judgment, -1 per incorrect." Outputs final verdict with action items to `review/`.

**6. Slash commands (.claude/commands/)**

- `/new-board` — interactive contract creation. Asks for board name, dimensions, layers, components, nets. Generates contract AND pytest test stubs in `tests/`.
- `/review-board {name}` — runs 3-agent pipeline: reviewer → defender → referee. Presents final action items.
- `/research-api {topic}` — delegates to api-researcher. Research only, zero implementation.

**7. Other files**

- `.gitignore` — `output/*.kicad_pcb`, `output/*.kicad_sch`, `research/`, `review/`, `__pycache__/`, `*.pyc`, `.env`, `*.bak`
- `requirements.txt` — `pytest>=7.0`, `kicad-python>=0.5.0`, `kigadgets>=0.5.0`
- `README.md` — architecture diagram (ASCII art: Engineer → Claude Code/Opus 4.6 → Python → KiCad Python API → KiCad 9.x), toolchain setup reference, slash command usage, project structure with descriptions, and a "Design Philosophy" section mapping principles to the article "How To Be A World-Class Agentic Engineer" by systematicls.

---

