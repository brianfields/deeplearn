# Resource Upload - Implementation Spec

## User Story

**As a** learner creating a personalized unit with the learning coach  
**I want** to upload files or share links to source material during the conversation  
**So that** the coach can build a unit tailored to my specific materials without me having to manually summarize them

---

## Requirements Summary

### What to Build

A complete resource upload system that allows learners to provide source materials (files and URLs) during learning coach conversations. Resources are:
- Uploaded to S3 (files) or fetched/scraped (URLs)
- Text content extracted and stored (max 100KB)
- Associated with conversations and units
- Reusable across multiple unit creations
- Viewable in a resource library

### Constraints

- **v1 scope**: Mobile-only uploads; admin read-only views
- **File types**: PDF, DOCX, PPTX, TXT, MD (up to 100MB)
- **URL types**: Web pages, YouTube videos, direct document links
- **Size limits**: 100MB file size, 100KB extracted text, 5 pages max for large PDFs
- **Extraction**: TXT/MD fully implemented, PDF basic text extraction, others as placeholders
- **Architecture**: Modular design supporting future enhancements (OCR, advanced parsing, content creator integration)
- **No deletion**: Resources persist permanently (no deletion UI/API in v1)

### Acceptance Criteria

- [ ] User can upload files (TXT, MD, PDF) during learning coach conversation
- [ ] User can paste URLs (with basic validation and error handling)
- [ ] Files are stored in S3; metadata and extracted text stored in database
- [ ] Large PDFs (>5 pages) prompt user to select which 5 pages to analyze
- [ ] Learning coach immediately acknowledges and references uploaded resources
- [ ] Resources are linked to the units they help create
- [ ] User can view their resource library and select previous resources for reuse
- [ ] Admin can view resources per unit and per user (read-only)
- [ ] Extraction placeholders exist for DOCX, PPTX, YouTube, web scraping (future implementation)

---

## Cross-Stack Module Mapping

### Backend Modules

#### NEW: `modules/resource`
**Purpose**: Central module for resource upload, storage, and text extraction

**Files to create:**
- `models.py` - `ResourceModel` table
- `repo.py` - Database access
- `service.py` - Orchestration and DTO mapping
- `service/extractors.py` - Text extraction implementations
- `public.py` - Cross-module interface
- `routes.py` - HTTP endpoints
- `test_resource_unit.py` - Unit tests

#### MODIFY: `modules/content`
**Files to edit:**
- `models.py` - Add `UnitResourceModel` join table
- `repo.py` - Add resource-unit linking methods
- `service/unit_handler.py` - Add method to attach resources during unit creation

#### MODIFY: `modules/learning_coach`
**Files to edit:**
- `conversation.py` - Add `add_resource()` session method
- `service.py` - Include resources in LLM context
- `prompts/system_prompt.md` - Update to acknowledge resource usage
- `routes.py` - Update DTOs to include resources
- `test_learning_coach_unit.py` - Add resource integration tests

#### MODIFY: `modules/object_store`
**Files to edit:**
- `models.py` - Add `DocumentModel` table
- `repo.py` - Add document repo methods
- `service.py` - Add document upload method
- `public.py` - Expose document upload in protocol

### Frontend Modules (Mobile)

#### NEW: `mobile/modules/resource`
**Purpose**: Resource upload UI and management

**Files to create:**
- `models.ts` - TypeScript interfaces
- `repo.ts` - HTTP API calls
- `service.ts` - Business logic
- `public.ts` - Cross-module interface
- `queries.ts` - React Query hooks
- `screens/AddResourceScreen.tsx` - Upload/URL/reuse screen
- `screens/ResourceLibraryScreen.tsx` - User's resource list
- `screens/ResourceDetailScreen.tsx` - Full resource view
- `components/ResourceCard.tsx` - List item component
- `components/ResourcePicker.tsx` - Previous resource selector
- `test_resource_unit.ts` - Unit tests

