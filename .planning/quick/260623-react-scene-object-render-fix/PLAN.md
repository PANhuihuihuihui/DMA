---
quick_id: 260623-react-scene-object-render-fix
status: in_progress
created: 2026-06-23
description: Fix React crash from rendering scene objects in Content Library
---

# React Scene Object Render Fix

## Symptom

Content Library crashes with:

- duplicate child key `[object Object]`
- `Objects are not valid as a React child (found: object with keys {caption, secondRange, shot})`

## Root Cause

`mediaAssetHighlights(asset)` returns raw scene objects for creator-style storyboard assets. The Content Library media asset list renders those objects directly as `<li key={item}>{item}</li>`.

## Fix

- Normalize media asset highlights into strings before rendering.
- Use stable keys based on asset ID plus index/string content.
- Make UGC package scene rendering tolerate object or string scene shapes.

## Verification

- `npm run build`
- `python3 -m unittest backend.tests.test_phase3_workspace`
- Browser smoke or targeted page load check for Content Library
