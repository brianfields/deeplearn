# Photo Resource - Implementation Spec

## User Story

**As a** learner using the mobile app  
**I want to** take photos or choose photos from my library as learning resources  
**So that** I can quickly share visual materials (textbook pages, handwritten notes, diagrams, whiteboards) with the learning coach without manually typing out the content

### User Experience Changes

**Current State:**
- AddResourceScreen shows "Coming soon" placeholder for "Take a photo" option
- No photo library option exists

**New Experience:**
1. User taps "Take a photo" → Camera opens → Snap photo → Shows progress: "Uploading and analyzing your photo..." → Returns to learning coach with "I've received your photo. Let me analyze it..." response
2. User taps "Choose a photo" (new option) → Photo library opens → Select photo → Same upload/analysis flow
3. During processing (2-5 seconds typical):
   - Photo uploads to S3 (ImageModel)
   - OpenAI Vision API extracts: detailed description + visible text (OCR)
   - Resource created with `resource_type: 'photo'`
4. Learning coach immediately has context from the photo for unit creation

**Permission Handling:**
- Standard iOS/Android permissions requested when user first taps camera/photo library
- Uses Expo's permission system (automatic via app.json config)
- If denied: shows alert with instructions to enable in Settings

---

## Requirements Summary

### What to Build

A photo resource upload system that allows learners to capture or select photos as learning materials. Photos are:
- Captured via device camera OR selected from photo library
- Uploaded to S3 as images (ImageModel, not DocumentModel)
- Analyzed by OpenAI Vision API to extract text description + OCR
- Stored as resources with `resource_type='photo'`
- Usable in learning coach conversations immediately

### Constraints

- **v1 scope**: Mobile-only; one photo at a time; no photo editing
- **Photo formats**: JPEG, PNG, HEIC (standard iOS/Android formats)
- **Size limits**: Use standard photo library images (no explicit size limit beyond S3 quotas; vision API handles resizing)
- **Extraction**: OpenAI Vision (GPT-4o or GPT-4 Vision) for description + OCR
- **Online-only**: Photo upload requires network connection (learning coach is online-only)
- **Progress feedback**: Show upload + analysis progress; don't allow navigation away during upload
- **Future expansion**: Code includes comments for future multi-photo support

### Acceptance Criteria

- [x] User can tap "Take a photo" and capture a photo with device camera
- [x] User can tap "Choose a photo" and select from photo library
- [x] Photos are uploaded to object_store as ImageModel (with presigned URLs)
- [x] OpenAI Vision API extracts detailed description + visible text from photos
- [x] Resources are created with `resource_type='photo'` and linked to ImageModel
- [x] Learning coach receives extracted text and can reference photo content
- [x] Progress indicator shows during upload + analysis (no background processing)
- [x] Permission errors are handled gracefully with user-friendly messages
- [x] Existing resource features (file upload, URL) continue to work unchanged

---

## Cross-Stack Module Mapping

### Backend Modules

#### MODIFY: `modules/resource`

**Purpose**: Add photo upload and vision-based text extraction

**Files to edit:**
- `models.py` - Add `object_store_image_id` column to ResourceModel
- `service/facade.py` - Add `upload_photo_resource()` method
- `service/extractors.py` - Add `extract_text_from_photo()` using OpenAI Vision
- `service/dtos.py` - Add `PhotoResourceCreate` DTO
- `routes.py` - Add `POST /api/v1/resources/upload-photo` endpoint
- `test_resource_unit.py` - Add tests for photo upload and vision extraction

**Key changes:**
- New DTO: `PhotoResourceCreate(user_id, filename, content_type, content, file_size)`
- New service method: `upload_photo_resource()` orchestrates upload → vision API → persistence
- New extractor: `extract_text_from_photo(image_url, llm_service)` calls vision API with prompt
- New route: `POST /upload-photo` (multipart/form-data) returns `ResourceRead`
- Database: Add nullable `object_store_image_id` FK column to resources table

