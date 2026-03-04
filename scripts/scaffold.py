#!/usr/bin/env python3
"""Scaffold the eda-kicad-agent directory tree.

Idempotent: skips directories/files that already exist.
Run from the project root: python scripts/scaffold.py
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    ".claude/agents",
    ".claude/commands",
    "agent_docs/rules",
    "agent_docs/skills",
    "contracts",
    "scripts",
    "tests",
    "output",
    "research",
    "review",
    ".github/workflows",
]

# Files that should exist as empty placeholders (only created if missing)
PLACEHOLDER_FILES = [
    "tests/__init__.py",
]


def scaffold() -> None:
    created_dirs: list[str] = []
    created_files: list[str] = []
    skipped: list[str] = []

    for d in DIRECTORIES:
        path = PROJECT_ROOT / d
        if path.exists():
            skipped.append(str(d))
        else:
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(d))

    for f in PLACEHOLDER_FILES:
        path = PROJECT_ROOT / f
        if path.exists():
            skipped.append(str(f))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            created_files.append(str(f))

    print("=== eda-kicad-agent scaffold ===")
    if created_dirs:
        print(f"\nCreated {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"  + {d}/")
    if created_files:
        print(f"\nCreated {len(created_files)} placeholder files:")
        for f in created_files:
            print(f"  + {f}")
    if skipped:
        print(f"\nSkipped {len(skipped)} (already exist):")
        for s in skipped:
            print(f"  ~ {s}")
    print("\nDone.")


if __name__ == "__main__":
    scaffold()
