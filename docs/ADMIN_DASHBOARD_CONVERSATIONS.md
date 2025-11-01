# Admin Dashboard: Teaching Assistant Conversations Support

## Overview

The admin dashboard has been updated to display both **Learning Coach** and **Teaching Assistant** conversations. This allows administrators to review and monitor all conversation types in a unified interface.

## Changes Made

### Backend (Python)

#### Models (`backend/modules/admin/models.py`)
- Added `ConversationDetail` - Generic conversation detail DTO with `conversation_type` field
- Added `ConversationSummary` - Generic conversation summary with `conversation_type` field  
- Added `ConversationsListResponse` - Generic list response for all conversation types
- Added `ConversationMessageAdmin` alias for backward compatibility
- Preserved all existing Learning Coach DTOs for backward compatibility

#### Service (`backend/modules/admin/service.py`)
- Added `TEACHING_ASSISTANT_CONVERSATION_TYPE` constant
- Implemented `list_conversations()` - Lists both conversation types with optional filtering
  - Query parameter: `conversation_type` (optional: "learning_coach", "teaching_assistant", or None for all)
  - Automatically detects type based on metadata (presence of "topic" field)
- Implemented `get_conversation()` - Retrieves any conversation type
- Updated `get_user_conversations()` - Now fetches and combines both conversation types
- Added helper methods:
  - `_fetch_conversations_by_type()` - Fetches conversations by specific type
  - `_count_conversations()` - Counts conversations with optional filtering

#### Routes (`backend/modules/admin/routes.py`)
- Added `GET /api/v1/admin/conversations` - Lists all conversations (both types)
- Added `GET /api/v1/admin/conversations/{conversation_id}` - Gets conversation details
- Preserved backward compatibility: `/api/v1/admin/learning-coach/conversations/*` routes still work

### Frontend (TypeScript/React)

#### Models (`admin/modules/admin/models.ts`)
- Updated `ConversationSummary` - Added `conversation_type: string` field
- Updated `ConversationDetail` - Added `conversation_type: string` field
- Updated `ApiConversationSummary` - Added `conversation_type: string` field
- Updated `ApiConversationDetail` - Added `conversation_type: string` field

#### Repository (`admin/modules/admin/repo.ts`)
- Updated conversations endpoint to use new generic `/conversations` endpoint

#### Components

**ConversationsList.tsx**
- Added `ConversationTypeBadge` component to display conversation type
  - Blue badge for "Learning Coach" conversations
  - Purple badge for "Teaching Assistant" conversations
- Added "Type" column to the conversations table
- Updated description text
- Maintains expandable row functionality

**UserDetail.tsx**
- Updated "Recent conversations" section to include conversation type
- Added "Type" column with colored badges
- Updated description to mention both conversation types

#### Pages

**app/conversations/page.tsx**
- Updated title and description to mention both conversation types

## How It Works

### Conversation Type Detection
The system automatically detects conversation type based on metadata:
- If metadata contains `"topic"` field → `learning_coach` conversation
- Otherwise → `teaching_assistant` conversation

### Admin Dashboard Features

**Conversations Tab:**
- View all conversations (both types) in a unified list
- Each row shows:
  - Conversation title
  - **Type badge** (Coach or Assistant)
  - User ID
  - Status
  - Message count
  - Created date
  - Last message date
- Click "View details" to see full transcript
- Expand rows to see conversation details inline
- Filter by pagination

**User Detail Page:**
- "Recent conversations" section now shows both types
- Sorted by recency (combined from both types)
- Shows up to 5 recent conversations
- Type badge distinguishes between Learning Coach and Teaching Assistant

## API Endpoints

### New Generic Endpoints
```
GET  /api/v1/admin/conversations
     Query: page, page_size, conversation_type (optional)
     Response: ConversationsListResponse

GET  /api/v1/admin/conversations/{conversation_id}
     Response: ConversationDetail
```

### Legacy Endpoints (Still Supported)
```
GET  /api/v1/admin/learning-coach/conversations
GET  /api/v1/admin/learning-coach/conversations/{conversation_id}
```

## Backward Compatibility

✅ All existing learning coach endpoints and DTOs remain unchanged
✅ No breaking changes to existing functionality
✅ New generic endpoints are additive

## Type Badges

### Learning Coach
- Background: `bg-blue-100`
- Text: `text-blue-800`
- Label: "Coach"

### Teaching Assistant
- Background: `bg-purple-100`
- Text: `text-purple-800`
- Label: "Assistant"

## Future Enhancements

Potential improvements:
1. Add filters to show only one conversation type
2. Add search/filter by context (unit, lesson, etc.)
3. Export conversation transcripts
4. Real-time conversation monitoring
5. Conversation analytics dashboard
