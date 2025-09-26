# Users Feature Description

## Overview
Add a comprehensive user system to the deeplearn application, introducing user authentication, user-specific content ownership, and user management capabilities.

## Core Requirements

### User Model & Authentication
- Create a new `users` module with user registration and email/password login
- Users have email, password, name, and basic profile information
- Authentication system for login/logout functionality

### Content Ownership & Visibility
- Add `user_id` fields to existing models: UnitModel, LLMRequestModel, UnitSessionModel, LearningSessionModel
- Implement "global" vs "user-specific" content distinction via `is_global` attribute on units
- Users see both their own units and global units when logged in

### User Interface Changes
- Login screen for authentication
- User's main screen shows:
  - Their personal units
  - Global units (marked with `is_global=True`)
- Admin interface enhancements:
  - Dedicated user management section
  - User association tracking for units/LLM requests
  - User identification in existing admin views

### Cross-Module Integration
- Existing modules (content, learning_session, etc.) need to be updated to support user ownership
- Admin module needs user management capabilities
- Mobile app needs login flow and user-aware content display

## Target Users
- **Learners**: Primary users who log in to access content
- **Admins**: Need visibility into user data and content ownership
- **Content Creators**: (Future consideration for user-generated content)

## Key Use Cases
1. User registration and login with email/password
2. Personal content management (user's own units)
3. Global content access (shared units)
4. Admin user management and oversight
5. Content ownership tracking across all entities