# Frontend Code Review Checklist

Use during the review of each modified file. 34 checks divided into 9 categories.

---

## SEC — Security (4 checks)

- [ ] **SEC1 — XSS via dangerouslySetInnerHTML**: Using `dangerouslySetInnerHTML` without DOMPurify sanitization? Never trust user input in innerHTML
- [ ] **SEC2 — Exposed Secrets in Client**: API keys, tokens, or secrets in client-side code or environment variables prefixed with `NEXT_PUBLIC_`/`REACT_APP_`? Move to server-side or use Fury secrets
- [ ] **SEC3 — Unsanitized URL Parameters**: Using `window.location`, `URLSearchParams`, or route params directly in DOM or API calls without validation?
- [ ] **SEC4 — Insecure External Resources**: Loading scripts, images, or iframes from untrusted origins without CSP or integrity checks?

---

## PERF — Performance (4 checks)

- [ ] **PERF1 — Unnecessary Re-renders**: Component re-renders on every parent render without `React.memo`, `useMemo`, or `useCallback` for expensive computations or stable references?
- [ ] **PERF2 — Large Bundle Import**: Importing entire library when only a submodule is needed (e.g., `import _ from 'lodash'` instead of `import get from 'lodash/get'`)? Use tree-shakeable imports
- [ ] **PERF3 — Missing Code Splitting**: Large component imported synchronously that could be `React.lazy()` + `Suspense`? Check route-level and modal-level splits
- [ ] **PERF4 — Unoptimized Images/Assets**: Large images without `loading="lazy"`, missing width/height (CLS), or uncompressed assets?

---

## A11Y — Accessibility (3 checks)

- [ ] **A11Y1 — Missing ARIA/Semantic HTML**: Interactive elements without proper `role`, `aria-label`, or using `<div onClick>` instead of `<button>`?
- [ ] **A11Y2 — Missing Alt Text**: Images without `alt` attribute, or decorative images without `alt=""`?
- [ ] **A11Y3 — Keyboard Navigation**: Interactive elements not reachable via Tab, missing focus styles, or custom widgets without keyboard handlers?

---

## I18N — Internationalization (3 checks)

- [ ] **I18N1 — Hardcoded Strings**: User-visible text written directly in JSX instead of using translation function (`t()`, `i18n()`, `getI18n()`)?
- [ ] **I18N2 — Missing Translation Keys**: New UI text added without corresponding entries in translation files/JSON?
- [ ] **I18N3 — Locale-Dependent Formatting**: Dates, numbers, or currencies formatted without `Intl` API or i18n library? Hardcoded date formats like `MM/DD/YYYY`?

---

## TEST — Testing (3 checks)

- [ ] **TEST1 — Missing Component Tests**: New or significantly modified component without corresponding test file? At minimum: render test + key interaction test
- [ ] **TEST2 — Snapshot-Only Tests**: Test file contains only snapshot tests (`toMatchSnapshot`) without behavioral assertions? Snapshots alone miss logic bugs
- [ ] **TEST3 — Missing User Interaction Tests**: Interactive component (forms, buttons, modals) without `userEvent` or `fireEvent` tests for key user flows?

---

## QUAL — Code Quality (5 checks)

- [ ] **QUAL1 — Any/Unknown Types**: TypeScript code using `any`, `unknown` cast, or `@ts-ignore` without justification? Type properly or add explanatory comment
- [ ] **QUAL2 — Magic Numbers/Strings**: Hardcoded numeric or string values without named constants? Extract to constants or enums
- [ ] **QUAL3 — Duplicated Logic**: Same logic repeated in 2+ components? Extract to custom hook or utility function
- [ ] **QUAL4 — Dead Code**: Commented-out code, unreachable branches, unused imports or variables? Remove or add TODO with ticket
- [ ] **QUAL5 — Effect Dependency Issues**: `useEffect` with missing or excessive dependencies in the dependency array? Can cause stale closures or infinite loops

---

## ARCH — Architecture (3 checks)

- [ ] **ARCH1 — Business Logic in Component**: Calculations, validations, or data transformations inside the render function or JSX? Extract to custom hook or service module
- [ ] **ARCH2 — API Call in Render Path**: Fetch/axios call inside component body (not in useEffect or event handler)? Causes request on every render
- [ ] **ARCH3 — Prop Drilling > 3 Levels**: Props passed through 3+ intermediate components? Consider Context, composition, or state management

---

## STYLE — Styling (2 checks)

- [ ] **STYLE1 — Inline Styles Over Design Tokens**: Using inline `style={{}}` or hardcoded hex colors instead of design tokens, CSS variables, or Andes tokens?
- [ ] **STYLE2 — Non-Responsive Layout**: Fixed pixel widths, missing media queries, or layouts that break on mobile viewports?

---

## PLAT — Platform / Nordic / Andes / Fury (7 checks)

- [ ] **PLAT1 — Wrong Andes Component**: Using a raw HTML element or custom component where an Andes equivalent exists (e.g., `<input>` instead of `<TextField>`, `<button>` instead of `<Button>`)?
- [ ] **PLAT2 — Andes Props Misuse**: Andes component used with incorrect or deprecated props? Check Andes documentation for current API
- [ ] **PLAT3 — Missing Nordic Lifecycle**: Nordic page/component missing required lifecycle hooks (`getInitialProps`, `getServerSideProps`, or Nordic-specific data fetching)?
- [ ] **PLAT4 — Nordic SSR Compatibility**: Code using `window`, `document`, or browser-only APIs without SSR guards (`typeof window !== 'undefined'`)? Nordic renders on server first
- [ ] **PLAT5 — Incorrect Fury Config**: `.fury` file or deployment config with wrong node version, missing environment variables, or incorrect CDN paths?
- [ ] **PLAT6 — Missing Kraken Security Rules**: Frontend application without Kraken security scanning configuration or with disabled rules? Check `.krakenrc` or equivalent
- [ ] **PLAT7 — Missing Tracking/Analytics**: User interaction or page view without proper tracking calls (Melidata, custom events)? Required for all user-facing features

---

## File-Type to Checks Mapping

When reviewing a specific file, prioritize these checks:

| File Type | Priority Checks |
|-----------|----------------|
| `*.tsx` / `*.jsx` (Component) | PERF1, A11Y1-3, I18N1, QUAL5, ARCH1, PLAT1-2 |
| `*.tsx` / `*.jsx` (Page/Route) | PERF3, PLAT3-4, I18N1-2, ARCH2, QUAL5 |
| `*.ts` / `*.js` (Hook) | QUAL3, QUAL5, ARCH1, TEST1 |
| `*.ts` / `*.js` (Utility/Service) | SEC2-3, QUAL1-2, TEST1, ARCH1 |
| `*.css` / `*.scss` | STYLE1-2, PLAT1 |
| `*.test.*` / `*.spec.*` | TEST1-3 |
| `package.json` | PERF2, SEC4, PLAT5 |
| `i18n/**` / `translations/**` | I18N2-3 |
| Config files | PLAT5-6 |

---

## How to Use

1. For each frontend file in the diff, identify its type from the mapping above
2. Run the priority checks for that file type, then scan remaining checks
3. For each failing check, create a comment using `assets/comment.md`
4. Classify severity as described in `SKILL.md`
5. At the end of the file, compile a summary with count by severity
