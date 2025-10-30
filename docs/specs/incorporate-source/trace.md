# Implementation Trace for Incorporate shared sources into unit creation prompts

## User Story Summary
Learners share documents and links with the learning coach, who evaluates coverage of the proposed objectives. When the learner accepts the brief, the system combines extracted text from those shared resources with any AI-generated supplements needed for uncovered objectives, links every resource to the resulting unit, and exposes both learner and generated resources in the admin dashboard. Phase 6 adds representative seed data and final verification.

## Implementation Trace

### Step 1: Learning coach captures resource coverage
**Files involved:**
- `backend/modules/learning_coach/conversation.py` (lines 118-157, 300-334) stores shared resource IDs, records the structured reply, and persists `uncovered_learning_objective_ids` in the conversation metadata once the coach finalizes the plan. 
- `backend/modules/learning_coach/prompts/system_prompt.md` (lines 18-40) instructs the coach to acknowledge learner uploads, evaluate objective coverage, and list uncovered IDs explicitly.

**Implementation reasoning:**
Learner-shared resources trigger `_generate_structured_reply`, which persists the coach’s assessment (including coverage gaps) so downstream services know which objectives still need supplements.

**Confidence level:** ✅ High
**Concerns:** None

### Step 2: Content creator uses learner resources as primary source material
**Files involved:**
- `backend/modules/content_creator/service/facade.py` (lines 108-155) fetches conversation resources, combines their extracted text, and uses it as the unit’s `source_material` when content exists.
- `backend/modules/content_creator/test_service_unit.py` (lines 182-209) verifies that resource text becomes the stored source material when present.

**Implementation reasoning:**
The service replaces generic generation with concatenated learner resource text, ensuring the created unit reflects the shared materials when available.

**Confidence level:** ✅ High
**Concerns:** None

### Step 3: Supplemental material covers uncovered objectives
**Files involved:**
- `backend/modules/content_creator/service/facade.py` (lines 125-137, 320-367) requests supplemental generation when uncovered objective IDs exist and the session contains matching objectives.
- `backend/modules/content_creator/test_service_unit.py` (lines 242-294) asserts that uncovered objectives trigger supplemental generation and the combined text is sent to the content pipeline.

**Implementation reasoning:**
The helper assembles an outline of uncovered objectives for the supplemental step, merges the result with learner text, and keeps tests to confirm the flow runs only when needed.

**Confidence level:** ✅ High
**Concerns:** None

### Step 4: Source text combination respects order and size limits
**Files involved:**
- `backend/modules/content_creator/service/facade.py` (lines 263-297) adds per-resource headers and truncates content at 200KB.
- `backend/modules/content_creator/service/facade.py` (lines 368-379) prefixes learner sections before supplemental content to preserve ordering.

**Implementation reasoning:**
Learner resources are concatenated with labelled headers, truncated for byte safety, and supplemental text is appended in a separate section so prompts preserve provenance.

**Confidence level:** ✅ High
**Concerns:** None

### Step 5: Resources persist and link to created units
**Files involved:**
- `backend/modules/content_creator/service/facade.py` (lines 382-435) links original resources to the unit and saves generated supplements via the resource service with metadata.
- `backend/modules/resource/service/facade.py` (lines 174-204) persists `generated_source` records with combined metadata.

**Implementation reasoning:**
After unit creation the service attaches learner resource IDs and persists supplemental text through the resource provider, so both learner and generated materials appear in downstream surfaces.

**Confidence level:** ✅ High
**Concerns:** None

### Step 6: Conversation context flows through the mobile client
**Files involved:**
- `mobile/modules/learning_coach/screens/LearningCoachScreen.tsx` (lines 320-373) passes `conversationId` into unit creation after acceptance so backend can fetch resources.
- `mobile/modules/content_creator/test_content_creator_unit.ts` (lines 17-55) verifies POST payloads include `conversation_id` when supplied.

**Implementation reasoning:**
The UI and repo propagate the conversation identifier for the accepted brief, enabling the backend to load resources and coverage state when creating the unit.

**Confidence level:** ✅ High
**Concerns:** None

### Step 7: Admin dashboard surfaces learner and generated resources
**Files involved:**
- `admin/modules/admin/components/resources/ResourceList.tsx` (lines 11-179) renders resource badges, previews, and download actions that highlight `generated_source` entries alongside learner uploads.

**Implementation reasoning:**
Resource rows include explicit styling and download actions for generated supplements, so administrators can distinguish and access AI-generated material next to learner resources.

**Confidence level:** ✅ High
**Concerns:** None

### Step 8: Seed data demonstrates hybrid resource coverage
**Files involved:**
- `backend/seed_data/units/community-first-aid-playbook.json` (lines 142-176) seeds both a learner-uploaded PDF and a generated supplement with uncovered objective IDs.
- `backend/seed_data/units/gradient-descent-mastery.json` (lines 204-250) mixes existing uploads, a learner-shared URL, and a generated supplement for optimization topics.
- `backend/scripts/create_seed_data.py` (lines 32-37) now announces seeding hybrid resources when run verbosely.

**Implementation reasoning:**
Seed fixtures ensure local environments immediately showcase units that combine learner resources with generated supplements, exercising the admin and content creator flows end to end.

**Confidence level:** ✅ High
**Concerns:** None

## Overall Assessment

### ✅ Requirements Fully Met
- Coach evaluates resource coverage and records uncovered objectives.
- Unit creation uses learner resources first and generates supplements for uncovered objectives.
- Combined source text preserves order and respects byte limits.
- All resources, including generated supplements, link back to the created unit and surface in admin.
- Mobile surfaces provide the conversation context needed for end-to-end execution.
- Seed data illustrates learner and generated resources for verification.

### ⚠️ Requirements with Concerns
- None.

### ❌ Requirements Not Met
- None.

## Recommendations
No additional changes required; continue monitoring seed data to reflect future schema updates.
