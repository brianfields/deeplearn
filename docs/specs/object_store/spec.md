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
- [x] Update ImageModel: remove category field, make user_id nullable
- [x] Complete AudioModel with duration, bitrate, sample_rate, transcript fields
- [x] Fix import paths in models.py to use modules.shared_models
- [x] Ensure proper indexes on user_id and s3_key fields
- [x] Generate and run Alembic migration for model changes

### Backend Repository Layer
- [x] Create repo.py with async SQLAlchemy operations
- [x] Implement ImageRepo class with CRUD operations (create, by_id, by_user_id, list_by_user, delete, exists)
- [x] Implement AudioRepo class with equivalent CRUD operations
- [x] Ensure repos return ORM objects only (no DTOs)
- [x] Handle async session management without commits/rollbacks in repo

### Backend Service Layer
- [x] Create service.py with DTOs: ImageRead, ImageCreate, AudioRead, AudioCreate, FileUploadResult
- [x] Implement ObjectStoreService class handling both images and audio
- [x] Integrate S3Provider for file upload/download/delete operations
- [x] Add image metadata extraction (width, height from file contents)
- [x] Add audio metadata extraction (duration, bitrate, sample_rate)
- [x] Implement async file validation (type checking, size limits)
- [x] Add presigned URL generation for secure file access
- [x] Ensure service returns DTOs only (never ORM objects)
- [x] Add proper error handling with domain exceptions

### Backend Public Interface
- [x] Create public.py with ObjectStoreProvider Protocol
- [x] Implement object_store_provider function returning service instance
- [x] Define narrow public interface exposing only essential methods
- [x] Export necessary DTOs and types in __all__
- [x] Ensure async consistency throughout public interface

### Backend S3 Integration
- [x] Update s3_provider.py for consistency with async patterns
- [x] Ensure S3Provider integrates cleanly with new service architecture
- [x] Handle S3 connection errors with proper exception mapping
- [x] Maintain existing file key generation and organization patterns

### Backend Testing
- [x] Create test_object_store_unit.py with unit tests for complex service behavior
- [x] Test file upload/download workflows
- [x] Test user ownership and authorization logic
- [x] Test error scenarios (file not found, invalid file types, S3 failures)
- [x] Test presigned URL generation
- [x] Mock S3Provider for isolated testing

### Database Migration & Seed Data
- [x] Create Alembic migration for AudioModel table creation
- [x] Create migration for ImageModel changes (nullable user_id, remove category)
- [x] Update create_seed_data.py to create sample image and audio records if relevant

### Code Quality & Integration
- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean
- [x] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py runs clean
- [x] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/object_store/trace.md
- [x] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code
