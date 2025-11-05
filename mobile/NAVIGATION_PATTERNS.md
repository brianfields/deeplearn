# Navigation Patterns Guide

This document defines the consistent navigation patterns used throughout the mobile app.

## Screen Types & Options

All screens should use one of these patterns via `getScreenOptions()`:

### 1. Stack Navigation (Primary Journey)

**Use for**: Sequential screens, main user flow, browsing

```typescript
options={getScreenOptions('stack')}
// or with custom title:
options={{
  ...getScreenOptions('stack'),
  title: 'Screen Name',
}}
```

**Behavior**:

- Animates in from RIGHT
- Swipe LEFT to go back (semantic)
- Part of navigation breadcrumb
- Fills entire screen
- Examples: LearningCoach, UnitDetail, UnitLODetail

---

### 2. Modal (Quick Overlays)

**Use for**: Non-blocking actions, quick interactions, overlays on current screen

```typescript
options={getScreenOptions('modal')}
// or with custom title:
options={{
  ...getScreenOptions('modal'),
  title: 'Modal Title',
}}
```

**Behavior**:

- Animates in from BOTTOM
- Swipe DOWN to dismiss (semantic)
- Overlay on previous screen (iOS shows card)
- Respects reduced motion setting
- Examples: CatalogBrowser, AddResource

---

### 3. Detail (Card Presentation - iOS)

**Use for**: Detailed views with card-style overlay (future use)

```typescript
options={getScreenOptions('detail')}
```

**Behavior**:

- Shows previous screen underneath (iOS)
- Animates in from BOTTOM
- Swipe DOWN to dismiss
- Partial screen height or custom sizing

---

### 4. Locked (No Gestures)

**Use for**: Screens where navigation should be prevented (learning sessions, results)

```typescript
options={getScreenOptions('locked')}
// or with custom title:
options={{
  ...getScreenOptions('locked'),
  title: 'Learning Session',
}}
```

**Behavior**:

- No swipe gestures enabled
- Only back button or programmatic navigation works
- Prevents accidental exits
- Examples: LearningFlow, Results

---

## Navigator Configuration

### LearningStack (Default Options)

```typescript
<LearningStack.Navigator
  screenOptions={{
    headerShown: false,
    animation: 'slide_from_right',
    animationDuration: 220,
    gestureDirection: 'horizontal',  // ← semantic
    contentStyle: { backgroundColor: theme.colors.background },
  }}
>
```

**Key settings**:

- `animation: 'slide_from_right'` - default for stack
- `animationDuration: 220` - smooth but responsive
- `gestureDirection: 'horizontal'` - enables left swipe back
- All individual screens inherit these defaults (override as needed)

### RootStack (Authentication Flow)

```typescript
<RootStack.Navigator
  screenOptions={{
    headerShown: false,
    animation: 'slide_from_right',
    animationDuration: 220,
    gestureDirection: 'horizontal',  // ← semantic
    contentStyle: { backgroundColor: theme.colors.background },
  }}
>
```

Same pattern as LearningStack for consistency.

---

## Current Navigation Structure

```
RootStack
├── Auth Screens (stack)
│   ├── Login
│   └── Register
└── User Screens (stack)
    ├── Dashboard (LearningStackNavigator)
    └── LessonDetail (locked - from outside stack)

LearningStack
├── LessonList (default stack)
├── Modals (quick actions)
│   ├── CatalogBrowser (modal)
│   └── AddResource (modal)
├── Stack Screens (primary journey)
│   ├── LearningCoach (stack)
│   ├── UnitDetail (stack)
│   ├── UnitLODetail (stack)
│   ├── LearningFlow (locked)
│   └── Results (locked)
└── Dev Tools (conditional __DEV__)
    ├── ManageCache (modal)
    ├── SQLiteDetail (modal)
    ├── AsyncStorageDetail (modal)
    └── FileSystemDetail (modal)
```

---

## Adding New Screens

### Template for Stack Screen

```typescript
<LearningStack.Screen
  name="ScreenName"
  component={ScreenComponent}
  options={{
    ...getScreenOptions('stack'),
    title: 'Display Title',
  }}
/>
```