#### MODIFY: `mobile/modules/learning_coach`
**Files to edit:**
- `screens/LearningCoachScreen.tsx` - Add "+" button and initial upload button
- `models.ts` - Add resources to session state
- `service.ts` - Add attach resource method
- `repo.ts` - Add attach resource API call
- `queries.ts` - Add attach resource mutation

#### MODIFY: `mobile/modules/content`
**Files to edit:**
- `models.ts` - Add resources field to UnitDetail
- `service.ts` - Include resources in unit detail response

### Admin Interface

#### MODIFY: `admin/modules/admin`
**Files to edit:**
- `components/UnitDetailView.tsx` - Add "Source Resources" section
- `components/UserDetailView.tsx` - Add "Resources" section
- `services/contentService.ts` - Fetch unit resources
- `services/userService.ts` - Fetch user resources

---

## Implementation Checklist

### Phase Overview

This implementation is organized into 6 phases, each building on the previous:

**Phase 1: Backend Foundation (Database & Core Module)**
- Set up database tables (resources, unit_resources, documents)
- Build core resource module (models, repo, service, routes)
- Add document support to object_store
- Add resource-unit linking to content module

**Phase 2: Backend Integration (Learning Coach)**
- Integrate resources into learning coach conversations
- Add resource context to LLM prompts
- Update conversation DTOs to include resources

**Phase 3: Mobile Frontend (Resource Module)**
- Build complete resource module UI
- File upload, URL input, resource library
- Resource selection and reuse

**Phase 4: Mobile Frontend (Learning Coach Integration)**
- Add resource upload UI to learning coach screen
- Connect resource attachment to conversations
- Update content module to display resources

**Phase 5: Admin Interface (Read-Only Views)**
- Add resource views to unit details
- Add resource views to user details

**Phase 6: Seed Data & Final Polish**
- Create sample resources
- Run full test suite
- Trace user story
- Verify architecture compliance

---

### Phase 1: Backend Foundation (Database & Core Module)

#### Backend - Database & Models

- [ ] Create `modules/resource/models.py` with `ResourceModel` (id, user_id, resource_type, source_url, filename, extracted_text, extraction_metadata, file_size, object_store_document_id FK, created_at, updated_at)
- [ ] Create `modules/content/models.py` addition: `UnitResourceModel` join table (unit_id, resource_id, added_at)
- [ ] Create `modules/object_store/models.py` addition: `DocumentModel` (id, user_id, s3_key, s3_bucket, filename, content_type, file_size, created_at, updated_at)
- [ ] Generate Alembic migration for new tables: `cd backend && alembic revision --autogenerate -m "Add resource and document tables"`
- [ ] Review and edit migration file if necessary
- [ ] Run migration to create tables: `cd backend && alembic upgrade head`

### Backend - Resource Module (Core)

- [ ] Create `modules/resource/__init__.py` to mark as a module
- [ ] Create `modules/resource/repo.py` with methods: create, get_by_id, list_by_user, get_by_unit, update_extracted_text
- [ ] Create `modules/resource/service/` directory for service submodules
- [ ] Create `modules/resource/service/__init__.py` to mark as a package
- [ ] Create `modules/resource/service/extractors.py` with:
  - [ ] `extract_text_from_txt()` - fully implemented
  - [ ] `extract_text_from_markdown()` - fully implemented  
  - [ ] `extract_text_from_pdf()` - basic text extraction (pypdf or pdfplumber)
  - [ ] `extract_text_from_docx()` - placeholder (raises NotImplementedError with message)
  - [ ] `extract_text_from_pptx()` - placeholder (raises NotImplementedError with message)
  - [ ] `extract_youtube_transcript()` - placeholder (raises NotImplementedError with message)
  - [ ] `scrape_web_page()` - placeholder (raises NotImplementedError with message)
