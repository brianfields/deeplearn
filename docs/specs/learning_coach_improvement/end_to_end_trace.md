# End-to-End Trace: Learning Coach → Unit Generation

**Date**: November 2025
**Purpose**: Verify complete data flow from learner interaction through unit generation

---

## 1. LEARNER INTERACTION: Learning Coach Conversation

### **1.1 Frontend: LearnerTurn (User Sends Message)**

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 242-272)
```typescript
const handleQuickReply = (reply: string): void => {
  setOptimisticMessage({
    id: uuid.v4(),
    role: 'user',
    content: reply,
    createdAt: new Date().toISOString(),
    metadata: {},
  });

  learnerTurn.mutate({
    conversationId,
    userMessage: reply,
    userId: user ? String(user.id) : null,
  });
};
```

**What happens**:
- ✅ User clicks quick reply or types message
- ✅ Optimistic UI update shows message immediately
- ✅ Frontend calls `learnerTurn.mutate()` with message

### **1.2 Frontend → Backend: HTTP Request**

**File**: `mobile/modules/learning_conversations/repo.ts` (lines 38-65)
```typescript
async learnerTurn(payload: {
  conversationId: string;
  userMessage: string;
  userId: string | null;
}): Promise<LearningCoachSessionState> {
  const response = await this.infrastructure.request<ApiSessionState>(
    `/api/v1/learning-coach/conversations/${encodeURIComponent(
      payload.conversationId
    )}/turn`,
    {
      method: 'POST',
      body: JSON.stringify({
        user_message: payload.userMessage,
        user_id: payload.userId,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return toSessionState(response);  // ✅ Maps API response to frontend DTO
}
```

**What happens**:
- ✅ Sends POST to `/api/v1/learning-coach/conversations/{id}/turn`
- ✅ Converts to snake_case for backend
- ✅ Awaits response
- ✅ Converts response back to camelCase via `toSessionState()` (now includes `learnerDesires`)

---

## 2. BACKEND: Learning Coach Conversation Processing

### **2.1 Backend Route Handler**

**File**: `backend/modules/learning_conversations/routes.py` (learning coach conversation endpoint)
```python
@router.post("/conversations/{conversation_id}/turn")
async def learner_turn(
    conversation_id: str,
    request: LearnerTurnRequest,
    service: LearningCoachService = Depends(get_service),
) -> LearningCoachSessionStateModel:
    """Process learner message and get updated conversation state."""
    result = await service.process_learner_turn(
        conversation_id=conversation_id,
        user_message=request.user_message,
        user_id=request.user_id,
    )
    return result
```

**What happens**:
- ✅ Receives learner message
- ✅ Calls service to process turn

### **2.2 Backend Service: Build Coach Message**

**File**: `backend/modules/learning_conversations/conversations/learning_coach.py`
```python
async def process_turn(
    self,
    user_message: str,
) -> CoachResponse:
    """Process turn and get coach response."""

    # Add user message to conversation
    self.messages.append(Message(role="user", content=user_message))

    # Call LLM with conversation history
    coach_response = await self._get_coach_response()

    return coach_response
```

**What happens**:
- ✅ Adds user message to conversation history
- ✅ Calls LLM to generate coach response

---

## 3. LLM CALL: Coach Response Generation

### **3.1 Backend: Invoke LLM Service**

**File**: `backend/modules/learning_conversations/conversations/learning_coach.py`
```python
async def _get_coach_response(self) -> CoachResponse:
    """Get structured response from LLM."""

    response, _, _ = await self.llm_service.generate_structured_response(
        messages=self.messages,  # ✅ Full conversation history
        response_model=CoachResponse,  # ✅ Instructs LLM to return JSON matching CoachResponse
    )

    return response
```

**LLM Service Call Stack**:
- **Entry**: `llm_services_provider()` returns LLM service instance
- **Service**: Calls appropriate provider (OpenAI, mock, etc.)
- **OpenAI Provider**: Sends to OpenAI API with model gpt-5
- **Response**: Receives structured JSON matching `CoachResponse` schema

### **3.2 CoachResponse Schema**

