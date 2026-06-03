---
name: review-java
description: >
  Knowledge baseline for Java/Spring Boot code review: templates, checklist,
  severity criteria and decision guidelines. Used by the review-java agent.
  Does NOT contain execution workflow — that is the agent's responsibility.
triggers:
  - review-java skill
  - java review templates
  - java severity criteria
---

# Review-Java Skill

Knowledge base for Java/Spring Boot code review.
Contains: comment templates, verification checklist, severity criteria and final decision guidelines.

**Does NOT contain**: execution workflow, bash/git commands, orchestration logic — that is the responsibility of the **review-java agent**.

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
| `assets/summary.md` | Impact analysis template | When generating a summary of changes |
| `assets/report.md` | Full report template | When generating the consolidated final report |

### References (Documentation)

| File | Purpose | When to Use |
|------|---------|-------------|
| `references/checklist.md` | Lean review checklist | During review of each file |
| `references/templates.md` | Comment examples by type | When generating comments |

---

## Issue Categories

| Emoji | Category | Examples |
|-------|----------|---------|
| 🔒 | Security | SQL injection, insecure deserialization, exposed secrets, missing authorization |
| ⚡ | Performance | N+1 queries, FetchType.EAGER, queries without index, loops in database calls |
| 🧪 | Testing | Missing tests, incorrect mocks, tests without assertions |
| 📝 | Documentation | Missing Javadoc, missing @param/@return on public methods |
| ⚙️ | Code Quality | Raw types, null without Optional, swallowed exception, confusing naming |
| 🏗️ | Architecture | Repository in Controller, Entity exposed in API, logic in Controller |
| 🌿 | Spring Patterns | Field injection, missing @Transactional, wrong scope |
| 💾 | JPA/Data | FetchType.EAGER, missing @Transactional, unresolved N+1 |

---

## Severities

| Emoji | Severity | Criteria |
|-------|----------|---------|
| 🔴 | Critical | Security vulnerabilities, data loss, guaranteed NullPointerException in production |
| 🟠 | High | N+1 query on critical endpoint, logic bug, missing tests on critical flow |
| 🟡 | Medium | Best practice violations (field injection, missing Optional, FetchType.EAGER) |
| 🟢 | Low | Improvement suggestions, naming, method extraction |
| ℹ️ | Info | Additional context, observations with no immediate impact |

---

## Final Decision Criteria

| Condition | Recommendation |
|-----------|---------------|
| 1+ 🔴 Critical issues | ❌ **Do Not Approve** — Merge blocked. Must fix |
| 0 Critical + 1+ 🟠 High | ⚠️ **Approve with Reservations** — Can merge, but fix before production |
| 0 Critical + 0 High | ✅ **Approve** — Only Medium, Low, Info |
| 0/few issues + high quality code | 🎉 **Approve with Praise** |

---

## Review Checklist

See `references/checklist.md` for the complete checklist of 25 verifications.

### Checklist Categories

- **Security** (5 checks): injection, deserialization, secrets, authorization, PII
- **Performance** (4 checks): N+1, FetchType.EAGER, indexes, lazy loading
- **Testing** (3 checks): coverage, correct mocks, edge cases
- **Code Quality** (7 checks): Optional/null, exceptions, generics, naming, SRP, records, logging
- **Spring Patterns** (4 checks): DI, @Transactional, scope, profile
- **Architecture** (2 checks): layer separation, entity vs DTO

---

## Integration with Arch-Java Skill

For each identified issue, reference the corresponding technical documentation in the `arch-java` skill:

| Category | Arch-Java Reference |
|----------|---------------------|
| Null / Optional | `arch-java/references/java/modern-java.md` |
| Exception handling | `arch-java/references/java/error-handling.md` |
| Concurrency | `arch-java/references/java/concurrency.md` |
| REST API patterns | `arch-java/references/spring/rest-api.md` |
| JPA / N+1 | `arch-java/references/spring/data-jpa.md` |
| Unit tests | `arch-java/references/testing/junit5-mockito.md` |
| Integration tests | `arch-java/references/testing/spring-boot-test.md` |
| Layer architecture | `arch-java/references/architecture/layers.md` |
