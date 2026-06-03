---
name: review-go
description: >
  Knowledge baseline for Go code review: templates, checklist,
  severity criteria and decision guidelines. Used by the review-go agent.
  Does NOT contain execution workflow — that is the agent's responsibility.
triggers:
  - review-go skill
  - go review templates
  - go severity criteria
---

# Review-Go Skill

Knowledge base for code review of Go projects.
Contains: comment templates, verification checklist, severity criteria and final decision guidelines.

**Does NOT contain**: execution workflow, bash/git commands, orchestration logic — that is the responsibility of the **review-go agent**.

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
| `references/checklist.md` | Lean Go review checklist | During review of each file |

---

## Issue Categories

| Emoji | Category | Examples |
|-------|----------|---------|
| S | Security | SQL injection, exposed secrets, unsanitized input, path traversal |
| P | Performance | N+1 queries, unnecessary allocation in loop, goroutine leak, missing preallocate |
| T | Testing | Missing tests, incorrect mock, no table-driven tests, missing -race |
| D | Documentation | Missing Godoc on exports, outdated comments |
| Q | Code Quality | Ignored error, non-idiomatic naming, bloated interface, panic in lib |
| A | Architecture | Repository in handler, domain coupled to infrastructure, circular import |
| C | Concurrency | Data race, goroutine leak, copied mutex, misused channel |
| E | Error Handling | Error without wrap, direct comparison instead of errors.Is, log+return |

---

## Severities

| Emoji | Severity | Criteria |
|-------|----------|---------|
| CRIT | Critical | Security vulnerabilities, data race in production, guaranteed goroutine leak |
| HIGH | High | Ignored error in critical flow, missing tests on core logic, N+1 query |
| MED | Medium | Go idiom violations (naming, error handling), bloated interface, missing context |
| LOW | Low | Improvement suggestions, naming, function extraction |
| INFO | Info | Additional context, observations with no immediate impact |

---

## Final Decision Criteria

| Condition | Recommendation |
|-----------|---------------|
| 1+ Critical issues | Do NOT Approve — Merge blocked. Must fix |
| 0 Critical + 1+ High | Approve with Reservations — Can merge, but fix before production |
| 0 Critical + 0 High | Approve — Only Medium, Low, Info |
| 0/few issues + high quality code | Approve with Praise |

---

## Review Checklist

See `references/checklist.md` for the complete verification checklist.

### Checklist Categories

- **Error Handling** (5 checks): ignored error, missing wrap, direct comparison, log+return, panic in lib
- **Concurrency** (4 checks): goroutine leak, data race, copied mutex, channel without close
- **Security** (4 checks): injection, secrets, input validation, path traversal
- **Performance** (3 checks): preallocate, goroutine leak, allocation in loop
- **Testing** (3 checks): coverage, table-driven, race flag
- **Code Quality** (5 checks): naming, interfaces, context, init(), logging
- **Architecture** (3 checks): layer separation, circular import, DI

---

## Integration with Arch-Go Skill

For each identified issue, reference the corresponding technical documentation in the `arch-go` skill:

| Category | Arch-Go Reference |
|----------|-------------------|
| Error handling | `arch-go/references/go/error-handling.md` |
| Naming / Idioms | `arch-go/references/go/idioms.md` |
| Concurrency | `arch-go/references/concurrency/goroutines-channels.md` |
| HTTP patterns | `arch-go/references/http/http-patterns.md` |
| Testing | `arch-go/references/testing/testing-patterns.md` |
| Architecture | `arch-go/references/architecture/project-structure.md` |
