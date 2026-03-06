# KiCad 9.x pcbnew SWIG API Skill

> **IMPORTANT**: Every snippet below is based on KiCad 9.x pcbnew SWIG bindings.
> SWIG names change between KiCad versions. Before using ANY function:
> 1. Check `api_manifest.json` — if the function is listed as "missing", do NOT use it.
> 2. If unsure, STOP and use the `/research-api` command before implementing.
> 3. All paths come from `config.json` — NEVER hardcode machine-specific paths.

## API Verification Status

Run `python scripts/discover_api.py` to regenerate `api_manifest.json` after any KiCad update.
Functions marked `UNVERIFIED` below have not been confirmed against your local installation.

---

## Setup — Headless Import

```python
# On Windows, pcbnew requires kigadgets bridge or KiCad's bundled Python.
# See TOOLCHAIN_NOTES.md for which method works on your machine.
import pcbnew
```

## Core Objects

### Create a New Board

```python
board = pcbnew.BOARD()  # UNVERIFIED — confirm via api_manifest.json
```

### Load / Save Board

```python
# Load existing board
board = pcbnew.LoadBoard("path/to/board.kicad_pcb")  # UNVERIFIED

# Save board
pcbnew.SaveBoard("path/to/board.kicad_pcb", board)  # UNVERIFIED
```

### Unit Conversion

KiCad internally uses nanometers. Always convert:

```python
mm_value = pcbnew.FromMM(10.0)   # 10mm → internal units (nanometers)  # UNVERIFIED
back = pcbnew.ToMM(mm_value)     # internal units → mm                  # UNVERIFIED
```

**CRITICAL**: Never pass raw numbers to position/size setters. Always wrap with `FromMM()`.

---

## Board Outline

Draw the board edge on the `Edge_Cuts` layer using `PCB_SHAPE`:

```python
# UNVERIFIED — verify PCB_SHAPE and Edge_Cuts exist in api_manifest.json
shape = pcbnew.PCB_SHAPE(board)
shape.SetShape(pcbnew.SHAPE_T_RECT)   # UNVERIFIED — shape enum name may differ
shape.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(0), pcbnew.FromMM(0)))
shape.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(40)))
shape.SetLayer(pcbnew.Edge_Cuts)
shape.SetWidth(pcbnew.FromMM(0.05))
board.Add(shape)
```

**Alternative**: Draw 4 line segments for the outline:

```python
# UNVERIFIED
corners = [(0, 0), (50, 0), (50, 40), (0, 40)]
for i in range(4):
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)  # UNVERIFIED
    x1, y1 = corners[i]
    x2, y2 = corners[(i + 1) % 4]
    seg.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
    seg.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
    seg.SetLayer(pcbnew.Edge_Cuts)
    seg.SetWidth(pcbnew.FromMM(0.05))
    board.Add(seg)
```

---

## Footprint Loading

Load footprints from the KiCad library. The footprint library path comes from `config.json`.

```python
import json
from pathlib import Path

# Read config for footprint path
config = json.loads(Path("config.json").read_text())
fp_lib_path = config["footprint_library_path"]

# UNVERIFIED — the IO class name may differ in KiCad 9
# Check api_manifest.json footprint_io section for the correct class
io = pcbnew.PCB_IO_KICAD_SEXPR()  # UNVERIFIED — might be PCB_IO_KICAD or PCB_IO

# Load a footprint from a .pretty library
fp = io.FootprintLoad(
    str(Path(fp_lib_path) / "Package_QFP.pretty"),
    "TQFP-32_7x7mm_P0.8mm"
)
fp.SetReference("U1")
fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25), pcbnew.FromMM(20)))
board.Add(fp)
```

### Common Footprint Libraries

| Component | Library | Footprint |
|-----------|---------|-----------|
| STM32 QFP | `Package_QFP.pretty` | `TQFP-32_7x7mm_P0.8mm` |
| Bypass cap | `Capacitor_SMD.pretty` | `C_0402_1005Metric` |
| Resistor | `Resistor_SMD.pretty` | `R_0402_1005Metric` |
| USB Micro-B | `Connector_USB.pretty` | `USB_Micro-B_Molex_47346-0001` |
| Crystal | `Crystal.pretty` | `Crystal_SMD_3215-2Pin_3.2x1.5mm` |

---

## Nets

### Create and Assign Nets

