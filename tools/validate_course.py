#!/usr/bin/env python3
# vendored: source repo mycourse-work/dronetrust (private)
# vendored: path .skills/mycourse-course-authoring/scripts/validate_course.py
# vendored: commit 1117acea439b2324f0f9b2d5ec0e8d34876782d6
# vendored: fetched 2026-11-08. Stdlib only, no helper modules. Do not edit by hand:
# vendored: re-vendor from upstream and update the commit line. Lines starting
# vendored: with this prefix are ignored by the nightly drift check.
"""Validate a module-first MyCourse/CourseViewerPlatform course package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_QUESTION_TYPES = {
    "MULTIPLE_CHOICE",
    "MULTIPLE_RESPONSE",
    "TRUE_FALSE",
    "MATCHING",
}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_RESOURCE_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_SOURCE_RE = re.compile(r"\b(?:src|href)=[\"']([^\"']+)[\"']", re.IGNORECASE)
WIDGET_RE = re.compile(r"^:::widget\s+([A-Za-z0-9_-]+)\s*$", re.MULTILINE)
# Same block match as the player's LessonRenderer: name line, then props up to the closing :::.
WIDGET_BLOCK_RE = re.compile(r":::widget\s+([^\n]+?)[ \t]*\n([\s\S]*?):::")
DIRECTIVE_PROP_RE = re.compile(r"^([a-zA-Z0-9_-]+)\s*:\s*(.+)$")
# Player protocol v2.1 (course.platform docs/widget-focus-mode.md).
FULLSCREEN_VALUES = {"phone", "always", "off"}
FOCUS_HINT = "recommended for full-screen on phones"
REFLECTION_ID_RE = re.compile(r'class=[\"\']reflection[\"\'][^>]*data-id=[\"\']([^\"\']+)', re.IGNORECASE)


def parse_directive_props(block: str) -> dict[str, Any]:
    """Python port of the player's parseDirectiveProps (packages/core/utils/directive-props.ts)."""
    props: dict[str, Any] = {}
    for line in block.split("\n"):
        match = DIRECTIVE_PROP_RE.match(line.strip())
        if not match:
            continue
        raw = match.group(2).strip()
        props[match.group(1)] = True if raw == "true" else False if raw == "false" else raw
    return props


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.stats = {"modules": 0, "contentLessons": 0, "quizzes": 0, "questions": 0}
        self.checked_widgets: set[Path] = set()

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Course directory or course.json path")
    parser.add_argument("--repo-root", type=Path, help="Repository root containing modules/ and widgets/")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args()


def load_json(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"Missing file: {path}")
        return None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report.error(f"Cannot parse JSON {path}: {exc}")
        return None
    if not isinstance(value, dict):
        report.error(f"JSON root must be an object: {path}")
        return None
    return value


def infer_paths(target: Path, repo_arg: Path | None, report: Report) -> tuple[Path, Path] | None:
    target = target.expanduser().resolve()
    course_file = target if target.name == "course.json" else target / "course.json"
    course_dir = course_file.parent
    if not course_file.is_file():
        report.error(f"Expected course.json at {course_file}")
        return None

    if repo_arg:
        repo_root = repo_arg.expanduser().resolve()
    else:
        repo_root = next((p for p in (course_dir, *course_dir.parents) if (p / "modules").is_dir()), None)
        if repo_root is None:
            report.error("Could not infer repository root containing modules/; pass --repo-root")
            return None

    if not (repo_root / "modules").is_dir():
        report.error(f"Repository root has no modules/ directory: {repo_root}")
        return None
    return course_file, repo_root


def require_string(obj: dict[str, Any], key: str, where: str, report: Report) -> str | None:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        report.error(f"{where}: {key} must be a non-empty string")
        return None
    return value


def check_id(value: str | None, where: str, report: Report) -> None:
    if value and not ID_RE.fullmatch(value):
        report.warn(f"{where}: ID should be kebab-case: {value!r}")


def safe_local_path(base: Path, raw: str, repo_root: Path, where: str, report: Report) -> Path | None:
    cleaned = raw.strip().split("#", 1)[0].split("?", 1)[0]
    if not cleaned or cleaned.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:", "javascript:")):
        return None
    candidate = (base / cleaned).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        report.error(f"{where}: local path escapes repository root: {raw}")
        return None
    return candidate


