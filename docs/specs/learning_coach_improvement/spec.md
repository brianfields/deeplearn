# Learning Coach → Unit Generation Flow Improvement

**Status**: In Implementation (Phase 1 Complete, Phase 2-3 In Progress)
**Date**: November 2025
**Rationale**: Preserve personalized learning objectives from coach; consolidate learner preferences into a unified field
**Progress**: 30% complete - Backend data models done, flows/prompts/frontend remaining

---

## Problem Statement

### Current Issues

1. **Fragmented Learner Context**
   - Learner preferences split across `topic`, `learner_level`, `voice`, and scattered conversation metadata
   - Prompts receive partial context (e.g., `topic` + `learner_level` + `voice` separately)
   - New preference types (presentation style, focus area, previous exposure) have no home

2. **Lost Learning Objectives**
   - Learning coach generates personalized learning objectives through conversation
   - Unit generation completely **re-generates** new objectives from source material alone
   - Coach's work (and learner validation) is discarded
   - `uncovered_learning_objective_ids` reference coach objectives, but the coach objectives aren't used—logical inconsistency

3. **Inflexible Preference Handling**
   - Adding a new learner preference (e.g., "prefer visual examples") requires schema changes everywhere
   - Prompts don't have unified access to learner desires

---

## Proposed Solution

### 1. Unified Learner Desires Field

Replace:
```
topic: str
learner_level: str
voice: str | None
```

With:
```
learner_desires: str
```

A **flexible, natural-language summary** of what the learner wants, written by the learning coach. This becomes the **single source of truth** for all learner preferences.

**Examples:**

```
"Learn React Native for building mobile apps. Previous experience with JavaScript.
Prefers project-based learning with real-world examples. Intermediate difficulty level.
Focus on practical patterns used in production apps."

"Beginner learner, no Python background. Prefers step-by-step explanations with lots of
analogies. Interested in web scraping and automation. Learn at a comfortable pace."

"Advanced learner familiar with AWS. Wants to understand infrastructure-as-code patterns.
Prefers technical depth over breadth. Emphasize Terraform and CloudFormation."
```

