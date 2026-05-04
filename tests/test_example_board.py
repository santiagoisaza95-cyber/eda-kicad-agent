"""Template test file for contract-driven PCB validation.

This file demonstrates the testing pattern used by eda-kicad-agent.
Each test maps to a checklist item in the board's contract file.
When /new-board generates a contract, it also generates a test file
following this structure.

Contract: contracts/EXAMPLE_CONTRACT.md
Board:    Simple MCU Board v1.0
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Path to the board file under test (update when board is generated)
BOARD_FILE = Path(__file__).resolve().parent.parent / "output" / "simple_mcu_board.kicad_pcb"

# ── Contract: Board Structure ──────────────────────────────────────────────


@pytest.fixture
def board(load_board):
    """Load the example board. Skip if not yet generated."""
    if not BOARD_FILE.exists():
        pytest.skip(f"Board not generated yet: {BOARD_FILE}")
    return load_board(BOARD_FILE)


class TestBoardDimensions:
    """Contract item: Board must be 50x40mm, 2-layer."""

    def test_board_dimensions(self, board, pcbnew_module):
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = pcbnew_module.ToMM(bbox.GetWidth())
        height_mm = pcbnew_module.ToMM(bbox.GetHeight())
        assert abs(width_mm - 50.0) < 0.5, f"Width {width_mm}mm, expected 50mm"
        assert abs(height_mm - 40.0) < 0.5, f"Height {height_mm}mm, expected 40mm"

    def test_layer_count(self, board):
        copper_layers = board.GetCopperLayerCount()
        assert copper_layers == 2, f"Expected 2 copper layers, got {copper_layers}"


# ── Contract: Components ───────────────────────────────────────────────────


class TestComponents:
    """Contract item: All required components must be placed."""

    REQUIRED_COMPONENTS = {
        "U1": "STM32 MCU (TQFP-32_7x7mm_P0.8mm)",
        "C1": "Bypass capacitor (C_0402)",
        "C2": "Bypass capacitor (C_0402)",
        "R1": "Pull-up resistor (R_0402)",
        "J1": "USB Micro-B connector",
        "Y1": "8MHz crystal",
    }

    def test_component_count(self, board):
        footprints = board.GetFootprints()
        assert len(footprints) >= len(self.REQUIRED_COMPONENTS), (
            f"Expected at least {len(self.REQUIRED_COMPONENTS)} components, "
            f"got {len(footprints)}"
        )

    @pytest.mark.parametrize("ref", ["U1", "C1", "C2", "R1", "J1", "Y1"])
    def test_component_exists(self, board, assert_component_exists, ref):
        assert_component_exists(board, ref)


# ── Contract: Net Connectivity ─────────────────────────────────────────────


class TestNetConnectivity:
    """Contract item: All required nets must exist and be connected."""

    REQUIRED_NETS = ["VCC", "GND", "NRST", "USB_DP", "USB_DM", "OSC_IN", "OSC_OUT"]

    @pytest.mark.parametrize("net_name", REQUIRED_NETS)
    def test_net_connectivity(self, board, assert_net_connected, net_name):
        assert_net_connected(board, net_name)


# ── Contract: Design Rule Check ────────────────────────────────────────────


class TestDRC:
    """Contract item: DRC must pass with 0 violations."""

    def test_drc_passes(self, run_drc):
        if not BOARD_FILE.exists():
            pytest.skip(f"Board not generated yet: {BOARD_FILE}")
        result = run_drc(BOARD_FILE)
        assert result["violations"] == 0, (
            f"DRC found {result['violations']} violations. "
            f"Report: {result['report_path']}"
        )
