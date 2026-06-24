# 04-05 Summary — Capability/Permission Health Gate

**One-liner:** Added `page_health()` + `active_page_health()` deriving connected/missing_permission/reconnect_required states, with a pre-publish 409 gate and 190→reconnect marking.

## What Was Built
- `backend/app/facebook_oauth.py` — `page_health(page_row)` + `active_page_health(conn)` deriving three states from tasks + token status. Falls back to in-memory vault for dev mode.
- `backend/app/facebook_publisher.py` — pre-publish capability gate in `queue_facebook_publish` (409 when not publishable); auth failures mark `reconnect_required`.

## Self-Check: PASSED — 30/30 tests green.
