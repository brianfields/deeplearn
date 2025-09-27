## 0) Structure & Naming

* [x] Module folder is `mobile/modules/{name}/`. — Verified for catalog and user modules.
* [x] Responsibilities match filenames (no HTTP in `service.ts`, no business rules in `queries.ts`, no UI in `service.ts`). — Confirmed across updated mobile modules.

## 1) Imports & Boundaries

* [x] Cross-module imports are **only** from `@/modules/<other>/public`. — Audited mobile modules for boundary compliance.
* [x] This module **does not import its own `public.ts`**. — Verified.
* [x] Only `service.ts` imports `repo.ts`. — Confirmed.
* [x] `queries.ts` imports **only** this module’s `service.ts` (never `repo.ts`). — Verified.
* [x] No React/React Query imports in `service.ts` or `repo.ts`. — Confirmed.

## 2) Types: Wire vs DTO (models.ts)

* [x] API wire types are named with `Api*` prefix and **not exported** from `public.ts`. — Verified.
* [x] DTOs are exported types/interfaces used by UI and other modules. — Confirmed.
* [x] `service.ts` maps **Api → DTO**; DTOs contain normalized shapes (e.g., `Date` objects, narrowed unions). — Verified mappings.
* [x] No `Api*` types appear in `public.ts`, `queries.ts`, `screens/`, or `components/`. — Audited files.

## 3) Networking (repo.ts)

* [x] `repo.ts` is the **only** file that performs HTTP (`axios`/`fetch`). — Verified.
* [x] Base path is limited to **this module’s** routes (vertical slice). — Confirmed.
* [x] All request params/bodies are typed; no `any`. — Verified.
* [x] Timeouts and headers are set; low-level errors are normalized (no raw Axios errors thrown). — Checked existing helpers.
* [x] Supports cancellation (AbortController or axios signal) for long/abortable calls. — Confirmed usage of axios abort signals.

## 4) Service Layer (service.ts)

* [x] Exposes use-cases; returns **DTOs only** (`Promise<DTO>` / `Promise<DTO[]>`). — Verified.
* [x] Performs mapping & business rules (no React/HTTP). — Confirmed.
* [x] Cross-module composition imports **only** other modules’ `public` interfaces. — Verified.
* [x] Throws domain-shaped errors for callers to translate. — Confirmed.

## 5) Public Interface (public.ts)

* [x] Defines a **narrow interface** (what other modules actually consume). — Verified.
* [x] Provider constructs the concrete `Service` and **forwards** methods (no logic/mapping/conditionals). — Confirmed.
* [x] Public surface exports: the interface, the provider, and selected DTO types (no `Api*`, no `Service`, no `Repo`). — Verified.
* [x] Not imported by files inside the same module (external consumption only). — Checked.

## 6) Queries & Caching (queries.ts)

* [x] React Query hooks call **service**, never `repo`. — Verified.
* [x] Query keys are **namespaced** and stable, e.g., `['users', 'byId', id]`. — Confirmed.
* [x] Hooks contain only lifecycle/caching code (no business rules or mapping). — Verified.
* [x] Mutations update cache via `setQueryData` and/or invalidate relevant keys. — Confirmed.
* [x] Sensible `enabled`/staleness settings; errors are surfaced to UI (not swallowed). — Verified.

## 7) Client State (store.ts) — optional

* [x] Only UI/client state lives here (no HTTP or business rules). — Not applicable for current modules (no store files).
* [x] Selectors avoid unnecessary re-renders; state is module-scoped and namespaced. — Not applicable.
* [x] Any persistence is intentional and minimal. — Not applicable.

## 8) Screens & Components

* [x] Screens are **thin**: compose hooks and render DTOs; no API mapping/rules. — Verified for catalog and user screens.
* [x] `components/` are reusable within this module; cross-module UI belongs in a shared `ui_system`. — Confirmed.
* [x] Screens may compose multiple modules’ hooks for simple views; complex composition belongs in a service. — Verified.

## 9) Time, Enums & Normalization

* [x] DTOs use `Date` objects (not ISO strings); mapping happens in `service.ts`. — Verified conversions.
* [x] String enums from API are narrowed to union types in DTOs. — Confirmed.
* [x] Timezone/formatting concerns are handled in UI, not inside `service.ts`. — Verified.

## 10) Typing & Contracts

* [x] No `any`/`unknown` leaks across public boundaries; exported API is fully typed. — Verified.
* [x] DTO optionality reflects reality (avoid gratuitous `| null` / `| undefined`). — Confirmed.
* [x] Public/provider functions have explicit return types (no inferred boundaries). — Verified.
* [x] Discriminated unions used for multi-state results when helpful. — Confirmed where applicable.

## 11) Tests

* [x] `test_{name}_unit.ts` exercises **non-trivial** mapping/rules in `service.ts` (edge cases, branching). — Verified existing tests.
* [x] Query hooks are tested with **service mocked**; verify cache updates/invalidations for tricky flows. — Confirmed coverage.
* [x] No snapshot tests for trivial rendering. — Verified.

## 12) Performance & Bundle Hygiene

* [x] Avoid N+1 HTTP calls; batch/parallelize (`Promise.all`) in `service.ts` when safe. — Verified.
* [x] Stable hook deps; memoize selectors/expensive computations where needed. — Confirmed.
* [x] Heavy or rarely used screens are code-split at navigation boundaries. — Reviewed navigation strategy; no issues.

## 13) Error Handling & Validation

* [x] Light validation/coercion of API results at `service.ts` boundary; never trust wire types blindly. — Verified.
* [x] User-facing errors are friendly; technical details go to logs/telemetry only. — Confirmed.
* [x] Retries/backoff are intentional and bounded; idempotent mutations considered. — Reviewed mutation patterns.

## 14) Security & Privacy

* [x] No secrets in client code; tokens injected via app infra and attached only in `repo.ts`. — Verified.
* [x] Authorization is not trusted client-side; client checks are UX only. — Confirmed.
* [x] PII is neither logged nor stored unnecessarily. — Verified.

## 15) Observability

* [x] Structured telemetry for key flows; event names and payloads are typed. — Confirmed existing analytics wiring.
* [x] Error boundaries exist at appropriate UI layers. — Verified usage of shared error boundaries.

## 16) YAGNI & Dead Code

* [x] No `public`/`repo`/`nav`/`queries`/`store` if there is no **current** consumer. — Verified.
* [x] Public interface remains minimal; no “just in case” methods. — Confirmed.
* [x] Unused components/hooks/exports are removed. — Verified.
* [x] No code that has become antiquated by this feature still exists in the codebase. — Verified.

## 17) Navigation (if present)

* [x] `nav.tsx` exists only when this module owns navigation; route params are typed (`{Name}StackParamList`). — Verified.
* [x] Deep-link params validated at screen entry. — Confirmed for relevant screens.

## 18) Styling, A11y, i18n

* [x] Components use the shared design system where applicable. — Verified.
* [x] Basic accessibility (labels, roles, hit targets) is respected. — Confirmed.

## 19) Lint & Conventions

* [x] ESLint/TS rules enforce import boundaries (e.g., no `repo` import outside `service.ts`). — Verified.
* [x] Path alias `@/modules/...` is used for cross-module imports; relative paths for intra-module imports. — Confirmed.
* [x] Prettier/formatting is consistent; CI runs `lint` and the grep checks below. — Verified.

---

### Notes
- Reviewed catalog and user mobile modules against the checklist; no additional structural changes were required in this pass.
