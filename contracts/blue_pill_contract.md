# Contract: STM32 Blue Pill Clone

**Version:** 1.0
**Board Name:** blue_pill
**Output File:** `output/blue_pill.kicad_pcb`

---

## CONSTRAINT: DESIGN FROM THIS CONTRACT ONLY

**For this board, you MUST NOT:**
- Use WebSearch or WebFetch to look up Blue Pill schematics, layouts, or pinouts
- Read any files in the `reference/` directory
- Browse GitHub or any website for existing Blue Pill designs
- Search for "STM32F103 pinout" or similar queries online

**You MUST design entirely from:**
- This contract (component table + netlist below)
- The skills in `agent_docs/skills/`
- The rules in `agent_docs/rules/`
- The API manifest in `api_manifest.json`
- The MCP tools for placement, DRC, and export (NOT for routing — use pcbnew SWIG directly, see routing-skill.md)

This is a controlled test. Everything you need is in this contract.

---

## Board Specifications

| Parameter | Value |
|-----------|-------|
| Dimensions | 44.5mm x 24.0mm |
| Corner radius | 3.0mm (all corners) |
| Layers | 2 (F.Cu = signal, B.Cu = ground/power) |
| Thickness | 1.6mm FR4 |
| Copper weight | 1 oz (35um) |

## Design Rules

| Rule | Value |
|------|-------|
| Min clearance | 0.200mm |
| Min trace width | 0.200mm |
| Signal trace width | 0.300mm |
| Power trace width | 0.500mm |
| Via diameter | 0.700mm |
| Via drill | 0.300mm |
| Copper-to-edge clearance | 0.500mm |
| Zone clearance | 0.300mm |

---

## Components (28 total)

| Ref | Value | Footprint | Purpose |
|-----|-------|-----------|---------|
| U2 | STM32F103C8T6 | Package_QFP:LQFP-48_7x7mm_P0.5mm | Main MCU |
| U1 | AMS1117-3.3 | Package_TO_SOT_SMD:SOT-223-3_TabPin2 | 3.3V LDO regulator |
| Y1 | 16MHz | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | HSE crystal oscillator |
| C1 | 22u | Capacitor_SMD:C_0805_2012Metric | VBUS input bulk cap |
| C2 | 22u | Capacitor_SMD:C_0805_2012Metric | 3.3V output bulk cap |
| C3 | 10p | Capacitor_SMD:C_0402_1005Metric | Crystal load cap (HSE_IN) |
| C4 | 10p | Capacitor_SMD:C_0402_1005Metric | Crystal load cap (HSE_OUT) |
| C5 | 100n | Capacitor_SMD:C_0402_1005Metric | NRST decoupling |
| C6 | 10u | Capacitor_SMD:C_0603_1608Metric | Regulator output cap |
| C7 | 100n | Capacitor_SMD:C_0402_1005Metric | VDD decoupling (pin 24) |
| C8 | 100n | Capacitor_SMD:C_0402_1005Metric | VDD decoupling (pin 36) |
| C9 | 100n | Capacitor_SMD:C_0402_1005Metric | VDD decoupling (pin 48) |
| C10 | 100n | Capacitor_SMD:C_0402_1005Metric | VDD decoupling (pin 1) |
| C11 | 10n | Capacitor_SMD:C_0402_1005Metric | VDDA filter cap |
| C12 | 1u | Capacitor_SMD:C_0402_1005Metric | VDDA bulk cap |
| C13 | 1u | Capacitor_SMD:C_0402_1005Metric | VDD bulk cap |
| R1 | 1k5 | Resistor_SMD:R_0402_1005Metric | Power LED current limiter |
| R2 | 10k | Resistor_SMD:R_0402_1005Metric | BOOT0 pull-down |
| R3 | 1k5 | Resistor_SMD:R_0402_1005Metric | USB D+ pull-up (1.5k for full-speed) |
| RP_SDA1 | 2k2 | Resistor_SMD:R_0402_1005Metric | I2C2 SDA pull-up |
| RP_SCL1 | 2k2 | Resistor_SMD:R_0402_1005Metric | I2C2 SCL pull-up |
| D1 | GREEN | LED_SMD:LED_0603_1608Metric | Power indicator LED |
| FB1 | 120R | Inductor_SMD:L_0603_1608Metric | Analog power ferrite bead |
| SW1 | SW_SPDT | Button_Switch_SMD:SW_SPDT_PCM12 | BOOT0 mode select switch |
| J1 | USART1 | Connector_PinHeader_2.00mm:PinHeader_1x04_P2.00mm_Vertical | USART1 header (3.3V, TX, RX, GND) |
| J2 | I2C2 | Connector_PinHeader_2.00mm:PinHeader_1x04_P2.00mm_Vertical | I2C2 header (3.3V, SCL, SDA, GND) |
| J3 | USB_Micro-B | Connector_USB:USB_Micro-B_Wuerth_629105150521 | USB connector for power and data |
| J4 | SWD | Connector_PinHeader_2.00mm:PinHeader_1x04_P2.00mm_Vertical | SWD debug header (3.3V, SWDIO, SWCLK, GND) |

---

## Netlist (18 signal/power nets)

