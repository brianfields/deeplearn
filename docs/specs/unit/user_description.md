# Unit Feature - User Description

## Overview
Create a larger learning concept called a "unit" that encompasses several lessons, building on the existing lesson structure created by `backend/scripts/create_lesson.py`.

## Current State
- `backend/scripts/create_lesson.py` creates individual lessons with short snippets and MCQs
- Lessons exist as standalone learning components

## Desired State
- **Units**: Larger learning concepts that contain multiple related lessons
- **Hierarchical Structure**: Units → Lessons (existing)
- **Content Creation Pipeline**: Tool to decompose large topics into units, each containing multiple lessons
- **Progress Tracking**: User progress through units and individual lessons within units
- **UI Navigation**: Users can click on units, see lesson breakdown, and resume where they left off

## Key Requirements
1. **Data Modeling**: New unit data structures that reference existing lessons
2. **Content Creation**: `create_unit.py` script for unit creation
3. **Progress Tracking**: Track user progress at both unit and lesson levels
4. **UI/UX**: Unit selection interface showing lesson progress and resumption capability
5. **Logical Organization**: Units should contain logically related lessons

## User Experience Flow
1. User sees available units
2. User clicks on a unit to see its lessons
3. User can see progress through the unit and individual lessons
4. User can resume learning from where they left off
5. Progress is tracked and persisted across sessions