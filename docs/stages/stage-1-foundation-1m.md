# Stage 1: Foundation — Detailed Reference (1M)

**Status:** AS PROPOSED (owner approved at architecture level in Phase 4; operational expansion below)
**Date:** 2026-05-16
**Project:** eda-kicad-agent v2
**Context budget:** 1M (Opus 4.7)

## Purpose
Build the v2 substrate — visual render pipeline (`scripts/render_board.py`), supplier-anchored DRC profile system (`supplier_profiles/` + `scripts/supplier_drc/`), audition contract for the 555 LED blinker, demotion of 4.6 artifacts to `baselines/4.6/`, and refreshed toolchain/API verification — all so Stage 2 can encode an iterative build loop on top of working primitives.

## Architecture
```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Stage 1: Foundation                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────┐         ┌────────────────────────┐                │
│   │  Batch 1.1       │         │  Batch 1.2             │                │
│   │  Render Pipeline │         │  Supplier DRC          │                │
│   │                  │         │                        │                │
│   │  requirements    │         │  supplier_profiles/    │                │
│   │  verify_toolchain│         │  ├── schema.py         │                │
│   │  render_board.py │         │  ├── jlcpcb.yaml       │                │
│   │  test_render     │         │  └── README.md         │                │
│   │  context.md      │         │  scripts/supplier_drc/ │                │
│   └──────────────────┘         │  ├── loader.py         │                │
│            │                   │  ├── validators.py     │                │
│            │                   │  └── __init__.py       │                │
│            │                   │  supplier-drc-rules.md │                │
│            │                   │  test_supplier_drc.py  │                │
│            │                   │  context.md            │                │
│            │                   └────────────────────────┘                │
│            │                            │                                │
│            ▼                            ▼                                │
│   ┌──────────────────┐         ┌────────────────────────┐                │
│   │  Batch 1.3       │         │  Batch 1.4             │                │
│   │  555 Contract    │         │  Baselines + Manifest  │                │
│   │                  │         │                        │                │
│   │  blinker_555     │         │  baselines/4.6/        │                │
│   │  _contract.md    │         │  (git mv from scripts) │                │
│   │  test_blinker    │         │  api_manifest refresh  │                │
│   │  _555.py         │         │  context.md ×2         │                │
│   │  context.md      │         └────────────────────────┘                │
│   └──────────────────┘                                                   │
│            │                            │                                │
│            └────────────┬───────────────┘                                │
│                         ▼                                                │
│           ┌─────────────────────────────────┐                            │
│           │  Stage 1 Complete                │                            │
│           │  → Stage 2 encodes build loop   │                            │
│           └─────────────────────────────────┘                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Data flow (runtime usage by Stage 2/3):
  KiCad .kicad_pcb ──► kicad-cli SVG ──► lxml dark-bg inject ──► cairosvg PNG
                                                                       │
                                                                       ▼
                                                              {full, copper, svg}
  supplier_profiles/jlcpcb.yaml ──► Pydantic ──► SupplierProfile ──► .kicad_dru
                                                                       │
                                                                       ▼
                                                              consumed by KiCad DRC
```

## Deliverables
| # | Deliverable | Key Files | Validation | Notes |
|---|-------------|-----------|------------|-------|
| 1 | PCB render primitive | `scripts/render_board.py` | `python scripts/render_board.py output/blue_pill.kicad_pcb` produces `<board>_full.png` + `<board>_copper.png` in <2 s | Subprocess kicad-cli + lxml + cairosvg; returns `{'full': Path, 'copper': Path \| None, 'svg': Path}` |
| 2 | Supplier profile schema | `supplier_profiles/schema.py`, `supplier_profiles/README.md` | `pytest tests/test_supplier_drc.py::test_schema_loads -v` | Pydantic v2 models; nested `trace_rules`, `via_rules`, `pad_rules`, `solder_mask_rules`, `silkscreen_rules`, `board_rules`, `cost_premiums` |
| 3 | JLCPCB populated profile | `supplier_profiles/jlcpcb.yaml` | `pytest tests/test_supplier_drc.py::test_jlcpcb_profile_valid -v` | All 18 axes from research/supplier_drc_research.md table; explicit units + `recommended` fields |
| 4 | DRC loader + DRU emitter | `scripts/supplier_drc/loader.py`, `scripts/supplier_drc/__init__.py`, `scripts/supplier_drc/validators.py` | `pytest tests/test_supplier_drc.py::test_emit_dru -v` produces valid `.kicad_dru` | `load_supplier_profile(name) -> SupplierProfile` + `emit_kicad_dru(profile, path) -> Path`; validators.py is stub for v2.x external checks |
| 5 | Mandatory supplier-DRC rule | `agent_docs/rules/supplier-drc-rules.md` | Loads via CLAUDE.md routing; appears in router table | Mandatory rule: load profile → emit DRU → block routing until DRU emitted; lists 5 risk axes from research |
| 6 | Audition contract (555 LED blinker) | `contracts/blinker_555_contract.md` | Contract checklist parseable; `supplier: jlcpcb` metadata present; "DESIGN FROM THIS CONTRACT ONLY" clause present | 5–7 components (NE555 + LED + 2× R + 2× C + power header); ~6 nets; 20×30 mm board |
| 7 | Audition test suite | `tests/test_blinker_555.py` | `pytest tests/test_blinker_555.py -v --collect-only` enumerates checks | Mirrors `tests/test_blue_pill.py` structure: component count, net connectivity, DRC=0/0 against DRU, dimensions, F.Cu layer placement |
| 8 | Render-board tests | `tests/test_render_board.py` | `pytest tests/test_render_board.py -v` passes | (a) return dict shape, (b) PNGs non-zero, (c) dark BG sample, (d) <2 s timeout |
| 9 | Supplier-DRC tests | `tests/test_supplier_drc.py` | `pytest tests/test_supplier_drc.py -v` passes | (a) schema_loads, (b) jlcpcb_profile_valid, (c) emit_dru parseable, (d) unknown supplier raises FileNotFoundError, (e) malformed YAML raises ValidationError |
| 10 | 4.6 baselines preserved | `baselines/4.6/README.md`, `baselines/4.6/build_blue_pill.py`, `baselines/4.6/route_blue_pill.py`, `baselines/4.6/blue_pill.kicad_pcb`, `.kicad_pro`, `.kicad_prl` | `git mv` history preserved; README explains provenance | All via `git mv` to preserve blame; README documents 2026-03-06 production + 54/54 tests + owner verdict |
| 11 | Refreshed API manifest | `api_manifest.json` (regenerated) | `python scripts/discover_api.py` completes; file timestamp updated; verified=100% | Runs against KiCad 9.0.7; one-shot refresh at v2 start |
| 12 | Updated toolchain verifier | `scripts/verify_toolchain.py` (UPDATED) | `python scripts/verify_toolchain.py` exits 0 | Adds import cairosvg + lxml checks + GTK3 DLL probe on Windows; clear remediation message on failure |
| 13 | Updated requirements | `requirements.txt` (+ `cairosvg>=2.7.0`, `lxml>=5.0.0`) | `pip install -r requirements.txt` clean | Two new lines; existing deps unchanged |
| 14 | Context docs (5) | `docs/context/{render-pipeline,supplier-drc,contracts,baselines,routing-primitives}.context.md` | Each describes its module boundary; routing-primitives explicitly notes v1 survivors | 5 of 6 .context.md files; the 6th (agent-skills.context.md) is Stage 2 |