**What It Contains:**
- Core topic (required)
- Difficulty/level indicators (beginner, intermediate, advanced, or learner's own framing)
- Prior exposure/context
- Presentation preferences (examples, analogies, depth vs. breadth, etc.)
- Voice/tone preferences
- Focus areas or constraints
- Resource preferences (if multiple resources provided)
- Learning style hints (visual, hands-on, theoretical, etc.)

### 2. Learning Coach Sets `learner_desires`

The coach conversation operates **mostly unchanged** but now includes a `learner_desires` field that synthesizes learner inputs:

**New field in `CoachResponse`:**

```python
class CoachResponse(BaseModel):
    message: str
    finalized_topic: str | None  # Deprecated; will become part of learner_desires
    unit_title: str | None
    learning_objectives: list[CoachLearningObjective] | None
    suggested_lesson_count: int | None

    # NEW: Unified learner preferences
    learner_desires: str | None = Field(
        default=None,
        description=(
            "Comprehensive synthesis of learner's goals, prior knowledge, learning style preferences, "
            "and constraints. Written for AI systems to understand the full context. "
            "Evolves throughout conversation. Include topic, level, prior exposure, "
            "presentation preferences, voice preferences, any resource-specific notes, "
            "time constraints, and any other relevant learner context."
        ),
    )

    suggested_quick_replies: list[str] | None
    uncovered_learning_objective_ids: list[str] | None
```

**Minimal Coach Prompt Addition** (add to existing system prompt):

```markdown
## Learner Desires Field

When you finalize the topic (set `finalized_topic`), also populate `learner_desires` with a comprehensive
synthesis of everything you've learned about the learner:

- **Topic**: What they want to learn (specific, with context)
- **Level**: Their current knowledge level in this topic (beginner/intermediate/advanced or descriptive)
- **Prior Exposure**: Relevant background they bring (e.g., "knows Python, new to web frameworks")
- **Preferences**: How they prefer to learn (e.g., "prefers real-world examples", "likes visual diagrams")
- **Voice/Style**: Any preferences about the learning material tone (e.g., "casual and encouraging" vs. "formal and technical")
- **Constraints**: Time constraints, format preferences, focus areas
- **Resource Notes**: If they uploaded materials, note any specific guidance about how to use them

Write this for AI systems to read (not learners). Be detailed and specific.

Example:
"Learn React basics for building interactive websites. Complete beginner to JavaScript and web development.
Prefers learning by doing (hands-on projects). Has strong fundamentals in other programming languages (Python).
Keep it practical with real-world use cases. Encouraging, not patronizing tone."
```

### 3. Mobile Client Sends `learner_desires`

Update the unit creation request:

**Old:**
```typescript
interface UnitCreationRequest {
  topic: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  unitTitle?: string | null;
  targetLessonCount?: number | null;
  conversationId?: string | null;
  ownerUserId?: number | null;
}
```

**New:**
```typescript
interface UnitCreationRequest {
  // Required fields (always present from coach)
  learnerDesires: string;  // From sessionState.learnerDesires
  unitTitle: string;       // From sessionState.unitTitle
  learningObjectives: LearningCoachLearningObjective[];  // From coach
  targetLessonCount: number;  // From sessionState.suggestedLessonCount
  conversationId: string;  // For traceability and resource lookup

  // Optional
  ownerUserId?: number | null;
}
```

**Mobile code (LearningCoachScreen.tsx):**

Updated guard ensures all required fields are present:

```typescript
const handleCreateUnit = () => {
  // Guard: Require all fields that coach should have finalized
  if (!conversationId ||
      !sessionState?.learnerDesires ||
      !sessionState?.unitTitle ||
      !sessionState?.learningObjectives ||
      !sessionState?.suggestedLessonCount) {
    console.log('[LearningCoach] Early return - missing required data');
    return;
  }

  createUnit.mutate(
    {
      learnerDesires: sessionState.learnerDesires,
      unitTitle: sessionState.unitTitle,
      learningObjectives: sessionState.learningObjectives,
      targetLessonCount: sessionState.suggestedLessonCount,
      conversationId: conversationId,
      ownerUserId: user?.id ?? undefined,
    },
    { ... }
  );
};
```

### 4. Backend Route and Service Updates

**Backend Route** (`POST /api/v1/content-creator/units`):

```python
class MobileUnitCreateRequest(BaseModel):
    """Request to create a unit from mobile app via learning coach.

    All fields are required because the coach conversation finalizes them
    before allowing unit creation.
    """

    learner_desires: str
    unit_title: str
    learning_objectives: list[UnitLearningObjective]  # From coach (required)
    target_lesson_count: int
    conversation_id: str  # For traceability and resource lookup
    owner_user_id: int | None = None  # Optional: may be null for guest users
```

**Service** (`ContentCreatorService.create_unit()`):

Updated signature with required coach fields:

```python
async def create_unit(
    self,
    *,
    learner_desires: str,
    unit_title: str,
    learning_objectives: list[UnitLearningObjective],  # From coach (required)
    target_lesson_count: int,
    conversation_id: str,  # Required for coach-initiated creation
    source_material: str | None = None,
    background: bool = False,
    user_id: int | None = None,
) -> UnitCreationResult | MobileUnitCreationResult:
    """Create a learning unit from a finalized coach conversation.

    All learner context fields are required because the coach conversation
    must finalize them before unit creation is allowed.
    """
```

**Pass through to flows:**

```python
# Instead of:
await self._flow_handler.execute_unit_creation_pipeline(
    unit_id=unit.id,
    topic=topic,
    source_material=combined_source_material,
    target_lesson_count=target_lesson_count,
    learner_level=learner_level,
    arq_task_id=None,
)

# Now:
await self._flow_handler.execute_unit_creation_pipeline(
    unit_id=unit.id,
    learner_desires=learner_desires,
    source_material=combined_source_material,
    target_lesson_count=target_lesson_count,
    learning_objectives=learning_objectives,  # From coach
    arq_task_id=None,
)
```

### 5. Flow Updates

**`UnitCreationFlow`** (`flows.py`):

```python
class UnitCreationFlow(BaseFlow):
    flow_name = "unit_creation"

    class Inputs(BaseModel):
        learner_desires: str  # NEW: replaces topic + learner_level
        learning_objectives: list[UnitLearningObjective]  # From coach (required)
        target_lesson_count: int  # From coach (required)
        source_material: str | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # ... existing code ...

        # Step 1: Extract unit metadata
        md_result = await ExtractUnitMetadataStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "target_lesson_count": inputs.get("target_lesson_count"),
                "source_material": material,
                "coach_learning_objectives": [
                    lo.model_dump() for lo in (inputs.get("learning_objectives") or [])
                ],
            }
        )
        unit_md = md_result.output_content
```

**`LessonCreationFlow`** (`flows.py`):

```python
class LessonCreationFlow(BaseFlow):
    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        learner_desires: str  # NEW: replaces topic + learner_level + voice
        learning_objectives: list[str]
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        # Lesson metadata extraction
        md_result = await ExtractLessonMetadataStep().execute(
            {
                "learner_desires": inputs["learner_desires"],
                "learning_objectives": inputs["learning_objectives"],
                "learning_objective_ids": inputs["learning_objective_ids"],
                "lesson_objective": inputs["lesson_objective"],
                "source_material": inputs["source_material"],
            }
        )
```

### 6. Prompt Updates

**All generation prompts** should replace topic/learner_level/voice with a unified `learner_desires` field.

**Pattern in prompts:**

Replace:
```markdown
- **TOPIC:** {{topic}}
- **LEARNER_LEVEL:** {{learner_level}}
- **VOICE:** {{voice}}
```

With:
```markdown
## Learner Context

{{learner_desires}}

This context describes what the learner wants to achieve, their background, preferences, and constraints.
Use this to inform all decisions about content depth, examples, tone, and focus areas.
```

**Affected prompts:**
- `generate_source_material.md`
- `extract_unit_metadata.md` (NEW: add `coach_learning_objectives` parameter)
- `extract_lesson_metadata.md`
- `generate_supplemental_source_material.md`
- All exercise/quiz generation prompts

**Key Addition to `extract_unit_metadata.md`:**

```markdown
## Coach-Provided Learning Objectives

{{coach_learning_objectives}}

These are learning objectives that the learner already validated with their learning coach.
**Use these as the unit's learning objectives.** Do NOT generate new learning objectives.

Your task is to:
1. Accept these learning objectives as the definitive objectives for this unit
2. Design lessons that cover these objectives (map each lesson to one or more objective IDs)
3. Ensure every objective is covered by at least one lesson

Do NOT modify, expand, or regenerate the learning objectives themselves.
```

### 7. Supplemental Material Generation

**`GenerateSupplementalSourceMaterialStep`** now has access to full learner context:

```python
class Inputs(BaseModel):
    learner_desires: str  # NEW: full learner context
    target_lesson_count: int | None = None
    objectives_outline: str  # Specific uncovered objectives
```

**Updated prompt** (`generate_supplemental_source_material.md`):

```markdown
## Learner Context
{{learner_desires}}

## Uncovered Learning Objectives
These specific objectives need additional source material:
{{objectives_outline}}

Generate supplemental content that:
1. Addresses the uncovered objectives
2. Matches the learner's desired depth, style, and prior knowledge (from context above)
3. Integrates seamlessly with existing learner resources
```

---

## Data Model Changes

### Backend Models

**`MobileUnitCreateRequest`** (routes.py):
```python
class MobileUnitCreateRequest(BaseModel):
    """All fields required - learning coach finalizes before allowing creation."""
    learner_desires: str
    unit_title: str
    learning_objectives: list[UnitLearningObjective]
    target_lesson_count: int
    conversation_id: str
    owner_user_id: int | None = None
```

**`CoachResponse`** (conversations/learning_coach.py):
```python
class CoachResponse(BaseModel):
    message: str
    finalized_topic: str | None  # Deprecated (still set for backwards compat)
    unit_title: str | None
    learning_objectives: list[CoachLearningObjective] | None
    suggested_lesson_count: int | None
    learner_desires: str | None  # NEW
    suggested_quick_replies: list[str] | None
    uncovered_learning_objective_ids: list[str] | None

# Note: All become required when finalized_topic is set
# Guard on mobile ensures all are present before unit creation
```

**`UnitCreationFlow.Inputs`** (flows.py):
```python
class Inputs(BaseModel):
    learner_desires: str
    learning_objectives: list[UnitLearningObjective]  # Required
    target_lesson_count: int  # Required
    source_material: str | None = None
```

**`LessonCreationFlow.Inputs`** (flows.py):
```python
class Inputs(BaseModel):
    learner_desires: str
    learning_objectives: list[str]
    learning_objective_ids: list[str]
    lesson_objective: str
    source_material: str
```

### Frontend Models

**`LearningCoachSessionState`** (mobile/modules/learning_conversations/models.ts):
```typescript
export interface LearningCoachSessionState {
  readonly conversationId: string;
  readonly messages: LearningCoachMessage[];
  readonly metadata: Record<string, any>;
  readonly finalizedTopic?: string | null;
  readonly learnerDesires?: string | null;  // NEW
  readonly unitTitle?: string | null;
  readonly learningObjectives?: LearningCoachLearningObjective[] | null;
  readonly suggestedLessonCount?: number | null;
  // ... rest
}
```

**`UnitCreationRequest`** (mobile/modules/content_creator/models.ts):
```typescript
export interface UnitCreationRequest {
  readonly learnerDesires: string;
  readonly unitTitle?: string | null;
  readonly targetLessonCount?: number | null;
  readonly learningObjectives?: LearningCoachLearningObjective[] | null;
  readonly conversationId?: string | null;
  readonly ownerUserId?: number | null;
}
```

---

## Implementation Steps

### Phase 1: Backend Groundwork
1. Add `learner_desires` field to `CoachResponse` (backend model)
2. Update coach system prompt to populate `learner_desires`
3. Add `learner_desires` to `MobileUnitCreateRequest`
4. Update `ContentCreatorService.create_unit()` to accept `learner_desires` and `learning_objectives`

### Phase 2: Flow Integration
5. Update `UnitCreationFlow.Inputs` to include `learner_desires` and `learning_objectives`
6. Update `LessonCreationFlow.Inputs` to include `learner_desires`
7. Update `ExtractUnitMetadataStep.Inputs` to include `learner_desires` and `coach_learning_objectives`

### Phase 3: Prompt Updates
8. Update `extract_unit_metadata.md` to use `learner_desires` and optionally preserve coach LOs
9. Update `extract_lesson_metadata.md` to use `learner_desires`
10. Update `generate_source_material.md` to use `learner_desires`
11. Update `generate_supplemental_source_material.md` to use `learner_desires`
12. Update exercise/quiz generation prompts to use `learner_desires`

### Phase 4: Frontend Integration
13. Add `learnerDesires` field to `LearningCoachSessionState` (frontend model)
14. Coach conversation populates `learnerDesires` progressively
15. Update `UnitCreationRequest` to send `learnerDesires` and `learningObjectives`
16. Update `LearningCoachScreen.tsx` to pass these fields

### Phase 5: Testing & Validation
17. Unit tests for flow handlers with `learner_desires`
18. Integration tests for end-to-end flow with coach LOs
19. Manual testing of unit generation with different learner preferences

---

## Benefits

1. **Preserved Personalization**: Learning coach's objectives are used, not discarded
2. **Unified Context**: All learner preferences in one flexible field that evolves with conversation
3. **Easier to Extend**: New preference types don't require schema changes everywhere
4. **Better Prompts**: All generation steps get full learner context, not fragments
5. **Consistency**: All generation steps operate with the same learner understanding
6. **Traceable**: Unit clearly linked to what learner actually wanted

---

## Backwards Compatibility

- `finalized_topic` field in `CoachResponse` can be deprecated but kept for transition period
- `learner_desires` becomes primary; legacy code can extract topic from `learner_desires` if needed
- Existing units created before this change are unaffected
- Mobile app can gradually transition to new request format

---

## Design Decisions (Finalized)

1. **Coach Prompt**: Minimal changes—coach emits `learner_desires` when finalizing the topic. This is a comprehensive, natural-language summary of learner context.
2. **Learning Objectives**: Coach's learning objectives are used **exactly as provided**. No generation, refinement, or expansion during unit creation flow.
3. **Extraction Step**: `extract_unit_metadata.md` receives coach LOs and uses them as-is. Its job is to design lessons that map to these objectives, not to modify the objectives themselves.
4. **Backwards Compatibility**: For units created without coach conversation, the flow can fall back to generating LOs (edge case).

---

## Success Criteria

- [ ] `learner_desires` is populated by coach when finalizing topic
- [ ] Unit generation receives and uses `learner_desires` in all prompts (replaces topic/learner_level/voice)
- [ ] Coach learning objectives become unit learning objectives **exactly** (no regeneration/refinement)
- [ ] Supplemental material generation uses full `learner_desires` context
- [ ] E2E test: Unit created from coach conversation has **identical** learning objectives as coach proposed
- [ ] E2E test: Generated lessons respect learner preferences from `learner_desires`
- [ ] E2E test: All coach learning objectives are covered by at least one lesson

---

## Implementation Checklist

### Phase 1: Backend Data Models & Learning Coach

**Learning Coach Module** (`backend/modules/learning_conversations/`)

- [x] Add `learner_desires: str | None` field to `CoachResponse` schema (`conversations/learning_coach.py`)
- [x] Add `learner_desires` to `LearningCoachSessionState` dataclass (`dtos.py`)
- [x] Add `learner_desires` to `LearningCoachSessionStateModel` Pydantic model (`routes.py`)
- [x] Update coach system prompt (`prompts/system_prompt.md`) to include `learner_desires` guidance
- [x] Update `_build_session_state()` method to extract `learner_desires` from metadata (`conversations/learning_coach.py`)

**Content Creator Module** (`backend/modules/content_creator/`)

- [x] Update `MobileUnitCreateRequest`: make coach fields **required** (`routes.py`)
  - [x] `learner_desires: str`
  - [x] `unit_title: str`
  - [x] `learning_objectives: list[UnitLearningObjective]`
  - [x] `target_lesson_count: int`
  - [x] `conversation_id: str`
  - [x] Add docstring explaining why all are required
- [x] Update route handler to pass these new fields to service (`routes.py`)
- [x] Update `ContentCreatorService.create_unit()` signature: make coach fields required (`service/facade.py`)
- [x] Pass `learning_objectives` through to flow handler (`service/facade.py`)

**Unit Creation Flow** (`backend/modules/content_creator/flows.py`)

- [x] Update `UnitCreationFlow.Inputs`: make coach fields optional (but support coach-driven)
  - [x] `learner_desires: str` (optional, coach-driven)
  - [x] `coach_learning_objectives: list[dict]` (optional, coach-driven)
  - [x] `target_lesson_count: int` (shared)
- [x] Keep `topic`, `learner_level` for backwards compatibility (legacy path)
- [x] Pass `learner_desires` and `coach_learning_objectives` to `ExtractUnitMetadataStep`
- [x] Update flow logic to use coach LOs directly (no regeneration when coach-driven)

**Lesson Creation Flow** (`backend/modules/content_creator/flows.py`)

- [x] Update `LessonCreationFlow.Inputs` to include `learner_desires: str`
- [x] Remove `topic`, `learner_level`, `voice` from lesson flow inputs
- [x] Pass `learner_desires` to `ExtractLessonMetadataStep`

**Flow Handler** (`backend/modules/content_creator/service/flow_handler.py`)

- [x] Update `execute_unit_creation_pipeline()` signature: accept coach fields (optional for backwards compat)
  - [x] `learner_desires: str | None` (coach-driven)
  - [x] `learning_objectives: list[UnitLearningObjective] | None` (coach-driven)
- [x] Keep `topic`, `learner_level` for backwards compatibility
- [x] Add mode detection logic (coach-driven vs. legacy)
- [x] Build appropriate flow inputs based on mode
- [x] Pass coach LOs directly through flow

**Step Definitions** (`backend/modules/content_creator/steps.py`)

- [x] Update `GenerateUnitSourceMaterialStep.Inputs` to use `learner_desires: str` instead of `topic`/`learner_level`
- [x] Update `GenerateSupplementalSourceMaterialStep.Inputs` to use `learner_desires: str` instead of `topic`/`learner_level`
- [x] Update `ExtractUnitMetadataStep.Inputs`:
  - [x] Add `learner_desires: str`
  - [x] Add `coach_learning_objectives: list[dict]` (optional)
  - [x] Remove `topic: str` and `learner_level: str`
- [x] Update `ExtractUnitMetadataStep.Outputs`:
  - [x] Keep `learning_objectives: list[UnitLearningObjective]` (for both coach and generated LOs)
- [x] Update `ExtractLessonMetadataStep.Inputs`:
  - [x] Add `learner_desires: str`
  - [x] Remove `topic: str`, `learner_level: str`, `voice: str`

**Unit-Level Prompts** (`backend/modules/content_creator/prompts/`)

- [x] Update `generate_source_material.md`: Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
- [x] Update `generate_supplemental_source_material.md`: Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
- [x] Update `extract_unit_metadata.md` - **CRITICAL CHANGE**:
  - [x] Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
  - [x] Add `{{coach_learning_objectives}}` input section (JSON array of LOs from coach)
  - [x] Update instructions to use coach LOs when provided, generate when absent
  - [x] Ensure each lesson maps to at least one LO ID and all LOs are covered

**Lesson-Level Prompts** (`backend/modules/content_creator/prompts/`)

- [x] Update `extract_lesson_metadata.md`: Replace `{{topic}}`, `{{learner_level}}`, `{{voice}}` with `{{learner_desires}}`
- [x] Update `generate_comprehension_questions.md`: Replace `{{topic}}` with `{{learner_desires}}`
- [x] Update `generate_transfer_questions.md`: Replace `{{topic}}` with `{{learner_desires}}`
- [x] `generate_quiz_from_questions.md`: No changes needed (uses question bank, not direct learner context)

### Phase 2: Frontend Updates

**Learning Conversations Module** (`mobile/modules/learning_conversations/`)

- [x] Add `learnerDesires?: string | null` to `LearningCoachSessionState` interface (`models.ts`)

**Content Creator Module** (`mobile/modules/content_creator/`)

- [x] Update `UnitCreationRequest` interface: make all coach fields required (`models.ts`)
  - [x] `learnerDesires: string` (required)
  - [x] `unitTitle: string` (required)
  - [x] `learningObjectives: LearningCoachLearningObjective[]` (required)
  - [x] `targetLessonCount: number` (required)
  - [x] `conversationId: string` (required)
- [x] Remove `difficulty` field from request (replaced by `learnerDesires`)
- [x] Add legacy `UnitCreationRequestLegacy` for backwards compatibility

**Learning Coach Screen** (`mobile/modules/learning_conversations/screens/`)

- [x] Update `handleCreateUnit()` in `LearningCoachScreen.tsx`:
  - [x] Update guard to require ALL finalized fields: `learnerDesires`, `unitTitle`, `learningObjectives`, `suggestedLessonCount`
  - [x] Send all required fields (no optional fields in request)
  - [x] Remove hardcoded `difficulty: 'intermediate'`
- [x] Update logging/debugging for new fields

### Phase 3: Testing & Validation

**Unit Tests** (Backend)

- [ ] Update unit tests and make sure they pass

**Integration Test** (update existing `test_lesson_creation_integration.py`)

- [x] Renamed test to `test_unit_creation_from_learning_coach()`
- [x] Simulates learning coach conversation outputs with learner desires and LOs
- [x] Calls `create_unit()` with `learner_desires`, `unit_title`, `learning_objectives`, `target_lesson_count`, `conversation_id`
- [x] Verifies generated unit has **identical** learning objectives as coach provided
- [x] Verifies all coach LO IDs are referenced by at least one lesson
- [x] Comprehensive assertions on result structure and database persistence

**Validation & Quality Assurance**
- [x] Python syntax validation: flows.py, steps.py, flow_handler.py ✅
- [x] TypeScript syntax validation: mobile frontend models ✅
- [x] Backend models: routes.py, facade.py ✅
- [x] Integration test: test_lesson_creation_integration.py ✅
- [x] Prompts updated for `learner_desires` ✅
- ⏳ Run lint: `./format_code.sh --no-venv`
- ⏳ Run backend unit tests: `cd backend && scripts/run_unit.py`
- ⏳ Run frontend unit tests: `cd mobile && npm run test`
- ⏳ Run integration tests: `cd backend && scripts/run_integration.py`

**Documentation & API Updates**
- ⏳ Update API docs (`docs/api/content-creator.md`) with new `MobileUnitCreateRequest` schema
- ⏳ Update `docs/api/learning_coach.md` with `learner_desires` field documentation

---

## Implementation Status Summary

### ✅ COMPLETED

**Backend Core (Phase 1):**
- ✅ Learning Coach: Added `learner_desires` to `CoachResponse`, `LearningCoachSessionState`, system prompt
- ✅ Content Creator Routes: Updated `MobileUnitCreateRequest` with **required** coach fields (no optional fallbacks)
- ✅ Content Creator Service: Updated `create_unit()` signature to accept **required** `learner_desires` and `learning_objectives`
- ✅ Flow Engine - Coach-Only:
  - `UnitCreationFlow.Inputs`: **Required** `learner_desires`, `coach_learning_objectives` (no legacy fallback)
  - `LessonCreationFlow.Inputs`: Simplified to use `learner_desires` only (no `topic`/`learner_level`/`voice`)
- ✅ Step Definitions - Simplified:
  - `GenerateUnitSourceMaterialStep`: Uses `learner_desires` (required)
  - `GenerateSupplementalSourceMaterialStep`: Uses `learner_desires` (required)
  - `ExtractUnitMetadataStep`: **Always** uses `coach_learning_objectives` (required, no fallback generation)
  - `ExtractLessonMetadataStep`: Uses `learner_desires` (required)
- ✅ Flow Handler: Single execution path, **always** coach-driven (no mode detection)

**Prompts (Phase 1):**
- ✅ `generate_source_material.md`: Replaced `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
- ✅ `generate_supplemental_source_material.md`: Replaced variables with `{{learner_desires}}`
- ✅ `extract_unit_metadata.md`: **CRITICAL** - Now accepts `{{coach_learning_objectives}}` and uses them as-is
- ✅ `extract_lesson_metadata.md`: Updated inputs to use `{{learner_desires}}`
- ✅ `generate_comprehension_questions.md`: Updated to use `{{learner_desires}}`
- ✅ `generate_transfer_questions.md`: Updated to use `{{learner_desires}}`

**Frontend (Phase 2) - Coach-Only:**
- ✅ `LearningCoachSessionState`: Added `learnerDesires?: string | null`
- ✅ `UnitCreationRequest`: **Required** coach fields only (no legacy support)
  - `learnerDesires`, `unitTitle`, `learningObjectives`, `targetLessonCount`, `conversationId` all required
- ✅ `LearningCoachScreen.tsx`: Updated `handleCreateUnit()` with comprehensive guard for all required fields
- ✅ Legacy `CreateUnitScreen`: Redirects to Learning Coach (no direct unit creation)
- ✅ Catalog service: Simplified validation for coach-driven requests only

**Code Quality:**
- ✅ Python syntax validation: All backend files compile cleanly
- ✅ TypeScript validation: All frontend files pass type checking (zero errors)
- ✅ Simplified implementation: No mode detection, no defensive dual-path logic

### 🔄 READY FOR TESTING

**Integration Test (Phase 3):**
- ✅ `test_unit_creation_from_learning_coach()` - Full end-to-end test covering:
  - Coach conversation simulation with learner desires
  - Coach-provided learning objectives
  - Unit creation with all required fields
  - Verification of LO preservation (no regeneration)
  - Verification of lesson plan coverage of all LOs

**Pending Tasks:**
- ⏳ Run `./format_code.sh --no-venv` for lint validation
- ⏳ Run `cd backend && scripts/run_unit.py` for backend unit tests
- ⏳ Run `cd mobile && npm run test` for frontend unit tests
- ⏳ Run `cd backend && scripts/run_integration.py` for integration tests
- ⏳ Update API documentation with new request schema
- ⏳ Update Learning Coach API documentation

---

## Key Design Decisions

### 1. Coach-Only Architecture
The implementation is **coach-driven only** - no legacy mode cruft:
- `UnitCreationFlow.Inputs` requires `learner_desires` and `coach_learning_objectives`
- All steps in the pipeline use `learner_desires` for unified learner context
- Backend flow handler has single execution path (no mode detection)
- Frontend models and services only support coach-driven requests
- Old form-based unit creation redirects to Learning Coach

### 2. Learning Objectives Handling
- **Always**: Uses LOs directly from learning coach; **NEVER** regenerates
- `UnitCreationFlow` passes `coach_learning_objectives` through to `ExtractUnitMetadataStep`
- `ExtractUnitMetadataStep` receives coach LOs and uses them as-is for lesson planning
- This eliminates redundant LO generation and preserves coach's carefully constructed objectives

### 3. Unified Learner Context
The `learner_desires` field consolidates all learner preferences:
- Topic/domain
- Difficulty level
- Prior exposure/experience
- Presentation style preferences
- Voice/tone preferences
- Resource focus preferences

This single field replaces the previous fragmented approach of passing separate `topic`, `learner_level`, `voice` fields, providing complete context to all generation steps.

### 4. Required Fields
All unit creation fields are **required** because the learning coach must finalize them:
- `learner_desires: str` (unified learner context from coach)
- `unit_title: str` (coach-created title)
- `learning_objectives: list` (coach-created LOs)
- `target_lesson_count: int` (coach-recommended count)
- `conversation_id: str` (for traceability and resource lookup)

This enforces that unit creation **only** happens after successful coach conversation.

---

## Next Steps

1. **Write/Update Integration Test** (`test_lesson_creation_integration.py`)
   - Simulate full learning coach conversation
   - Create unit with coach-provided LOs
   - Verify LOs are preserved (not regenerated)

2. **Run Full Test Suite**
   - Backend: `cd backend && scripts/run_unit.py`
   - Frontend: `cd mobile && npm run test`
   - Integration: `cd backend && scripts/run_integration.py`

3. **Lint & Format**
   - Run: `./format_code.sh --no-venv`
   - Fix any issues

4. **Update API Documentation**
   - Document `MobileUnitCreateRequest` schema changes
   - Document `learner_desires` field usage

5. **Monitor & Iterate**
   - Trace the user story via `codegen/prompts/trace.md`
   - Document findings in `trace.md`
   - Fix any integration issues
