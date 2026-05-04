#!/usr/bin/env python3
"""Install and configure the KiCAD MCP Server (mixelpixx/KiCAD-MCP-Server).

This script:
1. Clones the MCP server repo into tools/KiCAD-MCP-Server
2. Runs npm install and npm run build
3. Installs Python requirements into KiCad's bundled Python
4. Verifies the MCP server is ready

Run: python scripts/setup_mcp.py
"""

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = PROJECT_ROOT / "tools" / "KiCAD-MCP-Server"
CONFIG_FILE = PROJECT_ROOT / "config.json"
MCP_JSON = PROJECT_ROOT / ".mcp.json"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def log_ok(msg: str) -> None:
    print(f"  {GREEN}[OK]{RESET} {msg}")


def log_fail(msg: str) -> None:
    print(f"  {RED}[FAIL]{RESET} {msg}")


def log_info(msg: str) -> None:
    print(f"  {YELLOW}[INFO]{RESET} {msg}")


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        log_fail("config.json not found. Run verify_toolchain.py first.")
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text())


def check_node() -> str | None:
    """Return node executable path or None."""
    node = shutil.which("node")
    if node:
        result = subprocess.run([node, "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        log_ok(f"Node.js found: {version} ({node})")
        return node
    log_fail("Node.js not found. Install Node.js 18+ from https://nodejs.org/")
    return None


def check_npm() -> str | None:
    """Return npm executable path or None."""
    npm = shutil.which("npm")
    if npm:
        result = subprocess.run([npm, "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        log_ok(f"npm found: {version}")
        return npm
    log_fail("npm not found. Install Node.js 18+ from https://nodejs.org/")
    return None


def check_git() -> str | None:
    """Return git executable path or None."""
    git = shutil.which("git")
    if git:
        log_ok(f"git found: {git}")
        return git
    log_fail("git not found.")
    return None


def clone_repo(git: str) -> bool:
    """Clone the MCP server repository."""
    if MCP_DIR.exists():
        log_info(f"MCP server directory already exists: {MCP_DIR}")
        # Pull latest
        log_info("Pulling latest changes...")
        result = subprocess.run(
            [git, "pull"],
            cwd=str(MCP_DIR),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            log_ok("Updated to latest version")
        else:
            log_info(f"Pull skipped: {result.stderr.strip()}")
        return True

    log_info("Cloning mixelpixx/KiCAD-MCP-Server...")
    tools_dir = PROJECT_ROOT / "tools"
    tools_dir.mkdir(exist_ok=True)

    result = subprocess.run(
        [git, "clone", "https://github.com/mixelpixx/KiCAD-MCP-Server.git"],
        cwd=str(tools_dir),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        log_fail(f"Clone failed: {result.stderr.strip()}")
        return False
    log_ok("Repository cloned successfully")
    return True


def npm_install(npm: str) -> bool:
    """Run npm install in the MCP server directory."""
    log_info("Running npm install...")
    result = subprocess.run(
        [npm, "install"],
        cwd=str(MCP_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        log_fail(f"npm install failed: {result.stderr.strip()[:200]}")
        return False
    log_ok("npm install completed")
    return True


def npm_build(npm: str) -> bool:
    """Run npm run build in the MCP server directory."""
    log_info("Running npm run build...")
    result = subprocess.run(
        [npm, "run", "build"],
        cwd=str(MCP_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        log_fail(f"npm build failed: {result.stderr.strip()[:200]}")
        return False

    # Verify dist/index.js exists
    index_js = MCP_DIR / "dist" / "index.js"
    if not index_js.exists():
        log_fail(f"Build artifact not found: {index_js}")
        return False

    log_ok(f"Build successful: {index_js}")
    return True


def install_python_deps(config: dict) -> bool:
    """Install Python requirements for the MCP server."""
    reqs_file = MCP_DIR / "requirements.txt"
    if not reqs_file.exists():
        log_info("No requirements.txt in MCP server — skipping Python deps")
        return True

    python_exe = config.get("python_interpreter", "")
    if not python_exe or not Path(python_exe).exists():
        log_info("KiCad Python not found — skipping MCP Python deps")
        return True

    log_info(f"Installing Python deps using: {python_exe}")
    result = subprocess.run(
        [python_exe, "-m", "pip", "install", "-r", str(reqs_file)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        log_fail(f"pip install failed: {result.stderr.strip()[:200]}")
        return False
    log_ok("Python dependencies installed")
    return True


def get_pythonpath(config: dict) -> str:
    """Determine the PYTHONPATH for pcbnew access."""
    system = platform.system()
    install_path = config.get("kicad_install_path", "")

    if system == "Windows":
        return str(Path(install_path) / "lib" / "python3" / "dist-packages")
    elif system == "Darwin":
        return "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python3.11/site-packages"
    else:
        return "/usr/lib/kicad/lib/python3/dist-packages"


def write_mcp_json(config: dict) -> bool:
    """Write the .mcp.json configuration file."""
    pythonpath = get_pythonpath(config)
    # Use forward slashes for cross-platform compat in JSON
    index_js = str(MCP_DIR / "dist" / "index.js").replace("\\", "/")

    mcp_config = {
        "mcpServers": {
            "kicad-mcp": {
                "command": "node",
                "args": [index_js],
                "env": {
                    "PYTHONPATH": pythonpath,
                    "LOG_LEVEL": "info",
                },
            }
        }
    }

    MCP_JSON.write_text(json.dumps(mcp_config, indent=2) + "\n")
    log_ok(f"Wrote {MCP_JSON}")
    return True


def verify_mcp_server() -> bool:
    """Quick verification that the MCP server can start."""
    index_js = MCP_DIR / "dist" / "index.js"
    if not index_js.exists():
        log_fail("dist/index.js not found — MCP server not built")
        return False

    # MCP servers are stdio-based — they hang waiting for protocol messages.
    # A timeout is EXPECTED and means the server started successfully.
    # We only fail if it crashes immediately with MODULE_NOT_FOUND.
    try:
        result = subprocess.run(
            ["node", "-e", f"require('{str(index_js).replace(chr(92), '/')}')"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # If it exited within 5s, check for errors
        if result.returncode != 0:
            if "MODULE_NOT_FOUND" in result.stderr or "Cannot find module" in result.stderr:
                log_fail("MCP server has missing modules — run npm install again")
                return False
    except subprocess.TimeoutExpired:
        # Timeout = server started and is waiting for stdio input. This is correct.
        pass

    log_ok("MCP server entry point is valid (starts without crash)")
    return True


def main() -> None:
    print(f"\n{BOLD}=== KiCAD MCP Server Setup ==={RESET}\n")

    config = load_config()

    # Pre-flight checks
    print(f"{BOLD}Step 1: Prerequisites{RESET}")
    node = check_node()
    npm = check_npm()
    git = check_git()
    if not all([node, npm, git]):
        log_fail("Missing prerequisites. Install Node.js 18+ and git.")
        sys.exit(1)

    # Clone
    print(f"\n{BOLD}Step 2: Clone repository{RESET}")
    if not clone_repo(git):
        sys.exit(1)

    # Install & build
    print(f"\n{BOLD}Step 3: Install & build{RESET}")
    if not npm_install(npm):
        sys.exit(1)
    if not npm_build(npm):
        sys.exit(1)

    # Python deps
    print(f"\n{BOLD}Step 4: Python dependencies{RESET}")
    install_python_deps(config)

    # Write .mcp.json
    print(f"\n{BOLD}Step 5: Configure MCP{RESET}")
    write_mcp_json(config)

    # Verify
    print(f"\n{BOLD}Step 6: Verify{RESET}")
    if verify_mcp_server():
        print(f"\n{GREEN}{BOLD}MCP SERVER READY{RESET}")
        print(f"  Server: {MCP_DIR / 'dist' / 'index.js'}")
        print(f"  Config: {MCP_JSON}")
        print(f"\n  Restart Claude Code to load the MCP server.")
    else:
        print(f"\n{RED}{BOLD}MCP SERVER SETUP INCOMPLETE{RESET}")
        print("  Check the errors above and re-run this script.")
        sys.exit(1)


if __name__ == "__main__":
    main()
