#!/usr/bin/env python3
"""Create the initial label set for the epub2pdf GitHub repository.

Requires the GitHub CLI (`gh`) to be installed and authenticated.
Run from the repository root:

    python3 scripts/setup_labels.py
"""

from __future__ import annotations

import subprocess
import sys

LABELS = [
    # type
    ("type: bug", "d73a4a", "Something is broken"),
    ("type: feature", "a2eeef", "New capability"),
    ("type: docs", "0075ca", "Documentation"),
    ("type: refactor", "c5def5", "Code restructuring"),
    ("type: test", "ffd54f", "Tests"),
    ("type: security", "d93f0b", "Security-related"),
    # status
    ("status: needs triage", "fef2c0", "Needs initial review"),
    ("status: accepted", "0e8a16", "Accepted, waiting for implementation"),
    ("status: in progress", "ededed", "Currently being worked on"),
    ("status: blocked", "b60205", "Blocked by another issue or decision"),
    ("status: needs review", "fbca04", "Needs review"),
    ("status: wontfix", "ffffff", "Won't be addressed"),
    # area
    ("area: cli", "5319e7", "Command-line interface"),
    ("area: render", "5319e7", "PDF rendering engines"),
    ("area: extract", "5319e7", "PDF extraction backends"),
    ("area: pipeline", "5319e7", "High-level workflows"),
    ("area: mcp", "5319e7", "MCP server and agent integrations"),
    ("area: docker", "5319e7", "Docker image and publishing"),
    ("area: docs", "5319e7", "Documentation"),
    ("area: infra", "5319e7", "CI, packaging, repository settings"),
    # difficulty
    ("difficulty: good first issue", "7057ff", "Friendly for newcomers"),
    ("difficulty: help wanted", "008672", "Community help appreciated"),
    ("difficulty: advanced", "b60205", "Requires deep context"),
    # risk
    ("risk: breaking-change", "f9d0c4", "Changes public behavior or schema"),
    ("risk: security-sensitive", "d93f0b", "Security-sensitive code"),
    ("risk: ai-generated", "d876e3", "AI-assisted contribution"),
    ("risk: experimental", "f9d0c4", "Not yet stable"),
]


def run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    print(result.stdout, end="")


def main() -> int:
    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed.", file=sys.stderr)
        return 1
    output = result.stdout + result.stderr
    if "Active account: true" not in output:
        print("Error: GitHub CLI (gh) does not have an active authenticated account.", file=sys.stderr)
        return 1

    for name, color, description in LABELS:
        print(f"Creating label: {name}")
        run(
            [
                "gh",
                "label",
                "create",
                name,
                "--color",
                color,
                "--description",
                description,
                "--force",
            ]
        )

    print("Labels created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
