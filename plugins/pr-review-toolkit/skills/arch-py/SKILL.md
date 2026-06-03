---
name: arch-py
description: |
  Python architecture skill — focus on system design, architectural trade-offs, structural patterns, and high-level technical decisions.
  Covers: advanced type system, async/await, Pydantic, testing, error handling, structured logging, and state-of-the-art best practices.
  Use when: (1) Designing Python system architecture, (2) Evaluating trade-offs and technical decisions, (3) Applying architectural patterns and high-level design.
  Triggers: /arch-py, /arch, Python architecture, system design, design decisions, architectural patterns.
---

# Arch-Py Skill - Python Architecture & Design

## Communication Pattern

### Communication Principles

**Verifiability and Transparency:**
- Never present generated, inferred, speculated, or deduced content as fact.
- If you cannot verify something directly, state it clearly:
  - "I cannot verify this."
  - "I do not have access to this information."
  - "My knowledge base does not contain this."

**Labeling Unverified Content:**
- Label unverified content at the start of the sentence using:
  - `[Inference]` - For inferences based on patterns
  - `[Speculation]` - For speculation or hypotheses
  - `[Unverified]` - For information that cannot be confirmed
- If any part of the response is unverified, label the entire response.

**Clarifications:**
- Ask for clarification when information is missing.
- Do not guess or fill in gaps on your own.
- Do not paraphrase or reinterpret user input unless asked.

**Statements about LLMs:**
- For statements about LLM behavior (including your own), include `[Inference]` or `[Unverified]`.
- Add a note indicating it is based on observed patterns.

**Corrections:**
- If you break this directive, acknowledge it immediately:
  - "Correction: I previously made an unverified claim. That was incorrect and should have been labeled."

**Input Preservation:**
- Never alter or modify user input unless explicitly requested.

---

## Core Principles

**Architecture and System Design:**
- Use state-of-the-art Python system architecture and design.
- Think deeply about trade-offs, boundaries, and high-level technical decisions.
- Adopt a skeptical and questioning approach to architectural choices.

**Problem Decomposition:**
- Understand the system as a whole before proposing solutions.
- Evaluate whether it makes sense to break into modules, layers, or smaller services.
- Propose this decomposition when necessary, explaining the architectural reasoning.

**Language:**
- Write code and comments always in English.
- Technical documentation and variable names in English.
- Discussions and explanations can be in the user's language when requested.

---

## Basic Python Patterns

### Explicit Typing

Always use explicit typing on all variables and functions:
```python
from typing import Optional

def process_items(items: list[str], limit: int = 10) -> dict[str, int]:
    return {item: len(item) for item in items[:limit]}
```

### Black Formatting

Format all code in the `black` library style:
- Maximum line length of 88 characters (black default)
- Use double quotes for strings
- Trailing commas in multi-line structures
```python
def long_function_name(
    parameter_one: str,
    parameter_two: int,
    parameter_three: list[str] | None = None,
) -> dict[str, Any]:
    """Function with properly formatted parameters."""
    pass
```

---

## Modern Python Concepts - Overview

Overview of each state-of-the-art Python concept. For details and advanced examples, consult the reference files indicated.

### 1. Advanced Type System
**When to use:** Clear contracts, structural duck typing, reusable generic types.

Python 3.10+ offers: `Protocol` (structural duck typing), `TypeVar`/`Generic` (generic code), `Literal` (specific values), `TypedDict` (typed dicts), `X | Y` (modern union).
```python
from typing import Protocol, TypeVar, Generic, Literal

class Readable(Protocol):
    def read(self) -> str: ...

T = TypeVar("T")

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

Status = Literal["pending", "done", "failed"]

def process(status: Status, data: str | None = None) -> str:
    return f"{status}: {data or 'empty'}"
```

**Reference:** [references/python/type-system.md](references/python/type-system.md)

---

### 2. Async/Await
**When to use:** I/O-bound operations (APIs, databases, network, files).

Asyncio enables concurrent I/O without blocking: `async def` (coroutines), `await` (waits for operation), `asyncio.gather()` (parallelizes).
```python
import asyncio
import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def fetch_all(urls: list[str]) -> list[dict]:
    return await asyncio.gather(*[fetch_data(url) for url in urls])
```

**Reference:** [references/python/async-patterns.md](references/python/async-patterns.md)

---

### 3. Data Classes
**When to use:** Data structures with clear representation, comparison, optional immutability.

