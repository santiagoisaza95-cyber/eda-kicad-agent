"""Tests for the A* pathfinder --- pure geometry, no pcbnew needed."""
import pytest
import sys
from pathlib import Path

# Add scripts to path so we can import without pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from routing.pathfinder import AStarRouter, Grid, Obstacle


class TestGrid:
    def test_grid_creation(self):
        """Grid should be created with correct dimensions."""
        grid = Grid(width_mm=44.5, height_mm=24.0, resolution_mm=0.1)
        assert grid.cols == 445
        assert grid.rows == 240

    def test_grid_mm_to_cell(self):
        """Convert mm coordinates to grid cell indices."""
        grid = Grid(width_mm=44.5, height_mm=24.0, resolution_mm=0.1)
        col, row = grid.mm_to_cell(10.0, 5.0)
        assert col == 100
        assert row == 50

    def test_grid_cell_to_mm(self):
        """Convert grid cell back to mm coordinates (cell center)."""
        grid = Grid(width_mm=44.5, height_mm=24.0, resolution_mm=0.1)
        x, y = grid.cell_to_mm(100, 50)
        assert abs(x - 10.05) < 0.01  # center of cell
        assert abs(y - 5.05) < 0.01

    def test_grid_add_obstacle(self):
        """Obstacles should mark cells as blocked."""
        grid = Grid(width_mm=10.0, height_mm=10.0, resolution_mm=0.5)
        obs = Obstacle(x_mm=5.0, y_mm=5.0, width_mm=2.0, height_mm=2.0)
        grid.add_obstacle(obs, clearance_mm=0.2)
        col, row = grid.mm_to_cell(5.0, 5.0)
        assert grid.is_blocked(col, row)

    def test_grid_outside_obstacle_is_free(self):
        """Cells outside obstacle + clearance should be free."""
        grid = Grid(width_mm=10.0, height_mm=10.0, resolution_mm=0.5)
        obs = Obstacle(x_mm=5.0, y_mm=5.0, width_mm=1.0, height_mm=1.0)
        grid.add_obstacle(obs, clearance_mm=0.2)
        col, row = grid.mm_to_cell(1.0, 1.0)
        assert not grid.is_blocked(col, row)


class TestAStarRouter:
    def test_straight_path(self):
        """Route a straight horizontal path with no obstacles."""
        router = AStarRouter(width_mm=20.0, height_mm=10.0, resolution_mm=0.5)
        path = router.find_path(
            start_mm=(2.0, 5.0),
            end_mm=(18.0, 5.0),
            trace_width_mm=0.25,
            clearance_mm=0.2,
        )
        assert path is not None
        assert len(path) >= 2
        # Start and end should be close to requested
        assert abs(path[0][0] - 2.0) < 0.5
        assert abs(path[-1][0] - 18.0) < 0.5

    def test_path_around_obstacle(self):
        """Route around a rectangular obstacle."""
        router = AStarRouter(width_mm=20.0, height_mm=10.0, resolution_mm=0.5)
        router.add_obstacle(Obstacle(x_mm=10.0, y_mm=5.0, width_mm=3.0, height_mm=8.0))
        path = router.find_path(
            start_mm=(2.0, 5.0),
            end_mm=(18.0, 5.0),
            trace_width_mm=0.25,
            clearance_mm=0.2,
        )
        assert path is not None
        assert len(path) >= 3  # needs at least one waypoint to go around

    def test_no_path_exists(self):
        """Return None when no path exists (fully blocked)."""
        router = AStarRouter(width_mm=10.0, height_mm=10.0, resolution_mm=0.5)
        # Block entire middle column
        router.add_obstacle(Obstacle(x_mm=5.0, y_mm=5.0, width_mm=1.0, height_mm=10.0))
        path = router.find_path(
            start_mm=(2.0, 5.0),
            end_mm=(8.0, 5.0),
            trace_width_mm=0.25,
            clearance_mm=0.2,
        )
        assert path is None

    def test_45_degree_angles_only(self):
        """All path segments must be at 0, 45, 90, 135, 180, 225, 270, or 315 degrees."""
        import math
        router = AStarRouter(width_mm=20.0, height_mm=20.0, resolution_mm=0.5)
        path = router.find_path(
            start_mm=(2.0, 2.0),
            end_mm=(18.0, 15.0),
            trace_width_mm=0.25,
            clearance_mm=0.2,
        )
        assert path is not None
        for i in range(len(path) - 1):
            dx = path[i + 1][0] - path[i][0]
            dy = path[i + 1][1] - path[i][1]
            if abs(dx) < 0.001 and abs(dy) < 0.001:
                continue  # zero-length segment, skip
            angle = math.degrees(math.atan2(dy, dx)) % 45
            assert angle < 0.1 or abs(angle - 45) < 0.1, (
                f"Segment {i} has non-45 degree angle: ({path[i]}) -> ({path[i+1]})"
            )

    def test_path_simplification(self):
        """Collinear points should be merged into fewer waypoints."""
        router = AStarRouter(width_mm=20.0, height_mm=10.0, resolution_mm=0.5)
        path = router.find_path(
            start_mm=(2.0, 5.0),
            end_mm=(18.0, 5.0),
            trace_width_mm=0.25,
            clearance_mm=0.2,
        )
        assert path is not None
        # A straight horizontal line should simplify to just 2 points
        assert len(path) == 2

    def test_clearance_inflation(self):
        """Path should maintain clearance distance from obstacles."""
        router = AStarRouter(width_mm=20.0, height_mm=10.0, resolution_mm=0.25)
        router.add_obstacle(Obstacle(x_mm=10.0, y_mm=5.0, width_mm=2.0, height_mm=2.0))
        path = router.find_path(
            start_mm=(2.0, 5.0),
            end_mm=(18.0, 5.0),
            trace_width_mm=0.25,
            clearance_mm=0.5,
        )
        assert path is not None
        # Every waypoint should be at least clearance + half_width from obstacle center area
        for x, y in path:
            if 9.0 <= x <= 11.0:  # near obstacle
                dist_y = abs(y - 5.0)
                assert dist_y >= 1.0 + 0.5 + 0.125 - 0.3, (
                    f"Point ({x}, {y}) too close to obstacle"
                )
