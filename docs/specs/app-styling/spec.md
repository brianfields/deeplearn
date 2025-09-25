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
- Complete visual overhaul of the mobile app using Weimar Edge design system (see THEME DESCRIPTION below)
- Implement comprehensive design tokens (colors, typography, spacing, shadows) (see THEME DESCRIPTION below)
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
- [ ] All screens implement Weimar Edge visual design consistently (see THEME DESCRIPTION below)
- [ ] Navigation allows users to back out of any screen
- [ ] Interactive elements provide appropriate iOS haptic feedback
- [ ] Animations follow specified timing (160ms/220ms/320ms) with proper easing (see THEME DESCRIPTION below)
- [ ] Typography follows one-bold-move-per-screen principle
- [ ] Color palette strictly adheres to Babylon Berlin specifications (see THEME DESCRIPTION below)
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
- [x] Replace existing theme system in `ui_system/theme/theme.ts`
- [x] Update theme manager service for new token structure
- [x] Create Box primitive component for layout consistency
- [x] Create Text primitive component for typography hierarchy
- [x] Implement haptic feedback hook for iOS interactions
- [x] Create animation utilities with Weimar Edge timing specifications
- [x] Update ui_system public interface to export new primitives

### Phase 2: Core Component Redesign
- [x] Redesign Button component with four variants (primary, secondary, tertiary, destructive)
- [x] Update Button component with haptic feedback integration
- [x] Redesign Card component with 12pt radius, hairline borders, raised shadows
- [x] Update Progress component with new color system and animations
- [x] Test all ui_system components in isolation with new styling
- [x] Update ui_system unit tests for new component interfaces

### Phase 3: Catalog Module Styling
- [x] Redesign UnitListScreen with new visual hierarchy and search styling
- [x] Fix navigation flow to ensure back button functionality
- [x] Redesign UnitDetailScreen with floating content card and proper CTAs
- [x] Update UnitCard component with Weimar Edge styling and interactions
- [x] Style SearchFilters with new input design patterns
- [x] Update LessonCard component with typography and spacing improvements
- [x] Redesign UnitProgress component with new visual treatment

### Phase 4: Learning Session Styling
- [x] Redesign LearningFlowScreen with new visual treatment
- [x] Ensure escape navigation works properly from learning flow
- [x] Redesign ResultsScreen with celebration styling and haptic feedback
- [x] Update MultipleChoice component with new button styling and states
- [x] Style DidacticSnippet component with proper typography hierarchy
- [x] Update LearningFlow component with smooth transitions and new visual design

### Phase 5: Navigation and Integration
- [x] Update App.tsx with new theme provider integration
- [x] Configure navigation theme to work with Weimar Edge colors
- [x] Test complete user flow from UnitList → UnitDetail → LearningFlow → Results
- [x] Verify back navigation works from all screens
- [x] Test haptic feedback patterns across all interactions

### Phase 6: Polish and Quality Assurance
- [x] Ensure all components use design tokens exclusively (no ad-hoc styles)
- [x] Verify touch targets meet 44×44pt minimum requirements
- [x] Test typography hierarchy follows one-bold-move-per-screen principle
- [x] Validate color contrast meets accessibility standards
- [x] Test animations with proper timing and easing curves
- [x] Verify reduced motion support for accessibility
- [x] Remove any remnants of old theme system (colors, spacing, typography references)
- [x] Update maestro e2e tests with new testIDs if needed

### Phase 7: Final Validation
- [ ] Complete visual review of all screens against Weimar Edge specification
- [ ] Verify performance on target iOS devices
- [ ] Ensure no regressions in learning flow functionality
- [ ] Final haptic feedback testing and refinement
- [ ] Update maestro e2e tests in mobile/e2e if screen elements changed significantly
- [ ] Remove any outdated terminology or naming from previous theme system
- [ ] Follow the instructions in codegen/prompts/trace.md to ensure the user story is implemented correctly.
- [ ] Fix any issues documented during the tracing of the user story in docs.
- [ ] Follow the instructions in codegen/prompts/modulecheck.md to ensure the new code is following the modular architecture correctly.
- [ ] Examine all new code that has been created and make sure all of it is being used; there is no dead code, code meant for backward compatiblity, or code that has been deprecated.

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


--------------

THEME DESCRIPTION:

# Weimar Edge — Mobile Design System

*Apple‑grade craft, with Babylon Berlin grit*

---

## 1) Brand Principles

* **Poised, not precious.** Clean, precise foundations (Apple HIG) with selective patina and grain.
* **1920s Weimar noir.** Art‑Deco geometry, Bauhaus reduction, brass + oxblood accents.
* **One bold move per screen.** Typography or color carries attitude; everything else stays quiet.
* **Tactile clarity.** Crisp hierarchy, generous spacing, predictable motion, considered haptics.