**File**: `backend/modules/learning_conversations/conversations/learning_coach.py` (lines 29-50)
```python
class CoachResponse(BaseModel):
    message: str  # ✅ Coach's conversational response
    finalized_topic: str | None  # When coach finalizes the topic
    unit_title: str | None  # ✅ New: When coach creates unit title
    learning_objectives: list[CoachLearningObjective] | None  # ✅ Coach-generated LOs
    suggested_lesson_count: int | None  # ✅ Coach recommends lesson count
    learner_desires: str | None  # ✅ NEW: Comprehensive learner context
    suggested_quick_replies: list[str] | None  # Quick reply options
    uncovered_learning_objective_ids: list[str] | None  # LOs needing supplemental material
```

**LLM System Prompt** (lines 40-54 of system_prompt.md):
```markdown
## Learner Desires Field

When you finalize the topic, also populate `learner_desires` with a comprehensive
synthesis of everything you've learned about the learner:

- **Topic**: What they want to learn (specific, with context)
- **Level**: Their current knowledge level (beginner/intermediate/advanced or descriptive)
- **Prior Exposure**: Relevant background they bring
- **Preferences**: How they prefer to learn
- **Voice/Style**: Tone preferences
- **Constraints**: Time constraints, format preferences, focus areas
- **Resource Notes**: If they uploaded materials, note specific guidance

Write this for AI systems to read. Be detailed and specific.
```

**Example LLM Response**:
```json
{
  "message": "Great! I've gathered enough information...",
  "finalized_topic": "Learn gradient descent with practical applications",
  "unit_title": "Gradient Descent Fundamentals",
  "learning_objectives": [
    {
      "id": "lo_1",
      "title": "Understand gradient descent mechanics",
      "description": "Comprehend how GD algorithm works"
    },
    {
      "id": "lo_2",
      "title": "Apply gradient descent to training",
      "description": "Apply GD concepts to train networks"
    }
  ],
  "suggested_lesson_count": 2,
  "learner_desires": "Beginner looking to understand gradient descent with practical ML applications",
  "suggested_quick_replies": ["Generate unit now", "Tell me more"],
  "uncovered_learning_objective_ids": []
}
```

---

## 4. BACKEND → FRONTEND: Session State Response

### **4.1 Backend Returns CoachResponse**

**File**: `backend/modules/learning_conversations/routes.py`
```python
return LearningCoachSessionStateModel(
    conversation_id=conversation_id,
    messages=[...],  # All messages in conversation
    metadata={...},
    finalized_topic=coach_response.finalized_topic,  # ✅ Set when coach finalizes
    learner_desires=coach_response.learner_desires,  # ✅ NEW: Learner context
    unit_title=coach_response.unit_title,            # ✅ Coach-created title
    learning_objectives=coach_response.learning_objectives,  # ✅ Coach LOs
    suggested_lesson_count=coach_response.suggested_lesson_count,  # ✅ Lesson count
    # ... other fields
)
```

### **4.2 HTTP Response to Frontend**

**JSON Response** (snake_case):
```json
{
  "conversation_id": "conv-abc123",
  "messages": [...],
  "metadata": {...},
  "finalized_topic": "Learn gradient descent with practical applications",
  "learner_desires": "Beginner looking to understand gradient descent with practical ML applications",
  "unit_title": "Gradient Descent Fundamentals",
  "learning_objectives": [
    {"id": "lo_1", "title": "Understand gradient descent mechanics", "description": "..."},
    {"id": "lo_2", "title": "Apply gradient descent to training", "description": "..."}
  ],
  "suggested_lesson_count": 2,
  "uncovered_learning_objective_ids": []
}
```

---

## 5. FRONTEND: Session State Mapping & Update

### **5.1 Frontend Receives and Maps Response**

**File**: `mobile/modules/learning_conversations/repo.ts` (lines 132-148)
```typescript
function toSessionState(dto: ApiSessionState): LearningCoachSessionState {
  return {
    conversationId: dto.conversation_id,
    messages: dto.messages.map(toMessage),
    metadata: dto.metadata ?? {},
    finalizedTopic: dto.finalized_topic ?? null,
    learnerDesires: dto.learner_desires ?? null,  // ✅ NOW MAPPED
    unitTitle: dto.unit_title ?? null,
    learningObjectives: normalizeLearningObjectives(dto.learning_objectives),
    suggestedLessonCount: dto.suggested_lesson_count ?? null,
    proposedBrief: normalizeBrief(dto.proposed_brief),
    acceptedBrief: normalizeBrief(dto.accepted_brief),
    resources: normalizeResources(dto.resources),
    uncoveredLearningObjectiveIds: normalizeUncoveredLearningObjectiveIds(
      dto.uncovered_learning_objective_ids
    ),
  };
}
```

