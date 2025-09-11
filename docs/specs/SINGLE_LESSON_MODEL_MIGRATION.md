# Single LessonModel Migration Plan

## Overview

This document outlines the migration from the current two-table structure (`lessons` + `lesson_components`) to a single `LessonModel` with a JSON `package` field containing structured educational content. This refactoring will simplify the data model while providing a more flexible and comprehensive content structure.

**SIMPLIFIED APPROACH**: Since we haven't deployed yet, we can wipe existing data clean and implement the new structure without backward compatibility concerns.

## Current State Analysis

### Current Database Schema
```sql
-- Current lessons table
CREATE TABLE lessons (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    core_concept VARCHAR(500) NOT NULL,
    user_level VARCHAR(50) NOT NULL,
    learning_objectives JSON NOT NULL,
    key_concepts JSON NOT NULL,
    source_material TEXT,
    source_domain VARCHAR(100),
    source_level VARCHAR(50),
    refined_material JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Current lesson_components table (TO BE REMOVED)
CREATE TABLE lesson_components (
    id VARCHAR(36) PRIMARY KEY,
    lesson_id VARCHAR(36) NOT NULL,
    component_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content JSON NOT NULL,
    learning_objective VARCHAR(500),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (lesson_id) REFERENCES lessons(id)
);
```

### Current Module Dependencies
The content module is currently used by:
- **content_creator module**: Creates lessons and components via `ContentProvider`
- **lesson_catalog module**: Browses lessons via `ContentProvider`
- **learning_session module**: Accesses lesson data via `ContentProvider`
- **Scripts**: Direct usage of `content_provider()` for lesson creation
- **Frontend**: Indirectly via backend API endpoints

### Current DTOs and Public Interface
```python
# Current DTOs in content/service.py
class LessonRead(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    learning_objectives: list[str]
    key_concepts: list[str]
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: str | None = None
    created_at: datetime
    updated_at: datetime
    components: list[LessonComponentRead] = []

class LessonComponentRead(BaseModel):
    id: str
    lesson_id: str
    component_type: str
    title: str
    content: dict
    learning_objective: str | None = None
    created_at: datetime
    updated_at: datetime

# Current public interface
class ContentProvider(Protocol):
    def get_lesson(self, lesson_id: str) -> LessonRead | None: ...
    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead: ...
    def delete_lesson(self, lesson_id: str) -> bool: ...
    def lesson_exists(self, lesson_id: str) -> bool: ...
    def get_lesson_component(self, component_id: str) -> LessonComponentRead | None: ...
    def get_components_by_lesson(self, lesson_id: str) -> list[LessonComponentRead]: ...
    def save_lesson_component(self, component_data: LessonComponentCreate) -> LessonComponentRead: ...
    def delete_lesson_component(self, component_id: str) -> bool: ...
```

## Target State

### New Database Schema
```sql
-- New single lessons table
CREATE TABLE lessons (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    core_concept VARCHAR(500) NOT NULL,
    user_level VARCHAR(50) NOT NULL,

    source_material TEXT,
    source_domain VARCHAR(100),
    source_level VARCHAR(50),
    refined_material JSON,

    package JSON NOT NULL,          -- New structured content package
    package_version INTEGER NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- lesson_components table will be DROPPED
```

### New Package Structure
The `package` JSON field will contain a structured `LessonPackage` with the following Pydantic models:

