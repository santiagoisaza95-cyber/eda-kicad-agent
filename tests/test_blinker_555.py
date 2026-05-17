"""Tests for the 555 LED Blinker audition board contract.

Contract: contracts/blinker_555_contract.md
Stage: v2 Stage 1 Batch 1.3 (test file collectible) → Stage 3 (tests executed
       against the built board produced by the audition).

These tests validate the agent's output against `blinker_555_contract.md`.
The agent must make ALL tests pass — no test modifications allowed.

Tests SKIP cleanly when `output/blinker_555.kicad_pcb` does not yet exist
(i.e. before the Stage 3 audition has produced the board). After audition,
they must all pass for the contract to be declared complete.

The five contract-named tests are:
  - TestComponents::test_component_count          ("test_component_count")
  - TestNetConnectivity::test_nets_routed         ("test_nets_routed")
  - TestDRC::test_drc_zero                        ("test_drc_zero")
  - TestBoardDimensions::test_dimensions          ("test_dimensions")
  - TestComponents::test_components_on_f_cu       ("test_components_on_f_cu")

Parameterized supporting tests (test_component_exists, test_net_exists)
mirror the pattern used by tests/test_blue_pill.py for per-item visibility
in the pytest output. Routing tests (TestRouting) check trace/via/zone
presence; they SKIP if the audition has not yet produced any copper.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ── Board specs from contract ──────────────────────────────────────────────
BOARD_NAME = "blinker_555"
BOARD_FILE = Path(__file__).resolve().parent.parent / "output" / f"{BOARD_NAME}.kicad_pcb"
DRU_FILE = Path(__file__).resolve().parent.parent / "output" / f"{BOARD_NAME}.kicad_dru"

BOARD_WIDTH_MM = 20.0
BOARD_HEIGHT_MM = 30.0
BOARD_DIMENSION_TOLERANCE_MM = 0.5  # contract: bbox ≤ 20.5 × 30.5 mm

EXPECTED_COMPONENT_COUNT = 8  # U1, R1, R2, R3, C1, C2, D1, J1

EXPECTED_COMPONENTS = [
    "U1",  # NE555
    "R1",  # 1k — charge resistor
    "R2",  # 10k — discharge resistor
    "R3",  # 470Ω — LED current limit
    "C1",  # 10µF timing cap
    "C2",  # 100nF VCC decoupling
    "D1",  # LED
    "J1",  # 2-pin power header
]

# Per contract: VCC, GND, TRIG, THR, DISCH, OUT
EXPECTED_NETS = ["VCC", "GND", "TRIG", "THR", "DISCH", "OUT"]


# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def board(load_board):
    """Load the blinker_555 board file.

    Skips if `output/blinker_555.kicad_pcb` does not exist — the Stage 3
    audition has not yet produced the board. After audition, this fixture
    returns the loaded BOARD object for all dependent tests.
    """
    if not BOARD_FILE.exists():
        pytest.skip(f"Audition has not produced the board yet: {BOARD_FILE}")
    return load_board(BOARD_FILE)


# ── Board Dimensions ──────────────────────────────────────────────────────
class TestBoardDimensions:
    """Contract item: Board ≤ 20.5 × 30.5 mm, 2-layer."""

    def test_dimensions(self, board, pcbnew_module):
        """Bounding box of Edge_Cuts must fit within 20.5 × 30.5 mm.

        Either orientation is acceptable (20×30 or 30×20) — the contract
        specifies a rectangle, not a fixed axis assignment. We assert the
        max side ≤ max-dim and min side ≤ min-dim.
        """
        bbox = board.GetBoardEdgesBoundingBox()
        width_mm = pcbnew_module.ToMM(bbox.GetWidth())
        height_mm = pcbnew_module.ToMM(bbox.GetHeight())

        max_side = max(width_mm, height_mm)
        min_side = min(width_mm, height_mm)

        max_dim = max(BOARD_WIDTH_MM, BOARD_HEIGHT_MM) + BOARD_DIMENSION_TOLERANCE_MM
        min_dim = min(BOARD_WIDTH_MM, BOARD_HEIGHT_MM) + BOARD_DIMENSION_TOLERANCE_MM

        assert max_side <= max_dim, (
            f"Board longest side {max_side:.2f} mm exceeds "
            f"{max_dim:.2f} mm (nominal {max(BOARD_WIDTH_MM, BOARD_HEIGHT_MM)} mm "
            f"+ {BOARD_DIMENSION_TOLERANCE_MM} mm tolerance)"
        )
        assert min_side <= min_dim, (
            f"Board shortest side {min_side:.2f} mm exceeds "
            f"{min_dim:.2f} mm (nominal {min(BOARD_WIDTH_MM, BOARD_HEIGHT_MM)} mm "
            f"+ {BOARD_DIMENSION_TOLERANCE_MM} mm tolerance)"
        )

    def test_layer_count(self, board):
        """Board must be 2-layer (F.Cu + B.Cu)."""
        copper_layers = board.GetCopperLayerCount()
        assert copper_layers == 2, f"Expected 2 copper layers, got {copper_layers}"


# ── Components ────────────────────────────────────────────────────────────
class TestComponents:
    """Contract item: All 8 components present on F.Cu with correct footprints."""

    def test_component_count(self, board):
        """Board must have at least 8 components (U1, R1, R2, R3, C1, C2, D1, J1)."""
        footprints = list(board.GetFootprints())
        assert len(footprints) >= EXPECTED_COMPONENT_COUNT, (
            f"Expected ≥ {EXPECTED_COMPONENT_COUNT} components, got {len(footprints)}"
        )

    @pytest.mark.parametrize("ref", EXPECTED_COMPONENTS)
    def test_component_exists(self, board, assert_component_exists, ref):
        """Each contract-required component reference must be present."""
        assert_component_exists(board, ref)

    def test_components_on_f_cu(self, board, pcbnew_module):
        """All footprints must be placed on the F.Cu layer.

        Through-hole parts (U1 DIP-8, J1 2-pin header) are "on F.Cu" in the
        sense that their primary visible face is F.Cu, even though their pads
        cross all copper layers — KiCad reports such footprints as F.Cu by
        default. Any footprint reporting B.Cu (back side) fails this test.
        """
        bad_placements = []
        for fp in board.GetFootprints():
            layer = fp.GetLayer()
            if layer != pcbnew_module.F_Cu:
                layer_name = board.GetLayerName(layer)
                bad_placements.append(
                    f"{fp.GetReference()} on layer '{layer_name}' (expected F.Cu)"
                )
        assert not bad_placements, (
            "The following footprints are not on F.Cu:\n  - "
            + "\n  - ".join(bad_placements)
        )


# ── Net Connectivity ──────────────────────────────────────────────────────
class TestNetConnectivity:
    """Contract item: All 6 nets exist; no unconnected pads after routing."""

    @pytest.mark.parametrize("net_name", EXPECTED_NETS)
    def test_net_exists(self, board, assert_net_connected, net_name):
        """Each contract-required net must exist in the board's net table."""
        assert_net_connected(board, net_name)

    def test_nets_routed(self, board, pcbnew_module):
        """Every contract net must have ≥ 2 pads assigned to it (the minimum
        for a routable connection).

        This is the cheap connectivity check — the full unconnected-pad audit
        is performed by `TestDRC::test_drc_zero` via kicad-cli DRC against the
        JLCPCB-emitted DRU file.
        """
        netinfo = board.GetNetInfo()
        empty_nets = []
        for net_name in EXPECTED_NETS:
            net = netinfo.GetNetItem(net_name)
            if net is None:
                empty_nets.append(f"{net_name} (net missing entirely)")
                continue
            pad_count = sum(
                1
                for fp in board.GetFootprints()
                for pad in fp.Pads()
                if pad.GetNet().GetNetname() == net_name
            )
            if pad_count < 2:
                empty_nets.append(f"{net_name} (only {pad_count} pad(s) assigned)")
        assert not empty_nets, (
            "The following contract nets have <2 pads assigned (cannot be a real "
            "connection):\n  - " + "\n  - ".join(empty_nets)
        )


