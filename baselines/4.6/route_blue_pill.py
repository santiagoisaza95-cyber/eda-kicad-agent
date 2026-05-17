#!/usr/bin/env python3
"""Route the Blue Pill board — v8.

Complete rewrite for updated component positions:
  J1 at (43,2) rotation 0 — pins at y=2,4,6,8
  J4 at (42,10) rotation 0 — pins at y=10,12,14,16
  R2 at (20,3) rotation 0 — pads at (19.49,3) and (20.51,3)

Design rules: 0.3mm trace, 0.2mm clearance, 0.6mm via pad, 0.3mm via drill.
Half-trace = 0.15mm, half-via-pad = 0.30mm.
"""
import sys
from pathlib import Path
import pcbnew

PROJECT_ROOT = Path(__file__).resolve().parent.parent
board_path = str(PROJECT_ROOT / "output" / "blue_pill.kicad_pcb")
board = pcbnew.LoadBoard(board_path)
if board is None:
    print("ERROR: Could not load board", file=sys.stderr)
    sys.exit(1)

mm = pcbnew.FromMM

def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))

def trace(net_name, points, width=0.3, layer="F.Cu"):
    net = board.GetNetInfo().GetNetItem(net_name)
    if net is None:
        print(f"  WARNING: Net '{net_name}' not found", file=sys.stderr)
        return
    layer_id = board.GetLayerID(layer)
    for i in range(len(points) - 1):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pt(points[i][0], points[i][1]))
        t.SetEnd(pt(points[i + 1][0], points[i + 1][1]))
        t.SetWidth(mm(width))
        t.SetLayer(layer_id)
        t.SetNet(net)
        board.Add(t)

def add_via(net_name, x, y, drill=0.3, pad=0.6):
    net = board.GetNetInfo().GetNetItem(net_name)
    if net is None:
        return
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pt(x, y))
    v.SetDrill(mm(drill))
    v.SetWidth(mm(pad))
    v.SetNet(net)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    board.Add(v)

print("Routing Blue Pill board (v8)...")

# ═══════════════════════════════════════════════════════════════
# 1. PWR_LED_K: D1.1(4.21,21.5) → R1.1(7.49,21.5)
#    Straight F.Cu — same y level
trace("PWR_LED_K", [(4.21, 21.5), (7.49, 21.5)])

# ═══════════════════════════════════════════════════════════════
# 2. VBUS: C1.1(1.05,19.5) → J3.1(2.2,10.1) → U1.3(3.85,6.8)
#    F.Cu left edge. Wide trace for power.
trace("VBUS", [
    (1.05, 19.5), (1.05, 11.25), (2.2, 10.1)
], width=0.5)
trace("VBUS", [
    (2.2, 10.1), (2.2, 8.45), (3.85, 6.8)
], width=0.5)

# ═══════════════════════════════════════════════════════════════
# 3. USB_D-: J3.2(2.85,10.1) → U2.32(26.41,11.25)
#    B.Cu east — straight run, no F.Cu obstacles matter.
#    Via near J3, B.Cu east, via near MCU.
add_via("USB_D-", 3.5, 11.5)
trace("USB_D-", [(2.85, 10.1), (3.5, 10.7), (3.5, 11.5)], width=0.25)
trace("USB_D-", [(3.5, 11.5), (25.5, 11.5)], layer="B.Cu", width=0.25)
add_via("USB_D-", 25.5, 11.5)
trace("USB_D-", [(25.5, 11.5), (26.41, 11.25)], width=0.25)

# ═══════════════════════════════════════════════════════════════
# 4. USB_D+: J3.3(3.5,10.1) → R3.2(11.01,18.5) → U2.33(26.41,10.75)
#    J3.3 → south to R3.2 via F.Cu along left side
#    R3.2 → via → B.Cu east to MCU area → via → F.Cu to U2.33
trace("USB_D+", [
    (3.5, 10.1), (3.5, 14.0), (6.0, 16.5), (6.0, 18.5), (11.01, 18.5)
], width=0.25)
add_via("USB_D+", 11.5, 18.0)
trace("USB_D+", [(11.01, 18.5), (11.5, 18.0)], width=0.25)
trace("USB_D+", [(11.5, 18.0), (25.5, 10.75)], layer="B.Cu", width=0.25)
add_via("USB_D+", 25.5, 10.75)
trace("USB_D+", [(25.5, 10.75), (26.41, 10.75)], width=0.25)

