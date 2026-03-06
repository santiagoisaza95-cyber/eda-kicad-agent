"""Board perception layer — reads pcbnew board state for LLM routing decisions.

Provides compact JSON-serializable views of the board state that fit within
an LLM context window (~500-2000 tokens per query).
"""
from __future__ import annotations

from typing import Any


class BoardPerception:
    """Reads a pcbnew board and provides perception queries for routing."""

    def __init__(self, board: Any, pcbnew: Any):
        self._board = board
        self._pcbnew = pcbnew

    def get_board_summary(self) -> dict[str, Any]:
        """High-level board state: dimensions, counts, completion status."""
        bbox = self._board.GetBoardEdgesBoundingBox()
        to_mm = self._pcbnew.ToMM

        trace_count = 0
        via_count = 0
        for track in self._board.GetTracks():
            if track.GetClass() == "PCB_VIA":
                via_count += 1
            else:
                trace_count += 1

        zone_count = self._board.GetAreaCount()
        nets = self._get_all_signal_nets()

        # Count unrouted by checking DRC would be expensive, so approximate
        # by checking nets with pads that have no traces
        unrouted = self._count_nets_without_traces(nets)

        return {
            "width_mm": round(to_mm(bbox.GetWidth()), 2),
            "height_mm": round(to_mm(bbox.GetHeight()), 2),
            "component_count": len(list(self._board.GetFootprints())),
            "net_count": len(nets),
            "trace_count": trace_count,
            "via_count": via_count,
            "zone_count": zone_count,
            "unrouted_count": unrouted,
        }

    def get_unrouted_nets(self) -> list[dict[str, Any]]:
        """List nets that have pads but no connecting traces."""
        result = []
        nets = self._get_all_signal_nets()
        traced_nets = self._get_traced_net_names()

        for net_name in nets:
            if net_name not in traced_nets:
                pads = self.get_net_pads(net_name)
                if len(pads) >= 2:
                    result.append({
                        "net": net_name,
                        "pad_count": len(pads),
                        "pads": pads,
                    })
        return result

    def get_net_pads(self, net_name: str) -> list[dict[str, Any]]:
        """Get all pad positions for a given net."""
        to_mm = self._pcbnew.ToMM
        pads = []
        for fp in self._board.GetFootprints():
            ref = fp.GetReference()
            for pad in fp.Pads():
                if pad.GetNetname() == net_name:
                    pos = pad.GetPosition()
                    pads.append({
                        "ref": ref,
                        "pad": pad.GetName(),
                        "x_mm": round(to_mm(pos.x), 3),
                        "y_mm": round(to_mm(pos.y), 3),
                        "layer": self._board.GetLayerName(pad.GetLayer()),
                    })
        return pads

    def get_obstacles_in_region(
        self, x1_mm: float, y1_mm: float, x2_mm: float, y2_mm: float
    ) -> list[dict[str, Any]]:
        """Get all obstacles (pads, traces, vias, component bodies) in a bounding box."""
        to_mm = self._pcbnew.ToMM
        from_mm = self._pcbnew.FromMM
        obstacles = []

        # Component bodies
        for fp in self._board.GetFootprints():
            bbox = fp.GetBoundingBox()
            fx = to_mm(bbox.GetCenter().x)
            fy = to_mm(bbox.GetCenter().y)
            fw = to_mm(bbox.GetWidth())
            fh = to_mm(bbox.GetHeight())
            if self._overlaps_region(fx, fy, fw, fh, x1_mm, y1_mm, x2_mm, y2_mm):
                obstacles.append({
                    "type": "component",
                    "ref": fp.GetReference(),
                    "x_mm": round(fx, 3),
                    "y_mm": round(fy, 3),
                    "width_mm": round(fw, 3),
                    "height_mm": round(fh, 3),
                })

        # Existing traces
        for track in self._board.GetTracks():
            if track.GetClass() == "PCB_VIA":
                pos = track.GetPosition()
                vx = to_mm(pos.x)
                vy = to_mm(pos.y)
                if x1_mm <= vx <= x2_mm and y1_mm <= vy <= y2_mm:
                    obstacles.append({
                        "type": "via",
                        "x_mm": round(vx, 3),
                        "y_mm": round(vy, 3),
                        "net": track.GetNetname(),
                        "drill_mm": round(to_mm(track.GetDrillValue()), 3),
                    })
            else:
                start = track.GetStart()
                end = track.GetEnd()
                sx, sy = to_mm(start.x), to_mm(start.y)
                ex, ey = to_mm(end.x), to_mm(end.y)
                if self._segment_in_region(sx, sy, ex, ey, x1_mm, y1_mm, x2_mm, y2_mm):
                    obstacles.append({
                        "type": "trace",
                        "net": track.GetNetname(),
                        "start": [round(sx, 3), round(sy, 3)],
                        "end": [round(ex, 3), round(ey, 3)],
                        "width_mm": round(to_mm(track.GetWidth()), 3),
                        "layer": self._board.GetLayerName(track.GetLayer()),
                    })

        return obstacles

    def get_routed_net_summary(self) -> list[dict[str, Any]]:
        """Summary of already-routed nets with trace counts."""
        net_traces: dict[str, int] = {}
        for track in self._board.GetTracks():
            if track.GetClass() != "PCB_VIA":
                name = track.GetNetname()
                net_traces[name] = net_traces.get(name, 0) + 1
        return [{"net": n, "traces": c} for n, c in sorted(net_traces.items())]

    # -- Internal helpers --

    def _get_all_signal_nets(self) -> list[str]:
        """Get all non-empty, non-unconnected net names."""
        nets = []
        netinfo = self._board.GetNetInfo()
        for i in range(netinfo.GetNetCount()):
            net = netinfo.GetNetItem(i)
            name = net.GetNetname()
            if name and not name.startswith("unconnected-"):
                nets.append(name)
        return nets

    def _get_traced_net_names(self) -> set[str]:
        """Get names of nets that have at least one trace."""
        traced = set()
        for track in self._board.GetTracks():
            name = track.GetNetname()
            if name:
                traced.add(name)
        return traced

    def _count_nets_without_traces(self, nets: list[str]) -> int:
        """Count nets that have pads but no traces connecting them."""
        traced = self._get_traced_net_names()
        count = 0
        for net_name in nets:
            if net_name not in traced:
                # Check if this net has at least 2 pads (needs routing)
                pad_count = 0
                for fp in self._board.GetFootprints():
                    for pad in fp.Pads():
                        if pad.GetNetname() == net_name:
                            pad_count += 1
                            if pad_count >= 2:
                                break
                    if pad_count >= 2:
                        break
                if pad_count >= 2:
                    count += 1
        return count

    @staticmethod
    def _overlaps_region(
        cx: float, cy: float, w: float, h: float,
        x1: float, y1: float, x2: float, y2: float,
    ) -> bool:
        half_w, half_h = w / 2, h / 2
        return not (cx + half_w < x1 or cx - half_w > x2 or
                    cy + half_h < y1 or cy - half_h > y2)

    @staticmethod
    def _segment_in_region(
        sx: float, sy: float, ex: float, ey: float,
        x1: float, y1: float, x2: float, y2: float,
    ) -> bool:
        return ((x1 <= sx <= x2 and y1 <= sy <= y2) or
                (x1 <= ex <= x2 and y1 <= ey <= y2))
