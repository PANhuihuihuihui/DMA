# GSD context snapshot (2026-06-26T17:14:46.228Z)

## Top project memories
- [MEM001] (pattern) **S01 OAuth + Publishing Integration Pattern:** Split OAuth callback flow (list pages → UI selection → token persistence) uses URL params (connectSession) to bridge backend session state into React Router location state, avoiding localStorage for sensitive session tokens. Frontend renders conditional UI (Page picker, manual-fallback hints) without knowing the full backend contract — normalizes both `{pages: [...]}` and raw array responses. Pattern proved across 4 tasks and 6 backend integration points.
- [MEM002] (architecture) AiToEarn carousel publishing uses platform-specific flows: Facebook unpublished photos + attached_media[], Instagram container model with creation_status polling (2-10 images, jpg only, max 8MB), TikTok slideshow init with DIRECT_POST (2-35 images, HTTPS only). Video is always async-with-polling on all three platforms. Their PublishProvider interface follows validate→normalize→publish→finalize→verify pipeline. Error taxonomy: Auth, Quota, MediaProcessingFailed, Timeout. Credentials refreshed before execution.

## Recent gsd_exec runs
- [520bb9c2-f7f4-4d9b-9a4c-7c703045db53] bash exit:0 — UAT M002/S01/TC4-doc-check (uat-artifact-check)
- [3f558e15-5e1a-46ce-afee-5981d7b3821f] bash exit:0 — UAT M002/S01/TC2-rg-approval-queue-source (uat-artifact-check)
- [cbb8c4ae-cd31-497c-bb0d-a7704aea8e57] bash exit:0 — UAT M002/S01/TC2-seed-manual-fallback (uat-runtime-check)
- [8f42aa94-803b-45a3-9ca5-137bbc71004b] bash exit:0 — UAT M002/S01/TC2-rg-serialized-job (uat-artifact-check)
- [e7c54d86-5f4b-4dba-af3d-56d9a78b0b04] bash exit:0 — UAT M002/S01/TC2-rg-should-manual (uat-artifact-check)
