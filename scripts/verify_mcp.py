#!/usr/bin/env python3
"""Verify the KiCAD MCP Server is installed and functional.

Exit code 0 = MCP ready, exit code 1 = MCP not ready.
Designed to be called by Claude Code as a gate check.

Run: python scripts/verify_mcp.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = PROJECT_ROOT / "tools" / "KiCAD-MCP-Server"
MCP_JSON = PROJECT_ROOT / ".mcp.json"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

errors: list[str] = []


def check(label: str, condition: bool, fix: str = "") -> bool:
    if condition:
        print(f"  {GREEN}[PASS]{RESET} {label}")
        return True
    msg = f"{label} — FIX: {fix}" if fix else label
    errors.append(msg)
    print(f"  {RED}[FAIL]{RESET} {msg}")
    return False


def main() -> int:
    print(f"\n{BOLD}=== KiCAD MCP Server Verification ==={RESET}\n")

    # 1. Check .mcp.json exists
    check(
        ".mcp.json exists",
        MCP_JSON.exists(),
        "Run: python scripts/setup_mcp.py",
    )

    # 2. Check MCP server directory exists
    check(
        "MCP server cloned",
        MCP_DIR.exists(),
        "Run: python scripts/setup_mcp.py",
    )

    # 3. Check dist/index.js exists (built)
    index_js = MCP_DIR / "dist" / "index.js"
    check(
        "MCP server built (dist/index.js)",
        index_js.exists(),
        "Run: cd tools/KiCAD-MCP-Server && npm run build",
    )

    # 4. Check node_modules exists
    node_modules = MCP_DIR / "node_modules"
    check(
        "Node dependencies installed",
        node_modules.exists() and node_modules.is_dir(),
        "Run: cd tools/KiCAD-MCP-Server && npm install",
    )

    # 5. Check Node.js is available
    check(
        "Node.js available",
        shutil.which("node") is not None,
        "Install Node.js 18+ from https://nodejs.org/",
    )

    # 6. Check .mcp.json points to correct path
    if MCP_JSON.exists():
        try:
            mcp_config = json.loads(MCP_JSON.read_text())
            servers = mcp_config.get("mcpServers", {})
            kicad_server = servers.get("kicad-mcp", {})
            args = kicad_server.get("args", [])
            if args:
                entry = Path(args[0])
                check(
                    f".mcp.json entry point valid",
                    entry.exists(),
                    f"Path not found: {args[0]}. Re-run: python scripts/setup_mcp.py",
                )
            else:
                check(".mcp.json has args", False, "Re-run: python scripts/setup_mcp.py")
        except (json.JSONDecodeError, KeyError):
            check(".mcp.json valid JSON", False, "Re-run: python scripts/setup_mcp.py")

    # 7. Quick module load test (MCP servers hang on stdio — timeout is expected/OK)
    if index_js.exists() and shutil.which("node"):
        try:
            result = subprocess.run(
                ["node", "-e", f"try {{ require('{str(index_js).replace(chr(92), '/')}') }} catch(e) {{ if(e.code==='MODULE_NOT_FOUND') {{ process.exit(1) }} }}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            modules_ok = result.returncode != 1
        except subprocess.TimeoutExpired:
            # Timeout means server started and is waiting for stdio — this is correct
            modules_ok = True
        check(
            "MCP server modules resolve",
            modules_ok,
            "Run: cd tools/KiCAD-MCP-Server && npm install && npm run build",
        )

    # Summary
    if errors:
        print(f"\n{RED}{BOLD}MCP NOT READY — {len(errors)} issue(s){RESET}")
        print(f"\nTo fix, run: python scripts/setup_mcp.py")
        return 1
    else:
        print(f"\n{GREEN}{BOLD}MCP READY — all checks passed{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
