# Scribe Brand Details Inner Menu Parity

## Goal

Move `Brand & Social Accounts > Brand Details` closer to Scribe steps 53-54 by removing the separate top-level `Style` tab and rendering the Brand Details inner menu shown in the reference.

## Reference Evidence

- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-53.jpg`
- `.planning/quick/260623-scribe-screenshot-exact-parity/reference/steps/step-54.jpg`

## Visible Reference Structure

- Top tabs: `Social Platforms`, `Brand Details`, `Integrations`, `Exports`.
- Inner left menu: `Business identity`, `Style`, `Content settings`.
- Content settings panel shows:
  - `Content settings`
  - `Tonality of Communication` select
  - `Select Timezone` with `(GMT -4:00) America/Detroit`
  - `Brand Ethnicity` select
  - `Brand Voiceover` select and helper text
  - `AI Media`
  - `Brand Avatar` select and helper text
  - disabled-looking `Save Changes` action

## Scope

- Convert Style from top-level tab into an inner Brand Details section.
- Add working inner Brand Details section buttons.
- Preserve LocalPilot-safe demo data and owner-approval boundaries.
- Update future full-smoke assertions, but do not run full Phase 3 browser smoke until final parity.

## Verification

- `git diff --check`
- `PATH=/opt/homebrew/bin:$PATH npm run build`
