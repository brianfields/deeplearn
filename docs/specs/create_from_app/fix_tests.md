# Test Fixes for create_from_app

## 2025-09-21

**Files Changed:** backend/modules/content_creator/test_fast_flow_unit.py

**Test:** TestServiceFastFlag.test_create_unit_sets_flow_type_and_parallelizes

**SUT:** ContentCreatorService.create_lesson_from_source_material

**Rationale:** The mock function for create_lesson_from_source_material had a parameter named '_use_fast_flow' but the actual method signature uses 'use_fast_flow'. Since the method call uses keyword arguments, the names must match exactly. Changed the mock parameter name to 'use_fast_flow' to fix the TypeError and ensure lesson creation succeeds, allowing the assertion on assign_lessons_to_unit to pass.