### Tone of Voice (microcopy)

* **Candid**, **understated**, **assured**. Short sentences. No exclamation points.
* Examples: “Sync complete.” • “Saved to Drafts.” • “Try again in a moment.”

---

## 2) Visual Language

### Color System

A dual‑mode palette tuned for OLED. Babylon Berlin–inspired.

**Core Tokens**

* `ink/900` **Charcoal Noir** #0D0E10 (Text on Light, Surfaces on Dark)
* `paper/0` **Bone** #F2EFE6 (Light surfaces)
* `accent/600` **Petrol Blue** #0E3A53 (Primary brand accent)
* `accent/400` **Steel Blue** #2F5D76 (Pressed/hover)
* `accent/200` **Mist** #C2D3DB (Subtle borders on Light)
* `gilt/500` **Tarnished Gold** #C2A36B (Emphasis, dividers, icons)
* `rouge/600` **Oxblood** #4A1F1F (Destructive + highlights)
* `emerald/500` **Greenlight** #3C7A5A (Success)
* `amber/600` **Warn** #D0822A (Warning)
* `sky/500` **Info** #6BA3C8 (Info)

**Backgrounds**

* Light: `paper/0` #F2EFE6 → subtle vignette 2–3% top/bottom
* Dark: `ink/900` #0D0E10 with **film grain** (opacity 4–6%)

**On‑Color Text**

* On Light: `ink/900`
* On Dark: `paper/0`
* On Accent: `paper/0` at 96% opacity for long text

**Gradients** (sparingly)

* Petrol → Steel: #0E3A53 → #2F5D76 (hero, loading)
* Oxblood glaze: #4A1F1F → rgba(13,14,16,0.0) (card overlays)

**State Colors**

* Focus ring: `gilt/500` at 60% with 1.5px outer glow
* Pressed overlays: Black/White at 8–10% depending on mode

### Typography

* **Primary:** SF Pro (Text/Display). Dynamic Type required.
* **Display Accent (optional):** *League Gothic* (condensed, free) or *Big Shoulders Display* (variable). Use **only** for page titles or numbers.
* **Tracking:** Tighten headings −2% to −4% at ≥ 24pt. Body default tracking.

**Type Scale (iOS pts)**

* Display: 32/38 • H1: 28/34 • H2: 22/28 • Title: 18/24 • Body: 16/22 • Secondary: 14/20 • Caption: 12/16 • Mono: 13/18 (tabular)

**Do**: One display per screen max. **Don’t**: Mixed display fonts.

### Shape, Depth, Texture

* **Radius:** 4 • 8 • 12 • 20 • 28 (use 12 for default cards, 20 for modals)
* **Elevation:**

  * Flat: none, hairline border (1px @ 12% ink)
  * Raised: y=6, blur=24, opacity 12–16%
  * Floating: y=10, blur=40, opacity 18–22%
* **Borders:** 1px on Light (ink 14%), 1px on Dark (paper 12%)
* **Texture:** Subtle film grain overlay (2–4%), never on text.

### Iconography

* Stroke 1.5px, rounded joins, corner radius harmonized with 8‑pt grid.
* Filled variant for active states only. Use `gilt/500` for decorative line icons sparingly.

---

## 3) Motion & Haptics

* **Principles:** Smooth, purposeful, grounded. Motion reveals structure.
* **Durations:** 160ms (micro), 220ms (UI), 320ms (modal/view). Stagger lists 24ms.
* **Easing:**

  * Enter: cubic‑bezier(0.2, 0.8, 0.2, 1)
  * Exit: cubic‑bezier(0.4, 0.0, 1, 1)
* **Spatial:** Slide along axis of navigation; parallax 1.03× on hero images.
* **Haptics (iOS):**

  * Light selection for tabs, medium impact for primary CTA press, success/notify on completion.

---

## 4) Layout & Spacing

* **Grid:** 4‑pt base; 8‑pt for primary spacing.
* **Safe Areas:** Respect device insets; avoid full‑bleed text.
* **Touch Targets:** min 44×44pt; list rows 56pt default.
* **Content Margins:** 20pt edge gutters; 24–28pt for hero layouts.

---

## 5) Components

### Buttons

* **Primary:** Petrol background, on‑color text. Radius 12. Shadow (Raised). Pressed shift y=1.
* **Secondary:** Outline (ink 18% on Light / paper 16% on Dark), transparent fill.
* **Tertiary:** Text button, underline on press only.
* **Destructive:** Oxblood background; alert haptic on commit.

**Sizes:** Small 32pt • Medium 44pt • Large 52pt (padding x: 16/20/24)

