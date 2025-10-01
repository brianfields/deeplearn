## Weimar Edge — Design Language

### Philosophy

Apple‑grade craft with Babylon Berlin grit. The system blends Art‑Deco geometry and Bauhaus reduction with modern iOS conventions. Make one bold move per screen; keep everything else quiet. Prioritize tactile clarity, generous spacing, predictable motion, and considered haptics. The tone is candid, understated, and assured.

### Core Principles

- **Poised, not precious**: minimal, precise foundations; add patina sparingly.
- **One bold move**: a single standout element (type or color) defines the screen.
- **Tactile clarity**: crisp hierarchy, large touch targets, subtle depth.
- **Motion reveals structure**: purposeful animations with consistent timing.
- **Accessibility by default**: contrast, Dynamic Type, reduced motion.

### Visual Language

#### Color

- **Light surfaces**: paper/0 (#F2EFE6)
- **Dark surfaces**: ink/900 (#0D0E10)
- **Primary accent**: accent/600 Petrol Blue (#0E3A53); pressed: accent/400 (#2F5D76)
- **Structure**: hairline borders at ~12–18% of on‑color
- **Status**: emerald/success (#3C7A5A), amber/warn (#D0822A), rouge/destructive (#4A1F1F), sky/info (#6BA3C8)
- Use gilt/500 (#C2A36B) sparingly for emphasis and decorative strokes.

Guidelines:
- Keep backgrounds quiet; avoid more than two brand colors per screen.
- On‑color text: On Light use ink/900; on Dark use paper/0.

#### Typography (iOS pts)

- Display 32/38 • H1 28/34 • H2 22/28 • Title 18/24 • Body 16/22 • Secondary 14/20 • Caption 12/16
- **Primary**: SF Pro (Text/Display). Optional display accent: condensed face (e.g., League Gothic) only for large titles or numbers.
- Tighten headings −2% to −4% at ≥24pt. Enforce one display per screen max.

#### Shape, Depth, Texture

- **Radius**: 4 • 8 • 12 • 20 • 28 (default cards 12; modals 20)
- **Elevation**: Flat (none, hairline border) • Raised (y=6, blur=24, 12–16% opacity) • Floating (y=10, blur=40, 18–22% opacity)
- Subtle film grain 2–4% on backgrounds only; never on text.

### Motion & Haptics

- **Durations**: 160ms (micro), 220ms (UI), 320ms (modal/view)
- **Easing**: Enter cubic‑bezier(0.2, 0.8, 0.2, 1); Exit cubic‑bezier(0.4, 0.0, 1, 1)
- **Stagger**: 24ms between list items
- **Spatial**: Slide along navigation axis; subtle parallax (~1.03×) on hero imagery
- **Haptics (iOS)**: Light selection for tabs/lists; medium impact for primary CTA; success/notify for confirmations

### Layout & Spacing

- 4‑pt base grid; 8‑pt for primary spacing
- Touch targets ≥44×44pt; list rows 56pt default
- Edge gutters: 20pt; hero layouts: 24–28pt
- Respect safe areas; avoid full‑bleed text

### Components

- **Buttons**: Radius 12; Primary (accent/600, on‑color text, Raised); Secondary (outline, transparent); Tertiary (text, underline on press); Destructive (rouge/600). Sizes: 32/44/52pt.
- **Cards**: Radius 12, hairline border, Raised elevation; optional oxblood glaze for imagery.
- **Inputs**: Height 44pt, radius 12, 1px border (ink 16% on Light / paper 14% on Dark); focus ring in gilt.
- **Lists/Cells**: 56pt rows, 16pt insets, hairline dividers; trailing divider hidden on group end.
- **Navigation**: Tabs ≤5; active semibold label; stack large title collapses to Title on scroll; sheets/modals radius 20 with subtle grabber.
- **Toasts**: 48pt, floating elevation, optional leading icon, 3.5s; swipe to dismiss.

### Images

The Weimar Edge aesthetic for generated imagery balances Apple-grade polish with the grit of Babylon Berlin. Visual compositions start from restrained Art-Deco geometry and Bauhaus clarity, letting a single bold move—often a Petrol Blue accent or a condensed typographic element—create focus against quiet, paper-light backdrops or ink-dark night scenes. Textures stay subtle: film grain whispers at 2–4%, hairline gilt strokes articulate structure, and shadows suggest shallow, purposeful depth. Imagery should honor the palette’s discipline—no more than two brand colors active at once—with high-contrast ink-on-paper lighting so details remain crisp even when the mood leans noir.

When imagining scenes or assets, prioritize tactile clarity and believable materials. Surfaces should feel slightly worn yet precise; think brushed metal signage, lacquered wood, or etched glass catching a narrow beam. Motion cues translate into dynamic compositions: staged parallax layers, shafts of light, or staggered elements that imply a 24ms rhythmic reveal. Characters and objects carry confident posture, with haptic cues visualized through poised gestures or tension in fabrics. Accessibility remains core—legible contrast, uncluttered space, and narratives that read instantly even at thumbnail scale—so every generated image speaks with the candid, understated assurance of the design system.


### Accessibility

- Contrast: AA 4.5:1 for body; 3:1 for large text
- Dynamic Type through XL; titles reflow, never truncate
- Respect Reduce Motion; swap slides for crossfades where appropriate
- VoiceOver: descriptive labels; announce sort/filter changes

### Do / Don’t

- Do keep backgrounds quiet; let a single accent or typographic move lead.
- Do use gilt sparingly for moments of delight and focus rings.
- Don’t mix more than two brand colors per screen.
- Don’t stack heavy shadows or apply texture to text.

### Implementation Notes

- Use semantic tokens (e.g., surface/subtle, text/default) instead of raw hex in app code.
- Favor platform‑native controls styled via tokens; keep custom components minimal.
- Ensure consistent naming across backend and frontend models to avoid adapters.
