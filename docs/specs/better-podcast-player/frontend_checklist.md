# Better Podcast Player – Frontend Module Checklist

- [x] Cross-module imports use `modules/<other>/public` only (e.g., learning session composes `podcast_player/public`).
- [x] `podcast_player/service.ts` contains only business logic and persistence; no React or networking leaks.
- [x] `podcast_player/public.ts` exposes components and hooks without extra logic.
- [x] Zustand store (`store.ts`) is limited to UI/player state and all exported actions (`setMinimized`) are exercised by MiniPlayer/LearningFlow.
- [x] Track Player integration (`useTrackPlayer`) handles initialization and cleanup without leaking to UI.
- [x] Learning Flow surface pads content and renders restore control via module components, avoiding inline store access.