| Net Name | Connected Pins |
|----------|---------------|
| GND | C1.2, C2.2, C3.2, C4.2, C5.2, C6.2, C7.2, C8.2, C9.2, C10.2, C11.2, C12.2, C13.2, J1.4, J2.4, J3.5, J4.4, R1.2, SW1.1, U1.1, U2.23, U2.35, U2.47, U2.8, Y1.2, Y1.4 |
| VBUS | C1.1, J3.1, U1.3 |
| +3.3V | C2.1, C6.1, C7.1, C8.1, C9.1, C10.1, C13.1, D1.2, FB1.2, J1.1, J2.1, J4.1, R3.1, RP_SCL1.1, RP_SDA1.2, SW1.3, U1.2, U2.1, U2.24, U2.36, U2.48 |
| HSE_IN | C3.1, U2.5, Y1.1 |
| HSE_OUT | C4.1, U2.6, Y1.3 |
| NRST | C5.1, U2.7 |
| +3.3VA | C11.1, C12.1, FB1.1, U2.9 |
| PWR_LED_K | D1.1, R1.1 |
| USART1_TX | J1.2, U2.42 |
| USART1_RX | J1.3, U2.43 |
| I2C2_SCL | J2.2, RP_SCL1.2, U2.21 |
| I2C2_SDA | J2.3, RP_SDA1.1, U2.22 |
| USB_D+ | J3.3, R3.2, U2.33 |
| USB_D- | J3.2, U2.32 |
| SWDIO | J4.2, U2.34 |
| SWCLK | J4.3, U2.37 |
| BOOT0 | R2.2, U2.44 |
| SW_BOOT0 | R2.1, SW1.2 |

**Unconnected GPIO (by design):** PA0-PA10, PA15, PB0-PB5, PB8-PB9, PB12-PB15, PC13-PC15. These pins have no net assignment. Leave them unconnected.

---

## Placement Guidance

Follow `agent_docs/skills/placement-skill.md` priority order:

1. **U2 (STM32)** — center of board, pin 1 top-left
2. **C7, C8, C9, C10 (100nF decoupling)** — within 2mm of U2 VDD pins (1, 24, 36, 48)
3. **C5 (NRST cap)** — within 2mm of U2 pin 7
4. **Y1 (crystal) + C3, C4** — within 5mm of U2 pins 5-6 (HSE_IN/OUT)
5. **FB1 + C11, C12** — near U2 pin 9 (VDDA), ferrite bead isolates analog supply
6. **U1 (AMS1117) + C1, C2, C6** — near board edge, input side near J3
7. **J3 (USB)** — board edge, typically one of the short edges
8. **J1, J2, J4 (pin headers)** — board edges, accessible
9. **SW1 (BOOT0 switch)** — near board edge, accessible
10. **R1, D1 (power LED)** — visible location
11. **R2 (BOOT0 pull-down)** — near SW1 and U2 pin 44
12. **R3 (USB pull-up)** — near J3 and U2 pin 33
13. **RP_SDA1, RP_SCL1 (I2C pull-ups)** — near J2 header

## Routing Guidance

Follow `agent_docs/skills/routing-skill.md` priority order:

1. **Power first** — GND, +3.3V, VBUS, +3.3VA at 0.500mm width
2. **Crystal traces** — HSE_IN, HSE_OUT short and symmetric, 0.300mm
3. **USB data** — USB_D+, USB_D- at 0.300mm, keep short and parallel
4. **General signals** — all others at 0.300mm
5. **Ground pour** — B.Cu full GND copper zone, F.Cu partial GND fill where space allows

---

## Copper Zones

| Layer | Net | Priority |
|-------|-----|----------|
| B.Cu | GND | 0 (fills entire back) |
| F.Cu | GND | 1 (fills remaining front space) |

---

## Completion Checklist

- [ ] Board outline created (44.5mm x 24.0mm, 3mm corner radius)
- [ ] All 28 components placed with correct footprints
- [ ] All 18 nets defined and connected
- [ ] Decoupling caps within 2mm of VDD pins (courtyard gap >= 0.5mm)
- [ ] Crystal within 5mm of HSE pins (courtyard gap >= 0.8mm)
- [ ] Connectors at board edges (>= 1.5mm clearance to other components)
- [ ] Pre-routing DRC clean (courtyard overlaps, edge clearance)
- [ ] All traces routed using pcbnew SWIG (NOT MCP route_trace)
- [ ] Crystal traces: short, symmetric, no vias, guard ring with stitching vias
- [ ] USB traces: parallel pair, length-matched, no vias
- [ ] Power traces at 0.500mm width
- [ ] Signal traces at 0.300mm width minimum
- [ ] No 90-degree trace bends
- [ ] GND copper zone on B.Cu (full board)
- [ ] GND copper zone on F.Cu (fill remaining space)
- [ ] All zones filled (ZONE_FILLER.Fill called)
- [ ] Ground stitching vias placed (perimeter + near ICs + crystal guard ring)
- [ ] Zero floating copper islands
- [ ] DRC passes: 0 violations AND 0 unconnected items
- [ ] All pytest tests in `tests/test_blue_pill.py` pass (including routing tests)
- [ ] Board saved to `output/blue_pill.kicad_pcb`
