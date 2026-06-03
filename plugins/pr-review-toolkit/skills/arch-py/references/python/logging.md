# Structured Logging - Python 3.10+

Complete technical reference for structured logging with structlog. For decisions on when to use structured logging vs print, consult the main skill (`/developer`).

## Fundamentals

Structured logging produces logs in a structured format (JSON), not loose strings. It enables:
- Efficient querying and analysis (Elasticsearch, DataDog, CloudWatch)
- Automatic context (trace_id, user_id, request_id)
- Correlation between logs from different services
- Metrics derived from logs

**When to use:**
- Any production application
- Microservices (correlation between services)
- Debugging and troubleshooting
- Observability and monitoring

**Never use print:**
- `print` has no levels (INFO, ERROR)
- No structure (hard to parse)
- No automatic context
- Does not integrate with observability tools

---

## Basic structlog

### Installation
```bash
pip install structlog
```

### Simple Setup
```python
import structlog

# Basic configuration
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

# Get logger
logger = structlog.get_logger()

# Usage
logger.info("user_created", user_id=123, email="alice@example.com")
# Output:
# {"event": "user_created", "user_id": 123, "email": "alice@example.com", "level": "info", "timestamp": "2026-02-11T10:30:45.123456Z"}

logger.error("payment_failed", user_id=456, amount=99.99, reason="insufficient_funds")
# Output:
# {"event": "payment_failed", "user_id": 456, "amount": 99.99, "reason": "insufficient_funds", "level": "error", "timestamp": "2026-02-11T10:31:12.789012Z"}
```

### Log Levels
```python
import structlog

logger = structlog.get_logger()

# Standard log levels
logger.debug("debug_message", detail="verbose info")
logger.info("info_message", status="ok")
logger.warning("warning_message", threshold=90)
logger.error("error_occurred", error_code="E001")
logger.critical("system_failure", component="database")
```

---

## Complete Configuration

### Production Setup
```python
import structlog
import logging

# Configure standard logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        # Add log level
        structlog.stdlib.add_log_level,

        # Add logger name
        structlog.stdlib.add_logger_name,

        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),

        # Add stack info on exception
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,

        # Render to JSON
        structlog.processors.JSONRenderer()
    ],

    # Wrap standard library logger
    wrapper_class=structlog.stdlib.BoundLogger,

    # Cache logger instances
    cache_logger_on_first_use=True,
)

# Get logger
logger = structlog.get_logger()
```

### Development Setup (Console Friendly)
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()  # Colorful and readable
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
logger.info("server_started", host="localhost", port=8000)
# Output (colored):
# 2026-02-11 10:30:45 [info     ] server_started                 host=localhost port=8000
```

---

## Context Binding

### bind() - Local Context
```python
import structlog

logger = structlog.get_logger()

# Bind context to logger instance
request_logger = logger.bind(
    request_id="req-abc123",
    user_id=456
)

# Context included automatically
request_logger.info("processing_request")
# {"event": "processing_request", "request_id": "req-abc123", "user_id": 456, "level": "info", ...}

request_logger.info("request_completed", status_code=200)
# {"event": "request_completed", "request_id": "req-abc123", "user_id": 456, "status_code": 200, ...}
```

### Real-World Example

**FastAPI Middleware:**
```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid

app = FastAPI()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Bind context
        logger = structlog.get_logger().bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path
        )

        # Store logger in request state
        request.state.logger = logger

        logger.info("request_started")

        # Process request
        response = await call_next(request)

        logger.info(
            "request_completed",
            status_code=response.status_code
        )

        return response

app.add_middleware(LoggingMiddleware)

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    logger = request.state.logger

    logger.info("fetching_user", user_id=user_id)

    user = await db.get_user(user_id)

    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(status_code=404)

    logger.info("user_fetched", user_id=user_id)
    return user
```

---

## contextvars - Thread-Safe Context

### Using contextvars
```python
import structlog
from contextvars import ContextVar
import uuid

# Context vars (thread-safe)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

def get_logger():
    """Get logger with current context."""
    logger = structlog.get_logger()

    # Bind context from contextvars
    trace_id = trace_id_var.get()
    user_id = user_id_var.get()

    if trace_id:
        logger = logger.bind(trace_id=trace_id)
    if user_id:
        logger = logger.bind(user_id=user_id)

    return logger

# Set context
trace_id_var.set(str(uuid.uuid4()))
user_id_var.set("user-123")

# Use logger
logger = get_logger()
logger.info("operation_started")
# {"event": "operation_started", "trace_id": "...", "user_id": "user-123", ...}
```

### Real-World Example

**Distributed Tracing:**
```python
from contextvars import ContextVar
import structlog
import uuid
from typing import Optional

# Global context vars
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")