def validate_markdown(path: Path, repo_root: Path, reflection_ids: set[str], report: Report) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.error(f"Cannot read lesson {path}: {exc}")
        return

    if not re.search(r"^#\s+\S", text, re.MULTILINE):
        report.warn(f"{path}: lesson has no H1 title")

    resources = [m.group(1).strip().split(maxsplit=1)[0].strip("<>\"") for m in MARKDOWN_RESOURCE_RE.finditer(text)]
    resources.extend(m.group(1).strip() for m in HTML_SOURCE_RE.finditer(text))
    for raw in resources:
        candidate = safe_local_path(path.parent, raw, repo_root, str(path), report)
        if candidate is not None and not candidate.exists():
            report.error(f"{path}: referenced local file does not exist: {raw}")

    for widget in WIDGET_RE.findall(text):
        widget_path = repo_root / "widgets" / f"{widget}.html"
        if not widget_path.is_file():
            report.error(f"{path}: widget not found: {widget_path}")
        else:
            validate_widget_html(widget_path, report)

    for match in WIDGET_BLOCK_RE.finditer(text):
        validate_widget_props(path, match.group(1).strip(), parse_directive_props(match.group(2)), report)

    for reflection_id in REFLECTION_ID_RE.findall(text):
        if reflection_id in reflection_ids:
            report.error(f"Duplicate reflection data-id {reflection_id!r}: {path}")
        reflection_ids.add(reflection_id)


def validate_widget_props(path: Path, widget: str, props: dict[str, Any], report: Report) -> None:
    where = f"{path}: widget {widget!r}"
    for key in ("title", "description"):
        if not isinstance(props.get(key), str):
            report.warn(f"{where}: missing {key}: prop (the phone activity card shows it)")
    if "fullscreen" in props:
        value = props["fullscreen"]
        if isinstance(value, bool):
            report.warn(f"{where}: fullscreen: {str(value).lower()} works, but write "
                        f"{'phone' if value else 'off'} instead")
        elif value.lower() not in FULLSCREEN_VALUES:
            report.error(f"{where}: invalid fullscreen: {value!r} (use phone, always or off)")


def validate_widget_html(path: Path, report: Report) -> None:
    if path in report.checked_widgets:
        return
    report.checked_widgets.add(path)
    try:
        html = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.warn(f"Cannot read widget {path}: {exc}")
        return
    # Plain substring checks: good enough for warnings, but a comment naming a message also passes.
    if "widget-ready" not in html:
        report.warn(f"{path}: no widget-ready message (the player keeps Start disabled until it arrives)")
    if "widget-focus-optout" in html:
        return
    if "widget-mode" not in html:
        report.warn(f"{path}: no widget-mode handling ({FOCUS_HINT})")
    if "widget-focus-exit" not in html:
        report.warn(f"{path}: no Done button posting widget-focus-exit ({FOCUS_HINT})")


def validate_answers(question: dict[str, Any], where: str, report: Report) -> None:
    question_type = question.get("type")
    answers = question.get("answers")
    if not isinstance(answers, list) or len(answers) < 2:
        report.error(f"{where}: answers must contain at least two objects")
        return

    answer_ids: set[str] = set()
    correct_count = 0
    for index, answer in enumerate(answers, start=1):
        answer_where = f"{where} answer {index}"
        if not isinstance(answer, dict):
            report.error(f"{answer_where}: answer must be an object")
            continue
        answer_id = require_string(answer, "id", answer_where, report)
        require_string(answer, "text", answer_where, report)
        if answer_id:
            if answer_id in answer_ids:
                report.error(f"{where}: duplicate answer id {answer_id!r}")
            answer_ids.add(answer_id)
        if not isinstance(answer.get("correct"), bool):
            report.error(f"{answer_where}: correct must be boolean (use correct, not isCorrect)")
        elif answer["correct"]:
            correct_count += 1
        if "isCorrect" in answer:
            report.error(f"{answer_where}: unsupported isCorrect field; use correct")
        if question_type == "MATCHING" and not isinstance(answer.get("matchText"), str):
            report.error(f"{answer_where}: MATCHING answers require matchText")

    if question_type in {"MULTIPLE_CHOICE", "TRUE_FALSE"} and correct_count != 1:
        report.error(f"{where}: {question_type} requires exactly one correct answer, found {correct_count}")
    if question_type == "MULTIPLE_RESPONSE" and correct_count < 1:
        report.error(f"{where}: MULTIPLE_RESPONSE requires at least one correct answer")
    if question_type == "MATCHING" and correct_count != len(answers):
        report.warn(f"{where}: current MyCourse matching examples mark every valid pair correct")


def validate_quiz(path: Path, report: Report) -> None:
    quiz = load_json(path, report)
    if quiz is None:
        return
    report.stats["quizzes"] += 1
    require_string(quiz, "title", str(path), report)
    if quiz.get("type") != "quiz":
        report.error(f"{path}: top-level type must be 'quiz'")
    score = quiz.get("passingScore")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 100:
        report.error(f"{path}: passingScore must be a number from 0 to 100")

    questions = quiz.get("questions")
    if not isinstance(questions, list) or not questions:
        report.error(f"{path}: questions must be a non-empty array")
        return

    question_ids: set[str] = set()
    question_numbers: set[int] = set()
    for index, question in enumerate(questions, start=1):
        where = f"{path} question {index}"
        if not isinstance(question, dict):
            report.error(f"{where}: question must be an object")
            continue
        report.stats["questions"] += 1
        question_id = require_string(question, "id", where, report)
        require_string(question, "question", where, report)
        require_string(question, "feedback", where, report)
        if question_id:
            if question_id in question_ids:
                report.error(f"{path}: duplicate question id {question_id!r}")
            question_ids.add(question_id)
        number = question.get("questionNumber")
        if isinstance(number, int):
            if number in question_numbers:
                report.warn(f"{path}: duplicate questionNumber {number}")
            question_numbers.add(number)
        else:
            report.warn(f"{where}: questionNumber is missing or not an integer")
        question_type = question.get("type")
        if question_type not in ALLOWED_QUESTION_TYPES:
            report.error(f"{where}: unsupported type {question_type!r}")
        validate_answers(question, where, report)


