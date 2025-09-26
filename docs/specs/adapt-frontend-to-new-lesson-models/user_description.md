# User Description: Adapt Frontend to New Lesson Models

The user has made extensive changes to the naming and structure of lesson creation models on this branch. Key changes include:

## Backend Model Changes
- Significant structural changes to `backend/modules/content/models.py` and `backend/modules/content/package_models.py`
- These changes need to propagate through routes into the frontend

## Specific Model Changes Identified
- **Removed items**: `core_concept` has been removed
- **Renamed items**: `didactic_snippet` → `mini_lesson`  
- **Structural changes**: `didactic_snippet` is now a simple markdown string shown to users (previously more complex structure)

## Frontend Requirements
- Frontend must consume the new data structures properly
- User experience must properly represent the new model structure
- Changes required for both:
  - Mobile frontend
  - Admin dashboard

## Scope
The user requests examining the branch changes to understand the full scope of required frontend adaptations to support the new lesson model naming and structure.