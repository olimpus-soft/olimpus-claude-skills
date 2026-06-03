# Concurrency - Python 3.10+

Complete technical reference for concurrency in Python. For decisions on which model to use (asyncio vs threading vs multiprocessing), consult the main skill (`/developer`).

## Fundamentals

Python offers three concurrency models, each optimized for different workloads:

| Model | Best For | Parallelism | GIL Impact |
|-------|----------|-------------|------------|
| **asyncio** | I/O-bound (network, disk) | Cooperative (single-thread) | Not affected |
| **threading** | Legacy I/O-bound, blocking libs | Concurrent (multi-thread) | Limited by GIL |
| **multiprocessing** | CPU-bound (heavy computations) | Parallel (multi-process) | Bypasses GIL |

**GIL (Global Interpreter Lock):**
- Lock that prevents multiple Python threads from executing bytecode simultaneously
- Threads in I/O operations release the GIL automatically
- CPU-bound in threads does not gain speedup (requires multiprocessing)

---

## asyncio - Cooperative I/O

### When to Use

**✅ Use asyncio for:**
- Multiple simultaneous HTTP requests
- WebSockets, streaming, long-polling
- Concurrent database queries (with async drivers)
- Asynchronous file I/O (aiofiles)
- Any I/O-bound with latency

**❌ Don't use asyncio for:**
- CPU-bound (heavy computations) → use multiprocessing
- Libraries without async support → use threading + run_in_executor
- Simple scripts without concurrent I/O → overhead without gain

### Basic Syntax
```python
import asyncio
import httpx

async def fetch_user(user_id: str) -> dict:
    """Fetches user from API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        return response.json()

async def main() -> None:
    # Executes 10 requests concurrently
    user_ids = [f"user-{i}" for i in range(10)]
    users = await asyncio.gather(*[fetch_user(uid) for uid in user_ids])

# Run
asyncio.run(main())
```

### Real-World Example

**FastAPI - Async Endpoints:**
```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import structlog

logger = structlog.get_logger()

app = FastAPI()

@app.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str, db: AsyncSession) -> dict:
    """Dashboard with multiple data sources."""

    # Fetch data in parallel
    user_data, orders_data, notifications_data = await asyncio.gather(
        fetch_user_from_db(db, user_id),
        fetch_orders_from_api(user_id),
        fetch_notifications_from_redis(user_id),
        return_exceptions=True  # Does not fail all if one errors
    )

    # Handle errors gracefully
    if isinstance(user_data, Exception):
        logger.error("user_fetch_failed", error=str(user_data))
        raise HTTPException(status_code=500)

    return {
        "user": user_data,
        "orders": orders_data if not isinstance(orders_data, Exception) else [],
        "notifications": notifications_data if not isinstance(notifications_data, Exception) else []
    }

async def fetch_user_from_db(db: AsyncSession, user_id: str) -> dict:
    """Fetches user from database."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")
    return {"id": user.id, "name": user.name}

async def fetch_orders_from_api(user_id: str) -> list[dict]:
    """Fetches orders from external API."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"https://orders-api.example.com/users/{user_id}/orders")
        return response.json()

async def fetch_notifications_from_redis(user_id: str) -> list[dict]:
    """Fetches notifications from Redis."""
    import aioredis
    redis = await aioredis.from_url("redis://localhost")
    notifications = await redis.lrange(f"notifications:{user_id}", 0, -1)
    await redis.close()
    return [json.loads(n) for n in notifications]
```

