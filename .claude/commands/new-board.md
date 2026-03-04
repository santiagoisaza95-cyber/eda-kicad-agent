# /new-board

## Description
Interactive command to create a new board contract and its test stubs simultaneously.

## Workflow
1. Ask the user for the board name, dimensions, layers, components, and nets.
2. Generate BOTH the contract markdown file in `contracts/{board_name}_contract.md` AND the pytest test file in `tests/test_{board_name}.py`.
3. Ensure the test file and the contract share the exact same component list and net list.

The test file should contain basic stubs like:
- `test_board_dimensions()`
- `test_component_count()`
- `test_net_connectivity()`
- `test_drc_passes()`