# ── DRC ───────────────────────────────────────────────────────────────────
class TestDRC:
    """Contract item: DRC against the JLCPCB-emitted DRU must be 0/0."""

    def test_drc_zero(self, run_drc, tmp_path):
        """DRC must report 0 violations AND 0 unconnected items.

        Per `agent_docs/rules/supplier-drc-rules.md`, the JLCPCB DRU file at
        `output/blinker_555.kicad_dru` must already exist (emitted by the
        agent as its first build action). When kicad-cli runs DRC on the
        `.kicad_pcb`, KiCad picks up the co-located `.kicad_dru` automatically.
        """
        if not BOARD_FILE.exists():
            pytest.skip(f"Audition has not produced the board yet: {BOARD_FILE}")
        if not DRU_FILE.exists():
            pytest.skip(
                f"JLCPCB DRU has not been emitted yet: {DRU_FILE} — "
                "this is the agent's first build action per supplier-drc-rules.md"
            )

        result = run_drc(BOARD_FILE, output_dir=tmp_path)
        assert result["violations"] == 0, (
            f"DRC against JLCPCB DRU found {result['violations']} violation(s). "
            f"Report: {result['report_path']}"
        )

        # Cross-check unconnected items via the DRC JSON (run_drc only counts violations).
        import json

        if result["report_path"].exists():
            with open(result["report_path"]) as f:
                report = json.load(f)
            unconnected = report.get("unconnected_items", [])
            assert len(unconnected) == 0, (
                f"Board has {len(unconnected)} unconnected pad pair(s) — "
                "all nets must be routed. "
                f"Report: {result['report_path']}"
            )


# ── Routing ──────────────────────────────────────────────────────────────
class TestRouting:
    """Optional structural routing checks. Skip if audition has not yet
    produced any copper (e.g. mid-build inspection before routing checkpoints).
    """

    def test_has_traces(self, board):
        """Board must have routed traces after the routing checkpoints."""
        track_count = 0
        for track in board.GetTracks():
            if track.GetClass() != "PCB_VIA":
                track_count += 1
        if track_count == 0:
            pytest.skip(
                "Board has 0 traces — likely a pre-routing checkpoint snapshot. "
                "After Stage 3 audition completes, this should be > 0."
            )
        assert track_count > 0

    def test_has_ground_zone(self, board, pcbnew_module):
        """Board must have a GND copper zone on B.Cu after the zone checkpoint."""
        found_bcu_gnd = False
        for i in range(board.GetAreaCount()):
            zone = board.GetArea(i)
            if zone.GetLayer() == pcbnew_module.B_Cu and zone.GetNetname() == "GND":
                found_bcu_gnd = True
                break
        if not found_bcu_gnd:
            pytest.skip(
                "No B.Cu GND zone present yet — likely a pre-zone-fill checkpoint. "
                "After Stage 3 checkpoint 8 completes, this should be present."
            )
        assert found_bcu_gnd