**Batch Processing - asyncpg:**
```python
import asyncpg
import asyncio
from typing import AsyncIterator

async def stream_users_batch(
    pool: asyncpg.Pool,
    batch_size: int = 1000
) -> AsyncIterator[list[dict]]:
    """Stream users in batches."""
    offset = 0

    while True:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY id LIMIT $1 OFFSET $2",
                batch_size,
                offset
            )

            if not rows:
                break

            yield [dict(row) for row in rows]
            offset += batch_size

async def process_users_concurrently(pool: asyncpg.Pool) -> None:
    """Processes users in concurrent batches."""

    async def process_batch(batch: list[dict]) -> None:
        """Processes a batch of users."""
        # Simulates heavy processing (API calls, etc)
        await asyncio.gather(*[
            send_notification(user["id"], user["email"])
            for user in batch
        ])

    # Process 3 batches concurrently
    semaphore = asyncio.Semaphore(3)

    async def limited_process(batch: list[dict]) -> None:
        async with semaphore:
            await process_batch(batch)

    tasks = []
    async for batch in stream_users_batch(pool):
        task = asyncio.create_task(limited_process(batch))
        tasks.append(task)

    await asyncio.gather(*tasks)
```

### asyncio Patterns

**Rate Limiting:**
```python
import asyncio
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

class AsyncRateLimiter:
    """Rate limiter using asyncio.Semaphore."""

    def __init__(self, max_concurrent: int, calls_per_second: float):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0

    async def __aenter__(self):
        await self.semaphore.acquire()

        # Wait minimum interval since last call
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_call
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)

        self.last_call = asyncio.get_event_loop().time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()

# Usage
limiter = AsyncRateLimiter(max_concurrent=10, calls_per_second=100)

async def fetch_with_limit(url: str) -> dict:
    async with limiter:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()
```

**Retry with Exponential Backoff:**
```python
import asyncio
from typing import TypeVar, Callable
import structlog

logger = structlog.get_logger()

T = TypeVar("T")

async def async_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> T:
    """Retry async function with exponential backoff."""

    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as exc:
            if attempt == max_attempts - 1:
                logger.error(
                    "async_retry_exhausted",
                    attempts=max_attempts,
                    error=str(exc)
                )
                raise

            wait_time = backoff_factor ** attempt
            logger.warning(
                "async_retry_attempt",
                attempt=attempt + 1,
                max_attempts=max_attempts,
                wait_seconds=wait_time
            )
            await asyncio.sleep(wait_time)

    raise RuntimeError("Unreachable")

# Usage
async def flaky_api_call() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://flaky-api.example.com/data")
        response.raise_for_status()
        return response.json()

result = await async_retry(flaky_api_call, max_attempts=3)
```

### Established Use Cases

**Web Frameworks** (FastAPI, aiohttp, Sanic):
- Asynchronous endpoints for high concurrency
- WebSocket handlers

**Database Operations** (asyncpg, motor, tortoise-orm):
- Connection pooling
- Batch queries

**HTTP Clients** (httpx, aiohttp):
- Multiple API calls
- Web scraping

**Message Queues** (aio-pika, aiokafka):
- Async consumers
- Event processing

---

## threading - I/O with Synchronous Libraries

### When to Use

**✅ Use threading for:**
- Libraries without async support (requests, Pillow, etc)
- I/O-bound with blocking calls
- Compatibility with legacy code
- Lightweight background tasks

**❌ Don't use threading for:**
- CPU-bound → use multiprocessing (GIL prevents speedup)
- When async is available → asyncio is more efficient
- Complex coordination → asyncio is simpler

### Basic Syntax
```python
import threading
import requests
from queue import Queue

def fetch_url(url: str, result_queue: Queue) -> None:
    """Worker thread that fetches URL."""
    response = requests.get(url)
    result_queue.put((url, response.json()))

def fetch_multiple_urls(urls: list[str]) -> list[tuple[str, dict]]:
    """Fetches multiple URLs with threads."""
    result_queue: Queue = Queue()
    threads = []

    # Create threads
    for url in urls:
        thread = threading.Thread(target=fetch_url, args=(url, result_queue))
        thread.start()
        threads.append(thread)

    # Wait for all
    for thread in threads:
        thread.join()

    # Collect results
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())

    return results

# Usage
urls = ["https://api.example.com/1", "https://api.example.com/2"]
results = fetch_multiple_urls(urls)
```

### ThreadPoolExecutor

Modern and recommended approach:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from typing import Iterator
import structlog

logger = structlog.get_logger()

