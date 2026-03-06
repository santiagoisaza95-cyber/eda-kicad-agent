# Trace Routing Skill

Rules for routing traces on a KiCad PCB. Based on IPC-2221, ST AN2867, and professional 2-layer layout practices.

---

## IMPORTANT: Bypass MCP for Routing

The KiCAD MCP Server's `route_trace` tool creates only single straight-line segments with no pathfinding, no obstacle avoidance, and no clearance checking. **Do NOT use MCP routing tools for trace routing.**

Instead, use the **routing workbench CLI** (`scripts/routing_cli.py`) which provides an A* pathfinder, obstacle awareness, 45° angle enforcement, and immediate DRC feedback. See the "Routing Workbench" section below.

**Do NOT write large Python routing scripts with raw pcbnew calls.** The workbench handles all trace/via/zone creation with proper validation. Route one net at a time using the CLI iteratively.

You MAY still use MCP tools for: placement, DRC, export, library search, JLCPCB parts.

---

## Routing Workbench (MANDATORY for all trace routing)

Instead of writing large routing scripts that place traces blindly, use the **routing workbench CLI** iteratively. Each call gives you real-time feedback on the board state.

### Available Commands

The workbench runs at `scripts/routing_cli.py` using the KiCad bundled Python from `config.json`.

**Perception (read board state):**
```bash
# Board overview
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action summary

# Which nets need routing
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action unrouted

# Pad positions for a specific net
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action net_pads --net HSE_IN

# Obstacles in a region (components, traces, vias)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action obstacles --bbox 10,5,25,15
```

**Pathfinding (A* finds obstacle-avoiding path):**
```bash
# Find a path between two points
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action find_path --start 15,10 --end 22,14 --width 0.25
```

The A* pathfinder returns waypoints that naturally use 45° angles. You can accept the path as-is or modify the waypoints.

**Routing actions (modify board with feedback):**
```bash
# Route a trace (validates 45° angles, rejects 90° bends)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action route --net HSE_IN --waypoints "15,10;18,12;22,14" --width 0.25 --layer F.Cu

# Place a via
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action via --net GND --pos 10,12

# Undo last action
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action undo

# Rip up all traces for a net
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action rip_up --net HSE_IN

# Add ground zone
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action zone --net GND --layer B.Cu --priority 0

# Fill all zones
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action fill_zones

# Run DRC and get violations + unconnected count
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action drc
```

### Routing Workflow with Workbench

Follow this loop for each net:

1. **Check what needs routing:** `--action unrouted`
2. **Get pad positions:** `--action net_pads --net <name>`
3. **Check nearby obstacles:** `--action obstacles --bbox <around the pads>`
4. **Find a path:** `--action find_path --start <pad1> --end <pad2> --width <w>`
5. **Route the trace:** `--action route --net <name> --waypoints <from find_path> --width <w>`
6. **Check DRC:** `--action drc`
7. If violations: `--action undo` or `--action rip_up`, adjust, retry
8. Repeat for next net

### Routing Priority (use this order)

1. Crystal (HSE_IN, HSE_OUT) — route first while board is empty
2. USB differential pair (USB_D+, USB_D-)
3. Reset (NRST)
4. I2C (SDA, SCL)
5. USART and remaining signals
6. Power traces (3.3V, VBUS, 3.3VA) — wider traces
7. Ground zones (last)

---

## Layer Strategy (2-Layer Board)

This is non-negotiable for 2-layer designs:

```
F.Cu (Top):    ALL components + ALL signal traces + ALL power traces
B.Cu (Bottom): SOLID GND pour — keep >80% unbroken copper
```

- Route everything on F.Cu. Only cross to B.Cu when you must jump over another trace.
- Every via punches through the ground plane — minimize vias to keep the plane solid.
- The bottom ground plane gives every trace a continuous return path directly underneath.

---

## Routing Order (Priority)

Route nets in this exact order. Earlier signals get the cleanest paths while the board is still empty.

### 1. Crystal Oscillator (HSE_IN, HSE_OUT)
- Route FIRST while board is empty
- Traces must be short (<10mm each), equal length, symmetric
- No vias in crystal path — stay entirely on F.Cu
- No other signals routed under or adjacent to the crystal area
- Add a GND guard ring: copper trace on F.Cu tied to GND surrounding the crystal, both load caps, and the traces to MCU. Stitch the guard ring to B.Cu ground plane with vias every 2-3mm
- Trace width: 0.25mm (10 mil)

### 2. USB Differential Pair (USB_D+, USB_D-)
- Route as a parallel pair with consistent spacing
- Trace width: 0.24mm (9.5 mil) for 90-ohm differential impedance on 1.6mm FR4
- Pair gap: 0.127mm (5 mil) between D+ and D-
- Length match: max 3.8mm skew between D+ and D-
- Total length: keep under 50mm (MCU to connector)
- No vias — stay entirely on F.Cu
- Minimum 0.75mm (30 mil) spacing to any other signal
- 45-degree bends only; match both traces at each bend
- Series resistors (if present) placed near MCU pins, not near connector
- Unbroken ground plane on B.Cu underneath the entire USB run

