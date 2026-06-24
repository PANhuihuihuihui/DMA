# 04-07 Summary — Failure Action Mapping + Idempotent FB Retry

**One-liner:** Added `recommended_action_for()` mapping error classes to recovery actions, and `retry_facebook_publish()` for idempotent Facebook-aware retries with provider-based server dispatch.

## What Was Built
- `backend/app/facebook_publisher.py` — `recommended_action_for(error_class)` returning reconnect/retry/fix_media_or_copy/manual_fallback. `retry_facebook_publish()` is idempotent (already-published returns without Graph POST), re-validates media, runs through capability gate.
- `backend/app/server.py` — retry route dispatches Facebook jobs to `retry_facebook_publish`, others to `fake_publisher`.

## Self-Check: PASSED — 30/30 tests green.