```python
# New package structure models
class LengthBudgets(BaseModel):
    stem_max_words: int = Field(35, ge=1, le=200)
    vignette_max_words: int = Field(80, ge=1, le=500)
    option_max_words: int = Field(12, ge=1, le=50)

class Meta(BaseModel):
    lesson_id: str
    title: str
    core_concept: str
    user_level: str
    domain: str = "General"
    package_schema_version: int = 1
    content_version: int = 1
    length_budgets: LengthBudgets = LengthBudgets()

class Objective(BaseModel):
    id: str
    text: str
    bloom_level: Optional[str] = None

class GlossaryTerm(BaseModel):
    id: str
    term: str
    definition: str
    relation_to_core: Optional[str] = None
    common_confusion: Optional[str] = None
    micro_check: Optional[str] = None

class DidacticSnippet(BaseModel):
    id: str
    mini_vignette: Optional[str] = None
    plain_explanation: str
    key_takeaways: List[str]
    worked_example: Optional[str] = None
    near_miss_example: Optional[str] = None
    discriminator_hint: Optional[str] = None

class MCQOption(BaseModel):
    id: str
    label: str  # "A","B","C","D"
    text: str
    rationale_wrong: Optional[str] = None

class MCQAnswerKey(BaseModel):
    label: str
    option_id: Optional[str] = None

class MCQItem(BaseModel):
    id: str
    lo_id: str
    stem: str
    cognitive_level: Optional[str] = None
    estimated_difficulty: Optional[str] = None
    options: List[MCQOption]
    answer_key: MCQAnswerKey
    misconceptions_used: List[str] = []

    @model_validator(mode="after")
    def _check_options_and_key(self):
        if not (3 <= len(self.options) <= 4):
            raise ValueError("MCQ must have 3–4 options")
        labels = [o.label for o in self.options]
        if len(labels) != len(set(labels)):
            raise ValueError("Duplicate option labels")
        if self.answer_key.label not in labels:
            raise ValueError("answer_key.label missing in options")
        if self.answer_key.option_id:
            ids = [o.id for o in self.options]
            if self.answer_key.option_id not in ids:
                raise ValueError("answer_key.option_id missing in options")
        return self

class LessonPackage(BaseModel):
    meta: Meta
    objectives: List[Objective]
    glossary: Dict[str, List[GlossaryTerm]]  # {"terms": [...]}
    didactic: Dict[str, Dict[str, DidacticSnippet]]  # {"by_lo": {"lo_1": {...}}}
    mcqs: List[MCQItem]
    misconceptions: List[Dict[str, str]] = []
    confusables: List[Dict[str, str]] = []

    @model_validator(mode="after")
    def _cross_checks(self):
        lo_ids = {o.id for o in self.objectives}
        by_lo = self.didactic.get("by_lo", {}) if self.didactic else {}
        for lo_id in by_lo.keys():
            if lo_id not in lo_ids:
                raise ValueError(f"Didactic snippet references unknown lo_id '{lo_id}'")
        for item in self.mcqs:
            if item.lo_id not in lo_ids:
                raise ValueError(f"MCQ '{item.id}' references unknown lo_id '{item.lo_id}'")
        return self
```

### New DTOs and Public Interface
```python
# New simplified DTOs
class LessonRead(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None
    package: LessonPackage
    package_version: int
    created_at: datetime
    updated_at: datetime

class LessonCreate(BaseModel):
    id: str
    title: str
    core_concept: str
    user_level: str
    source_material: str | None = None
    source_domain: str | None = None
    source_level: str | None = None
    refined_material: dict | None = None
    package: LessonPackage
    package_version: int = 1

# Simplified public interface (component methods removed)
class ContentProvider(Protocol):
    def get_lesson(self, lesson_id: str) -> LessonRead | None: ...
    def get_all_lessons(self, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def search_lessons(self, query: str | None = None, user_level: str | None = None, limit: int = 100, offset: int = 0) -> list[LessonRead]: ...
    def save_lesson(self, lesson_data: LessonCreate) -> LessonRead: ...
    def delete_lesson(self, lesson_id: str) -> bool: ...
    def lesson_exists(self, lesson_id: str) -> bool: ...
    # Component methods removed - data now embedded in package
```

## Simplified Migration Strategy

Since we can wipe existing data and don't need backward compatibility, we can implement this as a straightforward refactor in 3 phases:

### Phase 1: Update Database Schema and Models
**Duration**: 1 day
**Risk**: Low

#### 1.1 Create New Package Models
- **File**: `backend/modules/content/package_models.py`
- **Action**: Create all the new Pydantic models for the package structure
- **Dependencies**: None
- **Testing**: Unit tests for model validation

#### 1.2 Update Database Models
- **File**: `backend/modules/content/models.py`
- **Action**: Replace current model with new single-table structure
- **Changes**:
  ```python
  class LessonModel(Base):
      __tablename__ = "lessons"

      id = Column(String(36), primary_key=True)
      title = Column(String(255), nullable=False)
      core_concept = Column(String(500), nullable=False)
      user_level = Column(String(50), nullable=False)

      source_material = Column(Text)
      source_domain = Column(String(100))
      source_level = Column(String(50))
      refined_material = Column(JSON)

      package = Column(JSON, nullable=False)
      package_version = Column(Integer, nullable=False, default=1)

      created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
      updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
  ```
- **Dependencies**: Phase 1.1
- **Testing**: Model validation works

#### 1.3 Create Database Migration (Clean Slate)
- **File**: `backend/alembic/versions/xxx_single_lesson_model.py`
- **Action**: Drop lesson_components table, update lessons table structure
- **SQL**:
  ```sql
  DROP TABLE lesson_components;
  ALTER TABLE lessons DROP COLUMN learning_objectives;
  ALTER TABLE lessons DROP COLUMN key_concepts;
  ALTER TABLE lessons ADD COLUMN package JSON NOT NULL;
  ALTER TABLE lessons ADD COLUMN package_version INTEGER NOT NULL DEFAULT 1;
  ```
- **Dependencies**: Phase 1.2
- **Testing**: Migration runs successfully on empty database

### Phase 2: Update Content Module
**Duration**: 1-2 days
**Risk**: Low

