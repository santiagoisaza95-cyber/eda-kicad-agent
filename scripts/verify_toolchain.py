#!/usr/bin/env python3
"""Verify the eda-kicad-agent toolchain is correctly installed.

Checks: Python version, kicad-cli, pcbnew import, pytest, footprint
libraries, and api_manifest.json. Prints pass/fail per check.

Run: .venv\\Scripts\\python scripts\\verify_toolchain.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ANSI colors (work in Windows Terminal / MINGW)
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def pass_msg(label: str, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"  {GREEN}[PASS]{RESET} {label}{suffix}")
    return True


def fail_msg(label: str, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"  {RED}[FAIL]{RESET} {label}{suffix}")
    return False


def warn_msg(label: str, detail: str = "") -> bool:
    suffix = f" — {detail}" if detail else ""
    print(f"  {YELLOW}[WARN]{RESET} {label}{suffix}")
    return True  # warnings don't block


def check_python_version() -> bool:
    """Python >= 3.11 required."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 11):
        return pass_msg("Python version", version_str)
    return fail_msg("Python version", f"{version_str} (need >= 3.11)")


def check_kicad_cli() -> bool:
    """kicad-cli must be on PATH or at known Windows location."""
    # Try PATH first
    kicad_cli = shutil.which("kicad-cli")
    if kicad_cli:
        try:
            result = subprocess.run(
                [kicad_cli, "version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip()
            return pass_msg("kicad-cli", f"{version} ({kicad_cli})")
        except Exception as e:
            return fail_msg("kicad-cli", f"found but error: {e}")

    # Try known Windows paths
    config_file = PROJECT_ROOT / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            cli_path = config.get("kicad_cli_path", "")
            if cli_path and Path(cli_path).exists():
                result = subprocess.run(
                    [cli_path, "version"],
                    capture_output=True, text=True, timeout=10
                )
                version = result.stdout.strip()
                return pass_msg("kicad-cli", f"{version} (from config.json)")
        except Exception:
            pass

    # Check common Windows install location
    win_default = Path(r"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe")
    if win_default.exists():
        try:
            result = subprocess.run(
                [str(win_default), "version"],
                capture_output=True, text=True, timeout=10
            )
            version = result.stdout.strip()
            return pass_msg("kicad-cli", f"{version} ({win_default})")
        except Exception as e:
            return fail_msg("kicad-cli", f"found at default path but error: {e}")

    return fail_msg(
        "kicad-cli",
        "NOT FOUND. Install KiCad 9.x from https://www.kicad.org/download/windows/"
    )


def check_pcbnew_import() -> bool:
    """pcbnew must be importable (directly or via kigadgets)."""
    try:
        import pcbnew  # type: ignore
        version = getattr(pcbnew, "Version", lambda: "unknown")()
        return pass_msg("pcbnew import", f"direct import, version {version}")
    except ImportError:
        pass

    # Try kigadgets
    try:
        import kigadgets  # type: ignore  # noqa: F401
        pcbnew_mod = kigadgets.get_pcbnew_module()
        if pcbnew_mod is not None:
            version = getattr(pcbnew_mod, "Version", lambda: "unknown")()
            return pass_msg("pcbnew import", f"via kigadgets, version {version}")
    except Exception:
        pass

    return fail_msg(
        "pcbnew import",
        "FAILED. Install KiCad 9.x, then run: python -m kigadgets"
    )


def check_pytest() -> bool:
    """pytest must be importable."""
    try:
        import pytest  # type: ignore
        return pass_msg("pytest", f"version {pytest.__version__}")
    except ImportError:
        return fail_msg("pytest", "NOT FOUND. Run: pip install pytest>=7.0")


def check_footprint_library() -> bool:
    """Footprint library path must exist and contain .pretty dirs."""
    config_file = PROJECT_ROOT / "config.json"
    if not config_file.exists():
        return fail_msg("Footprint library", "config.json not found")

    try:
        config = json.loads(config_file.read_text())
    except json.JSONDecodeError:
        return fail_msg("Footprint library", "config.json is invalid JSON")

    fp_path = config.get("footprint_library_path", "")
    if not fp_path:
        return fail_msg("Footprint library", "footprint_library_path not set in config.json")

    fp_dir = Path(fp_path)
    if not fp_dir.exists():
        return fail_msg("Footprint library", f"path does not exist: {fp_path}")

    # Check for .pretty directories
    pretty_dirs = list(fp_dir.glob("*.pretty"))
    if pretty_dirs:
        return pass_msg("Footprint library", f"{len(pretty_dirs)} .pretty dirs at {fp_path}")
    return fail_msg("Footprint library", f"no .pretty directories found in {fp_path}")


def check_api_manifest() -> bool:
    """api_manifest.json must exist and have verified entries."""
    manifest_file = PROJECT_ROOT / "api_manifest.json"
    if not manifest_file.exists():
        return fail_msg(
            "API manifest",
            "NOT FOUND. Run: python scripts/discover_api.py"
        )

    try:
        manifest = json.loads(manifest_file.read_text())
    except json.JSONDecodeError:
        return fail_msg("API manifest", "invalid JSON")

    method = manifest.get("pcbnew_import_method", "UNKNOWN")
    if method == "FAILED":
        return fail_msg("API manifest", "pcbnew import failed during discovery")

    summary = manifest.get("summary")
    if summary:
        verified = summary.get("verified", 0)
        total = summary.get("total_checked", 0)
        pct = summary.get("coverage_pct", 0)
        if verified == total:
            return pass_msg("API manifest", f"{verified}/{total} verified ({pct}%)")
        elif verified > 0:
            warn_msg(
                "API manifest",
                f"{verified}/{total} verified ({pct}%) — check missing items"
            )
            return True
        else:
            return fail_msg("API manifest", "0 verified — pcbnew not functional")

    return fail_msg("API manifest", "no summary section found")


def main() -> None:
    print(f"\n{BOLD}=== eda-kicad-agent Toolchain Verification ==={RESET}\n")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Python:       {sys.executable}")
    print()

    checks = [
        ("Python Version", check_python_version),
        ("KiCad CLI", check_kicad_cli),
        ("pcbnew Import", check_pcbnew_import),
        ("pytest", check_pytest),
        ("Footprint Library", check_footprint_library),
        ("API Manifest", check_api_manifest),
    ]

    results: list[tuple[str, bool]] = []
    for name, check_fn in checks:
        try:
            passed = check_fn()
        except Exception as e:
            passed = fail_msg(name, f"unexpected error: {e}")
        results.append((name, passed))

    # Summary
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    failed_count = total - passed_count

    print(f"\n{BOLD}=== Results: {passed_count}/{total} passed ==={RESET}")

    if failed_count == 0:
        print(f"\n{GREEN}{BOLD}GATE 1 PASSED — all checks green.{RESET}")
        print("Phase 2 (Agent Architecture) can proceed.")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}GATE 1 FAILED — {failed_count} check(s) failed.{RESET}")
        print("Fix the failures above before proceeding to Phase 2.")
        # Critical vs non-critical
        critical = {"KiCad CLI", "pcbnew Import"}
        critical_failures = [name for name, passed in results if not passed and name in critical]
        if critical_failures:
            print(f"\nCRITICAL: {', '.join(critical_failures)} must be resolved first.")
            print("Install KiCad 9.x from: https://www.kicad.org/download/windows/")
        sys.exit(1)


if __name__ == "__main__":
    main()
