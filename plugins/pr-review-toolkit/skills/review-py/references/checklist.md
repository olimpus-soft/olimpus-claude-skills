# Code Review Checklist

Code review checklist for Python. Each item points to the arch-py skill that contains the complete patterns and examples.

---

## How to Use

**For each modified Python file:**

1. Go through the categories below sequentially
2. For each check, consult the reference in the arch-py skill
3. Mark [x] when item is checked
4. If a violation is found, generate a comment citing:
   - The violated check
   - Typical severity
   - Reference from the arch-py skill

**Severity is indicative.** Use good judgement based on context.

---

## 🔒 Security

### [ ] 1. Secrets and Configuration
**Check:**
- No hardcoded API keys, tokens, or passwords
- Configurations come from environment variables
- Use of pydantic-settings or similar

**Typical severity:** 🔴 Critical
**Reference:** [Arch-Py - Configuration](../../arch-py/references/python/configuration.md)

---

### [ ] 2. External Input Validation
**Check:**
- Data from APIs, requests, and files is validated
- Use of Pydantic for schemas
- Required fields, types, and custom validations

**Typical severity:** 🟠 High
**Reference:** [Arch-Py - Pydantic](../../arch-py/references/python/pydantic.md)

---

### [ ] 3. SQL Injection Prevention
**Check:**
- Parameterized queries (not string concatenation)
- Use of ORM or prepared queries
- No f-strings in SQL

**Typical severity:** 🔴 Critical
**Reference:** OWASP SQL Injection + ORM best practices

---

### [ ] 4. Authentication and Authorization
**Check:**
- Endpoints protected when necessary
- Ownership/permissions verification
- Adequate token validation

**Typical severity:** 🔴 Critical (public endpoints) / 🟠 High (internal)
**Reference:** [Arch-Py - FastAPI Best Practices](../../arch-py/references/fastapi/best-practices.md)

---

### [ ] 5. Sensitive Data in Logs
**Check:**
- No passwords, tokens, or PII in logs
- Structured logging without exposing sensitive data
- Request/response bodies sanitized

**Typical severity:** 🔴 Critical
**Reference:** [Arch-Py - Logging](../../arch-py/references/python/logging.md)

---

## ⚡ Performance

### [ ] 6. N+1 Queries
**Check:**
- No loops with queries inside
- Eager loading of relationships
- Joins instead of multiple queries

**Typical severity:** 🟠 High
**Reference:** ORM documentation (SQLAlchemy, Django ORM)

---

### [ ] 7. Efficient Algorithms
**Check:**
- Algorithmic complexity (avoid O(n²) or worse)
- Appropriate data structures
- Costly operations outside loops

**Typical severity:** 🟡 Medium / 🟠 High (if on hot path)
**Reference:** Basic algorithms and data structures

---

### [ ] 8. Resource Management
**Check:**
- Context managers for files, connections, locks
- No memory leaks (limited caches, cleaned references)
- Resources released appropriately

**Typical severity:** 🔴 Critical (confirmed leaks) / 🟠 High (suspected)
**Reference:** [Arch-Py - Context Managers](../../arch-py/references/python/context-managers.md)

---

## 🧪 Testing

### [ ] 9. Test Coverage
**Check:**
- Critical code has tests (auth, payment, data)
- New endpoints/features have tests
- Coverage >60% (general), >80% (core), 100% (critical)

**Typical severity:** 🔴 Critical (critical code without tests) / 🟠 High (coverage <50%)
**Reference:** [Arch-Py - Pytest](../../arch-py/references/testing/pytest.md)

---

### [ ] 10. Test Quality
**Check:**
- Non-fragile tests (no sleep, no hardcoded IDs/timestamps)
- Edge cases tested
- Specific and clear assertions

**Typical severity:** 🟡 Medium
**Reference:** [Arch-Py - Testing Best Practices](../../arch-py/references/testing/pytest.md)

---

## ⚡ Code Quality

### [ ] 11. Type Hints
**Check:**
- Function parameters typed
- Function returns typed
- Complex variables typed
- Use modern types (list[str] not List[str])

**Typical severity:** 🟡 Medium (private functions) / 🟠 High (public APIs)
**Reference:** [Arch-Py - Type System](../../arch-py/references/python/type-system.md)

---

### [ ] 12. Error Handling
**Check:**
- Try/except on operations that can fail
- Specific exceptions (not generic Exception)
- Errors logged appropriately
- Cleanup in finally or context managers

**Typical severity:** 🔴 Critical (critical operations) / 🟠 High (APIs) / 🟡 Medium (general)
**Reference:** [Arch-Py - Error Handling](../../arch-py/references/python/error-handling.md)

---

### [ ] 13. Structured Logging
**Check:**
- Logs on critical operations
- Context included (user_id, request_id, order_id)
- Appropriate levels (info/warning/error)
- Structured logging (JSON) preferred

**Typical severity:** 🟠 High (APIs and services) / 🟡 Medium (internal code)
**Reference:** [Arch-Py - Logging](../../arch-py/references/python/logging.md)

