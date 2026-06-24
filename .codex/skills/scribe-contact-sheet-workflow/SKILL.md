---
name: scribe-contact-sheet-workflow
description: Capture Scribe walkthrough URLs into local step screenshots/contact sheets, map the visible workflow, and use that reference to rebuild LocalPilot creator-style UI/functionality. Use when a user gives a Scribe link, asks for screenshots from a workflow, wants a contact sheet, or asks to make LocalPilot/Predis-style creator workflow UI behave like a reference walkthrough.
---

# Scribe Contact Sheet Workflow

## Core Workflow

1. Start the work through the active repo workflow before editing app files.
2. Fetch the Scribe page HTML with `curl -L -sS -o /tmp/<slug>.html <url>`.
3. Run `scripts/extract_scribe_contact_sheet.mjs` to extract unique steps, download step images, and build `steps.md`, `steps.json`, and `contact-sheet.html`.
4. Render `contact-sheet.html` to `contact-sheet.png` with Playwright when visual comparison is needed.
5. Inspect the contact sheet and key step images before editing UI.
6. Map reference steps into LocalPilot product states, preserving legal/product boundaries.
7. Implement the closest equivalent workflow in the app.
8. Capture current LocalPilot screenshots for side-by-side evidence.
9. Verify with build, backend tests, and browser smoke tests.

## Commands

Use this script from the repo root:

```bash
node .codex/skills/scribe-contact-sheet-workflow/scripts/extract_scribe_contact_sheet.mjs \
  --html /tmp/localpilot-scribe-workflow.html \
  --out .planning/quick/<task>/reference
```

Or download directly from a URL:

```bash
node .codex/skills/scribe-contact-sheet-workflow/scripts/extract_scribe_contact_sheet.mjs \
  --url "https://scribehow.com/..." \
  --out .planning/quick/<task>/reference
```

Use `--skip-images` for a parsing smoke test that does not download remote images.

## LocalPilot Creator Workflow Mapping

When the reference is a Predis/Scribe creator workflow, read `references/localpilot-creator-workflow.md`.

Default target flow:

1. Create New.
2. Choose UGC / creator-style video.
3. Prompt step with `Generate ideas for me`.
4. Idea selection.
5. Script style with `Motivational` available and aspect ratio controls.
6. AI actor/avatar selection grid.
7. Scene/template or subtitle-style selection grid.
8. Review and confirm.
9. Generate backend creative, media asset, UGC package, and calendar slot.
10. Publish / Schedule Post handoff.

## Product Boundaries

- Use screenshots as structural reference, not as copied product assets.
- Do not copy proprietary Predis actor photos, media, logos, or watermarked images into LocalPilot.
- Keep LocalPilot branding and compliance language intact.
- If no real video renderer is integrated, label output as deterministic storyboard/package output, not a fully rendered video.
- Preserve owner approval and official account gating before publish.

## Verification Checklist

- `npm run build`
- Backend tests relevant to the workflow, usually `python3 -m unittest backend.tests.test_phase3_workspace`
- Browser smoke for the affected UI, usually `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
- Screenshot evidence in the quick-task folder:
  - reference contact sheet
  - key reference steps
  - current LocalPilot screens
