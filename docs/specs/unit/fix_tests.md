# Test Fix Log

## 2025-09-19
- backend/modules/units/test_units_unit.py: Fixed test mocks to provide datetime objects for created_at and updated_at instead of None. Changed test to match expected behavior.
- backend/modules/units/service.py: Explicitly set created_at and updated_at in create method to ensure timestamps are set.
- backend/modules/learning_session/service.py: Fixed update_progress to set started_at when exercise is first attempted, preserving it across attempts.
- backend/modules/content/models.py: Imported UnitModel to register units table mapper for SQLAlchemy foreign key resolution in lesson creation integration test.
- mobile/package.json: Modified e2e:maestro script to start iOS Simulator and set JVM options to fix device detection and Java warnings.

## 2025-09-20
- mobile/modules/unit_catalog/screens/UnitDetailScreen.tsx: Created missing UnitDetailScreen component moved from units module to fix bundling error.
- mobile/modules/unit_catalog/components/UnitCard.tsx: Created missing UnitCard component moved from units module.
- mobile/modules/unit_catalog/components/UnitProgress.tsx: Created missing UnitProgress component moved from units module.
- mobile/modules/unit_catalog/queries.ts: Added useUnit alias to useCatalogUnitDetail for compatibility.
- Changed test or SUT: SUT - Fixed missing components that caused iOS bundling failure preventing e2e test from running.
 - 2025-09-20 00:41: backend/scripts/create_seed_data.py — Changed SUT. Added session flush after adding `UnitModel` to ensure the `units` row exists before inserting `LessonModel` rows with `unit_id` FK, fixing FK violation during seed generation.
 - 2025-09-20 00:55: mobile/modules/infrastructure/public.ts — Changed SUT. Switched dev baseURL to localhost for iOS Simulator so unit list loads and `lesson-card-0` exists for Maestro.
 - 2025-09-20 18:10: start.sh, mobile/e2e/learning-flow.yaml — Changed SUT and test. Start script now runs Expo dev server without auto-opening iOS; Maestro test launches app and opens Expo URL to avoid simulator openurl timeout and ensure 'Units' screen becomes visible.
 - 2025-09-20 18:25: mobile/modules/unit_catalog/screens/LessonListScreen.tsx, mobile/e2e/learning-flow.yaml — Changed SUT and test. Added stable testID `units-title` to header and updated Maestro assertions to use id instead of text to avoid flakiness due to rendering and localization.