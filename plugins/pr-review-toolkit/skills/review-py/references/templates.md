# Comment Templates

Comment templates for code review. Use these templates when generating comments, filling in the indicated placeholders.

---

## Base Template (Complete)

Use this template for detailed comments:
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

---

## Templates by Severity

### 🔴 Critical
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 🔒 Security
**Severity:** 🔴 Critical

**Issue:**
{description of the critical problem}

**Current Code:**
```python
{problematic code}
```

**Suggested Code:**
```python
{corrected code}
```

**Justification:**
This is a critical problem that may cause {serious impact}.
{detailed technical explanation}

**Impact:**
- {consequence 1}
- {consequence 2}
- {consequence 3}

**Required Action:** Blocks merge. Must be fixed immediately.

**Reference:**
- Arch-Py Skill: [{file}](../arch-py/{path})
````

---

### 🟠 High
````markdown
**Lines:** {start_line}-{end_line}
**Category:** {emoji} {category}
**Severity:** 🟠 High

**Issue:**
{description of the problem}

**Current Code:**
```python
{problematic code}
```

**Suggested Code:**
```python
{corrected code}
```

**Justification:**
{explanation of the problem and impact}

**Impact:** {production impact if not fixed}

**Required Action:** Must fix before merge.

**Reference:**
- Arch-Py Skill: [{file}](../arch-py/{path})
````

---

### 🟡 Medium
````markdown
**Lines:** {start_line}-{end_line}
**Category:** {emoji} {category}
**Severity:** 🟡 Medium

**Issue:**
{description of the problem}

**Current Code:**
```python
{problematic code}
```

**Suggested Code:**
```python
{corrected code}
```

**Justification:**
{explanation of why this is important}

**Reference:**
- Arch-Py Skill: [{file}](../arch-py/{path})
````

---

### 🟢 Low
````markdown
**Lines:** {start_line}-{end_line}
**Category:** {emoji} {category}
**Severity:** 🟢 Low

**Issue:**
{improvement suggestion}

**Current Code:**
```python
{current code}
```

**Suggestion:**
```python
{improved code}
```

**Benefit:** {small improvement it brings}
````

---

### ℹ️ Info
````markdown
**Lines:** {start_line}-{end_line}
**Category:** ℹ️ Info

**Note:**
{useful information or additional context}

**Context:**
{explanation or alternative}

**Reference:** {if applicable}
````

---

## Templates by Category

### 🔒 Security - Secret Hardcoded
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 🔒 Security
**Severity:** 🔴 Critical

**Issue:**
Secret key hardcoded in the code. Credentials must never be in the source code.

**Current Code:**
```python
{code with hardcoded secret}
```

**Suggested Code:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    {secret_field_name}: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**Justification:**
- Secrets in code leak via Git history
- Makes credential rotation difficult
- Violates OWASP A02:2021 - Cryptographic Failures
- Anyone with access to the repository has access

**Impact:** Total system compromise if credentials leak.

**Required Action:** Blocks merge. Fix immediately and rotate credentials.

**Reference:**
- Arch-Py Skill: [references/python/configuration.md](../arch-py/references/python/configuration.md)
- OWASP: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
````

---

### 🔒 Security - SQL Injection
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 🔒 Security
**Severity:** 🔴 Critical

**Issue:**
SQL Injection vulnerability. Query is being built by string concatenation.

**Current Code:**
```python
{code with SQL injection}
```

**Suggested Code:**
```python
# Option 1: Parameterized query
query = "SELECT * FROM users WHERE email = :email"
result = db.execute(query, {"email": user_email})

# Option 2: ORM (preferred)
user = db.query(User).filter_by(email=user_email).first()
```

**Justification:**
Attacker can inject arbitrary SQL and:
- Read sensitive data from any table
- Modify or delete data
- Escalate privileges
- Execute commands on the server

**Impact:** Total database compromise.

**Required Action:** Blocks merge. Fix immediately.

**Reference:**
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
````

---

### 🔒 Security - Input Validation
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 🔒 Security
**Severity:** 🟠 High

**Issue:**
External input not validated. Data from external sources must always be validated.

**Current Code:**
```python
{code that blindly trusts input}
```

