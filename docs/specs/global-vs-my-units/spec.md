# Spec: Curated "My Units" with Catalog Browser

## User Story

**As a** mobile learner  
**I want to** curate my own list of learning units from the global catalog  
**So that** I only see units that are relevant to my learning goals, reducing clutter

### Acceptance Criteria

1. **My Units Display**
   - When I view the units list, I see only:
     - Units I created (always included automatically)
     - Global units I've explicitly added to "My Units"
   - I no longer see all globally shared units by default

2. **Catalog Access**
   - I can tap a "Browse Catalog" button on the units list screen
   - This opens a full-screen overlay showing all globally shared units
   - I can dismiss the overlay with a downward swipe gesture (standard iOS pattern)

3. **Catalog Search**
   - In the catalog overlay, I can search for units by title
   - Search results update as I type
   - I can see which units are already in "My Units" (visual indicator)

4. **Add to My Units**
   - From the catalog, I can tap a button/icon to add a unit to "My Units"
   - The unit immediately appears in my units list
   - The catalog shows that this unit is now in "My Units"

5. **Remove from My Units**
   - From my units list, I can remove a unit I previously added from the catalog
   - Units I created cannot be removed (they're always in "My Units")
   - My learning progress is preserved if I remove a unit (I can re-add it later and resume)

6. **Access Retention**
   - If I've added a unit to "My Units," I retain access even if the owner later un-shares it globally
   - The unit remains in my list and I can continue learning

### UI Changes

**Mobile - Units List Screen:**
- Add "Browse Catalog" button (prominent placement near search/create buttons)
- Units displayed are filtered to "My Units" only
- Add remove/delete action for catalog-added units (swipe-to-delete or similar)
- Units created by user cannot be removed

**Mobile - Catalog Browser Screen (New):**
- Full-screen modal with swipe-to-dismiss gesture
- Search bar at top (search by title)
- List of all global units
- Visual indicator showing which units are in "My Units"
- "Add to My Units" / "Remove from My Units" toggle button on each unit card

---

## Requirements Summary

### What to Build

1. **Backend: New join table** (`user_my_units`) to track which global units a user has added to "My Units"
2. **Backend: API endpoints** for adding/removing units from "My Units"
3. **Backend: Updated filtering logic** in catalog service to return only "My Units"
4. **Mobile: New catalog browser screen** with search and add/remove functionality
5. **Mobile: Updated units list screen** with "Browse Catalog" button and remove actions

### Constraints

- Mobile only (no admin/web changes)
- Search by title only (no advanced filters for now)
- User-created units always appear in "My Units" (cannot be removed)
- Progress data is retained when units are removed from "My Units"
- Users retain access to units they've added, even if later un-shared globally

### Acceptance Criteria

- User can browse global catalog from units list
- User can search catalog by title
- User can add/remove units to/from "My Units"
- Units list shows only "My Units" (owned + added from catalog)
- User-created units cannot be removed
- Progress is preserved when units are removed
- Lint passes (`./format_code.sh`)
- Unit tests pass (backend: `scripts/run_unit.py`, mobile: `npm run test`)
- Integration tests pass (backend: `scripts/run_integration.py`)
- Existing maestro e2e tests pass (mobile: `mobile/e2e`)

---

## Cross-Stack Module Mapping

### Backend

#### Module: `content` (existing)

**Files to modify:**
- `backend/modules/content/models.py` - Add `UserUnitCatalogMembershipModel`
- `backend/modules/content/repo.py` - Add methods for catalog membership queries
- `backend/modules/content/service.py` - Add business logic for add/remove operations
- `backend/modules/content/public.py` - Expose new methods in `ContentProvider` protocol
- `backend/modules/content/routes.py` - Add HTTP endpoints for My Units operations
- `backend/modules/content/test_content_unit.py` - Add unit tests

**New Model:**
```python
class UserMyUnitModel(Base):
    """Tracks which global units a user has added to 'My Units'."""
    __tablename__ = "user_my_units"
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), primary_key=True)
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

**New Repo Methods:**
- `add_unit_to_my_units(user_id, unit_id)` - Insert My Units record
- `remove_unit_from_my_units(user_id, unit_id)` - Delete My Units record
- `is_unit_in_my_units(user_id, unit_id)` - Check if unit is in My Units
- `list_my_units_unit_ids(user_id)` - Get all unit IDs in user's My Units
- `list_units_for_user_including_my_units(user_id, limit, offset)` - Get owned + My Units

**New Service Methods:**
- `add_unit_to_my_units(user_id, unit_id)` - Add unit to My Units (validates unit exists and is global)
- `remove_unit_from_my_units(user_id, unit_id)` - Remove unit from My Units (validates not owned by user)

**New Public Interface Methods:**
```python
async def add_unit_to_my_units(self, user_id: int, unit_id: str) -> None: ...
async def remove_unit_from_my_units(self, user_id: int, unit_id: str) -> None: ...
```

**New Routes:**
- `POST /api/v1/content/units/my-units/add` - Add unit to My Units
- `POST /api/v1/content/units/my-units/remove` - Remove unit from My Units

---

#### Module: `catalog` (existing)

**Files to modify:**
- `backend/modules/catalog/service.py` - Update `browse_units_for_user()` filtering logic
- `backend/modules/catalog/test_lesson_catalog_unit.py` - Update tests

**Updated Logic:**

Current `browse_units_for_user()`:
- `personal_units`: Units owned by user (`user_id` matches)
- `global_units`: All globally shared units (`is_global=True`)

New `browse_units_for_user()`:
- `personal_units`: Units owned by user OR units in My Units (via `content.list_units_for_user_including_my_units()`)
- `global_units`: Globally shared units NOT in My Units and NOT owned by user

---

### Frontend (Mobile)

#### Module: `content` (existing)

**Files to modify:**
- `mobile/modules/content/models.ts` - Add request/response types
- `mobile/modules/content/repo.ts` - Add HTTP calls for add/remove operations
- `mobile/modules/content/service.ts` - Add business logic methods
- `mobile/modules/content/public.ts` - Expose new methods in `ContentProvider`
- `mobile/modules/content/test_content_service_unit.ts` - Add unit tests

**New Types:**
```typescript
interface AddToMyUnitsRequest {
  userId: number;
  unitId: string;
}

interface RemoveFromMyUnitsRequest {
  userId: number;
  unitId: string;
}
```

**New Service Methods:**
- `addUnitToMyUnits(userId, unitId)` - Add to My Units
- `removeUnitFromMyUnits(userId, unitId)` - Remove from My Units

**New Public Interface Methods:**
```typescript
addUnitToMyUnits(userId: number, unitId: string): Promise<void>;
removeUnitFromMyUnits(userId: number, unitId: string): Promise<void>;
```

---

#### Module: `catalog` (existing)

**Files to modify:**
- `mobile/modules/catalog/queries.ts` - Add mutations for add/remove operations
- `mobile/modules/catalog/screens/UnitListScreen.tsx` - Add "Browse Catalog" button, update UI
- `mobile/modules/catalog/components/UnitCard.tsx` - Add remove action for catalog units
- `mobile/modules/catalog/service.ts` - No changes needed (delegates to content)
- `mobile/modules/catalog/test_catalog_unit.ts` - Update tests

**New Files:**
- `mobile/modules/catalog/screens/CatalogBrowserScreen.tsx` - Full-screen catalog overlay
- `mobile/modules/catalog/components/CatalogUnitCard.tsx` - Unit card for catalog browser

**New Queries:**
- `useAddUnitToMyUnits()` - Mutation to add unit
- `useRemoveUnitFromMyUnits()` - Mutation to remove unit

**CatalogBrowserScreen Features:**
- Full-screen modal presentation
- Header with close button and title "Browse Catalog"
- Search bar (filter by title, client-side)
- List of all global units (from `useUserUnitCollections` with `includeGlobal: true`)
- Visual badge showing "In My Units" for units already added
- Add/Remove button on each unit card
- Swipe-to-dismiss gesture (standard iOS modal)

**UnitListScreen Updates:**
- Add "Browse Catalog" button (icon button near search bar)
- Display only units from `collections.units` (backend now filters to My Units)
- Add swipe-to-delete action for units that are:
  - In catalog membership (not owned by user)
  - Status is 'completed' (not in-progress or failed)
- Show confirmation alert before removing

---

## Implementation Checklist

The implementation is divided into 4 phases for incremental progress and testing:

1. **Phase 1: Backend Foundation** - Database schema, repository layer, service layer, API routes, and backend tests
2. **Phase 2: Frontend Foundation** - Mobile data layer (models, repo, service, public interface) and tests
3. **Phase 3: Frontend UI** - Mobile screens, components, queries, and UI tests
4. **Phase 4: Seed Data & Final Verification** - Test data, end-to-end verification, and architecture compliance

Each phase includes verification steps to ensure quality before moving forward.

---

### Phase 1: Backend Foundation (Database & Core Logic)

#### Database & Models
- [ ] Create Alembic migration for `user_my_units` table
- [ ] Add `UserMyUnitModel` to `backend/modules/content/models.py`
- [ ] Run migration to create table in database

#### Content Module - Repository Layer
- [ ] Add `add_unit_to_my_units()` to `backend/modules/content/repo.py`
- [ ] Add `remove_unit_from_my_units()` to `backend/modules/content/repo.py`
- [ ] Add `is_unit_in_my_units()` to `backend/modules/content/repo.py`
- [ ] Add `list_my_units_unit_ids()` to `backend/modules/content/repo.py`
- [ ] Add `list_units_for_user_including_my_units()` to `backend/modules/content/repo.py`

#### Content Module - Service Layer
- [ ] Add `add_unit_to_my_units()` to `backend/modules/content/service.py` with validation
- [ ] Add `remove_unit_from_my_units()` to `backend/modules/content/service.py` with validation
- [ ] Ensure validation: unit must exist and be global to add
- [ ] Ensure validation: unit must not be owned by user to remove

#### Content Module - Public Interface
- [ ] Add `add_unit_to_my_units()` to `ContentProvider` protocol in `backend/modules/content/public.py`
- [ ] Add `remove_unit_from_my_units()` to `ContentProvider` protocol in `backend/modules/content/public.py`
- [ ] Update `content_provider()` function to expose new methods

#### Content Module - Routes
- [ ] Add `POST /api/v1/content/units/my-units/add` endpoint to `backend/modules/content/routes.py`
- [ ] Add `POST /api/v1/content/units/my-units/remove` endpoint to `backend/modules/content/routes.py`
- [ ] Add request/response models for endpoints
- [ ] Add proper error handling (404 if unit not found, 403 if not global, etc.)

#### Catalog Module - Service Layer
- [ ] Update `browse_units_for_user()` in `backend/modules/catalog/service.py` to use new filtering logic
- [ ] Ensure `personal_units` includes owned + My Units
- [ ] Ensure `global_units` excludes owned + My Units

#### Phase 1 Backend Tests
- [ ] Add unit tests for repo `add_unit_to_my_units()` in `backend/modules/content/test_content_unit.py`
- [ ] Add unit tests for repo `remove_unit_from_my_units()` in `backend/modules/content/test_content_unit.py`
- [ ] Add unit tests for service `add_unit_to_my_units()` validation in `backend/modules/content/test_content_unit.py`
- [ ] Add unit tests for service `remove_unit_from_my_units()` validation in `backend/modules/content/test_content_unit.py`
- [ ] Update catalog service tests in `backend/modules/catalog/test_lesson_catalog_unit.py` for new filtering
- [ ] Review and update existing integration tests in `backend/tests/` if they rely on old unit filtering behavior

#### Phase 1 Verification
- [ ] Verify backend lint passes: `./format_code.sh`
- [ ] Verify backend unit tests pass: `cd backend && scripts/run_unit.py`
- [ ] Verify backend integration tests pass: `cd backend && scripts/run_integration.py`

---

### Phase 2: Frontend Foundation (Models, Repo, Service)

#### Content Module - Models & Types
- [ ] Add `AddToMyUnitsRequest` type to `mobile/modules/content/models.ts`
- [ ] Add `RemoveFromMyUnitsRequest` type to `mobile/modules/content/models.ts`

#### Content Module - Repository Layer
- [ ] Add `addUnitToMyUnits()` HTTP call to `mobile/modules/content/repo.ts`
- [ ] Add `removeUnitFromMyUnits()` HTTP call to `mobile/modules/content/repo.ts`

#### Content Module - Service Layer
- [ ] Add `addUnitToMyUnits()` to `mobile/modules/content/service.ts`
- [ ] Add `removeUnitFromMyUnits()` to `mobile/modules/content/service.ts`
- [ ] Add error handling for both methods

#### Content Module - Public Interface
- [ ] Add `addUnitToMyUnits()` to `ContentProvider` interface in `mobile/modules/content/public.ts`
- [ ] Add `removeUnitFromMyUnits()` to `ContentProvider` interface in `mobile/modules/content/public.ts`
- [ ] Update `contentProvider()` function to expose new methods

#### Phase 2 Tests
- [ ] Add unit tests for `addUnitToMyUnits()` in `mobile/modules/content/test_content_service_unit.ts`
- [ ] Add unit tests for `removeUnitFromMyUnits()` in `mobile/modules/content/test_content_service_unit.ts`

#### Phase 2 Verification
- [ ] Verify frontend lint passes: `./format_code.sh`
- [ ] Verify frontend unit tests pass: `cd mobile && npm run test`

---

### Phase 3: Frontend UI (Catalog Browser & Unit List Updates)

#### Catalog Module - Queries
- [ ] Add `useAddUnitToMyUnits()` mutation hook to `mobile/modules/catalog/queries.ts`
- [ ] Add `useRemoveUnitFromMyUnits()` mutation hook to `mobile/modules/catalog/queries.ts`
- [ ] Ensure mutations invalidate `userUnitCollections` query on success
- [ ] Add optimistic updates to mutations for instant UI feedback

#### Catalog Module - Components
- [ ] Create `mobile/modules/catalog/components/CatalogUnitCard.tsx`
- [ ] Add "In My Units" badge to `CatalogUnitCard`
- [ ] Add "Add to My Units" / "Remove from My Units" button to `CatalogUnitCard`
- [ ] Update `mobile/modules/catalog/components/UnitCard.tsx` to support remove action
- [ ] Add swipe-to-delete gesture to `UnitCard` for catalog-added units
- [ ] Add confirmation alert before removing unit

#### Catalog Module - Screens
- [ ] Create `mobile/modules/catalog/screens/CatalogBrowserScreen.tsx`
- [ ] Add full-screen modal presentation with swipe-to-dismiss
- [ ] Add search bar with title filtering (client-side)
- [ ] Add list of global units using `useUserUnitCollections` with `includeGlobal: true`
- [ ] Integrate `CatalogUnitCard` component
- [ ] Add loading and error states
- [ ] Update `mobile/modules/catalog/screens/UnitListScreen.tsx` to add "Browse Catalog" button
- [ ] Add navigation to `CatalogBrowserScreen` from "Browse Catalog" button
- [ ] Update `UnitListScreen` to show only "My Units" (backend now filters)
- [ ] Add testID attributes for e2e testing

#### Catalog Module - Navigation
- [ ] Add `CatalogBrowser` route to catalog navigation stack (if needed)
- [ ] Ensure modal presentation style for `CatalogBrowserScreen`

#### Phase 3 Tests
- [ ] Add component tests for `CatalogUnitCard` if complex behavior
- [ ] Update catalog tests in `mobile/modules/catalog/test_catalog_unit.ts` for new behavior
- [ ] Fix any existing maestro e2e tests in `mobile/e2e` that may be affected
- [ ] Add testID attributes to new components for e2e testing

#### Phase 3 Verification
- [ ] Verify frontend lint passes: `./format_code.sh`
- [ ] Verify frontend unit tests pass: `cd mobile && npm run test`
- [ ] Manually test catalog browser screen (search, add/remove)
- [ ] Manually test unit list screen (browse catalog button, remove action)

---

### Phase 4: Seed Data & Final Verification

#### Seed Data
- [ ] Update `backend/scripts/create_seed_data.py` to create sample global units
- [ ] Update `backend/scripts/create_seed_data.py` to add some units to test user's My Units
- [ ] Run seed data script to populate test data

#### Final Verification
- [ ] Ensure lint passes across entire codebase: `./format_code.sh` runs clean
- [ ] Ensure backend unit tests pass: `cd backend && scripts/run_unit.py`
- [ ] Ensure frontend unit tests pass: `cd mobile && npm run test`
- [ ] Ensure backend integration tests pass: `cd backend && scripts/run_integration.py`
- [ ] Follow the instructions in `codegen/prompts/trace.md` to ensure the user story is implemented correctly
- [ ] Fix any issues documented during the tracing of the user story in `docs/specs/global-vs-my-units/trace.md`
- [ ] Follow the instructions in `codegen/prompts/modulecheck.md` to ensure the new code is following the modular architecture correctly
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code

---

## Notes

### Terminology Consistency

- **"My Units"**: User's curated list (owned units + units added from catalog)
- **"Catalog"**: The browsable collection of all global units
- **Database table**: `user_my_units` - tracks which units a user has added to My Units

### Design Decisions

1. **Join table name**: `user_my_units` - Simple and matches user-facing terminology
2. **User-created units**: Always in "My Units", cannot be removed
3. **Progress retention**: Learning session data is NOT deleted when unit is removed from My Units
4. **Access retention**: Users keep access to units they've added, even if later un-shared
5. **Search scope**: Title search only (simple and fast for MVP)
6. **Platform**: Mobile only (admin can be added later if needed)

### Future Enhancements (Out of Scope)

- Advanced search/filters (by difficulty, lesson count, etc.)
- Recommendations based on user interests
- "Recently added" section in catalog
- Bulk add/remove operations
- Admin interface for catalog management
- Analytics on which units are most added to My Units
