"""Shared helpers for the repo scripts: find recaps and modules, read their metadata.

Stdlib only. The scripts run as `python3 scripts/<name>.py`, so this module is importable
because scripts/ is first on sys.path.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLLING_COURSE = "colab-howtos"
REPO_SLUG = "thecolab-ai/colab-howtos"
REPO_URL = f"https://github.com/{REPO_SLUG}"
SITE_URL = "https://thecolab-ai.github.io/colab-howtos/"
ISSUES_URL = f"{REPO_URL}/issues?q=is%3Aopen+label%3Amodule"
RECAP_NAME_RE = re.compile(r"^(?P<week>[0-9]{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3]))\.md$")
STATUSES = ("seed", "draft", "tested")


@dataclass
class Recap:
    week: str
    path: Path
    title: str
    summary: str


@dataclass
class Module:
    id: str
    path: Path
    manifest: dict
    howto: dict
    lessons: list[dict] = field(default_factory=list)

    @property
    def example(self) -> bool:
        return self.howto.get("example") is True


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recap_files(recaps_dir: Path) -> list[Path]:
    """recaps/<YYYY>-W<NN>.md files, newest week first. Other files are ignored."""
    if not recaps_dir.is_dir():
        return []
    files = [p for p in recaps_dir.iterdir() if p.is_file() and RECAP_NAME_RE.match(p.name)]
    return sorted(files, key=lambda p: p.name, reverse=True)


def first_paragraph(lines: list[str]) -> str:
    """The first plain paragraph after the title, as one line of text."""
    para: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if para:
                break
            continue
        if stripped.startswith(("#", "|", "```", "- ", "* ", ">")) or re.match(r"^\d+[.)] ", stripped):
            if para:
                break
            continue
        para.append(stripped)
    text = " ".join(para)
    # Drop the common inline markdown so the summary reads as plain text.
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`]{1,2}([^*_`]+)[*_`]{1,2}", r"\1", text)
    return text


def load_recap(path: Path) -> Recap:
    lines = path.read_text(encoding="utf-8").splitlines()
    first = lines[0] if lines else ""
    title = first[2:].strip() if first.startswith("# ") else path.stem
    week = RECAP_NAME_RE.match(path.name).group("week")  # type: ignore[union-attr]
    return Recap(week=week, path=path, title=title, summary=first_paragraph(lines[1:]))


def load_recaps(recaps_dir: Path) -> list[Recap]:
    return [load_recap(p) for p in recap_files(recaps_dir)]


def module_dirs(root: Path) -> list[Path]:
    modules = root / "modules"
    if not modules.is_dir():
        return []
    return sorted(p for p in modules.iterdir() if p.is_dir())


def load_module(module_dir: Path) -> Module:
    """Raises OSError or ValueError (json.JSONDecodeError) if a file is missing or broken."""
    manifest = read_json(module_dir / "manifest.json")
    howto = read_json(module_dir / "howto.json")
    lessons = [l for l in manifest.get("lessons", []) if isinstance(l, dict)]
    return Module(id=module_dir.name, path=module_dir, manifest=manifest, howto=howto, lessons=lessons)


def load_modules(root: Path) -> list[Module]:
    return [load_module(d) for d in module_dirs(root)]


def first_lesson_path(module: Module) -> Path:
    for lesson in module.lessons:
        if lesson.get("type") == "content" and isinstance(lesson.get("markdownPath"), str):
            return module.path / lesson["markdownPath"]
    return module.path / "manifest.json"
