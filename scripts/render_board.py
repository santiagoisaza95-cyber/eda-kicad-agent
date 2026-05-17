#!/usr/bin/env python3
"""Render a KiCad PCB to PNG via kicad-cli SVG export + cairosvg rasterization.

Pipeline:
  1. Invoke `kicad-cli pcb export svg --mode-single --layers ...` to produce SVG.
  2. Parse SVG with lxml, inject a dark `<rect>` at z-order 0 so the agent sees
     contrast similar to KiCad's UI.
  3. Rasterize SVG to PNG with cairosvg at scale = dpi/96.
  4. Optionally re-emit a copper-only variant (F.Cu + B.Cu) for routing review.

Public API:
    render_board(pcb_path, output_dir=None, layers=None, dpi=150,
                 generate_variants=True) -> dict[str, Path]

Returns dict with keys: 'full', 'copper' (None if generate_variants=False), 'svg'.

CLI:
    python scripts/render_board.py output/blue_pill.kicad_pcb

Speed budget: ~1.3 s on a 2-layer board; <2 s hard ceiling enforced by tests.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# -- GTK3 / cairo DLL bootstrap (Windows fallback) -----------------------------
#
# cairocffi (cairosvg's backend) calls ctypes.util.find_library which only
# searches PATH on Windows. If a system-wide GTK3 runtime isn't installed,
# we fall back to KiCad's bundled `cairo-2.dll` by prepending KiCad's bin
# directory to PATH BEFORE importing cairosvg.
def _ensure_cairo_dll_findable() -> None:
    """Prepend a directory containing cairo-2.dll to PATH if needed (Windows)."""
    if sys.platform != "win32":
        return
    # If a libcairo-2.dll is already findable on PATH, nothing to do.
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if not p:
            continue
        if (Path(p) / "libcairo-2.dll").exists() or (Path(p) / "cairo-2.dll").exists():
            return
    # Try config.json for kicad_install_path; fall back to default location.
    candidates: list[Path] = []
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "config.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text())
            kicad_install = cfg.get("kicad_install_path", "")
            if kicad_install:
                candidates.append(Path(kicad_install) / "bin")
        except json.JSONDecodeError:
            pass
    candidates.append(Path(r"C:\Program Files\KiCad\9.0\bin"))
    candidates.append(Path(r"C:\Program Files\GTK3-Runtime Win64\bin"))
    for cand in candidates:
        if cand.exists() and ((cand / "cairo-2.dll").exists() or (cand / "libcairo-2.dll").exists()):
            os.environ["PATH"] = str(cand) + os.pathsep + os.environ.get("PATH", "")
            return


_ensure_cairo_dll_findable()

import cairosvg  # noqa: E402  (must come after PATH bootstrap)
from lxml import etree  # noqa: E402


DEFAULT_LAYERS: list[str] = ["Edge_Cuts", "B.Cu", "F.Cu", "F.Mask", "F.SilkS"]
COPPER_LAYERS: list[str] = ["F.Cu", "B.Cu"]
DARK_BG_COLOR: str = "#1a1a1a"
SVG_NS: str = "http://www.w3.org/2000/svg"


def _resolve_kicad_cli() -> str:
    """Return absolute path to kicad-cli, preferring config.json, falling back to PATH."""
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "config.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text())
            cli_path = cfg.get("kicad_cli_path", "")
            if cli_path and Path(cli_path).exists():
                return cli_path
        except json.JSONDecodeError:
            pass
    found = shutil.which("kicad-cli")
    if found:
        return found
    raise FileNotFoundError(
        "kicad-cli not found on PATH and not in config.json. Install KiCad 9.x."
    )


def _export_svg(pcb_path: Path, svg_path: Path, layers: list[str]) -> None:
    """Run kicad-cli to export a single composited SVG of the requested layers."""
    cli = _resolve_kicad_cli()
    cmd = [
        cli, "pcb", "export", "svg",
        "--mode-single",
        "--exclude-drawing-sheet",
        "--page-size-mode", "2",  # board area only
        "--layers", ",".join(layers),
        "--output", str(svg_path),
        str(pcb_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, cmd,
            output=result.stdout, stderr=result.stderr,
        )


def _inject_dark_background(svg_path: Path, color: str = DARK_BG_COLOR) -> bytes:
    """Parse SVG, insert a full-canvas `<rect>` at z-order 0, return serialized bytes."""
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(svg_path), parser)
    root = tree.getroot()
    rect = etree.SubElement(root, f"{{{SVG_NS}}}rect")
    rect.set("width", "100%")
    rect.set("height", "100%")
    rect.set("fill", color)
    # Move the new rect to be the FIRST child so it renders behind everything.
    root.insert(0, rect)
    root.remove(rect)  # remove the appended copy
    root.insert(0, rect)  # insert at z-0
    return etree.tostring(tree, xml_declaration=True, encoding="utf-8")


def _svg_bytes_to_png(svg_bytes: bytes, png_path: Path, dpi: int) -> None:
    """Rasterize SVG bytes to PNG using cairosvg."""
    try:
        cairosvg.svg2png(
            bytestring=svg_bytes,
            write_to=str(png_path),
            scale=dpi / 96.0,
        )
    except Exception as exc:
        raise RuntimeError(
            f"cairosvg failed to render PNG (typically GTK3/cairo DLL missing): {exc}"
        ) from exc


def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True,
) -> dict[str, Path]:
    """Render a KiCad PCB to dark-background PNG(s).

    Args:
        pcb_path: Path to .kicad_pcb file.
        output_dir: Where to write outputs. Defaults to pcb_path.parent / "renders".
        layers: Layer list for the "full" render. Defaults to Edge_Cuts + Cu + Mask + Silk.
        dpi: PNG rasterization DPI (default 150).
        generate_variants: If True, also render a copper-only variant.

    Returns:
        dict with keys 'full' (Path), 'copper' (Path | None), 'svg' (Path).

    Raises:
        FileNotFoundError: pcb_path doesn't exist or kicad-cli not found.
        subprocess.CalledProcessError: kicad-cli SVG export failed.
        RuntimeError: cairosvg failed (typically GTK3 not installed).
    """
    pcb_path = Path(pcb_path)
    if not pcb_path.exists():
        raise FileNotFoundError(f"PCB file not found: {pcb_path}")

    if output_dir is None:
        output_dir = pcb_path.parent / "renders"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if layers is None:
        layers = list(DEFAULT_LAYERS)

    stem = pcb_path.stem
    svg_path = output_dir / f"{stem}_full.svg"
    full_png = output_dir / f"{stem}_full.png"
    copper_png: Optional[Path] = None

    # 1. Full render
    _export_svg(pcb_path, svg_path, layers)
    full_svg_bytes = _inject_dark_background(svg_path)
    _svg_bytes_to_png(full_svg_bytes, full_png, dpi)

    # 2. Copper-only variant
    if generate_variants:
        copper_svg_path = output_dir / f"{stem}_copper.svg"
        copper_png = output_dir / f"{stem}_copper.png"
        _export_svg(pcb_path, copper_svg_path, COPPER_LAYERS)
        copper_svg_bytes = _inject_dark_background(copper_svg_path)
        _svg_bytes_to_png(copper_svg_bytes, copper_png, dpi)

    return {
        "full": full_png,
        "copper": copper_png,
        "svg": svg_path,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/render_board.py <pcb_path>", file=sys.stderr)
        sys.exit(2)
    pcb_arg = Path(sys.argv[1])
    try:
        result = render_board(pcb_arg)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: kicad-cli failed (rc={exc.returncode})", file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"full:   {result['full']}")
    print(f"copper: {result['copper']}")
    print(f"svg:    {result['svg']}")


if __name__ == "__main__":
    main()
