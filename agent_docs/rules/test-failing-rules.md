# Test Failure Remediation Rules

When a `pytest` suite fails, follow this strict diagnostic flowchart:

1. **Read the Error:** Carefully analyze the traceback and the specific assertion that failed.
2. **Re-Read Source:** Look at both the test file and your implementation code.
3. **Check API Manifest:** If the failure involves an API call error (e.g., `AttributeError`), immediately check `api_manifest.json` before assuming any function exists. SWIG bindings change between versions.
4. **Isolate:** Run the failing test individually to isolate the issue.
5. **Fix Implementation:** Modify the design code (Python PCB script), **NOT the test**. Remember the core rule: tests are immutable milestones.
6. **Verify:** Run the full test suite again to ensure the fix didn't introduce regressions.
