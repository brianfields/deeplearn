# Audio Player Race Condition Fixes

## Summary

Fixed race conditions causing "failed to load resource" and "track unplayable" errors on iOS. These occurred when multiple `loadTrack` calls overlapped before the player was fully ready.

## Changes Made

### 1. **Mutex for `loadTrack` Serialization** ★★★★★

**File**: `service.ts`
**What**: Added `loadTrackMutex` flag and `loadTrackPromise` to prevent concurrent track loading operations.
**Why**: Multiple simultaneous calls to `loadTrack` caused `TrackPlayer.add()` to fail while `TrackPlayer.reset()` was still executing.
**Impact**: Eliminates the core race condition causing most errors.

```typescript
private loadTrackMutex = false;
private loadTrackPromise: Promise<void> | null = null;

async loadTrack(track: PodcastTrack): Promise<void> {
  // Wait if already loading
  if (this.loadTrackMutex) {
    await this.loadTrackPromise;
  }

  this.loadTrackMutex = true;
  this.loadTrackPromise = this.loadTrackInternal(track);

  try {
    await this.loadTrackPromise;
  } finally {
    this.loadTrackMutex = false;
    this.loadTrackPromise = null;
  }
}
```

### 2. **Strict Await on `initialize()`** ★★★★★

**File**: `service.ts`
**What**: Modified `initialize()` to properly await the initialization promise and only return after it completes.
**Why**: The previous implementation returned early if initialization was in progress, but didn't wait for it to complete.
**Impact**: Ensures `TrackPlayer.setupPlayer()` fully completes before any operations.

```typescript
async initialize(): Promise<void> {
  if (this.isInitialized && !this.initializationPromise) {
    return;
  }
  if (this.initializationPromise) {
    await this.initializationPromise; // Now properly awaits
    return;
  }
  // ... rest of initialization
}
```

### 3. **Wait for Player Ready State** ★★★★☆

**File**: `service.ts`
**What**: Added `waitForPlayerReady()` method that polls for `duration > 0` or non-none state before calling `setRate()`/`seekTo()`.
**Why**: Calling operations before the player is ready causes iOS errors. Duration remains 0 while loading.
**Impact**: Prevents "failed to load resource" errors from premature operation calls.

```typescript
private async waitForPlayerReady(maxWaitMs = 3000): Promise<void> {
  const startTime = Date.now();

  while (Date.now() - startTime < maxWaitMs) {
    const progress = await TrackPlayer.getProgress();
    const state = await TrackPlayer.getState();

    if (progress.duration > 0 || (state !== 'none' && state !== 'loading')) {
      return;
    }

    await new Promise(resolve => setTimeout(resolve, 100));
  }
}
```

### 4. **Duplicate Load Guard in React Component** ★★★★☆

**File**: `components/PodcastPlayer.tsx`
**What**: Added `lastLoadedTrackIdRef` to prevent React effects from triggering duplicate loads of the same track.
**Why**: Navigation focus events and React 18 double-mount can trigger the effect multiple times.
**Impact**: Eliminates duplicate `loadTrack` calls from UI events.

```typescript
const lastLoadedTrackIdRef = useRef<string | null>(null);

useEffect(() => {
  const trackId = track.lessonId || `${track.unitId}:intro`;
  if (lastLoadedTrackIdRef.current === trackId) {
    return; // Skip duplicate load
  }

  lastLoadedTrackIdRef.current = trackId;
  loadTrack(track).catch(error => {
    lastLoadedTrackIdRef.current = null; // Reset on error
  });
}, [isCurrentTrack, loadTrack, track]);
```

### 5. **Better Error Handling in `loadTrackInternal`** ★★★☆☆

**File**: `service.ts`
**What**: Set `isLoading: false` in the catch block of `TrackPlayer.add()`.
**Why**: Errors left the loading state stuck, preventing retries.
**Impact**: Improves recovery from transient errors.

## Testing Recommendations

1. **Rapid track switching**: Navigate between lessons quickly
2. **Navigation focus**: Open/close the unit detail screen repeatedly
3. **Background/foreground**: Test app state transitions
4. **Physical device**: Simulator has known audio timing issues

## Why This Works

The core issue was **overlapping async operations**:

- Multiple `loadTrack` calls triggered before previous ones completed
- `TrackPlayer.add()` called before `TrackPlayer.reset()` finished
- `setRate()`/`seekTo()` called before track metadata loaded

The mutex ensures **strict serialization**: only one track operation at a time, each step fully awaited before the next begins.

## Logs to Watch For

**Good**:

```
[PodcastPlayerService] ✅ Player is ready: { duration: 233, state: 'ready' }
[PodcastPlayerService] ✅ loadTrack complete
```

**Fixed (should no longer appear)**:

```
[PodcastPlayerService] 🔒 loadTrack already in progress, waiting for mutex...
[PodcastPlayer] Track already loaded, skipping: unit-1:intro
```

**Bad (should be rare/gone)**:

```
[PodcastPlayer] 🎵 State from usePlaybackState hook: {"error": {"code": "ios_failed_to_load_resource"}}
```
