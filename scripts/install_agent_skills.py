#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install epub2pdf skill wrappers into global Codex and OpenCode skill directories."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to the epub2pdf repository root.",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")),
        help="Codex home directory. Defaults to $CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--opencode-config-home",
        type=Path,
        default=Path.home() / ".config" / "opencode",
        help="OpenCode config directory. Defaults to ~/.config/opencode.",
    )
    parser.add_argument(
        "--target",
        choices=("both", "codex", "opencode"),
        default="both",
        help="Install only Codex, only OpenCode, or both integrations.",
    )
    return parser.parse_args()


def install_tree(src: Path, dest: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Missing integration template: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, dirs_exist_ok=True)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    codex_template = repo_root / "integrations" / "codex" / "epub2pdf"
    opencode_template = repo_root / "integrations" / "opencode" / "epub2pdf"

    installed_paths: list[Path] = []

    if args.target in {"both", "codex"}:
        codex_dest = args.codex_home.resolve() / "skills" / "epub2pdf"
        install_tree(codex_template, codex_dest)
        installed_paths.append(codex_dest)

    if args.target in {"both", "opencode"}:
        opencode_dest = args.opencode_config_home.resolve() / "skills" / "epub2pdf"
        install_tree(opencode_template, opencode_dest)
        installed_paths.append(opencode_dest)

    for path in installed_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
