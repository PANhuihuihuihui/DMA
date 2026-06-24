---
quick_id: 260623-scribe-contact-sheet-workflow-skill
status: in_progress
created: 2026-06-23
description: Create reusable Scribe contact sheet workflow skill
---

# Create Reusable Scribe Contact Sheet Workflow Skill

## Goal

Package the Scribe screenshot extraction, contact sheet generation, and LocalPilot creator workflow parity process as a reusable project skill.

## Scope

- Create a project-local Codex skill.
- Include a reusable script for Scribe step extraction and contact sheet generation.
- Include LocalPilot creator workflow mapping notes.
- Validate the script and skill metadata.

## Verification

- Run extractor against the downloaded Scribe HTML with `--skip-images`.
- Run JavaScript syntax check.
- Run skill validation or a documented fallback if the validator dependency is unavailable.
