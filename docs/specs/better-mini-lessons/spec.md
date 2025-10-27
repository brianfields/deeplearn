# Better Mini-Lessons: Podcast Structure Enhancement

## User Story

**As a learner**, I want each lesson to have its own podcast that covers the lesson material in an engaging narrative format, so that I can learn through audio while moving through a unit in a structured way.

**As a learner**, I want the unit to start with an intro podcast that hooks me and teases what I'll learn, so that I'm motivated and understand the value of the unit before diving into individual lessons.

**As a learner**, I want to navigate between lesson podcasts (skip forward/back) and have them autoplay in sequence, so that I can listen through an entire unit seamlessly without manual intervention.

**As a learner**, I want the podcast player to always be visible while I'm in a lesson, so that I can control playback, see progress, and navigate between podcasts without losing my place.

**As an admin/content creator**, I want to see all generated podcasts (intro + lesson podcasts) in the admin interface with links to play them, so that I can review the content quality and verify generation succeeded.

### User Experience Changes

**Before (Current State):**
1. User browses catalog and selects a unit
2. User sees unit detail with one unit-level podcast covering all content
3. User starts learning session and goes through lessons sequentially
4. Each lesson shows: mini-lesson text → exercises
5. Podcast player (if present) plays single unit podcast throughout entire session

**After (New State):**
1. User browses catalog and selects a unit
2. User sees unit detail with intro podcast that teases the unit content
3. User starts learning session and hears intro podcast (autoplay on by default)
4. Each lesson shows: lesson podcast + mini-lesson text → exercises
5. Podcast player shows current podcast (intro or lesson N) with:
   - Skip forward/back buttons to navigate between podcasts
   - Progress indicator showing which podcast is playing
   - Autoplay continues: intro → lesson 1 → lesson 2 → ... → lesson N
6. User can control playback, speed, and navigation throughout the session

**Admin Interface Changes:**
- Unit detail view shows:
  - Intro podcast (with link to audio)
  - List of lessons, each with its podcast (with links to audio)
  - All podcasts are read-only (no editing/regeneration for now)

---

## Requirements Summary

### Functional Requirements

1. **Data Model Changes**
   - Add podcast fields to `LessonModel`: transcript, voice, audio_object_id, generated_at, duration_seconds
   - Modify `UnitModel` podcast fields to represent intro podcast only (rename/clarify purpose)
   - Each lesson must have a podcast before unit is marked as "completed"

2. **Content Generation**
   - Generate intro podcast during unit creation (~500 words, teaser/hook style, no intro line)
   - Generate lesson podcast for each lesson during unit creation
   - Lesson podcasts must start with intro line: "Lesson N. [Lesson Title]"
   - Lesson podcasts cover same material as mini-lesson in narrative, engaging fashion
   - All podcasts generated upfront (synchronously during unit creation flow)

3. **Mobile Playback**
   - Podcast player supports playlist of tracks: intro + lesson 1 + lesson 2 + ... + lesson N
   - Skip forward/back buttons navigate between tracks in playlist
   - Autoplay (default: on) continues from intro through all lesson podcasts
   - Current track indicator shows which podcast is playing (e.g., "Intro" or "Lesson 2 of 5")
   - Podcast player always visible during learning session
   - Lesson podcast loads/plays when user reaches that lesson's mini-lesson screen

4. **Offline Support**
   - All lesson podcasts downloaded during unit sync
   - Cached locally for offline playback

5. **Admin Interface**
   - Unit detail page shows intro podcast with audio link
   - Unit detail page shows list of lessons with their podcasts and audio links
   - Read-only view (no editing or regeneration)

### Constraints

- **No backward compatibility**: Database will be wiped; no migration of existing units needed
- **All podcasts required**: Unit cannot be marked "completed" unless intro + all lesson podcasts are generated
- **Generation timing**: All podcasts generated upfront during unit creation (not on-demand)
- **Storage**: Lesson podcasts stored in `LessonModel` (not separate table)

### Acceptance Criteria

- [ ] Lesson model includes podcast fields in database
- [ ] Unit creation flow generates intro podcast + lesson podcasts for all lessons
- [ ] Intro podcast is teaser-style (~500 words, engaging hook)
- [ ] Lesson podcasts include intro line "Lesson N. [Title]"
- [ ] Mobile podcast player shows playlist with skip forward/back buttons
- [ ] Autoplay works: intro → lesson 1 → lesson 2 → ... → lesson N
- [ ] Current track indicator visible in player
- [ ] Lesson podcasts sync and cache for offline playback
- [ ] Admin unit detail page shows intro + all lesson podcasts with links
- [ ] All tests pass (unit, integration)
- [ ] Lint passes