# ═══════════════════════════════════════════════════════════════
# 5. HSE_IN: C3.1(10.02,9.5) → Y1.1(13.4,12.35) → U2.5(18.09,11.25)
#    C3.1 → F.Cu south to y=12.35, east to Y1.1
#    Y1.1 → via → B.Cu east under Y1 → via → U2.5
trace("HSE_IN", [
    (10.02, 9.5), (10.02, 12.35), (13.4, 12.35)
])
add_via("HSE_IN", 13.4, 13.0)
trace("HSE_IN", [(13.4, 12.35), (13.4, 13.0)])
trace("HSE_IN", [(13.4, 13.0), (17.5, 11.25)], layer="B.Cu")
add_via("HSE_IN", 17.5, 11.25)
trace("HSE_IN", [(17.5, 11.25), (18.09, 11.25)])

# ═══════════════════════════════════════════════════════════════
# 6. HSE_OUT: C4.1(10.02,13.5) → Y1.3(15.6,10.65) → U2.6(18.09,11.75)
#    C4.1 → via → B.Cu east to Y1.3 area → via → F.Cu to both Y1.3 and U2.6
add_via("HSE_OUT", 10.02, 14.0)
trace("HSE_OUT", [(10.02, 13.5), (10.02, 14.0)])
trace("HSE_OUT", [(10.02, 14.0), (15.6, 10.65)], layer="B.Cu")
add_via("HSE_OUT", 15.6, 10.0)
trace("HSE_OUT", [(15.6, 10.65), (15.6, 10.0)], layer="B.Cu")
trace("HSE_OUT", [(15.6, 10.0), (17.5, 11.75)], layer="F.Cu")
trace("HSE_OUT", [(17.5, 11.75), (18.09, 11.75)])

# ═══════════════════════════════════════════════════════════════
# 7. NRST: C5.1(15.02,18.5) → U2.7(18.09,12.25)
#    Via near C5, B.Cu to inside MCU footprint, via, F.Cu west to MCU pad.
add_via("NRST", 15.02, 17.5)
trace("NRST", [(15.02, 18.5), (15.02, 17.5)])
trace("NRST", [(15.02, 17.5), (19.5, 12.25)], layer="B.Cu")
add_via("NRST", 19.5, 12.25)
trace("NRST", [(19.5, 12.25), (18.09, 12.25)])

# ═══════════════════════════════════════════════════════════════
# 8. SWDIO: U2.34(26.41,10.25) → J4.2(42,12)
#    F.Cu east from MCU, south jog to y=12.
trace("SWDIO", [
    (26.41, 10.25), (28.0, 10.25), (29.0, 11.25),
    (40.5, 11.25), (41.25, 12.0), (42.0, 12.0)
])

# ═══════════════════════════════════════════════════════════════
# 9. SWCLK: U2.37(25.0,7.84) → J4.3(42,14)
#    F.Cu north to y=6.5, east to x=40, via, B.Cu south to J4.3
trace("SWCLK", [
    (25.0, 7.84), (25.0, 6.5), (40.0, 6.5)
])
add_via("SWCLK", 40.0, 6.5)
trace("SWCLK", [
    (40.0, 6.5), (40.0, 14.0), (42.0, 14.0)
], layer="B.Cu")

# ═══════════════════════════════════════════════════════════════
# 10. USART1_TX: U2.42(22.5,7.84) → J1.2(43,4)
#     F.Cu north to y=4, east to J1.2.
#     R2.2 at (20.51,3) — pad extends x=20.26 to 20.76, y=2.73 to 3.27.
#     Trace at x=22.5 is well east. Clear.
trace("USART1_TX", [
    (22.5, 7.84), (22.5, 4.0), (43.0, 4.0)
])

# ═══════════════════════════════════════════════════════════════
# 11. USART1_RX: U2.43(22.0,7.84) → J1.3(43,6)
#     F.Cu north at x=22.0 to y=6, east to J1.3.
#     TX trace at y=4 doesn't interfere. R2 at x≈20, clear.
trace("USART1_RX", [
    (22.0, 7.84), (22.0, 6.0), (43.0, 6.0)
])

# ═══════════════════════════════════════════════════════════════
# 12. BOOT0: R2.2(20.51,3.0) → U2.44(21.5,7.84)
#     Via near R2.2, B.Cu south under traces, via near MCU, F.Cu to pad.
#     TX at x=22.5 and RX at x=22.0 are F.Cu — B.Cu is clear underneath.
add_via("BOOT0", 21.0, 3.0)
trace("BOOT0", [(20.51, 3.0), (21.0, 3.0)])
trace("BOOT0", [(21.0, 3.0), (21.0, 7.3)], layer="B.Cu")
add_via("BOOT0", 21.0, 7.3)
trace("BOOT0", [(21.0, 7.3), (21.5, 7.84)])

