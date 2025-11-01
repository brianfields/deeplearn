# Seed Data: Learning Coach and Teaching Assistant Conversations

## Overview

The seed data system has been updated to support both **Learning Coach** and **Teaching Assistant** conversations. After running the seed data script, the database will contain sample conversations of both types, allowing admins and developers to see them in the admin dashboard.

## Changes Made

### 1. Seed Script Updates (`backend/scripts/create_seed_data_from_json.py`)

**Key Changes:**
- Added support for `learning_conversations.assistant` section (previously only `coach` existed)
- Both conversation types now properly set `conversation_type` field:
  - Learning Coach conversations: `conversation_type = "learning_coach"`
  - Teaching Assistant conversations: `conversation_type = "teaching_assistant"`
- Conversations are seeded with realistic multi-turn message exchanges
- Both types preserve user messages with timestamps (via `offset_seconds`)

**Processing Flow:**
```
Unit JSON
├── learning_conversations.coach[]
│   └── Creates ConversationModel with type="learning_coach"
│       ├── Metadata with "topic" field (distinguishes from assistant)
│       └── Multiple messages with roles: user, assistant
└── learning_conversations.assistant[]
    └── Creates ConversationModel with type="teaching_assistant"
        ├── Generic metadata (no "topic" field)
        └── Multiple messages with roles: user, assistant
```

### 2. Seed Data Files Updated

#### Gradient Descent Mastery Unit
- **Coach Conversation**: "Understanding learning rate selection"
  - Discussion about learning rate selection and convergence
  - Includes practical advice on debugging convergence issues
- **Assistant Conversation**: "Mini-batch vs batch gradient descent clarification"
  - Quick Q&A about batch sizes and practical recommendations

#### Street Kittens of Istanbul Unit
- **Coach Conversation**: "Seasonality in kitten colonies"
  - Discussion of seasonal variation and TNR timing
  - Practical planning advice
- **Assistant Conversation**: "Triage prioritization and kitten age assessment"
  - Field techniques for quick assessment
  - Age estimation methods

### 3. Template Updated (`backend/seed_data/units/_template.json`)

Now includes a complete `learning_conversations` section demonstrating both types:

```json
{
  "learning_conversations": {
    "coach": [
      {
        "id": "uuid",
        "user_key": "brian",
        "title": "Conversation title",
        "status": "active",
        "metadata": {
          "topic": "Unit topic (distinguishes as learning_coach)"
        },
        "resource_ids": [],
        "messages": [
          {
            "role": "user",
            "content": "Question text",
            "offset_seconds": 0
          },
          {
            "role": "assistant",
            "content": "Answer text",
            "offset_seconds": 5
          }
        ]
      }
    ],
    "assistant": [
      {
        "id": "uuid",
        "user_key": "brian",
        "title": "Teaching assistant help",
        "status": "active",
        "metadata": {},
        "messages": [
          {
            "role": "user",
            "content": "Question",
            "offset_seconds": 0
          },
          {
            "role": "assistant",
            "content": "Response",
            "offset_seconds": 3
          }
        ]
      }
    ]
  }
}
```

## How to Create Custom Conversations in Seed Data

### 1. Basic Structure

Add a `learning_conversations` section to your unit JSON:

```json
{
  "title": "Your Unit",
  "...other fields...": "...",
  "learning_conversations": {
    "coach": [ /* coach conversations */ ],
    "assistant": [ /* assistant conversations */ ]
  }
}
```

### 2. Learning Coach Conversations

Include a `metadata.topic` field to distinguish from teaching assistant:

```json
{
  "id": "unique-uuid",
  "user_key": "brian",
  "title": "Descriptive title",
  "status": "active",
  "metadata": {
    "topic": "Your unit's main topic",
    "custom_field": "optional custom metadata"
  },
  "resource_ids": ["optional-resource-ids"],
  "messages": [
    {
      "role": "user",
      "content": "User's question",
      "offset_seconds": 0
    },
    {
      "role": "assistant",
      "content": "Coach's response",
      "offset_seconds": 5
    }
  ]
}
```

### 3. Teaching Assistant Conversations

Omit the `topic` from metadata to mark as teaching assistant:

```json
{
  "id": "unique-uuid",
  "user_key": "brian",
  "title": "Assistant help topic",
  "status": "active",
  "metadata": {
    "custom_field": "optional"
  },
  "messages": [
    {
      "role": "user",
      "content": "Question",
      "offset_seconds": 0
    },
    {
      "role": "assistant",
      "content": "Answer",
      "offset_seconds": 2
    }
  ]
}
```

## Running Seed Data

```bash
# Seed all units
python backend/scripts/create_seed_data_from_json.py --verbose

# Seed specific unit
python backend/scripts/create_seed_data_from_json.py --unit-file street-kittens-of-istanbul.json --verbose
```

**Output includes:**
```
📦 Processing unit: Gradient Descent Mastery
   • Seeded learning coach conversation: Understanding learning rate selection
   • Seeded teaching assistant conversation: Mini-batch vs batch gradient descent clarification
```

## Verification in Admin Dashboard

After seeding, navigate to the admin dashboard:

### Conversations Tab
- View both conversation types mixed together
- Filter by type if needed
- Each shows a type badge: 🔵 Coach or 🟣 Assistant

### User Detail Page
- "Recent conversations" section shows both types
- Sorted by recency
- Type badges distinguish between them

## Conversation Type Detection

The system automatically detects conversation type based on metadata:

| Condition | Type | Detection |
|-----------|------|-----------|
| `metadata.topic` present | Learning Coach | Has "topic" field |
| No `topic` field | Teaching Assistant | Lacks "topic" field |

This is how the backend distinguishes them and how the admin dashboard's type badges work.

## Short Answer Questions Support

✅ **Already fully supported** in seed data JSON format, matching the non-JSON version:

```json
{
  "short_answers": [
    {
      "stem": "Question prompt",
      "canonical_answer": "Primary correct answer",
      "acceptable_answers": ["Alternative correct answer"],
      "wrong_answers": [
        {
          "answer": "Common misconception",
          "explanation": "Why this is wrong",
          "misconception_ids": ["misconception_id"]
        }
      ],
      "explanation_correct": "Feedback for correct answer",
      "learning_objectives_covered": ["lo_id"],
      "cognitive_level": "Apply"
    }
  ]
}
```

All three seed data units contain short answer questions properly formatted.

## Database Schema

When conversations are seeded, they create:

1. **ConversationModel** entries:
   - `id`: UUID
   - `user_id`: Associated learner
   - `conversation_type`: "learning_coach" | "teaching_assistant"
   - `title`: Display name
   - `status`: "active" (default)
   - `conversation_metadata`: JSON metadata
   - `message_count`: Number of messages
   - `created_at`, `updated_at`, `last_message_at`: Timestamps

2. **ConversationMessageModel** entries:
   - One per message in the conversation
   - `role`: "user" | "assistant" | "system"
   - `content`: Message text
   - `message_order`: Sequence in conversation
   - `tokens_used`, `cost_estimate`: Optional LLM metrics
   - `message_metadata`: Optional custom data

## Legacy Compatibility

The seed script supports the old `learning_coach_conversations` key for backward compatibility:

```json
{
  "learning_coach_conversations": [ /* old format */ ]
  // Will be mapped to: learning_conversations.coach
}
```

However, new seed data should use the `learning_conversations.coach` format.

## Future Enhancements

- Add sample teaching assistant conversations that demonstrate context-aware responses (unit/lesson-specific)
- Include resource references in conversation metadata
- Add mock LLM request IDs for cost tracking examples
- Create more diverse conversation types across units
