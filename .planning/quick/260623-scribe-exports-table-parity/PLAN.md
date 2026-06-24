# Scribe Exports Table Parity

## Goal

Move the Brand & Social Accounts `Exports` tab closer to Scribe step 56 by replacing the generic export package cards with the visible Predis-style exports table.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-56.jpg`
- Visible structure: `Exports` heading, subtitle `View, download, and reuse all the posts you've created.`, table columns `Description`, `Dimension`, `Status`, two generated post rows, and a right-aligned download action.

## Scope

- Add local export row data using existing LocalPilot assets instead of copying Predis imagery.
- Render a rounded white table with description thumbnail, dimension, status, and download action columns.
- Keep download buttons demo-safe by using the existing local export package action.
- Update Phase 3 browser smoke assertions from the old card copy to the table copy.

## Verification

- `python3 -m unittest backend.tests.test_phase3_workspace`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens`
