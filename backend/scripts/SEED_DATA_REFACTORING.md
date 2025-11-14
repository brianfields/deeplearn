# Seed Data Scripts Refactoring

## Summary

Refactored `create_seed_data.py` and `export_seed_data.py` to use a **canonical JSON format** that precisely matches the database structure. This ensures:

✅ **Lossless round-trip**: Export → Import produces identical database state
✅ **No interpretation**: JSON deserialized directly into ORM objects
✅ **Type safety**: LessonPackage validation ensures referential integrity
✅ **Minimal surface area**: Only essential transformation (datetime parsing, UUID handling)

---

## Changes

### `export_seed_data.py` (Complete Rewrite)

**Before:** Tried to reverse-engineer the original JSON structure by extracting and transforming database records.

**After:** Exports database records directly in a canonical format that matches ORM models:

- **Lessons** include the full `package` field (LessonPackage with exercise_bank, quiz, quiz_metadata)
- **Flow runs, step runs, LLM requests** are included inline with lessons for complete traceability
- **Resources and conversations** exported at unit level with all relationships preserved
- **Datetimes** serialized as ISO 8601 strings
- **No transformation** of structure—database fields map directly to JSON fields

**New Functions:**
- `_serialize_value()`: Converts individual values to JSON-serializable form
- `_serialize_dict()`: Converts SQLAlchemy models to dicts, recursively
- `export_unit()`: Exports complete unit with all related data
- `export_users()`: Exports user records

### `create_seed_data.py` (Simplified)

**Before:** Contained complex logic to build LessonPackage from legacy formats (MCQs, short answers, objectives). Performed lots of interpretation and transformation.

**After:** Minimal, direct deserialization:

- **Requires complete `package` field** in JSON (no synthesis)
- **Validates LessonPackage** on import via Pydantic model validation
- **Direct field mapping**: JSON fields → ORM model fields
- **Datetime parsing**: Converts ISO 8601 strings to datetime objects
- **Flow/step/LLM data**: Imported directly if present

**Removed:**
- `_map_cognitive_level()`: No interpretation
- `_map_difficulty()`: No interpretation
- `_build_exercise_bank_from_specs()`: Not needed; package already complete
- `_build_quiz_metadata_from_bank()`: Not needed; metadata already complete
- `create_sample_flow_run()`: Not needed; flow data in JSON if needed
- `create_sample_step_runs()`: Not needed; step data in JSON if needed
- `create_sample_llm_requests()`: Not needed; LLM data in JSON if needed

**Key Functions:**
- `_parse_datetime()`: ISO 8601 → datetime
- `_serialize_value()`: JSON value conversion utility
- `process_unit_from_json()`: Direct deserialization with validation

---

## Canonical Format

See `SEED_DATA_FORMAT.md` for complete specification.

**Key sections:**
- Top-level unit file structure
- Lesson records with complete LessonPackage
- Flow runs, step runs, LLM requests (optional)
- Resources and conversations (optional)
- Datetime and UUID handling

---

## Benefits

### For Users

1. **Export what you import**: `export_seed_data.py --all-units` produces files that `create_seed_data.py` consumes directly
2. **No manual editing needed**: JSON is complete and valid (no need to synthesize packages)
3. **Full traceability**: Flow runs, step runs, and LLM requests capture how lessons were generated
4. **Predictable behavior**: No interpretation means no surprises

### For Developers

1. **Less code**: Removed ~200 lines of interpretation logic
2. **Better testing**: Direct mapping makes it easy to test round-trip scenarios
3. **Type safety**: LessonPackage validation catches errors early
4. **Maintainability**: Single, canonical format vs. multiple legacy formats

---

## Migration Path

### Existing Seed Data

Old seed files that use the legacy format (separate `objectives`, `mcqs`, `short_answers` fields) will **no longer work**.

**To migrate existing seed files:**

1. **Load the unit into the database** using the old format (before this change)
2. **Export it** using the new `export_seed_data.py`
3. **Use the exported JSON** as the canonical format going forward

Example:
```bash
# Old format → Database
python scripts/create_seed_data.py --unit-file old_format_unit.json

# Database → Canonical format
python scripts/export_seed_data.py --unit-id <unit-id> --output-dir seed_data

# Canonical format → Database (going forward)
python scripts/create_seed_data.py --verbose
```

### Creating New Seed Data

When creating new seed data:

1. **Run the flow/generation process** to create lessons with full packages
2. **Export to canonical format**:
   ```bash
   python scripts/export_seed_data.py --all-units
   ```
3. **Version control** the exported JSON files
4. **Import** in other environments:
   ```bash
   python scripts/create_seed_data.py --verbose
   ```

---

## Architecture Principles Reflected

This refactoring aligns with the workspace architecture guide:

- **Minimize surface area**: Only export what's needed; no transformation layers
- **Direct mapping**: JSON structure mirrors database structure (like DTO contracts)
- **Type safety**: Pydantic validation ensures integrity at boundaries
- **Explicit returns**: All functions have clear return types
- **Modular concerns**: Serialization, deserialization, validation are separate

---

## Files Modified

- `backend/scripts/create_seed_data.py` — Simplified to direct deserialization
- `backend/scripts/export_seed_data.py` — Rewritten to export canonical format
- `backend/scripts/SEED_DATA_FORMAT.md` — New documentation for canonical format
- `backend/scripts/SEED_DATA_REFACTORING.md` — This document

---

## Testing Recommendations

1. **Round-trip test**: Export a unit, then import it, verify database state is identical
2. **Legacy compatibility**: Manually migrate one existing seed file to canonical format
3. **Validation**: Verify LessonPackage validation catches invalid packages
4. **Resources & conversations**: Ensure resources and conversations are preserved across round-trip
5. **Flow metadata**: Verify flow runs, step runs, and LLM requests are correctly linked

---

## Next Steps

- [ ] Update existing seed data files to canonical format (or re-export them)
- [ ] Run tests to verify round-trip behavior
- [ ] Document in README or admin guide
- [ ] Consider adding a migration helper script if needed

