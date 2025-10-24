# Simplified Offline Unit Caching

## Status
**Draft** - Proposed simplification of offline caching model

## Problem Statement

The current offline caching system has multiple cache modes ('minimal' vs 'full'), complex state management, and unclear user experience around what data is available offline. Users are confused about:
- When units are usable offline
- What "Global" vs "Personal" means
- Why some units show no lessons
- Whether they can browse units offline

## Goal

Create a simple, predictable offline caching model that users understand intuitively, similar to how podcast or music apps work.

## Simplified Model

### Two-Section Unit List

Replace "Global Units" and "Personal Units" with:

1. **Downloaded** - Fully cached units ready to use
   - All lessons and assets downloaded
   - Can view unit details and start learning
   - Works completely offline
   - Shows storage size
   - Has "Delete" option

2. **Available** - Browsable units not yet downloaded
   - Only metadata cached (title, description, lesson count, cover image)
   - Can browse offline
   - Cannot view lessons or start learning
   - Has "Download" option
   - Shows download progress when downloading

### Caching Strategy

#### On Sync (Login/Pull-to-Refresh)
```
Action: Sync
Payload: Always 'minimal'
Fetches: Unit metadata only
  - id, title, description
  - lessonCount, difficulty
  - coverImageUrl
  - updatedAt timestamp
Stores: SQLite cache for offline browsing
Result: Full unit list browsable offline
```

#### On Download (Explicit User Action)
```
Action: Download specific unit
Payload: 'full' for that unit
Fetches:
  - All lesson metadata
  - All asset URLs (audio, images)
Downloads:
  - All audio files
  - All image files
Updates: downloadStatus = 'completed'
Result: Unit moves to "Downloaded" section
```

### User Flows

#### Browse Offline
```
1. User logs in → Sync runs → Unit metadata cached
2. User goes offline
3. User opens unit list → Sees all units (metadata from cache)
4. Taps on non-downloaded unit → "Download required to view lessons"
5. Taps on downloaded unit → Shows full lessons
```

#### Download Unit
```
1. User taps "Download" on a unit
2. Show confirmation: "Download [Unit Name]? (~5 MB)"
3. User confirms
4. Download starts:
   - Fetch full unit data (lessons + asset URLs)
   - Download all assets (audio, images)
   - Show progress indicator
5. On completion:
   - Unit moves to "Downloaded" section
   - User can now view lessons
```

#### View Unit Details
```
If downloadStatus === 'completed':
  → Show full unit detail with lessons
  → User can start learning

If downloadStatus !== 'completed':
  → Show unit info (title, description, lesson count)
  → Show "Download this unit to view lessons" prompt
  → Offer [Download] or [Cancel] buttons
```

## Implementation Changes

### 1. Remove Cache Mode Complexity

**Current:**
- `cacheMode`: 'minimal' | 'full'
- Complex logic to determine which mode to use
- Confusion about when lessons are available

**New:**
- `downloadStatus`: 'idle' | 'pending' | 'in_progress' | 'completed' | 'failed'
- Simple: completed = downloaded, everything else = not downloaded
- Always cache unit metadata for browsing

### 2. Sync Behavior

**File:** `mobile/modules/offline_cache/service.ts`

**Current:**
```typescript
const payload: CacheMode = units.some(unit => unit.cacheMode === 'full')
  ? 'full'
  : 'minimal';
```

**New:**
```typescript
// Always use 'minimal' for sync - just fetch unit metadata for browsing
const payload: CacheMode = 'minimal';
```

### 3. Unit List Screen

**File:** `mobile/modules/catalog/screens/UnitListScreen.tsx`

**Current Sections:**
- My Units
- Global Units

**New Sections:**
- Downloaded (units where `downloadStatus === 'completed'`)
- Available (all other units)

**Changes:**
- Remove `isGlobal` filtering
- Group by download status instead
- Show storage size only for downloaded units
- Show download button for available units

### 4. Unit Detail Fetching

**File:** `mobile/modules/content/service.ts`

**Current:**
```typescript
async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
  let cached = await this.offlineCache.getUnitDetail(unitId);
  if (!cached || cached.cacheMode === 'minimal') {
    // Fetch from API
  }
  return cached;
}
```