# ═══════════════════════════════════════════════════════════════
# 13. SW_BOOT0: R2.1(19.49,3.0) → SW1.2(32.75,1.07)
#     F.Cu: south to y=1.5, east to SW1.2 area.
#     SW1.1 GND at (29.75,1.07). Trace at y=1.5, edge=1.35. SW1.1 pad top ≈ 0.57.
#     Gap = 1.35 - 0.57 = 0.78. OK.
trace("SW_BOOT0", [
    (19.49, 3.0), (19.49, 1.5), (32.75, 1.5), (32.75, 1.07)
])

# ═══════════════════════════════════════════════════════════════
# 14. I2C2_SCL: U2.21(23.5,16.16) → RP_SCL1.2(38.01,17.5) → J2.2(42,19)
#     F.Cu south from MCU bottom pad at y=16.16, east along y=17.5 to pullup, then to J2.
trace("I2C2_SCL", [
    (23.5, 16.16), (23.5, 17.5), (38.01, 17.5)
])
trace("I2C2_SCL", [
    (38.01, 17.5), (42.0, 17.5), (42.0, 19.0)
])

# ═══════════════════════════════════════════════════════════════
# 15. I2C2_SDA: U2.22(24.0,16.16) → RP_SDA1.1(36.99,20) → J2.3(42,21)
#     Need to avoid SCL trace at y=17.5.
#     F.Cu south to y=16.7, via, B.Cu south to y=20, via, F.Cu east to pullup.
#     Then F.Cu east to J2.3.
add_via("I2C2_SDA", 24.0, 17.0)
trace("I2C2_SDA", [(24.0, 16.16), (24.0, 17.0)])
trace("I2C2_SDA", [(24.0, 17.0), (24.0, 20.0), (36.99, 20.0)], layer="B.Cu")
add_via("I2C2_SDA", 36.99, 20.0)
trace("I2C2_SDA", [(36.99, 20.0), (42.0, 20.0), (42.0, 21.0)])

# ═══════════════════════════════════════════════════════════════
# 16. +3.3VA: FB1.1(13.71,16.5) → C11.1(9.52,16) → C12.1(7.52,20.5) → U2.9(18.09,13.25)
#     FB1.1 → west to C11, C11 → south to C12, FB1 → east to U2.9
trace("+3.3VA", [(13.71, 16.5), (9.52, 16.5), (9.52, 16.0)])
trace("+3.3VA", [(9.52, 16.0), (7.52, 16.0), (7.52, 20.5)])
trace("+3.3VA", [
    (13.71, 16.5), (16.5, 13.25), (18.09, 13.25)
])

# ═══════════════════════════════════════════════════════════════
# 17. +3.3V: Complex power net — 21 pads.
#     Strategy: F.Cu backbone from U1.2(10.15,4.5) east to MCU area.
#     B.Cu backbone at y≈9.0 for east side distribution.
#     Local stubs to each pad.

# --- U1.2(10.15,4.5) → C2.1(12.55,4.5): F.Cu east at y=4.5
trace("+3.3V", [(10.15, 4.5), (12.55, 4.5)])

# --- C2.1(12.55,4.5) → C6.1(12.22,7.0): F.Cu south
trace("+3.3V", [(12.55, 4.5), (12.22, 7.0)])

# --- C6.1(12.22,7.0) → C10.1(16.52,7.5): F.Cu east
trace("+3.3V", [(12.22, 7.0), (12.22, 7.5), (16.52, 7.5)])

# --- C10.1(16.52,7.5) → U2.48(19.5,7.84): F.Cu east
trace("+3.3V", [(16.52, 7.5), (19.5, 7.5), (19.5, 7.84)])

# --- U2.48(19.5,7.84) → U2.1(18.09,9.25): Via inside MCU, B.Cu to left side
add_via("+3.3V", 19.0, 8.5)
trace("+3.3V", [(19.5, 7.84), (19.0, 8.5)])
trace("+3.3V", [(19.0, 8.5), (18.09, 9.25)], layer="B.Cu")

# --- U2.36(26.41,9.25): Via east of MCU, B.Cu from backbone
add_via("+3.3V", 27.0, 9.25)
trace("+3.3V", [(27.0, 9.25), (26.41, 9.25)])
trace("+3.3V", [(19.0, 8.5), (27.0, 9.25)], layer="B.Cu")