---

## Cross-Stack Module Mapping

### Backend Modules

#### 1. `content` Module (MODIFY)
**Owns**: `LessonModel`, `UnitModel`, content storage

**Changes:**
- `models.py`: Add podcast columns to `LessonModel`
- `service.py`: Update DTOs to include lesson podcast fields
- `repo.py`: Add queries for lesson podcast metadata
- `routes.py`: Add lesson podcast audio route
- `public.py`: Expose lesson podcast methods if needed
- `test_content_unit.py`: Update tests

#### 2. `content_creator` Module (MODIFY)
**Owns**: Content generation flows

**Changes:**
- `flows.py`: Create `LessonPodcastFlow`, modify `UnitPodcastFlow` for intro style, integrate into `LessonCreationFlow`
- `podcast.py`: Create `LessonPodcastGenerator`, modify `UnitPodcastGenerator` for intro style
- `steps.py`: Add `GenerateLessonPodcastTranscriptStep`
- `prompts/`: Add `generate_intro_podcast_transcript.md`, `generate_lesson_podcast_transcript.md`
- `service.py`: Update unit creation to generate intro + lesson podcasts
- `test_flows_unit.py`, `test_service_unit.py`: Update tests

#### 3. `catalog` Module (MODIFY)
**Owns**: Read-only catalog views

**Changes:**
- `service.py`: Update `LessonSummary`, `LessonDetail`, `UnitDetail` DTOs with podcast fields
- `test_lesson_catalog_unit.py`: Update tests

#### 4. `admin` Module (MODIFY)
**Owns**: Admin backend services

**Changes:**
- `models.py`: Update lesson DTOs with podcast fields
- `service.py`: Include podcast URLs in responses
- `routes.py`: Ensure podcast data returned

### Frontend Modules (Mobile)

#### 5. `content` Module (MODIFY)
**Owns**: Content sync and caching

**Changes:**
- `models.ts`: Add podcast fields to `Lesson` type
- `service.ts`: Update sync logic for lesson podcasts
- `repo.ts`: Update API calls and cache storage
- `test_content_service_unit.ts`: Update tests

#### 6. `catalog` Module (MODIFY)
**Owns**: Unit/lesson browsing UI

**Changes:**
- `models.ts`: Add podcast fields to DTOs
- `service.ts`: Map podcast fields from API
- `screens/UnitDetailScreen.tsx`: Show intro podcast
- `components/LessonCard.tsx`: Optional podcast indicator

#### 7. `podcast_player` Module (MODIFY)
**Owns**: Podcast playback

**Changes:**
- `models.ts`: Add `lessonId`, `lessonIndex` to `PodcastTrack`; create `UnitPodcastPlaylist` type
- `service.ts`: Add playlist loading, skip forward/back, autoplay logic
- `store.ts`: Add playlist state and autoplay setting
- `hooks/usePodcastPlayer.ts`: Expose navigation controls
- `components/PodcastPlayer.tsx`: Add skip buttons, track indicator
- `test_podcast_player_unit.ts`: Update tests

#### 8. `learning_session` Module (MODIFY)
**Owns**: Learning flow orchestration

**Changes:**
- `components/LearningFlow.tsx`: Load lesson podcast when showing mini-lesson
- `components/MiniLesson.tsx`: Ensure podcast player visible
- `screens/LearningFlowScreen.tsx`: Initialize playlist at session start

### Frontend Modules (Admin)

#### 9. `admin` Module (MODIFY)
**Owns**: Admin interface

**Changes:**
- `models.ts`: Add podcast fields to lesson DTOs
- `service.ts`: Map podcast fields
- `repo.ts`: Fetch podcast URLs
- `components/content/UnitPodcastList.tsx`: NEW component to display podcasts
- `admin/app/units/[id]/page.tsx`: Show intro + lesson podcasts with links

---

## Implementation Checklist

### Phase 1: Backend Data Model & Content Module Foundation

**Goal**: Establish database schema and basic content module support for lesson podcasts.

- [ ] Add podcast columns to `lessons` table in `backend/modules/content/models.py`:
  - `podcast_transcript` (Text, nullable)
  - `podcast_voice` (String(100), nullable)
  - `podcast_audio_object_id` (UUID, nullable)
  - `podcast_generated_at` (DateTime, nullable)
  - `podcast_duration_seconds` (Integer, nullable)
