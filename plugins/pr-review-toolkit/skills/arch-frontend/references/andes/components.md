# Andes Design System — Web Components

Andes (`@andes/*`) is MercadoLibre's official design system for web. Current version: 9.1.x.
It provides React components that are SSR-compatible with Nordic.

---

## Usage Principles

### Import Pattern

Each Andes component lives in its own package:

```tsx
import { Button } from '@andes/button';
import { Card } from '@andes/card';
import { TextField } from '@andes/textfield';
import { Snackbar } from '@andes/snackbar';
import { Badge } from '@andes/badge';
import { Tag } from '@andes/tag';
```

Never import from `@andes/andes` (the monolith) — always use individual packages.
This enables better tree-shaking and avoids bundle bloat.

### Never Override Andes CSS

```tsx
// ❌ WRONG — breaks design system consistency and future upgrades
<Button className="my-custom-button-override" />

// ✅ CORRECT — use the component's own API
<Button hierarchy="loud" size="large" />
```

If a component doesn't support a needed visual variation, open a request to the Andes team
or create a wrapper that composes Andes primitives without overriding CSS.

---

## Common Components

### Button (`@andes/button`)

```tsx
import { Button } from '@andes/button';

<Button
  hierarchy="loud"          // "loud" | "quiet" | "transparent"
  size="large"              // "large" | "medium" | "small"
  onClick={handleClick}
  disabled={isLoading}
>
  Submit
</Button>
```

### TextField (`@andes/textfield`)

```tsx
import { TextField } from '@andes/textfield';

<TextField
  label="Admin ID"
  value={value}
  onChange={(e) => setValue(e.target.value)}
  helper="Enter the admin identifier"
  modifier={error ? 'error' : undefined}
  message={error}
/>
```

### Card (`@andes/card`)

```tsx
import { Card } from '@andes/card';

<Card padding="16">
  <Card.Header title="Section Title" />
  <Card.Content>
    {/* content */}
  </Card.Content>
</Card>
```

### Snackbar (`@andes/snackbar`)

```tsx
import Snackbar from '@andes/snackbar';

<Snackbar
  show={showFeedback}
  message="Operation completed successfully"
  color="green"
  delay={3000}
  onClose={() => setShowFeedback(false)}
/>
```

### Badge / Tag

```tsx
import Badge from '@andes/badge';
import Tag from '@andes/tag';

<Badge content={count} type="standard" />
<Tag label="Active" color="green" />
```

---

## SSR Compatibility

All Andes components are SSR-compatible with Nordic. No special hydration wrappers needed.

If a component uses browser APIs (e.g., `window`, `document`), guard with:

```tsx
const [isMounted, setIsMounted] = React.useState(false);
React.useEffect(() => setIsMounted(true), []);

if (!isMounted) return null; // or a skeleton
```

---

## Layout with Andes

Andes provides layout primitives for consistent spacing and structure:

```tsx
// Use CSS classes from Andes design tokens
// Never use raw pixel values in styles
<div className="andes-container">
  <div className="andes-grid">
    {/* grid items */}
  </div>
</div>
```

---

## Icon Usage

Icons come from the MeLi icon set. Check the Andes documentation for available icons.

```tsx
import { IconShield20 } from '@andes/icons';

<IconShield20 color="var(--andes-color-brand-primary)" />
```

---

## Versioning

- Keep all `@andes/*` packages at the **same major.minor version** (e.g., all at 9.1.x)
- Mixed versions between Andes packages cause visual inconsistencies
- Run `npm outdated | grep @andes` to check alignment
- Upgrade all Andes packages together in a single PR
