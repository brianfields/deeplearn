## Frontend Architecture Compliance — Phase 6

- [x] No additional frontend edits were required for Phase 6; existing React Query mutations and services already encapsulate the photo upload workflow.
  - Confirmed `modules/resource/queries.ts` and `screens/AddResourceScreen.tsx` continue to call the module service directly without bypassing `public.ts`.
- [x] Verified the UI change that scoped the busy state (Phase 5) still respects module layering.
  - Buttons invoke the `useUploadPhotoResource` mutation through the service contract, keeping hook usage localized to the resource module.

_No further frontend adjustments were necessary once compliance was confirmed._
