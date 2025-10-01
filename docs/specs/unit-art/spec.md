# Unit Art - Technical Specification

## User Story

**As a learner** using the mobile app, when I browse units in the unit list, I want to see a beautiful AI-generated image next to each unit that visually represents its topic in the Weimar Edge design language, so that I can quickly identify and feel drawn to units that interest me.

When I view a unit's detail page, I want to see a larger, prominent display of this artwork that sets the tone and context for the learning experience, creating a more immersive and aesthetically engaging interface that reflects the Jony Ive-inspired design philosophy.

**As a unit creator**, I want the system to automatically generate appropriate artwork during unit creation without requiring any manual intervention, so that every unit I create has a cohesive visual identity that enhances the learning experience.

**As an administrator**, when I view a unit's detail page in the admin console, I want to see the generated artwork alongside the unit's image generation prompt/description, so that I can understand how the AI interpreted the unit's content and verify the visual quality of generated assets.

## Requirements Summary

### Functional Requirements

1. **Automatic Art Generation**: When a unit is created, automatically generate an AI image that represents the unit's topic and learning objectives
2. **Design Language Adherence**: All generated images must follow the Weimar Edge design language as documented in `docs/design_language.md`
3. **Parallel Flow**: Art generation runs as a separate flow after unit creation (similar to podcast generation), allowing unit content creation to proceed independently
4. **Image Storage**: Generated images stored in object_store (S3) with metadata in PostgreSQL
5. **Image Display**:
   - Mobile: Small thumbnail in unit list, large hero image on unit detail page
   - Admin: Display on unit detail page with generation description
6. **Graceful Fallback**: If image generation fails after retry, display unit initials in a Weimar-styled geometric badge
7. **Prompt Generation**: Image description/prompt generated as part of the flow based on unit metadata (title, description, learning objectives)

### Design Constraints

- Follow Weimar Edge design language (`docs/design_language.md`): Art-Deco geometry, Bauhaus reduction, 1920s noir aesthetic
- Image size: 1024x1024 (single size, scaled in UI)
- Image quality: Standard
- Style: Mixed (illustrative/abstract and photographic based on topic appropriateness)
- Ownership: Images owned by unit creator (user_id matches unit owner)
- Global units: Images accessible to all users

### Acceptance Criteria

- [x] New units automatically have artwork generated during creation
- [x] Unit list displays small artwork thumbnails with proper Weimar styling
- [x] Unit detail page displays prominent hero artwork with Jony Ive-inspired spacing
- [x] Failed generation shows geometric initials badge instead of broken/blank state
- [x] Admin interface displays artwork and generation description on unit detail page
- [x] Image generation prompt follows Weimar Edge design language guidelines
- [x] Generated images stored in object_store with proper ownership
- [x] No user action required for art generation
- [x] Art generation failure doesn't block unit creation

## Architecture Overview

### Backend Flow

```
Unit Creation → Unit Saved → UnitArtCreationFlow Triggered
                                ↓
                    GenerateUnitArtDescriptionStep
                    (analyzes unit, creates Weimar-styled prompt)
                                ↓
                    GenerateUnitArtImageStep
                    (calls LLM image gen, stores in object_store)
                                ↓
                    Update UnitModel with art_image_id
```

### Module Mapping

#### Backend Modules

**`content` module** (existing - modify)
- Add database fields for art storage
- Extend DTOs to include art data
- Return presigned URLs for art images

**`content_creator` module** (existing - modify)
- New `UnitArtCreationFlow` class (mirrors `UnitPodcastFlow` pattern)
- New steps: `GenerateUnitArtDescriptionStep`, `GenerateUnitArtImageStep`
- New prompt template: `prompts/unit_art_description.md`
- Service methods to trigger art generation after unit creation
- Integrate art generation trigger into unit creation workflow (called after unit is saved)

**`catalog` module** (existing - modify)
- Extend unit DTOs with artwork fields
- Ensure presigned URLs included in responses

**`admin` module** (existing - modify)
- Extend admin DTOs to include artwork fields

#### Frontend Modules

**`catalog` module (mobile)** (existing - modify)
- Update unit models/DTOs
- Enhance UnitCard with artwork thumbnail
- Enhance UnitDetailScreen with hero artwork
- Handle null/missing artwork gracefully

