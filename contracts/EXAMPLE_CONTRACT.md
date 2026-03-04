# Example Contract: Simple MCU Board v1.0

**CRITICAL RULE:** You are NOT allowed to terminate this session until ALL items in the completion criteria checklist are fulfilled.

## Specifications
- **Dimensions:** 50mm × 40mm
- **Layers:** 2-layer (F.Cu, B.Cu)

## Components Table
| Reference | Component | Footprint | Position |
| :--- | :--- | :--- | :--- |
| U1 | STM32 MCU | TQFP-32_7x7mm_P0.8mm | Center |
| C1 | Bypass Cap 100nF | C_0402 | Near U1 VCC |
| C2 | Bypass Cap 100nF | C_0402 | Near U1 VCC |
| R1 | Pull-up 10k | R_0402 | Near U1 NRST |
| J1 | USB Micro-B | USB_Micro-B | Edge |
| Y1 | Crystal 8MHz | Crystal_SMD | Near U1 OSC |

## Netlist Table
| Net Name | Connections |
| :--- | :--- |
| VCC | U1_VDD, C1_1, C2_1, R1_1, J1_VBUS |
| GND | U1_VSS, C1_2, C2_2, J1_GND, Y1_GND |
| NRST | U1_NRST, R1_2 |
| USB_DP | U1_PA12, J1_D+ |
| USB_DM | U1_PA11, J1_D- |
| OSC_IN | U1_OSC_IN, Y1_1 |
| OSC_OUT | U1_OSC_OUT, Y1_2 |

## Design Rules
- Trace Width: 0.25mm for signals, 0.5mm for power.
- Use a ground pour (B.Cu copper pour) connected to the GND net.
- All components must be placed within the board outline.

## Verification Commands
Use these commands to verify the completion criteria:
- **Run Tests:** `pytest tests/test_simple_mcu_board.py -v`
- **Run DRC:** `kicad-cli pcb drc --output report.json output/simple_mcu_board.kicad_pcb`

## Completion Criteria Checklist
- [ ] **Structure:** `test_board_dimensions()` passes (50x40mm verified).
- [ ] **Components:** `test_component_count()` passes (all 6 components exist).
- [ ] **Connectivity:** `test_net_connectivity()` passes (all nets routed correctly).
- [ ] **Quality:** `test_drc_passes()` passes (DRC report shows 0 errors).
- [ ] **Tests:** All `pytest` tests pass successfully without modification to the test files.
