# S01: Dispatch Engine and Provider Adapters — UAT

**Milestone:** M001
**Written:** 2026-06-26T00:34:28.900Z

# S01 UAT: Dispatch Engine and Provider Adapters

## Checks

### Server starts without ImportError
- **Command:** `python3 -c 'from backend.app.server import create_app; print("ok")'`
- **Expected:** prints `ok`
- **Result:** PASS

### Adapter registry covers both providers
- **Command:** `python3 -c 'from backend.app.generation_providers import get_adapter; print(type(get_adapter("openai:video")).__name__, type(get_adapter("heygen:avatar_video")).__name__)'`
- **Expected:** `OpenAIVideoAdapter HeyGenAvatarAdapter`
- **Result:** PASS

### HeyGen model has readiness=ready in catalog seed
- **Verified via:** `test_generation_dispatch.py::JobLifecycleTest::test_heygen_model_is_ready`
- **Result:** PASS

### Contract tests pass
- **Command:** `python3 -m pytest backend/tests/test_generation_dispatch.py -q`
- **Expected:** 15 passed
- **Result:** PASS

### Full backend test suite unbroken
- **Command:** `python3 -m pytest backend/tests/ -q`
- **Expected:** 168 passed
- **Result:** PASS