**What happens**:
- ✅ Converts snake_case to camelCase
- ✅ Maps `learner_desires` from API
- ✅ Maps `unit_title`, `learning_objectives`, `suggested_lesson_count`
- ✅ Normalizes arrays and complex types

### **5.2 Frontend Updates Session State in React**

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 80-94)
```typescript
const sessionState = sessionQuery.data ?? startSession.data ?? null;

// Debug: Log session state changes
useEffect(() => {
  if (sessionState) {
    console.log('[LearningCoach] Session state updated:', {
      conversationId: sessionState.conversationId,
      finalizedTopic: sessionState.finalizedTopic ? 'present' : 'null',
      learnerDesires: sessionState.learnerDesires,  // ✅ NOW AVAILABLE
      unitTitle: sessionState.unitTitle,
      learningObjectives: sessionState.learningObjectives,
      suggestedLessonCount: sessionState.suggestedLessonCount,
      messageCount: sessionState.messages.length,
    });
  }
}, [sessionState]);
```

**What happens**:
- ✅ Session state updates via React Query
- ✅ UI re-renders with new coach response
- ✅ Fields now available for display and unit creation

---

## 6. FRONTEND UI: Display Unit Generation Screen

### **6.1 Render Finalized State**

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 440-494)
```typescript
{sessionState.finalizedTopic ? (
  <View style={styles.finalizedContainer}>
    <Text style={styles.unitTitle}>{sessionState.unitTitle}</Text>

    <Text style={styles.sectionTitle}>Learning Objectives</Text>
    <View style={styles.objectivesList}>
      {sessionState.learningObjectives?.map((obj) => (
        <View key={obj.id} style={styles.objectiveItem}>
          <Text style={styles.objectiveBullet}>•</Text>
          <Text style={styles.objectiveText}>{obj.description}</Text>
        </View>
      ))}
    </View>

    {sessionState.suggestedLessonCount && (
      <Text style={styles.lessonCountInfo}>
        Suggested lessons: {sessionState.suggestedLessonCount}
      </Text>
    )}

    <Pressable
      style={styles.generateButton}
      onPress={handleCreateUnit}  // ✅ User clicks to generate
    >
      <Text style={styles.generateButtonText}>🚀 Generate Unit</Text>
    </Pressable>
  </View>
) : null}
```

**UI Display**:
- ✅ Shows unit title from coach
- ✅ Displays learning objectives from coach
- ✅ Shows suggested lesson count
- ✅ Shows "Generate Unit" button

---

## 7. LEARNER ACTION: Click "Generate Unit"

### **7.1 Frontend: Guard Check**

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 283-293)
```typescript
const handleCreateUnit = (): void => {
  console.log('[LearningCoach] handleCreateUnit called', {
    conversationId,
    learnerDesires: sessionState?.learnerDesires,  // ✅ Guard checks this
    unitTitle: sessionState?.unitTitle,
    learningObjectives: sessionState?.learningObjectives,
    suggestedLessonCount: sessionState?.suggestedLessonCount,
  });

  // Guard: Require all fields that coach should have finalized
  if (
    !conversationId ||
    !sessionState?.learnerDesires ||  // ✅ NEW: NOW CHECKING THIS
    !sessionState?.unitTitle ||
    !sessionState?.learningObjectives ||
    !sessionState?.suggestedLessonCount
  ) {
    console.log('[LearningCoach] Early return - missing required data');
    return;
  }

  // ... continues to call createUnit.mutate()
}
```

**What happens**:
- ✅ Guard ensures ALL required fields are present (including `learnerDesires`)
- ✅ Returns early if any field missing
- ✅ If all present, proceeds to unit creation

### **7.2 Prepare Request Payload**

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 308-316)
```typescript
createUnit.mutate(
  {
    learnerDesires: sessionState.learnerDesires!,              // ✅ From coach
    unitTitle: sessionState.unitTitle!,                         // ✅ From coach
    learningObjectives: sessionState.learningObjectives!,       // ✅ From coach
    targetLessonCount: sessionState.suggestedLessonCount!,      // ✅ From coach
    conversationId: conversationId,                             // ✅ For traceability
    ownerUserId: user?.id ?? undefined,
  },
  {
    onError: error => {
      console.error('Failed to create unit from learning coach', error);
    },
  }
);
```