class TraceContext:
    """Manages distributed tracing context."""

    @staticmethod
    def set_trace_id(trace_id: Optional[str] = None) -> str:
        """Set or generate trace ID."""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
        return trace_id

    @staticmethod
    def set_span_id(span_id: Optional[str] = None) -> str:
        """Set or generate span ID."""
        if span_id is None:
            span_id = str(uuid.uuid4())
        span_id_var.set(span_id)
        return span_id

    @staticmethod
    def get_logger() -> structlog.BoundLogger:
        """Get logger with tracing context."""
        logger = structlog.get_logger()

        trace_id = trace_id_var.get()
        span_id = span_id_var.get()

        if trace_id:
            logger = logger.bind(trace_id=trace_id)
        if span_id:
            logger = logger.bind(span_id=span_id)

        return logger

# FastAPI middleware
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract trace ID from headers or generate
        trace_id = request.headers.get("X-Trace-ID")
        TraceContext.set_trace_id(trace_id)

        # Generate span ID for this request
        TraceContext.set_span_id()

        logger = TraceContext.get_logger()
        logger.info("request_started", path=request.url.path)

        response = await call_next(request)

        logger.info("request_completed", status_code=response.status_code)

        # Add trace ID to response headers
        response.headers["X-Trace-ID"] = trace_id_var.get()

        return response

app = FastAPI()
app.add_middleware(TracingMiddleware)

@app.get("/process")
async def process_data():
    logger = TraceContext.get_logger()

    logger.info("processing_started")

    # Call external service (propagate trace ID)
    await call_external_service()

    logger.info("processing_completed")
    return {"status": "ok"}

async def call_external_service():
    """Call external service with trace propagation."""
    logger = TraceContext.get_logger()

    # New span for external call
    original_span = span_id_var.get()
    TraceContext.set_span_id()

    logger.info("external_call_started", service="payment-api")

    import httpx
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://payment-api.example.com/charge",
            headers={
                "X-Trace-ID": trace_id_var.get(),
                "X-Span-ID": span_id_var.get()
            }
        )

    logger.info("external_call_completed", status_code=response.status_code)

    # Restore original span
    span_id_var.set(original_span)
```

---

## Processors

### Custom Processors
```python
import structlog
from typing import Any

def add_app_metadata(
    logger: Any,
    method_name: str,
    event_dict: dict
) -> dict:
    """Add application metadata to every log."""
    event_dict["app_name"] = "my-service"
    event_dict["app_version"] = "1.2.3"
    event_dict["environment"] = "production"
    return event_dict

