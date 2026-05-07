from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HarnessGuide:
    id: str
    name: str
    source_url: str
    docs_url: str
    summary: str
    use_when: list[str]
    copyable_parts: list[str]
    commands: list[str]
    notes: list[str]


CODEX_HARNESSES = HarnessGuide(
    id="codex-harnesses",
    name="codex-harnesses",
    source_url="https://github.com/s-hiraoku/codex-harnesses",
    docs_url="https://s-hiraoku.github.io/codex-harnesses/",
    summary=(
        "Copyable Codex project harnesses for AGENTS.md templates, skills, hooks, "
        "policies, ledgers, and verification scripts."
    ),
    use_when=[
        "You want a complete Codex project harness around Rig.",
        "You need reusable skills, safety hooks, policy examples, or task ledgers.",
        "You want local and CI verification to share one project-specific script.",
    ],
    copyable_parts=[
        "templates/agents/",
        "skills/",
        "hooks/",
        "policies/",
        "ledger/",
        "scripts/verify.sh",
        "examples/",
    ],
    commands=[
        "git clone https://github.com/s-hiraoku/codex-harnesses.git",
        "cp codex-harnesses/templates/agents/strict/AGENTS.md AGENTS.md",
        "cp codex-harnesses/scripts/verify.sh scripts/verify.sh",
        "cp -R codex-harnesses/ledger ledger",
    ],
    notes=[
        "Rig stays focused on delegated runs and patch artifacts.",
        "codex-harnesses owns broader project guidance, skills, hooks, policies, and ledgers.",
        "Adapt copied files before relying on them in a production repository.",
    ],
)


def get_harness_guide(source: str) -> HarnessGuide:
    if source == CODEX_HARNESSES.id:
        return CODEX_HARNESSES
    raise ValueError(f"Unknown harness source: {source}")


def harness_guide_payload(guide: HarnessGuide) -> dict[str, Any]:
    return asdict(guide)


def format_harness_guide(guide: HarnessGuide) -> str:
    lines = [
        f"Rig harness source: {guide.name}",
        "",
        guide.summary,
        "",
        f"Source: {guide.source_url}",
        f"Docs:   {guide.docs_url}",
        "",
        "Use when",
    ]
    lines.extend(f"- {item}" for item in guide.use_when)
    lines.extend(["", "Copyable parts"])
    lines.extend(f"- {item}" for item in guide.copyable_parts)
    lines.extend(["", "Starting commands"])
    lines.extend(f"- {command}" for command in guide.commands)
    lines.extend(["", "Notes"])
    lines.extend(f"- {note}" for note in guide.notes)
    return "\n".join(lines) + "\n"