#### MODIFY: `modules/llm_services`

**Purpose**: Ensure vision API support for image content

**Files to potentially edit:**
- `types.py` - Extend `LLMMessage` to support image content (if needed)
- `providers/openai.py` - Verify vision API message format support
- `service.py` - Ensure `generate_response()` handles vision requests

**Key changes:**
- Verify that `generate_response()` with GPT-4o/GPT-4-vision can accept image URLs
- May need to support `content` as `list[dict]` (with text + image_url parts) instead of just `str`
- If changes needed: Update `LLMMessage.content` type and OpenAI provider's message conversion

### Frontend Modules (Mobile)

#### MODIFY: `mobile/modules/resource`

**Purpose**: Add camera capture and photo library selection UI

**Files to edit:**
- `models.ts` - Add `PhotoResourceCreate` interface
- `repo.ts` - Add `uploadPhotoResource()` method
- `service.ts` - Add `uploadPhotoResource()` with validation
- `public.ts` - Add `uploadPhotoResource` to public interface
- `queries.ts` - Add `useUploadPhotoResource()` mutation
- `screens/AddResourceScreen.tsx` - Implement camera + photo library functionality
- `test_resource_unit.ts` - Add tests for photo service logic

**Key changes:**
- Install `expo-image-picker` dependency
- Add camera permission request to app.json
- Replace placeholder button handlers with actual camera/library logic
- Add "Choose a photo" button (new option in same section)
- Show progress modal during upload + analysis (with explanation text)
- Handle permission errors, upload errors, network errors
- Add comments for future multi-photo expansion

---

## Implementation Checklist

### Phase 1: Database Schema & Backend Foundation

**Goal**: Set up database schema and core backend models/DTOs for photo resources.

#### Database Migration

- [x] Update `modules/resource/models.py`:
  - [x] Add `object_store_image_id: Mapped[uuid.UUID | None]` column with FK to images.id
  - [x] Add index on `object_store_image_id` if needed for performance
- [x] Generate Alembic migration: `cd backend && alembic revision --autogenerate -m "Add image_id to resources table"` (manual revision created due to missing DB connection)
- [x] Review migration file to ensure both `object_store_document_id` and `object_store_image_id` are nullable
- [ ] Run migration: `cd backend && alembic upgrade head`
  - Blocked locally: requires `DATABASE_URL` configuration before Alembic can connect.

#### Backend DTOs

- [x] Update `modules/resource/service/dtos.py`:
  - [x] Add `PhotoResourceCreate` DTO with fields: user_id, filename, content_type, content, file_size
  - [x] Ensure DTO has proper validation and type hints

---

### Phase 2: Vision API Integration (Backend)

**Goal**: Implement OpenAI Vision API integration for photo text extraction.

#### LLM Services Module (Vision Support)

- [x] Check `modules/llm_services/types.py`:
  - [x] Determine if `LLMMessage.content` needs to support structured content (list[dict] for vision)
  - [x] If yes: Update `LLMMessage` dataclass to accept `content: str | list[dict[str, Any]]`
  - [x] If no: Document that vision images must be passed as URLs in string content with special formatting (not required because structured content is already supported)
- [x] Check `modules/llm_services/providers/openai.py`:
  - [x] Verify `_convert_messages_to_gpt5_input()` or equivalent handles vision content
  - [x] Ensure GPT-4o or GPT-4-vision-preview model can receive messages with image URLs
  - [x] Test that image_url format is correct: `{"type": "image_url", "image_url": {"url": "https://..."}}`
  - [x] If changes needed: Update message conversion to detect image URLs and structure appropriately
- [x] Update `modules/llm_services/test_llm_services_unit.py`:
  - [x] Add test for vision request with image URL (if LLMMessage extended)

#### Resource Module (Vision Extraction)

