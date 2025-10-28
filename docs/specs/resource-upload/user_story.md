# Resource Upload - User Story

## User Story

**As a** learner creating a personalized unit with the learning coach  
**I want** to upload files or share links to source material during the conversation  
**So that** the coach can build a unit tailored to my specific materials without me having to manually summarize them

---

## User Experience Changes

### Mobile App (Primary Experience)

#### Initial Coach Screen
- When the learning coach conversation starts, the user sees a friendly button inviting them to "Upload source material" (optional)
- The button remains visible until the user **sends their first message**
- At any point during the conversation, the user can tap the "+" button next to the message input

#### Resource Upload Flow

**1. Tap "+" button** → Opens a new "Add Resource" screen with four options:
   - **Upload a file** (file picker: PDF, DOCX, PPTX, TXT, MD)
   - **Paste a URL** (web page, YouTube video, direct document link)
   - **Choose from previous resources** (list of user's uploaded resources)
   - **Take a photo** (camera → OCR, placeholder for v1)

**2. After selection:**
   - File upload → Shows progress indicator → "Processing..."
   - URL paste → Basic validation → "Fetching content..."
   - For large PDFs (>5 pages) → Prompt: "This document has 47 pages. Which 5 pages should I focus on?"

**3. Coach acknowledgment:**
   - Returns to conversation with coach message: "Got it! I've reviewed [filename/URL]. Based on what I see..."
   - Coach immediately starts referencing the resource in its responses

**4. During conversation:**
   - Coach can say things like: "Based on slide 7 in your deck..." or "The article mentions X, so let's build a lesson on..."
   - User can upload multiple resources; each is acknowledged and incorporated

**5. Unit creation:**
   - When the unit is generated, it's linked to the resources that were used
   - User can later see which resources informed which units

#### Resource Library (new screen)
- Accessible from user profile or settings
- Shows all resources the user has uploaded
- Each resource shows: filename/URL, upload date, preview of extracted text, which units used it
- Can select resources to reuse in new conversations

### Admin Interface (Read-Only)

#### Unit Detail Page
- Existing page enhanced with new "Source Resources" section showing:
  - List of resources used to create this unit
  - For each: filename/URL, upload date, extracted text preview
  - Link to full resource details

#### User Detail Page
- Existing page enhanced with new "Resources" section showing:
  - All resources this user has uploaded
  - Upload dates, file sizes, which units used each resource

---

## Acceptance Criteria

- [ ] User can upload files (PDF, DOCX, PPTX, TXT, MD up to 100MB) during learning coach conversation
- [ ] User can paste URLs (web pages, YouTube videos) during learning coach conversation
- [ ] Files are stored in S3; metadata and extracted text (max 100KB) stored in database
- [ ] YouTube videos extract transcript; web pages extract main article content
- [ ] Large PDFs (>5 pages) prompt user to select which 5 pages to analyze
- [ ] Learning coach immediately acknowledges and references uploaded resources
- [ ] Resources are linked to the units they help create
- [ ] User can view their resource library and select previous resources for reuse
- [ ] Admin can view resources per unit and per user (read-only) on existing detail pages
- [ ] Basic URL validation with error reporting
- [ ] Architecture supports future enhancements (direct PDF links, photo OCR, content creator integration)
