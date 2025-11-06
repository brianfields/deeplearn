# Learning Coach → Backend Unit Generation Investigation

## Summary

The learning coach collects conversation data and sends a **hardcoded** unit generation request to the backend. The approach is **overly simplified** and doesn't fully leverage the conversation context it has gathered.

---

## What the Learning Coach Sends

### Request Data Structure (Mobile → Backend)

When the learner clicks "Create Unit" from the learning coach screen, the app sends a `POST` to `/api/v1/content-creator/units` with this payload:

```json
{
  "topic": "string",
  "difficulty": "string",  // "beginner" | "intermediate" | "advanced"
  "unitTitle": "string | null",
  "targetLessonCount": "number | null",
  "conversationId": "string | null",
  "ownerUserId": "number | null"
}
```

**Source**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (lines 316–325)

```typescript
createUnit.mutate(
  {
    topic: sessionState.finalizedTopic ?? '',
    difficulty: 'intermediate',  // ← HARDCODED!
    unitTitle: sessionState.unitTitle ?? undefined,
    targetLessonCount: sessionState.suggestedLessonCount ?? undefined,
    ownerUserId: user?.id ?? undefined,
    conversationId: conversationId ?? undefined,
  },
  {
    onError: error => {
      console.error('Failed to create unit from finalized topic', error);
    },
  }
);
```

---

## How the Backend Uses These Fields

### Backend Route: `POST /api/v1/content-creator/units`

**File**: `backend/modules/content_creator/routes.py` (lines 58–93)

The route receives `MobileUnitCreateRequest`:

```python
class MobileUnitCreateRequest(BaseModel):
    """Request to create a unit from mobile app."""
    topic: str
    difficulty: str = "beginner"
    unit_title: str | None = None
    target_lesson_count: int | None = None
    conversation_id: str | None = None
```

It then calls the service:

```python
result = await service.create_unit(
    topic=request.topic,
    learner_level=request.difficulty,
    unit_title=request.unit_title,
    target_lesson_count=request.target_lesson_count,
    background=True,
    user_id=user_id,
    conversation_id=request.conversation_id,
)
```

**Key mapping:**
- `difficulty` → `learner_level` (used in the flow)
- `conversation_id` is passed through for context enrichment

---

## Backend Service Logic: `ContentCreatorService.create_unit()`

**File**: `backend/modules/content_creator/service/facade.py` (lines 94–190)

### Field Determination Strategy

| Field | Source | Approach |
|-------|--------|----------|
| **topic** | Mobile request | Passed directly from `finalizedTopic` or user input |
| **learner_level** | Mobile request | Sent as `difficulty` (hardcoded to `'intermediate'` from mobile) |
| **unit_title** | Mobile request | From `sessionState.unitTitle` (set by coach) |
| **target_lesson_count** | Mobile request | From `sessionState.suggestedLessonCount` (suggested by coach) |
| **source_material** | Conversation resources OR generated | If `conversation_id` provided, fetches learner-uploaded resources; otherwise `None` |
| **conversation_id** | Mobile request | Links unit back to the learning coach session |

### Smart Behavior When `conversation_id` is Present

When a `conversation_id` is provided, the service does the following (lines 116–137):

1. **Fetches conversation resources** (learner-uploaded materials)
   - Combines resource texts up to 200KB

2. **Fetches uncovered learning objective IDs** from conversation metadata
   - These are objectives identified by the coach as needing material

3. **Generates supplemental source material** if:
   - Resources are available AND
   - Uncovered learning objectives exist AND
   - Session state has learning objectives defined

4. **Combines everything** into `combined_source_material`:
   ```
   ## Learner-Provided Materials
   [resource content]

   ## Supplemental Generated Content
   [LLM-generated material for uncovered LOs]
   ```

This combined material is then passed to the unit creation flow.

---

## Data Flow Diagram