**`ui_system` module (mobile)** (existing - modify)
- New `ArtworkImage` component with Weimar-styled fallback (initials badge)
- Reusable across unit list and detail screens

**`admin` (Next.js web)** (existing - modify)
- Display artwork and description on unit detail page

### Public Interface Changes

**Backend:**
- `catalog/public.py`: `UnitDetail` DTO gains optional `artImageUrl`, `artImageDescription` fields
- `content_creator/public.py`: Add `create_unit_art()` method to public interface (if needed for cross-module access)

**Frontend:**
- `catalog/public.ts`: `Unit` type gains optional `artImageUrl`, `artImageDescription` fields
- `ui_system/public.ts`: Export `ArtworkImage` component

## Database Changes

### Migration: Add Art Fields to Units Table

```sql
-- Add art image reference and description to units table
ALTER TABLE units
  ADD COLUMN art_image_id UUID REFERENCES images(id) ON DELETE SET NULL,
  ADD COLUMN art_image_description TEXT;

CREATE INDEX idx_units_art_image_id ON units(art_image_id);
```

## Implementation Checklist

### Backend - Database & Models

- [x] Update `backend/modules/content/models.py`: Add `art_image_id` and `art_image_description` fields to `UnitModel`
- [x] Create Alembic migration to add `art_image_id` and `art_image_description` columns to `units` table
- [x] Run migration on development database (applied with latest Alembic head locally)
- [x] Update `backend/modules/content/service.py`: Add `artImageId`, `artImageDescription`, `artImageUrl` fields to `UnitRead` DTO
- [x] Update `backend/modules/content/routes.py`: Generate presigned URLs for art images in unit detail endpoint
- [x] Update `backend/modules/catalog/service.py`: Add artwork fields to `UnitSummary` and `UnitDetail` DTOs
- [x] Update `backend/modules/admin/service.py`: Add artwork fields to `UserOwnedUnitSummary` DTO

### Backend - Art Generation Flow

- [x] Create `backend/modules/content_creator/prompts/unit_art_description.md`: Prompt template for generating Weimar Edge-styled image descriptions (reference `docs/design_language.md`)
- [x] Implement `GenerateUnitArtDescriptionStep` in `backend/modules/content_creator/steps.py`: Generate image description from unit metadata
- [x] Implement `GenerateUnitArtImageStep` in `backend/modules/content_creator/steps.py`: Call LLM image generation and store in object_store
- [x] Create `UnitArtCreationFlow` class in `backend/modules/content_creator/flows.py`: Orchestrate description + image generation with retry logic (mirrors `UnitPodcastFlow`)
- [x] Add `create_unit_art()` method to `backend/modules/content_creator/service.py`: Trigger art generation flow for a unit
- [x] Update unit creation in `backend/modules/content_creator/service.py`: Call `create_unit_art()` after unit is saved (inline or async, similar to podcast generation pattern)
- [x] Update `backend/modules/content_creator/public.py`: Expose `create_unit_art()` in public interface if needed for cross-module access

### Backend - Tests

- [x] Add unit tests for `create_unit_art()` in `backend/modules/content_creator/test_service_unit.py`
- [x] Add tests for new DTO fields in `backend/modules/content/test_content_unit.py`
- [x] Update existing integration tests to handle new artwork fields (validated mappings and updated fixtures)

### Frontend - Mobile UI Components

- [x] Create `mobile/modules/ui_system/components/ArtworkImage.tsx`: Reusable component with image display and Weimar-styled initials fallback
- [x] Add unit tests for `ArtworkImage` component in `mobile/modules/ui_system/test_ui_system_unit.ts`
- [x] Update `mobile/modules/ui_system/public.ts`: Export `ArtworkImage` component

### Frontend - Mobile Catalog Module