Eliminates boilerplate: `@dataclass` generates `__init__`, `__repr__`, `__eq__`; `frozen=True` (immutable); `slots=True` (less memory).
```python
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float
    label: str = ""
    tags: list[str] = field(default_factory=list)

    def distance_from_origin(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5
```

**Reference:** [references/python/dataclasses.md](references/python/dataclasses.md)

---

### 4. Context Managers
**When to use:** Resource management (files, connections, locks), setup/teardown, transactions.

Guarantee cleanup even with exceptions: `with` (usage), `@contextmanager` (simple creation), `__enter__/__exit__` (manual).
```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def managed_connection(host: str) -> Iterator[Connection]:
    conn = Connection(host)
    try:
        conn.open()
        yield conn
    finally:
        conn.close()

with managed_connection("localhost") as conn:
    conn.execute("SELECT 1")
```

**Reference:** [references/python/context-managers.md](references/python/context-managers.md)

---

### 5. Decorators
**When to use:** Cross-cutting concerns (logging, caching, auth), modify behavior without altering code.

Functions that wrap others: `@functools.cache` (memoization), `@property` (computed attributes), custom decorators.
```python
from functools import wraps, cache
from typing import Callable, TypeVar

T = TypeVar("T")

def retry(times: int = 3) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times - 1:
                        raise
            raise RuntimeError("Unreachable")
        return wrapper
    return decorator
```

**Reference:** [references/python/decorators.md](references/python/decorators.md)

---

### 6. Pydantic v2
**When to use:** External data validation (APIs, configs, files), serialization, documented schemas.

Standard for validation: `@field_validator` (custom validation), `@computed_field` (derived fields), FastAPI integration.
```python
from pydantic import BaseModel, field_validator, computed_field

class User(BaseModel):
    name: str
    email: str
    age: int

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()

    @computed_field
    @property
    def is_adult(self) -> bool:
        return self.age >= 18
```

**Reference:** [references/python/pydantic.md](references/python/pydantic.md)

---

### 7. Error Handling
**When to use:** Always; create hierarchies for specific domain errors.

Well-structured exceptions: custom hierarchy, clear messages, use for exceptional cases (not normal flow).
```python
class AppError(Exception):
    """Base exception for application errors."""

class ValidationError(AppError):
    """Raised when data validation fails."""

class NotFoundError(AppError):
    """Raised when requested resource is not found."""

    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} with id '{id}' not found")
        self.resource = resource
        self.id = id
```

**Reference:** [references/python/error-handling.md](references/python/error-handling.md)

---

### 8. Testing with Pytest
**When to use:** Always. Tests are an integral part of development.

Standard framework: fixtures (reusable setup), `@pytest.mark.parametrize` (multiple cases), simple assertions.
```python
import pytest

@pytest.fixture
def premium_user() -> User:
    return User(name="Test", tier="premium")

@pytest.mark.parametrize("price,expected", [(100.0, 90.0), (50.0, 45.0), (0.0, 0.0)])
def test_discount(premium_user: User, price: float, expected: float) -> None:
    result = calculate_discount(premium_user, price)
    assert result == pytest.approx(expected)
```

**Reference:** [references/testing/pytest.md](references/testing/pytest.md)

---

### 9. Structured Logging
**When to use:** Production and debugging; essential for observability.

Structlog produces JSON logs: automatic context, customizable processors, integration with standard logging.
```python
import structlog

logger = structlog.get_logger()

def process_order(order_id: str, user_id: str) -> None:
    log = logger.bind(order_id=order_id, user_id=user_id)
    log.info("processing_started")
    try:
        # ... process ...
        log.info("processing_completed", status="success")
    except Exception as e:
        log.error("processing_failed", error=str(e))
        raise
```

**Reference:** [references/python/logging.md](references/python/logging.md)

---

### 10. Configuration Management
**When to use:** Any app that needs external configuration (envvars, files).

Pydantic-settings: loads from env vars, integrated validation, .env and secrets support.
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env")

    database_url: str
    debug: bool = False
    max_connections: int = 10

settings = Settings()  # Loads from APP_DATABASE_URL, etc.
```

**Reference:** [references/python/configuration.md](references/python/configuration.md)

---

### 11. Generators and Lazy Evaluation
**When to use:** Large data volumes, transformation pipelines, memory savings.

Values on demand: `yield` (produces incrementally), generator expressions, `itertools`.
```python
from typing import Iterator
from pathlib import Path

def read_chunks(path: Path, size: int = 8192) -> Iterator[str]:
    with open(path) as f:
        while chunk := f.read(size):
            yield chunk