#### 2.1 Update Repository Layer
- **File**: `backend/modules/content/repo.py`
- **Action**: Remove all component-related methods, simplify to lesson-only operations
- **Changes**:
  - Remove all component CRUD methods
  - Update lesson methods to work with package field
  - Simplify queries (no more joins needed)
- **Dependencies**: Phase 1 complete
- **Testing**: Repository operations work with new structure

#### 2.2 Update Service Layer
- **File**: `backend/modules/content/service.py`
- **Action**: Update DTOs and business logic for package-based structure
- **Changes**:
  - Remove component DTOs (`LessonComponentRead`, `LessonComponentCreate`)
  - Update `LessonRead` and `LessonCreate` to include package field
  - Remove all component-related service methods
  - Add package validation logic
- **Dependencies**: Phase 2.1
- **Testing**: Service methods work with package structure

#### 2.3 Update Public Interface
- **File**: `backend/modules/content/public.py`
- **Action**: Simplify public interface to remove component methods
- **Changes**:
  - Remove component-related methods from `ContentProvider` protocol
  - Update imports to exclude component DTOs
  - Clean up `__all__` exports
- **Dependencies**: Phase 2.2
- **Testing**: Public interface is clean and functional

### Phase 3: Update All Dependent Modules
**Duration**: 2-3 days
**Risk**: Medium

#### 3.1 Update Content Creator Module
- **Files**:
  - `backend/modules/content_creator/service.py`
  - `backend/modules/content_creator/flows.py`
  - `backend/modules/content_creator/steps.py`
- **Action**: Modify to create lessons with package structure
- **Changes**:
  - Update `LessonCreationFlow` to build `LessonPackage` objects
  - Modify steps to populate package structure instead of creating separate components
  - Update service to save complete lesson packages
- **Dependencies**: Phase 2 complete
- **Testing**: Lesson creation produces valid packages

#### 3.2 Update Other Backend Modules
- **Files**:
  - `backend/modules/lesson_catalog/service.py`
  - `backend/modules/learning_session/service.py`
  - `backend/scripts/create_lesson.py`
- **Action**: Update to work with package-based lessons
- **Changes**:
  - Extract data from package structure instead of separate components
  - Update component access patterns
  - Modify lesson creation scripts
- **Dependencies**: Phase 3.1
- **Testing**: All functionality works with new structure

#### 3.3 Update Frontend
- **Files**:
  - `mobile/modules/content/models.ts`
  - `mobile/modules/content/service.ts`
  - `mobile/modules/learning_session/service.ts`
  - `mobile/modules/learning_session/components/`
- **Action**: Update to work with package-based lesson data
- **Changes**:
  - Update TypeScript interfaces for package structure
  - Modify data extraction logic
  - Update component rendering to use package data
- **Dependencies**: Phase 3.2
- **Testing**: Frontend displays lesson content correctly

#### 3.4 Update Tests and Documentation
- **Files**: All test files and documentation
- **Action**: Update for new structure
- **Changes**:
  - Update test data to use package format
  - Remove component-related tests
  - Add package validation tests
  - Update documentation
- **Dependencies**: Phase 3.3
- **Testing**: All tests pass

## Detailed File Impact Analysis

### Backend Files Requiring Changes

#### High Impact (Major Changes Required)
1. **`backend/modules/content/models.py`** - Database model changes
2. **`backend/modules/content/service.py`** - DTO and business logic changes
3. **`backend/modules/content/repo.py`** - Data access pattern changes
4. **`backend/modules/content/public.py`** - Public interface changes
5. **`backend/modules/content_creator/service.py`** - Lesson creation logic changes
6. **`backend/modules/content_creator/flows.py`** - Flow output structure changes
7. **`backend/modules/content_creator/steps.py`** - Step output structure changes
8. **`backend/scripts/create_lesson.py`** - Lesson creation script changes

#### Medium Impact (Moderate Changes Required)
9. **`backend/modules/lesson_catalog/service.py`** - Data access pattern changes
10. **`backend/modules/learning_session/service.py`** - Component access changes
11. **`backend/modules/learning_session/routes.py`** - API response changes
12. **`backend/modules/lesson_catalog/routes.py`** - API response changes
13. **`backend/modules/content_creator/routes.py`** - API integration changes

#### Low Impact (Minor Changes Required)
14. **`backend/modules/content/test_content_unit.py`** - Test data updates
15. **`backend/modules/content_creator/test_content_creator_unit.py`** - Test updates
16. **`backend/modules/lesson_catalog/test_lesson_catalog_unit.py`** - Test updates
17. **`backend/modules/learning_session/test_learning_session_unit.py`** - Test updates
18. **`backend/tests/test_lesson_creation_integration.py`** - Integration test updates

### Frontend Files Requiring Changes

#### High Impact
1. **`mobile/modules/content/models.ts`** - Type definitions
2. **`mobile/modules/content/service.ts`** - Data transformation logic
3. **`mobile/modules/learning_session/service.ts`** - Component extraction logic

