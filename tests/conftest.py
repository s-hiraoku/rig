from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


def install_fake_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "codex",
    stdout: str = "done\n",
    stderr: str = "",
    exit_code: int = 0,
) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    command_path = bin_dir / name
    command_path.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import json",
                "import pathlib",
                "import sys",
                "pathlib.Path('fake-command-argv.json').write_text(json.dumps(sys.argv), encoding='utf-8')",
                f"sys.stdout.write({stdout!r})",
                f"sys.stderr.write({stderr!r})",
                f"raise SystemExit({exit_code})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    command_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    return command_path


def install_fake_script(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str,
    body: str,
) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    command_path = bin_dir / name
    command_path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    command_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")
    return command_path


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "rig@example.com"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Rig Tests"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    (path / "tracked.txt").write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True
    )
