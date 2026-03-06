"""Tests for board perception — requires pcbnew (KiCad bundled Python)."""
import pytest
import json
from pathlib import Path

# These tests require a board file. Skip if not available.
BOARD_FILE = "output/blue_pill.kicad_pcb"


@pytest.fixture(scope="module")
def pcbnew_module():
    try:
        import pcbnew
        return pcbnew
    except ImportError:
        pytest.skip("pcbnew not importable")


@pytest.fixture(scope="module")
def perception(pcbnew_module):
    """Create a BoardPerception from the blue_pill board if it exists."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from routing.perception import BoardPerception

    board_path = Path(__file__).resolve().parent.parent / BOARD_FILE
    if not board_path.exists():
        pytest.skip(f"Board file not found: {board_path}")
    board = pcbnew_module.LoadBoard(str(board_path))
    return BoardPerception(board, pcbnew_module)


class TestBoardPerception:
    def test_board_summary_has_required_keys(self, perception):
        summary = perception.get_board_summary()
        assert "width_mm" in summary
        assert "height_mm" in summary
        assert "net_count" in summary
        assert "trace_count" in summary
        assert "via_count" in summary
        assert "unrouted_count" in summary
        assert "component_count" in summary

    def test_get_unrouted_nets_returns_list(self, perception):
        nets = perception.get_unrouted_nets()
        assert isinstance(nets, list)

    def test_get_net_pads_returns_positions(self, perception):
        pads = perception.get_net_pads("GND")
        assert isinstance(pads, list)
        if pads:
            assert "x_mm" in pads[0]
            assert "y_mm" in pads[0]
            assert "ref" in pads[0]

    def test_get_obstacles_in_region_returns_list(self, perception):
        obstacles = perception.get_obstacles_in_region(0, 0, 44.5, 24.0)
        assert isinstance(obstacles, list)

    def test_board_summary_is_json_serializable(self, perception):
        summary = perception.get_board_summary()
        serialized = json.dumps(summary)
        assert len(serialized) > 10


class TestPerceptionWithoutBoard:
    """Tests that work without a board file (unit tests for helpers)."""

    def test_import_works(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from routing.perception import BoardPerception
        assert BoardPerception is not None
