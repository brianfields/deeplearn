# Fast Flow Implementation Spec

## User Story

**As a** content creator using the system
**I want** a faster content creation option that produces the same quality lessons and units
**So that** I can generate educational content more efficiently without sacrificing quality

## Requirements Summary

### What to Build
Implement a fast flow alternative to the existing content creation pipeline that:
- Reduces LLM calls from 4 to 2 per lesson (combine metadata/misconceptions/didactic into single step)
- Creates lessons in parallel during unit creation (instead of sequentially)
- Maintains identical data models and quality as existing implementation
- Provides opt-in access via `use_fast_flow=True` parameter

### Constraints
- Must produce identical lesson and unit data models as current implementation
- Must maintain existing public interfaces (backward compatible)
- Must use existing error handling and retry mechanisms from flow engine
- Must track which flow type was used for each unit
- Parallel lesson creation batch size controlled by constant

### Acceptance Criteria
- [x] Fast flow reduces content creation time through optimized LLM usage and parallelization
- [x] Users can choose between standard and fast flows via `use_fast_flow` parameter
- [x] Unit model tracks which approach was used (`flow_type` field)
- [x] Admin interface displays the flow type used for each unit
- [x] Failed lessons during parallel creation don't fail the entire unit
- [x] Error handling and retry logic matches existing implementation standards

## Cross-Stack Functionality Mapping

### Backend Changes

#### content/ module
**Files to modify:**
- `models.py`: Add `flow_type` column to `UnitModel`
- `service.py`: Add `flow_type` field to `UnitRead` and `UnitCreate` DTOs

#### content_creator/ module
**Files to modify:**
- `service.py`: Add `use_fast_flow` parameter logic and parallel lesson creation
- `flows.py`: Add `FastLessonCreationFlow` and `FastUnitCreationFlow` classes
- `steps.py`: Add `FastLessonMetadataStep` that combines metadata, misconceptions, and didactic content

**Files to create:**
- `prompts/fast_lesson_metadata.md`: Combined prompt template

### Frontend Changes

#### admin/ module
**Files to modify:**
- `modules/admin/components/units/`: Update unit display components to show flow type

### Database Changes
- Migration to add `flow_type` column to units table

## Implementation Checklist

### Backend Tasks

#### content/ module updates
- [x] Add `flow_type` field to `UnitModel` in `models.py`
- [x] Add `flow_type` field to `UnitRead` DTO in `service.py`
- [x] Add `flow_type` field to `UnitCreate` DTO in `service.py`

#### Database Migration
- [x] Create Alembic migration to add `flow_type` column to units table (nullable initially, default 'standard')

#### content_creator/ module implementation
- [x] Add `MAX_PARALLEL_LESSONS = 4` constant in `service.py`
- [x] Add `use_fast_flow: bool = False` parameter to `create_lesson_from_source_material` method
- [x] Add `use_fast_flow: bool = False` parameter to `create_unit_from_topic` method
- [x] Add `use_fast_flow: bool = False` parameter to `create_unit_from_source_material` method
- [x] Implement routing logic in service methods to choose between regular and fast flows
- [x] Create `FastLessonMetadataStep` class in `steps.py` that combines metadata extraction, misconceptions, and didactic generation
- [x] Create combined prompt template at `prompts/fast_lesson_metadata.md`
- [x] Create `FastLessonCreationFlow` class in `flows.py` that uses the combined step + existing MCQ step
- [x] Create `FastUnitCreationFlow` class in `flows.py` that creates lessons in parallel batches
- [x] Update unit creation methods to set `flow_type` field based on `use_fast_flow` parameter
- [x] Implement parallel lesson creation with batch size limit and error handling for partial failures

#### Backend Tests
- [x] Add unit tests for `FastLessonMetadataStep` to verify combined output format
- [x] Add unit tests for `FastLessonCreationFlow` to verify same output as standard flow
- [x] Add unit tests for `FastUnitCreationFlow` to verify parallel execution and error handling
- [x] Add unit tests for service methods with `use_fast_flow` parameter
- [x] Update existing integration tests to handle new `flow_type` field

### Frontend Tasks

#### admin/ module updates
- [x] Update unit list components to display flow type badge/indicator
- [x] Update unit detail views to show which flow type was used
- [x] Add testID attributes for flow type display elements (for maestro tests)

### Data and Testing

#### Seed Data
- [x] Update `create_seed_data.py` to set `flow_type` field for existing units

#### End-to-End Testing
- [x] Update maestro tests in `mobile/e2e` if unit display changes affect mobile screens
- [x] Add testID attributes to new flow type UI elements

### Terminology and Naming Consistency
- [x] Ensure consistent use of "fast flow" vs "standard flow" terminology across codebase
- [x] Use consistent `flow_type` values: "standard" and "fast"
- [x] Update any relevant documentation or comments referencing content creation approaches

## Technical Implementation Notes

### Parallel Execution Strategy
- Use `asyncio.gather()` with batching to create lessons in parallel
- Batch size controlled by `MAX_PARALLEL_LESSONS` constant
- Handle partial failures gracefully - continue with successful lessons, mark failed ones

### Combined Step Design
`FastLessonMetadataStep` will replace the sequential execution of:
1. `ExtractLessonMetadataStep`
2. `GenerateMisconceptionBankStep`
3. `GenerateDidacticSnippetStep`

The existing `GenerateMCQStep` will be reused as-is since it already generates all MCQs in one call.

### Error Handling
- Leverage existing flow engine retry mechanisms
- For unit creation: if individual lessons fail after retries, save successful lessons and mark unit as partially complete
- Maintain same exception handling patterns as existing implementation

### Flow Type Tracking
- Add `flow_type` column as `String(20)` with values "standard" | "fast"
- Default to "standard" for backward compatibility
- Set based on `use_fast_flow` parameter during unit creation

This specification provides a complete implementation plan for the fast flow feature while maintaining system consistency and backward compatibility.