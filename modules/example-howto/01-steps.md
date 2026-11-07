# Example: how a how-to module is laid out

## What it does

Shows the files a how-to module needs, using a dummy three-step guide. Copy this folder when you start a new module, then replace the content.

## What you need

- A fork of this repo
- Python 3.10 or later

## Steps

1. **Copy the folder.** Copy `modules/example-howto/` to `modules/howto-<slug>/`, where `<slug>` is the short kebab-case name from your issue.
2. **Edit the files.** In `manifest.json` and `howto.json`, set the id, title and tags. Remove `"example": true` from `howto.json`. Write your guide in `01-steps.md`, starting with `# ` plus the exact title.
3. **Run the checks.** From the repo root, run:

   ```
   python3 tools/validate_course.py courses/colab-howtos
   python3 scripts/check_repo.py
   ```

   Both should finish without errors.

## Gotchas

- No frontmatter: the first line of a lesson file is the `# ` title.
- Every lesson `.md` file must be listed under `lessons` in `manifest.json`.

## Notes

Status `tested`: a maintainer ran these three steps on 8 Nov 2026.

## Links

- [CONTRIBUTING.md](../../CONTRIBUTING.md)
