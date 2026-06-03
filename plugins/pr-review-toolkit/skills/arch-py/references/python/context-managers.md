# Context Managers - Python 3.10+

Complete technical reference for context managers in Python. For decisions on when to create custom context managers, consult the main skill (`/developer`).

## Fundamentals

Context managers guarantee resource setup and cleanup, even when exceptions occur. The `with` protocol calls `__enter__` at the start and `__exit__` at the end.

**When to use:**
- Resource management (files, connections, locks)
- Automatic setup/teardown
- Transactions (commit/rollback)
- Temporary state changes

**Benefits:**
- Guaranteed cleanup (even with exceptions)
- Cleaner and more readable code
- Prevents resource leaks

---

## with Statement - Basic Usage

### Definition
```python
# Without context manager - manual cleanup
file = open("data.txt")
try:
    data = file.read()
finally:
    file.close()  # Always runs

# With context manager - automatic cleanup
with open("data.txt") as file:
    data = file.read()
# file.close() called automatically
```

### Multiple Context Managers
```python
# Old way (nested)
with open("input.txt") as infile:
    with open("output.txt", "w") as outfile:
        outfile.write(infile.read())

# Modern way (Python 3.10+)
with (
    open("input.txt") as infile,
    open("output.txt", "w") as outfile,
):
    outfile.write(infile.read())
```

### Real-World Example

**Database Session (SQLAlchemy):**
```python
from sqlalchemy.orm import Session

# Without context manager - manual
session = Session(engine)
try:
    user = session.query(User).filter_by(id=1).first()
    user.name = "Updated"
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()

# With context manager - automatic
with Session(engine) as session:
    user = session.query(User).filter_by(id=1).first()
    user.name = "Updated"
    session.commit()
    # automatic rollback on exception
    # automatic close at the end
```

---

## Implementing __enter__ and __exit__

### Basic Protocol
```python
class ManagedResource:
    def __enter__(self):
        """Setup - runs at the beginning of the with block."""
        print("Acquiring resource")
        return self  # Returns object for 'as' clause

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup - runs at the end of the with block."""
        print("Releasing resource")
        return False  # Propagates exception (True = suppresses)

# Usage
with ManagedResource() as resource:
    print("Using resource")
    # resource is the return value of __enter__
```

### __exit__ Parameters
```python
class ResourceWithErrorHandling:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        exc_type: Exception type (or None)
        exc_val: Exception instance (or None)
        exc_tb: Traceback (or None)
        """
        if exc_type is None:
            print("Success - no exception")
        else:
            print(f"Exception occurred: {exc_type.__name__}: {exc_val}")

        # return False: propagates exception
        # return True: suppresses exception
        return False
```

### Real-World Example

**Database Connection Pool:**
```python
from typing import Any
import psycopg2
from psycopg2.pool import SimpleConnectionPool

class DatabaseConnection:
    """Context manager for pool connection."""

    def __init__(self, pool: SimpleConnectionPool):
        self.pool = pool
        self.conn = None

    def __enter__(self):
        """Acquire connection from pool."""
        self.conn = self.pool.getconn()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Return connection to pool."""
        if exc_type is not None:
            # Rollback on error
            self.conn.rollback()
        else:
            # Commit on success
            self.conn.commit()

        # Return to pool
        self.pool.putconn(self.conn)
        return False  # Propagate exception

# Usage
pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn="...")

with DatabaseConnection(pool) as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users VALUES (%s, %s)", ("Alice", "alice@example.com"))
    # automatic commit on success
    # automatic rollback on error
```

**File Lock:**
```python
import fcntl
from pathlib import Path

class FileLock:
    """Context manager for exclusive file lock."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.file = None

    def __enter__(self):
        """Acquire lock."""
        self.file = open(self.filepath, "a")
        fcntl.flock(self.file.fileno(), fcntl.LOCK_EX)
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock."""
        if self.file:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
            self.file.close()
        return False

# Usage - guarantees exclusive access
with FileLock(Path("/tmp/myapp.lock")) as f:
    # Only one process at a time here
    f.write("Processing...\n")
```