**Icon Buttons:** 40pt min; use filled icon when active.

### Cards

* 12 radius, hairline border, Raised elevation. Optional oxblood glaze gradient for imagery.

### Lists & Cells

* 56pt row height; 16pt insets. Dividers: hairline; hide trailing divider on group end.
* Leading icons 24pt; accessory chevron 16pt at 60% opacity.

### Navigation

* **Tabs:** 5 max; active label weight semibold, 90% opacity for inactive.
* **Stacks:** Large title (Display or H1), collapses to Title on scroll.
* **Sheets/Modals:** 20 radius, grabber bar 36×4 at 20% opacity.

### Inputs

* Field height 44pt, radius 12, 1px border (ink 16% / paper 14%), focus ring in gilt.
* Inline validation: amber/warn or emerald/success with 12/16 caption.

### Toasts

* 48pt, floating elevation, left icon optional. Time 3.5s. Swipe to dismiss.

### Empty States

* One-line headline, one sentence support, one primary action. Monochrome illustration with gilt accent.

---

## 6) Accessibility

* **Contrast:** AA: 4.5:1 body; 3:1 large text ≥18pt. Test all accent‑on‑accent.
* **Dynamic Type:** Support through XL; titles reflow, never truncate.
* **Motion:** Respect “Reduce Motion”; swap slides for crossfades.
* **VoiceOver:** Descriptive labels; announce sort/filter changes.

---

## 7) Tokens (Design & Code)

```json
{
  "radius": {"sm":4, "md":8, "lg":12, "xl":20, "xxl":28},
  "space": [0,4,8,12,16,20,24,28,32,40,48],
  "elevation": {"flat":0, "raised":6, "floating":10},
  "color": {
    "ink":{"900":"#0D0E10"},
    "paper":{"0":"#F2EFE6"},
    "accent":{"200":"#C2D3DB","400":"#2F5D76","600":"#0E3A53"},
    "gilt":{"500":"#C2A36B"},
    "rouge":{"600":"#4A1F1F"},
    "emerald":{"500":"#3C7A5A"},
    "amber":{"600":"#D0822A"},
    "sky":{"500":"#6BA3C8"}
  }
}
```

**React Native (StyleSheet snippet)**

```ts
export const tokens = {
  radius: { sm: 4, md: 8, lg: 12, xl: 20, xxl: 28 },
  space:  [0,4,8,12,16,20,24,28,32,40,48],
  color: {
    bgLight: '#F2EFE6', bgDark: '#0D0E10',
    textLight: '#0D0E10', textDark: '#F2EFE6',
    accent: '#0E3A53', accentDim: '#2F5D76', gold: '#C2A36B',
    danger: '#4A1F1F', success: '#3C7A5A', warn: '#D0822A'
  },
  shadow: {
    raised: { shadowColor:'#000', shadowOpacity:0.14, shadowRadius:12, elevation:6 },
    floating:{ shadowColor:'#000', shadowOpacity:0.2, shadowRadius:20, elevation:10 }
  }
}
```

---

## 8) Photo & Illustration

* **Photography:** High‑contrast monochrome with selective petrol or gilt duotone.
* **Illustration:** Geometric deco motifs, thin strokes, 2‑color max.
* **Overlays:** 8–12% black/white scrim under type.

---

## 9) Screen Recipes

### Onboarding (Dark)

* Full‑bleed monochrome image with petrol → steel gradient at bottom.
* Display title (League Gothic or SF Display), one‑sentence body, Primary CTA.
* Progress dots in gilt; skip as tertiary.

### Home Feed (Light)

* Large title (H1), search as pill (radius 20), sections as cards.
* Sticky tab bar. Pull‑to‑refresh with medium haptic.

### Detail View

* Edge‑to‑edge media; content card lifted from bottom (20 radius).
* Primary CTA docked, floating elevation.

---

## 10) Do / Don’t

**Do**

* Keep backgrounds quiet; let type or a single accent lead.
* Use gilt sparingly for moments of delight.
* Lean on hairline borders for structure (not heavy dividers).

**Don’t**

* Mix more than 2 brand colors per screen.
* Overuse textures; no grain on text.
* Stack multiple strong shadows.

---

## 11) Implementation Notes

* Prefer platform‑native controls styled via tokens; keep custom components minimal.
* Use semantic names (`surface/subtle`, `surface/raised`), not raw hex, in app code.
* Build a **storybook** with light & dark permutations and a11y tests.


*References to study:* Apple HIG (iOS), Bauhaus posters (geometry/reduction), 1920s Art‑Deco wayfinding (type + icon pairing), Babylon Berlin stills (lighting, palette).
