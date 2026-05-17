# Render Pipeline — Module Context

**Module:** `scripts/render_board.py`
**Status:** Stage 1 Batch 1.1 deliverable (v2.0 foundation).
**Owners:** v2 visual perception layer — produces the PNGs the agent inspects at every checkpoint.

## Boundary

`scripts/render_board.py` owns the path from a `.kicad_pcb` file to dark-background PNG renders. It is the **only** module in this repo that:
- Invokes `kicad-cli pcb export svg`
- Manipulates SVG XML with lxml
- Calls cairosvg for SVG-to-PNG rasterization

Callers (agent loops, checkpoint hooks, debugging scripts) should treat the render pipeline as a black box: pass a PCB path, get back a dict of output PNG paths.

## Public API

```python
def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True,
) -> dict[str, Path]
```

Returns `{"full": Path, "copper": Path | None, "svg": Path}`:
- `full` — composite PNG with all default layers (always present, non-zero size).
- `copper` — F.Cu + B.Cu only (None iff `generate_variants=False`).
- `svg` — intermediate SVG kept for debugging.

Raises: `FileNotFoundError` (missing pcb or kicad-cli), `subprocess.CalledProcessError` (SVG export failed), `RuntimeError` (cairosvg/GTK3 failure).

CLI: `python scripts/render_board.py <pcb_path>` — uses defaults, prints output paths.

## Layer Composition Rationale

Default layer order (rendered back-to-front by SVG z-order):

| Layer | Purpose |
|-------|---------|
| `Edge_Cuts` | Board outline — critical for shape judgment |
| `B.Cu` | Back copper (blue) — bottom layer first for z-order |
| `F.Cu` | Front copper (red) |
| `F.Mask` | Front solder mask — for pad visibility |
| `F.SilkS` | Front silkscreen — text/refs on top |

The agent's vision model judges placement, routing, and component density from this composite. Copper-only variant strips silk/mask/edge for routing-focused inspection.

## Speed Budget

| Variant | Typical | Hard ceiling |
|---------|---------|--------------|
| Full (5 layers, 150 DPI) | ~0.9 s | — |
| Copper-only (2 layers) | ~0.4 s | — |
| **Total `render_board()` call** | **~1.3 s** | **2.0 s** (enforced by `test_render_under_2_seconds` via pytest-timeout) |

If a render regresses past 2 s, drop DPI before reducing layers — the agent needs all five layers to make placement/routing judgments.

## Known Limitations (v2.0)

- **Windows-only cairo DLL path.** Module prepends a directory containing `cairo-2.dll` or `libcairo-2.dll` to `PATH` before importing cairosvg. Falls back through (1) existing PATH, (2) `config.json` → `kicad_install_path/bin`, (3) hardcoded `C:\Program Files\KiCad\9.0\bin`, (4) `C:\Program Files\GTK3-Runtime Win64\bin`. KiCad's bundled `cairo-2.dll` works as a substitute for a full GTK3 runtime.
- **No PLOT_CONTROLLER fallback.** Section 2 of the rendering research evaluated `pcbnew.PLOT_CONTROLLER` as an alternative; not selected for v2.0 because it requires `kipython` invocation and layer-by-layer plotting without speed benefit. Re-evaluate if mid-render color injection becomes a need.
- **Dark background is a `<rect>` injected at z-0, not a true bg layer.** Sample pixel test asserts `(26, 26, 26) ± 2`. If KiCad's SVG output structure changes such that something opaque renders behind z-0, the dark-BG test will fail loudly — that's intentional.
