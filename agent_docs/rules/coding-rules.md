# Coding Rules for KiCad EDA Agent

## Python Standards
- Python 3.11+
- Use strict type hints for all function signatures and variables.
- No wildcard imports (`from module import *`).
- Robust error handling: Wrap API calls in `try...except` blocks where appropriate and log meaningful errors.
- Naming conventions: Use `snake_case` for variables and functions, `PascalCase` for classes.
- Follow PEP 8 guidelines.

## KiCad API Integration
- **Execution Environment:** ALWAYS run scripts using the correct Python interpreter specified in `config.json` (e.g., `kipython` on Windows).
- **API Verification:** Before using ANY `pcbnew` function, verify that it exists in `api_manifest.json`. Do not assume API functions from older versions still exist in KiCad 9.x.

## Completion Checklist
Before marking a coding task as complete, perform the following self-checks:
- [ ] Code is fully typed and correctly formatted.
- [ ] All required imports are explicitly declared.
- [ ] Code executes successfully with the designated interpreter (e.g., `kipython`).
- [ ] `api_manifest.json` was checked for any KiCad API calls made.
