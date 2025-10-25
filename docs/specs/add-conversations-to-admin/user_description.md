# User Description: Add Conversations to Admin

## Context
The admin dashboard (NextJS) currently displays flow runs from the `flow_engine` module but does not show conversations from the `conversation_engine` module.

## Current State
- Conversations exist in the system (currently only learning_coach conversations)
- Admin dashboard has no visibility into these conversations
- User detail pages exist in the admin dashboard

## Desired State
- Admin dashboard should display conversations between users
- Conversations should be linked to/from the user's detail page
- System should support future conversation types beyond learning_coach

## Key Requirements
1. Show conversations in the admin dashboard
2. Link conversations to user detail pages
3. Design should accommodate future conversation types (not just learning_coach)
