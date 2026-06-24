# Scribe Wait Modal Parity

## Goal

Match the Scribe/Predis inspiration-library transition where clicking `View all` first shows the `Wait! Don't Go...` generation nudge instead of immediately entering the collection view.

## Scope

- Trigger a centered dark-overlay nudge from Inspiration `View all` and overlay `View all` controls.
- Keep `Maybe later` as the workflow-continuation action into the selected collection.
- Make `Download a post` perform a safe LocalPilot action by handing off to Content Library.
- Update the future Phase 3 browser smoke assertions so this modal is covered later.

## Reference

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-06.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-29.jpg`

## Verification

- Run `git diff --check` on touched files.
- Run `PATH=/opt/homebrew/bin:$PATH npm run build`.
- Defer the full Phase 3 browser smoke until the broader UI parity goal is finished.