### 3. Reset Line (NRST)
- Short, direct trace from MCU to filter cap and any reset header
- Keep away from high-speed signals (USB, crystal, SPI CLK)
- Trace width: 0.25mm
- No special impedance requirements

### 4. I2C Bus (SDA, SCL)
- Route SDA and SCL as a parallel pair, close together
- Pull-up resistors near the bus master (MCU)
- If crossing other signals, cross at 90 degrees
- Trace width: 0.25mm
- No length matching required (level-based protocol)

### 5. USART and Remaining Signals
- Standard point-to-point routing
- Trace width: 0.25mm
- 45-degree angles
- Route last — they're the most flexible

### 6. Power Traces (3.3V, VBUS, 3.3VA)
- Route AFTER signals (signals need clean paths, power is more forgiving)
- Trace width: 0.5mm minimum (20 mil) — handles up to 3A on external 1oz copper
- Star topology from regulator output to each VDD pin
- For analog supply (VDDA/3.3VA): route through ferrite bead, keep separate from digital 3.3V

### 7. Ground Pour (LAST)
- Create GND zone covering entire B.Cu — this is the last step
- Create GND zone on F.Cu filling all remaining empty space
- Fill zones after all routing is complete

---

## Trace Width Table (IPC-2221, 1oz Copper, External)

| Signal Type | Width | Current Capacity (10C rise) |
|-------------|-------|-----------------------------|
| General signal | 0.25mm (10 mil) | ~1A |
| Minimum signal | 0.15mm (6 mil) | ~0.5A |
| Power (3.3V, 5V) | 0.50mm (20 mil) | ~3A |
| High current | 1.00mm (40 mil) | ~5A |
| USB D+/D- | 0.24mm (9.5 mil) | Impedance-set, not current |
| Crystal | 0.25mm (10 mil) | Negligible current |

Quick rule: ~10 mils per amp for external 1oz copper, 10C temperature rise.

---

## Via Standards

| Parameter | Standard | Signal (dense areas) |
|-----------|----------|---------------------|
| Pad diameter | 0.6mm (24 mil) | 0.5mm (20 mil) |
| Drill diameter | 0.3mm (12 mil) | 0.25mm (10 mil) |
| Annular ring | 0.15mm (6 mil) | 0.125mm (5 mil) |
| Current per via | ~1.5A (10C rise) | ~1A |

### Via Placement Rules
- **Decoupling cap ground:** Via goes immediately at the cap's GND pad, then down to B.Cu ground plane. The via goes AFTER the cap — never between IC and cap (adds inductance to the decoupling loop)
- **IC ground pins:** One via per VSS/GND pin, within 1mm of the pin, down to B.Cu ground plane
- **Layer transition:** When a trace must jump over another trace, use a via pair (down to B.Cu, cross underneath, via back up to F.Cu). Minimize these — each via breaks the ground plane
- **Ground stitching:** Place vias every 10-15mm around the board perimeter and near ground pour islands to connect F.Cu ground copper to B.Cu ground plane

### Where NOT to Put Vias
- In the crystal signal path
- In the USB differential pair path
- Inside IC pad areas (via-in-pad requires special fill process)
- Closer than 0.3mm to any SMD pad edge

---

## Multi-Segment Routing (How to Route Around Obstacles)

**Use the routing workbench CLI** — do NOT write raw pcbnew routing scripts. The workbench handles multi-segment routing, 45° angle enforcement, and obstacle avoidance automatically:

```bash
# Step 1: Find an obstacle-avoiding path (A* pathfinder, 45° native)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action find_path --start 15,10 --end 22,14 --width 0.25

# Step 2: Route using the returned waypoints
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action route --net HSE_IN --waypoints "15,10;18.5,12.5;22,14" --width 0.25 --layer F.Cu
```

The `--action route` command validates all angles before placing traces. If you pass waypoints with a 90° bend, it returns an error immediately — you must fix the waypoints.

---

## EMC Ground Rules (MANDATORY)

### Rule 1: Every Empty Space is GND
All copper areas not used by traces, pads, or other nets MUST be filled with GND copper pour. This applies to BOTH layers:
- **B.Cu:** Full-board GND zone (priority 0) — the primary ground plane
- **F.Cu:** GND zone (priority 1) filling all remaining space after traces are routed

No empty copper-free areas larger than necessary. Ground copper absorbs EMI, provides return paths, and improves thermal performance.

### Rule 2: No Floating Copper Islands
After zone filling, there MUST be zero unconnected copper islands. Every piece of copper must be connected to its net (almost always GND).

Isolated copper islands act as antennas — they radiate EMI and cause noise. The standard fix is **GND stitching vias**: small drills that connect the F.Cu GND copper through to the B.Cu GND plane, turning isolated islands into connected ground fill.

**How to eliminate islands:**
1. Fill zones
2. Run DRC — check for "island" or "isolated copper" warnings
3. For each isolated island on F.Cu: place a GND stitching via inside the island. The via connects the F.Cu copper through to the B.Cu ground plane, making it part of the ground network. The via must not interfere with existing traces or pads (place it in open copper area)
4. For islands too small to fit a via (< 1mm²): remove them entirely
5. Re-fill zones after adding stitching vias
6. Repeat until zero islands remain

