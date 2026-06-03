# Generators and Lazy Evaluation - Python 3.10+

Complete technical reference for generators and iterators in Python. For decisions on when to use generators vs lists, consult the main skill (`/developer`).

## Fundamentals

Generators produce values on demand (lazy evaluation) instead of creating everything in memory. Benefits:
- **Memory efficiency**: O(1) vs O(n) in memory
- **Performance**: Starts immediately (does not wait for everything to compute)
- **Composability**: Transformation pipelines
- **Infinite sequences**: Can represent infinite series

**When to use:**
- Large datasets (do not fit in memory)
- Streaming/pipeline processing
- Infinite sequences
- File processing line by line
- One-pass iteration is sufficient

**When NOT to use:**
- Need indexing/slicing (`data[5]`)
- Multiple iterations over the same data
- Need `len()` or `reversed()`
- Small dataset (overhead without benefit)

---

## Generator Functions

### Definition

A function with `yield` returns a generator, not a single value:
```python
def count_up_to(n: int):
    """Generator that counts up to n."""
    i = 0
    while i < n:
        yield i
        i += 1

# Usage
counter = count_up_to(5)
print(type(counter))  # <class 'generator'>

# Iterate
for num in counter:
    print(num)  # 0, 1, 2, 3, 4

# Generator exhausted after first iteration
for num in counter:
    print(num)  # Prints nothing (generator already consumed)
```

### yield vs return
```python
def normal_function():
    """Normal function — returns once."""
    return [1, 2, 3]

def generator_function():
    """Generator — yields multiple times."""
    yield 1
    yield 2
    yield 3

# normal_function returns full list
result = normal_function()
print(result)  # [1, 2, 3]

# generator_function returns generator object
gen = generator_function()
print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3
# print(next(gen))  # StopIteration
```

### Real-World Example

**File Processing (Memory Efficient):**
```python
from pathlib import Path
from typing import Iterator

def read_large_file(filepath: Path) -> Iterator[str]:
    """
    Read file line by line (memory efficient).

    Advantage: a 10GB file uses ~1KB of memory.
    """
    with open(filepath) as f:
        for line in f:
            yield line.strip()

def process_logs(log_file: Path) -> Iterator[dict]:
    """
    Process logs without loading everything into memory.
    """
    for line in read_large_file(log_file):
        if line.startswith("ERROR"):
            parts = line.split("|")
            yield {
                "timestamp": parts[0],
                "level": parts[1],
                "message": parts[2]
            }

# Usage — memory efficient even with huge files
import structlog
logger = structlog.get_logger()

for error in process_logs(Path("/var/log/app.log")):
    logger.error("log_entry", **error)

# Alternative WITHOUT generator (bad):
def read_all_file_bad(filepath: Path) -> list[str]:
    """Loads everything into memory (bad for large files)."""
    with open(filepath) as f:
        return [line.strip() for line in f]  # 10GB file = 10GB RAM!
```

---

## Generator Expressions

### Syntax

Similar to list comprehension, but with `()`:
```python
# List comprehension — creates full list
squares_list = [x**2 for x in range(1000000)]  # ~8MB of memory

# Generator expression — lazy evaluation
squares_gen = (x**2 for x in range(1000000))   # ~100 bytes of memory

# Usage
print(next(squares_gen))  # 0
print(next(squares_gen))  # 1
print(next(squares_gen))  # 4
```

### Memory Comparison
```python
import sys

# List comprehension
numbers_list = [x for x in range(1000000)]
print(sys.getsizeof(numbers_list))  # ~8MB

# Generator expression
numbers_gen = (x for x in range(1000000))
print(sys.getsizeof(numbers_gen))   # ~120 bytes

# Generator is ~66,000x more memory efficient!
```

### Real-World Example