**Suggested Code:**
```python
from pydantic import BaseModel, field_validator

class {ModelName}(BaseModel):
    {field_name}: {field_type}

    @field_validator("{field_name}")
    @classmethod
    def validate_{field_name}(cls, v: {field_type}) -> {field_type}:
        # custom validation
        if not {condition}:
            raise ValueError("{error_message}")
        return v
```

**Justification:**
Without validation, invalid data can:
- Cause unhandled errors
- Bypass business rules
- Data corruption in the database

**Required Action:** Fix before merge.

**Reference:**
- Arch-Py Skill: [references/python/pydantic.md](../arch-py/references/python/pydantic.md)
````

---

### ⚡ Performance - N+1 Query
````markdown
**Lines:** {start_line}-{end_line}
**Category:** ⚡ Performance
**Severity:** 🟠 High

**Issue:**
N+1 query detected. Loop executing a query on each iteration.

**Current Code:**
```python
{code with N+1}
```

**Suggested Code:**
```python
# SQLAlchemy - Eager loading
from sqlalchemy.orm import joinedload

{objects} = db.query({Model}).options(
    joinedload({Model}.{relationship})
).all()

# Now {relationship} is already loaded
for obj in {objects}:
    # uses obj.{relationship} without additional query
    pass
```

**Justification:**
Performance degrades linearly with the number of records.
- 10 records = 11 queries
- 100 records = 101 queries
- 1000 records = 1001 queries

**Impact:**
- Significant slowdown
- Timeouts in production
- Unnecessary load on the database

**Required Action:** Fix before merge.

**Reference:**
- SQLAlchemy Relationship Loading: https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html
````

---

### ⚡ Code Quality - Type Hints Missing
````markdown
**Lines:** {start_line}-{end_line}
**Category:** ⚡ Code Quality
**Severity:** 🟡 Medium

**Issue:**
Type hints missing in function/method.

**Current Code:**
```python
{code without type hints}
```

**Suggested Code:**
```python
{code with type hints}
```

**Justification:**
Type hints improve:
- Type safety (error detection at development time)
- IDE autocomplete
- Inline documentation
- Safer refactoring

**Reference:**
- Arch-Py Skill: [references/python/type-system.md](../arch-py/references/python/type-system.md)
````

---

### ⚡ Code Quality - Error Handling
````markdown
**Lines:** {start_line}-{end_line}
**Category:** ⚡ Code Quality
**Severity:** {🔴 Critical / 🟠 High / 🟡 Medium}

**Issue:**
{description of the error handling problem}

**Current Code:**
```python
{code without adequate handling}
```

**Suggested Code:**
```python
try:
    {operation}
except {SpecificException} as e:
    logger.error(f"{context}: {e}")
    {appropriate handling}
    raise  # or raise CustomException() from e
```

**Justification:**
{explanation of why it is important to handle this error}

**Impact:** {consequence of not handling}

**Reference:**
- Arch-Py Skill: [references/python/error-handling.md](../arch-py/references/python/error-handling.md)
````

---

### ⚡ Code Quality - Logging Missing
````markdown
**Lines:** {start_line}-{end_line}
**Category:** ⚡ Code Quality
**Severity:** 🟠 High

**Issue:**
Missing logging in critical operation.

**Current Code:**
```python
{code without logging}
```

**Suggested Code:**
```python
import structlog

logger = structlog.get_logger()

def {function_name}({params}):
    log = logger.bind({context_fields})
    log.info("{operation}_started")

    try:
        {operation}
        log.info("{operation}_completed", {result_fields})
    except Exception as e:
        log.error("{operation}_failed", error=str(e))
        raise
```

**Justification:**
Logs are essential for:
- Debugging problems in production
- Auditing critical operations
- Monitoring and alerts
- Request tracing

**Reference:**
- Arch-Py Skill: [references/python/logging.md](../arch-py/references/python/logging.md)
````

---

### 🧪 Testing - Missing Tests
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 🧪 Testing
**Severity:** {🔴 Critical / 🟠 High}

**Issue:**
{Critical code / New functionality} without corresponding tests.

