# Object Store Module Specification

## User Story

**As a** developer building features that need file storage,
**I want** a clean, async object_store module that handles images and audio files in S3,
**So that** I can easily upload, retrieve, and manage media files with proper metadata and secure access URLs.

## Requirements Summary

### What to Build
- Async object_store module following modular architecture patterns
- Support for image files (JPEG, PNG, WebP, GIF) and audio files (MP3, WAV, FLAC, M4A)
- S3 integration for file storage with PostgreSQL metadata storage
- Files can be user-owned (user_id FK) or system-wide (user_id = null)
- Secure presigned URL generation for file access
- Clean public interface for other modules to use

### Constraints
- Follow async modular architecture (models, repo, service, public)
- No routes/API endpoints (backend-only service for now)
- 100MB file size limit
- Use existing S3Provider patterns where appropriate
- No frontend integration in this phase

### Acceptance Criteria
- ✅ Upload images/audio to S3 with metadata storage in PostgreSQL
- ✅ Retrieve file metadata with proper authorization (user ownership)
- ✅ Generate presigned URLs for secure file access
- ✅ List files by user with pagination
- ✅ Delete files from both S3 and database
- ✅ Handle async operations with proper error handling
- ✅ Provide clean public interface following Protocol pattern

## Cross-Stack Mapping

### Backend Module: object_store

#### Files to Create
- `repo.py` - Async database access layer for ImageModel and AudioModel
- `service.py` - Business logic with DTOs and S3 integration (async)
- `public.py` - Public interface with ObjectStoreProvider Protocol (async)
- `test_object_store_unit.py` - Unit tests for complex business logic

#### Files to Modify
- `models.py` - Complete AudioModel, fix imports, make user_id nullable, remove category
- `s3_provider.py` - Minor updates for consistency and async patterns

#### Files to Delete
- `image_service.py` - Functionality will move to proper service.py with architectural compliance

## Implementation Checklist

### Backend Models & Database
- [ ] Update ImageModel: remove category field, make user_id nullable
- [ ] Complete AudioModel with duration, bitrate, sample_rate, transcript fields
- [ ] Fix import paths in models.py to use modules.shared_models
- [ ] Ensure proper indexes on user_id and s3_key fields
- [ ] Generate and run Alembic migration for model changes

### Backend Repository Layer
- [ ] Create repo.py with async SQLAlchemy operations
- [ ] Implement ImageRepo class with CRUD operations (create, by_id, by_user_id, list_by_user, delete, exists)
- [ ] Implement AudioRepo class with equivalent CRUD operations
- [ ] Ensure repos return ORM objects only (no DTOs)
- [ ] Handle async session management without commits/rollbacks in repo

### Backend Service Layer
- [ ] Create service.py with DTOs: ImageRead, ImageCreate, AudioRead, AudioCreate, FileUploadResult
- [ ] Implement ObjectStoreService class handling both images and audio
- [ ] Integrate S3Provider for file upload/download/delete operations
- [ ] Add image metadata extraction (width, height from file contents)
- [ ] Add audio metadata extraction (duration, bitrate, sample_rate)
- [ ] Implement async file validation (type checking, size limits)
- [ ] Add presigned URL generation for secure file access
- [ ] Ensure service returns DTOs only (never ORM objects)
- [ ] Add proper error handling with domain exceptions

### Backend Public Interface
- [ ] Create public.py with ObjectStoreProvider Protocol
- [ ] Implement object_store_provider function returning service instance
- [ ] Define narrow public interface exposing only essential methods
- [ ] Export necessary DTOs and types in __all__
- [ ] Ensure async consistency throughout public interface

### Backend S3 Integration
- [ ] Update s3_provider.py for consistency with async patterns
- [ ] Ensure S3Provider integrates cleanly with new service architecture
- [ ] Handle S3 connection errors with proper exception mapping
- [ ] Maintain existing file key generation and organization patterns

### Backend Testing
- [ ] Create test_object_store_unit.py with unit tests for complex service behavior
- [ ] Test file upload/download workflows
- [ ] Test user ownership and authorization logic
- [ ] Test error scenarios (file not found, invalid file types, S3 failures)
- [ ] Test presigned URL generation
- [ ] Mock S3Provider for isolated testing

### Database Migration & Seed Data
- [ ] Create Alembic migration for AudioModel table creation
- [ ] Create migration for ImageModel changes (nullable user_id, remove category)
- [ ] Update create_seed_data.py to create sample image and audio records if relevant

### Code Quality & Integration
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py runs clean
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/object_store/trace.md
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code
