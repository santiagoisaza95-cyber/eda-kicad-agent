"""Shared pytest fixtures for eda-kicad-agent board tests.

These fixtures provide reusable helpers for loading boards, running DRC,
and asserting component/net properties against contract requirements.
"""

from __future__ import annotations

import json
import subprocess
import shutil
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_config() -> dict[str, Any]:
    """Load machine-specific config from config.json."""
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        pytest.skip("config.json not found — run Phase 1 toolchain setup first")
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def project_config() -> dict[str, Any]:
    """Machine-specific configuration (interpreter, footprint path, etc.)."""
    return _load_config()


@pytest.fixture
def tmp_board_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary directory for board file operations."""
    board_dir = tmp_path / "board"
    board_dir.mkdir()
    return board_dir


@pytest.fixture(scope="session")
def pcbnew_module(project_config: dict[str, Any]):
    """Import and return the pcbnew module using the configured interpreter.

    Skips the entire test session if pcbnew is not available.
    """
    try:
        import pcbnew
        return pcbnew
    except ImportError:
        pytest.skip(
            "pcbnew not importable from this Python. "
            f"Use interpreter: {project_config.get('python_interpreter', 'kipython')}"
        )


@pytest.fixture
def load_board(pcbnew_module):
    """Return a callable that loads a .kicad_pcb file into a BOARD object."""

    def _load(board_path: str | Path):
        path = Path(board_path)
        if not path.exists():
            pytest.fail(f"Board file not found: {path}")
        return pcbnew_module.LoadBoard(str(path))

    return _load


@pytest.fixture
def run_drc(project_config: dict[str, Any]):
    """Return a callable that runs DRC on a board file via kicad-cli.

    Returns a dict with 'returncode', 'violations' count, and 'report_path'.
    """

    def _run_drc(board_path: str | Path, output_dir: str | Path | None = None) -> dict[str, Any]:
        board_path = Path(board_path)
        if output_dir is None:
            output_dir = board_path.parent
        else:
            output_dir = Path(output_dir)

        report_path = output_dir / "drc_report.json"
        kicad_cli = project_config.get("kicad_cli_path", "kicad-cli")

        result = subprocess.run(
            [kicad_cli, "pcb", "drc", "--output", str(report_path), str(board_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        violations = 0
        if report_path.exists():
            with open(report_path) as f:
                report = json.load(f)
            violations = len(report.get("violations", []))

        return {
            "returncode": result.returncode,
            "violations": violations,
            "report_path": report_path,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    return _run_drc


@pytest.fixture
def assert_component_exists(pcbnew_module):
    """Return a callable that asserts a component reference exists on the board."""

    def _assert(board, reference: str) -> None:
        refs = [fp.GetReference() for fp in board.GetFootprints()]
        assert reference in refs, (
            f"Component '{reference}' not found on board. "
            f"Existing references: {sorted(refs)}"
        )

    return _assert


@pytest.fixture
def assert_net_connected(pcbnew_module):
    """Return a callable that asserts a net exists and has the expected pad count."""

    def _assert(board, net_name: str, expected_pad_count: int | None = None) -> None:
        netinfo = board.GetNetInfo()
        net = netinfo.GetNetItem(net_name)
        assert net is not None, (
            f"Net '{net_name}' not found. "
            f"Existing nets: {[n.GetNetname() for n in netinfo.NetsByName().values()]}"
        )

        if expected_pad_count is not None:
            pads = [
                pad for fp in board.GetFootprints()
                for pad in fp.Pads()
                if pad.GetNet().GetNetname() == net_name
            ]
            assert len(pads) == expected_pad_count, (
                f"Net '{net_name}' has {len(pads)} pads, expected {expected_pad_count}"
            )

    return _assert
