"""Tests for the STM32 Blue Pill board contract.

These tests validate the agent's output against the blue_pill_contract.md spec.
The agent must make ALL tests pass — no test modifications allowed.
"""
import pytest

# ── Board specs from contract ──────────────────────────────────────────────
BOARD_NAME = "blue_pill"
BOARD_FILE = f"output/{BOARD_NAME}.kicad_pcb"
BOARD_WIDTH_MM = 44.5
BOARD_HEIGHT_MM = 24.0
TOLERANCE_MM = 0.5  # allow small rounding in outline arcs

EXPECTED_COMPONENTS = [
    "U2", "U1", "Y1",
    "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13",
    "R1", "R2", "R3", "RP_SDA1", "RP_SCL1",
    "D1", "FB1", "SW1",
    "J1", "J2", "J3", "J4",
]

EXPECTED_NETS = [
    "GND", "VBUS", "+3.3V", "HSE_IN", "HSE_OUT", "NRST", "+3.3VA",
    "PWR_LED_K", "USART1_TX", "USART1_RX",
    "I2C2_SCL", "I2C2_SDA",
    "USB_D+", "USB_D-",
    "SWDIO", "SWCLK",
    "BOOT0", "SW_BOOT0",
]


# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def pcbnew_module():
    """Import pcbnew — skip entire session if unavailable."""
    try:
        import pcbnew
        return pcbnew
    except ImportError:
        pytest.skip("pcbnew not importable — run with KiCad bundled Python")


@pytest.fixture(scope="session")
def board(pcbnew_module):
    """Load the blue_pill board file."""
    from pathlib import Path

    board_path = Path(__file__).resolve().parent.parent / BOARD_FILE
    if not board_path.exists():
        pytest.skip(f"Board file not found: {board_path}")
    return pcbnew_module.LoadBoard(str(board_path))


# ── Board Dimensions ──────────────────────────────────────────────────────
class TestBoardDimensions:
    def test_board_dimensions(self, board, pcbnew_module):
        """Board must be 44.5mm x 24.0mm (within tolerance)."""
        bbox = board.GetBoardEdgesBoundingBox()
        width = pcbnew_module.ToMM(bbox.GetWidth())
        height = pcbnew_module.ToMM(bbox.GetHeight())
        assert abs(width - BOARD_WIDTH_MM) <= TOLERANCE_MM, (
            f"Width {width}mm != expected {BOARD_WIDTH_MM}mm"
        )
        assert abs(height - BOARD_HEIGHT_MM) <= TOLERANCE_MM, (
            f"Height {height}mm != expected {BOARD_HEIGHT_MM}mm"
        )

    def test_layer_count(self, board):
        """Board must be 2-layer (F.Cu + B.Cu)."""
        copper_layers = board.GetCopperLayerCount()
        assert copper_layers == 2, f"Expected 2 copper layers, got {copper_layers}"


# ── Components ────────────────────────────────────────────────────────────
class TestComponents:
    def test_component_count(self, board):
        """Board must have at least 28 components."""
        footprints = list(board.GetFootprints())
        assert len(footprints) >= len(EXPECTED_COMPONENTS), (
            f"Expected >= {len(EXPECTED_COMPONENTS)} components, got {len(footprints)}"
        )

    @pytest.mark.parametrize("ref", EXPECTED_COMPONENTS)
    def test_component_exists(self, board, ref):
        """Each required component must be present on the board."""
        refs_on_board = [fp.GetReference() for fp in board.GetFootprints()]
        assert ref in refs_on_board, (
            f"Component {ref} not found. Present: {sorted(refs_on_board)}"
        )


# ── Net Connectivity ──────────────────────────────────────────────────────
class TestNetConnectivity:
    @pytest.mark.parametrize("net_name", EXPECTED_NETS)
    def test_net_connectivity(self, board, net_name):
        """Each required net must exist on the board."""
        netinfo = board.GetNetInfo()
        net = netinfo.GetNetItem(net_name)
        assert net is not None, f"Net '{net_name}' not found on board"
        # Net code 0 = unassigned
        assert net.GetNetCode() > 0, f"Net '{net_name}' exists but has no net code"