## Technology
| Component | Choice | Why | Alternatives Considered |
|-----------|--------|-----|------------------------|
| PCB → SVG export | `kicad-cli pcb export svg --mode-single` | Supported CLI surface; ~300–400 ms; no GUI dependency | `pcbnew.PLOT_CONTROLLER` (requires kipython, layer-by-layer, no speed win on Windows); pcbnew Python direct (heavier boilerplate) |
| SVG → PNG conversion | `cairosvg>=2.7.0` (`scale=dpi/96`) | Best speed/quality on Windows; ~600–900 ms @ 150 DPI; documented Chocolatey GTK3 install path | `svglib+reportlab` (no gradients/clipping, 1–2 s); `Wand+ImageMagick` (heavy system dep); `Playwright headless` (2–4 s cold, overkill); `rsvg-convert` (not viable on Windows); `Pillow native` (cannot parse SVG) |
| SVG dark-BG injection | `lxml>=5.0.0` etree to inject `<rect width=100% height=100% fill=#1a1a1a>` at z-order 0 | Surgical SVG mutation; matches KiCad UI; better vision-model contrast than white | Generate PNG with transparency then alpha-blend (cairosvg→white default; adds Pillow step); custom theme via `--theme` (more complex, less portable) |
| Default layers (full view) | `Edge_Cuts, B.Cu, F.Cu, F.Mask, F.SilkS` (5 layers) | KiCad default palette already disambiguates; no custom theme needed | All-layer composite (too noisy); copper-only (loses outline context); silk+outline only (loses copper) |
| Copper variant | `F.Cu + B.Cu` (2 layers) | Routing-specific judgment without silk/mask noise | Single-layer per view (3 views) — N=3 explosion |
| Default DPI | 150 | Sub-2 s budget for full + copper sequential renders | 96 (too low for line judgments); 200 (~1.4 s — still in budget but margin tight); 300 (>3 s, breaks <2s budget) |
| Supplier schema format | YAML + Pydantic v2 | YAML readable for nested rules; Pydantic = type-checked load + clear errors; matches "configs are JSON, schemas are YAML" v1 convention | JSON (less readable for nested rules); JSON Schema (no clean Pydantic mapping); TOML (less common for deeply nested config); pure Python dataclasses (no YAML deserialization for free) |
| DRU emission | Native KiCad `.kicad_dru` text format using lisp-style S-expressions | KiCad-native enforcement; no custom Python re-checker needed for expressible rules | Custom Python validator wrapping pcbnew (duplicates KiCad's own DRC); external rule manager (overkill); convert at runtime via plugin (KiCad version risk) |
| Supplier #1 (populated) | JLCPCB | Most common low-cost fab; published spec is comprehensive | PCBWay (looser min trace but pricing less predictable); OSH Park (USA premium, 6-mil min, too restrictive baseline); Eurocircuits (EU premium, 8-mil min) |
| System dependency | `gtk3-runtime-bin-x64` via Chocolatey | One-liner install (`choco install gtk3-runtime-bin-x64`); cairosvg needs GTK on Windows | Manual GTK binary install (finicky); WSL2 + Linux GTK (host-system shift); container (overkill for dev) |

## Data Models / Schemas

### SupplierProfile (Pydantic v2)
```python
# supplier_profiles/schema.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

class Measurement(BaseModel):
    """A single dimensioned design-rule value."""
    value: float
    unit: Literal["mm", "mil", "oz"]
    mil_equiv: Optional[float] = None
    recommended: Optional[float] = None
    comment: Optional[str] = None
    cost_grade: Optional[Literal["standard", "premium"]] = None
    direction: Optional[Literal["per_side", "total"]] = None

class TraceRules(BaseModel):
    min_trace_width: Measurement
    min_trace_spacing: Measurement
    copper_to_edge: Measurement

class ViaRules(BaseModel):
    min_via_drill: Measurement
    min_via_pad_diameter: Measurement
    min_annular_ring: Measurement
    via_to_via_clearance: Measurement
    plated_hole_range: dict  # {min, max, unit, increment, tolerance}
    non_plated_hole_min: Measurement

class PadRules(BaseModel):
    min_pad_to_pad: Measurement
    min_smd_clearance: Measurement

class SolderMaskRules(BaseModel):
    min_mask_clearance: Measurement
    min_mask_web: Measurement

class SilkscreenRules(BaseModel):
    min_line_width: Measurement
    min_text_height: Measurement
    clearance_from_pad: Measurement

class BoardRules(BaseModel):
    thickness: dict  # {standard, range, unit}
    copper_weight: dict
    size_min: dict
    size_max: dict
    surface_finish: dict

class CostPremium(BaseModel):
    condition: str  # e.g. "trace_width < 0.0762mm"
    cost_impact: Literal["+", "++", "+++"]

class DesignRules(BaseModel):
    trace_rules: TraceRules
    via_rules: ViaRules
    pad_rules: PadRules
    solder_mask_rules: SolderMaskRules
    silkscreen_rules: SilkscreenRules
    board_rules: BoardRules
    cost_premiums: dict[str, CostPremium]

class SupplierMetadata(BaseModel):
    name: str
    capability_tier: str
    last_updated: str  # ISO date
    source_url: str

class SupplierProfile(BaseModel):
    metadata: SupplierMetadata
    design_rules: DesignRules
```

### supplier_profiles/jlcpcb.yaml (excerpt from research)
```yaml
# supplier_profiles/jlcpcb.yaml
metadata:
  name: "JLCPCB"
  capability_tier: "standard-2layer-fr4"
  last_updated: "2026-05-16"
  source_url: "https://jlcpcb.com/capabilities/pcb-capabilities"
design_rules:
  trace_rules:
    min_trace_width: { value: 0.127, unit: mm, mil_equiv: 5, recommended: 0.15 }
    min_trace_spacing: { value: 0.127, unit: mm, mil_equiv: 5 }
    copper_to_edge: { value: 0.3, unit: mm, comment: "From milled edge" }
  via_rules:
    min_via_drill: { value: 0.3, unit: mm, cost_grade: standard, comment: "0.2mm at premium" }
    min_via_pad_diameter: { value: 0.6, unit: mm }
    min_annular_ring: { value: 0.15, unit: mm, recommended: 0.2 }
    via_to_via_clearance: { value: 0.254, unit: mm }
    plated_hole_range: { min: 0.15, max: 6.35, unit: mm, increment: 0.05, tolerance: 0.08 }
    non_plated_hole_min: { value: 0.5, unit: mm }
  pad_rules:
    min_pad_to_pad: { value: 0.127, unit: mm }
    min_smd_clearance: { value: 0.1, unit: mm }
  solder_mask_rules:
    min_mask_clearance: { value: 0.05, unit: mm, direction: per_side }
    min_mask_web: { value: 0.1, unit: mm }
  silkscreen_rules:
    min_line_width: { value: 0.15, unit: mm }
    min_text_height: { value: 1.0, unit: mm }
    clearance_from_pad: { value: 0.1, unit: mm }
  board_rules:
    thickness: { standard: 1.6, range: [0.4, 2.0], unit: mm }
    copper_weight: { standard: 1, options: [1, 2], unit: oz }
    size_min: { x: 5, y: 5, unit: mm }
    size_max: { x: 400, y: 500, unit: mm }
    surface_finish: { standard: "HASL (lead-free)", options: ["HASL", "ENIG", "OSP"] }
  cost_premiums:
    trace_below_3mil:
      condition: "trace_width < 0.0762mm"
      cost_impact: "+++"
    via_below_12mil:
      condition: "via_drill < 0.3mm"
      cost_impact: "+++"
    enig_finish:
      condition: "surface_finish == ENIG"
      cost_impact: "++"
```

### render_board return type
```python
RenderResult = dict[str, Path]
# Keys:
#   'full'   → Path to <board>_full.png (5 layers, dark BG, 150 DPI default)
#   'copper' → Path to <board>_copper.png (F.Cu+B.Cu only) or None if generate_variants=False
#   'svg'    → Path to <board>_render.svg (intermediate; kept for debugging)
```

### Emitted .kicad_dru (excerpt)
```lisp
(version 1)
(rule "Min Trace Width (JLCPCB)" (constraint track_width (min 0.127mm)))
(rule "Min Clearance (JLCPCB)" (constraint clearance (min 0.127mm)) (condition "A.Type == 'track' && B.Type == 'track'"))
(rule "Min Edge Clearance (JLCPCB)" (constraint edge_clearance (min 0.3mm)))
(rule "Min Annular Ring (JLCPCB)" (constraint annular_width (min 0.15mm)) (condition "A.Type == 'via'"))
(rule "Min Via Drill (JLCPCB)" (constraint hole_size (min 0.3mm)) (condition "A.Type == 'via'"))
(rule "Min Silkscreen Line Width (JLCPCB)" (constraint silk_line_width (min 0.15mm)))
(rule "Min Silkscreen Text Height (JLCPCB)" (constraint silk_text_height (min 1.0mm)))
;; Known gaps (UI-only / external check):
;;   - Solder mask clearance: set via BOARD_DESIGN_SETTINGS, not DRU
;;   - Non-plated hole minimum: external Python validator (v2.x)
;;   - Board thickness / copper weight: metadata, not DRC-checkable
```

## API Contracts

### `render_board(pcb_path, output_dir=None, layers=None, dpi=150, generate_variants=True) -> dict[str, Path]`
```python
def render_board(
    pcb_path: Path,
    output_dir: Optional[Path] = None,
    layers: Optional[list[str]] = None,
    dpi: int = 150,
    generate_variants: bool = True,
) -> dict[str, Path]:
    """
    Render a KiCad PCB to PNG(s) with dark background.

    Pipeline:
      1. Subprocess `kicad-cli pcb export svg --mode-single --layers <L> --output <SVG> <PCB>`
      2. Parse SVG via lxml.etree; inject <rect width='100%' height='100%' fill='#1a1a1a'> at z-order 0
      3. cairosvg.svg2png(bytestring=..., scale=dpi/96, write_to=<PNG>)
      4. If generate_variants: repeat for copper-only (F.Cu + B.Cu) → second PNG

    Args:
      pcb_path: path to .kicad_pcb file
      output_dir: where to write SVG + PNG; defaults to pcb_path.parent
      layers: layer list for full view; defaults to [Edge_Cuts, B.Cu, F.Cu, F.Mask, F.SilkS]
      dpi: PNG rasterization DPI; default 150
      generate_variants: emit copper-only second PNG; default True

    Returns:
      {'full': Path, 'copper': Path | None, 'svg': Path}

    Raises:
      FileNotFoundError: pcb_path doesn't exist or kicad-cli not on PATH
      subprocess.CalledProcessError: kicad-cli SVG export fails
      RuntimeError: cairosvg fails (typically GTK3 not installed)
    """
```

### `load_supplier_profile(name: str) -> SupplierProfile`
```python
def load_supplier_profile(name: str) -> SupplierProfile:
    """
    Load and validate a supplier profile by name.

    Args:
      name: bare name (e.g. "jlcpcb") — resolves to supplier_profiles/<name>.yaml

    Returns:
      Validated SupplierProfile model

    Raises:
      FileNotFoundError: no such supplier YAML
      pydantic.ValidationError: YAML present but malformed against schema
    """
```

### `emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path`
```python
def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path:
    """
    Write a .kicad_dru file from the validated supplier profile.

    Emits expressible rules:
      - track_width, clearance, edge_clearance, annular_width, hole_size (via_diameter),
        silk_line_width, silk_text_height
    Documents gaps inline as comments:
      - Solder mask clearance (UI-only)
      - Non-plated hole min (external)
      - Board thickness / copper weight (metadata)

    Returns:
      out_path (for chaining)
    """
```

## Batches

### Batch 1.1: Render pipeline foundation
**Objective**: Stand up the visual perception primitive that Stage 2 visual-review-skill consumes; <2 s per render budget; dark-BG PNGs that vision models can read.

#### Task 1.1.1: Update requirements
- **Files**: Modify `requirements.txt`
- **Pattern**: Append two lines; preserve existing order
```
cairosvg>=2.7.0
lxml>=5.0.0
```
- **Test**: `pip install -r requirements.txt` → no errors

#### Task 1.1.2: Extend toolchain verifier
- **Files**: Modify `scripts/verify_toolchain.py`
- **Pattern**: Add cairosvg + lxml import probes; on Windows, probe GTK3 DLL presence; print clear remediation on failure
```python
# scripts/verify_toolchain.py — additions
try:
    import cairosvg  # noqa: F401
    import lxml      # noqa: F401
except ImportError as e:
    print(f"FAIL: missing render dep: {e.name}")
    print("  Fix: pip install -r requirements.txt")
    print("  Note: cairosvg requires GTK3 runtime on Windows.")
    print("        Install via: choco install gtk3-runtime-bin-x64")
    sys.exit(1)
```
- **Test**: `python scripts/verify_toolchain.py` → exit 0

#### Task 1.1.3: Implement render_board.py
- **Files**: Create `scripts/render_board.py` (~120 LOC)
- **Pattern**: subprocess kicad-cli → lxml dark-BG inject → cairosvg.svg2png; CLI entry under `if __name__ == "__main__":`
```python
# scripts/render_board.py
DEFAULT_LAYERS = ["Edge_Cuts", "B.Cu", "F.Cu", "F.Mask", "F.SilkS"]
COPPER_LAYERS = ["F.Cu", "B.Cu"]

def render_board(pcb_path, output_dir=None, layers=None, dpi=150, generate_variants=True):
    pcb_path = Path(pcb_path).resolve()
    output_dir = Path(output_dir) if output_dir else pcb_path.parent
    layers = layers or DEFAULT_LAYERS
    svg_path = output_dir / f"{pcb_path.stem}_render.svg"
    subprocess.run([
        "kicad-cli", "pcb", "export", "svg",
        "--mode-single", "--layers", ",".join(layers),
        "--output", str(svg_path), str(pcb_path),
    ], check=True)
    _inject_dark_background(svg_path)
    full_png = output_dir / f"{pcb_path.stem}_full.png"
    cairosvg.svg2png(url=str(svg_path), write_to=str(full_png), scale=dpi/96)
    copper_png = None
    if generate_variants:
        # second pass with COPPER_LAYERS → <stem>_copper.png
        ...
    return {"full": full_png, "copper": copper_png, "svg": svg_path}
```
- **Test**: `python scripts/render_board.py output/blue_pill.kicad_pcb` produces `output/blue_pill_full.png` + `output/blue_pill_copper.png` in <2 s

#### Task 1.1.4: Author render-board tests
- **Files**: Create `tests/test_render_board.py`
- **Pattern**: pytest-timeout for <2 s; sample-pixel check for dark BG
```python
@pytest.mark.timeout(3)
def test_render_blue_pill_under_2s():
    t0 = time.perf_counter()
    result = render_board(Path("output/blue_pill.kicad_pcb"))
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0, f"render took {elapsed:.2f}s, expected <2s"
    assert {"full", "copper", "svg"} == set(result.keys())
    assert result["full"].exists() and result["full"].stat().st_size > 0
    # dark BG check: sample top-left pixel
    img = Image.open(result["full"])
    assert img.getpixel((10, 10))[:3] == (26, 26, 26)  # #1a1a1a
```
- **Test**: `pytest tests/test_render_board.py -v` → all green

#### Task 1.1.5: Author render-pipeline context doc
- **Files**: Create `docs/context/render-pipeline.context.md`
- **Pattern**: Documents module boundary, return dict schema, layer order rationale, speed budget
- **Test**: Manual: doc readable in <30 s

#### Validation Checkpoint — Batch 1.1
```bash
pip install -r requirements.txt
# Expected: clean install of cairosvg, lxml

python scripts/verify_toolchain.py
# Expected: exit 0

pytest tests/test_render_board.py -v
# Expected: all tests green, no warnings about missing kicad-cli/GTK3

python scripts/render_board.py output/blue_pill.kicad_pcb
# Expected: output/blue_pill_full.png + output/blue_pill_copper.png exist, sub-2s wall time
```

### Batch 1.2: Supplier DRC profile system
**Objective**: Schema-first supplier rule subsystem; JLCPCB profile populated from research; `.kicad_dru` emission that KiCad parses without errors.

#### Task 1.2.1: Define Pydantic schema
- **Files**: Create `supplier_profiles/schema.py` (~150 LOC)
- **Pattern**: Pydantic v2 BaseModel hierarchy mirroring the 7 nested rule sections from `research/supplier_drc_research.md`
```python
# See "Data Models / Schemas" section above for full schema
class SupplierProfile(BaseModel):
    metadata: SupplierMetadata
    design_rules: DesignRules
# DesignRules nests: trace_rules, via_rules, pad_rules,
#                    solder_mask_rules, silkscreen_rules, board_rules, cost_premiums
```
- **Test**: `pytest tests/test_supplier_drc.py::test_schema_loads -v` → green

#### Task 1.2.2: Author JLCPCB YAML
- **Files**: Create `supplier_profiles/jlcpcb.yaml`
- **Pattern**: Pull all 18 axes from `research/supplier_drc_research.md` table; use explicit units; include `recommended` where research notes it (annular ring: 0.15 mm value, 0.2 recommended; trace width: 0.127 value, 0.15 recommended)
```yaml
# See "Data Models / Schemas" section above for full YAML
metadata:
  name: "JLCPCB"
  capability_tier: "standard-2layer-fr4"
  last_updated: "2026-05-16"
design_rules:
  trace_rules:
    min_trace_width: { value: 0.127, unit: mm, mil_equiv: 5, recommended: 0.15 }
    ...
```
- **Test**: `pytest tests/test_supplier_drc.py::test_jlcpcb_profile_valid -v` → green

#### Task 1.2.3: Implement loader
- **Files**: Create `scripts/supplier_drc/loader.py`
- **Pattern**: yaml.safe_load → Pydantic validation → return SupplierProfile
```python
def load_supplier_profile(name: str) -> SupplierProfile:
    path = Path(__file__).parent.parent.parent / "supplier_profiles" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No profile: {name} (looked at {path})")
    data = yaml.safe_load(path.read_text())
    return SupplierProfile.model_validate(data)
```
- **Test**: included in `test_supplier_drc.py`

#### Task 1.2.4: Implement DRU emitter
- **Files**: Same `scripts/supplier_drc/loader.py`
- **Pattern**: Map per the KiCad DRU mapping table in `research/supplier_drc_research.md`; document gaps inline as `;;` comments
```python
def emit_kicad_dru(profile: SupplierProfile, out_path: Path) -> Path:
    rules = profile.design_rules
    tw = rules.trace_rules.min_trace_width.value
    cl = rules.trace_rules.min_trace_spacing.value
    ec = rules.trace_rules.copper_to_edge.value
    ar = rules.via_rules.min_annular_ring.value
    vd = rules.via_rules.min_via_drill.value
    slw = rules.silkscreen_rules.min_line_width.value
    sth = rules.silkscreen_rules.min_text_height.value
    body = f'''(version 1)
(rule "Min Trace Width ({profile.metadata.name})" (constraint track_width (min {tw}mm)))
(rule "Min Clearance ({profile.metadata.name})" (constraint clearance (min {cl}mm)) (condition "A.Type == 'track' && B.Type == 'track'"))
(rule "Min Edge Clearance ({profile.metadata.name})" (constraint edge_clearance (min {ec}mm)))
(rule "Min Annular Ring ({profile.metadata.name})" (constraint annular_width (min {ar}mm)) (condition "A.Type == 'via'"))
(rule "Min Via Drill ({profile.metadata.name})" (constraint hole_size (min {vd}mm)) (condition "A.Type == 'via'"))
(rule "Min Silkscreen Line Width ({profile.metadata.name})" (constraint silk_line_width (min {slw}mm)))
(rule "Min Silkscreen Text Height ({profile.metadata.name})" (constraint silk_text_height (min {sth}mm)))
;; GAPS: solder mask clearance (UI-only), non-plated hole min (external),
;;       board thickness + copper weight (metadata, not DRC-checkable)
'''
    out_path.write_text(body)
    return out_path
```
- **Test**: `pytest tests/test_supplier_drc.py::test_emit_dru -v` → green; manual: open in KiCad pcbnew, verify DRC parses without errors

#### Task 1.2.5: Validator stub
- **Files**: Create `scripts/supplier_drc/validators.py`
- **Pattern**: Stub functions raising NotImplementedError for v2.x; document signatures the future implementations will satisfy
```python
def validate_solder_mask_web(board_path: Path, profile: SupplierProfile) -> list[Violation]:
    """v2.x: external check for solder mask web < min_mask_web; DRU cannot express this."""
    raise NotImplementedError("Deferred to v2.x")

def validate_non_plated_holes(board_path: Path, profile: SupplierProfile) -> list[Violation]:
    """v2.x: external check for non-plated hole diameter; DRU cannot express this."""
    raise NotImplementedError("Deferred to v2.x")
```
- **Test**: not exercised in Stage 1; documented existence verified by tests/test_supplier_drc.py via import

#### Task 1.2.6: Package __init__
- **Files**: Create `scripts/supplier_drc/__init__.py`
- **Pattern**: Re-export the two public functions
```python
from .loader import load_supplier_profile, emit_kicad_dru
__all__ = ["load_supplier_profile", "emit_kicad_dru"]
```

#### Task 1.2.7: Supplier-profiles README
- **Files**: Create `supplier_profiles/README.md`
- **Pattern**: Documents schema, how to add a new supplier (PCBWay/OSH Park/Eurocircuits), required fields, validation steps

#### Task 1.2.8: Author supplier-DRC tests
- **Files**: Create `tests/test_supplier_drc.py`
- **Pattern**: 5 named tests per Stage 1 deliverable spec
```python
def test_schema_loads():
    """SupplierProfile model imports and validates a known-good dict."""
def test_jlcpcb_profile_valid():
    """jlcpcb.yaml loads via load_supplier_profile and matches research table values."""
def test_emit_dru(tmp_path):
    """emit_kicad_dru produces a file containing all 7 expected rule lines."""
def test_unknown_supplier_raises():
    """load_supplier_profile('not_a_real_supplier') raises FileNotFoundError."""
def test_malformed_yaml_raises(tmp_path):
    """Loading a YAML with missing required field raises pydantic.ValidationError."""
```
- **Test**: `pytest tests/test_supplier_drc.py -v` → all 5 green

#### Task 1.2.9: Mandatory supplier-DRC rule
- **Files**: Create `agent_docs/rules/supplier-drc-rules.md`
- **Pattern**: Mandatory rule — read supplier from contract metadata, call load_supplier_profile, call emit_kicad_dru BEFORE any routing actions; lists the 5 risk axes (annular ring HIGH, silk-on-pad MEDIUM, trace-to-via MEDIUM, copper-to-edge after auto-outline MEDIUM, solder mask web LOW)

#### Task 1.2.10: Supplier-DRC context doc
- **Files**: Create `docs/context/supplier-drc.context.md`
- **Pattern**: Module boundary; what `supplier_profiles/` is for; what `scripts/supplier_drc/` is for; DRU emission semantics; the 3 documented gaps

#### Validation Checkpoint — Batch 1.2
```bash
pytest tests/test_supplier_drc.py -v
# Expected: 5/5 green

python -c "from scripts.supplier_drc import load_supplier_profile, emit_kicad_dru; from pathlib import Path; p = load_supplier_profile('jlcpcb'); emit_kicad_dru(p, Path('/tmp/test.kicad_dru')); print(open('/tmp/test.kicad_dru').read()[:500])"
# Expected: DRU header + first few (rule ...) lines visible

# Manual: open /tmp/test.kicad_dru in KiCad pcbnew DRC settings, verify it parses without errors
```

### Batch 1.3: 555 LED blinker audition contract
**Objective**: A pure-text contract the agent can build against; supplier metadata declared; "DESIGN FROM THIS CONTRACT ONLY" clause; test suite as audition gate.

#### Task 1.3.1: Author blinker_555_contract.md
- **Files**: Create `contracts/blinker_555_contract.md`
- **Pattern**: Follow `contracts/EXAMPLE_CONTRACT.md` template; required sections — Goal, Design Constraints, Components, Netlist, Success Criteria, "DESIGN FROM THIS CONTRACT ONLY" clause, `supplier: jlcpcb` metadata field
```markdown
---
supplier: jlcpcb
layer_count: 2
board_dimensions: 20x30 mm
fr4_thickness: 1.6 mm
copper_weight: 1 oz
surface_finish: HASL (lead-free)
---

# Contract: 555 LED Blinker

## DESIGN FROM THIS CONTRACT ONLY
No external references. No reference images. Design entirely from this contract + skills + rules + api_manifest + the loaded supplier profile.

## Components (5–7)
| Ref | Part | Footprint | Notes |
|-----|------|-----------|-------|
| U1  | NE555 | DIP-8 | Astable timer |
| R1  | 1k    | 0805  | Charging path |
| R2  | 10k   | 0805  | Discharge path |
| R3  | 470Ω  | 0805  | LED current limit |
| C1  | 10μF  | 0805  | Timing cap |
| C2  | 0.1μF | 0805  | Decoupling, near pin 8 |
| D1  | LED   | 0805  | Output indicator |
| J1  | Power header | 2.54mm pitch | VCC+GND |

## Netlist (~6 nets)
- VCC: U1.8, U1.4, C2.+, R1.A, J1.1
- GND: U1.1, C1.-, C2.-, D1.K (cathode), J1.2
- TRIG: U1.2, U1.6 (THRESHOLD tied), C1.+
- THR: same as TRIG (joined)
- DISCH: U1.7, R2 between R1 and TRIG
- OUT: U1.3, R3.A; R3.B → D1.A

## Success Criteria
- [ ] DRC: 0 errors against emitted supplier_profiles/jlcpcb.yaml DRU
- [ ] All nets routed (no unconnected_items)
- [ ] All components on F.Cu
- [ ] Board within 20×30 mm with ≥0.3 mm copper-to-edge
- [ ] Owner-judged visual: "credible 555 LED blinker"
```
- **Test**: Manual + `pytest tests/test_blinker_555.py -v --collect-only` enumerates checks

#### Task 1.3.2: Author audition test suite
- **Files**: Create `tests/test_blinker_555.py`
- **Pattern**: Mirror `tests/test_blue_pill.py` structure; uses pcbnew fixture to load `output/blinker_555.kicad_pcb`; checks: component count (7), net connectivity, DRC=0/0 against `output/blinker_555.kicad_dru`, board dimensions within 20×30 mm, all components on F.Cu
```python
# tests/test_blinker_555.py — structural skeleton
import pytest, pcbnew
from pathlib import Path

PCB = Path("output/blinker_555.kicad_pcb")

@pytest.fixture(scope="module")
def board():
    if not PCB.exists():
        pytest.skip("Audition not yet executed")
    return pcbnew.LoadBoard(str(PCB))

def test_component_count(board):
    assert len(board.GetFootprints()) == 7
def test_nets_routed(board):
    # walk netlist; assert no unconnected pads
def test_drc_zero(board, tmp_path):
    # run pcbnew DRC against output/blinker_555.kicad_dru → expect 0/0
def test_dimensions(board):
    bbox = board.GetBoardEdgesBoundingBox()
    assert bbox.GetWidth() / 1e6 <= 20.5 and bbox.GetHeight() / 1e6 <= 30.5
def test_components_on_f_cu(board):
    for fp in board.GetFootprints():
        assert fp.GetLayer() == pcbnew.F_Cu
```
- **Test**: `pytest tests/test_blinker_555.py -v --collect-only` enumerates 5 checks

#### Task 1.3.3: Author contracts context doc
- **Files**: Create `docs/context/contracts.context.md`
- **Pattern**: Documents `contracts/` template + per-board metadata fields (supplier, layer_count, dimensions); "DESIGN FROM THIS CONTRACT ONLY" semantics; how new contracts plug in

#### Validation Checkpoint — Batch 1.3
```bash
pytest tests/test_blinker_555.py -v --collect-only
# Expected: 5 tests enumerated, no import errors

# Manual: open contracts/blinker_555_contract.md, verify:
#   - "DESIGN FROM THIS CONTRACT ONLY" clause present
#   - supplier: jlcpcb metadata present
#   - 7-component table parseable
#   - ~6-net netlist parseable
```

### Batch 1.4: 4.6 baselines preservation + API manifest refresh + routing primitives doc
**Objective**: Demote v1's hardcoded board artifacts to `baselines/4.6/` while preserving git history; refresh `api_manifest.json` against KiCad 9.0.7; document what survives unchanged from v1.

#### Task 1.4.1: Create baselines/4.6/ + git mv build script
- **Files**: Create `baselines/4.6/` directory; `git mv scripts/build_blue_pill.py baselines/4.6/build_blue_pill.py`
- **Pattern**: Use `git mv` (not `mv` then `git add`) to preserve blame
- **Test**: `git log --oneline -5 baselines/4.6/build_blue_pill.py` shows pre-move history

#### Task 1.4.2: git mv route script
- **Files**: `git mv scripts/route_blue_pill.py baselines/4.6/route_blue_pill.py`

#### Task 1.4.3: git mv blue_pill PCB + project files
- **Files**: `git mv output/blue_pill.kicad_pcb baselines/4.6/blue_pill.kicad_pcb`; same for `.kicad_pro`, `.kicad_prl`

#### Task 1.4.4: Author baselines README
- **Files**: Create `baselines/4.6/README.md`
- **Pattern**: Document — what these are (Round 2 output from Opus 4.6 on 2026-03-06); status (54/54 tests passing, DRC 0/0, BUT owner-judged goal-failed); purpose in v2 (comparison baseline for Stage 3 stretch test); files manifest
```markdown
# baselines/4.6/

Frozen artifacts from `eda-kicad-agent` Round 2 under **Claude Opus 4.6** (2026-03-06).

## Status
- pytest: **54/54 passing** (commit `4787d57`)
- DRC against v1 ruleset: **0 violations, 0 unconnected** (`drc_report.json`)
- Owner verdict: **goal NOT achieved** — board DRC-clean but not judged credible as a Blue Pill replica.

## Why preserved
These are kept as the **v2 stretch-test baseline**. Stage 3 batch 3.3 (if 555 audition passes) re-runs Blue Pill under v2 architecture and produces a side-by-side visual + checklist comparison in `docs/auditions/blue_pill_v2_vs_4.6_comparison.md`.

## Files
- `build_blue_pill.py` (~370 LOC) — 4.6's hardcoded board builder; demoted from `scripts/`
- `route_blue_pill.py` (~390 LOC) — 4.6's hardcoded router with explicit waypoints; demoted from `scripts/`
- `blue_pill.kicad_pcb` — the DRC-clean Round 2 board
- `blue_pill.kicad_pro` — project file
- `blue_pill.kicad_prl` — local project file

## NOT for re-execution
Do not run these scripts in v2. They embed 4.6's choices; running them replays 4.6's outputs. v2 has no board-specific scripts — `scripts/routing_cli.py` is the generic primitive.
```

#### Task 1.4.5: Author baselines context doc
- **Files**: Create `docs/context/baselines.context.md`
- **Pattern**: Mirror README at module-boundary level (shorter, oriented to "what is this directory for")

#### Task 1.4.6: Author routing-primitives context doc
- **Files**: Create `docs/context/routing-primitives.context.md`
- **Pattern**: Documents what survives unchanged from v1 — `scripts/routing_cli.py` (A* iterative router with JSON I/O), `scripts/routing/{actions,perception,pathfinder}.py`, the 45° angle validation rule, the MCP-routing-tools-BANNED rule (no `route_trace`, `route_pad_to_pad`, `route_differential_pair`); points to `agent_docs/skills/routing-skill.md` for full operational detail

#### Task 1.4.7: Refresh api_manifest
- **Files**: Run `kipython scripts/discover_api.py`; commit refreshed `api_manifest.json`
- **Pattern**: Single command; verify `verified_count == total_count` post-refresh
- **Test**: `python -c "import json; m=json.load(open('api_manifest.json')); print(m.get('verified_count'), '/', m.get('total_count'))"` → `<N> / <N>` with both equal

#### Validation Checkpoint — Batch 1.4
```bash
git log --oneline -10
# Expected: visible "git mv" entries for build_blue_pill, route_blue_pill, blue_pill.*

python -c "import json; m=json.load(open('api_manifest.json')); print(m['verified_count'], m['total_count'])"
# Expected: equal counts (100% verified)

ls baselines/4.6/
# Expected: README.md, build_blue_pill.py, route_blue_pill.py, blue_pill.kicad_pcb, .kicad_pro, .kicad_prl

ls docs/context/
# Expected: 5 .context.md files — render-pipeline, supplier-drc, contracts, baselines, routing-primitives

# Manual: open baselines/4.6/README.md, confirm provenance + status + purpose documented
```

## Constraints
- **Performance**: `render_board()` produces full + copper PNGs in <2 s wall time on the developer's machine (Windows 11, Python 3.11+, KiCad 9.0.7). Enforced by `pytest-timeout`.
- **Performance**: Supplier profile load + DRU emit completes in <100 ms (no perceptible blocking before routing).
- **Security**: No code execution from YAML — `yaml.safe_load` only. Pydantic validation rejects malformed input before any consumer sees it.
- **Convention**: Use `kipython` (KiCad's bundled Python) for any script that imports `pcbnew`. All other scripts use the project venv. Per `agent_docs/rules/coding-rules.md`.
- **Convention**: No new MCP routing tools introduced; v1's "MCP routing BANNED" rule is preserved verbatim in `agent_docs/rules/` and reiterated in `routing-primitives.context.md`.
- **Convention**: Tests under `tests/` use the existing `conftest.py` fixture pattern; new fixtures (render_board result, supplier_profile) added there if cross-test reuse emerges.
- **Convention**: `git mv` for the 4.6 demotion — preserves blame; do not `rm` + `git add`.

## Extension Points
- **Stage 2 visual-review-skill** consumes `scripts/render_board.py` to produce the PNG inputs it critiques. Skill referenced `result['full']` + `result['copper']` paths.
- **Stage 2 pcb-design-skill rewrite** consumes `agent_docs/rules/supplier-drc-rules.md` (mandatory rule: load supplier profile before routing) and the `load_supplier_profile` + `emit_kicad_dru` pair.
- **Stage 3 audition** executes against `contracts/blinker_555_contract.md`; the contract is the input to the entire 8-checkpoint loop.
- **v2.x supplier profile extension**: drop a new YAML in `supplier_profiles/<name>.yaml` matching the Pydantic schema; no code changes needed for the loader/emitter to consume it.
- **v2.x render variant**: add a third entry to `generate_variants` (e.g. components-only with `F.SilkS + Edge_Cuts`) by extending the layer-tuple list in `render_board.py`. No callers break.
- **v2.x external DRC validators**: stubs in `scripts/supplier_drc/validators.py` are already in place — `validate_solder_mask_web`, `validate_non_plated_holes`. Implement to return `list[Violation]`; agent calls them post-route.

## Dependencies
- **Requires**: KiCad 9.0.7 installed (already verified on developer machine); KiCAD-MCP-Server installed and `python scripts/verify_mcp.py` exits 0 (already verified); v1 repo state at HEAD with `output/blue_pill.*` and `scripts/{build,route}_blue_pill.py` present
- **Requires (system)**: GTK3 runtime — install via `choco install gtk3-runtime-bin-x64`, OR follow the manual GTK install path documented in `verify_toolchain.py` error message. Blocks Batch 1.1 if missing.
- **Requires (Python)**: cairosvg>=2.7.0, lxml>=5.0.0, pydantic>=2.0 (likely already in requirements), pyyaml (already in requirements)
- **Produces (for Stage 2)**: `scripts/render_board.py` callable; `scripts/supplier_drc/__init__.py` exporting `load_supplier_profile` + `emit_kicad_dru`; `agent_docs/rules/supplier-drc-rules.md` listed in CLAUDE.md router; `contracts/blinker_555_contract.md` parseable; `baselines/4.6/` populated; refreshed `api_manifest.json`
- **Produces (for Stage 3)**: All Stage 2 prerequisites plus `tests/test_blinker_555.py` collectible (executable in Stage 3 audition); `baselines/4.6/blue_pill.kicad_pcb` available for `scripts/render_board.py` to render during the stretch comparison
- **External**: KiCad CLI (`kicad-cli` on PATH); pip-installed cairosvg + lxml; GTK3 system runtime

## Scope Boundaries
- **In scope**: kicad-cli SVG + cairosvg PNG pipeline with lxml dark-BG injection; YAML + Pydantic v2 supplier schema; JLCPCB profile (only) populated from research; DRU emission of the 7 expressible rules with documented gaps for the 3 unexpressible ones; 555 audition contract with all metadata + checklist; baselines demotion via git mv (preserves history); api_manifest refresh; toolchain verifier extension with GTK3 probe; 5 of 6 `.context.md` files (6th is Stage 2 agent-skills)
- **Deferred to v2.x**:
  - PCBWay / OSH Park / Eurocircuits populated profiles (schema supports them; YAMLs not authored — schema-first investment paid forward)
  - Components-only render variant (3rd PNG view with F.SilkS + Edge_Cuts)
  - Solder mask clearance external checker (`scripts/supplier_drc/validators.py::validate_solder_mask_web` — stub only)
  - Non-plated hole validator (`scripts/supplier_drc/validators.py::validate_non_plated_holes` — stub only)
  - Auto-refresh policy for `api_manifest.json` (currently one-shot at Stage 1 start)
  - pcbnew `PLOT_CONTROLLER` alternative render path (deferred unless cairosvg quality/speed issue surfaces)
  - Cost-premium warnings raised by the loader (loader returns profile only; consumer is responsible for cost-premium analysis if desired)
- **Trigger for promotion (v2.0 → v2.x mid-flight)**:
  - If Batch 1.1 render budget exceeds 2 s on developer machine — switch to PLOT_CONTROLLER alternative path documented in `research/rendering_toolchain_research.md`
  - If JLCPCB DFM rejects an audition output on a rule we don't enforce — implement the relevant `validators.py` stub before re-audition
  - If owner adds a second supplier (e.g. PCBWay) for any production board — populate the YAML; no code changes needed
- **Out of scope entirely**: Iterative build loop architecture (Stage 2); audition execution (Stage 3); `/review-board` repurposing (Stage 2); Blue Pill v2 retry (Stage 3 stretch); cross-session Reflexion memory; web UI / dashboard
