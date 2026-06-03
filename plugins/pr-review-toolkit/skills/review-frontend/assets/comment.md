# Frontend Code Review Comment Template

Use this template for EACH issue found during the review.
Fill in all `{...}` placeholders with specific information from the diff.

---

## Base Template

```markdown
---

**File:** `{filepath}`
**Lines:** {start_line}-{end_line}
**Category:** {category_id} {category_name}
**Severity:** {severity}

**Issue:**
{clear and objective description of the problem in 1-2 sentences}

**Current Code:**
```{language}
{problematic code extracted from the diff — exactly as it appears}
```

**Suggested Code:**
```{language}
{corrected code — must be valid and follow platform conventions}
```

**Rationale:**
{technical explanation of why this is a problem}
{impact if not fixed: performance, accessibility, security, UX}

**Reference:**
- Checklist: {check_id} — {check_name}
{other references: Andes docs, Nordic docs, MDN, etc.}
```

---

## Language Field Guide

| File Extension | Language Tag |
|---------------|-------------|
| `.tsx` | `tsx` |
| `.jsx` | `jsx` |
| `.ts` | `typescript` |
| `.js` | `javascript` |
| `.css` | `css` |
| `.scss` | `scss` |
| `.json` | `json` |

---

## Examples of Filled-in Comments

### Example 1 — XSS via dangerouslySetInnerHTML (Critical)

```markdown
---

**File:** `src/components/UserBio.tsx`
**Lines:** 14-16
**Category:** SEC Security
**Severity:** Critical

**Issue:**
User-provided HTML is rendered via `dangerouslySetInnerHTML` without sanitization,
allowing stored XSS attacks.

**Current Code:**
```tsx
<div dangerouslySetInnerHTML={{ __html: user.bio }} />
```

**Suggested Code:**
```tsx
import DOMPurify from 'dompurify';
// ...
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(user.bio) }} />
```

**Rationale:**
An attacker can inject `<script>` tags or event handlers via the bio field.
DOMPurify strips dangerous elements while preserving safe HTML formatting.

**Reference:**
- Checklist: SEC1 — XSS via dangerouslySetInnerHTML
```

---

### Example 2 — Hardcoded String (Medium)

```markdown
---

**File:** `src/pages/Checkout.tsx`
**Lines:** 42-42
**Category:** I18N Internationalization
**Severity:** Medium

**Issue:**
User-visible string is hardcoded in JSX instead of using the i18n translation function.

**Current Code:**
```tsx
<Button>Finalizar compra</Button>
```

**Suggested Code:**
```tsx
<Button>{t('checkout.finalize_button')}</Button>
```

**Rationale:**
MercadoLibre operates across LATAM. All user-facing strings must be translatable.
Hardcoded strings in Spanish will display incorrectly for Portuguese, English, and other locales.

**Reference:**
- Checklist: I18N1 — Hardcoded Strings
```

---

### Example 3 — Raw HTML Instead of Andes Component (Medium)

```markdown
---

**File:** `src/components/SearchBar.tsx`
**Lines:** 8-12
**Category:** PLAT Platform
**Severity:** Medium

**Issue:**
Using raw `<input>` element where Andes `<TextField>` provides consistent styling,
accessibility, and validation out of the box.

**Current Code:**
```tsx
<input
  type="text"
  placeholder="Buscar..."
  onChange={handleChange}
/>
```

**Suggested Code:**
```tsx
import { TextField } from '@andes/textfield';
// ...
<TextField
  label={t('search.placeholder')}
  onChange={handleChange}
/>
```

**Rationale:**
Andes components ensure visual consistency with MercadoLibre's design system,
include built-in accessibility attributes, and follow responsive guidelines.

**Reference:**
- Checklist: PLAT1 — Wrong Andes Component
```

---

### Example 4 — Missing SSR Guard (High)

```markdown
---

**File:** `src/components/Analytics.tsx`
**Lines:** 5-7
**Category:** PLAT Platform
**Severity:** High

**Issue:**
Direct access to `window.localStorage` without SSR guard. Nordic renders on the server
where `window` is undefined, causing a runtime crash.

**Current Code:**
```tsx
const token = window.localStorage.getItem('auth_token');
```

**Suggested Code:**
```tsx
const token = typeof window !== 'undefined'
  ? window.localStorage.getItem('auth_token')
  : null;
```

**Rationale:**
Nordic uses server-side rendering. Any browser-only API (`window`, `document`,
`localStorage`) must be guarded with a `typeof window !== 'undefined'` check
or placed inside `useEffect` which only runs on the client.

**Reference:**
- Checklist: PLAT4 — Nordic SSR Compatibility
```

---

### Example 5 — Unnecessary Re-renders (Medium)

```markdown
---

**File:** `src/components/ProductList.tsx`
**Lines:** 22-28
**Category:** PERF Performance
**Severity:** Medium

**Issue:**
A new array is created on every render via `.filter()` inside JSX, causing all child
components to re-render even when the source data has not changed.

**Current Code:**
```tsx
return (
  <List>
    {products.filter(p => p.active).map(product => (
      <ProductCard key={product.id} product={product} />
    ))}
  </List>
);
```

**Suggested Code:**
```tsx
const activeProducts = useMemo(
  () => products.filter(p => p.active),
  [products]
);

return (
  <List>
    {activeProducts.map(product => (
      <ProductCard key={product.id} product={product} />
    ))}
  </List>
);
```

**Rationale:**
Without `useMemo`, the `.filter()` runs on every render and produces a new array reference,
defeating `React.memo` on child components. Memoizing stabilizes the reference and avoids
unnecessary reconciliation when `products` has not changed.

**Reference:**
- Checklist: PERF1 — Unnecessary Re-renders
```

---

## Positive Points Section (Always Include)

At the end of the review for each file:

```markdown
### Positive Points

1. {well-implemented aspect — be specific}
2. {good practice followed}
3. {quality worth highlighting}
```
