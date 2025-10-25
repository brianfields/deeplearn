# Spec: Add Conversations to Admin Dashboard

## User Story

**As an** admin user of the learning platform,

**I want to** view and inspect learning coach conversations in the admin dashboard,

**So that** I can monitor user interactions, review conversation quality, and debug issues with the learning coach feature.

### User Experience Changes

**New Conversations Page (`/conversations`):**
- Admins will see a new "Conversations" link in the admin navigation
- The conversations page displays a paginated table of all learning coach conversations
- Each row shows: conversation title, user (linked), status, message count, created date, last message date
- Clicking a row expands to show conversation details inline (similar to flow runs pattern)
- Manual reload button to refresh the list

**Conversation Detail View (expanded row):**
- Full message transcript with all messages (user, assistant, system) in chronological order
- Conversation metadata displayed
- Links to:
  - Associated user detail page
  - Associated LLM requests (if any)
- Message details include: role, content, tokens used, cost estimate, timestamps

**User Detail Page Enhancement:**
- New "Recent Conversations" section added (similar to "Recent Sessions" and "Recent LLM Requests")
- Shows the user's most recent learning coach conversations
- Each conversation is clickable, linking to the dedicated conversation detail page
- Displays: conversation title, status, message count, last message date

**Navigation:**
- Admin shell navigation updated to include "Conversations" menu item
- Conversations are accessible from both the main navigation and user detail pages

---

## Requirements Summary

### What to Build

1. **Backend Admin Routes** - Add conversation endpoints to admin module
2. **Frontend Conversations List** - Paginated table view of all learning coach conversations
3. **Frontend Conversation Detail** - Full transcript view with metadata and links
4. **User Detail Integration** - Add recent conversations section to user detail page
5. **Navigation Update** - Add conversations link to admin navigation

### Constraints

- Read-only observability (no conversation editing or actions)
- Manual refresh only (no auto-polling)
- Focus on learning_coach conversation type only
- No filtering or search functionality in initial version
- Follow existing flow runs UX patterns
- Maintain modular architecture boundaries

### Acceptance Criteria

- [ ] Admin can view paginated list of all learning coach conversations
- [ ] Admin can expand a conversation to see full message transcript
- [ ] Admin can click through to user detail page from conversation
- [ ] Admin can click through to associated LLM requests from messages
- [ ] User detail page shows recent conversations for that user
- [ ] Navigation includes "Conversations" menu item
- [ ] All messages (user, assistant, system) are visible in transcript
- [ ] Message metadata (tokens, cost, timestamps) is displayed
- [ ] Pagination works correctly (50 items per page)
- [ ] Manual reload button refreshes data
- [ ] UI follows existing admin dashboard patterns and styling

---

## Cross-Stack Mapping

### Backend Changes

**Module: `admin`**

Files to modify:
- `backend/modules/admin/models.py` - Enhance existing conversation DTOs with additional fields
- `backend/modules/admin/service.py` - Update existing conversation methods for pagination and add user conversations
- `backend/modules/admin/routes.py` - Update existing conversation routes for pagination
- `backend/modules/admin/test_admin_unit.py` - Update existing tests and add new tests

**Existing Implementation Note:**
The backend already has:
- `GET /api/v1/admin/learning-coach/conversations` (with limit/offset)
- `GET /api/v1/admin/learning-coach/conversations/{conversation_id}`
- DTOs: `LearningCoachConversationSummaryAdmin`, `LearningCoachConversationDetail`, `LearningCoachMessageAdmin`
- Service methods: `list_learning_coach_conversations()`, `get_learning_coach_conversation()`

This spec enhances the existing implementation with:
- Pagination metadata (total_count, page, page_size, has_next)
- Message metadata (tokens, cost, llm_request_id, message_order)
- Status field on conversation summaries
- User-specific conversation queries for user detail page

**Module: `conversation_engine`**

No changes needed - existing public interface provides all required functionality.

---

### Frontend Changes (admin dashboard)

**Module: `admin`**

