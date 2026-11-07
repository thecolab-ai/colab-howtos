#!/usr/bin/env python3
"""Repo checks the mycourse validator doesn't cover. Exits 1 on any failure.

- No YAML frontmatter in any .md under modules/, courses/ or recaps/ (the player and the
  site render it as text).
- Recaps are named recaps/<YYYY>-W<NN>.md and start with "# ".
- Every .md in a module is listed as a lesson in its manifest.json, and starts with "# ".
- Every module has a howto.json that agrees with manifest.json (title, tags) and the first
  lesson heading. Non-example modules are named howto-<slug>, are listed in
  courses/colab-howtos/course.json, and any `recap` they name exists in recaps/.
- No video files, video links or Git LFS.
- Privacy grep over every text file, recaps included: phone numbers, emails (noreply
  addresses allowed), claude.ai links, Google Docs/Drive links, ChatGPT share links.
- With REQUIRE_ISSUE_LINKS=1 (set in CI), no ISSUE(<slug>) placeholders left in recaps.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

from howtolib import RECAP_NAME_RE, ROLLING_COURSE, ROOT, STATUSES, load_module, module_dirs

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "_site"}
# Generated at build time from the GitHub API; not part of the reviewed content.
SKIP_FILES = {"site/data/issues.json"}
NON_LESSON_DIRS = {"assets", "downloads"}
CONTENT_DIRS = {"modules", "courses", "recaps"}
RECAP_EXTRA_FILES = {"README.md"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}
VIDEO_LINK_RE = re.compile(r"\.(?:mp4|mov|m4v|webm)(?:[?#)\s\"'>]|$)|colab-howtos\.pages\.dev", re.IGNORECASE)
ISSUE_PLACEHOLDER = "ISSUE("

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
# Candidate phone numbers: start with + or a leading 0 (NZ style), then digits and separators.
PHONE_RE = re.compile(r"(?<![\w.:/#-])(?:\+|\(?0)[\d ()\-.]{6,}\d(?![\w-])")
LINK_RES = [
    (re.compile(r"claude\.ai/[^\s)>\]]", re.IGNORECASE), "claude.ai link"),
    (re.compile(r"docs\.google\.com", re.IGNORECASE), "Google Docs link"),
    (re.compile(r"drive\.google\.com", re.IGNORECASE), "Google Drive link"),
    (re.compile(r"chatgpt\.com/share", re.IGNORECASE), "ChatGPT share link"),
    (re.compile(r"chat\.openai\.com/share", re.IGNORECASE), "ChatGPT share link"),
]


class Checker:
    def __init__(self, root: Path, require_issue_links: bool) -> None:
        self.root = root
        self.require_issue_links = require_issue_links
        self.failures: list[str] = []
        self.notes: list[str] = []

    def fail(self, path: Path, message: str, line: int | None = None) -> None:
        where = path.relative_to(self.root).as_posix()
        if line is not None:
            where += f":{line}"
        self.failures.append(f"{where}: {message}")

    def files(self) -> list[Path]:
        found = []
        for path in sorted(self.root.rglob("*")):
            rel = path.relative_to(self.root)
            if any(part in SKIP_DIRS for part in rel.parts) or not path.is_file():
                continue
            if rel.as_posix() in SKIP_FILES:
                continue
            found.append(path)
        return found

    def rel(self, path: Path) -> Path:
        return path.relative_to(self.root)

    # --- markdown -----------------------------------------------------------------

    def check_frontmatter(self, files: list[Path]) -> None:
        for path in files:
            if path.suffix != ".md" or self.rel(path).parts[0] not in CONTENT_DIRS:
                continue
            if path.read_text(encoding="utf-8").lstrip("\ufeff").startswith("---"):
                self.fail(path, "starts with --- frontmatter; plain markdown only (module metadata goes in howto.json)")

    def check_recaps(self) -> int:
        recaps_dir = self.root / "recaps"
        if not recaps_dir.is_dir():
            return 0
        count = 0
        for path in sorted(recaps_dir.iterdir()):
            if path.is_dir():
                continue
            if path.suffix != ".md" or not RECAP_NAME_RE.match(path.name):
                if path.name not in RECAP_EXTRA_FILES and path.name != ".gitkeep":
                    self.fail(path, "recaps must be named <YYYY>-W<NN>.md, e.g. 2026-W45.md")
                continue
            count += 1
            year, week = path.stem.split("-W")
            try:
                datetime.date.fromisocalendar(int(year), int(week), 1)
            except ValueError:
                self.fail(path, f"{path.stem} is not a real ISO week")
            text = path.read_text(encoding="utf-8")
            if not text.startswith("# "):
                self.fail(path, "recap must start with '# Title'")
            hits = [n for n, line in enumerate(text.splitlines(), start=1) if ISSUE_PLACEHOLDER in line]
            if hits and self.require_issue_links:
                for number in hits:
                    self.fail(path, "ISSUE(...) placeholder not replaced with an issue link", number)
            elif hits:
                self.notes.append(
                    f"{self.rel(path).as_posix()}: {len(hits)} line(s) with ISSUE(...) placeholders "
                    "(allowed because REQUIRE_ISSUE_LINKS is not 1)"
                )
        return count

    # --- modules ------------------------------------------------------------------

    def check_lessons(self, module_dir: Path, manifest: dict) -> None:
        if manifest.get("id") != module_dir.name:
            self.fail(module_dir / "manifest.json", f"id must equal the directory name {module_dir.name!r}")
        listed = set()
        for lesson in manifest.get("lessons", []):
            raw = lesson.get("markdownPath") if isinstance(lesson, dict) else None
            if isinstance(raw, str):
                listed.add((module_dir / raw).resolve())
        for md in sorted(module_dir.rglob("*.md")):
            if md.relative_to(module_dir).parts[0] in NON_LESSON_DIRS:
                continue
            if md.resolve() not in listed:
                self.fail(md, "lesson markdown is not listed in manifest.json")
            if not md.read_text(encoding="utf-8").startswith("# "):
                self.fail(md, "lesson must start with '# Title'")

    def check_module(self, module_dir: Path, rolling: list[str]) -> bool:
        """Returns True for a real (non-example) module."""
        for name in ("manifest.json", "howto.json"):
            if not (module_dir / name).is_file():
                self.fail(module_dir, f"module has no {name}")
                return False
        try:
            module = load_module(module_dir)
        except (OSError, ValueError) as exc:
            self.fail(module_dir, f"cannot read manifest.json or howto.json: {exc}")
            return False

        self.check_lessons(module_dir, module.manifest)
        meta, meta_path = module.howto, module_dir / "howto.json"

        for key in ("title", "tags"):
            if meta.get(key) != module.manifest.get(key):
                self.fail(meta_path, f"{key} differs from manifest.json")
        content = [l for l in module.lessons if l.get("type") == "content" and l.get("markdownPath")]
        if content:
            first = module_dir / content[0]["markdownPath"]
            if first.is_file():
                heading = first.read_text(encoding="utf-8").split("\n", 1)[0]
                if heading != f"# {meta.get('title')}":
                    self.fail(first, "first line must be '# ' plus the howto.json title")

        # The JSON Schema covers these too; repeated here so this script works on its own.
        if meta.get("status") not in STATUSES:
            self.fail(meta_path, f"status must be one of {', '.join(STATUSES)}")
        contributors = meta.get("contributors")
        if not isinstance(contributors, list) or not contributors:
            self.fail(meta_path, "contributors must list at least one first name or GitHub username")
        if "tested" in meta:
            self.fail(meta_path, "'tested' was replaced by status (seed, draft or tested)")

        recap = meta.get("recap")
        if recap is not None and not (self.root / "recaps" / f"{recap}.md").is_file():
            self.fail(meta_path, f"recap {recap!r} has no recaps/{recap}.md")

        if module.example:
            return False
        if not module_dir.name.startswith("howto-"):
            self.fail(module_dir, "module folders are named howto-<slug>")
        if module_dir.name not in rolling:
            self.fail(meta_path, f"module is not listed in courses/{ROLLING_COURSE}/course.json")
        return True

    def load_rolling_course(self) -> list[str]:
        course_file = self.root / "courses" / ROLLING_COURSE / "course.json"
        try:
            course = json.loads(course_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.failures.append(f"courses/{ROLLING_COURSE}/course.json: cannot read: {exc}")
            return []
        modules = course.get("modules", [])
        return [m for m in modules if isinstance(m, str)]

    # --- media and privacy --------------------------------------------------------

    def check_media(self, files: list[Path]) -> None:
        for path in files:
            if path.suffix.lower() in VIDEO_SUFFIXES:
                self.fail(path, "video files don't belong in this repo")
            if path.name == ".gitattributes" and "filter=lfs" in path.read_text(encoding="utf-8"):
                self.fail(path, "Git LFS is not used in this repo")
            if path.suffix == ".md" and self.rel(path).parts[0] in CONTENT_DIRS:
                for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                    if VIDEO_LINK_RE.search(line):
                        self.fail(path, "video link; this repo has no videos", number)

    def check_privacy(self, files: list[Path]) -> tuple[int, int]:
        scanned = recaps = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            scanned += 1
            recaps += self.rel(path).parts[0] == "recaps"
            for number, line in enumerate(text.splitlines(), start=1):
                for match in EMAIL_RE.finditer(line):
                    if "noreply" not in match.group(0).lower():
                        self.fail(path, f"email address: {match.group(0)}", number)
                for match in PHONE_RE.finditer(line):
                    digits = re.sub(r"\D", "", match.group(0))
                    if 8 <= len(digits) <= 15:
                        self.fail(path, f"possible phone number: {match.group(0).strip()}", number)
                for pattern, label in LINK_RES:
                    if pattern.search(line):
                        self.fail(path, label, number)
        return scanned, recaps

    def run(self) -> int:
        files = self.files()
        self.check_frontmatter(files)
        recap_count = self.check_recaps()
        rolling = self.load_rolling_course()
        modules = module_dirs(self.root)
        real = sum(self.check_module(d, rolling) for d in modules)
        self.check_media(files)
        scanned, recap_files = self.check_privacy(files)

        for note in self.notes:
            print(f"note: {note}")
        if self.failures:
            for failure in self.failures:
                print(f"FAIL {failure}")
            print(f"check_repo: {len(self.failures)} problem(s)")
            return 1
        print(
            f"check_repo: OK ({len(modules)} modules, {real} non-example, {recap_count} recaps, "
            f"{scanned} text files scanned incl. {recap_files} in recaps/, "
            f"issue links {'required' if self.require_issue_links else 'not required'})"
        )
        return 0


def main() -> int:
    return Checker(ROOT, os.environ.get("REQUIRE_ISSUE_LINKS") == "1").run()


if __name__ == "__main__":
    sys.exit(main())
