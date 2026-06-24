---
quick_id: 260623-scribe-contact-sheet-workflow-skill
status: complete
completed: 2026-06-23
---

# Summary

Created a project-local skill for future Scribe-to-contact-sheet and LocalPilot creator workflow parity work.

## Skill

- `.codex/skills/scribe-contact-sheet-workflow/SKILL.md`
- `.codex/skills/scribe-contact-sheet-workflow/scripts/extract_scribe_contact_sheet.mjs`
- `.codex/skills/scribe-contact-sheet-workflow/references/localpilot-creator-workflow.md`
- `.codex/skills/scribe-contact-sheet-workflow/agents/openai.yaml`

## Validation

- `node .codex/skills/scribe-contact-sheet-workflow/scripts/extract_scribe_contact_sheet.mjs --html /tmp/localpilot-scribe-workflow.html --out /tmp/scribe-contact-sheet-skill-test --skip-images` passed and parsed 56 unique steps.
- `node --check .codex/skills/scribe-contact-sheet-workflow/scripts/extract_scribe_contact_sheet.mjs` passed.
- Manual frontmatter and metadata validation passed.
- `quick_validate.py` could not run because this Python environment lacks `PyYAML`.

## Notes

The skill is project-local so future LocalPilot sessions can use it from this repo without copying global personal configuration.
