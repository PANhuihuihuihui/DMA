# Secrets Manifest

**Milestone:** Text-to-Video and UGC Avatar Generation
**Generated:** 

### OPENAI_API_KEY

**Service:** 
**Status:** skipped
**Destination:** dotenv

1. Log in to https://platform.openai.com
2. Navigate to API Keys → Create new secret key
3. Verify your account has access to the video generation endpoint (`POST /v1/video/generations`) — may require Tier 3+ or explicit access grant
4. Copy the key and set `OPENAI_API_KEY=sk-...` in `backend/.env`

### HEYGEN_API_KEY

**Service:** 
**Status:** skipped
**Destination:** dotenv

1. Log in to https://app.heygen.com
2. Navigate to Settings → API → Generate API Token
3. Confirm the account has access to the v2 video generation API (`POST /v2/video/generate`) and avatar listing endpoint (`GET /v2/avatars`)
4. Copy the key and set `HEYGEN_API_KEY=<key>` in `backend/.env`