- [ ] Update `UnitModel` podcast field comments/docs to clarify they represent intro podcast
- [ ] Generate and run Alembic migration for lesson podcast columns
- [ ] Update `backend/modules/content/service.py`:
  - Add podcast fields to `LessonRead` DTO
  - Add podcast fields to `UnitLessonSummary` DTO
  - Add method to generate lesson podcast audio URL (similar to unit podcast audio URL)
  - Update `UnitDetailRead` to clarify unit podcast is intro podcast
- [ ] Update `backend/modules/content/repo.py`:
  - Add queries to fetch lessons with podcast metadata
  - Update unit queries to include lesson podcast data
- [ ] Update `backend/modules/content/routes.py`:
  - Add `GET /api/v1/content/lessons/{lesson_id}/podcast/audio` route
  - Ensure route returns audio file with proper headers
- [ ] Update `backend/modules/content/public.py` if lesson podcast methods needed by other modules
- [ ] Update `backend/modules/content/test_content_unit.py`:
  - Test lesson podcast fields in DTOs
  - Test lesson podcast audio URL generation
- [ ] **Phase 1 Validation**: Run backend unit tests for content module

### Phase 2: Backend Content Generation (Podcasts)

**Goal**: Implement podcast generation flows for intro and lesson podcasts.

- [ ] Create `backend/modules/content_creator/prompts/generate_intro_podcast_transcript.md`:
  - Prompt for generating engaging intro/teaser podcast (~500 words)
  - Emphasizes hooks, importance, and engagement
  - No intro line required
- [ ] Create `backend/modules/content_creator/prompts/generate_lesson_podcast_transcript.md`:
  - Prompt for generating lesson podcast from mini-lesson
  - Must include intro line: "Lesson N. [Lesson Title]"
  - Narrative and engaging style (not just reading mini-lesson)
- [ ] Add `GenerateLessonPodcastTranscriptStep` to `backend/modules/content_creator/steps.py`
- [ ] Create `LessonPodcastFlow` in `backend/modules/content_creator/flows.py`:
  - Orchestrates lesson podcast transcript generation + audio synthesis
  - Similar structure to `UnitPodcastFlow`
- [ ] Modify `UnitPodcastFlow` in `backend/modules/content_creator/flows.py`:
  - Change to generate intro-style podcast (teaser, ~500 words)
  - Use new intro podcast prompt
- [ ] Create `LessonPodcastGenerator` class in `backend/modules/content_creator/podcast.py`:
  - Similar to `UnitPodcastGenerator`
  - Generates transcript + audio for single lesson
  - Includes intro line in transcript
- [ ] Modify `UnitPodcastGenerator` in `backend/modules/content_creator/podcast.py`:
  - Update to generate intro-style podcasts
  - Use intro podcast prompt
- [ ] Modify `LessonCreationFlow` in `backend/modules/content_creator/flows.py`:
  - Integrate lesson podcast generation as part of lesson creation
  - Ensure podcast generated before lesson is saved
- [ ] Update `backend/modules/content_creator/service.py`:
  - Update `create_lesson` to generate lesson podcast
  - Update `create_unit` to generate intro podcast (not full unit podcast)
  - Ensure all lesson podcasts generated before unit marked "completed"
  - Store lesson podcast audio in object store and reference in `LessonModel`
- [ ] Update `backend/modules/content_creator/test_flows_unit.py`:
  - Test `LessonPodcastFlow` generates transcript + audio
  - Test intro podcast generation in `UnitPodcastFlow`
- [ ] Update `backend/modules/content_creator/test_service_unit.py`:
  - Test lesson creation includes podcast
  - Test unit creation generates intro + all lesson podcasts
- [ ] **Phase 2 Validation**: Run backend unit tests for content_creator module

### Phase 3: Backend Catalog, Admin & Seed Data

**Goal**: Surface podcast data in catalog/admin APIs and update seed data.

- [ ] Update `backend/modules/catalog/service.py`:
  - Add podcast fields to `LessonSummary` DTO (has_podcast, podcast_duration_seconds, podcast_voice)
  - Add podcast fields to `LessonDetail` DTO (transcript, audio_url, duration, voice, generated_at)
  - Add lesson podcast fields to `UnitDetail` DTO (lessons should include podcast metadata)
  - Update unit podcast fields in `UnitDetail` to clarify intro podcast
