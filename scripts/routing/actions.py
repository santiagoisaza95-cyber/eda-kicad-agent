"""Route actions — trace/via/zone placement with angle validation and DRC feedback.

All actions modify the board in-place and return a result dict with status
and any DRC violations caused by the action.
"""
from __future__ import annotations

import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional


def validate_trace_angles(
    points: list[tuple[float, float]],
) -> tuple[bool, str]:
    """Validate that all bends between consecutive segments are 45° multiples.

    Returns (True, "OK") if valid, or (False, error_message) if invalid.
    Individual segments can be any angle — we only check the BEND angle
    between consecutive segments. 90° bends are rejected.
    """
    if len(points) <= 2:
        return True, "OK"

    for i in range(len(points) - 2):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        x2, y2 = points[i + 2]

        dx1, dy1 = x1 - x0, y1 - y0
        dx2, dy2 = x2 - x1, y2 - y1

        # Skip zero-length segments
        len1 = math.hypot(dx1, dy1)
        len2 = math.hypot(dx2, dy2)
        if len1 < 0.001 or len2 < 0.001:
            continue

        # Calculate bend angle using atan2 difference
        angle1 = math.atan2(dy1, dx1)
        angle2 = math.atan2(dy2, dx2)
        bend = abs(math.degrees(angle2 - angle1)) % 360
        if bend > 180:
            bend = 360 - bend

        # Check if bend is a multiple of 45° (allow small tolerance)
        remainder = bend % 45
        is_45_multiple = remainder < 2.0 or remainder > 43.0

        if not is_45_multiple:
            return False, (
                f"Non-45° bend at waypoint {i + 1}: {bend:.1f}° "
                f"between ({x0},{y0})->({x1},{y1})->({x2},{y2})"
            )

        # Specifically reject 90° bends (they are 45° multiples but forbidden)
        is_90 = (88.0 < bend < 92.0)
        if is_90:
            return False, (
                f"90° bend at waypoint {i + 1}: "
                f"({x0},{y0})->({x1},{y1})->({x2},{y2}). "
                f"Use a 45° intermediate waypoint instead."
            )

    return True, "OK"