# --- C9.1(19.02,5.0): F.Cu stub from backbone
trace("+3.3V", [(12.55, 4.5), (14.5, 4.5), (19.02, 4.5), (19.02, 5.0)])

# --- C8.1(29.52,10.0): B.Cu from via at (27,9.25)
trace("+3.3V", [(27.0, 9.25), (29.52, 9.25), (29.52, 10.0)], layer="B.Cu")

# --- SW1.3(34.25,1.07): B.Cu from C8 area north
add_via("+3.3V", 34.25, 2.5)
trace("+3.3V", [(29.52, 10.0), (34.25, 10.0), (34.25, 2.5)], layer="B.Cu")
trace("+3.3V", [(34.25, 2.5), (34.25, 1.07)])

# --- J1.1(43,2): B.Cu east from SW1 area
trace("+3.3V", [(34.25, 2.5), (43.0, 2.5), (43.0, 2.0)], layer="B.Cu")

# --- J4.1(42,10): B.Cu from C8 backbone
trace("+3.3V", [(34.25, 10.0), (42.0, 10.0)], layer="B.Cu")

# --- FB1.2(15.29,16.5): F.Cu south from C6 area
trace("+3.3V", [(12.22, 7.0), (12.22, 14.0), (15.29, 16.5)])

# --- R3.1(9.99,18.5): F.Cu from +3.3VA path area
trace("+3.3V", [(12.22, 14.0), (9.99, 18.5)])

# --- D1.2(5.79,21.5): B.Cu from R3 area
add_via("+3.3V", 9.5, 19.0)
trace("+3.3V", [(9.99, 18.5), (9.5, 19.0)])
trace("+3.3V", [(9.5, 19.0), (5.79, 21.5)], layer="B.Cu")

# --- U2.24(25.0,16.16): B.Cu from via inside MCU area
add_via("+3.3V", 25.0, 15.5)
trace("+3.3V", [(27.0, 9.25), (27.0, 15.5), (25.0, 15.5)], layer="B.Cu")
trace("+3.3V", [(25.0, 15.5), (25.0, 16.16)])

# --- C7.1(25.52,19.5): F.Cu south from U2.24
trace("+3.3V", [(25.0, 16.16), (25.52, 16.16), (25.52, 19.5)])

# --- C13.1(20.52,19.5): F.Cu south from MCU bottom area
add_via("+3.3V", 20.52, 17.0)
trace("+3.3V", [(19.0, 8.5), (19.0, 17.0), (20.52, 17.0)], layer="B.Cu")
trace("+3.3V", [(20.52, 17.0), (20.52, 19.5)])

# --- RP_SCL1.1(36.99,17.5): B.Cu from J2 side
add_via("+3.3V", 37.0, 16.5)
trace("+3.3V", [(34.25, 10.0), (37.0, 10.0), (37.0, 16.5)], layer="B.Cu")
trace("+3.3V", [(37.0, 16.5), (36.99, 17.5)])

# --- RP_SDA1.2(38.01,20.0): F.Cu from RP_SCL area
trace("+3.3V", [(36.99, 17.5), (38.01, 17.5), (38.01, 20.0)])

# --- J2.1(42,17): F.Cu from RP_SCL, east along y=17.0
add_via("+3.3V", 41.0, 16.5)
trace("+3.3V", [(37.0, 16.5), (41.0, 16.5)], layer="B.Cu")
trace("+3.3V", [(41.0, 16.5), (42.0, 16.5), (42.0, 17.0)])

# ═══════════════════════════════════════════════════════════════
# 18. GND: Zone on B.Cu + vias from each GND pad
#     Zone covers entire board. Vias placed at each GND SMD pad.

# GND vias at critical locations — one near each SMD GND pad
gnd_via_locations = [
    # Capacitor GND pads
    (17.48, 7.5),    # C10.2 — inside MCU area (near top)
    (13.78, 7.5),    # C6.2 — moved to y=7.5 to avoid conflict
    (14.45, 4.0),    # C2.2 — north area
    (10.98, 10.0),   # C3.2 — near Y1
    (10.98, 14.0),   # C4.2 — near Y1
    (15.98, 19.0),   # C5.2 — south
    (19.98, 5.5),    # C9.2 — near MCU top
    (26.48, 20.0),   # C7.2 — south east
    (30.48, 10.5),   # C8.2 — east
    (10.48, 16.5),   # C11.2 — west
    (8.48, 21.0),    # C12.2 — southwest
    (21.48, 20.0),   # C13.2 — south
    (2.95, 20.0),    # C1.2 — far west
    # MCU GND pads
    (18.09, 12.5),   # U2.8 — left side MCU (adjusted to avoid NRST)
    (20.5, 16.7),    # U2.47 — near bottom pads (use B.Cu stub)
    (24.5, 15.5),    # U2.23 — bottom right (adjusted to avoid +3.3V via)
    (26.8, 10.0),    # U2.35 — right side MCU (shifted to avoid +3.3V via)
    # Other GND pads
    (8.51, 22.0),    # R1.2
    (3.85, 2.7),     # U1.1 — adjusted slightly
    # Crystal GND
    (13.0, 11.5),    # Y1 center — for Y1.2 and Y1.4
]