---

## @contextmanager Decorator

### Definition

`@contextmanager` simplifies creating context managers using generators.
```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    """Simplified context manager."""
    # Setup (before yield)
    print("Acquiring resource")
    resource = acquire_resource()

    try:
        yield resource  # Passes to 'with' block
    finally:
        # Cleanup (always runs)
        print("Releasing resource")
        release_resource(resource)

# Usage
with managed_resource() as resource:
    use(resource)
```

### Error Handling
```python
from contextlib import contextmanager

@contextmanager
def transaction(connection):
    """Context manager for database transaction."""
    cursor = connection.cursor()
    try:
        yield cursor
        # Success - commit
        connection.commit()
    except Exception:
        # Error - rollback
        connection.rollback()
        raise
    finally:
        cursor.close()

# Usage
with transaction(conn) as cursor:
    cursor.execute("INSERT INTO users VALUES (%s)", ("Alice",))
    # automatic commit on success
    # automatic rollback on error
```

### Real-World Example

**Temporary Directory:**
```python
from contextlib import contextmanager
from pathlib import Path
import tempfile
import shutil

@contextmanager
def temp_directory():
    """Creates temporary directory and removes it when done."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# Usage
with temp_directory() as tmp:
    # Work with temporary files
    (tmp / "data.txt").write_text("temporary data")
    process_files(tmp)
    # tmp is removed automatically
```

**Timing Context:**
```python
from contextlib import contextmanager
import time

@contextmanager
def timer(name: str):
    """Measures execution time of a block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{name} took {elapsed:.4f}s")

# Usage
with timer("Database query"):
    results = db.execute("SELECT * FROM large_table")
# Output: Database query took 2.3451s
```

**Database Session (FastAPI Pattern):**
```python
from contextlib import contextmanager
from typing import Iterator
from sqlalchemy.orm import Session, sessionmaker

SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_db() -> Iterator[Session]:
    """Context manager for database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Usage in endpoint
def create_user(name: str, email: str) -> User:
    with get_db() as db:
        user = User(name=name, email=email)
        db.add(user)
        # automatic commit on success
        return user
```

**Changing Working Directory:**
```python
from contextlib import contextmanager
from pathlib import Path
import os

@contextmanager
def cd(path: Path):
    """Temporarily changes directory."""
    old_dir = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_dir)

# Usage
print(f"Before: {Path.cwd()}")
with cd(Path("/tmp")):
    print(f"Inside: {Path.cwd()}")
    # Work in /tmp
print(f"After: {Path.cwd()}")  # Returns to original
```

---

## Async Context Managers

### Definition

Async context managers use `__aenter__` and `__aexit__` with `async with`.
```python
class AsyncResource:
    async def __aenter__(self):
        """Async setup."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async cleanup."""
        await self.disconnect()
        return False

# Usage
async with AsyncResource() as resource:
    await resource.operation()
```

### Real-World Example

**httpx - HTTP Client:**
```python
import httpx

# httpx.AsyncClient is an async context manager
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        return response.json()
    # client.aclose() called automatically
```

**asyncpg - Database Connection:**
```python
import asyncpg

async def query_users():
    # Connection pool as async context manager
    async with asyncpg.create_pool(
        "postgresql://user:pass@localhost/db",
        min_size=10,
        max_size=100
    ) as pool:
        # Connection from pool
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")
            return [dict(row) for row in rows]
        # Connection returned to pool
    # Pool closed
```

**FastAPI - Lifespan:**
```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle."""
    # Startup
    print("Starting up...")
    app.state.db_pool = await create_db_pool()
    app.state.redis = await create_redis_client()

    yield

    # Shutdown
    print("Shutting down...")
    await app.state.db_pool.close()
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)
```

---

## @asynccontextmanager

### Definition

Async version of `@contextmanager`.
```python
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def async_resource():
    """Simplified async context manager."""
    # Async setup
    resource = await acquire_async_resource()
    try:
        yield resource
    finally:
        # Async cleanup
        await release_async_resource(resource)

# Usage
async with async_resource() as r:
    await r.operation()
```

