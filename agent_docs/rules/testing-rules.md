# Testing Rules

## Milestone-Driven Development
- Every board design MUST include comprehensive `pytest` tests.
- Tests are THE ultimate milestone. A task is NOT complete until all tests pass.
- Tests must cover:
  - Board structure and dimensions.
  - Component existence and placement.
  - Netlist connectivity.
  - DRC compliance.

## Test Infrastructure
- Utilize the shared fixtures provided in `tests/conftest.py`:
  - `tmp_board_dir`: For temporary file operations.
  - `load_board`: Safely loads the `.kicad_pcb` file.
  - `run_drc`: Wrapper for executing `kicad-cli pcb drc`.
  - `assert_component_exists`: To verify component references.
  - `assert_net_connected`: To verify pad-to-net assignments.

## Strict Rules
- **NEVER edit tests to make them pass.** You must fix the implementation code to satisfy the tests.
- Run tests using the environment and interpreter specified in `config.json`.