**Data Pipeline:**
```python
from typing import Iterator

def load_raw_data(filename: str) -> Iterator[str]:
    """Load raw CSV lines."""
    with open(filename) as f:
        next(f)  # Skip header
        for line in f:
            yield line.strip()

def parse_line(line: str) -> dict:
    """Parse CSV line to dict."""
    parts = line.split(",")
    return {
        "user_id": parts[0],
        "amount": float(parts[1]),
        "timestamp": parts[2]
    }

def filter_large_amounts(records: Iterator[dict]) -> Iterator[dict]:
    """Filter records with amount > 1000."""
    for record in records:
        if record["amount"] > 1000:
            yield record

def transform_currency(records: Iterator[dict], rate: float) -> Iterator[dict]:
    """Convert amounts to different currency."""
    for record in records:
        record["amount"] = record["amount"] * rate
        yield record

# Pipeline composition — memory efficient
raw_lines = load_raw_data("transactions.csv")
records = (parse_line(line) for line in raw_lines)
large_transactions = filter_large_amounts(records)
converted = transform_currency(large_transactions, rate=5.5)

# Process (lazy — only processes when needed)
for transaction in converted:
    process_transaction(transaction)

# 10GB file processed with constant memory (~1MB)
```

---

## yield from

### Delegation

`yield from` delegates to another generator:
```python
def generator1():
    yield 1
    yield 2

def generator2():
    yield 3
    yield 4

def combined():
    """Combines generators."""
    yield from generator1()
    yield from generator2()

# Usage
for num in combined():
    print(num)  # 1, 2, 3, 4
```

### Real-World Example

**Tree Traversal:**
```python
from typing import Iterator
from dataclasses import dataclass

@dataclass
class TreeNode:
    value: int
    children: list["TreeNode"]

def traverse_tree(node: TreeNode) -> Iterator[int]:
    """Traverse tree depth-first (generator)."""
    yield node.value

    for child in node.children:
        yield from traverse_tree(child)

# Usage
root = TreeNode(1, [
    TreeNode(2, [
        TreeNode(4, []),
        TreeNode(5, [])
    ]),
    TreeNode(3, [
        TreeNode(6, [])
    ])
])

for value in traverse_tree(root):
    print(value)  # 1, 2, 4, 5, 3, 6
```

**Flatten Nested Lists:**
```python
from typing import Iterator, Any

def flatten(nested: list) -> Iterator[Any]:
    """Flatten arbitrarily nested list."""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

# Usage
nested_list = [1, [2, [3, 4], 5], [6, 7]]
flat = list(flatten(nested_list))
print(flat)  # [1, 2, 3, 4, 5, 6, 7]
```

---

## Iterators vs Generators

### Difference
```python
from typing import Iterator

# Generator (using yield)
def generator_counter(n: int) -> Iterator[int]:
    """Generator function."""
    i = 0
    while i < n:
        yield i
        i += 1

# Iterator (implementing the protocol)
class IteratorCounter:
    """Iterator class (more verbose)."""

    def __init__(self, n: int):
        self.n = n
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.i >= self.n:
            raise StopIteration
        value = self.i
        self.i += 1
        return value

# Both work the same way
for i in generator_counter(3):
    print(i)  # 0, 1, 2

for i in IteratorCounter(3):
    print(i)  # 0, 1, 2

# Generator is more concise (3 lines vs 15)
```

### Custom Iterator
```python
from typing import Iterator

class RangeIterator:
    """Custom iterator similar to range()."""

    def __init__(self, start: int, end: int, step: int = 1):
        self.current = start
        self.end = end
        self.step = step

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current >= self.end:
            raise StopIteration

        value = self.current
        self.current += self.step
        return value

# Usage
for num in RangeIterator(0, 10, 2):
    print(num)  # 0, 2, 4, 6, 8
```

---

## itertools - Powerful Tools

### count, cycle, repeat
```python
import itertools

# count — infinite counting
counter = itertools.count(start=10, step=2)
print(next(counter))  # 10
print(next(counter))  # 12
print(next(counter))  # 14

# cycle — repeats sequence infinitely
colors = itertools.cycle(["red", "green", "blue"])
print(next(colors))  # red
print(next(colors))  # green
print(next(colors))  # blue
print(next(colors))  # red (restarts)

# repeat — repeats value N times
threes = itertools.repeat(3, times=5)
print(list(threes))  # [3, 3, 3, 3, 3]
```