**Test Suggestion:**
```python
import pytest

def test_{function_name}_success():
    # Arrange
    {setup}

    # Act
    result = {function_name}({params})

    # Assert
    assert {expected_outcome}

def test_{function_name}_error_case():
    with pytest.raises({ExpectedException}):
        {function_name}({invalid_params})

@pytest.mark.parametrize("input,expected", [
    ({case_1}),
    ({case_2}),
    ({case_3}),
])
def test_{function_name}_multiple_cases(input, expected):
    assert {function_name}(input) == expected
```

**Justification:**
{Why this code needs tests}

**Expected Coverage:** {X}% for this module

**Reference:**
- Arch-Py Skill: [references/testing/pytest.md](../arch-py/references/testing/pytest.md)
````

---

### 📝 Documentation - Missing Docstring
````markdown
**Lines:** {start_line}-{end_line}
**Category:** 📝 Documentation
**Severity:** 🟠 High

**Issue:**
Public/complex function without docstring.

**Current Code:**
```python
{code without docstring}
```

**Suggested Code:**
```python
def {function_name}({params}) -> {return_type}:
    """
    {Brief description of what the function does in one line}

    {More detailed description if needed, explaining complex logic,
    edge cases, or important considerations}

    Args:
        {param_name}: {parameter description}
        {param_name}: {parameter description}

    Returns:
        {return description}

    Raises:
        {Exception}: {when it is raised}

    Example:
        >>> {usage example}
        {expected result}
    """
    {code}
```

**Justification:**
Public APIs and complex functions need documentation to:
- Help other developers know how to use it
- Prevent incorrect use
- Facilitate future maintenance

**Reference:**
- PEP 257: https://peps.python.org/pep-0257/
````

---

## Positive Points Template

Always use at the end of each file review:
````markdown
### ✅ Positive Points

1. ✨ {well-implemented aspect}
2. ✨ {good practice followed}
3. ✨ {highlighted quality}
````

**Concrete examples:**
````markdown
### ✅ Positive Points

1. ✨ Complete and correct type hints in all functions
2. ✨ Robust error handling with specific exceptions
3. ✨ Tests with good coverage (87%) including edge cases
4. ✨ Structured logging with adequate context
5. ✨ Well-organized code following Single Responsibility Principle
````

---

## Per-File Summary Template
````markdown
### 📊 Summary: `{path/file.py}`

| Category | Count | Max Severity |
|----------|-------|--------------|
| 🔒 Security | {n} | {max_severity} |
| ⚡ Performance | {n} | {max_severity} |
| 🧪 Testing | {n} | {max_severity} |
| ⚡ Code Quality | {n} | {max_severity} |
| 📝 Documentation | {n} | {max_severity} |
| **Total** | **{total}** | **{overall_max}** |

**Recommendation:** {✅ Approve / ⚠️ Approve with reservations / ❌ Do not approve}

**Justification:** {concise reason for the recommendation}
````

---

## Simple Issue Template (One-liner)

For very simple issues, use compact format:
````markdown
**L{line_num}** - {emoji} {severity} - {issue_description} → Suggestion: {quick_fix}
Ref: [Arch-Py - {topic}](../arch-py/references/{path})
````

**Example:**
````markdown
**L42** - 🟢 Low - Unused variable `count` → Remove or use in calculation
Ref: [Arch-Py - Code Quality](../arch-py/references/python/best-practices.md)
````

---

## Common Placeholders

**Severities:**
- `🔴 Critical`
- `🟠 High`
- `🟡 Medium`
- `🟢 Low`
- `ℹ️ Info`

**Categories:**
- `🔒 Security`
- `⚡ Performance`
- `🧪 Testing`
- `📝 Documentation`
- `⚡ Code Quality`
- `🏗️ Architecture`

**Result Emojis:**
- `✅` - Approve
- `⚠️` - Approve with reservations
- `❌` - Do not approve
- `🎉` - Approve with praise
- `✨` - Positive point
- `🚫` - Block

---

## Usage Notes

**Template selection:**
1. Use full template for complex issues
2. Use severity template for standard issues
3. Use category template for known specific issues
4. Use one-liner template for trivial issues

**Customization:**
- Always adapt the template to context
- Add specific details about the code in question
- Be specific about affected lines
- Cite the arch-py skill when applicable

**Bitbucket Format:**
- Standard Markdown works
- Code blocks with ```python work
- Internal links work
- Emojis work
