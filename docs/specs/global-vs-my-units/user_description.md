# Global vs My Units - User Description

## Problem Statement
At present, units show up on a learner's unit list if they created the unit, or if someone else created a unit and shared it globally. That could lead to clutter where a learner has a lot of stuff on their unit list that isn't of interest to them.

## Proposed Solution
Enable a learner to pick which of the shared globally units they would like to have in their units list. They can pick those from a new feature called the "catalog".

## Key Features
1. **Catalog Access**: Button on the units list that opens a full-screen overlay (dismissible with downward swipe)
2. **Search & Browse**: The learner can search the catalog by title for units of interest
3. **Add to My Units**: Select units they would like to add to "My Units"
4. **Show in Units List**: Once selected, they will show up in the learner's units list
5. **Remove from My Units**: There should also be a way to evict units in "My Units" that they are no longer interested in
6. **User-Created Units**: Units created by the user always appear in "My Units" automatically

## Impact
- Web (admin): No (mobile only for now)
- Mobile: Yes

## Design Decisions (from clarifying questions)
1. **Data Model**: New join table (`user_my_units`) to track which global units a user has added
2. **Default Behavior**: Fresh start (no existing users to migrate)
3. **UI Pattern**: Full-screen overlay with iOS swipe-to-dismiss gesture
4. **Search**: Title search only (to start)
5. **User-Created Units**: Always in "My Units" automatically
6. **Terminology**: "My Units" for curated list, "Catalog" for browsing global units
7. **Module**: Extend existing `catalog` module (no new module needed)
8. **Platform**: Mobile only
9. **Progress Retention**: Keep progress data when unit removed from "My Units"
10. **Access Retention**: User retains access to units they've added, even if later un-shared globally