- [x] Update `modules/resource/service/extractors.py`:
  - [x] Add `extract_text_from_photo(image_url: str, llm_service: LLMServicesProvider) -> str`
  - [x] Function calls `llm_service.generate_response()` with vision model (gpt-4o)
  - [x] Prompt instructs the model to return JSON with `description` and `visible_text` fields for learning context
  - [x] Return combined description + OCR as plain text string
  - [x] Handle errors (API failures, no text found, etc.)

---

### Phase 3: Backend Photo Upload Service & Routes

**Goal**: Implement complete backend photo upload workflow.

#### Resource Service (Photo Upload)

- [x] Update `modules/resource/service/facade.py`:
  - [x] Inject `llm_services_provider` into ResourceService constructor
  - [x] Update `resource_service_factory()` to provide llm_services dependency
- [x] Update `modules/resource/service/facade.py`:
  - [x] Add `upload_photo_resource(data: PhotoResourceCreate) -> ResourceRead` method
  - [x] Validate photo format (JPEG, PNG, HEIC via content_type)
  - [x] Upload to object_store as ImageModel (not DocumentModel): `object_store.upload_image()`
  - [x] Generate presigned URL for the uploaded image
  - [x] Call `extract_text_from_photo()` with presigned URL and llm_service
  - [x] Truncate extracted text if needed (same 100KB limit as files)
  - [x] Create ResourceModel with resource_type='photo', object_store_image_id, extracted_text
  - [x] Return ResourceRead DTO

#### Routes & Backend Tests

- [x] Update `modules/resource/routes.py`:
  - [x] Add `POST /api/v1/resources/upload-photo` endpoint
  - [x] Accept multipart/form-data with fields: user_id (form field), file (file upload)
  - [x] Call `service.upload_photo_resource()` and return ResourceRead
  - [x] Map exceptions to appropriate HTTP codes (400, 422, 500)
- [x] Update `modules/resource/test_resource_unit.py`:
  - [x] Add test for photo upload flow (mock object_store and llm_services)
  - [x] Add test for `extract_text_from_photo()` with mocked OpenAI response
  - [x] Add test for photo validation (invalid formats)
  - [x] Add test for truncation of long extracted text
  - [x] Add test for error handling (vision API failure, S3 failure)
- [x] Run backend unit tests to verify all new code: `cd backend && scripts/run_unit.py`

---

### Phase 4: Frontend Foundation & Dependencies

**Goal**: Set up frontend dependencies and data layer for photo uploads.

#### Dependencies & Configuration

- [x] Add `expo-image-picker` to `mobile/package.json`
- [x] Run `cd mobile && npm install`
- [x] Update `mobile/app.json` to include camera permissions:
  - [x] Add `ios.infoPlist.NSCameraUsageDescription`: "We need camera access to let you capture learning materials"
  - [x] Add `ios.infoPlist.NSPhotoLibraryUsageDescription`: "We need photo library access to let you select learning materials"
  - [x] Add `android.permissions`: `["CAMERA", "READ_EXTERNAL_STORAGE"]`
- [ ] Rebuild native app if necessary: `cd mobile && npm run ios:prebuild && npm run ios`

#### Frontend Data Layer

- [x] Update `mobile/modules/resource/models.ts`:
  - [x] Add `PhotoResourceCreate` interface: `{ userId: number; file: UploadableFile }`
  - [x] Ensure `UploadableFile` type supports photo metadata (uri, name, type, size)
- [x] Update `mobile/modules/resource/repo.ts`:
  - [x] Add `uploadPhotoResource(request: PhotoResourceCreate): Promise<ResourceApiResponse>`
  - [x] Construct FormData with user_id and file (same format as file upload)
  - [x] POST to `/api/v1/resources/upload-photo`
  - [x] Handle response and errors
