# Object Store Feature - User Description

The user wants to create an object_store module that handles file storage for images and audio files in S3, following the modular architecture patterns described in `docs/arch/backend.md`.

## Key Requirements:
- Store items (specifically images and audio files) in S3 object store
- Provide a clean, easy-to-use public interface
- Follow the established modular architecture patterns
- Modify existing code in `backend/modules/object_store/` to meet architectural requirements
- Create an audio file version similar to what exists for images

## Existing Code:
The `backend/modules/object_store/` directory contains:
- `models.py` - Contains `ImageModel` and partial `AudioModel` with S3 references and metadata
- `image_service.py` - Image upload, storage, and retrieval service using S3 and PostgreSQL
- `s3_provider.py` - S3 provider implementation for general file storage

## Architectural Compliance Needed:
- Convert to proper module structure (models.py, repo.py, service.py, public.py, routes.py)
- Ensure service returns DTOs (not ORM models)
- Create proper public interface following Protocol pattern
- Update import paths and dependencies to match project structure
- Add audio functionality equivalent to image functionality