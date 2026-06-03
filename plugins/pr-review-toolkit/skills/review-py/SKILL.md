---
name: review-py
description: |
  Knowledge baseline for Python code review: comment templates, verification checklist,
  severity criteria and decision guidelines. Used by the review-py agent as a reference for patterns and quality.
  Integrates with the arch-py skill to reference technical best practices.
  Use when: (1) You need comment templates, (2) Consulting the review checklist, (3) Classifying issue severity.
  Triggers: review-py skill, review templates, severity criteria.
---

# Review-Py Skill - Python Code Review Knowledge Base

## Purpose

This skill is a **knowledge library** for Python code review. It does NOT execute reviews,
but provides the patterns, templates, and criteria used by the **review-py agent** to conduct systematic reviews.

**Who uses this skill:**
- Agent `review-py` → consults templates, checklist, and criteria
- You directly → when you need a reference for structuring review feedback

**What this skill contains:**
- Comment templates by severity and category
- Verification checklist (what to review in each file)
- Severity classification criteria
- Final decision criteria (approve, block, approve with reservations)
- Examples of well-formatted comments

**What this skill does NOT contain:**
- Review execution workflow (that is in the review-py agent)
- Bash or git commands (those are executed by the agent)
- Orchestration logic (agent is responsible)

---

## Communication Pattern

### Communication Principles

**Verifiability and Transparency:**
- Base analyses on real code extracted via `git diff`
- Never invent problems that do not exist in the diff
- If you cannot verify something directly in the code, say so clearly
- Label inferences with `[Inference]` when applicable

**Objectivity:**
- Comments must be actionable and specific
- Always show current code vs suggested code
- Explain the "why" of the suggestion, not just the "what"

**Integration:**
- Reference the arch-py skill when applicable
- Cite specific lines and files
- Maintain feedback traceability

---

## Skill Structure

### Assets (Templates)

Markdown templates with placeholders to be filled in:

| File | Purpose | When to Use |
|------|---------|-------------|
| `assets/comment.md` | Individual comment template | When generating each review comment |
| `assets/summary.md` | Impact analysis template | When generating a change summary |
| `assets/report.md` | Complete report template | When generating the consolidated final report |

**How to use:**
1. Read the template with `view assets/{template}.md`
2. Identify the `{placeholder_name}` placeholders
3. Replace all placeholders with real values
4. Present the formatted final result

### References (Documentation)

Reference documentation for consultation:

| File | Purpose | When to Use |
|------|---------|-------------|
| `references/checklist.md` | Lean review checklist with pointers to arch-py | During review of each file |
| `references/templates.md` | Comment examples by issue type | When generating comments, for inspiration |
| `references/git.md` | Useful git commands and workflows | When specific git commands are needed |

### Scripts (Tools)

Auxiliary Python scripts (executed by the agent):

| Script | Purpose | Output |
|--------|---------|--------|
| `scripts/analyze_diff.py` | Automatic diff analysis, pattern detection | JSON with metrics, features, alerts |
| `scripts/format_output.py` | JSON formatting into markdown using templates | Formatted markdown file |

---

## Comment Templates

### Base Template

Use for detailed comments:

````markdown
**Lines:** {start_line}-{end_line}
**Category:** {emoji} {category}
**Severity:** {emoji} {severity}

**Issue:**
{clear and objective description of the problem in 1-2 sentences}

**Current Code:**
```python
{problematic code extracted from the diff}
```

**Suggested Code:**
```python
{corrected code}
```

**Justification:**
{technical explanation of why this is a problem}
{impact if not fixed}

**Reference:**
- Arch-Py Skill: [{file}](../arch-py/{path})
{other references if applicable}
````

### Categories and Emojis

Use these categories:
- 🔒 **Security** - Vulnerabilities, secrets, injections
- ⚡ **Performance** - N+1 queries, inefficient algorithms
- 🧪 **Testing** - Missing tests, weak assertions
- 📝 **Documentation** - Docstrings, comments
- ⚙️ **Code Quality** - Type hints, naming, complexity
- 🏗️ **Architecture** - SOLID, patterns, coupling

### Severities and Emojis

Use these severities:
- 🔴 **Critical** - Vulnerabilities, exposed secrets, data loss
- 🟠 **High** - Serious performance issues, serious bugs, missing critical tests
- 🟡 **Medium** - Code quality, type hints, naming
- 🟢 **Low** - Improvement suggestions
- ℹ️ **Info** - Additional context

---

## Review Checklist

For each Python file, check:

