# Quick Start Guide: JSON-Based Seed Data

## Overview

The seed data system has been refactored to use JSON files instead of hardcoded Python dictionaries. This makes it much easier to add, edit, and version control seed data.

## Directory Structure

```
backend/
├── seed_data/
│   ├── README.md              # Detailed structure documentation
│   ├── users.json             # User accounts (shared across all units)
│   └── units/
│       ├── _template.json     # Template for creating new units
│       ├── example-json-unit.json
│       └── your-unit.json     # Add your own units here
└── scripts/
    ├── create_seed_data.py    # Original script (still works)
    ├── create_seed_data_from_json.py  # NEW: JSON-based seeding
    └── export_seed_data.py    # Export current DB to JSON
```

## Usage

### 1. Create a New Unit

Copy the template and modify it:

```bash
cd backend/seed_data/units
cp _template.json my-new-unit.json
# Edit my-new-unit.json with your content
```

### 2. Seed a Specific Unit

```bash
cd backend
python scripts/create_seed_data_from_json.py --unit-file my-new-unit.json --verbose
```

### 3. Seed All Units

```bash
python scripts/create_seed_data_from_json.py --verbose
```

This will process all `*.json` files in `seed_data/units/` (except files starting with `_`).

### 4. Export Existing Data to JSON

If you already have units in the database and want to export them:

```bash
# Export all units
python scripts/export_seed_data.py --all-units

# Export specific unit
python scripts/export_seed_data.py --unit-id <uuid>

# Export users
python scripts/export_seed_data.py --users
```

## Benefits of the New System

1. **Easier to Edit**: JSON is more readable than Python dictionaries
2. **Better Version Control**: Diff tools work better with JSON
3. **Modular**: Each unit is a separate file
4. **Reusable**: Can share unit files across projects or with others
5. **No Code Changes**: Add new units without touching Python code

## JSON Structure Highlights

### Users (users.json)
```json
[
  {
    "key": "brian",
    "email": "user@example.com",
    "name": "User Name",
    "password": "password",
    "role": "admin"
  }
]
```

### Unit (units/my-unit.json)
```json
{
  "id": "uuid",
  "title": "Unit Title",
  "owner_key": "brian",
  "is_global": false,
  "lessons": [
    {
      "title": "Lesson Title",
      "objectives": [...],
      "glossary_terms": [...],
      "mini_lesson": "Content...",
      "mcqs": [...]
    }
  ]
}
```

See `seed_data/README.md` for the complete structure reference.

## Migration Note

The original `create_seed_data.py` script still works and contains the hardcoded units (Street Kittens, Gradient Descent, etc.). You can gradually migrate these to JSON files if desired, or keep using the original script for those units.

## Example

See `seed_data/units/example-json-unit.json` for a complete working example with all required fields.
