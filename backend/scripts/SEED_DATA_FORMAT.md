# Canonical Seed Data Format

## Overview

The seed data format is designed to be a **precise, lossless representation** of the database state. Files exported using `export_seed_data.py` can be directly re-imported using `create_seed_data.py` to recreate the exact same database state.

**Key principle:** The JSON structure matches the database models directly, with minimal transformation or interpretation.

---

## Structure

### Top-Level Unit File (`units/{unit-name}.json`)

Each unit file represents a complete unit with all related data:

```json
{
  "id": "unit-id-uuid",
  "title": "Unit Title",
  "description": "Unit description",
  "learner_level": "beginner",
  "learning_objectives": [
    {
      "id": "lo_1",
      "title": "Learning Objective",
      "description": "What students should learn"
    }
  ],
  "target_lesson_count": 5,
  "source_material": "Full source material text...",
  "generated_from_topic": true,
  "flow_type": "standard",
  "status": "completed",
  "is_global": false,
  "owner_key": "brian",
  "art_image_description": "Description of unit art",
  "art_image": { ... },
  "podcast_transcript": "Optional unit-level podcast transcript",
  "podcast_voice": "voice-id",
  "lessons": [ ... ],
  "resources": [ ... ],
  "learning_conversations": { ... }
}
```

### Lesson Records

Each lesson must include a **complete `package` field** (LessonPackage):

```json
{
  "id": "lesson-id",
  "title": "Lesson Title",
  "learner_level": "beginner",
  "lesson_type": "standard",
  "source_material": "Lesson-specific source material",
  "podcast_transcript": "Full podcast transcript for this lesson",
  "podcast_voice": "voice-id",
  "podcast_duration_seconds": 600,
  "podcast_generated_at": "2024-01-15T10:30:00",
  "podcast_audio_object_id": "uuid",
  "package": {
    "meta": {
      "lesson_id": "lesson-id",
      "title": "Lesson Title",
      "learner_level": "beginner",
      "package_schema_version": 2,
      "content_version": 1
    },
    "unit_learning_objective_ids": ["lo_1", "lo_2"],
    "exercise_bank": [
      {
        "id": "ex_1",
        "exercise_type": "mcq",
        "exercise_category": "comprehension",
        "stem": "Question text?",
        "cognitive_level": "Recall",
        "difficulty": "easy",
        "aligned_learning_objective": "lo_1",
        "options": [
          {
            "id": "opt_a",
            "label": "A",
            "text": "Option A text",
            "rationale_wrong": null
          }
        ],
        "answer_key": {
          "label": "A",
          "option_id": "opt_a",
          "rationale_right": "Explanation for correct answer"
        }
      }
    ],
    "quiz": ["ex_1", "ex_2"],
    "quiz_metadata": {
      "quiz_type": "formative_seed",
      "total_items": 2,
      "difficulty_distribution_target": { "easy": 0.5, "medium": 0.5, "hard": 0.0 },
      "difficulty_distribution_actual": { "easy": 0.5, "medium": 0.5, "hard": 0.0 },
      "cognitive_mix_target": { "Recall": 0.25, "Comprehension": 0.25, "Application": 0.25, "Transfer": 0.25 },
      "cognitive_mix_actual": { "Recall": 0.5, "Comprehension": 0.5, "Application": 0.0, "Transfer": 0.0 },
      "coverage_by_LO": {
        "lo_1": { "exercise_ids": ["ex_1"] }
      },
      "coverage_by_concept": {},
      "normalizations_applied": [],
      "selection_rationale": [],
      "gaps_identified": []
    }
  },
  "package_version": 1,
  "flow_run_id": "flow-run-uuid",
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:00:00",
  "flow_run": { ... },
  "step_runs": [ ... ],
  "llm_requests": [ ... ]
}
```

### Flow Runs

Optional flow run data (if the lesson was generated via a flow):

```json
{
  "id": "flow-run-uuid",
  "user_id": 1,
  "flow_name": "lesson_creation",
  "status": "completed",
  "execution_mode": "sync",
  "current_step": null,
  "step_progress": 3,
  "total_steps": 3,
  "progress_percentage": 100.0,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:30:00Z",
  "last_heartbeat": "2024-01-15T10:30:00Z",
  "total_tokens": 8420,
  "total_cost": 0.0415,
  "execution_time_ms": 30000,
  "inputs": { ... },
  "outputs": { ... },
  "flow_metadata": { ... },
  "error_message": null
}
```

### Step Runs

Optional step run data (workflow steps):

```json
{
  "id": "step-run-uuid",
  "flow_run_id": "flow-run-uuid",
  "llm_request_id": "llm-request-uuid",
  "step_name": "generate_lesson_podcast_transcript_instructional",
  "step_order": 1,
  "status": "completed",
  "inputs": { ... },
  "outputs": { ... },
  "tokens_used": 3200,
  "cost_estimate": 0.016,
  "execution_time_ms": 5200,
  "error_message": null,
  "step_metadata": { "prompt_file": "..." },
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z",
  "completed_at": "2024-01-15T10:05:00Z"
}
```

### LLM Requests

Optional LLM request data:

