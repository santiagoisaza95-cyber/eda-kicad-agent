#!/usr/bin/env python3
"""Routing CLI — iterative routing interface for the LLM agent.

The agent calls this script repeatedly via Bash. Each call performs one action
on the board and returns JSON with the result + board state feedback.

Usage examples:
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action summary
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action unrouted
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action net_pads --net HSE_IN
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action obstacles --bbox 10,5,25,15
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action find_path --start 15,10 --end 22,14 --width 0.25
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action route --net HSE_IN --waypoints "15,10;18,12;22,14" --width 0.25 --layer F.Cu
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action via --net GND --pos 10,12 --drill 0.3 --pad 0.6
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action undo
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action rip_up --net HSE_IN
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action zone --net GND --layer B.Cu --priority 0
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action fill_zones
  python scripts/routing_cli.py --board output/blue_pill.kicad_pcb --action drc
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Routing CLI — iterative routing interface for the LLM agent",
        prog="routing_cli",
    )
    parser.add_argument("--board", required=True, help="Path to .kicad_pcb file")
    parser.add_argument("--action", required=True,
                        choices=["summary", "unrouted", "net_pads", "obstacles",
                                 "find_path", "route", "via", "undo", "rip_up",
                                 "zone", "fill_zones", "drc", "routed_summary"],
                        help="Action to perform")
    # Query params
    parser.add_argument("--net", help="Net name (for net_pads, route, via, rip_up, zone)")
    parser.add_argument("--bbox", help="Bounding box as x1,y1,x2,y2 in mm (for obstacles)")
    # Pathfinding params
    parser.add_argument("--start", help="Start point as x,y in mm")
    parser.add_argument("--end", help="End point as x,y in mm")
    parser.add_argument("--width", type=float, default=0.25, help="Trace width in mm")
    parser.add_argument("--clearance", type=float, default=0.2, help="Clearance in mm")
    # Route params
    parser.add_argument("--waypoints", help="Waypoints as 'x1,y1;x2,y2;...' in mm")
    parser.add_argument("--layer", default="F.Cu", help="Copper layer name")
    # Via params
    parser.add_argument("--pos", help="Via position as x,y in mm")
    parser.add_argument("--drill", type=float, default=0.3, help="Via drill diameter in mm")
    parser.add_argument("--pad", type=float, default=0.6, help="Via pad diameter in mm")
    # Zone params
    parser.add_argument("--priority", type=int, default=0, help="Zone priority")

    return parser.parse_args()


def output_json(data: dict) -> None:
    """Print JSON result to stdout."""
    print(json.dumps(data, indent=2))


def main() -> int:
    args = parse_args()

    board_path = Path(args.board)
    if not board_path.exists() and args.action not in ("--help",):
        output_json({"status": "error", "message": f"Board not found: {args.board}"})
        return 1

    try:
        import pcbnew
    except ImportError:
        output_json({"status": "error", "message": "pcbnew not importable. Use KiCad bundled Python."})
        return 1

    board = pcbnew.LoadBoard(str(board_path))

    from routing.perception import BoardPerception
    from routing.actions import RouteActions

    perception = BoardPerception(board, pcbnew)
    actions = RouteActions(board, pcbnew, str(board_path))

    # ── Perception actions ──
    if args.action == "summary":
        output_json(perception.get_board_summary())
        return 0

    elif args.action == "unrouted":
        output_json({"unrouted_nets": perception.get_unrouted_nets()})
        return 0

    elif args.action == "net_pads":
        if not args.net:
            output_json({"status": "error", "message": "--net required"})
            return 1
        output_json({"net": args.net, "pads": perception.get_net_pads(args.net)})
        return 0

    elif args.action == "obstacles":
        if not args.bbox:
            output_json({"status": "error", "message": "--bbox required (x1,y1,x2,y2)"})
            return 1
        coords = [float(x) for x in args.bbox.split(",")]
        output_json({"obstacles": perception.get_obstacles_in_region(*coords)})
        return 0

    elif args.action == "routed_summary":
        output_json({"routed_nets": perception.get_routed_net_summary()})
        return 0

    # ── Pathfinding ──
    elif args.action == "find_path":
        if not args.start or not args.end:
            output_json({"status": "error", "message": "--start and --end required (x,y)"})
            return 1
        start = tuple(float(x) for x in args.start.split(","))
        end = tuple(float(x) for x in args.end.split(","))

        from routing.pathfinder import AStarRouter, Obstacle

        summary = perception.get_board_summary()
        router = AStarRouter(
            width_mm=summary["width_mm"],
            height_mm=summary["height_mm"],
            resolution_mm=0.25,  # 0.25mm grid for reasonable performance
        )

        # Add board obstacles to the pathfinder grid
        # Expand search area around the path
        margin = 5.0
        x1 = min(start[0], end[0]) - margin
        y1 = min(start[1], end[1]) - margin
        x2 = max(start[0], end[0]) + margin
        y2 = max(start[1], end[1]) + margin
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(summary["width_mm"], x2)
        y2 = min(summary["height_mm"], y2)

        obstacles = perception.get_obstacles_in_region(x1, y1, x2, y2)
        for obs in obstacles:
            if obs["type"] == "component":
                router.add_obstacle(
                    Obstacle(obs["x_mm"], obs["y_mm"], obs["width_mm"], obs["height_mm"]),
                    clearance_mm=args.clearance,
                )
            elif obs["type"] == "trace":
                router.grid.add_trace_obstacle(
                    obs["start"][0], obs["start"][1],
                    obs["end"][0], obs["end"][1],
                    obs["width_mm"], args.clearance,
                )
            elif obs["type"] == "via":
                router.add_obstacle(
                    Obstacle(obs["x_mm"], obs["y_mm"], 0.6, 0.6),
                    clearance_mm=args.clearance,
                )

        path = router.find_path(start, end, args.width, args.clearance)
        if path:
            output_json({
                "status": "ok",
                "path": [[round(x, 3), round(y, 3)] for x, y in path],
                "waypoint_count": len(path),
                "length_mm": round(sum(
                    ((path[i+1][0]-path[i][0])**2 + (path[i+1][1]-path[i][1])**2)**0.5
                    for i in range(len(path)-1)
                ), 2),
            })
        else:
            output_json({"status": "no_path", "message": "No valid path found"})
        return 0

    # ── Routing actions ──
    elif args.action == "route":
        if not args.net or not args.waypoints:
            output_json({"status": "error", "message": "--net and --waypoints required"})
            return 1
        waypoints = [
            tuple(float(x) for x in pt.split(","))
            for pt in args.waypoints.split(";")
        ]
        result = actions.add_trace(args.net, waypoints, args.width, args.layer)
        if result["status"] == "ok":
            actions.save_board()
        output_json(result)
        return 0 if result["status"] == "ok" else 1

    elif args.action == "via":
        if not args.net or not args.pos:
            output_json({"status": "error", "message": "--net and --pos required"})
            return 1
        pos = [float(x) for x in args.pos.split(",")]
        result = actions.add_via(args.net, pos[0], pos[1], args.drill, args.pad)
        if result["status"] == "ok":
            actions.save_board()
        output_json(result)
        return 0

    elif args.action == "undo":
        result = actions.undo_last()
        if result["status"] == "ok":
            actions.save_board()
        output_json(result)
        return 0

    elif args.action == "rip_up":
        if not args.net:
            output_json({"status": "error", "message": "--net required"})
            return 1
        result = actions.remove_net_traces(args.net)
        if result["status"] == "ok":
            actions.save_board()
        output_json(result)
        return 0

    elif args.action == "zone":
        if not args.net:
            output_json({"status": "error", "message": "--net required"})
            return 1
        result = actions.add_zone(args.net, args.layer, args.priority)
        if result["status"] == "ok":
            actions.save_board()
        output_json(result)
        return 0

    elif args.action == "fill_zones":
        result = actions.fill_zones()
        actions.save_board()
        output_json(result)
        return 0

    elif args.action == "drc":
        result = actions.run_drc()
        output_json(result)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
