---
name: review-frontend
description: >
  Knowledge baseline for frontend code review: templates, checklist,
  severity criteria and decision guidelines. Used by the review-frontend agent.
  Does NOT contain execution workflow — that is the agent's responsibility.
triggers:
  - review-frontend skill
  - frontend review templates
  - frontend severity criteria
  - react review checklist
  - nordic andes review
---

# Review-Frontend Skill

Knowledge base for frontend code review (JavaScript, TypeScript, React, CSS/SCSS).
Contains: comment templates, verification checklist, severity criteria and final decision guidelines.
Specialized in MercadoLibre's frontend ecosystem: Nordic, Andes, Fury Frontend, and i18n patterns.

**Does NOT contain**: execution workflow, bash/git commands, orchestration logic — that is the responsibility of the **review-frontend agent**.

---

## Communication Principles

- **Verifiability**: base analyses on real code extracted via `git diff`. Never invent problems that do not exist
- **Specificity**: cite file + line in each comment
- **Actionability**: each comment must include current code vs. suggested code + justification
- Use `[Inference]` for analyses that go beyond the visible diff
- Code and comments in **English**; discussions in **English**

---

## Skill Structure

### Assets (Templates)

| File | Purpose | When to Use |
|------|---------|-------------|
| `assets/comment.md` | Individual comment template | When generating each review comment |

### References (Documentation)

| File | Purpose | When to Use |
|------|---------|-------------|
| `references/checklist.md` | 34-check review checklist across 9 categories | During review of each file |

---

## Issue Categories

| Emoji | ID | Category | Examples |
|-------|----|----------|---------|
| :lock: | SEC | Security | XSS via `dangerouslySetInnerHTML`, unsanitized URL params, exposed API keys in client bundle |
| :zap: | PERF | Performance | Unnecessary re-renders, missing `useMemo`/`useCallback`, large bundle import, unoptimized images |
| :wheelchair: | A11Y | Accessibility | Missing `aria-*`, non-semantic HTML, missing `alt` on images, keyboard navigation broken |
| :globe_with_meridians: | I18N | Internationalization | Hardcoded strings, missing translation keys, locale-dependent formatting |
| :test_tube: | TEST | Testing | Missing component tests, snapshot-only tests, no user interaction tests |
| :gear: | QUAL | Code Quality | Any type, magic numbers, duplicated logic, confusing naming, dead code |
| :building_construction: | ARCH | Architecture | Business logic in component, API call in render, circular imports, prop drilling >3 levels |
| :art: | STYLE | Styling | Inline styles over design tokens, `!important` abuse, non-responsive layout, z-index wars |
| :package: | PLAT | Platform (Nordic/Andes/Fury) | Wrong Andes component usage, missing Nordic lifecycle hooks, incorrect Fury config |

---

## Severities

| Emoji | Severity | Criteria |
|-------|----------|---------|
| :red_circle: | Critical | Security vulnerabilities (XSS, exposed secrets), data loss, crash in production |
| :orange_circle: | High | Performance regression on critical path, accessibility violation blocking users, logic bug |
| :yellow_circle: | Medium | Best practice violations (missing memo, hardcoded strings, field injection), moderate risk |
| :green_circle: | Low | Improvement suggestions, naming, extraction of hooks, minor style issues |
| :information_source: | Info | Additional context, observations with no immediate impact |

---

## Final Decision Criteria

| Condition | Recommendation |
|-----------|---------------|
| 1+ :red_circle: Critical issues | :x: **Do Not Approve** — Merge blocked. Must fix |
| 0 Critical + 1+ :orange_circle: High | :warning: **Approve with Reservations** — Can merge, but fix before production |
| 0 Critical + 0 High | :white_check_mark: **Approve** — Only Medium, Low, Info |
| 0/few issues + high quality code | :tada: **Approve with Praise** |

---

## Review Checklist

See `references/checklist.md` for the complete checklist of 34 verifications across 9 categories.

### Checklist Categories

- **Security** (4 checks): XSS, exposed secrets, unsanitized URL params, insecure external resources
- **Performance** (4 checks): unnecessary re-renders, large bundle imports, missing code splitting, unoptimized assets
- **Accessibility** (3 checks): ARIA/semantic HTML, alt text, keyboard navigation
- **Internationalization** (3 checks): hardcoded strings, missing translation keys, locale-dependent formatting
- **Testing** (3 checks): component test coverage, snapshot-only tests, user interaction tests
- **Code Quality** (5 checks): any/unknown types, magic numbers, duplicated logic, dead code, effect dependencies
- **Architecture** (3 checks): business logic in component, API call in render, prop drilling
- **Styling** (2 checks): inline styles over design tokens, non-responsive layout
- **Platform** (7 checks): Andes component usage, Andes props, Nordic lifecycle, SSR compatibility, Fury config, Kraken rules, tracking/analytics

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

## Integration Note

This skill works in conjunction with the `arch-frontend` skill, which provides deeper architectural reference material for Nordic SSR, Andes Design System, Kraken auth, BFF Clean Architecture, and TypeScript patterns. The review-frontend agent should declare both `review-frontend` and `arch-frontend` as skills, matching the pattern of other review agents (e.g., `review-java` uses `review-java, arch-java`).
