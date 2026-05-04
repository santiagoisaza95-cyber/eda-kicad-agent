#!/usr/bin/env python3
"""Generate comprehensive PDF documentation for eda-kicad-agent.

Produces a detailed user guide covering architecture, toolchain, skills,
rules, subagents, slash commands, contracts, testing, and CI/CD.

Run: python scripts/generate_docs_pdf.py
Output: docs/EDA_KiCad_Agent_User_Guide.pdf
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from datetime import datetime

from fpdf import FPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "EDA_KiCad_Agent_User_Guide.pdf"


# ── Custom PDF class ────────────────────────────────────────────────────────

class AgentPDF(FPDF):
    """Custom PDF with headers, footers, and helper methods."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=25)
        self.add_font("DejaVu", "", "C:/Windows/Fonts/consola.ttf")
        self.add_font("DejaVu", "B", "C:/Windows/Fonts/consolab.ttf")
        self.add_font("DejaVu", "I", "C:/Windows/Fonts/consolai.ttf")
        self.add_font("DejaVu", "BI", "C:/Windows/Fonts/consolaz.ttf")
        self.chapter_num = 0
        self.section_num = 0

    def header(self):
        if self.page_no() > 1:
            self.set_font("DejaVu", "I", 7)
            self.set_text_color(120, 120, 120)
            self.cell(0, 6, "EDA KiCad Agent - Comprehensive User Guide", align="L")
            self.cell(0, 6, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(200, 200, 200)
            self.line(10, 12, 200, 12)
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | eda-kicad-agent Documentation", align="C")

    def chapter_title(self, title: str):
        self.chapter_num += 1
        self.section_num = 0
        self.add_page()
        self.set_font("DejaVu", "B", 18)
        self.set_text_color(0, 100, 180)
        self.cell(0, 12, f"Chapter {self.chapter_num}: {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 100, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)
        self.set_text_color(0, 0, 0)

    def section_title(self, title: str):
        self.section_num += 1
        self.ln(4)
        self.set_font("DejaVu", "B", 13)
        self.set_text_color(0, 70, 140)
        self.cell(0, 9, f"{self.chapter_num}.{self.section_num}  {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def subsection_title(self, title: str):
        self.ln(2)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str):
        self.set_font("DejaVu", "", 9)
        for line in text.strip().split("\n"):
            self.multi_cell(0, 5, line.strip(), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def bold_text(self, text: str):
        self.set_font("DejaVu", "B", 9)
        self.multi_cell(0, 5, text.strip(), new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 9)
        self.ln(1)

    def code_block(self, code: str, title: str = ""):
        if title:
            self.set_font("DejaVu", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
        self.set_fill_color(240, 240, 245)
        self.set_font("DejaVu", "", 7.5)
        x_start = self.get_x()
        y_start = self.get_y()
        lines = code.strip().split("\n")
        for line in lines:
            # Truncate very long lines
            if len(line) > 105:
                line = line[:102] + "..."
            self.cell(190, 4.5, f"  {line}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def tip_box(self, text: str):
        self.set_fill_color(230, 245, 255)
        self.set_draw_color(0, 120, 200)
        self.set_font("DejaVu", "B", 8)
        y = self.get_y()
        self.rect(10, y, 190, 4 + 5 * (1 + text.count("\n")), style="D")
        self.set_xy(12, y + 1)
        self.set_font("DejaVu", "", 8)
        self.multi_cell(186, 4.5, f"TIP: {text}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def warning_box(self, text: str):
        self.set_fill_color(255, 245, 230)
        self.set_draw_color(200, 120, 0)
        self.set_font("DejaVu", "B", 8)
        y = self.get_y()
        self.rect(10, y, 190, 4 + 5 * (1 + text.count("\n")), style="D")
        self.set_xy(12, y + 1)
        self.set_font("DejaVu", "", 8)
        self.multi_cell(186, 4.5, f"WARNING: {text}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def simple_table(self, headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None):
        if col_widths is None:
            w = 190 // len(headers)
            col_widths = [w] * len(headers)
            col_widths[-1] = 190 - w * (len(headers) - 1)

        # Header
        self.set_font("DejaVu", "B", 8)
        self.set_fill_color(0, 100, 180)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, f" {h}", border=1, fill=True)
        self.ln()

        # Rows
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(0, 0, 0)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(245, 245, 250)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 6
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, f" {cell[:col_widths[i]//2]}", border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(2)


# ── Content generation ──────────────────────────────────────────────────────

def load_file(rel_path: str) -> str:
    p = PROJECT_ROOT / rel_path
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    return f"[File not found: {rel_path}]"


def build_pdf() -> None:
    pdf = AgentPDF()

    # ═══════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(35)
    pdf.set_font("DejaVu", "B", 28)
    pdf.set_text_color(0, 80, 160)
    pdf.cell(0, 15, "EDA KiCad Agent", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Comprehensive User Guide", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 7, "Automated KiCad 9.x PCB Design", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "with Claude Code, Python & pcbnew SWIG API", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    # Architecture diagram on cover
    pdf.set_font("DejaVu", "", 8)
    pdf.set_fill_color(240, 240, 245)
    arch = [
        "+------------------------------------------------------------------+",
        "|                    SYSTEM ARCHITECTURE                           |",
        "+------------------------------------------------------------------+",
        "|                                                                  |",
        "|  Engineer  --->  Claude Code  --->  Python  --->  KiCad 9.x     |",
        "|  (You)          (Opus 4.6)         (pcbnew)      (.kicad_pcb)   |",
        "|                                                                  |",
        "|  [Natural     [AI Agent with    [SWIG API     [Professional     |",
        "|   Language]    Skills/Rules]     Bindings]      PCB Design]      |",
        "|                                                                  |",
        "+------------------------------------------------------------------+",
    ]
    for line in arch:
        pdf.cell(190, 4.5, f"  {line}", fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Version 1.0  |  Generated {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "KiCad 9.0.7  |  Python 3.11  |  Windows", align="C", new_x="LMARGIN", new_y="NEXT")

    # ═══════════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ═══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(0, 100, 180)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(0, 100, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("DejaVu", "", 10)

    toc = [
        "Chapter 1:  Introduction & Overview",
        "Chapter 2:  Installation & Toolchain Setup",
        "Chapter 3:  Project Architecture & File Map",
        "Chapter 4:  The CLAUDE.md Router (How the Agent Thinks)",
        "Chapter 5:  Rules - Coding Standards & Quality Gates",
        "Chapter 6:  Skills - PCB Design Recipes",
        "Chapter 7:  The Contract System (Task Completion)",
        "Chapter 8:  Subagents - Adversarial Review Pipeline",
        "Chapter 9:  Slash Commands - User Interface",
        "Chapter 10: Testing Infrastructure",
        "Chapter 11: API Discovery & Manifest",
        "Chapter 12: CI/CD & Automation",
        "Chapter 13: Workflows & Tutorials",
        "Chapter 14: Troubleshooting & FAQ",
        "Chapter 15: Windows Toolchain Deep Dive",
        "Chapter 16: Configuration Reference",
        "Chapter 17: Regenerating This Document",
    ]
    for item in toc:
        pdf.cell(0, 7, f"   {item}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 1: INTRODUCTION
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Introduction & Overview")

    pdf.section_title("What is EDA KiCad Agent?")
    pdf.body_text(
        "EDA KiCad Agent is an AI-powered PCB (Printed Circuit Board) design automation system "
        "that connects a human engineer to KiCad 9.x through Claude Code (Anthropic's Opus 4.6 model). "
        "Instead of manually placing components and routing traces in the KiCad GUI, you describe your "
        "board requirements in natural language, and the agent generates the complete PCB design "
        "programmatically using Python and KiCad's pcbnew SWIG API.\n\n"
        "The system is NOT a simple script generator. It is a complete engineering environment with:\n"
        "  - Contract-driven development (your board spec becomes a binding contract)\n"
        "  - Automated testing (pytest validates every aspect of the design)\n"
        "  - Adversarial review (3 AI agents critique and verify each other's work)\n"
        "  - API safety (every KiCad function is verified before use)\n"
        "  - Zero-tolerance quality gates (DRC must pass with 0 errors)"
    )

    pdf.section_title("Who Is This For?")
    pdf.body_text(
        "This tool is designed for:\n"
        "  - Electronics engineers who want to automate repetitive PCB layouts\n"
        "  - Students learning PCB design who want AI-guided assistance\n"
        "  - Prototyping teams who need rapid board iterations\n"
        "  - Anyone comfortable with the command line who wants to describe\n"
        "    a PCB in plain English and get a KiCad-compatible output"
    )

    pdf.section_title("Key Capabilities")
    pdf.body_text(
        "1. NATURAL LANGUAGE TO PCB: Describe your board, get a .kicad_pcb file\n"
        "2. CONTRACT SYSTEM: Define exact specs; agent cannot finish until all are met\n"
        "3. AUTOMATED TESTING: Every board gets pytest tests for dimensions, components, nets, DRC\n"
        "4. ADVERSARIAL REVIEW: Reviewer finds bugs, Defender tries to disprove them, Referee decides\n"
        "5. API SAFETY: All KiCad API functions verified against actual installation before use\n"
        "6. SLASH COMMANDS: /new-board, /review-board, /research-api for streamlined workflows\n"
        "7. CI/CD READY: GitHub Actions workflow for continuous verification"
    )

    pdf.section_title("The Pipeline at a Glance")
    pdf.code_block(
        "Engineer (you)\n"
        "    |\n"
        "    v\n"
        "[/new-board command]  -->  Contract + Test Stubs generated\n"
        "    |\n"
        "    v\n"
        "[Claude Code / Opus 4.6]  reads contract, skills, rules\n"
        "    |\n"
        "    v\n"
        "[Python pcbnew scripts]  creates board programmatically\n"
        "    |\n"
        "    v\n"
        "[DRC Check]  kicad-cli pcb drc  -->  must be 0 errors\n"
        "    |\n"
        "    v\n"
        "[pytest]  validates all contract items  -->  must all pass\n"
        "    |\n"
        "    v\n"
        "[/review-board]  Reviewer -> Defender -> Referee pipeline\n"
        "    |\n"
        "    v\n"
        "[Final .kicad_pcb]  ready to open in KiCad GUI",
        "System Pipeline"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 2: INSTALLATION
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Installation & Toolchain Setup")

    pdf.section_title("Prerequisites")
    pdf.body_text(
        "Before starting, you need:\n"
        "  1. Windows 10/11 (Linux and macOS also supported with path changes)\n"
        "  2. Python 3.11 or higher\n"
        "  3. Git (for version control)\n"
        "  4. Claude Code CLI (from Anthropic)\n"
        "  5. Internet connection (for initial setup)"
    )

    pdf.section_title("Step 1: Install KiCad 9.x")
    pdf.body_text(
        "Download KiCad 9 stable from: https://www.kicad.org/download/windows/\n\n"
        "Run the installer with default settings. This installs:\n"
        "  - KiCad GUI (for viewing/editing boards manually)\n"
        "  - kicad-cli (command-line tool for DRC, export, etc.)\n"
        "  - Bundled Python 3.11 with pcbnew module\n"
        "  - 155 footprint libraries (SMD, THT, connectors, etc.)\n"
        "  - Symbol and 3D model libraries"
    )

    pdf.body_text(
        "After installation, verify from a terminal:"
    )
    pdf.code_block(
        '# Check kicad-cli is accessible\n'
        '"C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe" version\n'
        '# Expected output: 9.0.7 (or similar)',
        "Verification Command"
    )

    pdf.section_title("Step 2: Clone the Repository")
    pdf.code_block(
        "git clone <your-repo-url> eda-kicad-agent\n"
        "cd eda-kicad-agent",
        "Clone"
    )

    pdf.section_title("Step 3: Set Up Python Environment")
    pdf.body_text(
        "The project uses a Python virtual environment for dependencies, "
        "BUT pcbnew scripts must run with KiCad's bundled Python. This is a "
        "key distinction on Windows."
    )
    pdf.code_block(
        "# Create venv for pytest and dev tools\n"
        "python -m venv .venv\n"
        ".venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "\n"
        "# Install pytest into KiCad's bundled Python too\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pip install pytest',
        "Environment Setup"
    )

    pdf.warning_box(
        "On Windows, pcbnew can ONLY be imported from KiCad's bundled Python "
        "(C:\\Program Files\\KiCad\\9.0\\bin\\python.exe), NOT from your system Python. "
        "All pcbnew scripts must be run with KiCad's Python interpreter."
    )

    pdf.section_title("Step 4: Run API Discovery")
    pdf.body_text(
        "This is a critical step. The discover_api.py script probes the actual "
        "pcbnew module on YOUR machine and records which classes, functions, and "
        "constants exist. This prevents the agent from using API calls that don't "
        "exist in your KiCad version."
    )
    pdf.code_block(
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" scripts/discover_api.py',
        "Run API Discovery"
    )

    # Include actual output
    pdf.subsection_title("Expected Output (from actual run on this machine):")
    pdf.code_block(
        "=== KiCad pcbnew API Discovery ===\n"
        "\n"
        "KiCad version: 9.0.7\n"
        "Import method: direct\n"
        "Python: C:\\Program Files\\KiCad\\9.0\\bin\\python.exe\n"
        "\n"
        "--- Classes ---\n"
        "  [  OK   ] BOARD\n"
        "  [  OK   ] FOOTPRINT\n"
        "  [  OK   ] PAD\n"
        "  [  OK   ] PCB_IO_KICAD_SEXPR\n"
        "  [  OK   ] NETINFO_ITEM\n"
        "  [  OK   ] NETINFO_LIST\n"
        "  [  OK   ] PCB_TRACK\n"
        "  [  OK   ] PCB_VIA\n"
        "  [  OK   ] PCB_SHAPE\n"
        "  [  OK   ] PCB_TEXT\n"
        "  [  OK   ] ZONE\n"
        "  [  OK   ] PCB_GROUP\n"
        "  [  OK   ] BOARD_DESIGN_SETTINGS\n"
        "  [  OK   ] BOARD_ITEM\n"
        "\n"
        "--- Functions ---\n"
        "  [  OK   ] FromMM      [  OK   ] ToMM\n"
        "  [  OK   ] FromMils    [  OK   ] ToMils\n"
        "  [  OK   ] SaveBoard   [  OK   ] LoadBoard\n"
        "  [  OK   ] GetBoard    [  OK   ] VECTOR2I\n"
        "  [  OK   ] EDA_ANGLE   [  OK   ] LSET\n"
        "\n"
        "--- Layer Constants ---\n"
        "  [  OK   ] F_Cu = 0        B_Cu = 2\n"
        "  [  OK   ] F_SilkS = 5     B_SilkS = 7\n"
        "  [  OK   ] Edge_Cuts = 25\n"
        "\n"
        "=== Summary: 39/39 verified (100.0%) ===",
        "discover_api.py Output"
    )

    pdf.section_title("Step 5: Run Toolchain Verification")
    pdf.code_block(
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" scripts/verify_toolchain.py',
        "Run Verification"
    )
    pdf.subsection_title("Expected Output:")
    pdf.code_block(
        "=== eda-kicad-agent Toolchain Verification ===\n"
        "\n"
        "  [PASS] Python version -- 3.11.5\n"
        "  [PASS] kicad-cli -- 9.0.7\n"
        "  [PASS] pcbnew import -- direct import, version 9.0.7\n"
        "  [PASS] pytest -- version 9.0.2\n"
        "  [PASS] Footprint library -- 155 .pretty dirs\n"
        "  [PASS] API manifest -- 39/39 verified (100.0%)\n"
        "\n"
        "=== Results: 6/6 passed ===\n"
        "\n"
        "GATE 1 PASSED -- all checks green.\n"
        "Phase 2 (Agent Architecture) can proceed.",
        "verify_toolchain.py Output"
    )
    pdf.tip_box("If any check fails, the output tells you exactly what to fix. The most common issue is KiCad not being installed or kicad-cli not being on PATH.")

    pdf.section_title("Step 6: Verify Tests Collect")
    pdf.code_block(
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/ --collect-only',
        "Test Collection"
    )
    pdf.subsection_title("Expected Output:")
    pdf.code_block(
        "collected 17 items\n"
        "\n"
        "<Module test_example_board.py>\n"
        "  <Class TestBoardDimensions>\n"
        "    <Function test_board_dimensions>\n"
        "    <Function test_layer_count>\n"
        "  <Class TestComponents>\n"
        "    <Function test_component_count>\n"
        "    <Function test_component_exists[U1]>\n"
        "    <Function test_component_exists[C1]>\n"
        "    <Function test_component_exists[C2]>\n"
        "    <Function test_component_exists[R1]>\n"
        "    <Function test_component_exists[J1]>\n"
        "    <Function test_component_exists[Y1]>\n"
        "  <Class TestNetConnectivity>\n"
        "    <Function test_net_connectivity[VCC]>\n"
        "    <Function test_net_connectivity[GND]>\n"
        "    ...(7 net tests total)\n"
        "  <Class TestDRC>\n"
        "    <Function test_drc_passes>",
        "17 Tests Collected"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 3: PROJECT ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Project Architecture & File Map")

    pdf.section_title("Directory Structure")
    pdf.code_block(
        "eda-kicad-agent/\n"
        "|\n"
        "|-- CLAUDE.md                  # Agent brain: thin routing table\n"
        "|-- README.md                  # Project overview & quick start\n"
        "|-- TOOLCHAIN_NOTES.md         # Windows-specific setup notes\n"
        "|-- config.json                # Machine-specific paths\n"
        "|-- api_manifest.json          # Verified KiCad API surface\n"
        "|-- requirements.txt           # Python dependencies\n"
        "|-- .gitignore                 # VCS exclusions\n"
        "|\n"
        "|-- .claude/\n"
        "|   |-- settings.json          # Subagent tool restrictions\n"
        "|   |-- agents/\n"
        "|   |   |-- api-researcher.md  # Research-only agent\n"
        "|   |   |-- design-reviewer.md # Bug finder\n"
        "|   |   |-- design-defender.md # Bug disprover\n"
        "|   |   |-- design-referee.md  # Final judge\n"
        "|   |-- commands/\n"
        "|       |-- new-board.md       # /new-board command\n"
        "|       |-- review-board.md    # /review-board command\n"
        "|       |-- research-api.md    # /research-api command\n"
        "|\n"
        "|-- agent_docs/\n"
        "|   |-- rules/                 # Behavioral constraints\n"
        "|   |   |-- coding-rules.md    # Python standards\n"
        "|   |   |-- drc-rules.md       # DRC zero-tolerance\n"
        "|   |   |-- testing-rules.md   # Test infrastructure\n"
        "|   |   |-- test-failing-rules.md  # Failure diagnostics\n"
        "|   |-- skills/                # Domain knowledge\n"
        "|       |-- kicad-api-skill.md     # pcbnew API reference\n"
        "|       |-- pcb-design-skill.md    # 12-step workflow\n"
        "|       |-- placement-skill.md     # Component placement\n"
        "|       |-- routing-skill.md       # Trace routing\n"
        "|\n"
        "|-- contracts/\n"
        "|   |-- EXAMPLE_CONTRACT.md    # Template: Simple MCU Board\n"
        "|\n"
        "|-- scripts/\n"
        "|   |-- scaffold.py            # Create directory tree\n"
        "|   |-- discover_api.py        # Probe pcbnew API\n"
        "|   |-- verify_toolchain.py    # Verify environment\n"
        "|\n"
        "|-- tests/\n"
        "|   |-- conftest.py            # Shared pytest fixtures\n"
        "|   |-- test_example_board.py  # Template test file\n"
        "|\n"
        "|-- output/                    # Generated .kicad_pcb files\n"
        "|-- research/                  # API research results\n"
        "|-- review/                    # Review pipeline output\n"
        "|-- .github/workflows/\n"
        "    |-- verify.yml             # CI/CD pipeline",
        "Complete File Tree"
    )

    pdf.section_title("File Categories Explained")
    pdf.body_text(
        "The project files are organized into distinct categories, each serving "
        "a specific role in the agent's decision-making process:"
    )

    pdf.subsection_title("Configuration Layer (Machine-Specific)")
    pdf.body_text(
        "config.json - Stores YOUR machine's paths: where KiCad is installed, which Python "
        "interpreter to use, where footprint libraries live. This file is the single source "
        "of truth for all machine-specific information. Skills and rules reference it instead "
        "of hardcoding paths.\n\n"
        "api_manifest.json - Auto-generated by discover_api.py. Contains a complete map of "
        "which KiCad pcbnew classes, functions, and constants exist on YOUR installation. "
        "The agent checks this before using any API function."
    )

    pdf.subsection_title("Intelligence Layer (Agent Brain)")
    pdf.body_text(
        "CLAUDE.md - The routing table. When Claude Code reads this file, it learns WHERE to "
        "find information, not the information itself. This keeps the file tiny (29 lines) so "
        "it never gets truncated during context compression.\n\n"
        "agent_docs/rules/ - Behavioral constraints. These tell the agent WHAT NOT TO DO "
        "(don't edit tests, don't skip DRC, don't guess API names).\n\n"
        "agent_docs/skills/ - Domain knowledge. These tell the agent HOW TO DO things "
        "(how to create a board, how to place components, how to route traces)."
    )

    pdf.subsection_title("Quality Layer (Verification)")
    pdf.body_text(
        "contracts/ - Define the exact deliverables for each board. The agent cannot finish "
        "until every checkbox is checked.\n\n"
        "tests/ - pytest tests that programmatically verify contract requirements. These are "
        "immutable milestones - the agent must fix its code, never the tests.\n\n"
        ".claude/agents/ - The adversarial review pipeline. Three separate agents (Reviewer, "
        "Defender, Referee) critique each other to catch bugs the primary agent missed."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 4: CLAUDE.MD ROUTER
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("The CLAUDE.md Router (How the Agent Thinks)")

    pdf.section_title("Why a Thin Router?")
    pdf.body_text(
        "Claude Code reads CLAUDE.md at the start of every session and after every context "
        "compression event. If this file is large, critical information gets lost when the "
        "context window fills up. The solution: keep CLAUDE.md as a pure routing table "
        "(currently 30 lines, limit is 50) that points to detailed documents elsewhere.\n\n"
        "Think of it like a switchboard operator: it doesn't know how to design a PCB, "
        "but it knows exactly who to connect you to."
    )

    pdf.section_title("The Routing Table")
    pdf.code_block(load_file("CLAUDE.md"), "CLAUDE.md (complete)")

    pdf.section_title("How Routing Works in Practice")
    pdf.body_text(
        "When you ask the agent to design a PCB, this is what happens:\n\n"
        "1. Agent reads CLAUDE.md\n"
        "2. Sees 'Designing a PCB' -> reads pcb-design-skill.md\n"
        "3. pcb-design-skill.md says 'Place components' -> reads placement-skill.md\n"
        "4. placement-skill.md says 'Use FromMM()' -> checks api_manifest.json\n"
        "5. api_manifest.json confirms FromMM exists -> proceeds\n"
        "6. If unsure about an API call -> uses /research-api command\n\n"
        "This chain of references means the agent always has the right information "
        "for the right task, without carrying everything in memory at once."
    )

    pdf.section_title("The First Rule: Compaction Recovery")
    pdf.body_text(
        "The First Rule in CLAUDE.md says: 'After every compaction event, STOP. Re-read "
        "your current task plan and the relevant source files.'\n\n"
        "This is critical because Claude Code compresses older messages when the context "
        "window fills up. Without this rule, the agent might forget what it was doing "
        "mid-task. With it, the agent always recovers its full context by re-reading "
        "the relevant files."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 5: RULES
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Rules - Coding Standards & Quality Gates")

    pdf.section_title("Overview")
    pdf.body_text(
        "Rules are behavioral constraints that the agent must follow at all times. "
        "They define WHAT NOT TO DO and set quality gates that cannot be bypassed. "
        "There are 4 rules files, each targeting a specific concern."
    )

    pdf.section_title("Coding Rules (coding-rules.md)")
    pdf.body_text(
        "These enforce Python coding standards and KiCad API safety:"
    )
    pdf.code_block(load_file("agent_docs/rules/coding-rules.md"), "agent_docs/rules/coding-rules.md")
    pdf.body_text(
        "KEY TAKEAWAY: The completion checklist at the bottom ensures the agent self-checks "
        "before declaring a task done. The api_manifest.json check is especially important - "
        "it prevents the agent from using KiCad functions that don't exist in your version."
    )

    pdf.section_title("DRC Rules (drc-rules.md)")
    pdf.body_text(
        "DRC (Design Rule Check) is KiCad's built-in validation system. It checks for "
        "electrical and manufacturing errors like unconnected nets, clearance violations, "
        "and overlapping components."
    )
    pdf.code_block(load_file("agent_docs/rules/drc-rules.md"), "agent_docs/rules/drc-rules.md")
    pdf.body_text(
        "The zero-tolerance policy means EVERY design must pass DRC with 0 errors "
        "before it can be considered complete. The agent runs DRC via kicad-cli "
        "(command-line interface) so it can be automated without opening the GUI."
    )
    pdf.tip_box(
        "You can run DRC manually too:\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe" pcb drc '
        "--output report.json output/your_board.kicad_pcb"
    )

    pdf.section_title("Testing Rules (testing-rules.md)")
    pdf.code_block(load_file("agent_docs/rules/testing-rules.md"), "agent_docs/rules/testing-rules.md")
    pdf.body_text(
        "The critical concept: tests are MILESTONES, not afterthoughts. The agent's task "
        "is not complete until all tests pass. And the golden rule: NEVER edit tests to "
        "make them pass - fix the implementation instead.\n\n"
        "The shared fixtures in conftest.py provide reusable helpers so every test file "
        "doesn't have to reinvent board loading and DRC checking."
    )

    pdf.section_title("Test Failure Rules (test-failing-rules.md)")
    pdf.code_block(load_file("agent_docs/rules/test-failing-rules.md"), "agent_docs/rules/test-failing-rules.md")
    pdf.body_text(
        "This is a diagnostic flowchart. When tests fail, the agent follows these "
        "steps IN ORDER instead of randomly trying fixes. Step 3 (Check API Manifest) "
        "is unique to this project - it catches the common case where a KiCad API function "
        "was renamed between versions."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 6: SKILLS
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Skills - PCB Design Recipes")

    pdf.section_title("Overview")
    pdf.body_text(
        "Skills are domain knowledge documents that teach the agent HOW to perform "
        "specific PCB design tasks. Unlike rules (which constrain), skills enable. "
        "There are 4 skills covering the complete PCB design workflow."
    )

    pdf.section_title("KiCad API Skill (kicad-api-skill.md)")
    pdf.body_text(
        "This is the most important skill - it's a verified reference for the KiCad 9.x "
        "pcbnew SWIG API. Every code snippet has been cross-referenced against the "
        "api_manifest.json to ensure it works on this specific KiCad installation.\n\n"
        "Key sections:"
    )
    pdf.body_text(
        "CORE OBJECTS AND OPERATIONS:\n"
        "  - BOARD: The root object. Create with pcbnew.BOARD() or load with LoadBoard()\n"
        "  - FOOTPRINT: A component placed on the board (has pads, position, reference)\n"
        "  - PAD: Connection point on a footprint (belongs to a net)\n"
        "  - NETINFO_ITEM: Defines a named electrical net (VCC, GND, etc.)\n"
        "  - PCB_TRACK: A copper trace connecting two points\n"
        "  - PCB_VIA: A through-hole connecting layers\n"
        "  - PCB_SHAPE: Board outline, circles, arcs on any layer\n"
        "  - PCB_TEXT: Silkscreen text, fab notes\n"
        "  - ZONE: Copper pour (ground plane, power plane)"
    )
    pdf.code_block(
        "import pcbnew\n"
        "\n"
        "# Create a new board\n"
        "board = pcbnew.BOARD()\n"
        "board.SetCopperLayerCount(2)\n"
        "\n"
        "# Unit conversion (ALL measurements in nanometers internally)\n"
        "x = pcbnew.FromMM(25.0)   # 25mm -> nanometers\n"
        "y = pcbnew.ToMM(25000000) # nanometers -> 25mm\n"
        "\n"
        "# Load a footprint from the library\n"
        "io = pcbnew.PCB_IO_KICAD_SEXPR()\n"
        "fp_path = r'C:\\Program Files\\KiCad\\9.0\\share\\kicad\\footprints'\n"
        "lib = f'{fp_path}\\Package_QFP.pretty'\n"
        "fp = io.ImportFootprint(lib, 'TQFP-32_7x7mm_P0.8mm')\n"
        "\n"
        "# Position and add to board\n"
        "fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(25), pcbnew.FromMM(20)))\n"
        "fp.SetReference('U1')\n"
        "board.Add(fp)\n"
        "\n"
        "# Create a net\n"
        "net = pcbnew.NETINFO_ITEM(board, 'VCC')\n"
        "board.Add(net)\n"
        "\n"
        "# Assign net to pad\n"
        "for pad in fp.Pads():\n"
        "    if pad.GetName() == '1':  # Pin 1 = VCC\n"
        "        pad.SetNet(net)\n"
        "\n"
        "# Save\n"
        "pcbnew.SaveBoard('output/my_board.kicad_pcb', board)",
        "Core API Usage Example"
    )

    pdf.body_text(
        "KNOWN API GOTCHAS (from kicad-api-skill.md):\n"
        "  - Shape enums: Use SHAPE_T_RECT, not SHAPE_RECT (KiCad 9 naming)\n"
        "  - Footprint IO: PCB_IO_KICAD_SEXPR exists in KiCad 9, PLUGIN does not\n"
        "  - Positions: Use VECTOR2I(FromMM(x), FromMM(y)), not tuples\n"
        "  - Net assignment: Must call board.Add(net) before pad.SetNet(net)\n"
        "  - Layer names: F_SilkS (not F_Silkscreen) in KiCad 9.0.7\n"
        "  - Zone filling: Call filler.Fill(board) after creating zones"
    )
    pdf.warning_box("ALWAYS check api_manifest.json before using any pcbnew function. If unsure, use /research-api to investigate.")

    pdf.section_title("PCB Design Skill (pcb-design-skill.md)")
    pdf.body_text(
        "This skill defines the ordered 12-step workflow for creating a complete PCB. "
        "The agent follows these steps IN ORDER, never skipping ahead:"
    )
    pdf.code_block(
        "Step 1:  Read Contract        -- Understand the specs\n"
        "Step 2:  Create Board          -- pcbnew.BOARD(), set layer count\n"
        "Step 3:  Set Board Outline     -- PCB_SHAPE on Edge_Cuts layer\n"
        "Step 4:  Place Components      -- Follow placement-skill.md order\n"
        "Step 5:  Define Nets           -- NETINFO_ITEM for each named net\n"
        "Step 6:  Assign Pads to Nets   -- pad.SetNet(net) for every connection\n"
        "Step 7:  Route Traces          -- PCB_TRACK following routing-skill.md\n"
        "Step 8:  Add Ground Plane      -- ZONE copper pour on B.Cu\n"
        "Step 9:  Add Silkscreen        -- PCB_TEXT for reference designators\n"
        "Step 10: Run DRC               -- kicad-cli, must be 0 errors\n"
        "Step 11: Run Tests             -- pytest, all must pass\n"
        "Step 12: Save Final Board      -- SaveBoard to output/",
        "12-Step PCB Design Workflow"
    )
    pdf.body_text(
        "ABORT CONDITIONS (design stops immediately if):\n"
        "  - A footprint is not found in the library\n"
        "  - An API function is missing from api_manifest.json\n"
        "  - DRC returns errors that cannot be fixed programmatically"
    )

    pdf.section_title("Placement Skill (placement-skill.md)")
    pdf.body_text(
        "Component placement is one of the most critical steps in PCB design. "
        "This skill defines strict priority ordering and spacing rules:"
    )
    pdf.code_block(
        "PLACEMENT PRIORITY ORDER:\n"
        "  1. MCU/Main IC       -- Center of board, Pin 1 at top-left\n"
        "  2. Decoupling Caps   -- Within 2mm of IC power pins\n"
        "  3. Crystal/Oscillator -- Within 5mm of clock pins\n"
        "  4. Connectors        -- At board edges\n"
        "  5. Pull-up Resistors -- Near the pin they service\n"
        "  6. Other Passives    -- Grouped by function\n"
        "\n"
        "COORDINATE SYSTEM:\n"
        "  Origin: Top-left corner\n"
        "  X-axis: Positive rightward\n"
        "  Y-axis: Positive downward (important!)\n"
        "  Units:  All in mm, use FromMM()\n"
        "  Grid:   0.5mm snap grid\n"
        "\n"
        "SPACING RULES:\n"
        "  IC pads to nearby component:  >= 1.0mm\n"
        "  SMD components (same group):  >= 0.5mm\n"
        "  Component to board edge:      >= 0.5mm\n"
        "  Connector to board edge:       0mm (flush)\n"
        "  Decoupling cap to IC power pin: <= 2.0mm\n"
        "  Crystal to clock pin:           <= 5.0mm",
        "Placement Rules Summary"
    )

    pdf.section_title("Routing Skill (routing-skill.md)")
    pdf.body_text(
        "Trace routing connects component pads with copper traces. The routing "
        "skill defines priorities, widths, and best practices:"
    )
    pdf.code_block(
        "ROUTING PRIORITY:\n"
        "  1. Power traces  (VCC, GND) -- route first, widest\n"
        "  2. Clock signals             -- short, direct\n"
        "  3. High-speed signals        -- controlled impedance\n"
        "  4. General signals           -- everything else\n"
        "\n"
        "TRACE WIDTH TABLE:\n"
        "  Signal traces:    0.25mm\n"
        "  Power traces:     0.50mm\n"
        "  High current:     1.00mm\n"
        "  USB data pairs:   0.25mm (matched length)\n"
        "  Clock signals:    0.25mm (short as possible)\n"
        "\n"
        "VIA RULES:\n"
        "  Drill diameter:   0.3mm\n"
        "  Pad diameter:     0.6mm\n"
        "  Min annular ring: 0.15mm\n"
        "\n"
        "GROUND PLANE STRATEGY (2-layer boards):\n"
        "  - B.Cu (bottom copper) = GND copper pour\n"
        "  - F.Cu (top copper) = signal and power traces\n"
        "  - Place GND vias near IC ground pins\n"
        "  - Via stitching along board edges",
        "Routing Rules Summary"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 7: CONTRACT SYSTEM
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("The Contract System (Task Completion)")

    pdf.section_title("What is a Contract?")
    pdf.body_text(
        "A contract is a binding specification document that defines EXACTLY what a board "
        "design must contain. The agent cannot terminate its session until every item in "
        "the contract's completion checklist is fulfilled.\n\n"
        "This prevents the common AI failure mode of 'good enough' - where the agent "
        "produces something that looks correct but is missing components, has unrouted "
        "nets, or fails DRC."
    )

    pdf.section_title("Contract Structure")
    pdf.body_text(
        "Every contract contains:\n"
        "  1. SPECIFICATIONS: Board dimensions, layer count\n"
        "  2. COMPONENTS TABLE: Reference, component, footprint, position\n"
        "  3. NETLIST TABLE: Net name, which pins connect\n"
        "  4. DESIGN RULES: Trace widths, clearances\n"
        "  5. VERIFICATION COMMANDS: Exact commands to validate\n"
        "  6. COMPLETION CHECKLIST: Checkboxes that must ALL be checked"
    )

    pdf.section_title("Example Contract: Simple MCU Board")
    pdf.code_block(load_file("contracts/EXAMPLE_CONTRACT.md"), "contracts/EXAMPLE_CONTRACT.md")

    pdf.section_title("How Contracts Drive Development")
    pdf.body_text(
        "The workflow is:\n"
        "1. You run /new-board and describe your board\n"
        "2. The command generates a contract AND a pytest test file\n"
        "3. The contract and tests share the same component/net lists\n"
        "4. The agent designs the board to satisfy the contract\n"
        "5. Tests validate every contract item programmatically\n"
        "6. The agent cannot stop until all tests pass\n\n"
        "This creates a tight feedback loop: contract defines success, "
        "tests verify success, agent iterates until verified."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 8: SUBAGENTS
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Subagents - Adversarial Review Pipeline")

    pdf.section_title("The Adversarial Review Concept")
    pdf.body_text(
        "After the primary agent designs a board, how do you know it's correct? "
        "Self-review is unreliable because the same 'brain' that made the mistake "
        "is unlikely to find it. The solution: THREE separate agents with competing "
        "incentives review the design.\n\n"
        "This is inspired by adversarial systems in law (prosecutor vs defense) "
        "and science (peer review). The key insight: agents perform better when "
        "their work is scored and they compete against each other."
    )

    pdf.section_title("The 3-Agent Pipeline")
    pdf.code_block(
        "STEP 1: DESIGN REVIEWER (finds bugs)\n"
        "  |\n"
        "  | Writes: review/{board}_review.md\n"
        "  | Scoring: +1 cosmetic, +5 design, +10 critical\n"
        "  |\n"
        "  v\n"
        "STEP 2: DESIGN DEFENDER (disproves bugs)\n"
        "  |\n"
        "  | Reads: review/{board}_review.md\n"
        "  | Writes: review/{board}_defense.md\n"
        "  | Scoring: Earns bug score for valid disproves\n"
        "  |          Loses 2x score for wrong disproves\n"
        "  |\n"
        "  v\n"
        "STEP 3: DESIGN REFEREE (final judgment)\n"
        "  |\n"
        "  | Reads: both review + defense\n"
        "  | Writes: review/{board}_verdict.md\n"
        "  | Scoring: +1 correct judgment, -1 incorrect\n"
        "  |\n"
        "  v\n"
        "FINAL: Action items presented to user",
        "Adversarial Review Pipeline"
    )

    pdf.section_title("Agent 1: API Researcher")
    pdf.code_block(load_file(".claude/agents/api-researcher.md"), ".claude/agents/api-researcher.md")
    pdf.body_text(
        "This agent is RESEARCH ONLY - it cannot write implementation code. It is "
        "restricted to Read, Grep, Glob, Bash, WebFetch, and WebSearch tools via "
        ".claude/settings.json. Its job: verify that KiCad API functions actually "
        "exist before anyone uses them."
    )

    pdf.section_title("Agent 2: Design Reviewer")
    pdf.code_block(load_file(".claude/agents/design-reviewer.md"), ".claude/agents/design-reviewer.md")
    pdf.body_text(
        "The Reviewer's incentive is to find as many real bugs as possible. "
        "Higher-severity bugs (critical = +10) are worth more points. This pushes "
        "the reviewer to focus on genuinely dangerous issues, not just cosmetic ones."
    )

    pdf.section_title("Agent 3: Design Defender")
    pdf.code_block(load_file(".claude/agents/design-defender.md"), ".claude/agents/design-defender.md")
    pdf.body_text(
        "The Defender's asymmetric scoring is key: successfully disproving a bug "
        "earns the bug's score, but wrongly disproving a real bug costs 2x. "
        "This means the Defender only challenges bugs it's confident about, "
        "which filters out false positives while preserving real issues."
    )

    pdf.section_title("Agent 4: Design Referee")
    pdf.code_block(load_file(".claude/agents/design-referee.md"), ".claude/agents/design-referee.md")
    pdf.body_text(
        "The Referee has 'ground truth' access and is scored on judgment accuracy. "
        "Its output is the final word: a verdict with concrete action items that "
        "must be fixed before the board is approved."
    )

    pdf.section_title("Tool Restrictions (settings.json)")
    pdf.body_text(
        "The .claude/settings.json file ENFORCES tool restrictions at the Claude Code "
        "level. The api-researcher agent literally cannot access the Write tool - "
        "this isn't just a polite request in markdown, it's a technical restriction."
    )
    pdf.code_block(load_file(".claude/settings.json"), ".claude/settings.json")

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 9: SLASH COMMANDS
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Slash Commands - User Interface")

    pdf.section_title("Overview")
    pdf.body_text(
        "Slash commands are the primary way users interact with the agent. They are "
        "shortcuts that trigger complex multi-step workflows. There are 3 commands:"
    )

    pdf.section_title("/new-board - Create a New Board Design")
    pdf.code_block(load_file(".claude/commands/new-board.md"), ".claude/commands/new-board.md")
    pdf.body_text(
        "HOW TO USE:\n"
        "  1. Type /new-board in the Claude Code CLI\n"
        "  2. The agent asks: board name, dimensions, layers, components, nets\n"
        "  3. It generates TWO files simultaneously:\n"
        "     - contracts/{board_name}_contract.md (the specification)\n"
        "     - tests/test_{board_name}.py (the verification tests)\n"
        "  4. Both files share the exact same component and net lists\n"
        "  5. The agent then begins designing the board to satisfy the contract\n\n"
        "EXAMPLE INTERACTION:\n"
        "  You: /new-board\n"
        "  Agent: What's the board name?\n"
        "  You: temperature_sensor\n"
        "  Agent: Dimensions?\n"
        "  You: 30x25mm, 2 layers\n"
        "  Agent: Components?\n"
        "  You: LM35 temp sensor, ATtiny85, 2 bypass caps, header connector\n"
        "  Agent: [generates contract and tests, begins design]"
    )

    pdf.section_title("/review-board - Adversarial Review Pipeline")
    pdf.code_block(load_file(".claude/commands/review-board.md"), ".claude/commands/review-board.md")
    pdf.body_text(
        "HOW TO USE:\n"
        "  1. Complete a board design first\n"
        "  2. Type /review-board my_board_name\n"
        "  3. The pipeline runs automatically:\n"
        "     - Reviewer examines the board, writes findings\n"
        "     - Defender challenges the findings\n"
        "     - Referee makes final judgment\n"
        "  4. You receive a list of action items to fix\n\n"
        "OUTPUT FILES:\n"
        "  review/my_board_review.md   -- Reviewer's findings\n"
        "  review/my_board_defense.md  -- Defender's arguments\n"
        "  review/my_board_verdict.md  -- Referee's final verdict"
    )

    pdf.section_title("/research-api - Investigate KiCad API")
    pdf.code_block(load_file(".claude/commands/research-api.md"), ".claude/commands/research-api.md")
    pdf.body_text(
        "HOW TO USE:\n"
        "  1. When unsure about a KiCad API function\n"
        "  2. Type /research-api zone filling\n"
        "  3. The api-researcher agent investigates:\n"
        "     - Checks api_manifest.json\n"
        "     - Runs discover_api.py if needed\n"
        "     - Searches web documentation\n"
        "  4. Results saved to research/ directory\n"
        "  5. Summary presented to you\n\n"
        "This is the SAFE way to verify API calls instead of guessing."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 10: TESTING
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Testing Infrastructure")

    pdf.section_title("The Testing Philosophy")
    pdf.body_text(
        "In this project, tests are NOT an afterthought. They are MILESTONES. "
        "The agent's task is literally defined as 'make all tests pass'. "
        "Tests are generated alongside contracts so they share the same "
        "component lists, net lists, and dimensional requirements.\n\n"
        "The golden rule: NEVER edit tests to make them pass. "
        "Always fix the implementation code instead."
    )

    pdf.section_title("Shared Fixtures (conftest.py)")
    pdf.body_text(
        "The conftest.py file provides 7 reusable fixtures that every test "
        "file can use. This prevents code duplication and ensures consistent "
        "board loading and validation across all test files."
    )
    pdf.code_block(load_file("tests/conftest.py"), "tests/conftest.py (complete)")

    pdf.subsection_title("Fixture Reference")
    pdf.body_text(
        "project_config -- Session-scoped. Loads config.json once.\n"
        "tmp_board_dir  -- Per-test. Clean temp directory for file I/O.\n"
        "pcbnew_module  -- Session-scoped. Imports pcbnew, skips if unavailable.\n"
        "load_board     -- Returns callable: load_board('path.kicad_pcb') -> BOARD\n"
        "run_drc        -- Returns callable: run_drc('path.kicad_pcb') -> dict\n"
        "                  with keys: returncode, violations, report_path, stdout, stderr\n"
        "assert_component_exists -- Callable: assert_component_exists(board, 'U1')\n"
        "assert_net_connected    -- Callable: assert_net_connected(board, 'VCC', pad_count=5)"
    )

    pdf.section_title("Template Test File (test_example_board.py)")
    pdf.code_block(load_file("tests/test_example_board.py"), "tests/test_example_board.py (complete)")

    pdf.body_text(
        "This template shows the 4 categories of tests that every board needs:\n\n"
        "1. TestBoardDimensions -- Validates physical size and layer count\n"
        "2. TestComponents -- Checks all required components exist on the board\n"
        "3. TestNetConnectivity -- Verifies all nets are present and connected\n"
        "4. TestDRC -- Runs Design Rule Check, requires 0 violations\n\n"
        "Each test class maps directly to a section in the contract's completion "
        "checklist. When /new-board generates a new test file, it follows this exact "
        "pattern with the specific components and nets from the contract."
    )

    pdf.section_title("Running Tests")
    pdf.code_block(
        "# Collect tests (verify they're found)\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/ --collect-only\n'
        "\n"
        "# Run all tests (verbose output)\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/ -v\n'
        "\n"
        "# Run a specific test file\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/test_example_board.py -v\n'
        "\n"
        "# Run a single test\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/test_example_board.py::TestDRC -v',
        "Test Commands"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 11: API DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("API Discovery & Manifest")

    pdf.section_title("Why API Discovery Matters")
    pdf.body_text(
        "KiCad's pcbnew SWIG API is NOT stable between versions. Class names, function "
        "signatures, and constants change. For example:\n"
        "  - KiCad 7: footprint loader was called 'PLUGIN'\n"
        "  - KiCad 8: renamed to 'PCB_IO_KICAD_SEXPR'\n"
        "  - KiCad 9: PCB_IO_KICAD_SEXPR still exists, but PLUGIN does not\n\n"
        "If the agent uses a function name from the wrong version, the script crashes. "
        "The solution: probe the ACTUAL installed module and record what exists."
    )

    pdf.section_title("The discover_api.py Script")
    pdf.body_text(
        "This script imports pcbnew and systematically checks for the existence of "
        "every class, function, and constant the agent might need. It outputs a "
        "JSON manifest that serves as the ground truth for skill documentation."
    )
    pdf.body_text(
        "What it checks:\n"
        "  - 14 classes (BOARD, FOOTPRINT, PAD, PCB_TRACK, etc.)\n"
        "  - 10 functions (FromMM, ToMM, SaveBoard, LoadBoard, etc.)\n"
        "  - 15 layer constants (F_Cu, B_Cu, Edge_Cuts, etc.)\n"
        "  - 5 footprint IO class name variants\n"
        "  - 7 pad shape constants\n"
        "  - 4 pad type constants\n\n"
        "Total: 55 items checked, 39 expected (rest are alternative names)"
    )

    pdf.section_title("The api_manifest.json File")
    pdf.body_text(
        "This auto-generated file is the single source of truth for API availability. "
        "Skills reference it, the coding rules require checking it, and the test-failing "
        "rules direct the agent to consult it when AttributeErrors occur.\n\n"
        "Current status on this machine:"
    )
    pdf.code_block(
        '{\n'
        '  "kicad_version": "9.0.7",\n'
        '  "pcbnew_import_method": "direct",\n'
        '  "summary": {\n'
        '    "total_checked": 39,\n'
        '    "verified": 39,\n'
        '    "missing": 0,\n'
        '    "coverage_pct": 100.0\n'
        '  }\n'
        '}',
        "api_manifest.json Summary"
    )

    pdf.tip_box(
        "Re-run discover_api.py after any KiCad update:\n"
        '"C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" scripts/discover_api.py'
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 12: CI/CD
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("CI/CD & Automation")

    pdf.section_title("GitHub Actions Workflow")
    pdf.body_text(
        "The project includes a GitHub Actions workflow that runs automatically "
        "on every push to main and every pull request. This catches regressions "
        "in the toolchain and test suite before they reach production."
    )
    pdf.code_block(load_file(".github/workflows/verify.yml"), ".github/workflows/verify.yml")
    pdf.body_text(
        "The workflow:\n"
        "  1. Checks out the repository\n"
        "  2. Sets up Python 3.11\n"
        "  3. Installs KiCad 9 from the Ubuntu PPA\n"
        "  4. Installs Python dependencies\n"
        "  5. Runs verify_toolchain.py (environment check)\n"
        "  6. Runs pytest (test suite)\n\n"
        "NOTE: CI runs on Ubuntu (GitHub's default runner), so it uses the Linux "
        "KiCad installation where pcbnew imports directly without kigadgets."
    )

    pdf.section_title("The Scaffold Script")
    pdf.body_text(
        "scripts/scaffold.py can recreate the entire directory structure from scratch. "
        "It's idempotent - running it multiple times is safe. Useful for setting up "
        "the project on a new machine or after a clean git checkout."
    )
    pdf.code_block(
        "python scripts/scaffold.py\n"
        "\n"
        "# Output:\n"
        "# === eda-kicad-agent scaffold ===\n"
        "# Created 11 directories:\n"
        "#   + .claude/agents/\n"
        "#   + .claude/commands/\n"
        "#   + agent_docs/rules/\n"
        "#   + agent_docs/skills/\n"
        "#   + contracts/\n"
        "#   + scripts/\n"
        "#   + tests/\n"
        "#   + output/\n"
        "#   + research/\n"
        "#   + review/\n"
        "#   + .github/workflows/\n"
        "# Created 1 placeholder files:\n"
        "#   + tests/__init__.py\n"
        "# Done.",
        "Scaffold Script Output"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 13: WORKFLOWS & TUTORIALS
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Workflows & Tutorials")

    pdf.section_title("Tutorial 1: Design Your First Board")
    pdf.body_text(
        "Let's walk through designing the example Simple MCU Board from scratch."
    )
    pdf.code_block(
        "STEP 1: Start Claude Code in the project directory\n"
        "  $ cd eda-kicad-agent\n"
        "  $ claude\n"
        "\n"
        "STEP 2: Create a new board contract\n"
        "  > /new-board\n"
        "  Agent: What's the board name?\n"
        "  > simple_mcu_board\n"
        "  Agent: Dimensions and layers?\n"
        "  > 50x40mm, 2 layers\n"
        "  Agent: Components?\n"
        "  > STM32 in TQFP-32, 2x 100nF bypass caps (0402),\n"
        "    10k pull-up resistor (0402), USB Micro-B, 8MHz crystal\n"
        "  Agent: Nets?\n"
        "  > VCC, GND, NRST (pull-up), USB_DP, USB_DM, OSC_IN, OSC_OUT\n"
        "\n"
        "STEP 3: Agent generates:\n"
        "  - contracts/simple_mcu_board_contract.md\n"
        "  - tests/test_simple_mcu_board.py\n"
        "\n"
        "STEP 4: Agent designs the board following pcb-design-skill.md:\n"
        "  - Creates board outline (50x40mm)\n"
        "  - Places STM32 at center\n"
        "  - Places bypass caps within 2mm of VCC pins\n"
        "  - Places crystal within 5mm of clock pins\n"
        "  - Places USB connector at board edge\n"
        "  - Defines and assigns all nets\n"
        "  - Routes traces (power first, then signals)\n"
        "  - Adds ground plane on B.Cu\n"
        "  - Runs DRC (0 errors)\n"
        "  - Runs tests (all pass)\n"
        "\n"
        "STEP 5: Review the design\n"
        "  > /review-board simple_mcu_board\n"
        "  [Reviewer -> Defender -> Referee pipeline runs]\n"
        "  Agent: Action items: [list]\n"
        "\n"
        "STEP 6: Open in KiCad GUI\n"
        "  Open output/simple_mcu_board.kicad_pcb in KiCad",
        "Full Design Workflow"
    )

    pdf.section_title("Tutorial 2: Investigate an Unknown API Function")
    pdf.code_block(
        "# Scenario: You want to add a thermal pad but aren't sure of the API\n"
        "\n"
        "> /research-api thermal pad creation\n"
        "\n"
        "# The api-researcher agent will:\n"
        "# 1. Check api_manifest.json for PAD-related classes\n"
        "# 2. Examine pcbnew module for thermal pad functions\n"
        "# 3. Search KiCad documentation online\n"
        "# 4. Save findings to research/thermal_pad.md\n"
        "# 5. Present summary to you\n"
        "\n"
        "# Key finding might be:\n"
        "# 'Use PAD with PAD_ATTRIB_SMD and set thermal relief in zone settings'",
        "API Research Workflow"
    )

    pdf.section_title("Tutorial 3: Customize for Your Project")
    pdf.body_text(
        "To adapt this system for your specific needs:\n\n"
        "1. ADD CUSTOM FOOTPRINTS:\n"
        "   - Place .pretty directories in a custom folder\n"
        "   - Update config.json footprint_library_path\n"
        "   - Re-run discover_api.py\n\n"
        "2. ADD CUSTOM RULES:\n"
        "   - Create new .md files in agent_docs/rules/\n"
        "   - Add routing entries in CLAUDE.md\n"
        "   - Keep CLAUDE.md under 50 lines\n\n"
        "3. ADD CUSTOM SKILLS:\n"
        "   - Create new .md files in agent_docs/skills/\n"
        "   - Add routing entries in CLAUDE.md\n"
        "   - Reference api_manifest.json for any API calls\n\n"
        "4. ADD CUSTOM CONTRACTS:\n"
        "   - Copy EXAMPLE_CONTRACT.md as a template\n"
        "   - Fill in your specific components and nets\n"
        "   - The /new-board command automates this"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 14: TROUBLESHOOTING
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Troubleshooting & FAQ")

    pdf.section_title("Common Issues")

    pdf.subsection_title("'import pcbnew' fails")
    pdf.body_text(
        "CAUSE: You're using system Python instead of KiCad's bundled Python.\n"
        "FIX: Use KiCad's Python:\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" your_script.py\n\n'
        "ALTERNATIVE: Link via kigadgets:\n"
        "  pip install kigadgets\n"
        "  python -m kigadgets\n"
        "  kipython your_script.py"
    )

    pdf.subsection_title("kicad-cli not found")
    pdf.body_text(
        "CAUSE: KiCad's bin directory is not on PATH.\n"
        "FIX: Add to PATH or use the full path from config.json:\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe" version'
    )

    pdf.subsection_title("Tests skip instead of running")
    pdf.body_text(
        "CAUSE: config.json is missing or pcbnew can't be imported.\n"
        "FIX: Run with KiCad's Python:\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" -m pytest tests/ -v'
    )

    pdf.subsection_title("DRC reports errors")
    pdf.body_text(
        "CAUSE: Design rule violations in the generated board.\n"
        "FIX: Check the DRC report JSON for specific violations:\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe" pcb drc '
        "--output report.json output/board.kicad_pcb\n"
        "  Then parse report.json to find violation locations and types."
    )

    pdf.subsection_title("Footprint not found")
    pdf.body_text(
        "CAUSE: Wrong footprint library path or footprint name.\n"
        "FIX: Check config.json footprint_library_path. List available footprints:\n"
        '  dir "C:\\Program Files\\KiCad\\9.0\\share\\kicad\\footprints\\*.pretty"\n'
        "  Then list footprints within a library:\n"
        '  dir "C:\\...\\Package_QFP.pretty\\*.kicad_mod"'
    )

    pdf.subsection_title("Agent uses wrong API function name")
    pdf.body_text(
        "CAUSE: api_manifest.json is outdated or wasn't generated.\n"
        "FIX: Re-run API discovery:\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" scripts/discover_api.py'
    )

    pdf.section_title("FAQ")

    pdf.subsection_title("Q: Can I use this without Claude Code?")
    pdf.body_text(
        "A: The Python scripts (discover_api.py, verify_toolchain.py) and test "
        "infrastructure work standalone. The skills, rules, and subagents are "
        "designed for Claude Code specifically, but the documentation is useful "
        "as a KiCad pcbnew API reference for anyone."
    )

    pdf.subsection_title("Q: Does this work on Linux/macOS?")
    pdf.body_text(
        "A: Yes. On Linux, pcbnew imports directly from system Python without "
        "kigadgets. On macOS, use kigadgets. Update config.json with your "
        "platform's paths. The CI workflow runs on Ubuntu successfully."
    )

    pdf.subsection_title("Q: Can I add more components beyond the example?")
    pdf.body_text(
        "A: Absolutely. Use /new-board to create contracts for any board. The "
        "system supports any KiCad footprint - there are 155 footprint libraries "
        "with thousands of individual footprints for all standard packages."
    )

    pdf.subsection_title("Q: How do I update when KiCad releases a new version?")
    pdf.body_text(
        "A: After updating KiCad:\n"
        "  1. Update config.json with new paths if they changed\n"
        "  2. Re-run discover_api.py to regenerate the API manifest\n"
        "  3. Re-run verify_toolchain.py to confirm everything works\n"
        "  4. Check api_manifest.json for any newly missing items"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 15: WINDOWS TOOLCHAIN DEEP DIVE
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Windows Toolchain Deep Dive (TOOLCHAIN_NOTES.md)")

    pdf.section_title("The pcbnew Import Problem on Windows")
    pdf.body_text(
        "On Windows, the pcbnew Python module is a compiled .pyd file inside KiCad's "
        "bundled Python installation. It is NOT importable from your system Python. "
        "This is the single most common setup issue and the TOOLCHAIN_NOTES.md file "
        "in the project root documents three strategies to resolve it."
    )
    pdf.code_block(load_file("TOOLCHAIN_NOTES.md"), "TOOLCHAIN_NOTES.md (complete)")

    pdf.section_title("Which Method to Use")
    pdf.body_text(
        "On this machine, the WORKING METHOD is Option B (KiCad's bundled Python):\n"
        '  "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe"\n\n'
        "This is recorded in config.json as:\n"
        '  python_interpreter: "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe"\n'
        '  pcbnew_import_method: "bundled_python"\n\n'
        "NOTE: The api_manifest.json records the import method as 'direct' because from "
        "KiCad's bundled Python's perspective, pcbnew imports directly. The config.json "
        "records 'bundled_python' because from the user's perspective, they must use "
        "KiCad's Python rather than their system Python. Both are correct - they describe "
        "the same situation from different viewpoints."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 16: CONFIGURATION REFERENCE
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Configuration Reference")

    pdf.section_title("config.json - Complete Reference")
    pdf.code_block(load_file("config.json"), "config.json")
    pdf.body_text(
        "FIELD REFERENCE:\n"
        "  kicad_version          -- Detected KiCad version (e.g., '9.0.7')\n"
        "  kicad_install_path     -- Root KiCad installation directory\n"
        "  kicad_cli_path         -- Full path to kicad-cli executable\n"
        "  python_interpreter     -- Python that can import pcbnew\n"
        "  pcbnew_import_method   -- How pcbnew is imported: 'bundled_python',\n"
        "                            'kigadgets', or 'direct'\n"
        "  footprint_library_path -- Directory containing .pretty folders\n"
        "  symbol_library_path    -- Directory containing .kicad_sym files\n"
        "  threed_model_path      -- Directory containing 3D model files"
    )

    pdf.section_title("api_manifest.json - Structure")
    pdf.body_text(
        "This file is auto-generated. Do not edit manually. Structure:\n"
        "  generated_at          -- ISO timestamp of last run\n"
        "  kicad_version         -- Version string from pcbnew\n"
        "  pcbnew_import_method  -- 'direct', 'kigadgets', or 'FAILED'\n"
        "  classes               -- Dict of {name: {exists, type, value}}\n"
        "  functions             -- Dict of {name: {exists, type, value}}\n"
        "  layer_constants       -- Dict of {name: {exists, type, value}}\n"
        "  footprint_io          -- Dict of IO class variants\n"
        "  pad_shapes            -- Dict of pad shape constants\n"
        "  pad_types             -- Dict of pad type constants\n"
        "  verified              -- List of names that exist\n"
        "  missing               -- List of names that don't exist\n"
        "  summary               -- {total_checked, verified, missing, coverage_pct}"
    )

    pdf.section_title(".claude/settings.json - Agent Permissions")
    pdf.body_text(
        "This file controls which tools each subagent can access. The format "
        "maps agent names to their allowed tools. Only tools listed in "
        "allowedTools are available to that agent - all others are blocked."
    )

    pdf.section_title("requirements.txt")
    pdf.code_block(load_file("requirements.txt"), "requirements.txt")
    pdf.body_text(
        "  pytest>=7.0         -- Test framework for board validation\n"
        "  kicad-python>=0.5.0 -- High-level KiCad Python bindings\n"
        "  kigadgets>=0.5.0    -- Bridge for headless pcbnew on Windows/macOS"
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CHAPTER 17: REGENERATING DOCUMENTATION
    # ═══════════════════════════════════════════════════════════════════════
    pdf.chapter_title("Regenerating This Document")

    pdf.section_title("When to Regenerate")
    pdf.body_text(
        "This PDF is generated by scripts/generate_docs_pdf.py. If you modify "
        "rules, skills, agents, or contracts, this PDF becomes stale. Regenerate it "
        "after any significant project changes."
    )
    pdf.code_block(
        "# Regenerate the PDF\n"
        "python scripts/generate_docs_pdf.py\n"
        "\n"
        "# Output: docs/EDA_KiCad_Agent_User_Guide.pdf",
        "Regeneration Command"
    )

    pdf.section_title("Project Origin")
    pdf.body_text(
        "This project was bootstrapped from Prompt/BOOTSTRAP_PROMPT.md, which defines "
        "the complete architecture, file tree, and content guidelines. Advanced users "
        "and contributors can refer to this file to understand the original design intent "
        "and the rationale behind the project's structure."
    )

    # ═══════════════════════════════════════════════════════════════════════
    # BACK COVER
    # ═══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(0, 80, 160)
    pdf.cell(0, 12, "EDA KiCad Agent", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Automated PCB Design with AI", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("DejaVu", "", 9)
    pdf.cell(0, 6, "KiCad 9.0.7 | Python 3.11 | Claude Code Opus 4.6", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "39/39 API Functions Verified | 17 Automated Tests", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "4 Subagents | 3 Slash Commands | 4 Skills | 4 Rules", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)
    pdf.set_font("DejaVu", "I", 8)
    pdf.cell(0, 6, "Contract-Driven | Test-Verified | Adversarially Reviewed", align="C", new_x="LMARGIN", new_y="NEXT")

    # Save
    pdf.output(str(OUTPUT_FILE))
    print(f"PDF generated: {OUTPUT_FILE}")
    print(f"Pages: {pdf.page_no()}")


if __name__ == "__main__":
    build_pdf()