### 🔒 Security
- [ ] No hardcoded secrets
- [ ] External input validated
- [ ] SQL injection prevented
- [ ] Authentication/authorization correct
- [ ] Sensitive data not in logs

**Typical severity:** 🔴 Critical
**Reference:** `references/checklist.md` (complete)

### ⚡ Performance
- [ ] No N+1 queries
- [ ] Efficient algorithms
- [ ] Resources managed (context managers)

**Typical severity:** 🟠 High (hot path) / 🟡 Medium
**Reference:** `references/checklist.md`

### 🧪 Testing
- [ ] Critical code has tests
- [ ] Non-fragile tests
- [ ] Specific assertions

**Typical severity:** 🔴 Critical (no tests) / 🟠 High (<50% coverage)
**Reference:** `references/checklist.md`

### ⚙️ Code Quality
- [ ] Type hints present
- [ ] Adequate error handling
- [ ] Structured logging
- [ ] Docstrings on public APIs
- [ ] Descriptive naming
- [ ] Single Responsibility Principle
- [ ] DRY (no duplicated code)
- [ ] Reasonable cyclomatic complexity
- [ ] Organized imports

**Typical severity:** 🟡 Medium / 🟠 High (public APIs)
**Reference:** `references/checklist.md`

### 🏗️ Architecture
- [ ] Separation of concerns
- [ ] Dependency injection
- [ ] Versioned dependencies
- [ ] Async/await used correctly

**Typical severity:** 🟡 Medium / 🟠 High (serious violation)
**Reference:** `references/checklist.md`

**Complete checklist:** See `references/checklist.md` for all 25 detailed checks with pointers to the arch-py skill.

---

## Severity Criteria

### 🔴 Critical

**When to use:**
- Security vulnerabilities
- Hardcoded secrets
- SQL injection, XSS, injections
- Potential data loss
- Authentication/authorization bypass

**Characteristics:**
- Can cause system compromise
- Must block merge immediately
- Requires urgent fix

**Template:**
```markdown
**Required Action:** Blocks merge. Must be fixed immediately.

**Impact:**
- {serious consequence 1}
- {serious consequence 2}
```

### 🟠 High

**When to use:**
- Serious performance issues (N+1 queries in hot path)
- Bugs that affect core functionality
- Missing tests in critical code
- Memory leaks
- Inadequate error handling in critical operations

**Characteristics:**
- Impacts production if not fixed
- Should fix before merge or shortly after
- Creates significant technical debt

**Template:**
```markdown
**Required Action:** Must fix before merge.

**Impact:** {production impact if not fixed}
```

### 🟡 Medium

**When to use:**
- Missing type hints
- Non-descriptive naming
- Code quality issues
- High complexity
- Missing docstrings in important functions

**Characteristics:**
- Does not block merge
- Should fix soon
- Affects maintainability

**Template:**
```markdown
**Justification:**
{explanation of why this is important}

**Reference:**
- Arch-Py Skill: [{file}](../arch-py/{path})
```

### 🟢 Low

**When to use:**
- Minor optimizations
- Improvement suggestions
- Unused imports
- Formatting

**Characteristics:**
- Nice to have
- Can fix later
- Incremental improvement

### ℹ️ Info

**When to use:**
- Additional context
- FYI about alternative patterns
- Notes about behavior

**Characteristics:**
- No action required
- Informational only

---

## Final Decision Criteria

Use these criteria to determine the final review recommendation:

### ❌ Do Not Approve (Block Merge)

**Condition:** 1+ **Critical** issues present

**Examples:**
- Hardcoded secrets
- SQL injection
- Security vulnerabilities
- Potential data loss

**Action:** Merge must be blocked until fixed

**Template:**
```markdown
**Recommendation:** ❌ Do not approve

**Justification:** Found {n} Critical issues that must be fixed before merge:
- {issue 1}
- {issue 2}
```

### ⚠️ Approve with Reservations

**Condition:**
- 0 Critical issues
- 1+ **High** issues present

**Examples:**
- N+1 queries
- Missing tests in important code
- Serious performance issues
- Non-critical bugs

**Action:** Can merge, but must fix before production. Create tasks/tickets for fixes.

**Template:**
```markdown
**Recommendation:** ⚠️ Approve with reservations

**Justification:** Found {n} High issues that must be fixed before production:
- {issue 1}
- {issue 2}

Suggestion: create tasks for post-merge fixes.
```

### ✅ Approve

**Condition:**
- 0 Critical issues
- 0 High issues
- Only Medium, Low, and/or Info