**New:**
```typescript
async getUnitDetail(unitId: string): Promise<UnitDetail | null> {
  const cached = await this.offlineCache.getUnitDetail(unitId);

  // Only return full detail if downloaded
  if (cached?.downloadStatus === 'completed') {
    return this.mapCachedUnitDetail(cached);
  }

  // Return metadata only (for "download required" screen)
  return this.mapCachedUnitMetadata(cached);
}
```

### 5. Download Flow

**File:** `mobile/modules/content/service.ts`

Keep existing download logic but ensure:
```typescript
async requestUnitDownload(unitId: string): Promise<void> {
  // 1. Mark as pending
  await this.offlineCache.markUnitPending(unitId);

  // 2. Fetch full unit data
  await this.runSyncCycleForUnit(unitId, 'full');

  // 3. Download all assets
  await this.offlineCache.downloadUnitAssets(unitId);

  // 4. Mark as completed
  // (handled by downloadUnitAssets)
}
```

### 6. Unit Detail Screen UI

**File:** `mobile/modules/catalog/screens/UnitDetailScreen.tsx`

**If not downloaded:**
```typescript
if (unit.downloadStatus !== 'completed') {
  return (
    <View>
      <UnitHeader unit={unit} />
      <DownloadPrompt
        onDownload={() => requestUnitDownload(unit.id)}
        estimatedSize={unit.estimatedSize}
      />
    </View>
  );
}

// Show full lessons only if downloaded
return <UnitDetailWithLessons unit={unit} />;
```

## Database Schema

No changes needed to SQLite schema. We already have:
- `downloadStatus` column in units table
- Asset tracking in separate table

## API Changes

No backend changes needed. The `/api/v1/content/units/sync` endpoint already supports both 'minimal' and 'full' payloads.

## Migration Strategy

### User Data
- Existing cached units remain in database
- Units with `cacheMode: 'full'` are already marked as `downloadStatus: 'completed'`
- Units with `cacheMode: 'minimal'` will show as available (not downloaded)

### Code Migration
1. Update unit list screen to use new sections
2. Update sync to always use 'minimal' payload
3. Update unit detail screen to check download status
4. Test download flow works as expected
5. Remove references to `cacheMode` in UI (keep in DB for backward compatibility)

## Testing Plan

### Manual Testing
1. **Fresh Login:**
   - Verify all units appear in "Available" section
   - Verify can browse unit list
   - Verify tapping unit shows "download required"

2. **Download Flow:**
   - Tap "Download" on a unit
   - Verify progress indicator shows
   - Verify unit moves to "Downloaded" when complete
   - Verify can view lessons

3. **Offline Browsing:**
   - Log in and sync
   - Go offline
   - Verify can still browse unit list
   - Verify downloaded units show lessons
   - Verify non-downloaded units show download prompt

4. **Storage Management:**
   - Download multiple units
   - Verify storage sizes are accurate
   - Delete a unit
   - Verify unit moves to "Available" section
   - Verify storage freed

### Edge Cases
- Download interruption (airplane mode mid-download)
- Stale metadata (unit updated on server)
- Network timeout during download
- Corrupt asset file

## Success Metrics

### User Experience
- ✅ Users understand two sections: Downloaded vs Available
- ✅ Clear when unit is usable offline
- ✅ Download action is explicit and predictable
- ✅ Offline browsing works reliably

### Technical
- ✅ Reduced code complexity (remove mode branching)
- ✅ Predictable sync behavior
- ✅ Accurate storage reporting
- ✅ No unexpected API calls

## Task List

### Phase 1: Core Logic Changes

- [x] **Update sync to always use 'minimal' payload**
  - File: `mobile/modules/offline_cache/service.ts`
  - Change: Remove logic that checks for 'full' cache mode
  - Set: `const payload: CacheMode = 'minimal';`

- [x] **Update getUnitDetail to check download status**
  - File: `mobile/modules/content/service.ts`
  - Change: Only return full lessons if `downloadStatus === 'completed'`
  - Add: `mapCachedUnitMetadata()` helper for non-downloaded units
  - Add: Logging to show why full detail is/isn't returned