**Payload Structure**:
```typescript
{
  learnerDesires: "Beginner looking to understand gradient descent with practical ML applications",
  unitTitle: "Gradient Descent Fundamentals",
  learningObjectives: [
    {id: "lo_1", title: "Understand gradient descent mechanics", description: "..."},
    {id: "lo_2", title: "Apply gradient descent to training", description: "..."}
  ],
  targetLessonCount: 2,
  conversationId: "conv-abc123",
  ownerUserId: 42
}
```

---

## 8. FRONTEND → BACKEND: Unit Creation Request

### **8.1 Frontend Sends Request**

**File**: `mobile/modules/content_creator/repo.ts` (lines 26-43)
```typescript
async createUnit(
  request: UnitCreationRequest
): Promise<UnitCreationResponse> {
  try {
    let url = `${CONTENT_CREATOR_BASE}/units`;
    if (request.ownerUserId != null) {
      const qs = new URLSearchParams({
        user_id: String(request.ownerUserId),
      });
      url = `${url}?${qs.toString()}`;
    }

    const response = await this.infrastructure.request<{
      unit_id: string;
      status: string;
      title: string;
    }>(url, {
      method: 'POST',
      body: JSON.stringify({
        learner_desires: request.learnerDesires,        // ✅ From coach
        unit_title: request.unitTitle,                   // ✅ From coach
        learning_objectives: request.learningObjectives, // ✅ From coach
        target_lesson_count: request.targetLessonCount,  // ✅ From coach
        conversation_id: request.conversationId,
        owner_user_id: request.ownerUserId ?? null,
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return {
      unitId: response.unit_id,
      status: response.status,
      title: response.title,
    };
  } catch (error) {
    throw this.handleServiceError(error, 'Failed to create unit');
  }
}
```

**HTTP Request**:
```
POST /api/v1/content-creator/units?user_id=42
Content-Type: application/json

{
  "learner_desires": "Beginner looking to understand gradient descent with practical ML applications",
  "unit_title": "Gradient Descent Fundamentals",
  "learning_objectives": [
    {"id": "lo_1", "title": "Understand gradient descent mechanics", "description": "..."},
    {"id": "lo_2", "title": "Apply gradient descent to training", "description": "..."}
  ],
  "target_lesson_count": 2,
  "conversation_id": "conv-abc123",
  "owner_user_id": 42
}
```

---

## 9. BACKEND: Unit Creation Route Handler

### **9.1 Backend Route**

**File**: `backend/modules/content_creator/routes.py` (lines 64-90)
```python
@router.post("/units", response_model=MobileUnitCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_unit_from_mobile(
    request: MobileUnitCreateRequest,  # ✅ Validates all coach fields required
    user_id: int | None = Query(None, ge=1, description="Authenticated user identifier"),
    service: ContentCreatorService = Depends(get_content_creator_service),
) -> MobileUnitCreateResponse:
    """Create a unit from learning coach conversation.

    Unit creation happens in the background and returns immediately with in_progress status.
    """
    try:
        logger.info("🔥 Mobile unit creation request from coach: conversation_id='%s', title='%s'",
                   request.conversation_id, request.unit_title)

        result = await service.create_unit(
            learner_desires=request.learner_desires,           # ✅ Pass through
            unit_title=request.unit_title,                     # ✅ Pass through
            learning_objectives=request.learning_objectives,   # ✅ Pass through
            target_lesson_count=request.target_lesson_count,   # ✅ Pass through
            conversation_id=request.conversation_id,           # ✅ Pass through
            background=True,                                    # ✅ Run in background
            user_id=user_id or request.owner_user_id,
        )

        logger.info("✅ Mobile unit creation started: unit_id=%s", result.unit_id)

        return MobileUnitCreateResponse(
            unit_id=result.unit_id,
            status=UnitStatus.IN_PROGRESS.value,
            title=result.title
        )
```

### **9.2 Request Validation**

**File**: `backend/modules/content_creator/routes.py` (lines 41-53)
```python
class MobileUnitCreateRequest(BaseModel):
    """Request to create a unit from mobile app via learning coach.

    All fields are required because the coach conversation finalizes them
    before allowing unit creation.
    """
    learner_desires: str                                    # ✅ Required
    unit_title: str                                         # ✅ Required
    learning_objectives: list[UnitLearningObjective]       # ✅ Required
    target_lesson_count: int                               # ✅ Required
    conversation_id: str                                   # ✅ Required
    owner_user_id: int | None = None
```

