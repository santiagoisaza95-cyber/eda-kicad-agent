"""A* pathfinder for PCB trace routing on an 8-directional grid.

This module has NO pcbnew dependency --- it operates purely on mm coordinates.
The 8-directional grid naturally produces 45-degree routing (0, 45, 90, etc.).
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Obstacle:
    """A rectangular obstacle in mm coordinates (center + size)."""
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float


class Grid:
    """2D occupancy grid for pathfinding. Cells are either free or blocked."""

    def __init__(self, width_mm: float, height_mm: float, resolution_mm: float = 0.1):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.resolution_mm = resolution_mm
        self.cols = int(width_mm / resolution_mm)
        self.rows = int(height_mm / resolution_mm)
        # bitfield: True = blocked
        self._blocked: set[tuple[int, int]] = set()

    def mm_to_cell(self, x_mm: float, y_mm: float) -> tuple[int, int]:
        """Convert mm coordinates to grid cell (col, row)."""
        col = int(x_mm / self.resolution_mm)
        row = int(y_mm / self.resolution_mm)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    def cell_to_mm(self, col: int, row: int) -> tuple[float, float]:
        """Convert grid cell to mm coordinates (center of cell)."""
        x = (col + 0.5) * self.resolution_mm
        y = (row + 0.5) * self.resolution_mm
        return x, y

    def add_obstacle(self, obs: Obstacle, clearance_mm: float = 0.0) -> None:
        """Mark cells covered by obstacle + clearance as blocked."""
        half_w = obs.width_mm / 2 + clearance_mm
        half_h = obs.height_mm / 2 + clearance_mm
        min_col, min_row = self.mm_to_cell(obs.x_mm - half_w, obs.y_mm - half_h)
        max_col, max_row = self.mm_to_cell(obs.x_mm + half_w, obs.y_mm + half_h)
        for c in range(min_col, max_col + 1):
            for r in range(min_row, max_row + 1):
                if 0 <= c < self.cols and 0 <= r < self.rows:
                    self._blocked.add((c, r))

    def add_trace_obstacle(
        self, x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float,
        width_mm: float, clearance_mm: float = 0.0
    ) -> None:
        """Mark cells along a trace segment as blocked (line with width)."""
        half_w = width_mm / 2 + clearance_mm
        # Rasterize the line with thickness
        c1, r1 = self.mm_to_cell(x1_mm, y1_mm)
        c2, r2 = self.mm_to_cell(x2_mm, y2_mm)
        steps = max(abs(c2 - c1), abs(r2 - r1), 1)
        inflate = int(half_w / self.resolution_mm) + 1
        for s in range(steps + 1):
            t = s / steps
            c = int(c1 + t * (c2 - c1))
            r = int(r1 + t * (r2 - r1))
            for dc in range(-inflate, inflate + 1):
                for dr in range(-inflate, inflate + 1):
                    nc, nr = c + dc, r + dr
                    if 0 <= nc < self.cols and 0 <= nr < self.rows:
                        self._blocked.add((nc, nr))

    def is_blocked(self, col: int, row: int) -> bool:
        return (col, row) in self._blocked

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows


# 8 directions: N, NE, E, SE, S, SW, W, NW
_DIRECTIONS = [
    (0, -1), (1, -1), (1, 0), (1, 1),
    (0, 1), (-1, 1), (-1, 0), (-1, -1),
]
_SQRT2 = math.sqrt(2)
_DIR_COSTS = [1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2, 1.0, _SQRT2]


def _heuristic(c1: int, r1: int, c2: int, r2: int) -> float:
    """Octile distance heuristic (admissible for 8-directional grid)."""
    dx = abs(c2 - c1)
    dy = abs(r2 - r1)
    return max(dx, dy) + (_SQRT2 - 1) * min(dx, dy)


def _simplify_path(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Remove collinear intermediate points (same direction)."""
    if len(points) <= 2:
        return points
    result = [points[0]]
    for i in range(1, len(points) - 1):
        # Check if direction changes
        dx1 = points[i][0] - points[i - 1][0]
        dy1 = points[i][1] - points[i - 1][1]
        dx2 = points[i + 1][0] - points[i][0]
        dy2 = points[i + 1][1] - points[i][1]
        # Normalize to signs
        s1 = (0 if abs(dx1) < 0.001 else (1 if dx1 > 0 else -1),
              0 if abs(dy1) < 0.001 else (1 if dy1 > 0 else -1))
        s2 = (0 if abs(dx2) < 0.001 else (1 if dx2 > 0 else -1),
              0 if abs(dy2) < 0.001 else (1 if dy2 > 0 else -1))
        if s1 != s2:
            result.append(points[i])
    result.append(points[-1])
    return result