---

### [ ] 14. Docstrings
**Check:**
- Public APIs documented
- Complex functions explained
- Parameters and returns described
- Examples when necessary

**Typical severity:** 🟠 High (public APIs) / 🟡 Medium (complex) / 🟢 Low (simple)
**Reference:** PEP 257 - Docstring Conventions

---

### [ ] 15. Naming
**Check:**
- Names reveal intent
- Conventions followed (snake_case functions, PascalCase classes)
- No obscure abbreviations
- Consistency within the module

**Typical severity:** 🟡 Medium (variables) / 🟠 High (public APIs)
**Reference:** PEP 8 - Style Guide

---

### [ ] 16. Single Responsibility Principle
**Check:**
- Function does one thing only
- <20-30 lines ideally
- Can be tested in isolation
- Name does not contain "and" (process_AND_send_AND_update)

**Typical severity:** 🟡 Medium / 🟠 High (if very complex)
**Reference:** [Arch-Py - Clean Architecture](../../arch-py/references/architecture/clean-architecture.md)

---

### [ ] 17. DRY (Don't Repeat Yourself)
**Check:**
- No duplicated code
- Repeated logic extracted into functions
- Patterns identified and abstracted

**Typical severity:** 🟡 Medium
**Reference:** DRY principle

---

### [ ] 18. Cyclomatic Complexity
**Check:**
- Reasonable decision points (<10 ideal, <15 acceptable)
- Nested ifs/loops minimized
- Function can be broken up if too complex

**Typical severity:** 🟡 Medium (>10) / 🟠 High (>15)
**Tool:** `radon cc --min C`

---

### [ ] 19. Organized Imports
**Check:**
- Order: stdlib → third-party → local
- No unused imports
- No star imports
- One import per line

**Typical severity:** 🟢 Low
**Tool:** `ruff check --select I` or `isort`

---

## 🏗️ Architecture

### [ ] 20. Separation of Concerns
**Check:**
- Models do not contain business logic
- Controllers/endpoints are thin
- Services contain logic
- Repositories isolate data access

**Typical severity:** 🟡 Medium / 🟠 High (serious violation)
**Reference:** [Arch-Py - Clean Architecture](../../arch-py/references/architecture/clean-architecture.md)

---

### [ ] 21. Dependency Injection
**Check:**
- Dependencies injected, not directly imported
- Facilitates testing with mocks
- Configurations come from outside

**Typical severity:** 🟡 Medium
**Reference:** [Arch-Py - Dependency Injection](../../arch-py/references/architecture/dependency-injection.md)

---

## 🔧 Configuration & Dependencies

### [ ] 22. Versioned Dependencies
**Check:**
- Pinned versions (requirements.txt or poetry.lock)
- Does not use very wide ranges
- Dev dependencies separated

**Typical severity:** 🟠 High (production) / 🟡 Medium (dev)
**Reference:** [Arch-Py - Packaging](../../arch-py/references/python/packaging.md)

---

### [ ] 23. Async/Await Used Correctly
**Check:**
- I/O-bound operations use async
- Does not block the event loop
- Await on async operations

**Typical severity:** 🟠 High (if blocking event loop) / 🟡 Medium (performance)
**Reference:** [Arch-Py - Async Patterns](../../arch-py/references/python/async-patterns.md)

---

## 📝 Documentation

### [ ] 24. Updated README
**Check:**
- Setup instructions reflect changes
- New dependencies documented
- New endpoints/features described

**Typical severity:** 🟡 Medium (new projects) / 🟢 Low (established)

---

### [ ] 25. Updated CHANGELOG
**Check:**
- Breaking changes documented
- New features listed
- Consistent format

**Typical severity:** 🟢 Low

---

## Quick Summary

**Review priority order:**

1. **Security** (checks 1-5) → Maximum priority
2. **Performance** (checks 6-8) → Look for serious problems
3. **Testing** (checks 9-10) → Coverage and quality
4. **Code Quality** (checks 11-19) → Conformance with arch-py skill
5. **Architecture** (checks 20-21) → Code structure
6. **Config/Deps** (checks 22-23) → Configurations
7. **Documentation** (checks 24-25) → Updated docs

---

## Supporting Tools

Some checks can be automated:
```bash
# Type checking
mypy src/

# Linting
ruff check .

# Formatting
black --check .

# Security
bandit -r src/

# Complexity
radon cc src/ --min C

# Coverage
pytest --cov=src --cov-report=term-missing

# Imports
ruff check --select I
```

**Complete reference:** [Arch-Py - Tooling](../../arch-py/references/tooling/setup.md)

---

## Important Notes

**This checklist is a guide, not a rigid rule:**
- Use good judgement based on project context
- Severities are indicative, not absolute
- Always consult the arch-py skill for detailed patterns
- Adapt to context (startup vs enterprise, prototype vs production)

**For the final approval decision:**
Consult the "Final Decision" section in the review-py main SKILL.md.