def fetch_url(url: str) -> tuple[str, dict | None]:
    """Fetches URL with error handling."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return (url, response.json())
    except Exception as exc:
        logger.error("fetch_failed", url=url, error=str(exc))
        return (url, None)

def fetch_urls_parallel(urls: list[str], max_workers: int = 10) -> list[tuple[str, dict | None]]:
    """Fetches URLs in parallel with thread pool."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(fetch_url, url) for url in urls]

        # Collect results as they complete
        results = []
        for future in as_completed(futures):
            results.append(future.result())

        return results

# Usage
urls = [f"https://api.example.com/items/{i}" for i in range(100)]
results = fetch_urls_parallel(urls, max_workers=20)
```

### Real-World Example

**Image Processing with Pillow:**
```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from typing import Iterator
import structlog

logger = structlog.get_logger()

def resize_image(input_path: Path, output_dir: Path, size: tuple[int, int]) -> Path:
    """Resizes image (I/O-bound)."""
    try:
        img = Image.open(input_path)
        img.thumbnail(size)

        output_path = output_dir / f"{input_path.stem}_thumb{input_path.suffix}"
        img.save(output_path)

        logger.info("image_resized", input=str(input_path), output=str(output_path))
        return output_path

    except Exception as exc:
        logger.error("resize_failed", path=str(input_path), error=str(exc))
        raise

def batch_resize_images(
    input_dir: Path,
    output_dir: Path,
    size: tuple[int, int] = (800, 600),
    max_workers: int = 4
) -> list[Path]:
    """Resizes multiple images in parallel."""

    output_dir.mkdir(exist_ok=True)
    image_files = list(input_dir.glob("*.{jpg,jpeg,png}"))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(resize_image, img_path, output_dir, size)
            for img_path in image_files
        ]

        return [future.result() for future in futures]

# Usage
resized = batch_resize_images(
    Path("/input/images"),
    Path("/output/thumbnails"),
    size=(400, 300),
    max_workers=8
)
```

**Background Tasks (FastAPI):**
```python
from fastapi import FastAPI, BackgroundTasks
from concurrent.futures import ThreadPoolExecutor
import structlog

logger = structlog.get_logger()
executor = ThreadPoolExecutor(max_workers=10)

app = FastAPI()

def send_email_blocking(to: str, subject: str, body: str) -> None:
    """Sends email using synchronous library."""
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["To"] = to

    with smtplib.SMTP("smtp.example.com", 587) as server:
        server.send_message(msg)

    logger.info("email_sent", to=to, subject=subject)

@app.post("/orders")
async def create_order(order: OrderCreate, background_tasks: BackgroundTasks):
    """Creates order and sends email in background."""

    # Save order (async)
    new_order = await db.create_order(order)

    # Schedule email (thread pool for blocking call)
    background_tasks.add_task(
        lambda: executor.submit(
            send_email_blocking,
            order.customer_email,
            "Order Confirmed",
            f"Your order {new_order.id} has been confirmed"
        )
    )

    return {"id": new_order.id, "status": "created"}
```

### Thread Safety - Locks
```python
import threading
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class ThreadSafeCache:
    """Thread-safe cache using Lock."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()  # Reentrant lock

    def get(self, key: str) -> Any | None:
        """Thread-safe get."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Thread-safe set."""
        with self._lock:
            self._cache[key] = value
            logger.debug("cache_set", key=key)

    def get_or_compute(self, key: str, compute_fn) -> Any:
        """Get from cache or compute (thread-safe)."""
        with self._lock:
            # Check cache
            if key in self._cache:
                logger.debug("cache_hit", key=key)
                return self._cache[key]

            # Compute
            logger.debug("cache_miss", key=key)
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

