# Create From App - User Description

The user wants to incorporate the existing `create_unit.py` script capability into the mobile app. 

## Feature Overview
- Users will have the option to either select an existing unit (on the unit list screen) or create a new one
- Creating a new unit involves the user inputting a topic
- The unit creation will be done in the background, allowing users to continue using the app
- In-progress units will be shown on the unit list screen with a clear indication of progress
- Once creation is complete, the user will be notified and can use the new unit

## Key Requirements
- Background processing for unit creation
- UI indication of in-progress units
- User notification when creation is complete
- Integration with existing unit list screen
- Topic input interface for new unit creation

## Reference
- Existing functionality: `create_unit.py` script