### Real-World Example

**Database Session:**
```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Async database session."""
    session = async_sessionmaker(engine, class_=AsyncSession)()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Usage
async def create_user(name: str) -> User:
    async with get_db_session() as db:
        user = User(name=name)
        db.add(user)
        return user
```

**Rate Limiter:**
```python
from contextlib import asynccontextmanager
import asyncio
from typing import AsyncIterator

class AsyncRateLimiter:
    def __init__(self, max_concurrent: int):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Acquire rate limit slot."""
        await self.semaphore.acquire()
        try:
            yield
        finally:
            self.semaphore.release()

# Usage
limiter = AsyncRateLimiter(max_concurrent=5)

async def fetch_with_limit(url: str) -> dict:
    async with limiter.acquire():
        return await fetch_data(url)
```

**Distributed Lock (Redis):**
```python
from contextlib import asynccontextmanager
from typing import AsyncIterator
import aioredis
from uuid import uuid4

@asynccontextmanager
async def redis_lock(
    redis: aioredis.Redis,
    key: str,
    timeout: int = 10
) -> AsyncIterator[bool]:
    """Distributed lock using Redis."""
    lock_id = str(uuid4())

    # Try to acquire lock
    acquired = await redis.set(
        key,
        lock_id,
        ex=timeout,
        nx=True  # Only set if not exists
    )

    try:
        yield acquired
    finally:
        if acquired:
            # Release lock (only if we still own it)
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await redis.eval(lua_script, 1, key, lock_id)

# Usage
async with redis_lock(redis, "order:123") as acquired:
    if acquired:
        # Process order with exclusive lock
        await process_order("123")
    else:
        # Lock not available
        raise LockNotAvailableError()
```

---

## contextlib Utilities

### suppress()

Suppresses specific exceptions.
```python
from contextlib import suppress

# Without suppress
try:
    os.remove("file.txt")
except FileNotFoundError:
    pass

# With suppress - cleaner
with suppress(FileNotFoundError):
    os.remove("file.txt")
```

### redirect_stdout() / redirect_stderr()
```python
from contextlib import redirect_stdout
import io

# Capture stdout
buffer = io.StringIO()
with redirect_stdout(buffer):
    print("This goes to buffer")
    print("Not to console")

output = buffer.getvalue()
print(f"Captured: {output}")
```

### nullcontext()

Context manager that does nothing — useful for conditionals.
```python
from contextlib import nullcontext

def process_file(filepath: str, use_lock: bool = True):
    """Process file, optionally with lock."""
    lock = FileLock(filepath) if use_lock else nullcontext()

    with lock:
        # Code works with or without lock
        process(filepath)
```

### ExitStack

Manages multiple context managers dynamically.
```python
from contextlib import ExitStack

def process_files(filenames: list[str]):
    """Process multiple files simultaneously."""
    with ExitStack() as stack:
        # Open all files
        files = [
            stack.enter_context(open(fname))
            for fname in filenames
        ]

        # Process all
        for f in files:
            process(f)
        # All closed automatically
```

### Real-World Example

**Dynamic Resource Management:**
```python
from contextlib import ExitStack
from typing import Iterator

def process_batch(
    input_files: list[str],
    output_file: str,
    use_compression: bool = False
) -> None:
    """Process multiple inputs with dynamic resources."""
    with ExitStack() as stack:
        # Open all inputs
        inputs = [
            stack.enter_context(open(f))
            for f in input_files
        ]

        # Open output (possibly compressed)
        if use_compression:
            import gzip
            output = stack.enter_context(gzip.open(output_file, "wt"))
        else:
            output = stack.enter_context(open(output_file, "w"))

        # Process
        for infile in inputs:
            output.write(infile.read())
        # All closed automatically
```

---

## Threading Locks

### thread.Lock
```python
import threading

lock = threading.Lock()

# Without context manager - manual
lock.acquire()
try:
    # Critical section
    shared_resource.modify()
finally:
    lock.release()

# With context manager - automatic
with lock:
    # Critical section
    shared_resource.modify()
    # lock.release() automatic
```

