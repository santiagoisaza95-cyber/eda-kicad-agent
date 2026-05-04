#!/usr/bin/env python3
"""Discover and verify KiCad 9.x pcbnew SWIG API surface.

Introspects the actual pcbnew module and produces api_manifest.json
with verified class/function names, layer constants, and version info.

Run with whatever Python can import pcbnew:
  kipython scripts/discover_api.py
  OR
  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" scripts/discover_api.py
  OR
  .venv\\Scripts\\python scripts/discover_api.py  (if kigadgets linked)

Output: api_manifest.json in the project root.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "api_manifest.json"

# Classes and functions the bootstrap prompt expects to exist
EXPECTED_CLASSES = [
    "BOARD",
    "FOOTPRINT",
    "PAD",
    "PCB_IO_KICAD_SEXPR",
    "NETINFO_ITEM",
    "NETINFO_LIST",
    "PCB_TRACK",
    "PCB_VIA",
    "PCB_SHAPE",
    "PCB_TEXT",
    "ZONE",
    "PCB_GROUP",
    "BOARD_DESIGN_SETTINGS",
    "BOARD_ITEM",
]

EXPECTED_FUNCTIONS = [
    "FromMM",
    "ToMM",
    "FromMils",
    "ToMils",
    "SaveBoard",
    "LoadBoard",
    "GetBoard",
    "VECTOR2I",
    "EDA_ANGLE",
    "LSET",
]

EXPECTED_LAYER_CONSTANTS = [
    "F_Cu",
    "B_Cu",
    "F_SilkS",
    "B_SilkS",
    "F_Mask",
    "B_Mask",
    "F_Paste",
    "B_Paste",
    "F_Fab",
    "B_Fab",
    "Edge_Cuts",
    "In1_Cu",
    "In2_Cu",
    "Dwgs_User",
    "Cmts_User",
]

# Footprint IO class names across KiCad versions (try all, record which exist)
FOOTPRINT_IO_CANDIDATES = [
    "PCB_IO_KICAD_SEXPR",
    "PCB_IO_KICAD",
    "PCB_IO",
    "PLUGIN",
    "IO_MGR",
]

# Pad shape constants
PAD_SHAPE_CANDIDATES = [
    "PAD_SHAPE_RECT",
    "PAD_SHAPE_CIRCLE",
    "PAD_SHAPE_OVAL",
    "PAD_SHAPE_TRAPEZOID",
    "PAD_SHAPE_ROUNDRECT",
    "PAD_SHAPE_CHAMFERED_RECT",
    "PAD_SHAPE_CUSTOM",
]

# Pad types
PAD_TYPE_CANDIDATES = [
    "PAD_ATTRIB_SMD",
    "PAD_ATTRIB_PTH",
    "PAD_ATTRIB_NPTH",
    "PAD_ATTRIB_CONN",
]


def check_attr(module: object, name: str) -> dict:
    """Check if an attribute exists on a module and return its type info."""
    if hasattr(module, name):
        obj = getattr(module, name)
        return {
            "exists": True,
            "type": type(obj).__name__,
            "value": str(obj) if not callable(obj) else None,
        }
    return {"exists": False, "type": None, "value": None}


def discover_api() -> dict:
    """Run full API discovery and return manifest dict."""
    manifest: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "discover_api.py",
        "python_version": sys.version,
        "python_executable": sys.executable,
        "kicad_version": None,
        "pcbnew_import_method": None,
        "classes": {},
        "functions": {},
        "layer_constants": {},
        "footprint_io": {},
        "pad_shapes": {},
        "pad_types": {},
        "verified": [],
        "missing": [],
        "warnings": [],
    }

    # Try to import pcbnew
    try:
        import pcbnew
        manifest["pcbnew_import_method"] = "direct"
    except ImportError:
        try:
            from kigadgets import pcbnew_bare as pcbnew  # type: ignore
            if pcbnew is None:
                raise ImportError("kigadgets loaded but pcbnew is None")
            manifest["pcbnew_import_method"] = "kigadgets"
        except (ImportError, TypeError):
            manifest["pcbnew_import_method"] = "FAILED"
            manifest["warnings"].append(
                "Could not import pcbnew via direct import or kigadgets. "
                "Install KiCad 9.x and run 'python -m kigadgets' to link."
            )
            return manifest

    # Get version
    try:
        manifest["kicad_version"] = pcbnew.Version()
    except Exception:
        try:
            manifest["kicad_version"] = pcbnew.GetBuildVersion()
        except Exception:
            manifest["kicad_version"] = "UNKNOWN"

    # Check classes
    for name in EXPECTED_CLASSES:
        result = check_attr(pcbnew, name)
        manifest["classes"][name] = result
        if result["exists"]:
            manifest["verified"].append(name)
        else:
            manifest["missing"].append(name)

    # Check functions
    for name in EXPECTED_FUNCTIONS:
        result = check_attr(pcbnew, name)
        manifest["functions"][name] = result
        if result["exists"]:
            manifest["verified"].append(name)
        else:
            manifest["missing"].append(name)

    # Check layer constants
    for name in EXPECTED_LAYER_CONSTANTS:
        result = check_attr(pcbnew, name)
        manifest["layer_constants"][name] = result
        if result["exists"]:
            manifest["verified"].append(name)
        else:
            manifest["missing"].append(name)

    # Check footprint IO variants
    for name in FOOTPRINT_IO_CANDIDATES:
        result = check_attr(pcbnew, name)
        manifest["footprint_io"][name] = result
        if result["exists"] and name not in manifest["verified"]:
            manifest["verified"].append(name)

    # Check pad shapes
    for name in PAD_SHAPE_CANDIDATES:
        result = check_attr(pcbnew, name)
        manifest["pad_shapes"][name] = result

    # Check pad types
    for name in PAD_TYPE_CANDIDATES:
        result = check_attr(pcbnew, name)
        manifest["pad_types"][name] = result

    # Summarize
    total_checked = len(EXPECTED_CLASSES) + len(EXPECTED_FUNCTIONS) + len(EXPECTED_LAYER_CONSTANTS)
    verified_count = sum(
        1 for name in EXPECTED_CLASSES + EXPECTED_FUNCTIONS + EXPECTED_LAYER_CONSTANTS
        if name in manifest["verified"]
    )
    manifest["summary"] = {
        "total_checked": total_checked,
        "verified": verified_count,
        "missing": total_checked - verified_count,
        "coverage_pct": round(verified_count / total_checked * 100, 1) if total_checked else 0,
    }

    return manifest


def main() -> None:
    print("=== KiCad pcbnew API Discovery ===\n")

    manifest = discover_api()

    if manifest["pcbnew_import_method"] == "FAILED":
        print("ERROR: Could not import pcbnew.")
        for w in manifest["warnings"]:
            print(f"  ! {w}")
        # Still write the manifest so verify_toolchain.py can detect the failure
        OUTPUT_FILE.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest written to: {OUTPUT_FILE} (INCOMPLETE — pcbnew not available)")
        sys.exit(1)

    print(f"KiCad version: {manifest['kicad_version']}")
    print(f"Import method: {manifest['pcbnew_import_method']}")
    print(f"Python: {manifest['python_executable']}")
    print()

    # Report classes
    print("--- Classes ---")
    for name in EXPECTED_CLASSES:
        status = "OK" if manifest["classes"][name]["exists"] else "MISSING"
        print(f"  [{status:^7}] {name}")

    # Report functions
    print("\n--- Functions ---")
    for name in EXPECTED_FUNCTIONS:
        status = "OK" if manifest["functions"][name]["exists"] else "MISSING"
        print(f"  [{status:^7}] {name}")

    # Report layers
    print("\n--- Layer Constants ---")
    for name in EXPECTED_LAYER_CONSTANTS:
        info = manifest["layer_constants"][name]
        if info["exists"]:
            print(f"  [  OK   ] {name} = {info['value']}")
        else:
            print(f"  [MISSING] {name}")

    # Report footprint IO
    print("\n--- Footprint IO Classes ---")
    for name in FOOTPRINT_IO_CANDIDATES:
        status = "OK" if manifest["footprint_io"][name]["exists"] else "MISSING"
        print(f"  [{status:^7}] {name}")

    # Summary
    s = manifest["summary"]
    print(f"\n=== Summary: {s['verified']}/{s['total_checked']} verified ({s['coverage_pct']}%) ===")

    if manifest["missing"]:
        print(f"\nMISSING ({len(manifest['missing'])}):")
        for name in manifest["missing"]:
            print(f"  - {name}")

    # Write manifest
    OUTPUT_FILE.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to: {OUTPUT_FILE}")

    if manifest["missing"]:
        print("\nWARNING: Some expected API names are missing. Skills must use UNVERIFIED markers.")
        sys.exit(2)
    else:
        print("\nAll expected API names verified. Skills can be written with confidence.")
        sys.exit(0)


if __name__ == "__main__":
    main()
