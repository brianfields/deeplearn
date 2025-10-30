# Incorporate Source - Implementation Spec

## User Story

**As a learner**, when I share resources (PDFs, documents, links) during my conversation with the learning coach and then accept the proposed learning plan, **I want** the system to use the content from my shared resources as the source material for generating the unit, **so that** the lessons are tailored to the specific materials I provided rather than generic AI-generated content.

### User Experience Changes

**Mobile App:**
1. When a learner shares resources during the coaching conversation, the coach acknowledges them
2. The coach evaluates whether the shared resources adequately cover the proposed learning objectives
3. The coach communicates coverage assessment:
   - If resources fully cover all learning objectives, coach confirms they will be used as-is
   - If resources partially cover objectives, coach identifies which objectives need supplemental generated material
   - If resources are empty or off-topic, coach indicates that source material will be generated
4. When the learner accepts the brief, the system automatically:
   - Extracts and combines text from all attached resources
   - Generates additional source material if needed to cover gaps identified by the coach
   - Combines both learner-provided resources and generated content into the source material
   - Links the original resources to the created unit
   - Saves any generated source material as a special "generated_source" resource type

**Admin Dashboard:**
- Admin can view which resources were used to create each unit (already exists via unit-resource links)
- Admin can now also view the generated source material for any unit (treated as a resource)
- Admin can see whether a unit was created from learner resources vs. generated content

---

## Requirements Summary

### What to Build

1. **Coach Resource Evaluation**: Learning coach evaluates if shared resources adequately cover proposed learning objectives and identifies which objectives need supplemental generated material
2. **Hybrid Source Material Pipeline**: Combine learner-provided resources with generated content (if needed) to ensure all learning objectives are covered
3. **Generated Source Storage**: Store AI-generated supplemental source material as a special resource type for traceability
4. **Conversation-Unit Bridge**: Connect learning coach conversations to unit creation via conversation_id parameter
5. **Admin Visibility**: Display both learner-provided resources and generated source material in admin views

### Constraints

- Maximum combined resource text: 200KB (truncate if exceeded)
- Resource text concatenation format: Header for each resource with filename/URL
- Generated source material is stored as resource type `generated_source`
- Existing unit creation flow remains unchanged (only source material input changes)
- No backward compatibility concerns (pre-launch application)

### Acceptance Criteria

- [ ] When a learner shares resources during coaching, the coach acknowledges them in conversation
- [ ] Coach evaluates if resources cover learning objectives and identifies which objectives need supplemental material
- [ ] When brief is accepted with resources, unit is created using learner-provided resources as primary source material
- [ ] If coach identified coverage gaps, system generates supplemental source material for uncovered learning objectives
- [ ] Both learner resources and generated supplements are combined into final source material (resources first, then generated content)
- [ ] All resources (learner-provided and generated) are automatically linked to the created unit via `UnitResourceModel`
- [ ] Admin can view both learner-provided resources and any generated supplemental material for any unit
- [ ] Combined resource text is capped at 200KB with graceful truncation
- [ ] Empty or failed resource extractions result in fully generated source material

---

## Cross-Stack Mapping

### Backend Modules

#### `content_creator` (MODIFY)
**Files:**
- `service/facade.py` - Add `conversation_id` parameter to `create_unit()`, add helper methods for resource fetching/combining/linking
- `routes.py` - Update `MobileUnitCreateRequest` to accept optional `conversation_id`

**Changes:**
- Add `conversation_id: str | None` parameter to `create_unit()` method
- When conversation_id provided:
  - Fetch resources via `learning_coach_provider()` from `modules.learning_coach.public`
  - Fetch `uncovered_learning_objective_ids` from conversation metadata to know which LOs need generated content
  - Combine resource extracted text (max 200KB) - this becomes the base source material
  - If `uncovered_learning_objective_ids` is present and non-empty, generate supplemental source material for those specific LOs
  - Combine learner resources + generated supplement into final source material (resources first, then generated content with clear section headers)