### chain, islice, takewhile
```python
import itertools

# chain — concatenates iterables
combined = itertools.chain([1, 2], [3, 4], [5, 6])
print(list(combined))  # [1, 2, 3, 4, 5, 6]

# islice — slice of iterator
numbers = itertools.count()
first_ten = itertools.islice(numbers, 10)
print(list(first_ten))  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# takewhile — takes while condition holds
numbers = itertools.count()
less_than_five = itertools.takewhile(lambda x: x < 5, numbers)
print(list(less_than_five))  # [0, 1, 2, 3, 4]

# dropwhile — skips while condition holds
numbers = [1, 2, 3, 4, 5, 4, 3, 2, 1]
after_peak = itertools.dropwhile(lambda x: x < 5, numbers)
print(list(after_peak))  # [5, 4, 3, 2, 1]
```

### groupby
```python
import itertools
from typing import Iterator

data = [
    {"name": "Alice", "city": "NYC"},
    {"name": "Bob", "city": "NYC"},
    {"name": "Charlie", "city": "LA"},
    {"name": "David", "city": "LA"},
]

# Group by city (must be sorted first)
data.sort(key=lambda x: x["city"])

for city, group in itertools.groupby(data, key=lambda x: x["city"]):
    people = [person["name"] for person in group]
    print(f"{city}: {people}")
# LA: ['Charlie', 'David']
# NYC: ['Alice', 'Bob']
```

### Real-World Example

**Batch Processing:**
```python
import itertools
from typing import Iterator, TypeVar

T = TypeVar("T")

def batch_iterator(iterable: Iterator[T], batch_size: int) -> Iterator[list[T]]:
    """Divide iterator into batches."""
    iterator = iter(iterable)
    while True:
        batch = list(itertools.islice(iterator, batch_size))
        if not batch:
            break
        yield batch

# Usage
def process_users_in_batches(user_ids: Iterator[str]) -> None:
    """Process users in batches of 100."""
    import structlog
    logger = structlog.get_logger()

    for batch in batch_iterator(user_ids, batch_size=100):
        logger.info("processing_batch", batch_size=len(batch))

        # Process batch
        results = db.bulk_update_users(batch)

        logger.info("batch_completed", updated=len(results))

# Memory efficient — processes 1 million users with constant memory
all_user_ids = (user["id"] for user in db.stream_all_users())
process_users_in_batches(all_user_ids)
```

---

## Async Generators

### Definition

Async generator uses `async def` + `yield`:
```python
import asyncio
from typing import AsyncIterator

async def async_count(n: int) -> AsyncIterator[int]:
    """Async generator."""
    for i in range(n):
        await asyncio.sleep(0.1)  # Simulate async operation
        yield i

# Usage
async def main():
    async for num in async_count(5):
        print(num)

asyncio.run(main())
```

### Real-World Example

**Stream Database Results:**
```python
import asyncio
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()

async def stream_users(
    db: AsyncSession,
    batch_size: int = 1000
) -> AsyncIterator[dict]:
    """Stream users from database (memory efficient)."""
    offset = 0

    while True:
        # Fetch batch
        result = await db.execute(
            select(User).offset(offset).limit(batch_size)
        )
        users = result.scalars().all()

        if not users:
            break

        logger.info("batch_fetched", count=len(users), offset=offset)

        # Yield individual users
        for user in users:
            yield {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }

        offset += batch_size

# Usage
async def process_all_users(db: AsyncSession):
    """Process all users without loading all in memory."""
    count = 0

    async for user in stream_users(db):
        await send_notification(user)
        count += 1

    logger.info("processing_completed", total_users=count)
```

