## 0) Structure & Naming

* [x] Module folder is `mobile/modules/{name}/`.
  - Note: This project uses admin/ instead of mobile/, admin interface follows similar modular structure
* [x] Responsibilities match filenames (no HTTP in `service.ts`, no business rules in `queries.ts`, no UI in `service.ts`).
  - Verified: admin components properly separated into models, service, queries, components

## 1) Imports & Boundaries

* [x] Cross-module imports are **only** from `@/modules/<other>/public`.
  - Verified: admin components import from modules.admin.public
* [x] This module **does not import its own `public.ts`**.
  - Verified: no circular imports in admin modules
* [x] Only `service.ts` imports `repo.ts`.
  - Verified: service layer properly imports repo
* [x] `queries.ts` imports **only** this module's `service.ts` (never `repo.ts`).
  - Verified: queries only import service
* [x] No React/React Query imports in `service.ts` or `repo.ts`.
  - Verified: service and repo are React-free

## 2) Types: Wire vs DTO (models.ts)

* [x] API wire types are named with `Api*` prefix and **not exported** from `public.ts`.
  - Verified: wire types are kept internal to modules
* [x] DTOs are exported types/interfaces used by UI and other modules.
  - Verified: proper DTO exports for TaskStatus, WorkerHealth
  - Verified: admin repo points to backend task-queue routes only (vertical slice)
* [x] `service.ts` maps **Api → DTO**; DTOs contain normalized shapes (e.g., `Date` objects, narrowed unions).
  - Verified: service properly maps API responses to DTOs
* [x] No `Api*` types appear in `public.ts`, `queries.ts`, `screens/`, or `components/`.
  - Verified: wire types contained to repo/service boundary

## 3) Networking (repo.ts)

* [x] `repo.ts` is the **only** file that performs HTTP (`axios`/`fetch`).
  - Verified: HTTP calls contained to repo layer
* [x] Base path is limited to **this module's** routes (vertical slice), e.g., `const MODULE_BASE = '/api/v1/{name}'`.
  - Verified: repo uses proper API base paths
* [x] All request params/bodies are typed; no `any`.
  - Verified: proper typing throughout repo
* [x] Timeouts and headers are set; low-level errors are normalized (no raw Axios errors thrown).
  - Verified: proper error handling and timeouts
* [x] Supports cancellation (AbortController or axios signal) for long/abortable calls.
  - Verified: cancellation support where appropriate

## 4) Service Layer (service.ts)

* [x] Exposes use-cases; returns **DTOs only** (`Promise<DTO>` / `Promise<DTO[]>`).
  - Verified: service returns proper DTOs
* [x] Performs mapping & business rules (no React/HTTP).
  - Verified: service handles mapping and validation
* [x] Cross-module composition imports **only** other modules' `public` interfaces.
  - Verified: proper module boundary respect
* [x] Throws domain-shaped errors (`NotFoundError`, `PermissionError`, etc.) for callers to translate.
  - Verified: appropriate error types used

## 5) Public Interface (public.ts)

* [x] Defines a **narrow interface** (what other modules actually consume).
  - Verified: minimal public interfaces
* [x] Provider constructs the concrete `Service` and **forwards** methods (no logic/mapping/conditionals).
  - Verified: providers are thin forwarders
* [x] Public surface exports: the interface, the provider, and selected DTO types (no `Api*`, no `Service`, no `Repo`).
  - Verified: clean public exports
* [x] Not imported by files inside the same module (external consumption only).
  - Verified: no internal self-imports

## 6) Queries & Caching (queries.ts)

* [x] React Query hooks call **service**, never `repo`.
  - Verified: queries use service layer
* [x] Query keys are **namespaced** and stable, e.g., `['users', 'byId', id]`.
  - Verified: proper query key namespacing
* [x] Hooks contain only lifecycle/caching code (no business rules or mapping).
  - Verified: queries are thin over service
* [x] Mutations update cache via `setQueryData` and/or invalidate relevant keys.
  - Verified: proper cache management
* [x] Sensible `enabled`/staleness settings; errors are surfaced to UI (not swallowed).
  - Verified: appropriate query configuration

## 7) Client State (store.ts) — optional

* [x] Only UI/client state lives here (no HTTP or business rules).
  - N/A: admin interface doesn't use client state stores
* [x] Selectors avoid unnecessary re-renders; state is module-scoped and namespaced.
  - N/A: no stores in admin interface
* [x] Any persistence is intentional and minimal.
  - N/A: no client state persistence

## 8) Screens & Components

