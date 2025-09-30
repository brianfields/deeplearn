# Better Podcast Player - Implementation Spec

## User Story

**As a learner**, I want to listen to unit podcasts with intuitive, feature-rich controls while I work through lessons and exercises, so that I can absorb content audibly without interrupting my learning flow.

### User Experience Flow

**On Unit Detail Screen (Full Player):**
1. User sees a polished, Apple-inspired podcast player card showing:
   - Large play/pause button
   - Current playback position and total duration with seekable progress bar
   - Playback speed controls (0.5x, 0.75x, 1x, 1.25x, 1.5x, 1.75x, 2x) - **global setting**
   - Skip backward/forward buttons (15 seconds)
   - Podcast title and duration
   - Transcript preview/full text
2. User taps play; podcast begins playing
3. Playback state is automatically saved locally:
   - **Per-unit**: Current position
   - **Global**: Playback speed (applies to all podcasts)

**During Learning Session (Mini-Player):**
4. User taps "Start Learning" on a lesson within the unit
5. A minimal floating mini-player appears at the **bottom** of all learning screens, showing:
   - Compact podcast title (truncated if needed)
   - Play/pause button
   - Skip backward (15s) button
   - Skip forward (15s) button
   - Minimal height (~60-80px) to avoid interfering with exercises
6. User works through didactic content and multiple-choice questions while podcast continues
7. User can control playback via mini-player without leaving the learning flow
8. Podcast continues playing unless user explicitly pauses it

**Navigation Behavior:**
9. User navigates back to Unit List → podcast pauses automatically
10. User returns to the same unit → playback state is restored (position at current global speed)
11. User navigates to a different unit → previous podcast pauses; new unit has independent position state
12. Starting a new unit's podcast automatically pauses any other unit's podcast

**Persistence Across Sessions:**
13. User closes and reopens the app:
    - Last playback position remembered **per unit**
    - Global playback speed setting remembered
    - User can resume from where they left off in each unit

## Requirements Summary

### What to Build

Create a comprehensive podcast player system with:
- **Full player component** for Unit Detail screen with complete controls
- **Mini-player component** for learning session screens with essential controls
- **Persistent state management** using AsyncStorage (per-unit position, global speed)
- **React Native Track Player integration** for robust audio management
- **Auto-pause on navigation** away from unit context
- **Single-podcast enforcement** (only one podcast plays at a time)

### Key Constraints

- Use **React Native Track Player** (not Expo AV) for better control and reliability
- Mini-player must occupy **minimal space** (60-80px height) and not interfere with exercises
- Playback speed is **global** across all podcasts
- Playback position is **per-unit** and independent
- Follow **Overcast-inspired** UI patterns for controls and polish
- All state must **persist across app restarts** using AsyncStorage
- Module must be **self-contained** with narrow public interface

### Acceptance Criteria

- [ ] Full player on Unit Detail screen has all controls (play/pause, speed, skip, seek, transcript)
- [ ] Mini-player appears on all learning session screens when podcast is loaded
- [ ] Mini-player is compact (60-80px) and doesn't interfere with exercise interaction
- [ ] Playback speed is global and persists across app sessions
- [ ] Playback position is per-unit and persists across app sessions
- [ ] Navigating out of a unit auto-pauses its podcast
- [ ] Only one podcast can play at a time (starting a new one pauses the previous)
- [ ] UI follows Apple/Overcast-inspired design patterns
- [ ] Audio playback is managed by React Native Track Player
- [ ] Unit tests cover state management and persistence logic
- [ ] Existing maestro e2e tests updated if they interact with affected screens

## Cross-Stack Implementation Mapping

### Backend Changes

**No backend changes required.** ✅

Existing podcast infrastructure is sufficient:
- `/api/v1/content/units/{id}/podcast/audio` provides audio streaming
- Unit metadata includes `hasPodcast`, `podcastAudioUrl`, `podcastDurationSeconds`, `podcastTranscript`

---

### Mobile Frontend Changes

#### NEW MODULE: `mobile/modules/podcast_player/`

**Purpose:** Self-contained podcast playback management with persistent state and UI components.

