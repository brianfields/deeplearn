# Implementation Trace for Photo Resource Upload

## User Story Summary
Learners can capture or select photos on mobile, upload them to the backend, run OpenAI Vision extraction, and immediately use the resulting photo resources in learning coach conversations. The experience shows progress feedback, handles permissions, and keeps other resource workflows intact.

## Implementation Trace

### Step 1: Capture or choose a photo on mobile
**Files involved:**
- `mobile/modules/resource/screens/AddResourceScreen.tsx`: `handleTakePhoto` and `handleChoosePhoto` request permissions via Expo Image Picker, launch camera or library workflows, and forward the selected asset to the upload mutation.
- `mobile/modules/resource/queries.ts`: `useUploadPhotoResource` exposes the mutation with pending/error state consumed by the screen buttons.

**Implementation reasoning:**
The screen uses Expo Image Picker APIs to request camera or media library access, surfaces alerts on denial, and calls the mutation with the selected file metadata. React Query tracks mutation status so the UI can disable only the camera/library buttons while showing progress messaging.

**Confidence level:** ✅ High
**Concerns:** None

### Step 2: Client validation and API composition
**Files involved:**
- `mobile/modules/resource/service.ts`: `uploadPhotoResource` validates the DTO, ensuring user ID and file metadata are present before calling the repo.
- `mobile/modules/resource/repo.ts`: Builds a `FormData` payload with `user_id` and the photo file, posting to `/api/v1/resources/upload-photo`.
- `mobile/modules/resource/public.ts`: Exposes the service function through the resource module contract.

**Implementation reasoning:**
The service prevents malformed uploads by checking `request.file` and `request.userId`, while the repo prepares multipart form data in the same format expected by the backend route. The public contract keeps cross-module usage consistent with other resource flows.

**Confidence level:** ✅ High
**Concerns:** None

### Step 3: Backend upload orchestration
**Files involved:**
- `backend/modules/resource/service/facade.py`: `upload_photo_resource` validates content types, uploads via `object_store.upload_image`, generates presigned URLs, invokes text extraction, and persists the resource with `resource_type='photo'`.
- `backend/modules/resource/service/extractors.py`: `extract_text_from_photo` prompts the LLM provider with text + image payload, returning combined description/OCR content with truncation safeguards.
- `backend/modules/resource/routes.py`: `upload_photo_resource` endpoint wires request parsing, calls the service, and maps domain exceptions to HTTP responses.

**Implementation reasoning:**
The service handles all domain rules: validation, storage, presigned URL creation, LLM invocation, truncation, and DTO mapping. Routes remain thin HTTP wrappers, and extractors encapsulate the vision-specific prompt logic. The object store interaction reuses the image pipeline so files land in the existing S3 bucket with metadata recorded in `ImageModel`.

**Confidence level:** ✅ High
**Concerns:** None

### Step 4: Learning coach consumption of photo resources
**Files involved:**
- `backend/modules/learning_coach/service.py` & `conversation.py`: `_extract_resource_ids` and `_fetch_resources` load linked resources using `resource_provider`, and conversation state serialization includes `LearningCoachResource` summaries with extracted text previews.
- `mobile/modules/resource/screens/AddResourceScreen.tsx`: On upload success, the UI notifies the learner and triggers `handleResourceAttached` so the conversation gains immediate context.

**Implementation reasoning:**
The learning coach service uses metadata stored on the conversation to retrieve full `ResourceRead` DTOs, ensuring the extracted text influences prompt building. The mobile screen triggers post-upload flow that adds the resource to the active conversation, aligning with the backend metadata contract.

**Confidence level:** ✅ High
**Concerns:** None

### Step 5: Seed data covering the new workflow
**Files involved:**
- `backend/scripts/create_seed_data_from_json.py`: Seeds photo-aware resources by creating linked `ImageModel` records and attaches learning coach conversations that reference the photo via `resource_ids` metadata. Conversations and messages are regenerated idempotently on reruns.
- `backend/seed_data/units/community-first-aid-playbook.json`: Declares a photo resource with detailed extraction metadata plus a sample learning coach conversation referencing the resource.

**Implementation reasoning:**
Seeding uses the same ORM models as runtime code, ensuring deterministic IDs and metadata for sample photos. Conversations leverage the established metadata key used by learning coach services, so the seeded conversation immediately surfaces the photo context in dev environments.

**Confidence level:** ✅ High
**Concerns:** None

### Step 6: Quality gates and modular compliance
**Files involved:**
- `docs/specs/photo-resource/backend_checklist.md` & `frontend_checklist.md`: Record the architecture audit for Phase 6, confirming no new boundary violations.
- `docs/specs/photo-resource/spec.md`: Phase 6 checklist updated to reflect completed seed data, QA commands, tracing, and module compliance work.

**Implementation reasoning:**
The checklists and spec updates document the verification steps required by Phase 6—formatting, unit/integration tests, module architecture review, and trace creation—ensuring future readers know the state of the feature.

**Confidence level:** ✅ High
**Concerns:** None

## Overall Assessment

### ✅ Requirements Fully Met
- Mobile capture and library selection workflows
- Backend photo upload, storage, and vision extraction pipeline
- Learning coach consumption of photo resources
- Seed data and QA coverage for the end-to-end flow

### ⚠️ Requirements with Concerns
- None

### ❌ Requirements Not Met
- None

## Recommendations
- Continue adding sample photos for additional units if future demos require broader coverage, but the current seed data demonstrates the workflow end to end.
