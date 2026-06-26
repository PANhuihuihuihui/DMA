---
id: T02
parent: S02
milestone: M002
key_files:
  - backend/app/facebook_publisher.py
  - backend/tests/test_media_validation.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-06-26T16:32:13.201Z
blocker_discovered: false
---

# T02: R004 verified: 12 new tests prove validate_facebook_media rejects multi-image, private hosts, bad extensions, oversized files, bad content-types, and passes valid single images

**R004 verified: 12 new tests prove validate_facebook_media rejects multi-image, private hosts, bad extensions, oversized files, bad content-types, and passes valid single images**

## What Happened

Wrote new test_media_validation.py with 12 tests covering validate_facebook_media(): text-only returns text kind, link-only returns link kind, single valid image passes, multiple images rejected (400), FTP scheme filtered as non-image, private host rejected (127.0.0.1, localhost), bad extension rejected (.bmp), oversized image rejected (>10MB), bad content-type rejected (application/pdf), non-image kind ignored, PNG passes, GIF passes. Uses mock opener to avoid network calls. AiToEarn reference: their publish supports JPG/PNG/GIF/BMP/TIFF; our validation is tighter (JPG/PNG/GIF only per D12) and adds URL accessibility + private host checks.

## Verification

python3 -m pytest backend/tests/test_media_validation.py -v — 12 passed

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `python3 -m pytest backend/tests/test_media_validation.py -v` | 0 | pass | 50ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `backend/app/facebook_publisher.py`
- `backend/tests/test_media_validation.py`
