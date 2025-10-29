# Implementation Trace for resource-upload

## User Story Summary
Learners can upload or link source materials during a learning coach conversation, have that context flow into generated units, review the materials in a reusable library, and allow admins to audit the uploaded resources. Phase 6 adds representative seed data and verifies end-to-end readiness.

## Implementation Trace

### Step 1: Resource ingestion and storage
**Files involved:**
- `backend/modules/resource/routes.py` — `POST /api/v1/resources/upload` and `/from-url` endpoints validate requests and stream uploads through the resource service (lines 20-140).
- `backend/modules/resource/service/__init__.py` — `ResourceService.upload_file_resource` / `create_url_resource` orchestrate validation, extraction, truncation, and persistence; helpers enforce file-size limits and PDF page selection (lines 52-214).
- `backend/modules/object_store/service.py` — `upload_document` persists binary payloads and metadata to S3-backed storage for reuse (lines 140-205).

**Implementation reasoning:**
Routes accept multipart/form-data or URL payloads, call the service factory, and return DTOs. The service performs file-type validation, extracts text (TXT/MD/PDF) via extractor helpers, truncates to 100 KB, and records metadata plus the object-store document reference. URL resources run through `_extract_text_for_url`, raising friendly `NotImplementedError` messages for unsupported types, matching the spec’s placeholder requirement. Object-store updates ensure uploaded binaries are captured centrally.

**Confidence level:** ✅ High
**Concerns:** None.

### Step 2: Learning coach consumes resource context
**Files involved:**
- `backend/modules/learning_coach/conversation.py` — `add_resource` conversation session method and structured-reply builder merge resource summaries into metadata (lines 120-236).
- `backend/modules/learning_coach/service.py` — resource helpers fetch `ResourceRead` DTOs, generate prompt snippets, and expose them via session state (lines 60-210).
- `backend/modules/learning_coach/routes.py` — attaches resources to conversations and returns updated session state including resource chips (lines 35-150).

**Implementation reasoning:**
When a learner selects a resource, the conversation session stores the resource IDs; `get_conversation_resources` retrieves summaries and `build_resource_context_string` formats them for the system prompt. The structured reply pipeline includes the context, so the coach acknowledges the materials immediately. Routes expose a `POST /resources` attachment endpoint and surface resource metadata in session responses, satisfying conversational feedback requirements.

**Confidence level:** ✅ High
**Concerns:** None.

### Step 3: Mobile resource management and learning coach UI
**Files involved:**
- `mobile/modules/resource/screens/AddResourceScreen.tsx` plus `ResourceLibraryScreen.tsx` and `ResourceDetailScreen.tsx` implement upload, URL entry, previous-resource selection, and detail browsing (lines 30-320, 20-170, 20-150 respectively).
- `mobile/modules/resource/service.ts` and `queries.ts` coordinate DTO mapping and React Query hooks for upload/list/detail flows (lines 20-160 and 15-120).
- `mobile/modules/learning_coach/screens/LearningCoachScreen.tsx` wires the plus button, upload CTA, processing banner, and conversation updates (lines 25-180).

**Implementation reasoning:**
The resource module encapsulates wire/DTO mapping, exposes mutations and queries, and renders upload options (file picker via `react-native-document-picker`, URL validation, prior resources list, “coming soon” photo placeholder). Learning coach screen hooks into these flows: the composer’s plus button navigates to the resource stack, displays processing status, and shows attached resource chips once the coach responds. This satisfies mobile upload, reuse, and acknowledgement requirements.

**Confidence level:** ✅ High
**Concerns:** None.

### Step 4: Admin visibility of learner resources
**Files involved:**
- `admin/modules/admin/components/resources/ResourceList.tsx` renders reusable cards with metadata and usage indicators (lines 1-160).
- `admin/modules/admin/service.ts` plus `repo.ts` aggregate unit/user resource usage (lines 40-220, 30-110).
- `admin/app/units/[id]/page.tsx` and `admin/modules/admin/components/users/UserDetail.tsx` include resource sections in unit/user detail pages (lines 20-90 and 40-120).

**Implementation reasoning:**
Admin services fetch unit-linked resources and per-user uploads, mapping usage counts. The shared `ResourceList` component renders filename/URL, upload dates, sizes, and preview text. Unit and user detail screens embed the list, delivering the read-only oversight mandated by the spec.

**Confidence level:** ✅ High
**Concerns:** None.

### Step 5: Seed data and readiness polish
**Files involved:**
- `backend/scripts/create_seed_data.py` seeds deterministic `DocumentModel`, `ResourceModel`, and `UnitResourceModel` rows, links them to Street Kittens and Gradient Descent units, prints summaries, and exposes data through the JSON output (lines 1450-1700, 1880-1940).
- `docs/specs/resource-upload/backend_checklist.md` and `frontend_checklist.md` document the Phase 6 architecture review.

**Implementation reasoning:**
The script now creates sample file and URL resources for the seeded learners/admin, cleans stale entries to keep reruns idempotent, and connects resources to units so downstream apps show populated data immediately. Checklists record the scoped architecture audit per the modulecheck instructions, confirming no further module adjustments were necessary.

**Confidence level:** ✅ High
**Concerns:** None.

## Overall Assessment

### ✅ Requirements Fully Met
- Resource upload, storage, and extraction pipeline.
- Learning coach resource attachment and prompt enrichment.
- Mobile resource library and learning coach integration.
- Admin resource visibility.
- Seed data populates representative resources.

### ⚠️ Requirements with Concerns
- None.

### ❌ Requirements Not Met
- None.

## Recommendations
Continue extending extractor placeholders (DOCX/PPTX/YouTube) in future phases if richer parsing is needed.
