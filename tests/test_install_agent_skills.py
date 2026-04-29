from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class InstallAgentSkillsTests(unittest.TestCase):
    def test_installer_copies_codex_and_opencode_templates(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            codex_home = root / "codex-home"
            opencode_home = root / "opencode-home"

            result = subprocess.run(
                [
                    sys.executable,
                    str(repo_root / "scripts" / "install_agent_skills.py"),
                    "--repo-root",
                    str(repo_root),
                    "--codex-home",
                    str(codex_home),
                    "--opencode-config-home",
                    str(opencode_home),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            codex_skill = codex_home / "skills" / "epub2pdf" / "SKILL.md"
            codex_openai_yaml = codex_home / "skills" / "epub2pdf" / "agents" / "openai.yaml"
            opencode_skill = opencode_home / "skills" / "epub2pdf" / "SKILL.md"

            self.assertTrue(codex_skill.exists())
            self.assertTrue(codex_openai_yaml.exists())
            self.assertTrue(opencode_skill.exists())
            self.assertIn(str(codex_skill.parent), result.stdout)
            self.assertIn(str(opencode_skill.parent), result.stdout)