for gx, gy in gnd_via_locations:
    add_via("GND", gx, gy)

# Short F.Cu stubs from GND pads to their nearest via
trace("GND", [(17.48, 7.5), (17.48, 7.5)])  # C10.2 pad-to-via (same pos)
trace("GND", [(13.78, 7.0), (13.78, 7.5)])  # C6.2 to via
trace("GND", [(14.45, 4.5), (14.45, 4.0)])  # C2.2 to via
trace("GND", [(10.98, 9.5), (10.98, 10.0)])  # C3.2 to via
trace("GND", [(10.98, 13.5), (10.98, 14.0)])  # C4.2 to via
trace("GND", [(15.98, 18.5), (15.98, 19.0)])  # C5.2 to via
trace("GND", [(19.98, 5.0), (19.98, 5.5)])  # C9.2 to via
trace("GND", [(26.48, 19.5), (26.48, 20.0)])  # C7.2 to via
trace("GND", [(30.48, 10.0), (30.48, 10.5)])  # C8.2 to via
trace("GND", [(10.48, 16.0), (10.48, 16.5)])  # C11.2 to via
trace("GND", [(8.48, 20.5), (8.48, 21.0)])  # C12.2 to via
trace("GND", [(21.48, 19.5), (21.48, 20.0)])  # C13.2 to via
trace("GND", [(2.95, 19.5), (2.95, 20.0)])  # C1.2 to via
trace("GND", [(18.09, 12.75), (18.09, 12.5)])  # U2.8 to via
trace("GND", [(20.0, 7.84), (20.5, 7.84), (20.5, 16.7)])  # U2.47 to via (B.Cu path via zone)
trace("GND", [(24.5, 16.16), (24.5, 15.5)])  # U2.23 to via
trace("GND", [(26.41, 9.75), (26.8, 10.0)])  # U2.35 to via
trace("GND", [(8.51, 21.5), (8.51, 22.0)])  # R1.2 to via
trace("GND", [(3.85, 2.2), (3.85, 2.7)])  # U1.1 to via
# Y1 GND pads to central via
trace("GND", [(15.6, 12.35), (15.0, 12.35), (13.0, 11.5)])  # Y1.2 to via
trace("GND", [(13.4, 10.65), (13.0, 11.5)])  # Y1.4 to via

# GND PTH pads connect to B.Cu zone directly (J1.4, J2.4, J3.5, J4.4, SW1.1)
# No F.Cu traces needed — zone fills to PTH pads on B.Cu.

# ═══════════════════════════════════════════════════════════════
# GND Zone on B.Cu (covers entire board)
bbox = board.GetBoardEdgesBoundingBox()
margin = pcbnew.FromMM(0.3)

zone = pcbnew.ZONE(board)
gnd_net = board.GetNetInfo().GetNetItem("GND")
zone.SetNet(gnd_net)
zone.SetLayer(pcbnew.B_Cu)
zone.SetAssignedPriority(0)
outline = zone.Outline()
outline.NewOutline()
outline.Append(bbox.GetLeft() + margin, bbox.GetTop() + margin)
outline.Append(bbox.GetRight() - margin, bbox.GetTop() + margin)
outline.Append(bbox.GetRight() - margin, bbox.GetBottom() - margin)
outline.Append(bbox.GetLeft() + margin, bbox.GetBottom() - margin)
zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
zone.SetLocalClearance(pcbnew.FromMM(0.3))
board.Add(zone)

# Fill zones
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())

# ═══════════════════════════════════════════════════════════════
# Save
pcbnew.SaveBoard(board_path, board)
print(f"Board saved to {board_path}")

# Track/via counts
tracks = sum(1 for t in board.GetTracks()
             if t.GetClass() == "PCB_TRACK")
vias = sum(1 for t in board.GetTracks()
           if t.GetClass() == "PCB_VIA")
zones_count = board.GetAreaCount()
print(f"  Tracks: {tracks}, Vias: {vias}, Zones: {zones_count}")