```python
# UNVERIFIED — verify NETINFO_ITEM exists
netinfo = pcbnew.NETINFO_ITEM(board, "VCC")
board.Add(netinfo)

# Get net by name after adding
net = board.GetNetInfo().GetNetItem("VCC")  # UNVERIFIED — method name may differ

# Assign net to a pad
for pad in fp.Pads():
    if pad.GetName() == "1":  # Pin 1
        pad.SetNet(net)
```

### Standard Net Names

| Net | Purpose |
|-----|---------|
| `VCC` | Power supply (3.3V) |
| `GND` | Ground |
| `NRST` | MCU reset (active low) |
| `USB_DP` | USB D+ |
| `USB_DM` | USB D- |
| `OSC_IN` | Crystal oscillator input |
| `OSC_OUT` | Crystal oscillator output |

---

## Traces (Routing)

> **DO NOT copy-paste this code for routing.** Use the routing workbench CLI (`scripts/routing_cli.py --action route`) which handles pathfinding, 45° angle validation, and DRC feedback. This section is API reference only.

```python
# UNVERIFIED — verify PCB_TRACK exists
track = pcbnew.PCB_TRACK(board)
track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(10), pcbnew.FromMM(10)))
track.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(20), pcbnew.FromMM(10)))
track.SetWidth(pcbnew.FromMM(0.25))  # 0.25mm signal trace
track.SetLayer(pcbnew.F_Cu)
track.SetNet(net)
board.Add(track)
```

### Via

```python
# UNVERIFIED — verify PCB_VIA exists
via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(15), pcbnew.FromMM(15)))
via.SetDrill(pcbnew.FromMM(0.3))
via.SetWidth(pcbnew.FromMM(0.6))  # Via pad diameter
via.SetNet(net)
board.Add(via)
```

---

## Silkscreen Text

```python
# UNVERIFIED — verify PCB_TEXT and F_SilkS exist
text = pcbnew.PCB_TEXT(board)
text.SetText("My Board v1.0")
text.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25), pcbnew.FromMM(2)))
text.SetLayer(pcbnew.F_SilkS)
text.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1), pcbnew.FromMM(1)))
board.Add(text)
```

---

## Zones (Copper Pour / Ground Plane)

> **DO NOT copy-paste this code for zone creation.** Use the routing workbench CLI (`scripts/routing_cli.py --action zone`) which handles zone outline, island removal, and fill. This section is API reference only.

```python
# UNVERIFIED — verify ZONE exists
zone = pcbnew.ZONE(board)
zone.SetNet(board.GetNetInfo().GetNetItem("GND"))
zone.SetLayer(pcbnew.B_Cu)

# Define zone outline
outline = zone.Outline()
outline.NewOutline()
outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(0))
outline.Append(pcbnew.FromMM(50), pcbnew.FromMM(0))
outline.Append(pcbnew.FromMM(50), pcbnew.FromMM(40))
outline.Append(pcbnew.FromMM(0), pcbnew.FromMM(40))

board.Add(zone)

# Fill zones
filler = pcbnew.ZONE_FILLER(board)  # UNVERIFIED
filler.Fill(board.Zones())
```

---

## DRC (Design Rule Check)

Prefer `kicad-cli` for DRC (see `drc-rules.md`). Programmatic DRC:

```python
# UNVERIFIED — DRC API may vary
# Preferred: use kicad-cli instead
# kicad-cli pcb drc --output report.json board.kicad_pcb
```

---

## Known API Gotchas

| Issue | Detail |
|-------|--------|
| **Shape enums** | `SHAPE_T_RECT`, `SHAPE_T_SEGMENT` etc. may be named differently in KiCad 9. Check `dir(pcbnew)` for `SHAPE_T_*` constants. |
| **Footprint IO class** | Was `PLUGIN` in KiCad 7, `PCB_IO_KICAD_SEXPR` in KiCad 8. May have changed again in KiCad 9. Check `api_manifest.json` `footprint_io` section. |
| **VECTOR2I** | KiCad 9 uses `VECTOR2I` for positions. Earlier versions used `wxPoint`. If `VECTOR2I` is missing, try `wxPoint`. |
| **Net assignment** | `board.GetNetInfo().GetNetItem()` method name may differ. Alternatives: `FindNet()`, `GetNet()`. |
| **Layer names** | `F_SilkS` may be `F_Silkscreen` in KiCad 9. Check `api_manifest.json`. |
| **Zone filling** | `ZONE_FILLER` may require different arguments. Test with a simple zone first. |

---

## Escape Hatch

**If you are unsure about ANY API function:**
1. Check `api_manifest.json` first
2. If not in manifest or marked missing, run `/research-api {function_name}`
3. NEVER guess API names — wrong names produce silent failures or crashes
