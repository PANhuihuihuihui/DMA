---
quick_id: 260623-react-scene-object-render-fix
status: complete
completed: 2026-06-23
---

# Summary

Fixed the Content Library React crash caused by rendering creator-style storyboard scene objects directly.

## Root Cause

`mediaAssetHighlights(asset)` returned raw objects from `metadata.scenes`, such as `{caption, secondRange, shot}`. The media asset renderer used those objects as both React keys and child text.

## Fix

- Added shared `describeDisplayItem` and `displayItemKey` helpers so object-shaped storyboard data is converted before React sees it as text or a key.
- Normalized scene, slide, placement, media-highlight, channel asset, and tracking-event metadata into display strings.
- Made UGC package scene rendering tolerate string and object scene shapes.

## Verification

- `npm run build` passed.
- `python3 -m unittest backend.tests.test_phase3_workspace` passed.
- Targeted Playwright load of `/app?module=content-library` with `{caption, secondRange, shot}` objects seeded into list data passed with no React child/key errors.
- `PHASE3_SCREEN_API_PORT=8898 PHASE3_SCREEN_WEB_PORT=5293 npm run test:phase3-screens` passed.