- [ ] Update `backend/modules/catalog/test_lesson_catalog_unit.py`:
  - Test lesson DTOs include podcast fields
- [ ] Update `backend/modules/admin/models.py`:
  - Add podcast fields to `LessonSummary` DTO
  - Add podcast fields to `LessonDetails` DTO
- [ ] Update `backend/modules/admin/service.py`:
  - Include lesson podcast URLs in unit detail responses
  - Include intro podcast URL in unit detail responses
- [ ] Update `backend/modules/admin/routes.py`:
  - Ensure unit detail endpoint returns podcast data for intro + all lessons
- [ ] Update `backend/scripts/create_seed_data.py`:
  - Generate seed units with intro + lesson podcasts
  - Ensure seed data reflects new structure
- [ ] **Phase 3 Validation**: 
  - Run backend unit tests: `backend/scripts/run_unit.py`
  - Run backend integration tests: `backend/scripts/run_integration.py`
  - Verify seed data generation works

### Phase 4: Mobile Content & Catalog (Data Layer)

**Goal**: Update mobile content sync and catalog to handle lesson podcasts.

- [ ] Update `mobile/modules/content/models.ts`:
  - Add podcast fields to `Lesson` interface:
    - `podcastTranscript?: string | null`
    - `podcastAudioUrl?: string | null`
    - `podcastDurationSeconds?: number | null`
    - `podcastVoice?: string | null`
    - `podcastGeneratedAt?: string | null`
  - Add `hasPodcast` computed property
- [ ] Update `mobile/modules/content/service.ts`:
  - Update sync logic to download lesson podcast audio files
  - Cache lesson podcast metadata in offline cache
- [ ] Update `mobile/modules/content/repo.ts`:
  - Update API wire types to include lesson podcast fields
  - Update cache storage to persist lesson podcast data
- [ ] Update `mobile/modules/content/test_content_service_unit.ts`:
  - Test lesson podcast fields synced and cached
- [ ] Update `mobile/modules/catalog/models.ts`:
  - Add podcast fields to `LessonSummary` interface
  - Add podcast fields to `LessonDetail` interface
  - Update `UnitDetail` to clarify unit podcast is intro podcast
- [ ] Update `mobile/modules/catalog/service.ts`:
  - Map lesson podcast fields from API responses to DTOs
- [ ] Update `mobile/modules/catalog/screens/UnitDetailScreen.tsx`:
  - Update UI to show "Intro Podcast" label (instead of "Unit Podcast")
  - Optionally show lesson podcast indicators in lesson list
- [ ] Update `mobile/modules/catalog/components/LessonCard.tsx`:
  - Add podcast indicator icon if lesson has podcast
- [ ] **Phase 4 Validation**: Run mobile unit tests for content and catalog modules

### Phase 5: Mobile Podcast Player & Learning Session (Playback)

**Goal**: Implement playlist, navigation, and autoplay in podcast player; integrate with learning session.

- [ ] Update `mobile/modules/podcast_player/models.ts`:
  - Add `lessonId?: string | null` to `PodcastTrack` (null for intro)
  - Add `lessonIndex?: number | null` to `PodcastTrack` (null for intro, 0-based for lessons)
  - Create `UnitPodcastPlaylist` interface:
    - `unitId: string`
    - `tracks: PodcastTrack[]` (intro + lesson podcasts in order)
    - `currentTrackIndex: number`
- [ ] Update `mobile/modules/podcast_player/store.ts`:
  - Add `playlist: UnitPodcastPlaylist | null` state
  - Add `autoplayEnabled: boolean` state (default: true)
  - Add actions: `setPlaylist`, `setCurrentTrackIndex`, `toggleAutoplay`
- [ ] Update `mobile/modules/podcast_player/service.ts`:
  - Add `loadPlaylist(unitId: string, tracks: PodcastTrack[]): Promise<void>` method
  - Add `skipToNext(): Promise<void>` method (move to next track in playlist)
  - Add `skipToPrevious(): Promise<void>` method (move to previous track in playlist)
  - Add autoplay logic: when track ends, automatically load and play next track if autoplayEnabled
  - Update `loadTrack` to set current track index in playlist
- [ ] Update `mobile/modules/podcast_player/hooks/usePodcastPlayer.ts`:
  - Expose `skipToNext` and `skipToPrevious` functions
  - Expose `loadPlaylist` function
  - Expose `autoplayEnabled` and `toggleAutoplay`
