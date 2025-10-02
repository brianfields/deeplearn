# User Story: Enhanced Podcast Player with Persistent Mini-Player

**As a learner**, I want to listen to unit podcasts with intuitive, feature-rich controls while I work through lessons and exercises, so that I can absorb content audibly without interrupting my learning flow.

## User Experience Flow

### On Unit Detail Screen (Full Player)

1. User sees a polished, Apple-inspired podcast player card showing:
   - Large play/pause button
   - Current playback position and total duration with seekable progress bar
   - Playback speed controls (0.5x-2.5x with .1x increments) - **global setting**
   - Skip backward/forward buttons (15 seconds)
   - Podcast title and duration
   - Transcript preview/full text
2. User taps play; podcast begins playing
3. Playback state is automatically saved locally:
   - **Per-unit**: Current position
   - **Global**: Playback speed (applies to all podcasts)

### During Learning Session (Mini-Player)

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

### Navigation Behavior

9. User navigates back to Unit List → podcast pauses automatically
10. User returns to the same unit → playback state is restored (position at current global speed)
11. User navigates to a different unit → previous podcast pauses; new unit has independent position state
12. Starting a new unit's podcast automatically pauses any other unit's podcast

### Persistence Across Sessions

13. User closes and reopens the app:
    - Last playback position remembered **per unit**
    - Global playback speed setting remembered
    - User can resume from where they left off in each unit

## Acceptance Criteria

- [ ] Full player on Unit Detail screen has all controls (play/pause, speed, skip, seek, transcript)
- [ ] Mini-player appears on all learning session screens when podcast is loaded
- [ ] Mini-player is compact and doesn't interfere with exercise interaction
- [ ] Playback speed is global and persists across app sessions
- [ ] Playback position is per-unit and persists across app sessions
- [ ] Navigating out of a unit auto-pauses its podcast
- [ ] Only one podcast can play at a time (starting a new one pauses the previous)
- [ ] UI follows Apple/Overcast-inspired design patterns
- [ ] Audio playback is managed by React Native Track Player for reliability