The workbench `--action zone` command automatically sets island removal mode. After placing stitching vias, re-fill zones:
```bash
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action fill_zones
```

### Rule 3: Ground Stitching Vias (Proactive)
Don't wait for islands to appear — proactively place GND stitching vias to interconnect the F.Cu and B.Cu ground layers. This is standard practice on every professional board:

- **Board perimeter:** Every 10-15mm around the edges
- **Near IC ground pads:** One via per VSS pin, within 1mm
- **Crystal guard ring:** Every 2-3mm along the ring
- **Between signal trace corridors:** Wherever F.Cu has GND copper between traces, drop a stitching via to tie it to B.Cu
- **Near connectors:** 2-3 vias near each connector ground pin

These vias are small (0.5mm pad, 0.25mm drill), carry no signal current, and their only job is to stitch the two ground layers together for low-impedance return paths and EMC performance.

Use the workbench CLI to place stitching vias:
```bash
# Place a GND stitching via at position (x, y)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action via --net GND --pos 10,12

# Repeat for each stitching via position around the perimeter, near ICs, and crystal guard ring
```

### Rule 4: Thermal Relief on Through-Hole Pads
Through-hole pads connected to ground plane MUST use thermal relief (4 spokes):
- Spoke width: 0.25mm (10 mil)
- Gap: 0.25mm (10 mil)
- Without thermal relief, the ground plane sinks all heat and the pin cannot be soldered

SMD pads connected to ground: use direct connect (no thermal relief needed — soldered by reflow).

---

## Decoupling Loop Optimization

The decoupling current loop must be as small as possible:

```
CORRECT:
  MCU VDD pin ──short trace──> Cap pad 1
  Cap pad 2 ──via──> B.Cu GND plane
  MCU VSS pin ──via──> B.Cu GND plane
  (tiny loop: VDD → cap → via → plane → via → VSS)

WRONG:
  MCU VDD pin ──via──> trace ──> Cap pad 1
  (via between IC and cap adds inductance to the loop)
```

- One 100nF per VDD pin, within 2mm
- One bulk cap (4.7-10uF) per MCU, within 10mm
- Smallest value capacitor closest to the pin

---

## Zone Creation and Fill

Use the workbench CLI to create zones and fill them:
```bash
# Create B.Cu GND zone (full board, priority 0)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action zone --net GND --layer B.Cu --priority 0

# Create F.Cu GND zone (fill remaining space, priority 1)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action zone --net GND --layer F.Cu --priority 1

# Fill all zones (do this LAST, after all traces are routed)
"C:/Program Files/KiCad/9.0/bin/python.exe" scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action fill_zones
```

---

## Routing Geometry Rules

### Angles
- **Always 45 degrees.** No 90-degree bends.
- 90-degree corners create acid traps during etching and minor impedance bumps
- For USB differential pairs: 45-degree bends with both traces bending together

### Trace Spacing
| Pair | Minimum Clearance |
|------|------------------|
| Trace to trace (same net class) | 0.2mm (8 mil) |
| Trace to via pad | 0.2mm (8 mil) |
| Trace to board edge | 0.5mm (20 mil) |
| USB pair to other signals | 0.75mm (30 mil) |
| Trace to through-hole pad | 0.25mm (10 mil) |

### Avoid
- Traces under crystals or oscillators
- Long parallel traces (crosstalk) — if unavoidable, separate by 3x trace width
- Stubs on high-speed nets (unterminated transmission line reflections)
- Traces crossing ground plane splits (return current detour = antenna)
- Routing on B.Cu unless jumping over an obstacle (preserve ground plane)

---

## Post-Routing Checklist

Before moving to DRC:
- [ ] ALL nets from contract are routed — every pad pair has copper between them
- [ ] Trace count > 0 (if you have zero traces, routing was skipped)
- [ ] Crystal traces: short, symmetric, guard ring with stitching vias
- [ ] USB traces: parallel pair, length-matched within 3.8mm, no vias
- [ ] Power traces >= 0.5mm width
- [ ] Signal traces >= 0.25mm width
- [ ] No 90-degree bends
- [ ] Decoupling cap vias placed AFTER cap (not between IC and cap)
- [ ] GND zone on B.Cu covering entire board
- [ ] GND zone on F.Cu filling remaining empty space
- [ ] Zones filled (filler.Fill called)
- [ ] Zero floating copper islands
- [ ] Ground stitching vias placed (perimeter + near ICs)
- [ ] DRC: 0 violations AND 0 unconnected items

---

## Future Compatibility Note

This skill is generic — it applies to any 2-layer PCB designed through this agent, not just a specific board. The routing order, trace widths, via standards, EMC rules, and ground strategy are universal for 2-layer designs with MCU + USB + I2C + USART + crystal circuits. For 4+ layer boards, the layer strategy changes but the routing principles remain the same.