def process_lines(path: Path) -> Iterator[str]:
    for chunk in read_chunks(path):
        for line in chunk.splitlines():
            if line.strip():
                yield line.upper()
```

**Reference:** [references/python/generators.md](references/python/generators.md)

---

### 12. Concurrency
**When to use:** Choice based on workload type - I/O-bound vs CPU-bound.

Three models: `asyncio` (I/O, single-thread, cooperative), `threading` (I/O, multi-thread, GIL), `multiprocessing` (CPU, bypasses GIL).
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# asyncio for I/O-bound (preferred)
results = await asyncio.gather(*tasks)

# threading for legacy I/O-bound
with ThreadPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(io_func, items))

# multiprocessing for CPU-bound
with ProcessPoolExecutor() as ex:
    results = list(ex.map(cpu_func, items))
```

**Reference:** [references/python/concurrency.md](references/python/concurrency.md)

---

### 13. Modern Packaging
**When to use:** Distributed projects or those with managed dependencies.

`pyproject.toml` (PEP 621): replaces setup.py/setup.cfg, centralized config, modern build systems.
```toml
[project]
name = "mypackage"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.0", "httpx>=0.24"]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1"]

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Reference:** [references/python/packaging.md](references/python/packaging.md)

---

## Essential Tools

| Category | Tool | Purpose | Command |
|----------|------|---------|---------|
| Lint | **ruff** | Ultra-fast linter | `ruff check . --fix` |
| Format | **black** | Opinionated formatter | `black .` |
| Types | **mypy** | Type checker | `mypy src/` |
| Test | **pytest** | Testing framework | `pytest` |
| Coverage | **pytest-cov** | Coverage | `pytest --cov=src` |
| Hooks | **pre-commit** | Git hooks | `pre-commit install` |

**Reference:** [references/tooling/setup.md](references/tooling/setup.md)

---

## Recommended Workflow
```
ANALYZE → DESIGN → TYPE → IMPLEMENT → VALIDATE → REVIEW
```

1. **Analyze**: Understand the system, map dependencies and constraints
2. **Design**: Define boundaries, interfaces, and architectural trade-offs
3. **Type**: Type hints before implementation
4. **Implement**: Code following the design and types
5. **Validate**: ruff/black/mypy (via pre-commit)
6. **Review**: Code review focused on design and clarity

---

## References by Domain

### Python Core
- [references/python/type-system.md](references/python/type-system.md) - Protocol, TypeVar, Generic, Literal
- [references/python/async-patterns.md](references/python/async-patterns.md) - Advanced async/await
- [references/python/dataclasses.md](references/python/dataclasses.md) - Dataclasses in depth
- [references/python/context-managers.md](references/python/context-managers.md) - Context managers
- [references/python/decorators.md](references/python/decorators.md) - Advanced decorators
- [references/python/generators.md](references/python/generators.md) - Generators and iterators
- [references/python/concurrency.md](references/python/concurrency.md) - Threading, multiprocessing, asyncio
- [references/python/error-handling.md](references/python/error-handling.md) - Exceptions and error handling
- [references/python/packaging.md](references/python/packaging.md) - pyproject.toml and packaging

### Frameworks and Libraries
- [references/python/pydantic.md](references/python/pydantic.md) - Complete Pydantic v2
- [references/python/configuration.md](references/python/configuration.md) - Pydantic-settings
- [references/python/logging.md](references/python/logging.md) - Structlog
- [references/fastapi/best-practices.md](references/fastapi/best-practices.md) - FastAPI patterns

### Testing
- [references/testing/pytest.md](references/testing/pytest.md) - Complete Pytest
- [references/testing/fixtures.md](references/testing/fixtures.md) - Advanced fixtures
- [references/testing/mocking.md](references/testing/mocking.md) - Mocking and patching

### Architecture
- [references/architecture/clean-architecture.md](references/architecture/clean-architecture.md) - Clean Architecture
- [references/architecture/dependency-injection.md](references/architecture/dependency-injection.md) - DI patterns
- [references/architecture/repository-pattern.md](references/architecture/repository-pattern.md) - Repository pattern

### Tooling
- [references/tooling/setup.md](references/tooling/setup.md) - Complete tooling setup
- [references/tooling/pre-commit.md](references/tooling/pre-commit.md) - Pre-commit hooks
- [references/tooling/makefile.md](references/tooling/makefile.md) - Makefile for Python