- [x] Update `mobile/modules/resource/service.ts`:
  - [x] Add `uploadPhotoResource(request: PhotoResourceCreate): Promise<Resource>`
  - [x] Validate user_id and file fields
  - [x] Call `repo.uploadPhotoResource()` and map to DTO
  - [x] Return Resource DTO
- [x] Update `mobile/modules/resource/public.ts`:
  - [x] Add `uploadPhotoResource` to `ResourceServiceContract` type
  - [x] Expose method in provider function
- [x] Update `mobile/modules/resource/queries.ts`:
  - [x] Add `useUploadPhotoResource()` mutation hook
  - [x] On success: invalidate resource list queries
  - [x] Return mutation with isPending, error states

---

### Phase 5: Frontend UI Implementation

**Goal**: Implement camera capture and photo library selection UI.

#### AddResourceScreen UI

- [x] Update `mobile/modules/resource/screens/AddResourceScreen.tsx`:
  - [x] Import `expo-image-picker`: `import * as ImagePicker from 'expo-image-picker'`
  - [x] Replace `handlePhotoPlaceholder` with `handleTakePhoto` that:
  - [x] Requests camera permissions: `ImagePicker.requestCameraPermissionsAsync()`
  - [x] If denied: show Alert with instructions
  - [x] If granted: launch camera: `ImagePicker.launchCameraAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 1 })`
  - [x] On photo captured: call `photoMutation.mutate()` with photo data
  - [x] Show ActivityIndicator with text "Uploading and analyzing your photo..."
  - [x] Add `handleChoosePhoto` (new function) that:
  - [x] Requests photo library permissions: `ImagePicker.requestMediaLibraryPermissionsAsync()`
  - [x] If denied: show Alert with instructions
  - [x] If granted: launch picker: `ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 1 })`
  - [x] On photo selected: call `photoMutation.mutate()` with photo data
  - [x] Show ActivityIndicator with text "Uploading and analyzing your photo..."
  - [x] Add "Choose a photo" button in the "Take a photo" section (rename section to "Add a photo")
  - [x] Handle success: Alert user and call `handleResourceAttached()` if attaching to conversation
  - [x] Handle errors: Alert with user-friendly message
  - [x] Add comment: `// TODO: Future - support selecting multiple photos at once`
  - [x] Disable both buttons while upload is in progress

#### Frontend Tests

- [x] Update `mobile/modules/resource/test_resource_unit.ts`:
  - [x] Add test for `uploadPhotoResource()` service method
  - [x] Mock repo and verify correct data flow
- [x] Run frontend unit tests: `cd mobile && npm run test`

---

### Phase 6: Testing, Seed Data & Final Verification

**Goal**: Ensure all code works end-to-end and passes quality checks.

#### Seed Data

- [x] Update `backend/scripts/create_seed_data.py`:
  - [x] Create sample photo resources for test users (can use placeholder images)
  - [x] Link photo resources to sample learning coach conversations
  - [x] Ensure seed data includes variety of resource types (files, URLs, photos)

#### Quality Assurance

- [x] Ensure lint passes: `./format_code.sh --no-venv`
- [x] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [x] Ensure frontend unit tests pass: `cd mobile && npm run test`
- [x] Ensure integration tests pass: `cd backend && scripts/run_integration.py`
- [x] Follow the instructions in `codegen/prompts/trace.md` to ensure the user story is implemented correctly
- [x] Fix any issues documented during the tracing of the user story in `docs/specs/photo-resource/trace.md`
- [x] Follow the instructions in `codegen/prompts/modulecheck.md` to ensure the new code is following the modular architecture correctly
- [x] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Technical Notes

### OpenAI Vision API Usage

**Model Selection:**
- Use `gpt-4o` (has native vision capabilities, faster and cheaper than gpt-4-vision-preview)
- Fallback to `gpt-4-vision-preview` if gpt-4o unavailable