# ── DRC ───────────────────────────────────────────────────────────────────
class TestDRC:
    def test_drc_passes(self, board, pcbnew_module, tmp_path):
        """DRC must report 0 violations."""
        import json
        import subprocess
        from pathlib import Path

        board_path = Path(__file__).resolve().parent.parent / BOARD_FILE
        report_path = tmp_path / "drc_report.json"

        # Find kicad-cli
        import shutil
        kicad_cli = shutil.which("kicad-cli")
        if not kicad_cli:
            # Try config.json path
            config_file = Path(__file__).resolve().parent.parent / "config.json"
            if config_file.exists():
                config = json.loads(config_file.read_text())
                kicad_cli = config.get("kicad_cli_path", "")
            if not kicad_cli or not Path(kicad_cli).exists():
                pytest.skip("kicad-cli not found")

        result = subprocess.run(
            [
                str(kicad_cli), "pcb", "drc",
                "--output", str(report_path),
                "--format", "json",
                str(board_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if report_path.exists():
            report = json.loads(report_path.read_text())
            violations = report.get("violations", [])
            assert len(violations) == 0, (
                f"DRC found {len(violations)} violation(s):\n"
                + "\n".join(
                    f"  - {v.get('type', '?')}: {v.get('description', '?')}"
                    for v in violations[:10]
                )
            )
        else:
            # If no report file, check return code
            assert result.returncode == 0, (
                f"kicad-cli DRC failed: {result.stderr.strip()}"
            )

    def test_no_unconnected_items(self, board, pcbnew_module, tmp_path):
        """DRC must report 0 unconnected pad pairs."""
        import json
        import subprocess
        from pathlib import Path

        board_path = Path(__file__).resolve().parent.parent / BOARD_FILE
        report_path = tmp_path / "drc_unconnected_report.json"

        import shutil
        kicad_cli = shutil.which("kicad-cli")
        if not kicad_cli:
            config_file = Path(__file__).resolve().parent.parent / "config.json"
            if config_file.exists():
                config = json.loads(config_file.read_text())
                kicad_cli = config.get("kicad_cli_path", "")
            if not kicad_cli or not Path(kicad_cli).exists():
                pytest.skip("kicad-cli not found")

        subprocess.run(
            [
                str(kicad_cli), "pcb", "drc",
                "--output", str(report_path),
                "--format", "json",
                str(board_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if report_path.exists():
            report = json.loads(report_path.read_text())
            unconnected = report.get("unconnected_items", [])
            assert len(unconnected) == 0, (
                f"Board has {len(unconnected)} unconnected pad pair(s):\n"
                + "\n".join(
                    f"  - {' <-> '.join(i.get('description', '?') for i in u.get('items', []))}"
                    for u in unconnected[:10]
                )
            )
        else:
            pytest.skip("DRC report not generated")


# ── Routing ──────────────────────────────────────────────────────────────
class TestRouting:
    def test_has_traces(self, board):
        """Board must have routed traces (not just zones)."""
        track_count = 0
        for track in board.GetTracks():
            if track.GetClass() != "PCB_VIA":
                track_count += 1
        assert track_count > 0, (
            "Board has 0 routed traces — routing was skipped. "
            "The agent must create PCB_TRACK segments between pads."
        )

    def test_has_vias(self, board):
        """Board must have vias for layer transitions and ground stitching."""
        via_count = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
        assert via_count > 0, (
            "Board has 0 vias — no layer transitions or ground stitching. "
            "The agent must create PCB_VIA objects."
        )

    def test_has_ground_zone(self, board, pcbnew_module):
        """Board must have a GND copper zone on B.Cu."""
        found_bcu_gnd = False
        for i in range(board.GetAreaCount()):
            zone = board.GetArea(i)
            layer = zone.GetLayer()
            net = zone.GetNetname()
            if layer == pcbnew_module.B_Cu and net == "GND":
                found_bcu_gnd = True
                break
        assert found_bcu_gnd, (
            "No GND zone found on B.Cu — the board has no ground plane."
        )