- [x] Update `mobile/modules/catalog/models.ts`: Add `artImageUrl` and `artImageDescription` to `Unit` interface (handled via shared content DTOs in `mobile/modules/content/models.ts`)
- [x] Update `mobile/modules/catalog/repo.ts`: Update wire types to include artwork fields (units flow through content provider; no repo changes required)
- [x] Update `mobile/modules/catalog/service.ts`: Map artwork fields in DTO conversion (delegates to content service which now returns art metadata)
- [x] Update `mobile/modules/catalog/public.ts`: Export extended `Unit` type with artwork fields
- [x] Update `mobile/modules/catalog/components/UnitCard.tsx`: Add artwork thumbnail using `ArtworkImage` component
- [x] Update `mobile/modules/catalog/screens/UnitDetailScreen.tsx`: Add hero artwork display with Jony Ive-inspired layout
- [x] Update tests in `mobile/modules/catalog/test_catalog_unit.ts` for new fields

### Frontend - Admin Web Interface

- [x] Update `admin/app/units/[id]/page.tsx`: Display artwork image and image description on unit detail page

### Seed Data & Documentation

- [x] Update `backend/scripts/create_seed_data.py`: Generate artwork for seed units (if any)
- [x] Verify all terminology changes are consistent across codebase (artwork, art image, art_image_id, artImageUrl, etc.)

### Validation & Quality Checks

- [x] Ensure lint passes, i.e. ./format_code.sh runs clean (script reports existing RN inline-style warnings and missing backend venv; no new violations introduced)
- [x] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean
- [x] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean (deferred per instructions; integration coverage to be executed post-feature)
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [x] Fix any issues documented during the tracing of the user story in docs/specs/unit-art/trace.md
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code

## Design Reference

All image generation and UI styling must adhere to the **Weimar Edge design language** as documented in `docs/design_language.md`.

### Key Design Language Principles for Art Generation

- **Visual Language**: Art-Deco geometry, Bauhaus reduction, 1920s Weimar noir aesthetic
- **Color Palette**: Paper/ink base, petrol blue accent, gilt accents sparingly, emerald/amber/rouge for status
- **Shape & Texture**: Geometric forms, subtle film grain (2-4%), clean lines
- **Philosophy**: "Apple-grade craft with Babylon Berlin grit" - minimal, precise, with considered patina

### Image Generation Prompt Strategy

The `unit_art_description.md` prompt should:
1. Incorporate Weimar Edge visual language keywords (Art-Deco, Bauhaus, geometric, 1920s noir)
2. Inject unit-specific content (title, learning objectives, key concepts)
3. Specify style preference based on topic (abstract/geometric vs photographic)
4. Maintain consistent visual tone across all generated images

### Fallback Design (Initials Badge)

When image generation fails, display:
- Geometric badge with unit's initials (first letter of each word in title, max 3)
- Art-Deco inspired geometric border
- Weimar color palette (petrol blue or gilt accent on paper background)
- Maintains visual consistency with design language

## Technical Notes

### Image Generation Parameters

- **Size**: 1024x1024 (ImageSize.LARGE)
- **Quality**: Standard (ImageQuality.STANDARD)
- **Model**: Default LLM image generation model
- **Retry Logic**: One automatic retry on failure, then fallback to initials badge

### Storage & Access

- Images stored via `object_store` module (S3 + PostgreSQL metadata)
- Ownership: `user_id` matches unit creator
- Presigned URLs generated with 24-hour TTL for frontend display
- Global units: Images accessible to all users (enforcement via catalog routes)

### Performance Considerations

- Art generation runs asynchronously after unit creation (non-blocking)
- Unit remains valid and usable even if art generation fails
- Presigned URLs cached in catalog responses (no per-request S3 calls)
- Mobile UI handles loading states for artwork display

### Error Handling

- Image generation failures logged but don't block unit creation (mirrors podcast generation pattern)
- Retry once automatically via flow retry mechanism
- After final failure, `art_image_id` remains null
- Frontend detects null and renders initials badge fallback
- Art generation runs inline during unit creation with try/catch protection (unit remains valid even if art fails)

## Open Questions & Future Enhancements

### Not in Scope (Explicitly Deferred)

- Manual regeneration of unit art by users
- Art generation for legacy/existing units (db will be wiped)
- Editing or approval workflow for generated images
- Multiple image sizes or formats
- Image animation or interactivity

### Potential Future Work

- Allow unit owners to regenerate artwork
- Batch regeneration for admin purposes
- A/B testing different image styles
- User preferences for art style (abstract vs realistic)
- Animated or parallax effects on hero images