- [ ] Create `modules/resource/service.py` with:
  - [ ] `upload_file_resource()` - validates file, uploads to S3 via object_store, extracts text, creates ResourceModel
  - [ ] `create_url_resource()` - validates URL, determines type (YouTube/web/direct doc), extracts/fetches content, creates ResourceModel
  - [ ] `get_resource()` - fetches resource with extracted text
  - [ ] `list_user_resources()` - returns user's resources sorted by created_at desc
  - [ ] `get_resources_for_unit()` - returns resources linked to unit
  - [ ] Helper: `_truncate_extracted_text()` - limits to 100KB
  - [ ] Helper: `_validate_file_size()` - max 100MB
  - [ ] Helper: `_prompt_for_page_selection()` - for large PDFs (return placeholder logic)
- [ ] Create `modules/resource/public.py` with `ResourceProvider` protocol exposing: get_resource, list_user_resources, get_resources_for_unit
- [ ] Create `modules/resource/routes.py` with endpoints:
  - [ ] `POST /api/v1/resources/upload` - file upload (multipart/form-data)
  - [ ] `POST /api/v1/resources/from-url` - URL resource creation
  - [ ] `GET /api/v1/resources` - list user's resources (query param: user_id)
  - [ ] `GET /api/v1/resources/{resource_id}` - get resource detail
- [ ] Register resource router in `backend/server.py`
- [ ] Add required Python dependencies to `backend/requirements.txt`: pypdf (or pdfplumber), python-multipart (if not present)
- [ ] Create `modules/resource/test_resource_unit.py` with tests for text extraction (TXT, MD, PDF basic)

#### Backend - Object Store Enhancement

- [ ] Add `modules/object_store/repo.py` DocumentRepo class with create, get_by_id, delete methods
- [ ] Add `modules/object_store/service.py` upload_document() method (similar to upload_image/audio)
- [ ] Update `modules/object_store/public.py` ObjectStoreProvider protocol to include upload_document()
- [ ] Add basic tests to `modules/object_store/test_object_store_unit.py` for document upload

#### Backend - Content Module Enhancement

- [ ] Add `modules/content/repo.py` methods: link_resource_to_unit(), get_resources_for_unit()
- [ ] Add `modules/content/service/unit_handler.py` method: attach_resources_to_unit(unit_id, resource_ids)
- [ ] Add route endpoint `GET /api/v1/units/{unit_id}/resources` to fetch resources for a unit
- [ ] Update existing integration tests if necessary to handle new join table

### Phase 2: Backend Integration (Learning Coach)

#### Backend - Learning Coach Integration

- [ ] Update `modules/learning_coach/conversation.py`:
  - [ ] Add `@conversation_session async def add_resource(*, _conversation_id, _user_id, resource_id)` method
  - [ ] Store resource_ids in conversation metadata
  - [ ] Modify `_generate_structured_reply()` to include resource context in LLM messages
  - [ ] Add route endpoint `POST /api/v1/learning-coach/conversations/{conversation_id}/resources` to attach resource to conversation
- [ ] Update `modules/learning_coach/service.py`:
  - [ ] Add `get_conversation_resources()` method that fetches ResourceRead objects for conversation
  - [ ] Add helper to build resource context string for LLM system prompt
- [ ] Update `modules/learning_coach/prompts/system_prompt.md` to include resource handling instructions
- [ ] Update `modules/learning_coach/routes.py` DTOs to include resources in LearningCoachSessionStateModel
- [ ] Add tests to `modules/learning_coach/test_learning_coach_unit.py` for resource integration

### Phase 3: Mobile Frontend (Resource Module)

#### Frontend - Resource Module (Mobile)