- Pass combined source material to existing `_execute_unit_creation_pipeline()` via `source_material` parameter
- After unit creation:
  - Link learner-provided resources to unit via `resource_provider().attach_resources_to_unit()`
  - If supplemental material was generated, save as `generated_source` resource and link to unit
- If no resources provided or all have empty text, generate complete source material (existing behavior)

#### `learning_coach` (MODIFY)
**Files:**
- `conversation.py` - Update `CoachResponse` model to include resource coverage evaluation
- `prompts/system_prompt.md` - Add guidance for evaluating resource coverage per learning objective
- `service.py` - Expose conversation resources via existing `get_conversation_resources()` method (already exists)
- `public.py` - Add `get_conversation_resources()` to public interface if not already exposed

**Changes:**
- Add `uncovered_learning_objective_ids: list[str] | None` field to `CoachResponse` Pydantic model in `conversation.py`
  - List of LO IDs that are NOT adequately covered by shared resources
  - Empty list means resources cover everything; None means no resources shared; populated list identifies gaps
- Update system prompt to instruct coach to:
  - Evaluate if each proposed learning objective is adequately covered by shared resources
  - Identify which learning objectives need supplemental generated material
  - Communicate coverage gaps to learner (e.g., "Your materials cover X and Y well, but we'll need to generate additional content for Z")
- Store `uncovered_learning_objective_ids` in conversation metadata when coach response is persisted
- Ensure `get_conversation_resources(conversation_id: str)` is accessible via public interface for content_creator to call

#### `resource` (MODIFY)
**Files:**
- `service/facade.py` - Add method to create generated source resources
- `service/dtos.py` - Document `generated_source` as valid resource type

**Changes:**
- Add `create_generated_source_resource(user_id: int, unit_id: str, source_text: str, metadata: dict) -> ResourceRead` method
- Resource type `generated_source` stores AI-generated source material for traceability
- Generated source resources are linked to units like any other resource

#### `content` (NO CHANGES)
- Existing `UnitResourceModel` join table handles resource-unit links
- Existing `source_material` field on units stores the text
- No public interface changes needed

#### `conversation_engine` (NO CHANGES)
- Already stores resource IDs in conversation metadata
- No changes to storage or retrieval

### Frontend Modules (Mobile)

#### `learning_coach` (MODIFY)
**Files:**
- `models.ts` - Add `uncoveredLearningObjectiveIds` field to session state model
- `repo.ts` - Update API response types
- `screens/LearningCoachScreen.tsx` - Pass `conversationId` to unit creation, optionally display coverage status

**Changes:**
- Add `uncoveredLearningObjectiveIds?: string[] | null` to `LearningCoachSessionState` model
- Optionally display coverage status in UI (e.g., badge showing "Resources cover all objectives" or "Supplemental content needed for 2 objectives")
- Pass `conversationId` when calling `createUnit.mutate()` after brief acceptance

#### `content_creator` (MODIFY)
**Files:**
- `models.ts` - Add `conversationId` to `CreateUnitRequest`
- `repo.ts` - Include `conversationId` in API payload
- `service.ts` - Pass through parameter
- `queries.ts` - Update mutation signature

**Changes:**
- Add `conversationId?: string` to `CreateUnitRequest` interface
- Pass `conversation_id` in API request body when provided
- No breaking changes (parameter is optional)

### Frontend Modules (Admin)

#### Unit detail views (MODIFY)
**Files:**
- `admin/modules/units/components/UnitDetailView.tsx` (or equivalent)

**Changes:**
- Display generated source material resource alongside learner-provided resources
- Show badge or indicator to distinguish `generated_source` from `file_upload` or `url` types
- Provide link to view/download generated source material text

---

## Implementation Checklist

### Phase 1: Foundation - Resource Module & Learning Coach Evaluation

**Goal**: Enable the learning coach to evaluate resource coverage and prepare resource module for generated sources.

