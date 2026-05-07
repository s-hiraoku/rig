from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_docs_navigation_targets_exist() -> None:
    layout = (ROOT / "docs" / "_layouts" / "default.html").read_text(
        encoding="utf-8"
    )
    match = re.search(r'assign nav_data = "([^"]+)"', layout)
    assert match is not None

    for entry in match.group(1).split(";;"):
        _group, url, _title = entry.split("|")
        if url == "/":
            target = ROOT / "docs" / "index.md"
        else:
            target = ROOT / "docs" / url.lstrip("/").replace(".html", ".md")
        assert target.is_file(), f"missing docs nav target: {url}"


def test_docs_do_not_reference_removed_cli_commands() -> None:
    stale_patterns = (
        "rig suggest",
        "rig show latest",
        "rig run ",
        "rig list",
        "rig env ",
        "rig guide ",
        "rig worktree",
    )
    allowed_files = {
        ROOT / "docs" / "troubleshooting.md",
    }
    docs = [
        path
        for path in (ROOT / "docs").glob("*.md")
        if path not in allowed_files
    ]
    docs.extend([ROOT / "README.md", ROOT / "AGENTS.md"])

    for path in docs:
        text = path.read_text(encoding="utf-8")
        for pattern in stale_patterns:
            assert pattern not in text, f"{path} references removed command {pattern!r}"
