# App-Styling Feature Specification

## User Story

As a mobile app user, I want the learning application to have a beautiful, cohesive design system inspired by Weimar Edge aesthetics (Apple-grade craft with Babylon Berlin grit) so that:

- **Navigation feels intuitive and escapable** - I can always back out of any screen and understand where I am in the app flow
- **Visual experience is stunning and consistent** - Every screen follows the same design language with Art-Deco geometry, muted Babylon Berlin colors (charcoal noir, bone, petrol blue, tarnished gold), and Bauhaus reduction principles
- **Interactions feel premium and responsive** - Button presses, screen transitions, and gestures provide appropriate haptic feedback and smooth animations with purposeful motion
- **Content hierarchy is clear** - Typography follows the one-bold-move-per-screen principle with SF Pro as primary and accent fonts for display text
- **Learning experience is enhanced** - Interactive learning components (multiple choice, didactic snippets) maintain their functionality while adopting the sophisticated visual treatment

## Requirements Summary

### What to Build
- Complete visual overhaul of the mobile app using Weimar Edge design system
- Implement comprehensive design tokens (colors, typography, spacing, shadows)
- Update all UI components with new styling while maintaining functionality
- Ensure proper navigation escape routes on all screens
- Add iOS haptic feedback patterns for premium interactions
- Apply smooth animation transitions with specific timing and easing

### Constraints
- iOS-focused development (haptics, fonts, platform-specific optimizations)
- Maintain existing navigation structure and business logic
- No new features - purely styling enhancements
- No backend changes required
- Use system fonts (SF Pro) with free accent font alternatives
- Single theme mode (no light/dark theme switching)
- Performance optimized for modern devices

### Acceptance Criteria
- [ ] All screens implement Weimar Edge visual design consistently
- [ ] Navigation allows users to back out of any screen
- [ ] Interactive elements provide appropriate iOS haptic feedback
- [ ] Animations follow specified timing (160ms/220ms/320ms) with proper easing
- [ ] Typography follows one-bold-move-per-screen principle
- [ ] Color palette strictly adheres to Babylon Berlin specifications
- [ ] Touch targets meet 44×44pt minimum with 56pt for list rows
- [ ] Components use design tokens exclusively (no ad-hoc styling)
- [ ] Learning flow maintains pedagogical effectiveness with new styling

## Cross-Stack Implementation Plan

### Backend Changes
**NONE** - This is a frontend-only styling project.

### Frontend Module Changes

#### 1. `mobile/modules/ui_system/` [CORE FOUNDATION]

**Files to Modify:**
- `theme/theme.ts` - Replace existing theme with Weimar Edge design tokens
- `theme/theme-manager.ts` - Update theme service integration
- `components/Button.tsx` - Complete redesign with new variants and haptics
- `components/Card.tsx` - Update with 12pt radius, borders, shadows
- `components/Progress.tsx` - Apply new color system and styling
- `models.ts` - Update type definitions for new theme structure
- `service.ts` - Enhance with haptic integration and animation utilities
- `public.ts` - Export new primitives and utilities

**Files to Add:**
- `tokens/index.ts` - Weimar Edge design tokens (colors, spacing, typography)
- `components/primitives/Box.tsx` - Layout primitive with spacing system
- `components/primitives/Text.tsx` - Typography primitive with variants
- `hooks/useHaptics.ts` - iOS haptic feedback integration
- `utils/animations.ts` - Animation utilities with Weimar Edge timing/easing
- `utils/motion.ts` - Reanimated motion presets and reduced motion support

#### 2. `mobile/modules/catalog/` [BROWSING EXPERIENCE]

**Files to Modify:**
- `screens/UnitListScreen.tsx` - Apply new styling, improve search UX
- `screens/UnitDetailScreen.tsx` - Redesign with new visual treatment, fix navigation
- `components/UnitCard.tsx` - Weimar Edge card styling with proper shadows
- `components/SearchFilters.tsx` - New input styling with focus states
- `components/LessonCard.tsx` - Updated visual design with typography hierarchy
- `components/UnitProgress.tsx` - New progress bar styling and animations

#### 3. `mobile/modules/learning_session/` [LEARNING EXPERIENCE]

**Files to Modify:**
- `screens/LearningFlowScreen.tsx` - Apply new styling, ensure escape navigation
- `screens/ResultsScreen.tsx` - Redesign with celebration animations and haptics
- `components/MultipleChoice.tsx` - Weimar Edge button styling with interaction states
- `components/DidacticSnippet.tsx` - New typography treatment and spacing
- `components/LearningFlow.tsx` - Updated transitions and visual hierarchy

#### 4. Root Application

**Files to Modify:**
- `mobile/App.tsx` - Update theme provider and navigation theme integration

**Dependencies to Add:**
- `@shopify/restyle` - Design token system integration
- `expo-blur` - Modal and sheet blur effects

**No Database Changes Required:**
- This is a frontend-only styling project with no data model changes
- No migrations needed
- No seed data updates required

## Implementation Checklist