#### 1.1 Resource Module - Generated Source Support
- [x] Add `create_generated_source_resource()` method to `backend/modules/resource/service/facade.py`
- [x] Document `generated_source` as a valid resource type in `backend/modules/resource/service/dtos.py`
- [x] Add unit test for creating generated source resources in `backend/modules/resource/test_resource_unit.py`

#### 1.2 Learning Coach - Resource Coverage Evaluation
- [x] Update `CoachResponse` model in `backend/modules/learning_coach/conversation.py` to add `uncovered_learning_objective_ids: list[str] | None` field (Empty list = resources cover all LOs; Populated list = these LO IDs need supplemental material; None = no resources shared yet)
- [x] Update `backend/modules/learning_coach/prompts/system_prompt.md` to instruct coach to evaluate each learning objective against shared resources, identify uncovered LOs, and communicate coverage assessment to learner
- [x] Update `_generate_structured_reply()` in `conversation.py` to store `uncovered_learning_objective_ids` in conversation metadata
- [x] Verify `get_conversation_resources(conversation_id: str)` method in `service.py` is accessible (already exists)
- [x] Add or update `get_conversation_resources()` in `backend/modules/learning_coach/public.py` to expose it for content_creator

#### 1.3 Phase 1 Testing
- [x] Ensure lint passes: `./format_code.sh --no-venv`
- [x] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [x] Test learning coach conversation with resources - verify `uncovered_learning_objective_ids` is set correctly

---

### Phase 2: Content Creator - Resource Fetching & Combining

**Goal**: Enable content creator to fetch conversation resources and combine them into source material.

#### 2.1 Content Creator - Basic Integration
- [x] Add `conversation_id: str | None` parameter to `create_unit()` in `backend/modules/content_creator/service/facade.py`
- [x] Add helper method `_fetch_conversation_resources()` to retrieve resources via `learning_coach_provider`
- [x] Add helper method `_fetch_uncovered_lo_ids()` to retrieve `uncovered_learning_objective_ids` from conversation metadata
- [x] Add helper method `_combine_resource_texts()` to concatenate resource text with headers (max 200KB) - use algorithm from Technical Notes
- [x] Update `create_unit()` to fetch resources if conversation_id provided, combine into base source material, and pass to `_execute_unit_creation_pipeline()`

#### 2.2 Content Creator - Routes
- [x] Update `MobileUnitCreateRequest` in `backend/modules/content_creator/routes.py` to accept optional `conversation_id`
- [x] Update `create_unit_from_mobile()` route handler to pass `conversation_id` to service

#### 2.3 Phase 2 Testing
- [x] Ensure lint passes: `./format_code.sh --no-venv`
- [x] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [x] Add unit tests for creating unit with resources and empty resources fallback

---

### Phase 3: Content Creator - Supplemental Generation & Resource Linking

**Goal**: Add supplemental generation for uncovered LOs and link all resources to created units.

#### 3.1 Supplemental Generation
- [x] Add helper method `_generate_supplemental_source_material()` to generate source material for specific LO IDs
- [x] Update `create_unit()` to fetch uncovered LO IDs, generate supplemental material if needed, and combine with headers

#### 3.2 Resource Linking
- [x] Add method `_link_resources_and_save_generated_source()` to link learner resources and save generated supplements
- [x] Call `_link_resources_and_save_generated_source()` after unit creation succeeds

#### 3.3 Phase 3 Testing
- [x] Ensure lint passes: `./format_code.sh --no-venv`
- [x] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [x] Add unit tests for full coverage, partial coverage, and resource linking scenarios
- [x] Update and run integration tests: `cd backend && scripts/run_integration.py`

---

### Phase 4: Mobile Frontend - Learning Coach & Content Creator

**Goal**: Update mobile app to pass conversation context and display coverage status.