**Stream API Responses:**
```python
import asyncio
import httpx
from typing import AsyncIterator
import structlog

logger = structlog.get_logger()

async def stream_api_pages(
    base_url: str,
    endpoint: str
) -> AsyncIterator[dict]:
    """Stream paginated API results."""
    async with httpx.AsyncClient() as client:
        page = 1

        while True:
            logger.info("fetching_page", page=page)

            response = await client.get(
                f"{base_url}{endpoint}",
                params={"page": page, "per_page": 100}
            )
            response.raise_for_status()

            data = response.json()
            items = data["items"]

            if not items:
                break

            for item in items:
                yield item

            page += 1

# Usage
async def sync_external_data():
    """Sync data from external API."""
    count = 0

    async for item in stream_api_pages("https://api.example.com", "/products"):
        await db.upsert_product(item)
        count += 1

    logger.info("sync_completed", synced_items=count)
```

---

## Streaming Patterns

### Pipeline Pattern
```python
from typing import Iterator
import structlog

logger = structlog.get_logger()

def load_data(filename: str) -> Iterator[str]:
    """Stage 1: Load raw lines."""
    logger.info("loading_data", filename=filename)
    with open(filename) as f:
        for line in f:
            yield line.strip()

def parse_data(lines: Iterator[str]) -> Iterator[dict]:
    """Stage 2: Parse lines to dicts."""
    for line in lines:
        parts = line.split(",")
        yield {
            "id": parts[0],
            "value": float(parts[1]),
            "timestamp": parts[2]
        }

def filter_data(records: Iterator[dict]) -> Iterator[dict]:
    """Stage 3: Filter invalid records."""
    for record in records:
        if record["value"] > 0:
            yield record

def transform_data(records: Iterator[dict]) -> Iterator[dict]:
    """Stage 4: Transform records."""
    for record in records:
        record["value"] = record["value"] * 1.1
        yield record

def save_data(records: Iterator[dict]) -> int:
    """Stage 5: Save to database."""
    count = 0
    for record in records:
        db.insert(record)
        count += 1
    return count

# Better syntax with explicit chaining
raw_lines = load_data("data.csv")
parsed = parse_data(raw_lines)
filtered = filter_data(parsed)
transformed = transform_data(filtered)
saved_count = save_data(transformed)

logger.info("pipeline_completed", records_saved=saved_count)
```

### Producer-Consumer Pattern
```python
import asyncio
from typing import AsyncIterator
import structlog

logger = structlog.get_logger()

async def producer(queue: asyncio.Queue, n: int) -> None:
    """Produce items asynchronously."""
    for i in range(n):
        item = f"item-{i}"
        await queue.put(item)
        logger.info("produced", item=item)
        await asyncio.sleep(0.1)

    # Signal completion
    await queue.put(None)

async def consumer(queue: asyncio.Queue) -> None:
    """Consume items asynchronously."""
    while True:
        item = await queue.get()

        if item is None:
            break

        logger.info("consuming", item=item)
        await process_item(item)
        await asyncio.sleep(0.2)

async def main():
    queue = asyncio.Queue(maxsize=10)

    await asyncio.gather(
        producer(queue, 20),
        consumer(queue)
    )

asyncio.run(main())
```

---

## Performance Comparisons

### List vs Generator
```python
import time
import sys

# List - eager evaluation
def process_with_list(n: int) -> list[int]:
    return [x ** 2 for x in range(n)]

# Generator - lazy evaluation
def process_with_generator(n: int):
    return (x ** 2 for x in range(n))

n = 10_000_000

# List
start = time.perf_counter()
result_list = process_with_list(n)
list_time = time.perf_counter() - start
list_memory = sys.getsizeof(result_list)

# Generator
start = time.perf_counter()
result_gen = process_with_generator(n)
gen_time = time.perf_counter() - start
gen_memory = sys.getsizeof(result_gen)

print(f"List: {list_time:.3f}s, {list_memory / 1_000_000:.1f}MB")
# List: 0.450s, 80.0MB

print(f"Generator: {gen_time:.6f}s, {gen_memory}bytes")
# Generator: 0.000001s, 112bytes

# Generator is ~450,000x faster (initialization)
# Generator is ~714,000x more memory efficient
```

