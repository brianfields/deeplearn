# Learning Coach → Unit Generation Flow Improvement

**Status**: Draft
**Date**: November 2025
**Rationale**: Preserve personalized learning objectives from coach; consolidate learner preferences into a unified field

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

- [ ] Add `learner_desires: str | None` field to `CoachResponse` schema (`conversations/learning_coach.py`)
- [ ] Add `learner_desires` to `LearningCoachSessionState` dataclass (`dtos.py`)
- [ ] Add `learner_desires` to `LearningCoachSessionStateModel` Pydantic model (`routes.py`)
- [ ] Update coach system prompt (`prompts/system_prompt.md`) to include `learner_desires` guidance
- [ ] Update `_build_session_state()` method to extract `learner_desires` from metadata (`conversations/learning_coach.py`)

**Content Creator Module** (`backend/modules/content_creator/`)

- [ ] Update `MobileUnitCreateRequest`: make coach fields **required** (`routes.py`)
  - [ ] `learner_desires: str`
  - [ ] `unit_title: str`
  - [ ] `learning_objectives: list[UnitLearningObjective]`
  - [ ] `target_lesson_count: int`
  - [ ] `conversation_id: str`
  - [ ] Add docstring explaining why all are required
- [ ] Update route handler to pass these new fields to service (`routes.py`)
- [ ] Update `ContentCreatorService.create_unit()` signature: make coach fields required (`service/facade.py`)
- [ ] Pass `learning_objectives` through to flow handler (`service/facade.py`)

**Unit Creation Flow** (`backend/modules/content_creator/flows.py`)

- [ ] Update `UnitCreationFlow.Inputs`: make coach fields required
  - [ ] `learner_desires: str` (required)
  - [ ] `learning_objectives: list[UnitLearningObjective]` (required)
  - [ ] `target_lesson_count: int` (required)
- [ ] Remove `topic`, `learner_level`, `voice` from flow inputs (replaced by `learner_desires`)
- [ ] Pass `learner_desires` and `learning_objectives` to `ExtractUnitMetadataStep`
- [ ] Update flow logic to use coach LOs directly (no regeneration)

**Lesson Creation Flow** (`backend/modules/content_creator/flows.py`)

- [ ] Update `LessonCreationFlow.Inputs` to include `learner_desires: str`
- [ ] Remove `topic`, `learner_level`, `voice` from lesson flow inputs
- [ ] Pass `learner_desires` to `ExtractLessonMetadataStep`

**Flow Handler** (`backend/modules/content_creator/service/flow_handler.py`)

- [ ] Update `execute_unit_creation_pipeline()` signature: make coach fields required
  - [ ] `learner_desires: str` (required)
  - [ ] `learning_objectives: list[UnitLearningObjective]` (required)
  - [ ] `target_lesson_count: int` (required)
- [ ] Remove parameters: `topic`, `learner_level` (replaced by `learner_desires`)
- [ ] Store coach LOs on unit immediately after flow returns (before lesson creation)
- [ ] Pass `learning_objectives` to unit creation flow as `coach_learning_objectives`
- [ ] Pass `learner_desires` to lesson creation flows (not `topic`/`learner_level`/`voice`)
- [ ] Update lesson iteration logic to use `learner_desires`

**Step Definitions** (`backend/modules/content_creator/steps.py`)

- [ ] Update `GenerateUnitSourceMaterialStep.Inputs` to use `learner_desires: str` instead of `topic`/`learner_level`
- [ ] Update `GenerateSupplementalSourceMaterialStep.Inputs` to use `learner_desires: str` instead of `topic`/`learner_level`
- [ ] Update `ExtractUnitMetadataStep.Inputs`:
  - [ ] Add `learner_desires: str`
  - [ ] Add `coach_learning_objectives: list[dict]` (required)
  - [ ] Remove `topic: str` and `learner_level: str`
- [ ] Update `ExtractUnitMetadataStep.Outputs`:
  - [ ] **Remove** `learning_objectives: list[UnitLearningObjective]` field entirely
  - [ ] Keep `lessons: list[LessonPlanItem]` (which reference LO IDs)
- [ ] Update `ExtractLessonMetadataStep.Inputs`:
  - [ ] Add `learner_desires: str`
  - [ ] Remove `topic: str`, `learner_level: str`, `voice: str`

**Unit-Level Prompts** (`backend/modules/content_creator/prompts/`)

