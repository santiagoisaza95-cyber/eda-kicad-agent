"""Tests for routing CLI — basic argument parsing and help."""
import subprocess
import sys
import pytest
from pathlib import Path


PYTHON = r"C:\Program Files\KiCad\9.0\bin\python.exe"
CLI_PATH = str(Path(__file__).resolve().parent.parent / "scripts" / "routing_cli.py")


class TestRoutingCLI:
    def test_help_flag(self):
        """CLI should show help without errors."""
        result = subprocess.run(
            [PYTHON, CLI_PATH, "--help"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "routing_cli" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_unknown_action_errors(self):
        """Unknown action should return error JSON."""
        result = subprocess.run(
            [PYTHON, CLI_PATH, "--board", "nonexistent.kicad_pcb", "--action", "bogus"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode != 0 or "error" in result.stdout.lower()

    def test_missing_board_errors(self):
        """Missing board file should return error JSON."""
        result = subprocess.run(
            [PYTHON, CLI_PATH, "--board", "nonexistent.kicad_pcb", "--action", "summary"],
            capture_output=True, text=True, timeout=15,
        )
        # Should error or print error JSON
        output = result.stdout + result.stderr
        assert "error" in output.lower() or "not found" in output.lower()