### Real Processing Time
```python
import time

def process_first_10_list(n: int) -> list[int]:
    """Process with list — creates everything first."""
    data = [x ** 2 for x in range(n)]  # Waits to process everything
    return data[:10]

def process_first_10_gen(n: int) -> list[int]:
    """Process with generator — lazy."""
    data = (x ** 2 for x in range(n))  # Instantaneous
    return list(itertools.islice(data, 10))  # Only processes 10

n = 10_000_000

# List — processes 10M before returning 10
start = time.perf_counter()
result = process_first_10_list(n)
print(f"List: {time.perf_counter() - start:.3f}s")
# List: 0.450s

# Generator — processes only 10
start = time.perf_counter()
result = process_first_10_gen(n)
print(f"Generator: {time.perf_counter() - start:.6f}s")
# Generator: 0.000010s

# Generator is ~45,000x faster (only processes what is needed)
```

---

## Infinite Sequences

### Definition

Generators can represent infinite sequences:
```python
import itertools

def fibonacci() -> Iterator[int]:
    """Generate infinite fibonacci sequence."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Usage — take as many as needed
fib = fibonacci()
first_10 = list(itertools.islice(fib, 10))
print(first_10)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### Real-World Example

**ID Generator:**
```python
import itertools
from typing import Iterator
from datetime import datetime

def generate_ids(prefix: str) -> Iterator[str]:
    """Generate infinite unique IDs."""
    counter = itertools.count(1)

    while True:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        count = next(counter)
        yield f"{prefix}-{timestamp}-{count:06d}"

# Usage
id_gen = generate_ids("order")

order_id_1 = next(id_gen)  # "order-20260211103045-000001"
order_id_2 = next(id_gen)  # "order-20260211103045-000002"
order_id_3 = next(id_gen)  # "order-20260211103045-000003"
```

---

## Established Use Cases

### Data Processing
```python
for record in read_large_csv("data.csv"):
    process_record(record)
```

### Log Analysis
```python
for error_line in parse_error_logs("/var/log/app.log"):
    alert_team(error_line)
```

### Streaming APIs
```python
async for event in stream_api_events():
    handle_event(event)
```

### Database Cursors
```python
for row in db.stream_query("SELECT * FROM large_table"):
    transform_row(row)
```

### ETL Pipelines
```python
pipeline = extract() | transform() | load()
```

---

## Best Practices

✅ **Use generators for large datasets**
```python
# CORRECT — memory efficient
def read_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()

# AVOID — loads everything
def read_file_bad(path):
    with open(path) as f:
        return [line.strip() for line in f]
```

✅ **Prefer generator expressions**
```python
# CORRECT
sum(x**2 for x in range(1000000))

# AVOID — unnecessary
sum([x**2 for x in range(1000000)])
```

✅ **Use itertools for complex operations**
```python
import itertools

# Batching
for batch in itertools.batched(items, 100):
    process_batch(batch)
```

✅ **Document if generator is one-shot**
```python
def stream_data():
    """
    Stream data from API.

    Note: Generator can only be consumed once.
    """
    yield from fetch_data()
```

❌ **Do not try len() on a generator**
```python
# ERROR
gen = (x for x in range(10))
# len(gen)  # TypeError

# If you need len, don't use a generator
data = list(gen)
print(len(data))
```

❌ **Do not use generator if you need multiple iterations**
```python
# AVOID
gen = (x**2 for x in range(100))
sum1 = sum(gen)
sum2 = sum(gen)  # 0 (exhausted!)

# USE a list
data = [x**2 for x in range(100)]
sum1 = sum(data)
sum2 = sum(data)  # OK
```

---

## References

- [Generators Documentation](https://docs.python.org/3/howto/functional.html#generators)
- [PEP 255](https://peps.python.org/pep-0255/) - Simple Generators
- [PEP 342](https://peps.python.org/pep-0342/) - Coroutines via Enhanced Generators
- [itertools Documentation](https://docs.python.org/3/library/itertools.html)
- [Generator Tricks for Systems Programmers](http://www.dabeaz.com/generators/)
