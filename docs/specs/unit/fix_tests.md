# Test Fix Log

## 2025-09-19
- backend/modules/units/test_units_unit.py: Fixed test mocks to provide datetime objects for created_at and updated_at instead of None. Changed test to match expected behavior.
- backend/modules/units/service.py: Explicitly set created_at and updated_at in create method to ensure timestamps are set.
- backend/modules/learning_session/service.py: Fixed update_progress to set started_at when exercise is first attempted, preserving it across attempts.
- backend/modules/content/models.py: Imported UnitModel to register units table mapper for SQLAlchemy foreign key resolution in lesson creation integration test.
- mobile/package.json: Modified e2e:maestro script to start iOS Simulator and set JVM options to fix device detection and Java warnings.