**What happens**:
- ✅ Pydantic validates ALL required fields are present
- ✅ Type validation: strings are strings, ints are ints, arrays are arrays
- ✅ If any required field missing → 422 Unprocessable Entity error

---

## 10. BACKEND: Service Layer - Coach-Only Enforcement

### **10.1 Service Create Unit**

**File**: `backend/modules/content_creator/service/facade.py` (lines 94-217)
```python
async def create_unit(
    self,
    *,
    learner_desires: str | None = None,
    learning_objectives: list | None = None,
    unit_title: str | None = None,
    target_lesson_count: int | None = None,
    conversation_id: str | None = None,
    source_material: str | None = None,
    background: bool = False,
    user_id: int | None = None,
) -> UnitCreationResult | MobileUnitCreationResult:
    """Create a learning unit from learning coach context."""

    # Determine if this is a coach-driven or legacy creation
    is_coach_driven = learner_desires is not None  # ✅ Check if coach fields present

    if is_coach_driven:
        if not learning_objectives:
            raise ValueError("learning_objectives must be provided with learner_desires")

        # Extract topic from learner_desires (will be used by flows)
        determined_topic = learner_desires  # ✅ Use learner_desires as context
    else:
        if not topic:
            raise ValueError("Either learner_desires or topic must be provided")
        determined_topic = topic

    # Use appropriate title source
    title_source = unit_title if unit_title else (determined_topic if is_coach_driven else topic)
    provisional_title = self._truncate_title(title_source, max_length=200)

    # ... create unit ...

    if background:
        await self._status_handler.enqueue_unit_creation(
            unit_id=unit.id,
            learner_desires=learner_desires if is_coach_driven else None,    # ✅ Pass to task queue
            learning_objectives=learning_objectives if is_coach_driven else None,
            source_material=combined_source_material,
            target_lesson_count=target_lesson_count,
            topic=topic if not is_coach_driven else None,
            learner_level=learner_level,
        )
        return MobileUnitCreationResult(unit_id=unit.id, title=unit.title, status=UnitStatus.IN_PROGRESS.value)

    # Coach-driven only path now
    if not is_coach_driven:
        raise ValueError("Coach-driven unit creation is required - legacy mode is no longer supported")

    result = await self._flow_handler.execute_unit_creation_pipeline(
        unit_id=unit.id,
        learner_desires=learner_desires,           # ✅ Pass all coach fields
        learning_objectives=learning_objectives,   # ✅ To flow handler
        source_material=combined_source_material,
        target_lesson_count=target_lesson_count,
        arq_task_id=None,
    )

    return result
```

**What happens**:
- ✅ Detects this is coach-driven (learner_desires present)
- ✅ Validates learning_objectives provided
- ✅ Creates unit record in DB
- ✅ Enqueues task for background processing (or runs immediately if foreground)

---

## 11. BACKEND: Flow Handler - Execute Unit Creation Pipeline

### **11.1 Flow Handler: Coach Fields Processing**

**File**: `backend/modules/content_creator/service/flow_handler.py` (lines 50-101)
```python
async def execute_unit_creation_pipeline(
    self,
    *,
    unit_id: str,
    learner_desires: str,                           # ✅ Required: Learner context
    learning_objectives: list[UnitLearningObjective],  # ✅ Required: Coach LOs
    target_lesson_count: int | None,
    source_material: str | None = None,
    arq_task_id: str | None = None,
) -> UnitCreationResult:
    """Execute the end-to-end unit creation pipeline.

    All parameters are required because the learning coach must finalize them
    before unit creation is allowed.
    """

    logger.info("=" * 80)
    logger.info("🧱 UNIT CREATION START")
    logger.info(f"   Unit ID: {unit_id}")
    logger.info(f"   Learner Desires: {learner_desires[:50]}...")
    logger.info(f"   Learning Objectives: {len(learning_objectives)}")
    logger.info(f"   Target Lessons: {target_lesson_count or 'auto'}")
    logger.info("=" * 80)

    # ... update status ...

    logger.info("📋 Phase 1: Unit Planning")
    flow = UnitCreationFlow()

    # Build flow inputs with coach-provided context
    # Handle both UnitLearningObjective objects and dicts
    coach_los = []
    for lo in learning_objectives:
        if isinstance(lo, dict):
            coach_los.append(lo)
        else:
            coach_los.append(lo.model_dump())

    flow_inputs: dict[str, Any] = {
        "learner_desires": learner_desires,           # ✅ Pass to flow
        "coach_learning_objectives": coach_los,       # ✅ Pass to flow
        "source_material": source_material,
        "target_lesson_count": target_lesson_count,
    }

    unit_plan = await flow.execute(flow_inputs, arq_task_id=arq_task_id)

    # ... process results ...

    # CRITICAL: Return coach LOs directly (no regeneration)
    return {
        "unit_title": unit_md.unit_title,
        "learning_objectives": coach_learning_objectives,  # ✅ COACH LOS PRESERVED
        "lessons": [...],
        "lesson_count": int(unit_md.lesson_count),
    }
```