#### Medium Impact
4. **`mobile/modules/learning_session/components/MultipleChoice.tsx`** - Data access patterns
5. **`mobile/modules/learning_session/screens/`** - Component rendering logic
6. **`mobile/modules/lesson_catalog/`** - Lesson display logic

#### Low Impact
7. **`mobile/modules/content/test_content_unit.ts`** - Test updates
8. **`mobile/modules/learning_session/test_learning_session_unit.ts`** - Test updates

### Database Files
1. **Single Migration**: `backend/alembic/versions/xxx_single_lesson_model.py` - Clean slate migration

## Risk Assessment and Mitigation

### Medium Risk Areas

#### 1. Cross-Module Dependencies
**Risk**: Breaking changes in public interface affect multiple modules simultaneously
**Mitigation**:
- Comprehensive integration testing after each phase
- Update all dependent modules in coordinated fashion
- Test end-to-end workflows before deployment

#### 2. Complex Package Validation
**Risk**: Invalid package data causing runtime errors
**Mitigation**:
- Comprehensive Pydantic validation with clear error messages
- Extensive unit tests for edge cases and validation scenarios
- Graceful error handling and validation feedback

#### 3. Frontend-Backend Synchronization
**Risk**: Frontend and backend changes must be deployed together
**Mitigation**:
- Coordinate deployment timing
- Test full stack integration thoroughly
- Have rollback plan ready

### Low Risk Areas

#### 1. Database Schema Changes
**Risk**: Since we're wiping data, schema changes are straightforward
**Mitigation**:
- Test migration on development database
- Validate new schema structure

#### 2. Performance Impact
**Risk**: JSON package field may affect query performance
**Mitigation**:
- Monitor query performance in development
- Add database indexes if needed
- Optimize queries as needed

## Success Criteria

### Functional Requirements
- [ ] All lesson creation workflows produce valid packages
- [ ] All lesson browsing and search functionality works with new structure
- [ ] All learning session functionality works with package data
- [ ] All API endpoints return correct data in new format
- [ ] Frontend displays lesson content correctly from packages

### Non-Functional Requirements
- [ ] Performance maintained or improved (simpler queries, no joins)
- [ ] All tests pass
- [ ] Clean, maintainable code structure
- [ ] Comprehensive package validation

### Technical Requirements
- [ ] Database schema updated correctly (single table)
- [ ] All component-related code removed
- [ ] Package validation working correctly
- [ ] Error handling for invalid packages
- [ ] Documentation updated

## Rollback Plan

Since we're doing a clean slate approach, rollback is straightforward:

### Rollback Steps
1. **Revert code changes** to previous version
2. **Run reverse migration** to restore lesson_components table and old schema
3. **Redeploy previous version**
4. **Investigate issues** before retry

### Rollback Triggers
- Critical functionality broken during testing
- Significant performance degradation
- Package validation issues causing data corruption
- Frontend integration failures

## Timeline and Resource Allocation

### Estimated Timeline: 4-5 days (Significantly Reduced)

#### Day 1
- **Phase 1**: Update Database Schema and Models

#### Days 2-3
- **Phase 2**: Update Content Module

#### Days 4-5
- **Phase 3**: Update All Dependent Modules

### Resource Requirements
- **1 Backend Developer** (primary implementer)
- **1 Frontend Developer** (mobile updates)
- **Testing can be done incrementally by developers**

### Critical Path Dependencies
1. Phase 1 must complete before Phase 2
2. Phase 2 must complete before Phase 3
3. Frontend updates can happen in parallel with backend module updates in Phase 3

## Conclusion

This simplified migration represents a significant architectural improvement that will:

1. **Simplify the data model** by eliminating the complex lesson-component relationship
2. **Improve data consistency** by storing related content together in atomic packages
3. **Enable richer content structures** through the flexible package format
4. **Reduce complexity** in dependent modules by providing a single, comprehensive data structure
5. **Improve maintainability** by centralizing content validation and structure
6. **Improve performance** by eliminating joins and reducing database complexity

The clean slate approach makes this migration much more straightforward and less risky than a traditional data migration.

**Key Success Factors**:
- Thorough testing at each phase
- Comprehensive package validation with clear error messages
- Coordinated updates across all dependent modules
- Simple rollback procedures
- Clean implementation without backward compatibility concerns

**Benefits of Clean Slate Approach**:
- **Faster implementation** (4-5 days vs 12-15 days)
- **Lower risk** (no data migration complexity)
- **Cleaner code** (no dual-mode support needed)
- **Simpler testing** (no backward compatibility scenarios)
- **Better architecture** (designed from scratch for new structure)

Following this simplified plan will result in a cleaner, more maintainable content system that better supports the application's educational goals while being much faster and safer to implement.
