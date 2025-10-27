# Frontend Modular Compliance (Phase 6)

- [x] Admin service continues to map API → DTO in `service.ts` (podcast metadata additions stayed in service layer with tests updated).
- [x] Unit detail UI consumes DTOs via new `UnitPodcastList` component without bypassing module boundaries (`admin/modules/admin/components/content/UnitPodcastList.tsx`).
- [x] Podcast player retains modular UI boundaries while adding Maestro test coverage (`mobile/modules/podcast_player/components/PodcastPlayer.tsx`).