Files to modify:
- `admin/modules/admin/models.ts` - Add conversation types
- `admin/modules/admin/repo.ts` - Add conversation HTTP methods
- `admin/modules/admin/service.ts` - Add conversation service methods
- `admin/modules/admin/queries.ts` - Add React Query hooks
- `admin/modules/admin/store.ts` - Add conversation filters state
- `admin/modules/admin/components/users/UserDetail.tsx` - Add recent conversations section
- `admin/modules/admin/components/shared/Navigation.tsx` - Add conversations link
- `admin/modules/admin/service.test.ts` - Add unit tests

Files to create:
- `admin/modules/admin/components/conversations/ConversationsList.tsx` - Main list component
- `admin/modules/admin/components/conversations/ConversationDetails.tsx` - Expanded detail view
- `admin/modules/admin/components/conversations/MessageTranscript.tsx` - Message rendering component
- `admin/app/conversations/page.tsx` - Conversations list page
- `admin/app/conversations/[id]/page.tsx` - Individual conversation detail page

**Frontend Implementation Note:**
The frontend currently has NO conversation-related code. All components, types, queries, and pages need to be created from scratch, following the patterns established by the flow runs implementation.

---

## Implementation Checklist

### Backend Tasks

- [ ] Update conversation DTOs in `backend/modules/admin/models.py`:
  - Update `LearningCoachMessageAdmin` to include `tokens_used`, `cost_estimate`, `llm_request_id`, and `message_order` fields
  - Update `LearningCoachConversationSummaryAdmin` to include `status` field
  - Update `LearningCoachConversationsListResponse` to include pagination fields: `total_count`, `page`, `page_size`, `has_next`
  - Add `UserConversationSummary` DTO for recent conversations on user detail page
  - Update `UserDetail` to include `recent_conversations: list[UserConversationSummary]` field

- [ ] Update conversation methods in `backend/modules/admin/service.py`:
  - Update `list_learning_coach_conversations()` to support pagination (page/page_size instead of limit/offset)
  - Update `list_learning_coach_conversations()` to return total count and pagination metadata
  - Update `get_learning_coach_conversation()` to include message metadata (tokens, cost, llm_request_id)
  - Add `get_user_conversations(user_id, limit)` method to get recent conversations for a user
  - Update `get_user_detail()` to include recent conversations in the response

- [ ] Update conversation routes in `backend/modules/admin/routes.py`:
  - Update `GET /api/v1/admin/learning-coach/conversations` to use page/page_size query params (instead of limit/offset)
  - Routes already exist for list and detail - just need to update to match new pagination format
  - Update `GET /api/v1/admin/users/{user_id}` response to include recent conversations

- [ ] Add unit tests to `backend/modules/admin/test_admin_unit.py`:
  - Test `get_conversations()` with pagination
  - Test `get_conversation_detail()` with valid and invalid IDs
  - Test `get_user_conversations()` for user with and without conversations
  - Test updated `get_user_detail()` includes conversations

### Frontend Tasks

- [ ] Add conversation types to `admin/modules/admin/models.ts`:
  - `Conversation` interface (summary for list view) - map from `LearningCoachConversationSummaryAdmin`
  - `ConversationMessage` interface - map from `LearningCoachMessageAdmin`
  - `ConversationDetail` interface (with messages array) - map from `LearningCoachConversationDetail`
  - `ConversationsListResponse` interface - map from `LearningCoachConversationsListResponse`
  - `UserConversationSummary` interface for user detail page
  - Update `UserDetail` interface to include `recent_conversations: UserConversationSummary[]`
  - Add `ConversationFilters` type for store (page, page_size)

- [ ] Add conversation HTTP methods to `admin/modules/admin/repo.ts`:
  - `conversations.list(params)` - fetch paginated conversations from `/api/v1/admin/learning-coach/conversations`
  - `conversations.byId(id)` - fetch conversation detail from `/api/v1/admin/learning-coach/conversations/{id}`

- [ ] Add conversation service methods to `admin/modules/admin/service.ts`:
  - Map API responses to frontend DTOs
  - Handle conversation type filtering
  - Format dates and metadata

- [ ] Add React Query hooks to `admin/modules/admin/queries.ts`:
  - `useConversations(filters)` - for list view with pagination
  - `useConversation(id)` - for detail view

