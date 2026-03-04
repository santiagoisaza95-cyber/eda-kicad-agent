# Design Rule Check (DRC) Rules

## Execution
- Always run a DRC before saving and completing a board.
- The command to run DRC via the KiCad CLI is:
  `kicad-cli pcb drc --output report.json board.kicad_pcb`
- **Note for Windows:** Use the Windows-specific `kicad-cli` path defined in `config.json` if `kicad-cli` is not globally available in the PATH.

## Quality Standards
- **0 Errors Required:** A PCB design is NOT considered complete if there is even a single DRC error.
- All violations must be addressed programmatically in the design script.

## Remediation Steps
If DRC fails:
1. Parse the `report.json` output to identify the failing rules and locations.
2. Cross-reference the failures with the `api_manifest.json` and your routing/placement scripts.
3. Adjust the board layout, trace widths, clearances, or component placement.
4. Re-run the DRC and repeat until `report.json` shows 0 errors.
