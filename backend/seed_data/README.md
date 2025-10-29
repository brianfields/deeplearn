# Seed Data JSON Structure

This directory contains JSON files used to seed the database with sample data.

## Structure

```
seed_data/
├── users.json              # User accounts
├── units/                  # Unit definitions
│   ├── street-kittens.json
│   ├── gradient-descent.json
│   └── first-aid.json
└── README.md              # This file
```

## Users (users.json)

Array of user objects with the following structure:

```json
[
  {
    "key": "unique-key",        // Used for referencing in unit owner_key
    "email": "user@example.com",
    "name": "User Name",
    "password": "password",     // Will be hashed during seed
    "role": "admin|learner"
  }
]
```

## Units (units/*.json)

Each unit JSON file contains:

```json
{
  "id": "uuid",                    // Unit UUID
  "title": "Unit Title",
  "description": "Description",
  "learner_level": "beginner|intermediate|advanced",
  "learning_objectives": [         // Array of objectives
    {
      "id": "lo_1",
      "title": "Objective title",
      "description": "Objective description",
      "bloom_level": "Remember|Understand|Apply|Analyze|..."
    }
  ],
  "target_lesson_count": 2,
  "source_material": "Optional source text",
  "generated_from_topic": true,
  "is_global": false,
  "owner_key": "brian",            // References key from users.json
  "podcast_transcript": "Transcript text...",
  "podcast_voice": "Plain|Narrative",
  "art_image": {                   // Optional
    "id": "uuid",
    "s3_key": "path/to/image.png",
    "filename": "image.png",
    "content_type": "image/png",
    "file_size": 1234,
    "width": 1024,
    "height": 1024,
    "alt_text": "Alt text",
    "description": "Image description"
  },
  "podcast_audio": {               // Optional
    "id": "uuid",
    "s3_key": "path/to/audio.mp3",
    "filename": "audio.mp3",
    "content_type": "audio/mpeg",
    "file_size": 4668000,
    "duration_seconds": 233.0,
    "bitrate_kbps": 128,
    "sample_rate_hz": 44100
  },
  "lessons": [
    {
      "id": "lesson-uuid",
      "title": "Lesson Title",
      "learner_level": "intermediate",
      "source_material": "Optional source",
      "objectives": [              // Subset of unit objectives
        {
          "id": "lo_1",
          "title": "Objective title",
          "description": "Description",
          "bloom_level": null
        }
      ],
      "glossary_terms": [
        {
          "term": "Term",
          "definition": "Definition"
        }
      ],
      "mini_lesson": "Lesson content text...",
      "mcqs": [
        {
          "stem": "Question text?",
          "options": [
            {
              "text": "Option A text",
              "rationale_wrong": "Why this is wrong (null for correct)"
            }
          ],
          "correct_index": 0,
          "cognitive_level": "Apply",
          "difficulty": "Medium",
          "misconceptions": ["MC1"],
          "correct_rationale": "Why this is correct"
        }
      ],
      "misconceptions": [
        {
          "id": "MC1",
          "misbelief": "Common misconception",
          "why_plausible": "Why it seems reasonable",
          "correction": "What's actually true"
        }
      ],
      "confusables": [
        {
          "a": "Term A",
          "b": "Term B",
          "contrast": "How they differ"
        }
      ]
    }
  ],
  "resources": [                   // Optional resources
    {
      "resource_id": "uuid",
      "resource_type": "file_upload|url",
      "filename": "file.txt",
      "source_url": null,
      "extracted_text": "Content...",
      "metadata": {},
      "file_size": 1234,
      "document": {                // For file_upload types
        "id": "uuid",
        "s3_key": "path/to/doc.txt",
        "filename": "doc.txt",
        "content_type": "text/plain",
        "file_size": 1234
      }
    }
  ]
}
```

## Adding New Seed Data

1. To add a new user: Edit `users.json` and add a new entry
2. To add a new unit: Create a new JSON file in `units/` following the structure above
3. Run: `python scripts/create_seed_data.py` to seed the database

## Exporting Current Data

To export current database data to JSON format:

```bash
# Export all units
python scripts/export_seed_data.py --all-units

# Export specific unit
python scripts/export_seed_data.py --unit-id <unit-uuid>

# Export users
python scripts/export_seed_data.py --users
```

