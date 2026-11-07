<!-- For a new module, put "Closes #<issue number>" on the next line. -->
Closes #

## What this changes

<!-- One or two sentences. For a module: what a reader ends up with. -->

## Checklist

- [ ] `python3 tools/validate_course.py courses/colab-howtos` passes
- [ ] `check-jsonschema --schemafile schema/howto.schema.json modules/*/howto.json` passes
- [ ] `python3 scripts/check_repo.py` passes
- [ ] `python3 scripts/build_index.py` run, and `INDEX.md` committed
- [ ] New modules are in `courses/colab-howtos/course.json`
- [ ] `status` in `howto.json` is honest (seed, draft or tested), and untested steps are marked
- [ ] `contributors` lists first names or GitHub usernames only
- [ ] No private links, secrets, emails, phone numbers or other people's personal details
- [ ] No video files or video links
