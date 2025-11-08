# Fix Lint Log

This file tracks all lint and type fixes applied to the create_from_app project.

## Format
Each entry includes:
- Date/Time
- Files changed
- Issue type
- Rationale

---

## 2024-09-22 ~15:30

### Files changed:
- `backend/modules/content_creator/service.py`
- `backend/modules/content_creator/test_content_creator_unit.py`
- `backend/modules/content_creator/test_fast_flow_unit.py`
- `mobile/modules/catalog/screens/CreateUnitScreen.tsx`

### Issue types fixed:

**Backend Ruff Issues (8 total):**
1. **RUF006**: Store reference to `asyncio.create_task` return value - Fixed by storing task/future references in instance sets to prevent garbage collection
2. **ANN001**: Missing type annotation for `background_tasks` parameter - Fixed by importing and using `BackgroundTasks` type from FastAPI
3. **PLC0415**: Import at top-level - Fixed by removing redundant asyncio import (already imported at top)
4. **F841**: Unused variable `mock_create_task` - Fixed by prefixing with underscore (`_mock_create_task`)  
5. **ERA001**: Commented-out code - Fixed by removing commented assertion line
6. **ARG001**: Unused argument `use_fast_flow` - Fixed by prefixing with underscore (`_use_fast_flow`)
7. **I001**: Import block un-sorted/unformatted - Fixed by running `ruff --fix` to auto-sort imports

**Backend MyPy Issues (6 original + 3 new = 9 total):**
1. **var-annotated**: Missing type annotations for list variables - Fixed by adding explicit type annotations:
   - `objectives: list[Objective] = []`
   - `transcripts: list[str] = []`
   - `exercises: list[MCQExercise] = []`
   - `self._background_tasks: set[asyncio.Task[Any]] = ...`
   - `self._background_futures: set[asyncio.Future[Any]] = ...`
2. **attr-defined**: "object" has no attribute "add_task" - Fixed by importing and using proper `BackgroundTasks` type

**Frontend ESLint/Prettier Issues (5 total):**
1. **prettier/prettier**: Line formatting in error handling - Fixed by reformatting multi-line assignment and function call to match Prettier style

### Rationale:
All fixes maintain existing behavior while satisfying type safety and code quality requirements. Used underscore prefix for legitimately unused test parameters rather than removal to maintain test API compatibility. Added proper type annotations to improve code maintainability and catch potential type errors.