##### Files to create:

**`models.ts`** - Type definitions
- `PodcastTrack` - Track metadata (unitId, title, audioUrl, duration, transcript)
- `PlaybackState` - Current playback state (position, isPlaying, isLoading)
- `PlaybackSpeed` - Speed enum/type (0.5x - 2x)
- `PersistedUnitState` - Per-unit state structure for AsyncStorage
- `GlobalPlayerState` - Global settings structure

**`service.ts`** - Business logic and persistence
- `PodcastPlayerService` class:
  - `initialize()` - Set up Track Player with configuration
  - `loadTrack(track: PodcastTrack)` - Load and prepare a podcast for playback
  - `play()` - Start playback
  - `pause()` - Pause playback
  - `skipForward(seconds: number)` - Skip ahead
  - `skipBackward(seconds: number)` - Skip back
  - `seekTo(position: number)` - Seek to position
  - `setSpeed(speed: PlaybackSpeed)` - Update global playback speed
  - `getSpeed(): PlaybackSpeed` - Get current global speed
  - `getPosition(unitId: string): number` - Get saved position for unit
  - `savePosition(unitId: string, position: number)` - Persist position
  - `pauseCurrentTrack()` - Pause whatever is currently playing
  - `getCurrentTrack(): PodcastTrack | null` - Get active track
  - Private methods for AsyncStorage interaction via infrastructure service

**`store.ts`** - Zustand store for UI state
- State:
  - `currentTrack: PodcastTrack | null`
  - `playbackState: PlaybackState`
  - `globalSpeed: PlaybackSpeed`
  - `isMinimized: boolean` (for UI state)
- Actions:
  - `setCurrentTrack(track: PodcastTrack | null)`
  - `updatePlaybackState(state: Partial<PlaybackState>)`
  - `setGlobalSpeed(speed: PlaybackSpeed)`
  - `setMinimized(minimized: boolean)`

**`public.ts`** - Narrow public interface
- Export `FullPlayer` component
- Export `MiniPlayer` component
- Export `usePodcastPlayer()` hook (wraps service)
- Export `usePodcastState()` hook (wraps store selectors)
- Export essential types: `PodcastTrack`, `PlaybackSpeed`

**`components/FullPlayer.tsx`** - Full-featured player UI
- Props: `track: PodcastTrack`, `onClose?: () => void`
- Displays:
  - Large play/pause button (animated)
  - Seekable progress bar with time labels
  - Playback speed selector (horizontal list of speeds)
  - Skip backward/forward buttons (15s)
  - Transcript section (collapsible/expandable)
  - Loading states
- Uses `usePodcastPlayer()` and `usePodcastState()`
- Overcast-inspired styling with smooth animations

**`components/MiniPlayer.tsx`** - Compact floating player
- Props: `unitId: string` (to determine context)
- Fixed position at bottom of screen (60-80px height)
- Displays:
  - Truncated podcast title
  - Play/pause button (compact)
  - Skip backward button (15s)
  - Skip forward button (15s)
  - Minimal progress indicator (thin bar or percentage)
- Only renders when `currentTrack` matches `unitId`
- Semi-transparent background with blur effect
- Uses `usePodcastPlayer()` and `usePodcastState()`

**`hooks/useTrackPlayer.ts`** - Track Player setup and lifecycle
- `useTrackPlayer()` hook:
  - Initializes Track Player on mount
  - Sets up event listeners (playback state changes, position updates)
  - Updates store when Track Player state changes
  - Cleanup on unmount
  - Returns player status and methods

**`hooks/usePodcastPlayer.ts`** - Simplified hook for components
- Wraps `PodcastPlayerService` methods
- Provides convenient interface for UI components
- Handles loading states and error handling
- Returns: `{ play, pause, skipForward, skipBackward, seekTo, setSpeed, loadTrack, currentTrack, playbackState, globalSpeed, isLoading }`

**`hooks/usePodcastState.ts`** - State access hook
- Wraps Zustand store selectors
- Provides optimized state access to prevent re-renders
- Returns specific slices of state

