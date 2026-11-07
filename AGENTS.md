# AGENTS.md

Instructions for AI coding agents (Claude Code, Codex, Cursor and others) working in this repo. Follow them exactly.

## What this repo is

- `recaps/<YYYY>-W<NN>.md`: weekly recaps of techniques people in The Colab shared. Written by maintainers. Do not edit them.
- `modules/howto-<slug>/`: one how-to module per technique, built by community contributors in the mycourse module format.
- `modules/example-howto/`: the format example. Copy it; never edit or delete it.
- `courses/colab-howtos/course.json`: the one course. Every module must be listed in it.
- `INDEX.md`: generated list of recaps and modules. Regenerate it, never edit it by hand.
- `tools/validate_course.py`: vendored validator. Never edit it.

## If your user wants to follow a module

1. Read `INDEX.md` to find the module, then its `howto.json`.
2. Check `status`. `tested` means a contributor ran every step. `draft` means some steps are marked untested. `seed` means nobody has run the steps. For `draft` and `seed`, check each step against the linked official docs before you run it.
3. Read **Gotchas** first, then follow **Steps** in order.
4. Ask the user before running anything that needs credentials, costs money or changes their system. Never write keys or tokens into this repo.

## If your user wants to build a module

Do these steps in order.

### 1. Read the issue and the recap

1. Read the issue: `gh issue view <N> --repo thecolab-ai/colab-howtos`. It is labelled `module` and `help wanted`.
2. Make sure your user has claimed it (commented on it, or it's assigned to them). If not, tell them to comment "I'll take this" first.
3. Open the recap the issue points to in `recaps/` and read the matching section. Note the slug from the issue; the module folder is `modules/howto-<slug>/`.

### 2. Research and test

1. Read the official docs and repos for every tool involved. Prefer primary sources.
2. Work through the technique on your user's machine, with their permission, step by step. Record exact commands, versions and output that matters.
3. Keep track of which steps you ran and which you didn't. Any step you didn't run is untested, and must be marked so in the module.

### 3. Write the module files

```
cp -r modules/example-howto modules/howto-<slug>
```

Then edit the copied files.

`modules/howto-<slug>/manifest.json`:

```json
{
  "id": "howto-session-logs-into-a-database",
  "title": "Ship your coding agent session logs into a database",
  "description": "Collect Claude Code and Codex session logs into SQLite so you and your agents can search past runs.",
  "tags": ["claude-code", "codex", "sqlite", "observability"],
  "lessons": [
    {
      "id": "steps",
      "title": "Ship your coding agent session logs into a database",
      "type": "content",
      "markdownPath": "01-steps.md"
    }
  ]
}
```

`modules/howto-<slug>/howto.json`:

```json
{
  "$schema": "../../schema/howto.schema.json",
  "title": "Ship your coding agent session logs into a database",
  "tags": ["claude-code", "codex", "sqlite", "observability"],
  "difficulty": "intermediate",
  "status": "draft",
  "contributors": ["Sam", "octocat"],
  "recap": "2026-W45",
  "issue": 12
}
```

Rules for these files:

- `id` equals the folder name. `title` and `tags` are identical in both files.
- `tags` are lowercase kebab-case.
- `difficulty` is `beginner`, `intermediate` or `advanced`.
- `status` is `seed` (outline, nothing run), `draft` (partly run, untested steps marked) or `tested` (every step run). Pick the honest one.
- `contributors` holds one-word entries: first names or GitHub usernames without the @. Ask your user what to put. Never add surnames or emails.
- `recap` is the recap week, and `recaps/<recap>.md` must exist. `issue` is the issue number as an integer.
- Do not add `"example": true`. Remove it from the copied file.

`modules/howto-<slug>/01-steps.md`:

- The first line is `# ` plus the exact title. No frontmatter.
- Sections, in order: `## What it does`, `## What you need`, `## Steps`, `## Gotchas`, `## Notes`, `## Links`.
- The first paragraph of What it does is the `description` in `manifest.json`.
- Steps are numbered and each one is a single action with the exact command.
- After any step you did not run, add `(untested)`. In Notes, say what you tested, when, and on what (OS, versions).
- Links are public: official docs, public repos.
- Images go in `assets/` and are linked with relative paths. No video files or video links.

Keep `assets/.gitkeep` if there are no images.

Then add the module id to the top of `modules` in `courses/colab-howtos/course.json`.

### 4. Run the checks

From the repo root, run all of these and fix every error before you continue:

```
python3 tools/validate_course.py courses/colab-howtos
python3 scripts/check_repo.py
python3 scripts/build_index.py
```

If `check-jsonschema` is available, also run:

```
check-jsonschema --schemafile schema/howto.schema.json modules/*/howto.json
```

`build_index.py` rewrites `INDEX.md`; commit it with the module.

### 5. Open the pull request

Commit on a branch, push to your user's fork, then:

```
gh pr create --repo thecolab-ai/colab-howtos \
  --title "Module: <title>" \
  --body "Closes #<N>

<one or two sentences on what the module covers and what was tested>"
```

Fill in the checklist from `.github/pull_request_template.md` in the body. Only tick items you checked.

## Privacy rules

This repo is public. These apply to every file you write:

- No private links: no shared AI conversations (claude.ai, ChatGPT share links), Google Docs or Drive, private chats or internal tools.
- No secrets: no keys, tokens or passwords. Use placeholders like `YOUR_API_KEY`.
- No other people's personal details: no surnames, emails, phone numbers or employers. First names only, and only for people who agreed to be named.
- No content copied from private community chats. Write it in your own words.
- Mark untested steps. Never claim a step works if you didn't run it.

`scripts/check_repo.py` catches some of this (emails, phone numbers, private links, videos), not all of it. Check by reading.

## Don't

- Don't edit `recaps/`, `tools/validate_course.py`, `modules/example-howto/` or `INDEX.md` by hand.
- Don't rename a module after it's merged; its id is permanent.
- Don't run the Publish or Pages workflows. They're for maintainers.