**Action:** Can merge normally. Minor issues can be fixed later.

**Template:**
```markdown
**Recommendation:** ✅ Approve

**Justification:** No blocking issues found. Medium/Low issues can be addressed later as continuous improvement.
```

### 🎉 Approve with Praise

**Condition:**
- Few or zero issues (only Low/Info)
- High-quality code
- Good practices followed consistently

**Action:** Highlight the quality of the work

**Template:**
```markdown
**Recommendation:** 🎉 Approve with praise

**Justification:** Excellent quality code. Patterns followed consistently. Few minor issues identified.

**Highlights:**
- {highlight 1}
- {highlight 2}
```

---

## Integration with Arch-Py Skill

Whenever you identify a violation of a Python pattern, reference the arch-py skill:

### Reference Examples

**Missing type hints:**
```markdown
**Reference:**
- Arch-Py Skill: [references/python/type-system.md](../arch-py/references/python/type-system.md)
```

**Inadequate error handling:**
```markdown
**Reference:**
- Arch-Py Skill: [references/python/error-handling.md](../arch-py/references/python/error-handling.md)
```

**Incorrectly used async:**
```markdown
**Reference:**
- Arch-Py Skill: [references/python/async-patterns.md](../arch-py/references/python/async-patterns.md)
```

**Wrong Pydantic patterns:**
```markdown
**Reference:**
- Arch-Py Skill: [references/python/pydantic.md](../arch-py/references/python/pydantic.md)
```

**Missing tests:**
```markdown
**Reference:**
- Arch-Py Skill: [references/testing/pytest.md](../arch-py/references/testing/pytest.md)
```

**Coupled architecture:**
```markdown
**Reference:**
- Arch-Py Skill: [references/architecture/clean-architecture.md](../arch-py/references/architecture/clean-architecture.md)
```

---

## Skill File Structure

```
review-py/
├── SKILL.md                          (this file - declarative knowledge)
├── references/
│   ├── checklist.md                 (complete checklist with 25 checks)
│   ├── templates.md                 (comment examples by issue type)
│   └── git.md                       (useful git commands)
├── scripts/
│   ├── analyze_diff.py              (git diff parser + pattern detection)
│   └── format_output.py             (markdown output formatter)
└── assets/
    ├── comment.md                   (individual comment template)
    ├── summary.md                   (impact analysis template)
    └── report.md                    (complete report template)
```

---

## Quick Guide: When to Consult Each File

### For the Review-Py Agent

| Moment | File | What to consult |
|--------|------|----------------|
| Generating individual comment | `assets/comment.md` | Base template with placeholders |
| Generating impact analysis | `assets/summary.md` | Summary template |
| Generating complete report | `assets/report.md` | Report template |
| Reviewing Python file | `references/checklist.md` | List of 25 checks to perform |
| Needing examples | `references/templates.md` | Ready-made comments by type |
| Needing git command | `references/git.md` | Useful git commands |

### For Direct Use

If you are doing a review manually:
1. Use `references/checklist.md` as a guide for what to check
2. Consult `references/templates.md` to see examples of well-formatted comments
3. Use the severity criteria in this skill to classify issues
4. Use the final decision criteria to determine whether to approve or block

---

## References

### Files in this Skill
- [references/checklist.md](references/checklist.md) - Complete review checklist (25 checks)
- [references/templates.md](references/templates.md) - Templates and comment examples by issue type
- [references/git.md](references/git.md) - Git commands and workflows

### Assets (Templates)
- [assets/comment.md](assets/comment.md) - Individual comment template
- [assets/summary.md](assets/summary.md) - Impact analysis template
- [assets/report.md](assets/report.md) - Complete report template

### Scripts
- [scripts/analyze_diff.py](scripts/analyze_diff.py) - Automatic diff analysis
- [scripts/format_output.py](scripts/format_output.py) - Output formatting

### Arch-Py Skill (Python Technical Standards)
- [../arch-py/SKILL.md](../arch-py/SKILL.md) - Main Arch-Py skill
- [../arch-py/references/python/](../arch-py/references/python/) - Python patterns (type system, async, Pydantic, error handling, etc.)
- [../arch-py/references/testing/](../arch-py/references/testing/) - Testing patterns (pytest, fixtures, mocking)
- [../arch-py/references/architecture/](../arch-py/references/architecture/) - Architecture (clean architecture, DI, repository pattern)

### Generated Output (by Agent)
- `review-output.md` - Final file saved at project root (copy-paste ready for PRs)