**`test_podcast_player_unit.ts`** - Unit tests
- Test service persistence logic (save/load position, speed)
- Test store state transitions
- Test single-podcast enforcement
- Mock Track Player and AsyncStorage

---

#### MODIFIED MODULE: `mobile/modules/catalog/`

**`screens/UnitDetailScreen.tsx`** - Replace basic player with FullPlayer

Changes:
- Remove all Expo AV imports and state (`Audio`, `podcastSound`, `isPodcastPlaying`, `isLoadingPodcast`)
- Remove `handleTogglePodcast` callback
- Import `FullPlayer` and `usePodcastPlayer` from `podcast_player/public`
- Create `PodcastTrack` object from unit metadata
- Render `FullPlayer` component in place of current basic player UI
- Use `usePodcastPlayer()` to load track when screen mounts (if unit has podcast)
- Handle cleanup: pause podcast when navigating away from unit detail

**No changes to other files** - Models, service, repo, queries already provide necessary data

---

#### MODIFIED MODULE: `mobile/modules/catalog/`

**`models.ts`** - Add unitId to LessonDetail

Changes:
- Add `unitId?: string | null` field to `LessonDetail` interface
- Add `unit_id?: string | null` to `ApiLessonDetail` wire type
- Update `toLessonDetailDTO()` mapper to include unitId

**`service.ts`** - Pass through unitId

Changes:
- Ensure `getLessonDetail()` includes unitId in mapped DTO

---

#### MODIFIED MODULE: `mobile/modules/learning_session/`

**`screens/LearningFlowScreen.tsx`** - Track unit ID for podcast context

Changes:
- Extract `unitId` from lesson metadata (lesson.unitId)
- Pass `unitId` to `LearningFlow` component as prop
- Add navigation listener to pause podcast when screen loses focus
- Handle case where unitId might be null/undefined (no mini-player in that case)

**`components/LearningFlow.tsx`** - Add MiniPlayer

Changes:
- Add `unitId?: string | null` prop to component interface
- Import `MiniPlayer` and `usePodcastState` from `podcast_player/public`
- Check if podcast is active for current unit using `usePodcastState()`
- Only render `MiniPlayer` if unitId is provided and podcast is active
- Render MiniPlayer at bottom of screen (outside main content, using absolute positioning)
- Adjust main content padding/margin to accommodate mini-player when visible
- Pass `unitId` to MiniPlayer

**No changes needed to learning_session models** - `unitId` is already available in session types

---

#### MODIFIED MODULE: `mobile/modules/infrastructure/`

**`service.ts`** - Minor enhancement (optional)

Changes:
- Consider adding typed helpers for podcast state persistence patterns
- May add `getObject()` / `setObject()` convenience methods for JSON storage
- If current implementation already sufficient, no changes needed

---

#### Root-level Changes

**`package.json`** - Add dependency
- Add `"react-native-track-player": "^4.1.1"` to dependencies

**`App.tsx`** (or app entry point) - Initialize Track Player
- Import and call Track Player setup at app root
- Register playback service if required by library

**`__mocks__/react-native-track-player.ts`** - Jest mock
- Create mock implementation for testing
- Mock all Track Player methods used by the app

**`jest.config.js`** - Register mock
- Add mock mapping for `react-native-track-player`

---

### Database

**No database changes required.** ✅

---

## Implementation Checklist

### Setup & Dependencies
- [ ] Add `react-native-track-player` to `mobile/package.json`
- [ ] Run `npm install` in mobile directory
- [ ] Create `__mocks__/react-native-track-player.ts` with mock implementation
- [ ] Update `jest.config.js` to register Track Player mock

### Backend
**No backend tasks** ✅

### Mobile: New Module - `podcast_player`
- [ ] Create `mobile/modules/podcast_player/` directory
- [ ] Create `models.ts` with type definitions (`PodcastTrack`, `PlaybackState`, `PlaybackSpeed`, persistence types)
- [ ] Create `store.ts` with Zustand store (currentTrack, playbackState, globalSpeed, actions)
- [ ] Create `service.ts` with `PodcastPlayerService` class:
  - [ ] Implement Track Player initialization and configuration
  - [ ] Implement `loadTrack()` with single-track enforcement
  - [ ] Implement playback controls (play, pause, skip, seek)
  - [ ] Implement global speed management with AsyncStorage persistence
  - [ ] Implement per-unit position persistence with AsyncStorage
  - [ ] Integrate with infrastructure service for storage access
