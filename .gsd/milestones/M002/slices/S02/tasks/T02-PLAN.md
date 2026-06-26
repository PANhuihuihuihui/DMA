---
estimated_steps: 1
estimated_files: 1
skills_used: []
---

# T02: R004 verified: 12 new tests prove validate_facebook_media rejects multi-image, private hosts, bad extensions, oversized files, bad content-types, and passes valid single images

Run automated checks against validate_facebook_media() in facebook_publisher.py to prove: (1) valid single-image ref passes, (2) multiple images rejected, (3) invalid URL schemes rejected, (4) private host URLs rejected. AiToEarn reference: their publish supports JPG/PNG/GIF/BMP/TIFF; our validation covers URL accessibility and single-image enforcement per D12.

## Inputs

- `backend/app/facebook_publisher.py`
- `backend/app/store.py`

## Expected Output

- `backend/tests/test_media_validation.py`

## Verification

python -m pytest backend/tests/test_media_validation.py -v exits 0