**Message Format:**
```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "This image is being added as learning material. Please provide: 1) A detailed description of what's shown in the image, 2) Any text visible in the image (OCR). Format your response as a comprehensive text description suitable for learning context."
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://presigned-s3-url.com/image.jpg"
                }
            }
        ]
    }
]
```

**Response Handling:**
- Extract text from response content
- Combine description + OCR into single string
- Truncate if exceeds 100KB (same as other resource types)
- Store in `ResourceModel.extracted_text` field

### Database Schema Change

**Add to ResourceModel:**
```python
object_store_image_id: Mapped[uuid.UUID | None] = mapped_column(
    PostgresUUID(as_uuid=True), 
    ForeignKey("images.id"), 
    nullable=True
)
```

**Rationale:**
- Resources can link to EITHER documents (files) OR images (photos)
- Both FKs are nullable; exactly one should be non-null for file_upload/photo types
- URL resources have both as null
- Future: Could add validation constraint to ensure mutual exclusivity

### Photo Upload Flow (Backend)

1. **Receive upload** (`POST /upload-photo`)
   - Multipart form data: user_id (int), file (image bytes)
   - Validate content_type is image/* (JPEG, PNG, HEIC)

2. **Upload to S3** (via object_store)
   - Call `object_store.upload_image(ImageCreate(...))`
   - Returns `ImageRead` with S3 location and ID
   - Generate presigned URL (24hr expiry) for vision API access

3. **Extract text via vision** (via llm_services)
   - Call `llm_services.generate_response()` with gpt-4o model
   - Send message with text prompt + image_url
   - Receive description + OCR as string

4. **Create resource** (via resource repo)
   - Create `ResourceModel` with:
     - resource_type='photo'
     - object_store_image_id=<image_id>
     - extracted_text=<vision_response>
     - extraction_metadata={'source': 'photo', 'model': 'gpt-4o', ...}
   - Return `ResourceRead` DTO

### Photo Upload Flow (Frontend)

1. **User taps button** ("Take a photo" or "Choose a photo")
2. **Request permissions** (camera or library)
   - If denied: show Alert with settings instructions
   - If granted: proceed to capture/select
3. **Capture/select photo**
   - expo-image-picker returns: `{ uri, width, height, type, fileName }`
   - Show progress modal: "Uploading and analyzing your photo..."
4. **Upload photo**
   - Call `useUploadPhotoResource().mutate()`
   - Disable buttons during upload (prevent duplicate)
5. **Handle response**
   - Success: dismiss modal, call `handleResourceAttached()` if in conversation
   - Error: show Alert with error message, re-enable buttons

### Error Handling

**Backend:**
- Invalid image format → 400 Bad Request: "Unsupported image format. Please use JPEG, PNG, or HEIC."
- Vision API failure → 422 Unprocessable Entity: "Failed to analyze image. Please try again."
- S3 upload failure → 500 Internal Server Error: "Failed to upload image. Please try again."

**Frontend:**
- Permission denied → Alert: "Camera/Photo Library access is required. Please enable in Settings."
- Network error → Alert: "Upload failed. Please check your connection and try again."
- Upload timeout → Alert: "Upload is taking too long. Please try a smaller photo."

### Performance Considerations

**Photo Size:**
- No explicit resize in v1 (keep it simple)
- OpenAI Vision API accepts up to 20MB images (handles resizing server-side)
- Mobile photos typically 2-5MB (acceptable)
- Future optimization: resize large photos client-side before upload

**Processing Time:**
- S3 upload: 1-2 seconds (depends on network)
- Vision API: 2-5 seconds (depends on image complexity)
- Total: 3-7 seconds typical
- Show progress indicator to manage user expectations

**Cost:**
- Vision API: ~$0.01 per image (gpt-4o vision pricing)
- S3 storage: ~$0.023 per GB per month
- Acceptable for learning use case (not high volume)

### Future Enhancements (Out of Scope for v1)

- [ ] Multiple photos at once (batch upload)
- [ ] Photo editing before upload (crop, rotate, adjust brightness)
- [ ] Client-side image compression/resize
- [ ] Photo preview before upload (confirm selection)
- [ ] Retry failed uploads automatically
- [ ] Background upload (allow navigation during upload)
- [ ] Photo library album selection
- [ ] Video resource support (extract frames + audio transcript)
- [ ] Handwriting recognition optimization (specialized OCR model)
- [ ] Offline photo queue (cache photos locally, upload when online)

---

## Dependencies

### Backend

**No new dependencies required:**
- OpenAI SDK already installed (supports vision)
- object_store module already handles image uploads
- llm_services module supports GPT-4o

### Frontend

**New dependency:**
- `expo-image-picker` (camera + photo library access)
  - Version: Latest compatible with Expo SDK ~53
  - Installation: `npm install expo-image-picker`
  - Permissions: Configured via app.json

**Existing dependencies used:**
- `react-native-document-picker` (for file uploads, unchanged)
- `expo-file-system` (for file I/O, may be used indirectly)
- `@tanstack/react-query` (for mutations/queries)

---

## Testing Strategy

### Backend Unit Tests

**`test_resource_unit.py`:**
- Test `upload_photo_resource()` with valid photo data
- Test `extract_text_from_photo()` with mocked LLM response
- Test photo format validation (reject non-images)
- Test extracted text truncation (over 100KB)
- Test error handling (vision API failure, S3 failure)

**Mock strategy:**
- Mock `object_store_provider()` to return fake ImageRead
- Mock `llm_services_provider()` to return fake vision response
- Use `AsyncMock` for async methods
- Verify correct data flow and DTO mapping

### Frontend Unit Tests

**`test_resource_unit.ts`:**
- Test `uploadPhotoResource()` service method
- Test validation (invalid userId, missing file)
- Test error handling (network failure, API error)

**Mock strategy:**
- Mock `infrastructureProvider().request()` to return fake responses
- Test both success and error paths
- Verify DTO mapping is correct

### Integration Tests

**No new integration tests needed:**
- Existing resource integration tests cover end-to-end upload flow
- Photo upload follows same pattern as file upload
- Manual testing via mobile app sufficient for v1

### Manual Testing Checklist

- [ ] Take photo with camera → uploads successfully → learning coach receives description
- [ ] Choose photo from library → uploads successfully → learning coach receives description
- [ ] Test with photo containing text → verify OCR extracts visible text
- [ ] Test with photo without text → verify description-only response
- [ ] Deny camera permission → verify graceful error message
- [ ] Deny library permission → verify graceful error message
- [ ] Test with poor network → verify timeout/error handling
- [ ] Test with large photo (>10MB) → verify upload completes
- [ ] Test during active conversation → verify resource attaches to conversation
- [ ] Test without conversation → verify resource saves to library
- [ ] Verify existing file/URL uploads still work (no regression)

---

## Rollout Plan

**Phase 1: Development (1 week)**
- Implement backend photo upload + vision extraction
- Implement frontend camera + library UI
- Unit tests for all new code

**Phase 2: Testing (2-3 days)**
- Manual testing on iOS and Android devices
- Test with various photo types (text-heavy, diagrams, handwriting)
- Verify no regressions in existing features

**Phase 3: Deployment**
- Backend deploys first (new endpoints, backward compatible)
- Mobile app update required (new dependency, UI changes)
- No database migration issues (nullable column, backward compatible)

**Phase 4: Monitoring**
- Track photo upload success rate
- Monitor vision API costs and latency
- Collect user feedback on photo quality/OCR accuracy

---

## Success Metrics

- **Adoption:** % of learning coach conversations that include photo resources
- **Success rate:** % of photo uploads that complete successfully
- **Performance:** Average time from photo capture to resource creation (<10 seconds target)
- **Quality:** User feedback on OCR accuracy and description usefulness
- **Cost:** Vision API cost per active user per month (<$1 target)