- [ ] Create `hooks/useTrackPlayer.ts` for Track Player lifecycle management
- [ ] Create `hooks/usePodcastPlayer.ts` as simplified service wrapper for UI
- [ ] Create `hooks/usePodcastState.ts` for optimized state access
- [ ] Create `components/FullPlayer.tsx`:
  - [ ] Implement layout with large play/pause button
  - [ ] Implement seekable progress bar with time display
  - [ ] Implement playback speed selector (0.5x - 2x)
  - [ ] Implement skip buttons (15s backward/forward)
  - [ ] Implement transcript display section
  - [ ] Add loading and error states
  - [ ] Apply Overcast-inspired styling and animations
- [ ] Create `components/MiniPlayer.tsx`:
  - [ ] Implement compact fixed-bottom layout (60-80px height)
  - [ ] Implement truncated title display
  - [ ] Implement compact play/pause button
  - [ ] Implement skip buttons (15s backward/forward)
  - [ ] Add minimal progress indicator
  - [ ] Add semi-transparent background with blur
  - [ ] Ensure it only renders when current track matches unitId
- [ ] Create `public.ts` exposing components, hooks, and essential types
- [ ] Create `test_podcast_player_unit.ts` with unit tests:
  - [ ] Test service persistence (position save/load, speed save/load)
  - [ ] Test single-podcast enforcement (loading new track pauses old one)
  - [ ] Test store state transitions
  - [ ] Test AsyncStorage interaction (mock infrastructure service)

### Mobile: Module Updates - `catalog`
- [ ] Update `models.ts`:
  - [ ] Add `unitId?: string | null` to `LessonDetail` interface
  - [ ] Add `unit_id?: string | null` to `ApiLessonDetail` wire type
  - [ ] Update `toLessonDetailDTO()` mapper to include unitId
- [ ] Update `service.ts`:
  - [ ] Ensure `getLessonDetail()` includes unitId in mapped DTO
- [ ] Update `screens/UnitDetailScreen.tsx`:
  - [ ] Remove Expo AV imports (`Audio`, `Sound`)
  - [ ] Remove local podcast state (`podcastSound`, `isPodcastPlaying`, `isLoadingPodcast`)
  - [ ] Remove `handleTogglePodcast` and related logic
  - [ ] Import `FullPlayer`, `usePodcastPlayer` from `podcast_player/public`
  - [ ] Create `PodcastTrack` object from unit metadata
  - [ ] Add effect to load track when unit has podcast
  - [ ] Render `FullPlayer` component in place of old player UI
  - [ ] Add cleanup to pause podcast on unmount/navigation away

### Mobile: Module Updates - `learning_session`
- [ ] Update `screens/LearningFlowScreen.tsx`:
  - [ ] Extract `unitId` from lesson metadata (lesson.unitId)
  - [ ] Pass `unitId` prop to `LearningFlow` component
  - [ ] Add navigation listener to pause podcast on blur/unfocus
  - [ ] Handle case where unitId is null/undefined
- [ ] Update `components/LearningFlow.tsx`:
  - [ ] Add `unitId?: string | null` prop to component interface
  - [ ] Import `MiniPlayer`, `usePodcastState` from `podcast_player/public`
  - [ ] Add logic to check if podcast is active for current unit
  - [ ] Only render `MiniPlayer` if unitId is provided and podcast is active
  - [ ] Render `MiniPlayer` at bottom with absolute positioning
  - [ ] Adjust content container padding/margin when mini-player is visible

### Mobile: Root-level Updates
- [ ] Update `App.tsx` (or entry point):
  - [ ] Import Track Player setup utilities
  - [ ] Initialize Track Player at app startup
  - [ ] Register playback service if required