class AStarRouter:
    """A* pathfinder on an 8-directional grid. Produces 45-degree-native paths."""

    def __init__(
        self,
        width_mm: float,
        height_mm: float,
        resolution_mm: float = 0.1,
    ):
        self.grid = Grid(width_mm, height_mm, resolution_mm)
        self._obstacles: list[Obstacle] = []

    def add_obstacle(self, obs: Obstacle, clearance_mm: float = 0.0) -> None:
        """Add a rectangular obstacle to the routing grid."""
        self._obstacles.append(obs)
        self.grid.add_obstacle(obs, clearance_mm)

    def add_trace(
        self, x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float,
        width_mm: float, clearance_mm: float = 0.0,
    ) -> None:
        """Add an existing trace segment as an obstacle."""
        self.grid.add_trace_obstacle(x1_mm, y1_mm, x2_mm, y2_mm, width_mm, clearance_mm)

    def find_path(
        self,
        start_mm: tuple[float, float],
        end_mm: tuple[float, float],
        trace_width_mm: float = 0.25,
        clearance_mm: float = 0.2,
    ) -> Optional[list[tuple[float, float]]]:
        """Find an obstacle-avoiding path from start to end.

        Returns a list of (x_mm, y_mm) waypoints, or None if no path exists.
        All segments between consecutive waypoints are at 45-degree multiples.
        Collinear segments are merged (simplified).
        """
        # Inflate obstacles by half trace width + clearance for this path
        # We build an expanded blocked set so the trace keeps its distance
        inflate_cells = int((trace_width_mm / 2 + clearance_mm) / self.grid.resolution_mm) + 1

        blocked = set(self.grid._blocked)
        if inflate_cells > 0:
            expanded: set[tuple[int, int]] = set()
            for bc, br in blocked:
                for dc in range(-inflate_cells, inflate_cells + 1):
                    for dr in range(-inflate_cells, inflate_cells + 1):
                        nc, nr = bc + dc, br + dr
                        if 0 <= nc < self.grid.cols and 0 <= nr < self.grid.rows:
                            expanded.add((nc, nr))
            blocked = expanded

        sc, sr = self.grid.mm_to_cell(*start_mm)
        ec, er = self.grid.mm_to_cell(*end_mm)

        # Quick check: start/end blocked
        if (sc, sr) in blocked or (ec, er) in blocked:
            return None

        # A* search
        open_set: list[tuple[float, int, int]] = []  # (f_cost, col, row)
        heapq.heappush(open_set, (_heuristic(sc, sr, ec, er), sc, sr))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {(sc, sr): 0.0}

        visited: set[tuple[int, int]] = set()
        max_iterations = self.grid.cols * self.grid.rows * 2

        iterations = 0
        while open_set and iterations < max_iterations:
            iterations += 1
            _, cc, cr = heapq.heappop(open_set)

            if (cc, cr) in visited:
                continue
            visited.add((cc, cr))

            if cc == ec and cr == er:
                # Reconstruct path
                path_cells = []
                node = (ec, er)
                while node in came_from:
                    path_cells.append(node)
                    node = came_from[node]
                path_cells.append((sc, sr))
                path_cells.reverse()

                # Convert to mm
                path_mm = [self.grid.cell_to_mm(c, r) for c, r in path_cells]
                return _simplify_path(path_mm)

            for i, (dc, dr) in enumerate(_DIRECTIONS):
                nc, nr = cc + dc, cr + dr
                if not self.grid.in_bounds(nc, nr):
                    continue
                if (nc, nr) in visited:
                    continue
                if (nc, nr) in blocked:
                    continue

                new_g = g_score[(cc, cr)] + _DIR_COSTS[i]
                if new_g < g_score.get((nc, nr), float("inf")):
                    g_score[(nc, nr)] = new_g
                    f = new_g + _heuristic(nc, nr, ec, er)
                    came_from[(nc, nr)] = (cc, cr)
                    heapq.heappush(open_set, (f, nc, nr))

        return None  # No path found