- [ ] Create `mobile/modules/resource/__init__.ts` to mark as a module
- [ ] Create `mobile/modules/resource/models.ts` with interfaces: Resource, ResourceSummary, CreateResourceRequest, AddResourceFromURLRequest
- [ ] Create `mobile/modules/resource/repo.ts` with HTTP methods calling backend endpoints
- [ ] Create `mobile/modules/resource/service.ts` with business logic and DTO mapping
- [ ] Create `mobile/modules/resource/public.ts` with ResourceProvider interface
- [ ] Create `mobile/modules/resource/queries.ts` with React Query hooks: useUploadResource, useAddResourceFromURL, useUserResources, useResourceDetail
- [ ] Create `mobile/modules/resource/screens/` directory for screens
- [ ] Create `mobile/modules/resource/components/` directory for components
- [ ] Add required npm dependencies to `mobile/package.json`: react-native-document-picker
- [ ] Create `mobile/modules/resource/nav.tsx` for resource navigation stack (ResourceLibrary, ResourceDetail, AddResource screens)
- [ ] Create `mobile/modules/resource/screens/AddResourceScreen.tsx`:
  - [ ] Four options: Upload file, Paste URL, Choose previous, Take photo
  - [ ] File picker integration (react-native-document-picker)
  - [ ] URL input with validation
  - [ ] Previous resources list (using useUserResources)
  - [ ] Photo option shows "Coming soon" placeholder
- [ ] Create `mobile/modules/resource/screens/ResourceLibraryScreen.tsx` displaying user's resources with search/filter
- [ ] Create `mobile/modules/resource/screens/ResourceDetailScreen.tsx` showing full resource details and units that used it
- [ ] Create `mobile/modules/resource/components/ResourceCard.tsx` for list display
- [ ] Create `mobile/modules/resource/components/ResourcePicker.tsx` for selecting from previous resources
- [ ] Create `mobile/modules/resource/test_resource_unit.ts` with unit tests for service logic

### Phase 4: Mobile Frontend (Learning Coach Integration)

#### Frontend - Learning Coach Integration (Mobile)

- [ ] Update `mobile/modules/learning_coach/screens/LearningCoachScreen.tsx`:
  - [ ] Add "+" button next to message input (always visible)
  - [ ] Add "Upload source material" button below greeting (visible until first message sent)
  - [ ] Both buttons navigate to AddResourceScreen
  - [ ] After resource added, show processing indicator then coach response
- [ ] Update `mobile/modules/learning_coach/models.ts` to include resources: ResourceSummary[] in session state
- [ ] Update `mobile/modules/learning_coach/service.ts` with attachResource(conversationId, resourceId) method
- [ ] Update `mobile/modules/learning_coach/repo.ts` with API call to attach resource endpoint
- [ ] Update `mobile/modules/learning_coach/queries.ts` with useAttachResource mutation
- [ ] Add tests to `mobile/modules/learning_coach/test_learning_coach_unit.ts` for resource attachment

#### Frontend - Content Module Enhancement (Mobile)

- [ ] Update `mobile/modules/content/models.ts` UnitDetail interface to include resources: ResourceSummary[]
- [ ] Update `mobile/modules/content/service.ts` to map resources from API response
- [ ] Update `mobile/modules/content/repo.ts` to fetch resources when getting unit details

### Phase 5: Admin Interface (Read-Only Views)

#### Admin Interface (Read-Only)