**What happens**:
- ✅ Receives coach-provided learner_desires and learning_objectives
- ✅ Converts learning_objectives to dicts for flow
- ✅ Builds flow inputs with BOTH coach fields
- ✅ Executes flow with full learner context

---

## 12. BACKEND: Flow Execution - Unit Creation Flow

### **12.1 Unit Creation Flow**

**File**: `backend/modules/content_creator/flows.py` (lines 165-234)
```python
class UnitCreationFlow(BaseFlow):
    """Create a coherent learning unit using only the active steps.

    Pipeline:
    1) Generate unit source material if not provided
    2) Extract unit-level metadata (title, lesson plan) using coach-provided LOs
    """

    flow_name = "unit_creation"

    class Inputs(BaseModel):
        learner_desires: str                            # ✅ From flow handler
        coach_learning_objectives: list[dict]           # ✅ From flow handler
        source_material: str | None = None
        target_lesson_count: int | None = None

    async def _execute_flow_logic(self, inputs: dict[str, Any]) -> dict[str, Any]:
        logger.info("🧱 Unit Creation Flow - Starting")

        learner_desires: str = inputs.get("learner_desires") or ""
        coach_learning_objectives: list[dict] = inputs.get("coach_learning_objectives") or []

        # Step 0: Ensure we have source material
        material: str | None = inputs.get("source_material")

        if not material:
            logger.info("📝 Generating source material…")
            gen_result = await GenerateUnitSourceMaterialStep().execute(
                {
                    "learner_desires": learner_desires,  # ✅ PASS LEARNER DESIRES
                    "target_lesson_count": inputs.get("target_lesson_count"),
                }
            )
            material = str(gen_result.output_content)

        # Step 1: Extract unit metadata (lesson plan using coach LOs)
        logger.info("📋 Extracting unit metadata…")
        md_result = await ExtractUnitMetadataStep().execute(
            {
                "learner_desires": learner_desires,              # ✅ PASS LEARNER DESIRES
                "coach_learning_objectives": coach_learning_objectives,  # ✅ PASS COACH LOS
                "target_lesson_count": inputs.get("target_lesson_count"),
                "source_material": material,
            }
        )
        unit_md = md_result.output_content

        # Final assembly - use coach LOs directly (no regeneration)
        return {
            "unit_title": unit_md.unit_title,
            "learning_objectives": coach_learning_objectives,  # ✅ RETURN COACH LOS UNCHANGED
            "lessons": [ls.model_dump() for ls in unit_md.lessons],
            "lesson_count": int(unit_md.lesson_count),
            "source_material": material,
        }
```

**What happens**:
- ✅ Step 0: Generate source material using `learner_desires` context
- ✅ Step 1: Extract unit metadata, passing BOTH `learner_desires` and `coach_learning_objectives`
- ✅ **Critical**: Return `coach_learning_objectives` directly (no regeneration)

### **12.2 Extract Unit Metadata Step**

**File**: `backend/modules/content_creator/steps.py` (lines 58-82)
```python
class ExtractUnitMetadataStep(StructuredStep):
    """Extract unit-level metadata and ordered lesson plan as strict JSON.

    Uses coach-provided learning objectives directly (no regeneration).
    Focuses on generating lesson plan that covers all coach LOs.
    """

    step_name = "extract_unit_metadata"
    prompt_file = "extract_unit_metadata.md"

    class Inputs(BaseModel):
        learner_desires: str                      # ✅ From flow
        coach_learning_objectives: list[dict]     # ✅ From flow
        target_lesson_count: int | None = None
        source_material: str

    class Outputs(BaseModel):
        unit_title: str
        # NOTE: Lesson plan only; LOs come directly from coach (not regenerated)
        learning_objectives: list[UnitLearningObjective] = []  # ✅ Empty by design
        lessons: list[LessonPlanItem]
        lesson_count: int
```

### **12.3 Prompt Guides LLM to Use Coach LOs**