- [x] **Ensure download flow marks units correctly**
  - File: `mobile/modules/content/service.ts`
  - Verify: `requestUnitDownload()` properly sets statuses
  - Ensure: Downloads complete before marking 'completed'

### Phase 2: UI Changes - Unit List Screen

- [x] **Replace sections from Global/Personal to Downloaded/Available**
  - File: `mobile/modules/catalog/screens/UnitListScreen.tsx`
  - Remove: `filteredPersonalUnits`, `filteredGlobalUnits` logic
  - Add: `downloadedUnits`, `availableUnits` sections
  - Group by: `unit.downloadStatus === 'completed'`

- [x] **Update section titles and empty messages**
  - "Downloaded" section: "Your downloaded units"
  - "Available" section: "Available units"
  - Empty message for downloaded: "No units downloaded yet"
  - Empty message for available: "No units available"

- [x] **Update unit card to show download status**
  - Show storage size only for downloaded units
  - Show download button/icon for available units
  - Show progress indicator for downloading units

- [x] **Remove isGlobal filtering and UI elements**
  - Remove "Make Global" / "Make Private" buttons
  - Remove ownership labels
  - Simplify to just download status

### Phase 3: UI Changes - Unit Detail Screen

- [x] **Add download status check**
  - File: `mobile/modules/catalog/screens/UnitDetailScreen.tsx`
  - Check: `unit.downloadStatus === 'completed'`
  - If not downloaded: Show download prompt instead of lessons

- [x] **Create DownloadPrompt component**
  - Show: Unit metadata (title, description, lesson count)
  - Show: Estimated download size
  - Button: "Download Unit" (primary)
  - Button: "Cancel" (secondary)
  - Handle: Call `requestUnitDownload(unitId)`

- [x] **Show download progress if in progress**
  - If `downloadStatus === 'in_progress'`: Show progress indicator
  - Display: "Downloading... X/Y assets"
  - Button: "Cancel Download"

### Phase 4: Downloads Screen Updates

- [x] **Update CacheManagementScreen sections**
  - File: `mobile/modules/offline_cache/screens/CacheManagementScreen.tsx`
  - Same grouping: Downloaded vs Available
  - Show storage size only for downloaded
  - Show download button for available

- [x] **Remove sync/clear all buttons**
  - Already done per previous feedback
  - Verify this is still in place

### Phase 5: Content Service Updates

- [x] **Add mapCachedUnitMetadata helper**
  - File: `mobile/modules/content/service.ts`
  - Returns: Unit info without lessons
  - Used for: Non-downloaded units in detail view

- [x] **Update getUserUnitCollections**
  - File: `mobile/modules/content/service.ts`
  - Change: Return single array instead of Global/Personal split
  - Keep filtering by userId for "My Units" if needed elsewhere

- [x] **Add logging for cache decisions**
  - Log when serving from cache vs requiring download
  - Log download start/progress/completion
  - Help debugging cache issues

### Phase 6: Cleanup

- [x] **Remove unused code**
  - Remove `cacheMode` references from UI (keep in DB)
  - Remove Global/Personal distinction code
  - Clean up unused imports

- [x] **Update logging**
  - Remove debug logs added during development
  - Keep useful production logs
  - Ensure no sensitive data logged

- [ ] **Documentation**
  - Update relevant comments in code
  - Add JSDoc for new helper methods
  - Update any relevant README sections

## Open Questions

1. **Auto-delete strategy:** Should we auto-delete old/unused units to save space?
   - Initial answer: No, explicit only. Add later if needed.

2. **Partial downloads:** What if only some assets fail to download?
   - Mark as 'failed', allow retry, don't mark as 'completed'

3. **Background sync:** Should we auto-sync metadata in background?
   - Not in initial version. Only sync on login and pull-to-refresh.

4. **Download over cellular:** Should we warn users?
   - Yes, show estimated size in download confirmation.

## Related Documents

- Original spec: `/docs/specs/offline-unit-cache/spec.md`
- Implementation trace: `/docs/specs/offline-unit-cache/trace.md`
- Architecture: `/docs/arch/frontend.md`