threads = [threading.Thread(target=worker, args=(f"item-{i}",)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Established Use Cases

**Legacy Code Integration:**
- Wrapping synchronous libraries in async contexts
- Gradual migration to async

**I/O-bound with Blocking Libraries:**
- requests, ftplib, smtplib
- Pillow, OpenCV (I/O operations)

**Background Tasks:**
- Email sending
- Report generation
- File processing

---

## multiprocessing - CPU-bound

### When to Use

**✅ Use multiprocessing for:**
- Heavy computations (CPU-bound)
- Parallel data processing
- Machine learning training/inference
- Image/video processing (compute-intensive)

**❌ Don't use multiprocessing for:**
- I/O-bound → asyncio or threading are lighter
- Complex shared state → serialization overhead
- Very small tasks → process creation overhead

### Basic Syntax
```python
from multiprocessing import Pool
from typing import List

def compute_heavy(n: int) -> int:
    """CPU-intensive computation."""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

def parallel_compute(numbers: List[int]) -> List[int]:
    """Processes in parallel using multiple cores."""
    with Pool() as pool:
        results = pool.map(compute_heavy, numbers)
    return results

# Usage - uses all CPU cores
numbers = [10_000_000] * 8
results = parallel_compute(numbers)
```

### ProcessPoolExecutor

Modern form (similar interface to ThreadPoolExecutor):
```python
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from typing import List
import structlog

logger = structlog.get_logger()

def process_chunk(data: np.ndarray) -> float:
    """Processes data chunk (CPU-bound)."""
    # Heavy operations (matrix multiplication, etc)
    result = np.sum(data ** 2)
    logger.info("chunk_processed", size=len(data), result=result)
    return result

def parallel_data_processing(
    data: np.ndarray,
    num_chunks: int = 4
) -> float:
    """Splits data and processes in parallel."""

    # Split data into chunks
    chunks = np.array_split(data, num_chunks)

    # Process in parallel
    with ProcessPoolExecutor(max_workers=num_chunks) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        results = [future.result() for future in futures]

    # Aggregate results
    return sum(results)

# Usage
large_array = np.random.rand(10_000_000)
total = parallel_data_processing(large_array, num_chunks=8)
```

### Real-World Example

**Parallel ML Inference:**
```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List
import numpy as np
import structlog

logger = structlog.get_logger()

def load_model():
    """Loads ML model (executed in each process)."""
    # Each process loads its own model copy
    import tensorflow as tf
    model = tf.keras.models.load_model("/path/to/model.h5")
    return model

# Global model (one per process)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model()
    return _model

def predict_batch(image_paths: List[Path]) -> List[dict]:
    """Processes a batch of images."""
    model = get_model()

    # Load and preprocess images
    images = [preprocess_image(path) for path in image_paths]

    # Batch prediction
    predictions = model.predict(np.array(images))

    return [
        {"path": str(path), "prediction": pred.tolist()}
        for path, pred in zip(image_paths, predictions)
    ]

def parallel_inference(
    image_dir: Path,
    batch_size: int = 32,
    num_workers: int = 4
) -> List[dict]:
    """Parallel inference across multiple processes."""

    # List images
    image_paths = list(image_dir.glob("*.jpg"))

    # Split into batches
    batches = [
        image_paths[i:i + batch_size]
        for i in range(0, len(image_paths), batch_size)
    ]

    logger.info(
        "starting_inference",
        total_images=len(image_paths),
        num_batches=len(batches),
        workers=num_workers
    )

    # Process batches in parallel
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(predict_batch, batch) for batch in batches]
        results = [item for future in futures for item in future.result()]

    logger.info("inference_complete", total_predictions=len(results))
    return results

# Usage
predictions = parallel_inference(
    Path("/data/images"),
    batch_size=32,
    num_workers=8
)
```

**Data Processing Pipeline:**
```python
from multiprocessing import Pool, cpu_count
from pathlib import Path
import pandas as pd
from typing import List
import structlog

logger = structlog.get_logger()

def process_csv_file(filepath: Path) -> pd.DataFrame:
    """Processes CSV file (CPU-intensive transformations)."""
    df = pd.read_csv(filepath)

    # Heavy operations
    df["processed"] = df["value"].apply(lambda x: expensive_calculation(x))
    df["normalized"] = (df["value"] - df["value"].mean()) / df["value"].std()

    logger.info("csv_processed", file=str(filepath), rows=len(df))
    return df

def expensive_calculation(value: float) -> float:
    """CPU-intensive calculation."""
    result = 0.0
    for i in range(10000):
        result += (value ** 0.5) * (i % 10)
    return result

def parallel_csv_processing(input_dir: Path, output_file: Path) -> None:
    """Processes multiple CSVs in parallel."""

    csv_files = list(input_dir.glob("*.csv"))
    num_workers = cpu_count()

    logger.info(
        "starting_processing",
        files=len(csv_files),
        workers=num_workers
    )

    # Process in parallel
    with Pool(processes=num_workers) as pool:
        dataframes = pool.map(process_csv_file, csv_files)

    # Concatenate results
    final_df = pd.concat(dataframes, ignore_index=True)
    final_df.to_csv(output_file, index=False)

    logger.info(
        "processing_complete",
        total_rows=len(final_df),
        output=str(output_file)
    )

# Usage
parallel_csv_processing(
    Path("/data/raw"),
    Path("/data/processed/combined.csv")
)
```

### Shared Memory (Python 3.8+)

To share large data between processes without copying:
```python
from multiprocessing import Process, shared_memory
import numpy as np

def worker_process(shm_name: str, shape: tuple, dtype: np.dtype) -> None:
    """Worker process that accesses shared memory."""
    # Attach to existing shared memory
    shm = shared_memory.SharedMemory(name=shm_name)

    # Create numpy array from shared memory
    array = np.ndarray(shape, dtype=dtype, buffer=shm.buf)

    # Modify array in-place
    array[:] = array ** 2

    shm.close()

# Main process
data = np.arange(1000000, dtype=np.float64)

# Create shared memory
shm = shared_memory.SharedMemory(create=True, size=data.nbytes)

# Copy data to shared memory
shared_array = np.ndarray(data.shape, dtype=data.dtype, buffer=shm.buf)
shared_array[:] = data

# Start worker processes
processes = [
    Process(target=worker_process, args=(shm.name, data.shape, data.dtype))
    for _ in range(4)
]

for p in processes:
    p.start()
for p in processes:
    p.join()

# Read results
result = shared_array.copy()

# Cleanup
shm.close()
shm.unlink()
```

### Established Use Cases

**Data Science** (pandas, numpy):
- Large dataset processing
- Feature engineering pipelines

**Machine Learning** (scikit-learn, PyTorch):
- Hyperparameter tuning
- Cross-validation
- Batch inference

**Image Processing** (OpenCV, Pillow):
- Video frame processing
- Batch transformations

**Scientific Computing** (scipy, sympy):
- Simulations
- Monte Carlo methods

---

## Performance Comparison

### Benchmark: I/O-bound (HTTP Requests)
```python
import time
import requests
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def sync_fetch(url: str) -> int:
    """Synchronous fetch."""
    response = requests.get(url)
    return response.status_code

async def async_fetch(url: str) -> int:
    """Asynchronous fetch."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.status_code

# Test URLs
urls = ["https://httpbin.org/delay/1"] * 10

# 1. Sequential (baseline)
start = time.perf_counter()
for url in urls:
    sync_fetch(url)
sequential_time = time.perf_counter() - start
# ~10 seconds (1s * 10)

# 2. Threading
start = time.perf_counter()
with ThreadPoolExecutor(max_workers=10) as executor:
    list(executor.map(sync_fetch, urls))
threading_time = time.perf_counter() - start
# ~1 second (parallel)

# 3. Asyncio
start = time.perf_counter()
asyncio.run(asyncio.gather(*[async_fetch(url) for url in urls]))
asyncio_time = time.perf_counter() - start
# ~1 second (parallel)

# 4. Multiprocessing (overhead, not recommended for I/O)
start = time.perf_counter()
with ProcessPoolExecutor(max_workers=10) as executor:
    list(executor.map(sync_fetch, urls))
multiprocessing_time = time.perf_counter() - start
# ~2-3 seconds (process overhead)
```

**Result:**
- **Sequential:** ~10s (baseline)
- **Threading:** ~1s (10x speedup)
- **Asyncio:** ~1s (10x speedup, less overhead)
- **Multiprocessing:** ~2-3s (overhead without gain)

### Benchmark: CPU-bound (Computations)
```python
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def cpu_intensive(n: int) -> int:
    """CPU-bound computation."""
    result = 0
    for i in range(n):
        result += i ** 2
    return result

numbers = [10_000_000] * 8

# 1. Sequential
start = time.perf_counter()
for n in numbers:
    cpu_intensive(n)
sequential_time = time.perf_counter() - start
# ~8 seconds (baseline)

# 2. Threading (limited by GIL)
start = time.perf_counter()
with ThreadPoolExecutor(max_workers=8) as executor:
    list(executor.map(cpu_intensive, numbers))
threading_time = time.perf_counter() - start
# ~8 seconds (NO speedup due to GIL)

# 3. Multiprocessing
start = time.perf_counter()
with ProcessPoolExecutor(max_workers=8) as executor:
    list(executor.map(cpu_intensive, numbers))
multiprocessing_time = time.perf_counter() - start
# ~1 second (8x speedup on 8 cores)
```

**Result:**
- **Sequential:** ~8s (baseline)
- **Threading:** ~8s (GIL prevents parallelism)
- **Multiprocessing:** ~1s (real 8x speedup)

---

## Choosing the Right Model

### Decision Tree
```
Is the workload CPU-bound (heavy computations)?
├─ YES → multiprocessing
└─ NO (I/O-bound)
   └─ Does the library have async support?
      ├─ YES → asyncio
      └─ NO → threading
```

### Decision Table

| Scenario | Model | Reason |
|----------|-------|--------|
| 100+ HTTP requests | asyncio | Efficient concurrent I/O |
| Image resize (Pillow) | threading | Synchronous library, I/O-bound |
| ML training | multiprocessing | Heavy CPU-bound |
| Database queries (asyncpg) | asyncio | Async driver available |
| Legacy requests library | threading | Synchronous library |
| Matrix operations | multiprocessing | CPU-bound, bypasses GIL |
| WebSocket connections | asyncio | Native async I/O |
| File compression | multiprocessing | CPU-bound |

---

## Best Practices

✅ **Use asyncio as first choice for I/O**
```python
# Prefer asyncio when possible
async def fetch_data():
    async with httpx.AsyncClient() as client:
        return await client.get(url)
```

✅ **Use executors for mixing sync/async**
```python
# Run synchronous code in async context
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, blocking_function, arg)
```

✅ **Limit worker count appropriately**
```python
# Threading: I/O-bound can have many workers
ThreadPoolExecutor(max_workers=100)

# Multiprocessing: CPU-bound = number of cores
ProcessPoolExecutor(max_workers=cpu_count())
```

✅ **Use context managers**
```python
# CORRECT - cleanup guaranteed
with ThreadPoolExecutor() as executor:
    results = executor.map(func, items)

# AVOID - may leak resources
executor = ThreadPoolExecutor()
results = executor.map(func, items)
# Forgot executor.shutdown()
```

❌ **Don't use multiprocessing for I/O-bound**
```python
# AVOID - overhead without gain
with ProcessPoolExecutor() as executor:
    executor.map(requests.get, urls)

# PREFER - asyncio or threading
async with httpx.AsyncClient() as client:
    await asyncio.gather(*[client.get(url) for url in urls])
```

❌ **Don't rely on threading for CPU-bound**
```python
# AVOID - GIL prevents speedup
with ThreadPoolExecutor() as executor:
    executor.map(cpu_heavy_function, items)

# USE - multiprocessing bypasses GIL
with ProcessPoolExecutor() as executor:
    executor.map(cpu_heavy_function, items)
```

---

## References

- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [threading Documentation](https://docs.python.org/3/library/threading.html)
- [multiprocessing Documentation](https://docs.python.org/3/library/multiprocessing.html)
- [concurrent.futures Documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [Understanding the GIL](https://realpython.com/python-gil/)
- [PEP 3148](https://peps.python.org/pep-3148/) - futures