### Testing
- [ ] Ensure lint passes: `./format_code.sh` runs clean
- [ ] Ensure unit tests pass: `(in mobile) npm run test` runs clean
- [ ] Update `mobile/e2e/learning-flow.yaml` maestro test if needed:
  - [ ] Add `testID` attributes to mini-player buttons if e2e test needs to interact with them
  - [ ] Verify learning flow test still passes with mini-player present
- [ ] Manually test full player on Unit Detail screen:
  - [ ] Verify play/pause works
  - [ ] Verify skip forward/backward (15s) works
  - [ ] Verify seek bar is draggable and updates position
  - [ ] Verify playback speed selector changes speed globally
  - [ ] Verify transcript displays correctly
- [ ] Manually test mini-player during learning session:
  - [ ] Verify mini-player appears when podcast is loaded
  - [ ] Verify play/pause works from mini-player
  - [ ] Verify skip buttons work from mini-player
  - [ ] Verify mini-player doesn't interfere with exercise interaction
- [ ] Manually test navigation behavior:
  - [ ] Start podcast on Unit A detail screen
  - [ ] Navigate to lesson in Unit A → mini-player appears
  - [ ] Navigate back to unit list → podcast pauses
  - [ ] Navigate back to Unit A → podcast position restored
  - [ ] Navigate to Unit B and start its podcast → Unit A podcast pauses
- [ ] Manually test persistence:
  - [ ] Play podcast, adjust speed, close app
  - [ ] Reopen app → speed setting persists
  - [ ] Play podcast, seek to middle, close app
  - [ ] Reopen app, navigate to unit → position restored

### Verification & Quality
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/better-podcast-player/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Technical Notes

### React Native Track Player Setup

Track Player requires native module setup and a playback service. Key configuration:
- Capabilities: play, pause, skip forward, skip backward, seek, change rate
- Notification controls for background playback (optional, but nice-to-have)
- Event listeners: `playback-state`, `playback-track-changed`, `playback-queue-ended`

### Persistence Strategy

**AsyncStorage keys:**
- `podcast_player:global_speed` - Global playback speed (single value)
- `podcast_player:unit:{unitId}:position` - Per-unit position (separate key per unit)

**Storage format:**
```typescript
// Global speed
"1.5" // string representation of speed multiplier

// Per-unit position
"125.7" // string representation of position in seconds
```

Use infrastructure service's `getItem()` / `setItem()` for consistency.

### Single-Podcast Enforcement

When `loadTrack()` is called:
1. Check if there's a currently playing track
2. If yes and it's different from new track: pause current, save position
3. Load new track
4. Restore position for new track from AsyncStorage
5. Apply global speed setting

### Navigation Integration

Use React Navigation's focus/blur events to detect context changes:
- `useFocusEffect()` in UnitDetailScreen - load podcast when entering
- `useEffect()` with navigation listeners in LearningFlowScreen - pause on blur
- Store tracks current unit context to enforce single-podcast rule

### UI Design Reference

**Overcast-inspired patterns:**
- Large circular play/pause button with smooth icon transition
- Progress bar with draggable thumb and time labels (current / total)
- Horizontal speed selector with highlighted current speed
- Compact skip buttons flanking play/pause
- Clean typography with strong hierarchy
- Subtle shadows and depth
- Smooth animations for all interactions

**Colors/Theme:**
- Use existing `ui_system` theme colors (design language: /docs/design_language.md)
- Primary color for active states and progress
- Secondary/muted colors for inactive states
- High contrast for accessibility

---

## Risks & Considerations

### Performance
- Track Player manages audio efficiently, but watch for memory leaks
- Unload track when no longer needed (e.g., user logs out)
- Consider limiting AsyncStorage writes (debounce position saves)

### Edge Cases
- Handle missing/corrupted audio URLs gracefully
- Handle network errors during streaming
- Handle AsyncStorage failures (fallback to defaults)
- Handle rapid track switching (debounce or queue)

### Future Enhancements (Out of Scope)
- Background playback with lock screen controls
- Playlist support (queue multiple units)
- Chapter markers within podcasts
- Transcript auto-scroll synchronized with audio
- Download for offline playback
- Variable skip intervals (user-configurable)
- Sleep timer