def validate_course(course_file: Path, repo_root: Path, report: Report) -> None:
    course = load_json(course_file, report)
    if course is None:
        return
    course_id = require_string(course, "id", str(course_file), report)
    require_string(course, "title", str(course_file), report)
    require_string(course, "description", str(course_file), report)
    require_string(course, "estimatedDuration", str(course_file), report)
    check_id(course_id, str(course_file), report)
    if course_id and course_file.parent.name != course_id:
        report.warn(f"{course_file}: id {course_id!r} does not match directory {course_file.parent.name!r}")

    welcome = require_string(course, "welcomePath", str(course_file), report)
    if welcome:
        welcome_path = safe_local_path(course_file.parent, welcome, repo_root, str(course_file), report)
        if welcome_path is not None and not welcome_path.is_file():
            report.error(f"{course_file}: welcomePath does not exist: {welcome}")

    modules = course.get("modules")
    if not isinstance(modules, list) or not modules:
        report.error(f"{course_file}: modules must be a non-empty array")
        return
    if len(modules) != len(set(m for m in modules if isinstance(m, str))):
        report.error(f"{course_file}: module IDs must be unique")

    lesson_ids: set[tuple[str, str]] = set()
    reflection_ids: set[str] = set()
    for module_index, module_id in enumerate(modules, start=1):
        if not isinstance(module_id, str) or not module_id:
            report.error(f"{course_file}: module entry {module_index} must be a non-empty string")
            continue
        check_id(module_id, f"{course_file} module entry", report)
        module_dir = repo_root / "modules" / module_id
        manifest_path = module_dir / "manifest.json"
        manifest = load_json(manifest_path, report)
        if manifest is None:
            continue
        report.stats["modules"] += 1
        if manifest.get("id") != module_id:
            report.error(f"{manifest_path}: id must match course module ID {module_id!r}")
        require_string(manifest, "title", str(manifest_path), report)
        require_string(manifest, "description", str(manifest_path), report)
        lessons = manifest.get("lessons")
        if not isinstance(lessons, list) or not lessons:
            report.error(f"{manifest_path}: lessons must be a non-empty array")
            continue

        for lesson_index, lesson in enumerate(lessons, start=1):
            where = f"{manifest_path} lesson {lesson_index}"
            if not isinstance(lesson, dict):
                report.error(f"{where}: lesson must be an object")
                continue
            lesson_id = require_string(lesson, "id", where, report)
            require_string(lesson, "title", where, report)
            if lesson_id:
                key = (module_id, lesson_id)
                if key in lesson_ids:
                    report.error(f"{manifest_path}: duplicate lesson id {lesson_id!r}")
                lesson_ids.add(key)
                check_id(lesson_id, where, report)

            lesson_type = lesson.get("type")
            if lesson_type == "content":
                report.stats["contentLessons"] += 1
                raw_path = require_string(lesson, "markdownPath", where, report)
                if raw_path:
                    lesson_path = safe_local_path(module_dir, raw_path, repo_root, where, report)
                    if lesson_path is not None:
                        if lesson_path.is_file():
                            validate_markdown(lesson_path, repo_root, reflection_ids, report)
                        else:
                            report.error(f"{where}: markdownPath does not exist: {raw_path}")
            elif lesson_type == "quiz":
                raw_path = require_string(lesson, "quizPath", where, report)
                if raw_path:
                    quiz_path = safe_local_path(module_dir, raw_path, repo_root, where, report)
                    if quiz_path is not None:
                        validate_quiz(quiz_path, report)
            else:
                report.error(f"{where}: type must be 'content' or 'quiz'")


def main() -> int:
    args = parse_args()
    report = Report()
    paths = infer_paths(args.target, args.repo_root, report)
    if paths:
        validate_course(paths[0], paths[1], report)

    result = {
        "ok": not report.errors,
        "errors": report.errors,
        "warnings": report.warnings,
        "stats": report.stats,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status}: {report.stats['modules']} modules, {report.stats['contentLessons']} lessons, "
              f"{report.stats['quizzes']} quizzes, {report.stats['questions']} questions")
        for message in report.errors:
            print(f"ERROR: {message}")
        for message in report.warnings:
            print(f"WARNING: {message}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
