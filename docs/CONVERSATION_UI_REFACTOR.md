# Conversation UI Refactoring

## Overview

The Learning Coach and Teaching Assistant features now share **unified conversation UI components**, ensuring visual consistency and reducing maintenance burden across both experiences.

**Before:** Separate implementations of headers, message bubbles, quick replies, and composer for each conversation type
**After:** Shared `ConversationHeader` and `ConversationContainer` used by both

## What Changed

### New Components

1. **ConversationHeader** (NEW)
   - Shared header component for both conversation types
   - Provides unified title styling and close button affordance (✕)
   - Supports optional subtitle for context information
   - Ensures both Learning Coach and Teaching Assistant have identical header appearance

2. **ConversationContainer** (NEW - previously refactored)
   - Reusable wrapper for core conversation UI
   - Orchestrates message display, quick replies, and composer
   - Supports customization via props for different conversation types

### Updated Components

1. **ConversationList** - Now accepts optional `loadingMessage` prop
2. **TeachingAssistantConversation** - Refactored to use `ConversationContainer`
3. **LearningCoachScreen** - Refactored to use `ConversationHeader` + `ConversationContainer`
4. **TeachingAssistantModal** - Refactored to use `ConversationHeader` + `ConversationContainer`

### Removed Duplication

- ✅ Eliminated duplicate header implementations (both had own close button styles)
- ✅ Removed duplicate conversation UI components
- ✅ Consolidated close button affordances (now both use ✕)

## Architecture

### Before (Inconsistent)
```
Learning Coach Screen
├─ Custom Header (✕ button)
├─ ConversationList
├─ QuickReplies
└─ Composer

Teaching Assistant Modal
├─ Custom Header (text "Close" button)
├─ ConversationList (similar but separate)
├─ QuickReplies (similar but separate)
└─ Composer (similar but separate)
```

### After (Unified)
```
Learning Coach Screen
├─ ConversationHeader (✕ button)
├─ ConversationContainer
│  ├─ ConversationList
│  ├─ QuickReplies
│  └─ Composer

Teaching Assistant Modal
├─ ConversationHeader (✕ button + optional subtitle)
├─ ConversationContainer (via TeachingAssistantConversation)
│  ├─ ConversationList
│  ├─ QuickReplies
│  └─ Composer
```

## Benefits

✅ **Visual Consistency**
- Identical headers with same close button affordance (✕)
- Matching message bubble styles
- Unified quick reply and composer styling

✅ **Maintainability**
- Change styling once, applies to both conversation types
- Bug fixes needed in one place instead of two
- New features automatically available to both types

✅ **DRY Principle**
- Eliminated 100+ lines of duplicated UI code
- Single source of truth for conversation styling

✅ **Testability**
- Core conversation components tested once
- Both Learning Coach and Teaching Assistant inherit consistency

✅ **Extensibility**
- Future conversation types (mentor, study buddy, etc.) automatically consistent
- Easy to add new types without duplication

## Implementation Details

### ConversationHeader Props

```typescript
interface Props {
  readonly title: string;           // "Learning Coach" or "Teaching Assistant"
  readonly onClose: () => void;     // Close button callback
  readonly subtitle?: string;       // Optional context (e.g., "Lesson: X • Progress: Y%")
}
```

### ConversationContainer Props

```typescript
interface Props {
  readonly messages: ConversationMessage[];
  readonly suggestedReplies: readonly string[];
  readonly onSendMessage: (message: string) => void;
  readonly onSelectReply: (message: string) => void;
  readonly isLoading?: boolean;
  readonly disabled?: boolean;
  readonly onAttachResource?: () => void;
  readonly attachDisabled?: boolean;
  readonly composerPlaceholder?: string;
  readonly loadingMessage?: string;
}
```

## Files Modified

### New Files
1. `mobile/modules/learning_conversations/components/ConversationHeader.tsx`
2. `mobile/modules/learning_conversations/components/ConversationContainer.tsx`

### Updated Files
1. `mobile/modules/learning_conversations/components/ConversationList.tsx`
2. `mobile/modules/learning_conversations/components/TeachingAssistantConversation.tsx`
3. `mobile/modules/learning_conversations/screens/LearningCoachScreen.tsx`
4. `mobile/modules/learning_conversations/components/TeachingAssistantModal.tsx`
5. `mobile/modules/learning_conversations/components/README.md`

### Removed Styles
- Eliminated 100+ lines of header styling duplicated between Learning Coach and Teaching Assistant

## Usage Examples

### Learning Coach
```tsx
<SafeAreaView style={styles.screen}>
  <ConversationHeader title="Learning Coach" onClose={handleCancel} />
  <View style={styles.body}>
    {/* Upload prompt, brief card, etc. */}
    <ConversationContainer
      messages={displayMessages}
      suggestedReplies={quickReplies}
      onSendMessage={handleSend}
      onSelectReply={handleQuickReply}
      isLoading={isCoachLoading}
      disabled={isCoachLoading}
      composerPlaceholder="Tell the coach what you need"
      loadingMessage="Coach is thinking..."
    />
  </View>
</SafeAreaView>
```

### Teaching Assistant
```tsx
<Modal visible={visible} onRequestClose={onClose}>
  <SafeAreaView style={styles.container}>
    <ConversationHeader
      title="Teaching Assistant"
      onClose={onClose}
      subtitle="Lesson: Advanced Algebra • Progress: 65%"
    />
    <ConversationContainer
      messages={messages}
      suggestedReplies={replies}
      onSendMessage={onSend}
      onSelectReply={onSelectReply}
      isLoading={isLoading}
      disabled={disabled}
      composerPlaceholder="Ask the teaching assistant..."
      loadingMessage="Teaching assistant is responding..."
    />
  </SafeAreaView>
</Modal>
```

## Quality Assurance

✅ **No Breaking Changes**
- All existing functionality preserved
- Public APIs unchanged
- Backward compatible

✅ **Type Safety**
- All components properly typed with TypeScript
- No runtime type errors

✅ **Linting & Formatting**
- Passes all linting checks
- Code formatted consistently

✅ **Visual Consistency**
- Both features now have identical:
  - Header styling
  - Close button affordance (✕)
  - Message bubble appearance
  - Quick reply styling
  - Composer input styling

## Future Enhancement Opportunities

This refactoring enables seamless addition of new conversation types:
1. **Study Buddy** - Share notes, quiz partners
2. **Mentor** - Personalized guidance and feedback
3. **Peer Tutor** - Learn from classmates
4. **Career Coach** - Resume, interview prep
5. **Subject Expert** - Deep dives into topics

Each new type simply needs to:
- Use `ConversationHeader` with appropriate title
- Use `ConversationContainer` for the UI
- Provide custom context/state management
- All will automatically inherit visual consistency

## Performance Impact

✅ No negative performance impact
✅ Shared components are already optimized
✅ Potential improvement: Easier to memoize shared components

## Migration Path

If you need to work on conversation-related features:

1. **Styling changes** → Update `ConversationHeader` and `ConversationContainer`
2. **Adding features** → Implement in shared components if beneficial for both types
3. **New conversation types** → Create feature-specific wrapper around shared components
4. **Learning Coach only** → Keep in `LearningCoachScreen` (e.g., resource upload, brief card)
5. **Teaching Assistant only** → Keep in `TeachingAssistantModal` or wrapper component

## Technical Debt Resolved

- ✅ Eliminated duplicated header code
- ✅ Unified close button affordance
- ✅ Consolidated message styling
- ✅ Removed repeated composition logic
- ✅ Established clear component reuse patterns