#### 4.1 Mobile - Learning Coach
- [x] Add `uncoveredLearningObjectiveIds?: string[] | null` to `LearningCoachSessionState` in `mobile/modules/learning_coach/models.ts`
- [x] Update `mobile/modules/learning_coach/repo.ts` to parse `uncovered_learning_objective_ids` from API response
- [x] Update `LearningCoachScreen.tsx` to optionally display coverage status and pass `conversationId` to `createUnit.mutate()`
- [x] Add unit test for conversationId passthrough

#### 4.2 Mobile - Content Creator
- [x] Add `conversationId?: string` to `CreateUnitRequest` in `mobile/modules/content_creator/models.ts`
- [x] Update repo, service, and queries to pass through `conversationId`
- [x] Add unit test for conversation-based unit creation

#### 4.3 Phase 4 Testing
- [x] Ensure frontend unit tests pass: `cd mobile && npm run test`
- [ ] Update maestro tests if needed (add testID attributes only, no new tests)

---

### Phase 5: Admin Frontend - Display Resources & Generated Sources

**Goal**: Update admin dashboard to display both learner-provided and generated source resources.

#### 5.1 Admin - Unit Detail Views
- [x] Update unit detail view in `admin/modules/units/` to display resources with type badges
- [x] Add visual distinction for `generated_source` resource type
- [x] Provide view/download link for generated source material text
- [x] Add unit test for resource type display

#### 5.2 Phase 5 Testing
- [x] Test admin UI displays learner-provided and generated source resources with clear visual distinction

---

### Phase 6: Integration, Polish & Verification

**Goal**: Seed data, end-to-end testing, and final quality verification.

#### 6.1 Seed Data
- [x] Update `backend/scripts/create_seed_data.py` to create sample units with resources
- [x] Ensure seed data includes examples of learner-provided and generated source material

#### 6.2 Final Verification
- [x] Ensure lint passes: `./format_code.sh --no-venv`
- [x] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [x] Ensure frontend unit tests pass: `cd mobile && npm run test`
- [x] Ensure integration tests pass: `cd backend && scripts/run_integration.py`
- [x] Follow instructions in `codegen/prompts/trace.md` to trace the user story end-to-end
- [x] Fix any issues documented in `docs/specs/incorporate-source/trace.md`
- [x] Follow instructions in `codegen/prompts/modulecheck.md` to verify modular architecture compliance
- [x] Examine all new code and ensure no dead code exists

---

## Technical Notes

### Resource Text Combination Algorithm
```python
def combine_resource_texts(resources: list[ResourceRead], max_bytes: int = 200_000) -> str:
    """Combine resource texts with headers, respecting byte limit."""
    parts = []
    current_bytes = 0
    
    for resource in resources:
        # Create header
        label = resource.filename or resource.source_url or f"Resource {len(parts) + 1}"
        header = f"\n\n## Source: {label}\n\n"
        content = resource.extracted_text
        
        # Calculate sizes
        header_bytes = len(header.encode('utf-8'))
        content_bytes = len(content.encode('utf-8'))
        
        # Check if we can fit this resource
        if current_bytes + header_bytes + content_bytes > max_bytes:
            # Try to fit partial content
            remaining = max_bytes - current_bytes - header_bytes
            if remaining > 100:  # Only include if we can fit meaningful content
                truncated = content.encode('utf-8')[:remaining].decode('utf-8', errors='ignore')
                parts.append(header + truncated)
            break
        
        parts.append(header + content)
        current_bytes += header_bytes + content_bytes
    
    return "".join(parts)
```

### Supplemental Source Material Generation
When learner resources don't fully cover all learning objectives:
1. After combining learner resource texts
2. Check if `uncovered_learning_objective_ids` exists and is non-empty
3. If yes, generate supplemental source material focused on those specific LOs (pass LO IDs to generation prompt)
4. Combine: "## Learner-Provided Materials\n\n{resource_text}\n\n## Supplemental Generated Content\n\n{generated_text}"
5. After unit creation, save generated supplement as `generated_source` resource
6. Metadata should include: `{"generated_at": timestamp, "unit_id": unit_id, "method": "ai_supplemental", "uncovered_lo_ids": [...]}`