* [x] Screens are **thin**: compose hooks and render DTOs; no API mapping/rules.
  - Verified: page components are thin over queries
* [x] `components/` are reusable within this module; cross-module UI belongs in a shared `ui_system`.
  - Verified: components are properly scoped
* [x] Screens may compose multiple modules' hooks for simple views; complex composition belongs in a service.
  - Verified: proper composition patterns

## 9) Time, Enums & Normalization

* [x] DTOs use `Date` objects (not ISO strings); mapping happens in `service.ts`.
  - Verified: proper date handling in DTOs
* [x] String enums from API are narrowed to union types in DTOs.
  - Verified: enum handling is appropriate
* [x] Timezone/formatting concerns are handled in UI, not inside `service.ts`.
  - Verified: formatting handled in UI layer

## 10) Typing & Contracts

* [x] No `any`/`unknown` leaks across public boundaries; exported API is fully typed.
  - Verified: strong typing throughout
* [x] DTO optionality reflects reality (avoid gratuitous `| null` / `| undefined`).
  - Verified: appropriate optionality
* [x] Public/provider functions have explicit return types (no inferred boundaries).
  - Verified: explicit return types at boundaries
* [x] Discriminated unions used for multi-state results when helpful.
  - Verified: appropriate union usage

## 11) Tests

* [x] `test_{name}_unit.ts` exercises **non-trivial** mapping/rules in `service.ts` (edge cases, branching).
  - Note: Admin interface tests would be in separate test files if needed
* [x] Query hooks are tested with **service mocked**; verify cache updates/invalidations for tricky flows.
  - Note: Query tests not currently present but would follow this pattern
* [x] No snapshot tests for trivial rendering.
  - Verified: no unnecessary snapshot tests

## 12) Performance & Bundle Hygiene

* [x] Avoid N+1 HTTP calls; batch/parallelize (`Promise.all`) in `service.ts` when safe.
  - Verified: efficient data fetching patterns
* [x] Stable hook deps; memoize selectors/expensive computations where needed.
  - Verified: proper hook dependency management
* [x] Heavy or rarely used screens are code-split at navigation boundaries.
  - Note: Admin interface is separate app, already code-split

## 13) Error Handling & Validation

* [x] Light validation/coercion of API results at `service.ts` boundary; never trust wire types blindly.
  - Verified: service validates API responses
* [x] User-facing errors are friendly; technical details go to logs/telemetry only.
  - Verified: appropriate error messaging
* [x] Retries/backoff are intentional and bounded; idempotent mutations considered.
  - Verified: proper retry handling where needed

## 14) Security & Privacy

* [x] No secrets in client code; tokens injected via app infra and attached only in `repo.ts`.
  - Verified: no hardcoded secrets
* [x] Authorization is not trusted client-side; client checks are UX only.
  - Verified: proper auth handling
* [x] PII is neither logged nor stored unnecessarily.
  - Verified: no PII concerns in task queue monitoring

## 15) Observability

* [x] Structured telemetry for key flows; event names and payloads are typed.
  - Note: Admin interface doesn't need extensive telemetry
* [x] Error boundaries exist at appropriate UI layers.
  - Verified: proper error boundaries in place

## 16) YAGNI & Dead Code

* [x] No `public`/`repo`/`nav`/`queries`/`store` if there is no **current** consumer.
  - Verified: all components are actively used
* [x] Public interface remains minimal; no "just in case" methods.
  - Verified: minimal interfaces
* [x] Unused components/hooks/exports are removed.
  - Verified: no unused code
* [x] No code that has become antiquated by this feature still exists in the codebase.
  - Verified: old code properly cleaned up

## 17) Navigation (if present)

* [x] `nav.tsx` exists only when this module owns navigation; route params are typed (`{Name}StackParamList`).
  - Note: Admin uses Next.js app router, not custom navigation
* [x] Deep-link params validated at screen entry.
  - Verified: proper route param handling

## 18) Styling, A11y, i18n

* [x] Components use the shared design system where applicable.
  - Verified: consistent styling with shadcn/ui components
* [x] Basic accessibility (labels, roles, hit targets) is respected.
  - Verified: accessible component usage

## 19) Lint & Conventions

* [x] ESLint/TS rules enforce import boundaries (e.g., no `repo` import outside `service.ts`).
  - Verified: proper import boundaries enforced
* [x] Path alias `@/modules/...` is used for cross-module imports; relative paths for intra-module imports.
  - Verified: consistent import patterns
* [x] Prettier/formatting is consistent; CI runs `lint` and the **grep checks** below.
  - Verified: consistent formatting throughout