- [ ] Add conversation state to `admin/modules/admin/store.ts`:
  - `conversationFilters` state (page, page_size)
  - `setConversationFilters` action

- [ ] Create `admin/modules/admin/components/conversations/MessageTranscript.tsx`:
  - Component to render message history
  - Display role badges (user/assistant/system)
  - Show message content with proper formatting
  - Display metadata (tokens, cost, timestamp)
  - Link to LLM requests when available

- [ ] Create `admin/modules/admin/components/conversations/ConversationDetails.tsx`:
  - Component for expanded conversation view
  - Display conversation metadata
  - Render MessageTranscript component
  - Links to user detail page
  - Show conversation status and timestamps

- [ ] Create `admin/modules/admin/components/conversations/ConversationsList.tsx`:
  - Main list component following FlowRunsList pattern
  - Paginated table with expand/collapse rows
  - Columns: title, user (linked), status, message count, dates
  - Expand row to show ConversationDetails
  - Pagination controls
  - Manual reload button

- [ ] Create `admin/app/conversations/page.tsx`:
  - Page wrapper for ConversationsList component
  - Page title and layout

- [ ] Create `admin/app/conversations/[id]/page.tsx`:
  - Full-page conversation detail view
  - Use ConversationDetails component
  - Breadcrumb navigation back to list

- [ ] Update `admin/modules/admin/components/users/UserDetail.tsx`:
  - Add "Recent Conversations" section
  - Display user's recent learning coach conversations
  - Link each conversation to detail page
  - Show conversation title, status, message count, last message date

- [ ] Update `admin/modules/admin/components/shared/Navigation.tsx`:
  - Add "Conversations" navigation link
  - Position between "Flows" and "LLM Requests" (or appropriate location)

- [ ] Add unit tests to `admin/modules/admin/service.test.ts`:
  - Test conversation service methods
  - Test DTO mapping for conversations and messages

### Integration and Testing Tasks

- [ ] Ensure lint passes, i.e. ./format_code.sh runs clean.
- [ ] Ensure unit tests pass, i.e. (in backend) scripts/run_unit.py and (in mobile) npm run test both run clean.
- [ ] Ensure integration tests pass, i.e. (in backend) scripts/run_integration.py runs clean.
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs/specs/add-conversations-to-admin/trace.md.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code.

---

## Technical Notes

### Backend Architecture

- **Reuse learning_coach public interface** - Admin service already calls `learning_coach_provider()` which wraps conversation_engine
- **Existing routes** - Routes at `/api/v1/admin/learning-coach/conversations` already exist, need enhancement for pagination
- **No new database tables** - All data exists in `conversations` and `conversation_messages` tables
- **DTO enhancements** - Existing DTOs need additional fields for tokens, cost, llm_request_id, and pagination metadata
- **Pagination** - Update from limit/offset to page/page_size pattern (matching flow runs)

### Frontend Architecture

- **Follow flow runs pattern** - ConversationsList component will mirror FlowRunsList structure
- **Expandable rows** - Use same expand/collapse pattern as flow runs
- **React Query caching** - Leverage React Query for data fetching and caching
- **Consistent styling** - Use existing admin dashboard Tailwind classes and components

### Field Name Consistency

Backend → Frontend mapping (should be consistent):
- `conversation_id` → `conversation_id` (or `id` in Conversation type)
- `user_id` → `user_id`
- `conversation_type` → `conversation_type`
- `message_count` → `message_count`
- `created_at` → `created_at`
- `updated_at` → `updated_at`
- `last_message_at` → `last_message_at`

### Message Role Display

- **user** - Display with blue badge
- **assistant** - Display with green badge
- **system** - Display with gray badge (visible to admins)

### Performance Considerations

- Initial version focuses on correctness over optimization
- Pagination limits data transfer (50 items per page)
- React Query provides client-side caching
- No database indexes needed initially (conversation queries are simple)

---

## Out of Scope

- Conversation editing or status updates
- Conversation deletion
- Advanced filtering (by date, status, etc.)
- Search functionality
- Real-time updates / auto-refresh
- Conversation analytics or metrics
- Support for non-learning_coach conversation types
- Export functionality
- Conversation notes or annotations

These features can be added in future iterations if needed.
