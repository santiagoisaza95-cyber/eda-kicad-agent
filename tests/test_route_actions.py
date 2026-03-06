"""Tests for route actions — angle validation (no pcbnew needed for some)."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from routing.actions import validate_trace_angles


class TestAngleValidation:
    def test_straight_horizontal(self):
        ok, msg = validate_trace_angles([(0, 0), (10, 0)])
        assert ok, msg

    def test_straight_vertical(self):
        ok, msg = validate_trace_angles([(0, 0), (0, 10)])
        assert ok, msg

    def test_45_degree_diagonal(self):
        ok, msg = validate_trace_angles([(0, 0), (5, 5)])
        assert ok, msg

    def test_valid_45_bend(self):
        """Horizontal then 45° diagonal — valid."""
        ok, msg = validate_trace_angles([(0, 0), (5, 0), (8, 3)])
        assert ok, msg

    def test_90_degree_bend_rejected(self):
        """Horizontal then vertical — 90° bend — rejected."""
        ok, msg = validate_trace_angles([(0, 0), (5, 0), (5, 5)])
        assert not ok
        assert "90" in msg

    def test_single_point_ok(self):
        ok, msg = validate_trace_angles([(0, 0)])
        assert ok

    def test_two_points_ok(self):
        ok, msg = validate_trace_angles([(0, 0), (3, 7)])
        assert ok  # Any single segment is valid (angle constraint is between segments)

    def test_135_degree_turn_valid(self):
        """Going right, then turning 135° left — valid (45° multiple)."""
        ok, msg = validate_trace_angles([(0, 0), (5, 0), (2, 3)])
        assert ok, msg