```
LearningCoachScreen
├─ sessionState.finalizedTopic          ─┐
├─ sessionState.unitTitle               ─┼─→ createUnit.mutate()
├─ sessionState.suggestedLessonCount    ─┤   (hardcoded difficulty = 'intermediate')
├─ conversationId                       ─┘
└─ user?.id

                ↓
         Backend Route
    POST /api/v1/content-creator/units

                ↓
    ContentCreatorService.create_unit()

    ┌───────────────────────────────────┐
    │ If conversation_id provided:      │
    ├───────────────────────────────────┤
    │ • Fetch conversation resources    │
    │ • Fetch uncovered LO IDs          │
    │ • Generate supplemental content   │
    │ • Combine into source_material    │
    └───────────────────────────────────┘

                ↓
    UnitCreationFlow
    ├─ topic
    ├─ learner_level
    ├─ target_lesson_count
    ├─ source_material (enriched)
    └─ unit_title
```

---

## Critical Issues

### 1. **Difficulty is Hardcoded**
The mobile app **always** sends `difficulty: 'intermediate'` regardless of what the learning coach conversation determined.

**File**: `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` (line 319)

```typescript
difficulty: 'intermediate',  // ← Always this!
```

**Problem**: The learning coach's `sessionState` has enough context to infer difficulty:
- `learningObjectives` (complexity of LOs)
- `proposedBrief` (explicit scope/depth)
- Conversation history

But none of this is used.

### 2. **Limited Metadata Sent**
The mobile app only sends:
- `topic`
- `difficulty`
- `unitTitle`
- `targetLessonCount`
- `conversationId`

**Missing from the request:**
- Learning objectives (coach has these in `sessionState.learning_objectives`)
- Unit description (coach has this in `proposedBrief.description`)
- Proposed brief metadata (coach has this in `sessionState.proposedBrief`)
- Resources/materials uploaded

The backend then **re-fetches** these from the conversation store (lines 117–118 of `facade.py`).

### 3. **Inefficiency: Metadata Duplication**
- Mobile app has `sessionState` with all coach-derived metadata
- Mobile app **only sends** `topic`, `difficulty`, `unitTitle`, `targetLessonCount`
- Backend receives request → **re-queries** the conversation store to get everything else
- Backend fetches: resources, uncovered LO IDs, session state

This round-trip is necessary but could be optimized by sending this data in the initial request.

---

## What **Should** Go into Request (Not Currently Done)

Based on the learning coach's capabilities, the request could include:

```typescript
{
  topic: string;
  difficulty: string;  // Inferred from LOs, not hardcoded
  unitTitle: string | null;
  targetLessonCount: number | null;

  // NEW: Coach-derived metadata
  learningObjectives: Array<{id, title, description}>;
  unitDescription: string;  // From proposedBrief.description
  proposedBrief: {
    title: string;
    description: string;
    objectives: string[];
    notes: string;
  };

  conversationId: string | null;  // For traceability
}
```

---

## Current Approach Summary

**The learning coach is a "decision maker" that narrows options but doesn't fully communicate its reasoning to the backend.**

- ✅ Coach gathers requirements via conversation
- ✅ Coach extracts: title, objectives, lesson count
- ❌ Difficulty is hardcoded by mobile UI, not derived from coach insights
- ❌ Metadata is not sent; backend re-fetches it
- ✅ Backend enriches with resources when `conversation_id` provided

This works but is **suboptimal**:
1. Wastes work re-fetching conversation context
2. Ignores coach's ability to infer difficulty
3. Creates dependency on conversation store being available at unit creation time

---

## Files Involved

| File | Role |
|------|------|
| `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx` | Collects session state and initiates unit creation (hardcoded difficulty) |
| `backend/modules/content_creator/routes.py` | HTTP route that receives `MobileUnitCreateRequest` |
| `backend/modules/content_creator/service/facade.py` | Main service logic that enriches request with conversation resources |
| `backend/modules/learning_conversations/service.py` | Provides conversation context (resources, objectives, session state) |

---

## Recommendations for Future Work

1. **Stop hardcoding difficulty**: Extract from learning objectives complexity or accept it from the request
2. **Send richer metadata**: Include LOs, description, proposed brief in the initial request
3. **Make conversation enrichment optional**: The backend should not fail if conversation_id is unavailable
4. **Document the decision** of what "learner_level" (difficulty) actually represents in the context of coach-derived units
