"""Integration test: perception + pathfinder working together on a real board."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

REF_BOARD = "reference/STM32-Blue-Pill/stm32 blue pill.kicad_pcb"


@pytest.fixture(scope="module")
def pcbnew_module():
    try:
        import pcbnew
        return pcbnew
    except ImportError:
        pytest.skip("pcbnew not importable")


@pytest.fixture(scope="module")
def ref_board(pcbnew_module):
    board_path = Path(__file__).resolve().parent.parent / REF_BOARD
    if not board_path.exists():
        pytest.skip(f"Reference board not found: {board_path}")
    return pcbnew_module.LoadBoard(str(board_path))


class TestWorkbenchIntegration:
    def test_perception_reads_reference_board(self, ref_board, pcbnew_module):
        from routing.perception import BoardPerception
        p = BoardPerception(ref_board, pcbnew_module)
        summary = p.get_board_summary()
        assert summary["component_count"] > 0
        assert summary["net_count"] > 0

    def test_pathfinder_finds_path_on_empty_area(self):
        from routing.pathfinder import AStarRouter
        router = AStarRouter(width_mm=44.5, height_mm=24.0, resolution_mm=0.25)
        path = router.find_path((5, 12), (40, 12), 0.25, 0.2)
        assert path is not None
        assert len(path) >= 2

    def test_pathfinder_with_perception_obstacles(self, ref_board, pcbnew_module):
        from routing.perception import BoardPerception
        from routing.pathfinder import AStarRouter, Obstacle

        p = BoardPerception(ref_board, pcbnew_module)
        summary = p.get_board_summary()

        router = AStarRouter(
            width_mm=summary["width_mm"],
            height_mm=summary["height_mm"],
            resolution_mm=0.25,
        )

        # Load all component obstacles
        obstacles = p.get_obstacles_in_region(0, 0, summary["width_mm"], summary["height_mm"])
        for obs in obstacles:
            if obs["type"] == "component":
                router.add_obstacle(
                    Obstacle(obs["x_mm"], obs["y_mm"], obs["width_mm"], obs["height_mm"]),
                    clearance_mm=0.2,
                )

        # Try to find ANY path across the board
        path = router.find_path(
            (2, summary["height_mm"] / 2),
            (summary["width_mm"] - 2, summary["height_mm"] / 2),
            0.25, 0.2,
        )
        # Path may or may not exist depending on obstacles, but should not crash
        assert path is None or len(path) >= 2

    def test_angle_validation_on_pathfinder_output(self):
        """A* output should always pass angle validation."""
        from routing.pathfinder import AStarRouter, Obstacle
        from routing.actions import validate_trace_angles

        router = AStarRouter(width_mm=30, height_mm=20, resolution_mm=0.25)
        router.add_obstacle(Obstacle(15, 10, 4, 4), clearance_mm=0.2)

        path = router.find_path((3, 10), (27, 10), 0.25, 0.2)
        assert path is not None

        ok, msg = validate_trace_angles(path)
        assert ok, f"A* produced invalid angles: {msg}"
