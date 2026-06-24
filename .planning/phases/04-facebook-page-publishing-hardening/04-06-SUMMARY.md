# 04-06 Summary — Link + Image Publishing, Media Validation, v25.0

**One-liner:** Extended the publisher for link and single-image Facebook posts with pre-job media validation and unified Graph API to v25.0.

## What Was Built
- `backend/app/facebook_publisher.py` — `GRAPH_API_BASE` → v25.0 (was v20.0). `validate_facebook_media()` with SSRF guards, type/size/reachability checks, actionable error messages. `publish_approved_snapshot` branches: text→`/feed`, link→`/feed+link`, image→`/photos?url=`.

## Self-Check: PASSED — 30/30 tests green.