- [ ] Update `generate_source_material.md`: Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
- [ ] Update `generate_supplemental_source_material.md`: Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
- [ ] Update `extract_unit_metadata.md`:
  - [ ] Replace `{{topic}}`, `{{learner_level}}` with `{{learner_desires}}`
  - [ ] Add `{{coach_learning_objectives}}` input (JSON array of LOs)
  - [ ] **Remove** learning objectives generation from prompt instructions
  - [ ] **Remove** `learning_objectives` from output JSON schema
  - [ ] Update task: "Design lessons that cover the coach-provided learning objectives"
  - [ ] Ensure each lesson maps to at least one LO ID
  - [ ] Ensure every LO is covered by at least one lesson

**Lesson-Level Prompts** (`backend/modules/content_creator/prompts/`)

- [ ] Update `extract_lesson_metadata.md`: Replace `{{topic}}`, `{{learner_level}}`, `{{voice}}` with `{{learner_desires}}`
- [ ] Update `generate_comprehension_questions.md`: Replace `{{topic}}` with `{{learner_desires}}` (if present)
- [ ] Update `generate_transfer_questions.md`: Replace `{{topic}}` with `{{learner_desires}}` (if present)
- [ ] Update `generate_quiz_from_questions.md`: Add `{{learner_desires}}` context (if needed)
- [ ] Update any other prompts that reference `topic`, `learner_level`, or `voice`

### Phase 2: Frontend Updates

**Learning Conversations Module** (`mobile/modules/learning_conversations/`)

- [ ] Add `learnerDesires?: string | null` to `LearningCoachSessionState` interface (`models.ts`)
- [ ] Update session state mapping in service/queries to include `learnerDesires` (`service.ts`, `queries.ts`)

**Content Creator Module** (`mobile/modules/content_creator/`)

- [ ] Update `UnitCreationRequest` interface: make all coach fields required (`models.ts`)
  - [ ] `learnerDesires: string` (required)
  - [ ] `unitTitle: string` (required)
  - [ ] `learningObjectives: LearningCoachLearningObjective[]` (required)
  - [ ] `targetLessonCount: number` (required)
  - [ ] `conversationId: string` (required)
- [ ] Remove `difficulty` field from request (replaced by `learnerDesires`)
- [ ] Update repo to send new request format (`repo.ts`)

**Learning Coach Screen** (`mobile/modules/learning_conversations/screens/`)

- [ ] Update `handleCreateUnit()` in `LearningCoachScreen.tsx`:
  - [ ] Update guard to require ALL finalized fields: `learnerDesires`, `unitTitle`, `learningObjectives`, `suggestedLessonCount`
  - [ ] Send all required fields (no optional fields in request)
  - [ ] Remove hardcoded `difficulty: 'intermediate'`
- [ ] Update logging/debugging for new fields

### Phase 3: Testing & Validation

**Unit Tests** (Backend)

- [ ] Update unit tests and make sure they pass

**Integration Test** (update existing `test_lesson_creation_integration.py`)

- [ ] Update `TestUnitCreationIntegration.test_unit_creation_from_topic()` to:
  - [ ] Simulate learning coach conversation that finalizes topic and creates LOs
  - [ ] Call `create_unit()` with `learner_desires` and `learning_objectives` (not `topic`/`learner_level`)
  - [ ] Verify generated unit has **identical** learning objectives as coach provided
  - [ ] Verify all coach LO IDs are referenced by at least one lesson
  - [ ] Verify lesson content was generated using `learner_desires` context
  - [ ] Verify unit metadata (title, lesson count) matches coach expectations

**Checks**
- [ ] Ensure lint passes, i.e. './format_code.sh --no-venv' runs clean.
- [ ] Ensure backend unit tests pass, i.e. cd backend && scripts/run_unit.py
- [ ] Ensure frontend unit tests pass, i.e. cd mobile && npm run test
- [ ] Ensure integration tests pass, i.e. cd backend && scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/learning_coach_improvement/trace.md.

**Migration & Cleanup**

- [ ] Document new request format in API docs (`docs/api/content-creator.md`)
- [ ] Update `docs/api/learning_coach.md` with `learner_desires` field

- [ ] Update `docs/api/content-creator.md` with new request schema
- [ ] Update `docs/api/learning_coach.md` with `learner_desires` field documentation
