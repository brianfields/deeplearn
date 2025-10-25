# User Description: Improve Admin Dashboard

## Overview
Simplify the top-level menu of the admin dashboard while supporting more drilldown and understanding between entities.

## Concrete Changes Requested

### 1. Flow Run Drilldown
- Clicking on a Flow Run should show the Flow Run Steps used to execute that Flow Run
- In each Flow Run Step, show the LLM Request (if any) for that step
- Enable navigation through the execution hierarchy: Flow Run → Flow Run Steps → LLM Requests

### 2. Combine Task Queue and Workers
- Merge 'Task Queue' and 'Workers' into a single tab
- Show information about background tasks and their workers
- Focus on seeing all tasks and their status (not performance stats)

### 3. Merge Units and Lessons
- Combine Units and Lessons tabs into a single tab
- Enable clicking into lessons within a unit
- Maintain current lesson detail views
- Easy navigation: click into lesson, then back out to unit
- Show status of units still being processed
- Link to the background task for the unit (if possible)

### 4. Consistent Reload Functionality
- Add "Reload" button to all pages (like the one on the unit page)
- Replace ad-hoc refresh mechanisms with consistent UI pattern

### 5. Enhanced Unit Creation Observability
- Get more observability into unit creation process:
  - Flow runs that have happened
  - Errors that have occurred
  - What stage unit creation is in
- Ability to re-run a failed unit creation task
- **Note**: Need to scope out difficulty/feasibility of this feature

## Goals
- Simplify top-level navigation
- Improve entity relationship visibility
- Enhance debugging and monitoring capabilities
- Provide consistent UX patterns across all admin pages
