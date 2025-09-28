# Unit Podcast Generation & Playback

## Requirements Summary

### What to Build
Extend unit creation so every completed unit automatically receives a narrated podcast. The backend must generate a Dan Carlin–style transcript, synthesize audio with OpenAI voice models, persist both, and expose a streaming endpoint. Mobile learners should see a "Unit Podcast" card on the detail screen with play/pause controls and the transcript.

### Key Constraints
- Podcast generation cannot block unit creation failure handling; log and continue if synthesis fails.
- Store binary audio safely (DB column is acceptable) and expose via authenticated API route.
- Reuse the requested lesson voice for transcript tone while using OpenAI TTS voices for audio playback.
- Mobile playback relies on Expo AV and must handle buffering, pause/resume, and clean unload on navigation.

### Acceptance Criteria
- [x] New units persist transcript + audio metadata and expose `has_podcast`, `podcast_voice`, duration, and transcript text in unit summaries/details.
- [x] `/api/v1/content/units/{id}/podcast/audio` streams audio bytes for completed units.
- [x] Catalog responses (admin/mobile) surface podcast metadata.
- [x] Mobile `UnitDetailScreen` renders podcast card with play/pause, duration, and transcript preview; audio plays via Expo AV.
- [x] Specs/tests updated to cover podcast metadata and audio retrieval.

## Cross-Stack Implementation Mapping

### Backend Changes

#### content module
- **models.py** – Add podcast columns (transcript, voice, audio blob, MIME type, duration, timestamp).
- **service.py** – Track `has_podcast`, expose `set_unit_podcast`, `get_unit_podcast_audio`, include podcast metadata in `UnitRead` / `UnitDetailRead`, and compute audio URL.
- **repo.py** – Persist podcast fields via new `set_unit_podcast` helper.
- **routes.py** – Add `/podcast/audio` streaming endpoint.
- **public.py** – Extend provider protocol & exports with `UnitPodcastAudio` helpers.

#### content_creator module
- **prompts/** – Add `generate_unit_podcast_transcript.md` prompt for Dan Carlin–style script.
- **steps.py** – Register `GenerateUnitPodcastTranscriptStep` with typed lesson input.
- **podcast.py** – New helper using transcript step + OpenAI speech API to yield `UnitPodcast` payloads.
- **service.py** – Inject podcast generator, summarize unit plan, call generator post lesson creation, and persist metadata via content service. Guard failures with warnings.
- **tests** – Mock generator/audio persistence to assert behavior without real OpenAI calls.

#### catalog module
- **service.py** – Surface podcast metadata in `UnitSummary` / `UnitDetail` DTOs and map through detail fetches.
- **tests** – Update expectations for new fields.

### Admin Frontend
- **models.ts** – Add podcast fields to API/DTO types.
- **service.ts** – Pass through `has_podcast`, voice, duration, transcript URL when mapping units and details.

### Mobile Frontend
- **modules/content/models.ts** – Extend DTO + domain types with podcast metadata and mapping helpers.
- **modules/catalog/screens/UnitDetailScreen.tsx** – Add Expo AV playback (play/pause button, ActivityIndicator, duration formatting, transcript text) and ensure cleanup on navigation.
- **__mocks__/expo-av.js** & **jest.config.js** – Provide jest mock for Expo AV.
- **catalog tests** – Update fixtures for new fields.

### Database
- **Alembic migration** – Add podcast columns to `units` table (transcript, voice, audio blob, MIME type, duration, generated_at).

## Implementation Checklist

### Backend
- [x] Migration adds podcast columns.
- [x] Content service/repo persist and expose podcast metadata & streaming route.
- [x] Content creator generates transcript/audio with graceful failure handling.
- [x] Catalog service & DTOs expose podcast fields across APIs.
- [x] Unit tests cover podcast persistence and audio retrieval.

### Frontend
- [x] Admin models/services accept podcast metadata.
- [x] Mobile content models + mapping include podcast fields.
- [x] `UnitDetailScreen` renders podcast card with playback, duration, transcript.
- [x] Expo AV jest mock added for unit tests.
- [x] Catalog service tests updated for new field requirements.

### Documentation & Observability
- [x] Spec (this file) outlining feature scope & mapping.
- [x] Logging around podcast synthesis failures (warning-level) for observability.
