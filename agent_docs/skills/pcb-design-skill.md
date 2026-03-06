# PCB Design Skill — Ordered Workflow

This skill defines the step-by-step workflow for designing a PCB using the KiCad Python API. Follow this order strictly. Do NOT skip steps.

---

## Prerequisites

Before starting:
1. Read the task contract in `contracts/` — understand all requirements
2. Read `agent_docs/rules/coding-rules.md` — know the coding standards
3. Read `agent_docs/rules/clearance-rules.md` — know the clearance tables
4. Read `agent_docs/skills/kicad-api-skill.md` — know the API patterns
5. Verify `config.json` exists and has valid paths
6. Verify `api_manifest.json` has been generated

---

## Workflow Steps

### Step 1: Read Contract
- Open the contract file for your task
- List every component, net, and design rule
- Note the completion criteria checklist — you must satisfy ALL items

### Step 2: Create Board
```python
import pcbnew
board = pcbnew.BOARD()
```

### Step 3: Set Board Outline
- Draw the board edge on `Edge_Cuts` layer using `PCB_SHAPE`
- Use the exact dimensions from the contract
- See `kicad-api-skill.md` → Board Outline section

### Step 4: Place Components
- Load footprints from KiCad library using the IO class
- Follow the 5-phase placement workflow from `placement-skill.md`:
  1. Mechanicals first (mounting holes, connectors, switches)
  2. ICs (MCU center, regulator near power input)
  3. Critical passives (decoupling caps, crystal, analog filter)
  4. Remaining passives (pull-ups, signal conditioning)
  5. Verify placement clearances
- Set reference designators to match contract exactly
- Verify all contract components are placed
- **Respect all clearance rules from `clearance-rules.md`** — courtyard gaps, board-edge keepout, drill-to-pad clearance

### Step 4b: Pre-Routing DRC (MANDATORY)
- Run DRC AFTER placement, BEFORE routing
- Check for courtyard overlaps, board-edge violations, pad clearance issues
- Fix any violations by adjusting placement
- Do NOT proceed to Step 5 until pre-routing DRC is clean

### Step 5: Define Nets
- Create all nets from the contract netlist using `NETINFO_ITEM`
- At minimum: VCC, GND, and all signal nets listed in the contract

### Step 6: Assign Pads to Nets
- For each component, assign the correct net to each pad
- Cross-reference the contract netlist table
- Double-check power pins (VCC, GND) on every IC

### Step 7: Route Traces (NON-OPTIONAL)
**This step is MANDATORY. A board with 0 traces is a failed board.** Copper zones alone do NOT constitute routing — you must create explicit trace segments between pads.

- Use the **routing workbench CLI** (`scripts/routing_cli.py`) for all routing — see `routing-skill.md` → Routing Workbench section
- Follow the iterative loop: query pads → find path (A*) → route → check DRC → fix/retry
- Follow routing priority from `routing-skill.md`
- After routing, verify the track count is > 0. If you have 0 traces, you skipped this step.

### Step 8: Add Ground Plane
- Create a copper pour zone on B.Cu for GND
- Fill the zone to complete the ground plane
- See `routing-skill.md` → Ground Plane section

### Step 9: Add Silkscreen
- Add board name/version text on F.SilkS
- Verify reference designators are visible and not overlapping

### Step 10: Run DRC (Final)
- Save the board first
- Run DRC per `drc-rules.md`
- Parse the JSON report and check BOTH keys:
  - `violations` must be empty (0 clearance/short errors)
  - `unconnected_items` must be empty (0 missing connections)
- **If unconnected_items > 0:** you have missing traces. Go back to Step 7 and route the missing connections. Each unconnected item tells you exactly which two pads need copper between them.
- Re-run DRC after every fix until both lists are empty

### Step 11: Run Tests
- Execute the pytest test suite for this board
- **ALL tests must pass** — see `testing-rules.md`
- If tests fail, read `test-failing-rules.md` and fix
- NEVER edit tests to make them pass

### Step 12: Save Final Board
- Save to `output/{board_name}.kicad_pcb`
- Run DRC one final time
- Run tests one final time
- Verify all contract checklist items are satisfied

---

## Checkpoints

After each step, verify before moving to the next:

| Step | Checkpoint |
|------|-----------|
| 3 | Board outline matches contract dimensions |
| 4 | Component count matches contract, all clearances met |
| 4b | Pre-routing DRC clean (courtyard overlaps, edge clearance) |
| 6 | Net count matches contract netlist |
| 7 | Trace count > 0, all nets have physical copper connections |
| 10 | DRC: 0 violations AND 0 unconnected items |
| 11 | All pytest tests pass |
| 12 | All contract checklist items checked |

---

## Abort Conditions

STOP and request human review if:
- An API function is missing from `api_manifest.json`
- DRC produces errors you cannot resolve after 3 attempts
- A test fails and you cannot identify the root cause
- The contract requirements are ambiguous or contradictory
