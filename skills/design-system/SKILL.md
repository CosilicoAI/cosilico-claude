# Cosilico Design System

Use this skill when creating or modifying frontend components for cosilico.ai. This ensures consistent styling using our vanilla-extract based design system.

## CRITICAL Requirements

### 1. Always Use Vanilla Extract (CSS-in-JS)

**NEVER use plain CSS files.** All styles must use vanilla-extract for type-safety:

```typescript
// Create: src/styles/myComponent.css.ts
import { style } from '@vanilla-extract/css';
import { vars } from '../theme.css';

export const container = style({
  fontFamily: vars.font.display,
  background: vars.color.bg,
  color: vars.color.text,
});
```

```tsx
// Use in component:
import * as styles from '../styles/myComponent.css';

<div className={styles.container}>...</div>
```

### 2. Always Include Grid Background

**Every page MUST have the grid background.** This is a core Cosilico brand element:

```tsx
import * as styles from '../styles/myComponent.css';

export function MyPage() {
  return (
    <div className={styles.page}>
      <div className={styles.gridBg} />  {/* REQUIRED */}
      {/* page content */}
    </div>
  );
}
```

```typescript
// In your .css.ts file:
export const gridBg = style({
  position: 'fixed',
  inset: 0,
  pointerEvents: 'none',
  zIndex: 0,
  backgroundImage: `
    linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
  `,
  backgroundSize: '40px 40px',
  maskImage: 'radial-gradient(ellipse 80% 80% at 50% 20%, black 40%, transparent 100%)',
});
```

## Theme Tokens (src/theme.css.ts)

All design values come from the theme contract. **Never hardcode colors, fonts, or spacing.**

### Fonts
```typescript
vars.font.display  // 'Geist' - headings, UI
vars.font.body     // 'Crimson Pro' - body text, italic accents
vars.font.mono     // 'JetBrains Mono' - code, data
```

### Colors
```typescript
// Backgrounds
vars.color.void         // #050508 - deepest black
vars.color.bg           // #08080c - page background
vars.color.bgElevated   // #0e0e14 - slightly elevated
vars.color.bgCard       // #12121a - card backgrounds
vars.color.surface      // #1a1a24 - interactive surfaces

// Borders
vars.color.border       // #252532 - standard borders
vars.color.borderSubtle // #1c1c28 - subtle dividers
vars.color.borderGlow   // #3a3a52 - hover state

// Text
vars.color.text          // #f0f0f5 - primary text
vars.color.textSecondary // #b8b8c8 - secondary text
vars.color.textMuted     // #707088 - muted/labels
vars.color.textFaint     // #505068 - very dim

// Accent (cyan)
vars.color.accent        // #00d4ff - primary accent
vars.color.accentBright  // #40e8ff - hover state
vars.color.accentDim     // #0099bb - darker variant
vars.color.accentGlow    // rgba(0, 212, 255, 0.15) - subtle glow

// Status
vars.color.success       // #00ff88 - success/passed
vars.color.successGlow   // rgba(0, 255, 136, 0.15)
vars.color.warning       // #ffaa00 - warnings
vars.color.error         // #ff4466 - errors/failed
vars.color.amber         // #ffaa00 - amber accent
```

### Spacing
```typescript
vars.space.xs   // 4px
vars.space.sm   // 8px
vars.space.md   // 16px
vars.space.lg   // 24px
vars.space.xl   // 32px
vars.space['2xl'] // 48px
vars.space['3xl'] // 64px
vars.space['4xl'] // 96px
```

### Border Radius
```typescript
vars.radius.sm   // 4px
vars.radius.md   // 8px
vars.radius.lg   // 12px
vars.radius.xl   // 16px
vars.radius['2xl'] // 24px
```

### Animation
```typescript
vars.duration.fast   // 150ms
vars.duration.normal // 250ms
vars.duration.slow   // 400ms

vars.ease.out    // cubic-bezier(0.16, 1, 0.3, 1)
vars.ease.spring // cubic-bezier(0.34, 1.56, 0.64, 1)
```

## Common Patterns

### Card Component
```typescript
export const card = style({
  background: vars.color.bgCard,
  border: `1px solid ${vars.color.border}`,
  borderRadius: vars.radius.lg,
  padding: vars.space.lg,
  transition: `all ${vars.duration.normal} ${vars.ease.out}`,
  ':hover': {
    borderColor: vars.color.borderGlow,
    boxShadow: `0 0 20px ${vars.color.accentGlow}`,
  },
});
```

### Gradient Text
```typescript
export const gradientText = style({
  background: `linear-gradient(135deg, #fff 0%, ${vars.color.accent} 100%)`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
});
```

### Status Indicators
```typescript
export const passed = style({
  color: vars.color.success,
  background: vars.color.successGlow,
});

export const failed = style({
  color: vars.color.error,
  background: 'rgba(255, 68, 102, 0.15)',
});
```

### Badge/Pill
```typescript
export const badge = style({
  display: 'inline-block',
  padding: `6px ${vars.space.md}`,
  background: vars.color.accentGlow,
  border: '1px solid rgba(0, 212, 255, 0.3)',
  borderRadius: '100px',
  fontSize: '11px',
  fontWeight: 600,
  letterSpacing: '1.5px',
  color: vars.color.accent,
  textTransform: 'uppercase',
});
```

### Mono Data Display
```typescript
export const dataValue = style({
  fontFamily: vars.font.mono,
  fontSize: '14px',
  color: vars.color.accent,
});
```

### Interactive Row
```typescript
export const tableRow = style({
  display: 'grid',
  padding: `${vars.space.md} ${vars.space.lg}`,
  borderBottom: `1px solid ${vars.color.borderSubtle}`,
  cursor: 'pointer',
  transition: `all ${vars.duration.fast}`,
  ':hover': {
    background: vars.color.accentGlow,
  },
});
```

## Responsive Design

Use globalStyle for media queries:

```typescript
import { globalStyle } from '@vanilla-extract/css';

globalStyle(`@media (max-width: 768px) .${container}`, {
  padding: vars.space.md,
  flexDirection: 'column',
});
```

## File Naming

- Style files: `myComponent.css.ts` (camelCase)
- Import as: `import * as styles from '../styles/myComponent.css'`
- Use with: `className={styles.myClass}`

## Example: Complete Page Structure

```tsx
// src/pages/MyPage.tsx
import * as styles from '../styles/myPage.css';

export function MyPage() {
  return (
    <div className={styles.page}>
      {/* Grid background - REQUIRED */}
      <div className={styles.gridBg} />

      {/* Hero section */}
      <header className={styles.hero}>
        <div className={styles.badge}>MY PAGE</div>
        <h1 className={styles.title}>Page Title</h1>
        <p className={styles.subtitle}>Descriptive subtitle text</p>
      </header>

      {/* Main content */}
      <main className={styles.content}>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Section</h2>
          <div className={styles.card}>
            {/* Card content */}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <span>Footer text</span>
      </footer>
    </div>
  );
}
```

## Checklist Before Submitting

- [ ] Uses vanilla-extract (`.css.ts` files), NOT plain CSS
- [ ] Grid background included on every page
- [ ] All colors from `vars.color.*`
- [ ] All fonts from `vars.font.*`
- [ ] All spacing from `vars.space.*`
- [ ] Proper hover/transition states
- [ ] Responsive styles for mobile