### Template for Modal Screen

```typescript
<LearningStack.Screen
  name="ModalName"
  component={ModalComponent}
  options={getScreenOptions('modal')}
/>
```

### Template for Locked Screen (No Swipe)

```typescript
<LearningStack.Screen
  name="LockedScreen"
  component={LockedComponent}
  options={{
    ...getScreenOptions('locked'),
    title: 'Display Title',
  }}
/>
```

### Template for Dev Screen (Dev-only)

```typescript
{__DEV__ && (
  <LearningStack.Screen
    name="DevScreen"
    component={DevComponent}
    options={{
      ...getDevScreenOptions(),
      title: 'Dev Tool',
    }}
  />
)}
```

---

## Accessibility

### Reduced Motion

All animations automatically respect the system's `prefers-reduced-motion` setting:

```typescript
// Defined in navigationOptions.ts
const noAnimation = reducedMotion.enabled ? 'none' : undefined;
```

When `reducedMotion.enabled === true`:

- All animations disabled
- Instant transitions
- Gestures still work
- No performance impact

### Android Back Button

- **Stack screens**: Back button pops to previous screen
- **Modal screens**: Back button dismisses modal (via `onRequestClose`)
- **Locked screens**: Back button behavior depends on implementation

---

## Icons & Visual Indicators

### Screen Titles

- **Stack screens**: Show title without visual indicator
- **Modal screens**: May show title or "X" close button
- **Dev screens**: Append " (Dev)" to title to indicate development tool

Example:

```typescript
// Stack
title: 'Unit Details';

// Modal (close button shown)
title: 'Add Resource';

// Dev tool
title: 'SQLite Database (Dev)';
```

---

## Common Patterns

### Navigation from Stack to Modal

```typescript
// In UnitDetail (stack screen)
navigation.navigate('AddResource', { attachToConversation: true });
// → Opens AddResource as overlay modal
```

### Navigation Back from Modal

```typescript
// In AddResource modal
navigation.goBack();
// → Dismisses modal, returns to previous stack screen
```

### Programmatic Navigation

```typescript
// Go to another stack screen
navigation.navigate('UnitDetail', { unitId: '123' });

// Go back without modal interaction
navigation.goBack();
```

---

## Code Examples

### Complete Screen Definition (Stack)

```typescript
<LearningStack.Screen
  name="UnitDetail"
  component={UnitDetailScreen}
  options={{
    ...getScreenOptions('stack'),
    title: 'Unit Details',
  }}
/>
```

### Complete Screen Definition (Modal)

```typescript
<LearningStack.Screen
  name="CatalogBrowser"
  component={CatalogBrowserScreen}
  options={getScreenOptions('modal')}
/>
```

### Navigator Setup

```typescript
<LearningStack.Navigator
  screenOptions={{
    headerShown: false,
    animation: 'slide_from_right',
    animationDuration: 220,
    gestureDirection: 'horizontal',
    contentStyle: { backgroundColor: theme.colors.background },
  }}
>
  {/* screens go here */}
</LearningStack.Navigator>
```

---

## Quick Reference

| Pattern    | Animation         | Gesture              | Use Case               | Accessibility     |
| ---------- | ----------------- | -------------------- | ---------------------- | ----------------- |
| **stack**  | slide_from_right  | left swipe = back    | Primary journey        | ✅ reduced motion |
| **modal**  | slide_from_bottom | down swipe = dismiss | Quick actions          | ✅ reduced motion |
| **detail** | slide_from_bottom | down swipe = dismiss | Card overlay (future)  | ✅ reduced motion |
| **locked** | (inherited)       | none                 | No exit during session | ✅ no motion      |

---

## Maintenance

When adding new screens:

1. Choose appropriate type (stack/modal/locked)
2. Use `getScreenOptions(type)` utility
3. Add title if needed
4. Verify gesture direction matches intent
5. Test on iOS and Android
6. Check accessibility with reduced motion enabled

When updating navigation:

1. Keep patterns consistent
2. Don't mix hardcoded options with utilities
3. Always use the utility for new screens
4. Document any exceptions
5. Run linter to catch inconsistencies