structlog.configure(
    processors=[
        add_app_metadata,  # Custom processor
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
logger.info("service_started")
# {
#     "event": "service_started",
#     "app_name": "my-service",
#     "app_version": "1.2.3",
#     "environment": "production",
#     ...
# }
```

### Filtering Sensitive Data
```python
import structlog
from typing import Any

SENSITIVE_KEYS = {"password", "api_key", "secret", "token", "credit_card"}

def mask_sensitive_data(
    logger: Any,
    method_name: str,
    event_dict: dict
) -> dict:
    """Mask sensitive fields in logs."""
    for key in event_dict:
        if key in SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
    return event_dict

structlog.configure(
    processors=[
        mask_sensitive_data,
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
logger.info("user_login", username="alice", password="secret123")
# {"event": "user_login", "username": "alice", "password": "***REDACTED***", ...}
```

---

## Exception Logging

### Logging Exceptions
```python
import structlog

logger = structlog.get_logger()

try:
    result = 1 / 0
except Exception as exc:
    logger.error(
        "calculation_failed",
        exc_info=True  # Include traceback
    )
    # {
    #     "event": "calculation_failed",
    #     "exception": "ZeroDivisionError: division by zero",
    #     "traceback": "...",
    #     ...
    # }
```

### Real-World Example

**FastAPI Error Handler:**
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging."""
    logger = structlog.get_logger().bind(
        path=request.url.path,
        method=request.method
    )

    if isinstance(exc, HTTPException):
        logger.warning(
            "http_exception",
            status_code=exc.status_code,
            detail=exc.detail
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # Unexpected error
    logger.error(
        "unexpected_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/divide/{a}/{b}")
async def divide(a: int, b: int):
    logger = structlog.get_logger()

    logger.info("division_requested", a=a, b=b)

    try:
        result = a / b
        logger.info("division_completed", result=result)
        return {"result": result}
    except ZeroDivisionError as exc:
        logger.error("division_by_zero", a=a, b=b, exc_info=True)
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
```

---

## Performance Metrics

### Timing Operations
```python
import structlog
import time

logger = structlog.get_logger()

def timed_operation(operation_name: str):
    """Decorator to log operation timing."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start

                logger.info(
                    f"{operation_name}_completed",
                    duration_ms=round(elapsed * 1000, 2),
                    success=True
                )

                return result

            except Exception as exc:
                elapsed = time.perf_counter() - start

                logger.error(
                    f"{operation_name}_failed",
                    duration_ms=round(elapsed * 1000, 2),
                    error=str(exc),
                    exc_info=True
                )
                raise

        return wrapper
    return decorator

@timed_operation("database_query")
def fetch_users():
    # Simulate query
    time.sleep(0.5)
    return [{"id": 1, "name": "Alice"}]

users = fetch_users()
# {"event": "database_query_completed", "duration_ms": 502.34, "success": true, ...}
```

### Real-World Example

**API Performance Tracking:**
```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = structlog.get_logger().bind(
            method=request.method,
            path=request.url.path
        )

        start = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms
            )

            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.error(
                "request_failed",
                duration_ms=duration_ms,
                error=str(exc),
                exc_info=True
            )
            raise

app = FastAPI()
app.add_middleware(PerformanceLoggingMiddleware)
```

---

## Integration with Standard Logging

### Using Standard Library
```python
import logging
import structlog

# Configure standard logging to use structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Standard logging also uses structlog
std_logger = logging.getLogger(__name__)
std_logger.info("message from standard logging")
# Output in structured JSON

# structlog logger
struct_logger = structlog.get_logger()
struct_logger.info("message from structlog")
# Output in structured JSON
```

---

## Testing with Logging

### Capturing Logs in Tests
```python
import structlog
import pytest
from io import StringIO

@pytest.fixture
def captured_logs():
    """Fixture to capture logs during tests."""
    stream = StringIO()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=stream),
        cache_logger_on_first_use=False
    )

    yield stream

    # Reset configuration
    structlog.reset_defaults()

def test_user_creation(captured_logs):
    """Test with log capture."""
    logger = structlog.get_logger()

    logger.info("user_created", user_id=123)

    logs = captured_logs.getvalue()
    assert "user_created" in logs
    assert "user_id" in logs
    assert "123" in logs
```

---

## Established Use Cases

### Web Applications (FastAPI, Flask)
```python
logger.info("request_completed", status_code=200, duration_ms=42.5)
```

### Background Workers (Celery, RQ)
```python
logger.info("task_started", task_id="abc123", queue="high-priority")
```

### Database Operations
```python
logger.info("query_executed", table="users", duration_ms=15.2, rows=42)
```

### External API Calls
```python
logger.info("api_call", provider="stripe", endpoint="/charges", status_code=200)
```

### Error Tracking
```python
logger.error("payment_failed", user_id=123, amount=99.99, exc_info=True)
```

### Audit Trail
```python
logger.info("user_action", user_id=456, action="delete_account", resource="user-789")
```

### Performance Monitoring
```python
logger.info("cache_hit", key="user:123", hit_rate=0.95)
```

---

## Best Practices

✅ **Always use structured logging**
```python
# CORRECT
logger.info("user_created", user_id=123, email="alice@example.com")

# WRONG
print(f"User {123} created with email alice@example.com")
```

✅ **Use descriptive event names**
```python
# GOOD
logger.info("payment_processed", amount=99.99)

# BAD
logger.info("success")
```

✅ **Always include context**
```python
logger = logger.bind(request_id="req-123", user_id=456)
logger.info("order_created", order_id=789)
```

✅ **Use appropriate log levels**
```python
logger.debug("verbose_detail")      # Development only
logger.info("normal_operation")     # Informational
logger.warning("recoverable_issue") # Warning
logger.error("operation_failed")    # Error
logger.critical("system_failure")   # Critical
```

✅ **Mask sensitive data**
```python
def mask_sensitive(event_dict):
    if "password" in event_dict:
        event_dict["password"] = "***REDACTED***"
    return event_dict
```

❌ **Never use print in production**
```python
# NEVER DO THIS
print("User created")
print(f"Error: {exc}")
```

❌ **Do not log sensitive data**
```python
# AVOID
logger.info("login", password="secret123")  # NEVER!

# CORRECT
logger.info("login_successful", user_id=123)
```

❌ **Avoid unnecessary string formatting**
```python
# AVOID — string formatting before knowing if it will be logged
logger.debug(f"Processing {expensive_calculation()}")

# CORRECT — lazy evaluation
logger.debug("processing", result=expensive_calculation())
```

---

## Configuration by Environment

### Development vs Production
```python
import structlog
import os

def configure_logging():
    """Configure logging based on environment."""
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        # JSON structured logs
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Human-readable console logs
        processors = [
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Call once at startup
configure_logging()
```

---

## References

- [structlog Documentation](https://www.structlog.org/)
- [Twelve-Factor App - Logs](https://12factor.net/logs)
- [OpenTelemetry Logging](https://opentelemetry.io/docs/specs/otel/logs/)
- [ELK Stack](https://www.elastic.co/elastic-stack)
- [DataDog Logging](https://docs.datadoghq.com/logs/)
