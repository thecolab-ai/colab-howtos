# Colab How-Tos

Practical how-tos from [The Colab](https://thecolab.ai), a community of people in Aotearoa New Zealand building with AI.

Every week people in the community share how they got something working: a skill setup, a tool, a workflow, a fix. We write those up in a weekly recap. The community then turns each technique into a how-to module that anyone, or any agent, can follow step by step.

**Read it on the site: https://thecolab-ai.github.io/colab-howtos/**

## How it works

1. **Recaps.** Each week the maintainers write a deep-dive recap in `recaps/<year>-W<week>.md`, for example `recaps/2026-W45.md`. It covers what people shared, credits them by first name, and links each technique to an issue.
2. **Issues.** Every technique becomes a GitHub issue labelled `module` and `help wanted`. The site lists the open ones under Help wanted.
3. **Modules.** A community member claims an issue, works through the technique, tests it, and opens a pull request with a module in `modules/howto-<slug>/`. Each module says how far it was tested: `seed`, `draft` or `tested`.

We don't write the modules ourselves. The only one we wrote is `modules/example-howto/`, a tiny example of the format. It's hidden on the site and never published.

## What's in here

```
recaps/<year>-W<nn>.md            weekly recaps, plain markdown
modules/howto-<slug>/             one module per technique, built by contributors
  manifest.json                   mycourse module manifest (id, title, description, tags, lessons)
  howto.json                      status, contributors, recap and issue (schema/howto.schema.json)
  01-steps.md                     the guide, starting with "# Title"
  assets/                         images, if any
modules/example-howto/            the format example (hidden, never published)
courses/colab-howtos/             the one course: course.json lists every module
site/                             the viewer: index.html, app.js, md.js, styles.css, no build step
schema/howto.schema.json          JSON Schema for howto.json
tools/validate_course.py          the mycourse course validator, vendored from mycourse-work/skills (see Licence)
scripts/check_repo.py             frontmatter, module, course, privacy, video and issue-link checks
scripts/build_index.py            builds INDEX.md from the recaps and modules
scripts/build_site.py             assembles the site into _site/ with data/content.json
.github/workflows/                validate, pages, publish (optional) and upstream-drift
INDEX.md                          recaps and modules with their status (generated)
CONTRIBUTING.md                   how to claim an issue and build a module
AGENTS.md                         the same, written for AI coding agents
```

## Fork it and point your agent at it

Fork the repo, or clone it:

```
git clone https://github.com/thecolab-ai/colab-howtos.git
```

Then point your agent at it. For example: "read colab-howtos/AGENTS.md, then pick an open module issue and help me build it", or "follow the session logs module with me". [AGENTS.md](AGENTS.md) tells the agent how to read a module's status, follow its steps, and build and check a new one.

## Contributing

Pick an open issue labelled `module` and `help wanted`, comment to claim it, build the module and open a pull request. [CONTRIBUTING.md](CONTRIBUTING.md) has the full steps, the file format and the checks. Fixes to existing modules are just as welcome.

Before you open a pull request, run:

```
python3 tools/validate_course.py courses/colab-howtos
python3 scripts/check_repo.py
python3 scripts/build_index.py
```

The Validate workflow runs these on every pull request, plus `check-jsonschema` on every `howto.json`. In CI it also fails if a recap still has an `ISSUE(...)` placeholder (set `REQUIRE_ISSUE_LINKS=1` to check that locally).

## The site

`site/` is a static viewer with no build step: plain JavaScript, one stylesheet and a small markdown renderer. `scripts/build_site.py` copies it, the recaps, the course and the modules into `_site/`, and writes `data/content.json` for the viewer to read. The Pages workflow runs it on every push to main and every 6 hours, after fetching the open module issues for the Help wanted list, then deploys to GitHub Pages.

To preview locally:

```
python3 scripts/build_site.py --out /tmp/colab-howtos-site
python3 -m http.server 8000 --bind 127.0.0.1 --directory /tmp/colab-howtos-site
```

## Publishing to mycourse (optional)

The modules use the mycourse module and course format, so they can also be published as a course on the Colab mycourse site. This is optional and for maintainers only: run **Actions > Publish to mycourse > Run workflow**. It:

1. does nothing if there are no community modules yet;
2. runs the checks;
3. copies the community modules (not the example) and `courses/colab-howtos` into `mycourse-work/thecolab` on a new branch, with the example taken out of the course;
4. opens a pull request there.

It never pushes to main. Merging that pull request is the publish step. Modules removed here are listed in the pull request but not deleted there, because learner progress points at module ids.

Secrets (repository secrets in this repo):

- `THECOLAB_PUBLISH_TOKEN` (needed only for publishing): a fine-grained token limited to `mycourse-work/thecolab`, with Contents and Pull requests set to read and write.
- `MYCOURSE_READ_TOKEN` (optional): read access to the private upstream validator repo, for the nightly drift check. Without it the check is skipped with a notice.

## Credits and consent

Recaps credit people by first name only. Modules credit their contributors by first name or GitHub username.

If you're mentioned anywhere here and want to be removed or corrected, [open an issue](https://github.com/thecolab-ai/colab-howtos/issues/new) and we'll fix it. The same goes for anything that shouldn't be public.

## Licence

- Text (recaps, modules and docs): [CC BY 4.0](LICENSE-CONTENT). Share and adapt it, with credit to The Colab community.
- Code written for this repo (scripts, the site and workflows): [MIT](LICENSE).
- Commands and snippets quoted from third-party docs or repos stay under their owners' terms; see the linked source.
- `tools/validate_course.py` is vendored from the public [mycourse-work/skills](https://github.com/mycourse-work/skills) repo (commit pinned in its header) and is not covered by this repo's MIT licence.
- The Colab name and logo are not covered by either licence.

Guides describe community experience, not official vendor advice. Check the linked docs and use at your own risk.