- [ ] Update `mobile/modules/podcast_player/components/PodcastPlayer.tsx`:
  - Add skip forward button (calls `skipToNext`)
  - Add skip back button (calls `skipToPrevious`)
  - Add current track indicator (e.g., "Intro" or "Lesson 2 of 5")
  - Add autoplay toggle (optional, can be in settings)
  - Update UI to show which track is playing in playlist
- [ ] Update `mobile/modules/podcast_player/public.ts`:
  - Export new playlist and navigation methods
- [ ] Update `mobile/modules/podcast_player/test_podcast_player_unit.ts`:
  - Test playlist loading
  - Test skip forward/back navigation
  - Test autoplay logic
- [ ] Update `mobile/modules/learning_session/screens/LearningFlowScreen.tsx`:
  - On session start, load podcast playlist (intro + all lesson podcasts)
  - Initialize podcast player with playlist
- [ ] Update `mobile/modules/learning_session/components/LearningFlow.tsx`:
  - When showing mini-lesson, load corresponding lesson podcast track
  - Ensure podcast player is visible and playing lesson podcast
- [ ] Update `mobile/modules/learning_session/components/MiniLesson.tsx`:
  - Ensure podcast player remains visible
  - Optionally add UI hint that podcast is available
- [ ] **Phase 5 Validation**: 
  - Run mobile unit tests: `cd mobile && npm run test`
  - Manual testing: Verify playlist navigation and autoplay work correctly

### Phase 6: Admin UI, E2E Tests & Final Validation

**Goal**: Complete admin interface, update e2e tests, ensure terminology consistency, and validate entire implementation.

- [ ] Update `admin/modules/admin/models.ts`:
  - Add podcast fields to `LessonSummary` interface
  - Add podcast fields to `LessonDetails` interface
- [ ] Update `admin/modules/admin/service.ts`:
  - Map lesson podcast fields from API responses
- [ ] Update `admin/modules/admin/repo.ts`:
  - Ensure lesson podcast URLs fetched in unit detail calls
- [ ] Create `admin/modules/admin/components/content/UnitPodcastList.tsx`:
  - Component to display intro podcast + list of lesson podcasts
  - Each podcast shows: title, duration, voice, link to audio file
  - Read-only view (no editing)
- [ ] Update `admin/app/units/[id]/page.tsx`:
  - Import and render `UnitPodcastList` component
  - Show intro podcast at top
  - Show lesson podcasts in order below
- [ ] Update existing Maestro e2e tests in `mobile/e2e/` to handle new podcast structure
- [ ] Add testID attributes to new UI elements (skip buttons, track indicator) for Maestro tests
- [ ] Search codebase for "unit podcast" references and update to clarify "intro podcast" where appropriate
- [ ] Ensure all UI labels distinguish between "intro podcast" and "lesson podcasts"
- [ ] Update any documentation or comments that reference old single-podcast structure
- [ ] Ensure lint passes: `./format_code.sh` runs clean
- [ ] Ensure all unit tests pass:
  - Backend: `backend/scripts/run_unit.py`
  - Mobile: `cd mobile && npm run test`
- [ ] Ensure integration tests pass: `backend/scripts/run_integration.py`
- [ ] Follow instructions in `codegen/prompts/trace.md` to trace the user story implementation
- [ ] Fix any issues documented during tracing in `docs/specs/better-mini-lessons/trace.md`
- [ ] Follow instructions in `codegen/prompts/modulecheck.md` to verify modular architecture compliance
- [ ] Examine all new code and ensure no dead code exists (all code is being used)

---

## Notes

- **No backward compatibility**: Database will be wiped; existing units do not need migration
- **All podcasts required**: Unit creation must generate intro + all lesson podcasts before marking unit "completed"
- **Autoplay default**: Autoplay should be enabled by default for seamless listening experience
- **Intro line format**: Lesson podcasts must include "Lesson N. [Lesson Title]" at the start of transcript
- **Intro podcast style**: Engaging teaser (~500 words) that hooks learner, no specific intro line needed
- **Storage**: Lesson podcasts stored in `LessonModel`, not separate table
- **Admin read-only**: Admin interface shows podcasts with links but no editing/regeneration for now

---

## Success Metrics

- Unit creation successfully generates intro + N lesson podcasts
- Mobile learners can navigate between podcasts using skip buttons
- Autoplay works seamlessly from intro through all lessons
- Lesson podcasts sync and play offline
- Admin can review all podcasts via links in unit detail page
- All tests pass, lint passes, architecture compliance verified
