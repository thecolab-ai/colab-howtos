# Contributing

Thanks for helping. This repo has two kinds of content:

- **Recaps** in `recaps/`, one per week, written by the maintainers. They summarise what people in The Colab got working.
- **Modules** in `modules/`, one per technique, built by the community. Each module is a short guide someone can follow step by step.

Every technique in a recap becomes an issue labelled `module` and `help wanted`. You pick one, build the module and open a pull request. The site lists open ones under Help wanted: https://thecolab-ai.github.io/colab-howtos/

Using an AI agent to help? Point it at [AGENTS.md](AGENTS.md). It has the same steps written for an agent.

## 1. Pick an issue and claim it

1. Find an [open module issue](https://github.com/thecolab-ai/colab-howtos/issues?q=is%3Aopen+label%3Amodule+label%3A%22help+wanted%22) (labels `module` and `help wanted`).
2. Read the matching section of the recap it links to.
3. Comment "I'll take this" on the issue. A maintainer assigns it to you and adds the `claimed` label, so nobody doubles up. If you go quiet for two weeks, it may be opened up again.

Want to build something that has no issue yet? Use the **Claim a module** issue form, or **Suggest a how-to** if you'd like someone else to build it.

## 2. Build the module

Copy the example and rename it:

```
cp -r modules/example-howto modules/howto-<slug>
```

`<slug>` is short and kebab-case, for example `session-logs-into-a-database`. Use the slug from the issue if it has one. Once a module is published its id never changes.

A module folder holds:

```
modules/howto-<slug>/
  manifest.json   mycourse module manifest: id, title, description, tags, lessons
  howto.json      our metadata, checked against schema/howto.schema.json
  01-steps.md     the guide, starting with "# " plus the exact title
  assets/         images for the guide, if any (assets/.gitkeep if empty)
```

**`01-steps.md`**: no frontmatter. The first line is `# ` plus the title. Use these sections: What it does, What you need, Steps, Gotchas, Notes, Links. Only split into more lesson files (`02-...md`) if the guide splits naturally, and list every lesson file in `manifest.json`.

**`manifest.json`**: `id` is the folder name. `title` and `tags` match `howto.json`. `description` is the first paragraph of What it does.

**`howto.json`**:

| Field | Required | What it means |
|---|---|---|
| `title` | yes | Same as `manifest.json` and the `# ` heading |
| `tags` | yes | Lowercase kebab-case, same as `manifest.json` |
| `difficulty` | yes | `beginner`, `intermediate` or `advanced` |
| `status` | yes | `seed`, `draft` or `tested` (see below) |
| `contributors` | yes | Who built it: first names or GitHub usernames (see below) |
| `recap` | no | The recap week it came from, e.g. `2026-W45` |
| `issue` | no | The issue number it closes, e.g. `12` |
| `example` | no | Only on the example module. Leave it out of yours |

Then add your module id to `modules` in `courses/colab-howtos/course.json`, at the top of the list (newest first).

### Status: seed, draft or tested

- **seed**: an outline from the recap. Nobody has run the steps yet. Fine as a starting point if you want early feedback.
- **draft**: written up and partly worked through. Mark every step you didn't run, for example "(untested)" after the step, and say why in Notes.
- **tested**: you ran every step end to end. Say when, and on what, in Notes (for example "Tested on 8 Nov 2026 on macOS 15 with Node 22").

Be honest about status. A good draft beats a tested label on steps nobody ran.

`status` replaces the old `tested: true/false` field.

### Contributors

`contributors` is a list of one-word names: your first name (`Sam`) or your GitHub username without the @ (`octocat`). No surnames, emails or handles from other sites. Add everyone who did real work on the module.

## 3. Run the checks

From the repo root:

```
python3 tools/validate_course.py courses/colab-howtos
python3 -m pip install check-jsonschema
check-jsonschema --schemafile schema/howto.schema.json modules/*/howto.json
python3 scripts/check_repo.py
python3 scripts/build_index.py
```

- `tools/validate_course.py` checks the course and its modules: ids, manifests, lesson files and the local files they link to.
- `scripts/check_repo.py` checks frontmatter, unlisted lessons, `howto.json` against its manifest, that your module is in the course, video files and links, Git LFS, and privacy (phone numbers, emails, private chat and document links).
- `scripts/build_index.py` regenerates `INDEX.md`. Commit the result.

To preview the site locally:

```
python3 scripts/build_site.py --out /tmp/colab-howtos-site
python3 -m http.server 8000 --bind 127.0.0.1 --directory /tmp/colab-howtos-site
```

Then open http://127.0.0.1:8000/.

## 4. Open a pull request

Push your branch to your fork and open a pull request. Put `Closes #<issue number>` in the description so the issue closes when it's merged. With the GitHub CLI:

```
gh pr create --title "Module: <title>" --body "Closes #<issue number>"
```

The Validate workflow runs the same checks. A maintainer reviews and merges.

## Privacy rules

This repo is public. In anything you add:

- No private links: no links to private chats, shared AI conversations (claude.ai, ChatGPT share links), Google Docs or Drive, or internal tools.
- No secrets: no keys, tokens or passwords, even expired ones. Use placeholders like `YOUR_API_KEY`.
- No other people's personal details: no surnames, emails, phone numbers or employers. First names only, and only for people who are happy to be named.
- No videos: no video files and no video links.

If something here is about you and you'd like it removed or corrected, open an issue.

## Fixing things

Fixes are just as useful as new modules. If a step is wrong or out of date, open a pull request or an issue.