class RouteActions:
    """Actions that modify the pcbnew board with validation and feedback."""

    def __init__(self, board: Any, pcbnew: Any, board_path: str):
        self._board = board
        self._pcbnew = pcbnew
        self._board_path = board_path
        self._last_added: list[Any] = []  # for undo

    def add_trace(
        self,
        net_name: str,
        waypoints: list[tuple[float, float]],
        width_mm: float,
        layer_name: str = "F.Cu",
    ) -> dict[str, Any]:
        """Add a multi-segment trace and return DRC feedback.

        Returns {"status": "ok"|"error", "segments_added": N, "message": str}
        """
        # Validate angles first
        ok, msg = validate_trace_angles(waypoints)
        if not ok:
            return {"status": "error", "segments_added": 0, "message": msg}

        if len(waypoints) < 2:
            return {"status": "error", "segments_added": 0, "message": "Need at least 2 waypoints"}

        # Resolve net
        net = self._board.GetNetInfo().GetNetItem(net_name)
        if net is None:
            return {"status": "error", "segments_added": 0, "message": f"Net '{net_name}' not found"}

        # Resolve layer
        layer = self._board.GetLayerID(layer_name)
        if layer < 0:
            return {"status": "error", "segments_added": 0, "message": f"Layer '{layer_name}' not found"}

        from_mm = self._pcbnew.FromMM
        self._last_added = []

        for i in range(len(waypoints) - 1):
            track = self._pcbnew.PCB_TRACK(self._board)
            track.SetStart(self._pcbnew.VECTOR2I(
                from_mm(waypoints[i][0]), from_mm(waypoints[i][1])))
            track.SetEnd(self._pcbnew.VECTOR2I(
                from_mm(waypoints[i + 1][0]), from_mm(waypoints[i + 1][1])))
            track.SetWidth(from_mm(width_mm))
            track.SetLayer(layer)
            track.SetNet(net)
            self._board.Add(track)
            self._last_added.append(track)

        return {
            "status": "ok",
            "segments_added": len(waypoints) - 1,
            "message": f"Routed {net_name}: {len(waypoints)} waypoints, {len(waypoints)-1} segments",
        }

    def add_via(
        self,
        net_name: str,
        x_mm: float,
        y_mm: float,
        drill_mm: float = 0.3,
        pad_mm: float = 0.6,
    ) -> dict[str, Any]:
        """Place a via and return feedback."""
        net = self._board.GetNetInfo().GetNetItem(net_name)
        if net is None:
            return {"status": "error", "message": f"Net '{net_name}' not found"}

        from_mm = self._pcbnew.FromMM
        via = self._pcbnew.PCB_VIA(self._board)
        via.SetPosition(self._pcbnew.VECTOR2I(from_mm(x_mm), from_mm(y_mm)))
        via.SetDrill(from_mm(drill_mm))
        via.SetWidth(from_mm(pad_mm))
        via.SetNet(net)
        via.SetLayerPair(self._pcbnew.F_Cu, self._pcbnew.B_Cu)
        self._board.Add(via)
        self._last_added = [via]

        return {
            "status": "ok",
            "message": f"Via placed at ({x_mm}, {y_mm}) on net {net_name}",
        }

    def undo_last(self) -> dict[str, Any]:
        """Remove the items added by the last action."""
        if not self._last_added:
            return {"status": "error", "message": "Nothing to undo"}

        count = len(self._last_added)
        for item in self._last_added:
            self._board.Remove(item)
        self._last_added = []
        return {"status": "ok", "message": f"Removed {count} item(s)"}

    def remove_net_traces(self, net_name: str) -> dict[str, Any]:
        """Rip up all traces and vias for a net (keep pads and zones)."""
        to_remove = []
        for track in self._board.GetTracks():
            if track.GetNetname() == net_name:
                to_remove.append(track)
        for item in to_remove:
            self._board.Remove(item)
        return {
            "status": "ok",
            "message": f"Removed {len(to_remove)} traces/vias from net {net_name}",
        }

    def add_zone(
        self,
        net_name: str,
        layer_name: str,
        priority: int = 0,
    ) -> dict[str, Any]:
        """Create a GND copper zone covering the full board."""
        net = self._board.GetNetInfo().GetNetItem(net_name)
        if net is None:
            return {"status": "error", "message": f"Net '{net_name}' not found"}

        layer = self._board.GetLayerID(layer_name)
        zone = self._pcbnew.ZONE(self._board)
        zone.SetNet(net)
        zone.SetLayer(layer)
        zone.SetAssignedPriority(priority)

        bbox = self._board.GetBoardEdgesBoundingBox()
        margin = self._pcbnew.FromMM(0.5)

        outline = zone.Outline()
        outline.NewOutline()
        outline.Append(bbox.GetLeft() + margin, bbox.GetTop() + margin)
        outline.Append(bbox.GetRight() - margin, bbox.GetTop() + margin)
        outline.Append(bbox.GetRight() - margin, bbox.GetBottom() - margin)
        outline.Append(bbox.GetLeft() + margin, bbox.GetBottom() - margin)

        zone.SetIslandRemovalMode(self._pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        zone.SetLocalClearance(self._pcbnew.FromMM(0.3))
        self._board.Add(zone)

        return {"status": "ok", "message": f"Zone {net_name} on {layer_name} (priority {priority})"}

    def fill_zones(self) -> dict[str, Any]:
        """Fill all zones on the board."""
        filler = self._pcbnew.ZONE_FILLER(self._board)
        filler.Fill(self._board.Zones())
        return {"status": "ok", "message": f"Filled {self._board.GetAreaCount()} zone(s)"}

    def save_board(self) -> dict[str, Any]:
        """Save the board to disk."""
        self._pcbnew.SaveBoard(self._board_path, self._board)
        return {"status": "ok", "message": f"Saved to {self._board_path}"}

    def run_drc(self) -> dict[str, Any]:
        """Run DRC via kicad-cli and return violations + unconnected counts."""
        # Save first
        self.save_board()

        config_file = Path(self._board_path).parent.parent / "config.json"
        kicad_cli = None
        if config_file.exists():
            config = json.loads(config_file.read_text())
            kicad_cli = config.get("kicad_cli_path", "")

        import shutil
        if not kicad_cli:
            kicad_cli = shutil.which("kicad-cli")
        if not kicad_cli or not Path(kicad_cli).exists():
            return {"status": "error", "message": "kicad-cli not found"}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            report_path = f.name

        subprocess.run(
            [str(kicad_cli), "pcb", "drc", "--output", report_path,
             "--format", "json", self._board_path],
            capture_output=True, text=True, timeout=60,
        )

        report_file = Path(report_path)
        if report_file.exists():
            report = json.loads(report_file.read_text())
            violations = report.get("violations", [])
            unconnected = report.get("unconnected_items", [])
            report_file.unlink()
            return {
                "status": "ok",
                "violations": len(violations),
                "unconnected": len(unconnected),
                "violation_details": [
                    {"type": v.get("type", "?"), "desc": v.get("description", "?")}
                    for v in violations[:5]
                ],
                "unconnected_details": [
                    {
                        "net": u.get("description", "?"),
                        "items": [i.get("description", "?") for i in u.get("items", [])]
                    }
                    for u in unconnected[:5]
                ],
            }
        return {"status": "error", "message": "DRC report not generated"}
