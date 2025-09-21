## Fix Log for Fast Flow Tests

### 2025-09-21 - TestServiceFastFlag.test_create_unit_sets_flow_type_and_parallelizes

**Files Changed:**
- backend/modules/content_creator/test_fast_flow_unit.py (parameter name in mock function)

**Test vs SUT:**
- Test: Mock function `fake_create_lesson` had incorrect parameter name `_use_fast_flow` instead of `use_fast_flow`
- SUT: `ContentCreatorService.create_lesson_from_source_material` uses keyword argument `use_fast_flow`

**Rationale:**
- The TypeError occurred because the mock didn't accept the `use_fast_flow` keyword argument, causing lesson creation to fail and preventing `assign_lessons_to_unit` from being called.
- Changed the mock parameter name to match the actual method signature, ensuring the test runs correctly and verifies the behavior.