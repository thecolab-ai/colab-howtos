#!/usr/bin/env python3
"""Assemble the static viewer into an output folder (default _site/) for GitHub Pages.

Copies site/ (the viewer), recaps/*.md, courses/ and modules/ into the output, then writes
data/content.json, the index the viewer reads (Pages has no directory listing). If an
issues file exists (the Pages workflow fetches it with `gh api`), it is trimmed to the
fields the viewer needs and written to data/issues.json. Without it the viewer links to
the issue list on GitHub instead.

Usage:
  python3 scripts/build_site.py [--out _site] [--recaps-dir recaps] [--issues site/data/issues.json]

Stdlib only. The output folder is deleted and rebuilt, so it must be empty or a previous
build (it has data/content.json), and it can't be the repo root or a source folder.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import sys
from pathlib import Path

from howtolib import REPO_SLUG, ROLLING_COURSE, ROOT, Module, load_modules, load_recaps, read_json

SOURCE_DIRS = ("site", "modules", "courses", "recaps", "scripts", "schema", "tools", ".github", ".git")
IGNORE = shutil.ignore_patterns(".gitkeep", ".DS_Store", "__pycache__")


def safe_out_dir(out: Path) -> Path:
    out = out.resolve()
    if out == ROOT or out in ROOT.parents:
        sys.exit(f"build_site: refusing to write to {out}: it contains the repo")
    for name in SOURCE_DIRS:
        source = ROOT / name
        if out == source or source in out.parents:
            sys.exit(f"build_site: refusing to write inside {name}/")
    if out.exists():
        if not out.is_dir():
            sys.exit(f"build_site: {out} is not a folder")
        if any(out.iterdir()) and not (out / "data" / "content.json").is_file():
            sys.exit(f"build_site: {out} is not empty and is not a previous build; pick another --out")
        shutil.rmtree(out)
    return out


def week_dates(week: str) -> tuple[str, str]:
    year, number = week.split("-W")
    try:
        start = datetime.date.fromisocalendar(int(year), int(number), 1)
    except ValueError:
        sys.exit(f"build_site: recaps/{week}.md is not a real ISO week")
    return start.isoformat(), (start + datetime.timedelta(days=6)).isoformat()


def module_entry(module: Module) -> dict:
    meta = module.howto
    lessons = []
    for lesson in module.lessons:
        entry = {"id": lesson.get("id"), "title": lesson.get("title"), "type": lesson.get("type")}
        raw = lesson.get("markdownPath") if lesson.get("type") == "content" else lesson.get("quizPath")
        if isinstance(raw, str):
            entry["path"] = f"modules/{module.id}/{raw}"
        lessons.append(entry)
    entry = {
        "id": module.id,
        "title": meta.get("title") or module.manifest.get("title"),
        "description": module.manifest.get("description", ""),
        "tags": meta.get("tags", []),
        "difficulty": meta.get("difficulty"),
        "status": meta.get("status"),
        "contributors": meta.get("contributors", []),
        "example": meta.get("example") is True,
        "path": f"modules/{module.id}/",
        "lessons": lessons,
    }
    for key in ("recap", "issue"):
        if key in meta:
            entry[key] = meta[key]
    return entry


def course_entries() -> list[dict]:
    courses = []
    for course_file in sorted((ROOT / "courses").glob("*/course.json")):
        course = read_json(course_file)
        folder = course_file.parent.name
        entry = {
            "id": course.get("id", folder),
            "title": course.get("title", ""),
            "description": course.get("description", ""),
            "modules": [m for m in course.get("modules", []) if isinstance(m, str)],
        }
        if isinstance(course.get("welcomePath"), str):
            entry["welcomePath"] = f"courses/{folder}/{course['welcomePath']}"
        courses.append(entry)
    return courses


def flatten(raw: object) -> list:
    """`gh api --paginate --slurp` gives a list of pages; plain `gh api` gives one list."""
    if isinstance(raw, dict):
        return [raw]
    items: list = []
    for item in raw if isinstance(raw, list) else []:
        items.extend(flatten(item) if isinstance(item, list) else [item])
    return items


def normalise_issues(raw: object) -> list[dict]:
    issues = []
    for item in flatten(raw):
        if not isinstance(item, dict) or "pull_request" in item or item.get("state", "open") != "open":
            continue
        labels = [l.get("name") if isinstance(l, dict) else l for l in item.get("labels", [])]
        labels = [l for l in labels if isinstance(l, str)]
        if "module" not in labels:
            continue
        issues.append({
            "number": item.get("number"),
            "title": item.get("title", ""),
            "url": item.get("html_url") or item.get("url", ""),
            "labels": labels,
            "help_wanted": "help wanted" in labels,
            "claimed": bool(item.get("assignees")) or bool(item.get("claimed")) or "claimed" in labels,
            "comments": item.get("comments", 0),
            "updated_at": item.get("updated_at", ""),
        })
    # Open for the taking first, then newest first.
    issues.sort(key=lambda i: (i["claimed"], -(i["number"] or 0)))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble the static viewer for GitHub Pages.")
    parser.add_argument("--out", type=Path, default=ROOT / "_site", help="output folder (default _site/)")
    parser.add_argument("--recaps-dir", type=Path, default=ROOT / "recaps",
                        help="where the recap markdown lives (default recaps/; override for local tests)")
    parser.add_argument("--issues", type=Path, default=ROOT / "site" / "data" / "issues.json",
                        help="open module issues as JSON from the GitHub API (optional)")
    args = parser.parse_args()

    # Read and check everything first, so a bad input leaves the output folder untouched.
    recaps = load_recaps(args.recaps_dir.resolve())
    recap_entries = []
    for recap in recaps:
        start, end = week_dates(recap.week)
        recap_entries.append({
            "week": recap.week,
            "title": recap.title,
            "summary": recap.summary,
            "start": start,
            "end": end,
            "path": f"recaps/{recap.path.name}",
        })
    modules = load_modules(ROOT)
    courses = course_entries()
    rolling = next((c["modules"] for c in courses if c["id"] == ROLLING_COURSE), [])
    order = {module_id: n for n, module_id in enumerate(rolling)}
    modules.sort(key=lambda m: (order.get(m.id, len(order)), m.id))
    content = {
        "generated": datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat(),
        "repo": os.environ.get("GITHUB_REPOSITORY") or REPO_SLUG,
        "recaps": recap_entries,
        "courses": courses,
        "modules": [module_entry(m) for m in modules],
    }
    issues = None
    issues_note = "no issues file, the site links to GitHub instead"
    if args.issues.is_file():
        try:
            issues = normalise_issues(json.loads(args.issues.read_text(encoding="utf-8")))
            issues_note = f"{len(issues)} open module issues"
        except json.JSONDecodeError as exc:
            print(f"build_site: warning: {args.issues} is not valid JSON ({exc}); skipping issues", file=sys.stderr)

    out = safe_out_dir(args.out)
    shutil.copytree(ROOT / "site", out, ignore=shutil.ignore_patterns(".gitkeep", ".DS_Store", "data"))
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "recaps").mkdir()
    for recap in recaps:
        shutil.copy2(recap.path, out / "recaps" / recap.path.name)
    shutil.copytree(ROOT / "courses", out / "courses", ignore=IGNORE)
    shutil.copytree(ROOT / "modules", out / "modules", ignore=IGNORE)
    (out / "data").mkdir()
    (out / "data" / "content.json").write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    if issues is not None:
        (out / "data" / "issues.json").write_text(json.dumps(issues, indent=2) + "\n", encoding="utf-8")

    real = sum(not m.example for m in modules)
    print(f"build_site: {out} ({len(recaps)} recaps, {real} modules plus {len(modules) - real} example, {issues_note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
