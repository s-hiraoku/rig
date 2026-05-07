from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOC_PATHS = [
    ROOT / "AGENTS.md",
    ROOT / "CHANGELOG.md",
    ROOT / "README.md",
    ROOT / "ROADMAP.md",
    *(ROOT / "docs").glob("*.md"),
]

REMOVED_COMMAND_REFERENCES = (
    "rig run ",
    "rig list",
    "rig show ",
    "rig worktree ",
    "rig manual ",
    "rig guide ",
    "rig env ",
    "rig suggest",
)

REMOVED_MCP_REFERENCES = (
    "rig_run",
    "rig_list_runs",
    "rig_get_run",
    "rig_get_result",
    "rig_get_diff",
    "rig_apply_patch",
    "rig_suggest",
)

ALLOWED_REMOVED_REFERENCES = {
    ROOT / "ROADMAP.md": {
        "rig suggest",
    },
}


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


def test_current_docs_do_not_advertise_removed_mvp_commands() -> None:
    failures: list[str] = []
    for path in DOC_PATHS:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            failures.append(f"{path.relative_to(ROOT)}: missing file")
            continue

        allowed = ALLOWED_REMOVED_REFERENCES.get(path, set())
        for needle in REMOVED_COMMAND_REFERENCES + REMOVED_MCP_REFERENCES:
            if needle in allowed:
                continue
            if needle in text:
                failures.append(f"{path.relative_to(ROOT)}: {needle}")

    assert failures == [], f"unexpected removed command references: {failures}"