**File**: `backend/modules/content_creator/prompts/extract_unit_metadata.md` (lines 13-24)
```markdown
- **COACH_LEARNING_OBJECTIVES (from learning coach conversation):**
  {{coach_learning_objectives}}   // Provided from coach

# Your Task in Detail

1) Derive a **concise, specific unit title** that clearly reflects the learner's desires and intended learning scope.

2) **Handle learning objectives based on COACH_LEARNING_OBJECTIVES:**
   - **IF coach_learning_objectives provided:** Use them as-is; do not regenerate.
     Map them to the provided IDs and ensure lesson plans cover all of them.
   - **IF coach_learning_objectives is empty or null:** Define 3–8 unit-level learning objectives
     from the source material...

3) Propose an **ordered list of 1–20 lessons** that **coherently covers the unit**. For each lesson, provide:
   - `title` (unique, concrete, non-overlapping)
   - `lesson_objective` (one precise, measurable objective for the lesson; 1–2 sentences)
   - `learning_objective_ids` (array of UO ids this lesson advances; ALL UOs must be covered)
```

**What happens**:
- ✅ LLM receives `learner_desires` for context
- ✅ LLM receives `coach_learning_objectives` (coach's LOs)
- ✅ **Key Instruction**: "Use them as-is; do not regenerate"
- ✅ LLM creates lesson plan that covers all coach LOs
- ✅ LLM returns empty `learning_objectives` (they come from coach)

---

## 13. BACKEND: Lesson Generation - LO Context Flow

### **13.1 For Each Lesson: Lesson Creation Flow**

**File**: `backend/modules/content_creator/service/flow_handler.py` (lines 154-162)
```python
tasks = [
    self._create_single_lesson(
        lesson_plan=lp,
        lesson_index=i,
        unit_los=unit_los,
        unit_material=unit_material,
        learner_desires=learner_desires,  # ✅ PASS LEARNER DESIRES
        arq_task_id=arq_task_id,
    )
    for i, lp in enumerate(batch, start=batch_start)
]
```

**File**: `backend/modules/content_creator/service/flow_handler.py` (lines 333-342)
```python
md_res = await LessonCreationFlow().execute(
    {
        "learner_desires": learner_desires,      # ✅ PASS LEARNER DESIRES
        "learning_objectives": lesson_lo_descriptions,
        "learning_objective_ids": lesson_lo_ids,
        "lesson_objective": lesson_objective_text,
        "source_material": unit_material,
    },
    arq_task_id=arq_task_id,
)
```

### **13.2 Lesson Creation Flow**

**File**: `backend/modules/content_creator/flows.py` (lines 36-54)
```python
class LessonCreationFlow(BaseFlow):
    """Create a complete lesson using the concept-driven pipeline."""

    flow_name = "lesson_creation"

    class Inputs(BaseModel):
        learner_desires: str                  # ✅ NEW: Replaces topic/learner_level/voice
        learning_objectives: list[str]
        learning_objective_ids: list[str]
        lesson_objective: str
        source_material: str
```

**What happens**:
- ✅ Each lesson gets `learner_desires` context
- ✅ Lesson generation respects learner preferences (difficulty, presentation style, etc.)
- ✅ All exercises, concepts, and quiz generation receives unified learner context

---

## 14. BACKEND: Comprehensive Data Flow in Prompts

### **14.1 Extract Lesson Metadata**

**File**: `backend/modules/content_creator/prompts/extract_lesson_metadata.md`
```markdown
## Learner Context

{{learner_desires}}

This context describes what the learner wants to achieve, their background,
preferences, and constraints. Use this to inform all decisions about content
depth, examples, tone, and focus areas.
```

### **14.2 Generate Comprehension Exercises**

**File**: `backend/modules/content_creator/prompts/generate_comprehension_questions.md`
```markdown
## Learner Context

{{learner_desires}}

Create comprehension exercises appropriate for this learner's level and preferences.
```

### **14.3 Generate Transfer Exercises**

**File**: `backend/modules/content_creator/prompts/generate_transfer_questions.md`
```markdown
## Learner Context

{{learner_desires}}

Create transfer exercises that apply to this learner's goals and context.
```

**What happens**:
- ✅ ALL generation steps receive `learner_desires`
- ✅ Exercises tailored to learner's level and preferences
- ✅ Content depth matches learner's background and goals

---

## 15. BACKEND: Unit Persistence - Coach LOs Stored

### **15.1 Save Unit with Coach LOs**

**File**: `backend/modules/content_creator/service/flow_handler.py` (lines 105-120)
```python
unit_learning_objectives: list[UnitLearningObjective] = []
for item in raw_unit_learning_objectives:
    if isinstance(item, UnitLearningObjective):
        unit_learning_objectives.append(item)
    elif isinstance(item, dict):
        payload = dict(item)
        raw_id = payload.get("id") or payload.get("lo_id")
        inferred_title = payload.get("title") or payload.get("short_title")
        if inferred_title is None:
            inferred_title = payload.get("description") or raw_id
        description = payload.get("description") or inferred_title
        payload.setdefault("id", str(raw_id))
        payload["title"] = str(inferred_title)
        payload["description"] = str(description)
        unit_learning_objectives.append(UnitLearningObjective.model_validate(payload))

# Save to database
await self.content.update_unit_metadata(
    unit_id=unit_id,
    title=final_title,
    learning_objectives=unit_learning_objectives,  # ✅ COACH LOS SAVED
    # ...
)
```

**What happens**:
- ✅ Unit learning objectives (from coach) are parsed and validated
- ✅ Stored in database exactly as coach provided (with IDs intact)
- ✅ Unit record has reference to coach's learning objectives

---

## 16. SUMMARY: Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ LEARNER INTERACTION                                             │
│ User sends message → Frontend sends to Backend                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LLM CALL                                                        │
│ Backend invokes LLM with conversation history                  │
│ LLM returns: learner_desires, unit_title, learning_objectives  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND RECEIVES & MAPS                                        │
│ Backend returns: learner_desires, unit_title, LOs              │
│ Frontend maps to session state (learnerDesires, etc.)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ UI DISPLAYS FINALIZED STATE                                     │
│ Shows: title, learning objectives, suggested lesson count      │
│ Shows: "Generate Unit" button                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LEARNER CLICKS GENERATE                                         │
│ Frontend guard validates ALL fields present                     │
│ Frontend sends: learnerDesires, unitTitle, LOs, targetCount    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND ROUTES                                                  │
│ Validates all required fields (Pydantic)                       │
│ Passes to service layer                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ SERVICE LAYER                                                   │
│ Creates unit record                                            │
│ Queues/runs flow handler with coach fields                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ FLOW HANDLER                                                    │
│ Receives: learner_desires, learning_objectives (from coach)    │
│ Passes to UnitCreationFlow with full context                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ UNIT CREATION FLOW                                              │
│ Step 1: Generate source material (with learner_desires)        │
│ Step 2: Extract metadata (passes coach LOs & learner_desires)  │
│ Result: Returns coach LOs unchanged                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LESSON GENERATION (for each lesson)                             │
│ Each lesson receives: learner_desires, learning_objective_ids  │
│ All exercises/concepts/quizzes generated with full context     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PERSISTENCE                                                     │
│ Unit saved with coach learning objectives intact               │
│ Lessons saved with all generated content                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Implementation Points

### ✅ Implemented Correctly

1. **learner_desires Field**
   - ✅ Coach generates it from conversation
   - ✅ Backend returns it in session state
   - ✅ **FIXED**: Frontend now maps it to session state (was missing)
   - ✅ Frontend guards require it before unit creation
   - ✅ Sent to backend in unit creation request

2. **Learning Objectives from Coach**
   - ✅ Coach generates them from conversation
   - ✅ Backend returns them in session state
   - ✅ Frontend displays them in UI
   - ✅ Frontend sends them in unit creation request
   - ✅ Backend flow receives them and preserves them (no regeneration)
   - ✅ Saved to database with coach's IDs intact

3. **Context Flow**
   - ✅ learner_desires flows through ALL generation steps
   - ✅ Exercises respect learner level and preferences
   - ✅ Content tailored to learner's goals

### ✅ Fixed Issue

- ✅ **Frontend now maps `learner_desires`** from API response to session state

---

## Conclusion

The end-to-end flow is now **fully functional**:

1. Learning coach conversation generates learner preferences
2. Backend returns complete session state with learner_desires
3. Frontend receives, maps, and stores all fields
4. UI displays finalized state to learner
5. Learner clicks "Generate" with all required fields present
6. Backend receives coach-driven request
7. Unit creation flow executes with full learner context
8. Coach learning objectives preserved throughout
9. Unit saved with coach LOs and all generated content
10. Learner receives generated unit with content tailored to their preferences