### Coach Coverage Evaluation Criteria
The coach should populate `uncovered_learning_objective_ids` based on:
- **Empty list `[]`**: Learner resources adequately cover ALL proposed learning objectives
- **Populated list `["lo_3", "lo_5"]`**: These specific LO IDs are NOT covered by learner resources and need generated content
- **None**: No resources shared yet, or conversation not finalized (generation will be done for all LOs if no resources at unit creation time)

The coach evaluates coverage by:
- Checking if resource text contains relevant content for each LO
- Assessing depth and quality of coverage
- Identifying missing topics, concepts, or context needed for specific LOs

### Frontend Data Flow
```
LearningCoachScreen (accept brief) 
  ? conversationId passed to createUnit mutation
  ? Mobile repo includes conversation_id in POST /api/v1/content-creator/units
  ? Backend fetches resources from conversation metadata
  ? Backend combines resource texts
  ? Backend creates unit with combined source material
  ? Backend links resources to unit
```

---

## Testing Strategy

### Unit Tests (Backend)
- `test_content_creator_service_unit.py`: 
  - Test unit creation with resources that fully cover all LOs (no supplemental generation)
  - Test unit creation with resources that partially cover LOs (supplemental generation for specific LOs)
  - Test fallback to full generation when resources are empty
  - Test resource linking after unit creation (both learner and generated resources)
  - Test supplemental source resource creation
- `test_resource_unit.py`:
  - Test creating `generated_source` resource type
- `test_learning_coach_unit.py`:
  - Test coach response includes `uncovered_learning_objective_ids` field
  - Test coach correctly identifies uncovered LOs vs. covered LOs

### Unit Tests (Frontend)
- `test_learning_coach_unit.ts`:
  - Test conversationId is passed to unit creation
  - Test `uncoveredLearningObjectiveIds` is parsed from API response
- `test_content_creator_unit.ts`:
  - Test `conversationId` parameter flows through service/repo

### Integration Tests (Backend)
- Update existing integration tests to handle conversation-based unit creation flow
- Test end-to-end: create conversation ? attach resources ? accept brief ? create unit ? verify resources linked

### Manual Testing (Maestro - Mobile)
- Update existing maestro flows if needed
- Add testID attributes where necessary for E2E testing
- Do not create new maestro test files

---

## Terminology Changes

No terminology changes are introduced by this spec. Existing terms remain:
- "source material" - text used to generate lessons
- "resources" - learner-provided materials
- "learning objectives" - goals for the unit
- "brief" - proposed learning plan from coach

---

## Edge Cases & Error Handling

1. **No resources attached**: Fall back to generating complete source material (existing behavior)
2. **All resources have empty extracted_text**: Coach communicates this; if brief accepted anyway, generate complete source material
3. **Resources partially cover some LOs**: Generate supplemental material only for uncovered LOs; combine both sources
4. **Coach doesn't provide `uncovered_learning_objective_ids`**: Treat resources as covering all LOs (use them as-is)
5. **Resource extraction fails mid-creation**: Log error, continue with partial resources and generate supplements for gaps
6. **Conversation not found**: Return 404 error from content_creator route
7. **Resources exceed 200KB combined**: Truncate resource portion; supplemental generation still happens if needed
8. **Unit creation fails after resource fetching**: Resources remain linked to conversation, not orphaned
9. **Supplemental source resource creation fails**: Log warning but don't fail unit creation (non-critical)

---

## Success Metrics

- Units created from learner resources have higher completion rates (hypothesis)
- Learners who share resources are more engaged in coaching conversations
- Admin can trace unit source material for quality audits
- Zero data loss: all learner-provided resources are preserved and linked

---

## Future Enhancements (Out of Scope)

- Allow learners to select which specific resources to use (currently uses all)
- Prioritize certain resource types over others when combining
- Resource relevance scoring to auto-select best resources
- Multi-language resource support
- Resource chunking for very large documents (>200KB)
- Preview of source material before unit creation