### Phase 1: Design System Foundation
- [x] Create Weimar Edge design tokens in `ui_system/tokens/index.ts`
- [ ] Replace existing theme system in `ui_system/theme/theme.ts`
- [ ] Update theme manager service for new token structure
- [ ] Create Box primitive component for layout consistency
- [ ] Create Text primitive component for typography hierarchy
- [ ] Implement haptic feedback hook for iOS interactions
- [ ] Create animation utilities with Weimar Edge timing specifications
- [ ] Update ui_system public interface to export new primitives

### Phase 2: Core Component Redesign
- [ ] Redesign Button component with four variants (primary, secondary, tertiary, destructive)
- [ ] Update Button component with haptic feedback integration
- [ ] Redesign Card component with 12pt radius, hairline borders, raised shadows
- [ ] Update Progress component with new color system and animations
- [ ] Test all ui_system components in isolation with new styling
- [ ] Update ui_system unit tests for new component interfaces

### Phase 3: Catalog Module Styling
- [ ] Redesign UnitListScreen with new visual hierarchy and search styling
- [ ] Fix navigation flow to ensure back button functionality
- [ ] Redesign UnitDetailScreen with floating content card and proper CTAs
- [ ] Update UnitCard component with Weimar Edge styling and interactions
- [ ] Style SearchFilters with new input design patterns
- [ ] Update LessonCard component with typography and spacing improvements
- [ ] Redesign UnitProgress component with new visual treatment

### Phase 4: Learning Session Styling
- [ ] Redesign LearningFlowScreen with new visual treatment
- [ ] Ensure escape navigation works properly from learning flow
- [ ] Redesign ResultsScreen with celebration styling and haptic feedback
- [ ] Update MultipleChoice component with new button styling and states
- [ ] Style DidacticSnippet component with proper typography hierarchy
- [ ] Update LearningFlow component with smooth transitions and new visual design

### Phase 5: Navigation and Integration
- [ ] Update App.tsx with new theme provider integration
- [ ] Configure navigation theme to work with Weimar Edge colors
- [ ] Test complete user flow from UnitList → UnitDetail → LearningFlow → Results
- [ ] Verify back navigation works from all screens
- [ ] Test haptic feedback patterns across all interactions

### Phase 6: Polish and Quality Assurance
- [ ] Ensure all components use design tokens exclusively (no ad-hoc styles)
- [ ] Verify touch targets meet 44×44pt minimum requirements
- [ ] Test typography hierarchy follows one-bold-move-per-screen principle
- [ ] Validate color contrast meets accessibility standards
- [ ] Test animations with proper timing and easing curves
- [ ] Verify reduced motion support for accessibility
- [ ] Remove any remnants of old theme system (colors, spacing, typography references)
- [ ] Update maestro e2e tests with new testIDs if needed

### Phase 7: Final Validation
- [ ] Complete visual review of all screens against Weimar Edge specification
- [ ] Test complete user journeys with new styling
- [ ] Verify performance on target iOS devices
- [ ] Ensure no regressions in learning flow functionality
- [ ] Final haptic feedback testing and refinement
- [ ] Update maestro e2e tests in mobile/e2e if screen elements changed significantly
- [ ] Remove any outdated terminology or naming from previous theme system

## Technical Notes

### Design Token Structure
```typescript
export const tokens = {
  radius: { sm: 4, md: 8, lg: 12, xl: 20, xxl: 28 },
  space: [0, 4, 8, 12, 16, 20, 24, 28, 32, 40, 48],
  color: {
    ink900: '#0D0E10',
    paper0: '#F2EFE6', 
    accent600: '#0E3A53',
    accent400: '#2F5D76',
    accent200: '#C2D3DB',
    gilt500: '#C2A36B',
    rouge600: '#4A1F1F',
    emerald500: '#3C7A5A',
    amber600: '#D0822A',
    sky500: '#6BA3C8'
  }
}
```

### Animation Specifications
- **Micro interactions**: 160ms with cubic-bezier(0.2, 0.8, 0.2, 1)
- **UI transitions**: 220ms with cubic-bezier(0.2, 0.8, 0.2, 1) 
- **Modal/view changes**: 320ms with cubic-bezier(0.4, 0.0, 1, 1) for exit
- **List stagger**: 24ms delay between items

### Haptic Feedback Patterns
- **Light selection**: Tab switches, list item selection
- **Medium impact**: Primary button press, toggle states
- **Success notification**: Completion events, correct answers

### Typography Scale (iOS points)
- **Display**: 32/38 (League Gothic condensed equivalent using SF Pro)
- **H1**: 28/34 with -0.3pt letter spacing
- **H2**: 22/28
- **Title**: 18/24 
- **Body**: 16/22
- **Secondary**: 14/20 at 80% opacity
- **Caption**: 12/16 at 70% opacity

## Success Metrics

The app-styling feature will be considered successful when:
1. All screens consistently implement Weimar Edge design language
2. Users can navigate backward from any screen in the application
3. Interactive elements provide appropriate haptic feedback on iOS
4. Animations follow specified timing and feel smooth and purposeful
5. Typography hierarchy is clear with one bold element per screen
6. Learning functionality is preserved while visual experience is enhanced
7. No ad-hoc styling remains - all styles derive from design tokens