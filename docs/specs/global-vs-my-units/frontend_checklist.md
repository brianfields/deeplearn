## 0) Structure & Naming

* [x] Module files follow vertical slice structure (`models.ts`, `repo.ts`, `service.ts`, `public.ts`, `queries.ts`). — My Units additions stay within content/catalog modules.

## 1) Imports & Boundaries

* [x] No cross-module imports beyond `public.ts`. — Catalog UI and queries consume content services via public providers only.
* [x] Modules do not import their own `public.ts`. — Verified for content and catalog modules.
* [x] `repo.ts` owns HTTP calls for its module. — Add/remove requests live only in `content/repo.ts`.

## 2) DTO vs Wire Separation

* [x] `repo.ts` returns raw API payloads. — Content repo relays backend responses without mapping.
* [x] `service.ts` converts payloads to DTOs and applies business logic. — Service validates IDs and surfaces typed results.
* [x] `public.ts` is a thin forwarder. — Content provider exposes service methods without extra logic.

## 3) React Query & State Management

* [x] `queries.ts` calls service layer directly. — Catalog queries request DTOs and manage cache lifecycle.
* [x] Optimistic updates implemented in queries when mutating. — `useAddUnitToMyUnits` and `useRemoveUnitFromMyUnits` update caches immediately.

## 4) Typing & Contracts

* [x] All exported functions/types fully annotated. — New request interfaces and service methods declare argument/return types.
* [x] DTO shapes mirror backend fields. — Membership toggles use consistent naming (`unitId`, `userId`).

## 5) UI Components

* [x] Components consume DTOs rather than raw wire types. — `CatalogUnitCard` and `UnitCard` use DTOs from services/queries.
* [x] No cross-module data fetching inside components. — Components rely on hooks and service props instead of hitting repos.
* [x] TestIDs added for new interactive elements. — Catalog browser and swipe-to-remove controls expose IDs for e2e tests.

## 6) Tests

* [x] Unit/component tests cover non-trivial logic. — Catalog card tests assert optimistic toggles and failure paths.
* [x] Tests avoid mocking internal module boundaries incorrectly. — Queries/services mocked via public contracts only.

## 7) Dead Code & Surface Area

* [x] No unused exports added. — Public interfaces expose only the necessary membership methods.
* [x] Removed temporary helpers after integration. — Verified during trace; no dead files.

## 8) Styling & Accessibility

* [x] Components reuse UI system primitives where possible. — Catalog cards leverage `Card`, `Button`, and `ArtworkImage` from UI system.
* [x] Swipe/delete flows present confirmations and respect disabled states. — `UnitCard` uses alerts and disables actions while pending.

## 9) Documentation & Consistency

* [x] Spec updated with completed checklist items and seed data notes. — Phase 4 section now checked off.

---

### Notes
- Inline-style ESLint warnings remain from earlier phases; addressing them globally is out of scope for this pass but documented in the trace recommendations.
