# Redo Exercise Generation - Specification Complete

## Artifacts Created

1. **`user_description.md`** - Original feature request
2. **`codebase_understanding.md`** - Survey of existing architecture
3. **`user_story.md`** - Complete user story with acceptance criteria
4. **`module_changes_proposal.md`** - Detailed module-by-module breakdown
5. **`spec.md`** - **Complete implementation specification** ✅

## Spec Overview

### Structure
- **User Story**: Clear as-a/I-want/so-that format with acceptance criteria
- **Requirements Summary**: What to build, constraints, high-level acceptance criteria
- **Cross-Stack Module Mapping**: Backend, mobile, and admin module changes
- **Implementation Checklist**: 10 phases, ~85 concrete tasks with GitHub-style checkboxes

### Implementation Phases

1. **Phase 1: Backend - Prompt Updates** (6 tasks)
   - Update `extract_lesson_metadata.md`
   - Create/update 5 new exercise generation prompts

2. **Phase 2: Backend - Models and Steps** (4 tasks)
   - Update package models in `content` module
   - Add 5 new step classes in `content_creator`
   - Update lesson creation flow
   - Update service to build new lesson packages

3. **Phase 3: Backend - Learning Session Updates** (2 tasks)
   - Update service to extract exercises from quiz
   - Update tests

4. **Phase 4: Backend - Tests** (2 tasks)
   - Update content_creator tests
   - Update content tests

5. **Phase 5: Database Migration** (2 tasks)
   - Generate migration (no-op for schema)
   - Run migration

6. **Phase 6: Frontend (Mobile) - Models and Services** (7 tasks)
   - Update content module models/service
   - Update learning_session module models/service/components
   - Add specific wrong answer rationale display

7. **Phase 7: Frontend (Admin) - Content Review Components** (6 tasks)
   - Update admin models/service
   - Create 4 new view components (ConceptGlossary, ExerciseBank, QuizStructure, QuizMetadata)
   - Update lesson detail page

8. **Phase 8: Seed Data Updates** (1 task)
   - Update seed data script

9. **Phase 9: Integration Testing and Fixes** (2 tasks)
   - Update backend integration tests
   - Fix mobile Maestro tests

10. **Phase 10: Verification and Cleanup** (8 tasks)
    - Lint, unit tests, integration tests
    - Trace user story
    - Module architecture check
    - Remove dead code

### Key Design Decisions

1. **Zero new modules** - All changes within existing vertical slices
2. **6 modules modified**: 3 backend, 2 mobile, 1 admin
3. **Single learning objective per exercise** (simplified from list)
4. **Quiz as ordered IDs** (not full exercise objects)
5. **Exercise bank stores all** (comprehension + transfer)
6. **Concept glossary at lesson level** (not unit level)
7. **No backward compatibility** (all lessons regenerated)
8. **Admin views read-only** (no editing UI)

### Module Changes Summary

| Module | Type | Key Changes |
|--------|------|-------------|
| `backend/modules/content_creator/` | Modify | 5-step exercise generation pipeline |
| `backend/modules/content/` | Modify | New package models (concept_glossary, exercise_bank, quiz, quiz_metadata) |
| `backend/modules/learning_session/` | Modify | Quiz-based exercise extraction, single LO tracking |
| `mobile/modules/content/` | Modify | New package structure DTOs |
| `mobile/modules/learning_session/` | Modify | Quiz-based display, specific wrong answer feedback |
| `admin/modules/admin/` | Modify | 4 new content review components |

## Next Steps

The spec is ready for implementation. The checklist format allows for:
- Incremental progress tracking
- Clear accountability per task
- Easy identification of blockers
- Phase-by-phase completion

### Implementation Order
Follow the phases sequentially:
1. Backend prompts → models → flow → tests
2. Database migration
3. Frontend mobile → admin
4. Seed data
5. Integration testing
6. Verification

Each checkbox can be marked complete as work progresses.

## Notes

- All prompt files need "question" → "exercise" terminology changes
- All prompts need lesson-scoped inputs (lesson_source_material, lesson_learning_objectives, lesson_objective)
- Exercise model unifies MCQ and ShortAnswer with discriminated union on exercise_type
- Quiz metadata provides transparency for content quality review
- Mobile UI changes are minimal (curated quiz order, specific wrong answer rationales)
- Admin gets full visibility into generation artifacts

---

**Specification Status: ✅ COMPLETE AND READY FOR IMPLEMENTATION**