- [ ] Create `admin/modules/admin/components/resources/` directory for resource components (if it doesn't exist)
- [ ] Create `admin/modules/admin/components/resources/ResourceList.tsx` component for displaying resources
- [ ] Update `admin/modules/admin/components/UnitDetailView.tsx`:
  - [ ] Add "Source Resources" section
  - [ ] Fetch and display resources used for unit
  - [ ] Show filename/URL, upload date, extracted text preview
- [ ] Update `admin/modules/admin/components/UserDetailView.tsx`:
  - [ ] Add "Resources" section  
  - [ ] Fetch and display user's uploaded resources
  - [ ] Show upload dates, file sizes, which units used each resource
- [ ] Update `admin/lib/services/contentService.ts` to add getUnitResources(unitId) method
- [ ] Update `admin/lib/services/userService.ts` to add getUserResources(userId) method (or create if doesn't exist)

### Phase 6: Seed Data & Final Polish

#### Seed Data

- [ ] Update `backend/scripts/create_seed_data.py`:
  - [ ] Create sample resources for test users
  - [ ] Link resources to sample units
  - [ ] Include variety of resource types (text files, URLs as placeholders)

#### Testing & Quality

- [ ] Ensure lint passes, i.e. './format_code.sh --no-venv' runs clean.
- [ ] Ensure backend unit tests pass, i.e. cd backend && scripts/run_unit.py
- [ ] Ensure frontend unit tests pass, i.e. cd mobile && npm run test
- [ ] Ensure integration tests pass, i.e. cd backend && scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/resource-upload/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Technical Notes

### Resource Types
- `file_upload` - User uploaded a file (stored in S3)
- `url` - User provided a URL (content fetched/scraped)
- `photo` - User took a photo (uses ImageModel, OCR extraction - placeholder)

### Text Extraction Strategy (v1)
**Fully Implemented:**
- TXT: Read and decode (UTF-8)
- MD: Read and decode, preserve structure (headers, lists)
- PDF: Use pypdf or pdfplumber for basic text extraction (no OCR, no complex layouts)

**Placeholders (raise NotImplementedError with friendly message):**
- DOCX: "Word document parsing coming soon. Please convert to PDF or copy/paste text."
- PPTX: "PowerPoint parsing coming soon. Please convert to PDF or copy/paste text."
- YouTube: "YouTube transcript extraction coming soon. Please copy/paste the transcript."
- Web scraping: "Web page extraction coming soon. Please copy/paste the article text."
- Direct PDF links: "Direct document links coming soon. Please download and upload the file."

### Size Limit Handling
- Files >100MB: Reject at upload with error message
- Extracted text >100KB: Truncate and add note in metadata
- PDFs >5 pages: Prompt user to select 5 pages (placeholder: take first 5 pages with warning)

### LLM Context Integration
Resources are included in learning coach system prompt as:
```
## Source Materials Provided

The learner has provided the following materials for context:

1. [Filename/URL] (uploaded on [date])
   Extracted content:
   [first 500 words or up to 100KB total]

Use these materials to inform your coaching and unit design.
```

### API Response DTOs
```python
# Backend DTOs
class ResourceRead:
    id: str
    user_id: int
    resource_type: str  # file_upload | url | photo
    filename: str | None
    source_url: str | None
    extracted_text: str
    extraction_metadata: dict  # {pages_extracted, truncated, original_size, etc}
    file_size: int | None
    created_at: datetime
    
class ResourceSummary:
    id: str
    resource_type: str
    filename: str | None
    source_url: str | None
    file_size: int | None
    created_at: datetime
    preview_text: str  # First 200 chars of extracted_text
```

### Navigation Flow (Mobile)
```
LearningCoachScreen
  → Tap "+" or "Upload source material"
  → AddResourceScreen (4 options)
    → If "Upload file": Native file picker → Upload progress → Return to coach
    → If "Paste URL": URL input → Validation → Fetch progress → Return to coach
    → If "Choose previous": ResourcePicker modal → Select → Return to coach
    → If "Take photo": "Coming soon" message
  → After adding: Coach acknowledgment appears in conversation
```

---

## Future Enhancements (Out of Scope for v1)

- DOCX/PPTX text extraction
- YouTube transcript API integration
- Web scraping (BeautifulSoup/readability)
- Direct PDF/document link downloads
- Photo OCR (Tesseract or cloud OCR)
- Advanced PDF parsing (tables, images, complex layouts)
- Page selection UI for large PDFs
- Resource editing/deletion
- Resource sharing between users
- Content creator flow integration (using resources during lesson generation)
- Resource version history
- Automatic resource type detection
- Resource preview thumbnails
- Text similarity search across resources
- Resource tagging and categorization
