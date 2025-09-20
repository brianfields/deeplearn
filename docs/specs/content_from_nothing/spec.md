# Content From Nothing - Unit-Level Content Generation

## Requirements Summary

### What to Build
Transform the content creation system to generate complete learning units (multiple lessons) from minimal input - either just a topic or topic + source material. Each unit will contain 1-20 lessons of approximately 5 minutes each, with coherent progression and unit-level learning architecture.

### Key Constraints
- Maintain content coherence across all lessons in a unit
- Support both topic-only and topic+source-material workflows
- Generate comprehensive source material when none provided
- Create unit-level and lesson-level learning objectives hierarchy
- Allow lessons to reference prior material within the unit
- Target 5-minute lessons with flexibility for important concepts to span multiple lessons
- Maximum 1 hour (20 lessons) per unit

### Acceptance Criteria
- [ ] Topic-only input generates complete multi-lesson unit
- [ ] System creates comprehensive source material from topic
- [ ] Time-based lesson chunking with ~5-minute targets
- [ ] Unit-level learning objectives with detailed lesson-level drilling down
- [ ] Later lessons can reference earlier lesson concepts
- [ ] Complete lesson structure (didactic, MCQs, glossary, objectives)
- [ ] Legacy source material workflow maintained
- [ ] New unit fields visible in admin interface

## Cross-Stack Implementation Mapping

### Backend Changes

#### content_creator Module
- **flows.py**: Add `UnitCreationFlow` class
- **steps.py**: Add `GenerateUnitSourceMaterialStep`, `ExtractUnitMetadataStep`, `ChunkSourceMaterialStep`
- **prompts/**: Add `generate_unit_source_material.md`, `extract_unit_metadata.md`, `chunk_source_material.md`
- **service.py**: Add unit flow execution methods
- **test_content_creator_unit.py**: Unit tests for new functionality

#### content Module
- **models.py**: Extend `UnitModel` with learning_objectives, target_duration_minutes, source_material, generated_from_topic fields
- **repo.py**: Add unit creation and lesson association methods
- **service.py**: Add `UnitCreateFromTopic`, `UnitCreateFromSource` DTOs and creation logic
- **public.py**: Expose new unit creation methods
- **test_content_unit.py**: Tests for extended unit functionality

#### Scripts
- **create_unit.py**: Complete rewrite to use `UnitCreationFlow`

### Frontend Changes

#### Admin Interface
- **admin/app/units/page.tsx**: Display new unit fields in list view
- **admin/app/units/[id]/page.tsx**: Show detailed unit information including learning objectives, duration, source material

#### Mobile Interface (Minor)
- **mobile/modules/catalog/models.ts**: Add unit learning objectives to Unit type
- **mobile/modules/catalog/service.ts**: Update DTO mapping for new fields
- **mobile/modules/catalog/components/UnitCard.tsx**: Optionally display target duration

### Database Changes
- **Migration**: Add new columns to units table
- **Seed Data**: Update with examples using new unit structure

## Implementation Checklist

### Backend Tasks

#### Database & Models
- [x] Update UnitModel in content/models.py with new fields
- [x] Create Alembic migration for units table: add learning_objectives (JSON), target_duration_minutes (Integer), source_material (Text), generated_from_topic (Boolean)
- [x] Add unit creation DTOs in content/service.py: UnitCreateFromTopic, UnitCreateFromSource

#### Content Creator Flow System
- [x] Create GenerateUnitSourceMaterialStep in content_creator/steps.py
- [x] Create ExtractUnitMetadataStep in content_creator/steps.py
- [x] Create ChunkSourceMaterialStep in content_creator/steps.py
- [x] Write generate_unit_source_material.md prompt
- [x] Write extract_unit_metadata.md prompt
- [x] Write chunk_source_material.md prompt
- [x] Create UnitCreationFlow in content_creator/flows.py
- [x] Add unit flow execution methods to content_creator/service.py
- [x] Update content_creator/public.py to expose unit creation flow

#### Content Storage & Management
- [x] Add unit creation methods to content/repo.py
- [x] Add unit creation logic to content/service.py
- [x] Update content/public.py interface with new unit methods
- [x] Update create_unit.py script to use UnitCreationFlow

#### Testing
- [x] Update existing integration test to generate a unit from a specified topic without source material (ask for a 10 minute unit)

### Frontend Tasks

#### Admin Interface Updates
- [ ] Update admin/app/units/page.tsx to display target_duration_minutes and generated_from_topic
- [ ] Update admin/app/units/[id]/page.tsx to show learning_objectives, source_material, and generation metadata
- [ ] Add testID attributes for unit fields if needed for mobile e2e tests

#### Mobile Interface Updates
- [ ] Update Unit type in mobile/modules/catalog/models.ts with learning_objectives field
- [ ] Update service mapping in mobile/modules/catalog/service.ts for new unit fields
- [ ] Optionally update mobile/modules/catalog/components/UnitCard.tsx to display duration

### Data & Infrastructure
- [x] Update create_seed_data.py to create sample units with new structure
- [ ] Run database migration to add new unit fields
- [ ] Review codebase for any terminology changes and update consistently (e.g., "unit creation" vs "lesson creation" in logs, error messages)

### Documentation & Future Work
- [ ] Document UnitCreationFlow in content_creator module
- [ ] Add future work section for parallelized lesson creation alternatives

## Future Work: Parallelized Lesson Creation

The current implementation uses a single flow to maintain content coherence across lessons. Future optimizations could explore:

### Alternative 1: Parallel Lesson Flows with Shared Context
- Extract unit metadata and chunk source material upfront
- Execute multiple LessonCreationFlow instances in parallel
- Pass shared unit context (learning objectives, previous lesson summaries) to each flow
- Requires flow engine enhancements for context sharing

### Alternative 2: Template-Based Generation
- Generate detailed unit outline with lesson templates
- Create lessons in parallel using templates with structured prompts
- Post-process for cross-lesson coherence and reference resolution
- Faster but potentially less coherent than current approach

### Alternative 3: Iterative Lesson Building
- Generate lessons sequentially but asynchronously
- Each lesson flow receives context from previously completed lessons
- Allows partial unit completion and progressive enhancement
- Balances speed with coherence better than full parallelization

The current single-flow approach prioritizes content quality and coherence over generation speed, which aligns with the requirement for lessons to reference prior material and maintain unit-level learning progression.

## Implementation Notes

### Error Handling
- Unit creation flow should handle partial failures gracefully
- If lesson generation fails partway through, save successfully created lessons
- Provide clear error messages indicating which lessons failed and why

### Performance Considerations
- Unit creation will take significantly longer than single lesson creation
- Consider adding progress indicators for long-running unit generation
- Monitor LLM token usage for cost management

### Content Quality
- Ensure unit-level learning objectives properly decompose into lesson objectives
- Validate that lesson chunking produces coherent 5-minute segments
- Test that later lessons appropriately reference earlier concepts

### Backwards Compatibility
- Remove single lesson creation capabilities cleanly
- Update any existing scripts or tools that relied on individual lesson workflows
- Database can be reset as no backwards compatibility needed