### RLock (Reentrant Lock)
```python
import threading

class Counter:
    def __init__(self):
        self._lock = threading.RLock()
        self._count = 0

    def increment(self):
        with self._lock:
            self._count += 1

    def increment_by(self, n: int):
        # RLock allows acquiring multiple times
        with self._lock:
            for _ in range(n):
                self.increment()  # Acquires lock again
```

### Real-World Example

**Thread-Safe Cache:**
```python
import threading
from typing import Dict, Any

class ThreadSafeCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = value

    def get_or_compute(self, key: str, compute_fn) -> Any:
        # Lock for check and computation
        with self._lock:
            if key in self._cache:
                return self._cache[key]

            value = compute_fn()
            self._cache[key] = value
            return value

# Multi-threaded usage
cache = ThreadSafeCache()

def worker(item_id: str):
    result = cache.get_or_compute(
        item_id,
        lambda: expensive_computation(item_id)
    )
    process(result)
```

---

## Testing Context Managers

### pytest
```python
import pytest
from contextlib import contextmanager

@contextmanager
def db_transaction():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def test_transaction_success():
    """Tests commit on success."""
    with db_transaction() as conn:
        conn.execute("INSERT INTO users VALUES ('Alice')")

    # Verify commit was called
    assert user_exists("Alice")

def test_transaction_rollback():
    """Tests rollback on error."""
    with pytest.raises(ValueError):
        with db_transaction() as conn:
            conn.execute("INSERT INTO users VALUES ('Bob')")
            raise ValueError("Force rollback")

    # Verify rollback was done
    assert not user_exists("Bob")
```

---

## Established Use Cases

### File Operations
```python
with open("file.txt") as f:
    data = f.read()
```

### Database Sessions (SQLAlchemy, asyncpg)
```python
with Session(engine) as session:
    user = session.query(User).first()
```

### HTTP Clients (httpx, aiohttp)
```python
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Locks (threading, asyncio)
```python
with lock:
    # Critical section
    modify_shared_resource()
```

### Temporary Resources (tempfile)
```python
with tempfile.TemporaryDirectory() as tmpdir:
    # Work with temp files
    process(tmpdir)
```

### Transactions (database, file systems)
```python
with transaction(conn):
    conn.execute(query)
    # Auto commit/rollback
```

### Timing and Profiling
```python
with timer("operation"):
    expensive_operation()
```

### Context Changes (cd, environment)
```python
with cd("/tmp"):
    # Work in /tmp
    process_files()
```

---

## Best Practices

✅ **Always use context managers for resources**
```python
# CORRECT
with open("file.txt") as f:
    data = f.read()

# AVOID (may leak resource)
f = open("file.txt")
data = f.read()
f.close()
```

✅ **Use @contextmanager for simplicity**
```python
from contextlib import contextmanager

@contextmanager
def simple_manager():
    setup()
    try:
        yield
    finally:
        cleanup()
```

✅ **Cleanup in finally**
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    # Cleanup ALWAYS runs
    self.resource.close()
    return False
```

✅ **Propagate exceptions (return False)**
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    cleanup()
    return False  # Does not suppress exception
```

❌ **Don't suppress exceptions without reason**
```python
# AVOID
def __exit__(self, exc_type, exc_val, exc_tb):
    cleanup()
    return True  # Suppresses ALL exceptions!
```

❌ **Don't do heavy I/O in __enter__**
```python
# AVOID
def __enter__(self):
    self.data = load_huge_file()  # May block
    return self

# PREFER - lazy loading
def __enter__(self):
    return self

def get_data(self):
    if not hasattr(self, '_data'):
        self._data = load_huge_file()
    return self._data
```

---

## References

- [PEP 343](https://peps.python.org/pep-0343/) - The "with" Statement
- [contextlib Documentation](https://docs.python.org/3/library/contextlib.html)
- [PEP 492](https://peps.python.org/pep-0492/) - Async Context Managers
- [Real Python - Context Managers](https://realpython.com/python-with-statement/)