```json
{
  "id": "llm-request-uuid",
  "user_id": 1,
  "api_variant": "responses",
  "provider": "openai",
  "model": "gpt-4",
  "provider_response_id": "chatcmpl-...",
  "system_fingerprint": "fp_...",
  "temperature": 0.7,
  "max_output_tokens": 2000,
  "messages": [ ... ],
  "additional_params": {},
  "request_payload": { ... },
  "response_content": "JSON string of response",
  "response_raw": { ... },
  "tokens_used": 3200,
  "input_tokens": null,
  "output_tokens": null,
  "cost_estimate": 0.016,
  "status": "completed",
  "execution_time_ms": 5200,
  "error_message": null,
  "error_type": null,
  "retry_attempt": 1,
  "cached": false,
  "response_created_at": "2024-01-15T10:05:00Z",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:05:00Z"
}
```

### Resources

Optional unit-level resources:

```json
{
  "id": "resource-uuid",
  "user_id": 1,
  "resource_type": "article",
  "filename": "document.pdf",
  "source_url": "https://example.com/document.pdf",
  "extracted_text": "Full extracted text from document",
  "extraction_metadata": { ... },
  "file_size": 1024000,
  "object_store_document_id": "doc-uuid",
  "object_store_image_id": "image-uuid",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "document": { ... },
  "image": { ... }
}
```

### Learning Conversations

Optional conversations (both learning coach and teaching assistant):

```json
{
  "learning_conversations": {
    "coach": [
      {
        "id": "conversation-uuid",
        "user_id": 1,
        "conversation_type": "learning_coach",
        "title": "Conversation Title",
        "status": "active",
        "conversation_metadata": { ... },
        "message_count": 3,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "last_message_at": "2024-01-15T10:30:00Z",
        "messages": [
          {
            "conversation_id": "conversation-uuid",
            "role": "user",
            "content": "User message",
            "message_order": 1,
            "llm_request_id": null,
            "tokens_used": 10,
            "cost_estimate": 0.0001,
            "message_metadata": { ... },
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
          }
        ]
      }
    ],
    "assistant": [ ... ]
  }
}
```

---

## Important Notes

### Package Field

The `package` field is **required** for every lesson. It contains the complete `LessonPackage` structure with:
- `exercise_bank`: Full list of all exercises (with options, answer keys, etc.)
- `quiz`: IDs of exercises included in the quiz
- `quiz_metadata`: Comprehensive metadata about the quiz

**No interpretation or transformation** is performed on the package during import—it is deserialized directly.

### Datetime Format

All datetime fields use **ISO 8601 format** (e.g., `"2024-01-15T10:30:00Z"` or `"2024-01-15T10:30:00"`).

The import script automatically parses these using Python's `datetime.fromisoformat()`.

### UUIDs and IDs

- All ID fields are strings (UUIDs are stored as string representations)
- If an ID is missing, a new UUID is auto-generated during import
- The `owner_key` field (e.g., `"brian"`) maps to the user's email via the `users.json` file

### Flow Metadata

If a lesson has associated flow runs, step runs, and LLM requests:
- They are stored inline in the lesson JSON
- The import script reconstructs relationships via foreign keys
- The `flow_run_id` on the lesson must match the `id` in the `flow_run` object

---

## Export and Import Workflow

### Export (Current State → JSON)

```bash
python backend/scripts/export_seed_data.py --all-units --output-dir backend/seed_data
python backend/scripts/export_seed_data.py --users
```

This creates:
- `backend/seed_data/users.json` — User records
- `backend/seed_data/units/{unit-name}.json` — Full unit records with all related data

### Import (JSON → Database)

```bash
python backend/scripts/create_seed_data.py --verbose
```

This:
1. Loads all users from `seed_data/users.json`
2. Loads all unit JSON files from `seed_data/units/`
3. Deserializes each directly into ORM objects
4. Creates all relationships (lessons, resources, conversations, etc.)

### Round-Trip

The format ensures:
```
Database State A → export → JSON → import → Database State A (identical)
```

No information is lost; the JSON is an exact mirror of the database.

---

## Best Practices

1. **Always include the full `package` field** for every lesson. The package validation ensures referential integrity.
2. **Use `owner_key` for ownership** — map emails in `users.json` to reduce hardcoding.
3. **Datetimes are serialized as ISO 8601** — respect the format to ensure smooth import.
4. **Export and re-import to validate** — if export → import produces different JSON, there's a schema mismatch to fix.
5. **Keep flow/step/LLM data alongside lessons** — they provide full traceability of how lessons were generated.

---

## Troubleshooting

### "Package validation failed"
The lesson's `package` field is missing or invalid. Ensure:
- All exercises have valid `aligned_learning_objective` IDs
- All quiz IDs reference exercises in `exercise_bank`
- `quiz_metadata.total_items` matches the length of `quiz`

### "Unknown owner_key"
The `owner_key` in the unit JSON (e.g., `"brian"`) doesn't have a matching user in `users.json`. Check that the user's email matches the `email_to_key` mapping, or add the user to `users.json`.

### "Datetime parsing error"
Ensure all datetime fields are in ISO 8601 format: `"2024-01-15T10:30:00Z"` or `"2024-01-15T10:30:00+00:00"`.

