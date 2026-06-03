# Advanced Type System - Python 3.10+

Complete technical reference for the modern type system in Python. For decisions on when to apply each pattern, consult the main skill (`/developer`).

## Fundamentals

Python 3.10+ introduces modern syntax for types:
- **Union with `|`**: `str | None` instead of `Union[str, None]`
- **Built-in Generics**: `list[str]` instead of `List[str]`
- **Pattern matching**: `match`/`case` with type narrowing

This document covers advanced features for type safety in production.

---

## Protocol - Structural Subtyping

### Definition

Protocol defines an interface based on structure (duck typing), not inheritance. Classes that implement the methods satisfy the protocol implicitly.
```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> str: ...

class Circle:
    def draw(self) -> str:
        return "○"

class Square:
    def draw(self) -> str:
        return "□"

def render(shape: Drawable) -> None:
    print(shape.draw())

# Type checker accepts both without inheritance
render(Circle())  # OK
render(Square())  # OK
```

### Runtime Checking

By default, Protocol is only for static type checking. Use `@runtime_checkable` for runtime validation:
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    def close(self) -> None: ...

class File:
    def close(self) -> None:
        pass

f = File()
isinstance(f, Closeable)  # True (with @runtime_checkable)
```

### Real-World Examples

**FastAPI - Dependency Protocol:**
```python
# fastapi/dependencies/utils.py
from typing import Protocol

class Dependable(Protocol):
    async def __call__(self) -> Any: ...

# Any async callable satisfies the protocol
async def get_db() -> Database:
    return Database()

# FastAPI accepts because it implements __call__
@app.get("/users")
async def users(db: Database = Depends(get_db)):
    ...
```

**httpx - Transport Protocol:**
```python
# httpx/_transports/base.py
from typing import Protocol

class AsyncBaseTransport(Protocol):
    async def handle_async_request(self, request: Request) -> Response: ...

# Concrete implementations
class AsyncHTTPTransport:
    async def handle_async_request(self, request: Request) -> Response:
        # HTTP/1.1 implementation
        ...

class AsyncHTTP2Transport:
    async def handle_async_request(self, request: Request) -> Response:
        # HTTP/2 implementation
        ...

# httpx accepts any transport that implements the protocol
client = httpx.AsyncClient(transport=AsyncHTTPTransport())
```

**Pydantic - Validator Protocol:**
```python
# pydantic/functional_validators.py
from typing import Protocol, Any

class FieldValidator(Protocol):
    def __call__(self, __value: Any) -> Any: ...

# Any callable satisfies
def validate_email(value: str) -> str:
    if "@" not in value:
        raise ValueError("Invalid email")
    return value.lower()

# Pydantic accepts as validator
class User(BaseModel):
    email: str

    _validate_email = field_validator("email")(validate_email)
```

### Comparison: Protocol vs ABC

| Aspect | Protocol | ABC |
|--------|----------|-----|
| Coupling | Low (structural) | High (inheritance) |
| Compatibility | Existing code | Requires modification |
| Validation | Static (mypy) | Runtime (`isinstance`) |
| When to use | Libraries, plugins | Internal hierarchies |

### Established Use Cases

**Public libraries** (FastAPI, httpx, Pydantic):
- Accept third-party objects without forcing inheritance
- Define plugin/extension contracts

**Dependency Injection**:
- Define service interfaces
- Allow multiple implementations

**Testing**:
- Create mocks that satisfy protocols
- No need to inherit test classes

---

## TypeVar and Generic - Parameterized Types

### Definition

`TypeVar` creates type variables for generic functions and classes. `Generic[T]` defines classes that accept type parameters.
```python
from typing import TypeVar, Generic

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

# Type checker infers the type
x: int = first([1, 2, 3])      # T = int
y: str = first(["a", "b"])     # T = str
```

### Generic Classes
```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

# Type-safe usage
int_stack: Stack[int] = Stack()
int_stack.push(1)      # OK
int_stack.push("a")    # Type error
```

### Bounded TypeVar

Restricts accepted types:
```python
from typing import TypeVar

# Accepts only int or float
Numeric = TypeVar("Numeric", int, float)

def add(a: Numeric, b: Numeric) -> Numeric:
    return a + b

add(1, 2)      # OK, returns int
add(1.0, 2.0)  # OK, returns float
add("a", "b")  # Type error
```

### Real-World Examples

**SQLAlchemy - Generic Query:**
```python
# sqlalchemy/orm/query.py
from typing import TypeVar, Generic

_T = TypeVar("_T")

class Query(Generic[_T]):
    def filter(self, *criterion) -> Query[_T]:
        ...

    def first(self) -> _T | None:
        ...

    def all(self) -> list[_T]:
        ...

# Type-safe queries
users: Query[User] = session.query(User)
user: User | None = users.filter(User.id == 1).first()
all_users: list[User] = users.all()
```

**FastAPI - Generic Response:**
```python
# fastapi/responses.py
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class JSONResponse(Generic[T]):
    def __init__(self, content: T) -> None:
        self.content = content

    def render(self) -> bytes:
        return self.content.model_dump_json().encode()

# Type-safe responses
class UserResponse(BaseModel):
    id: int
    name: str

response: JSONResponse[UserResponse] = JSONResponse(
    UserResponse(id=1, name="Alice")
)
```

**Repository Pattern:**
```python
from typing import TypeVar, Generic, Protocol

class Entity(Protocol):
    id: str

T = TypeVar("T", bound=Entity)

class Repository(Generic[T]):
    def find_by_id(self, id: str) -> T | None:
        ...

    def save(self, entity: T) -> T:
        ...

    def delete(self, entity: T) -> None:
        ...

# Type-safe repositories
class User:
    id: str
    name: str

user_repo: Repository[User] = Repository()
user: User | None = user_repo.find_by_id("123")
```

### Established Use Cases

**ORMs and Query Builders** (SQLAlchemy, Tortoise ORM):
- Type-safe queries that return correct types

**Generic containers** (Repository, Service layers):
- Reuse logic for different entities

**API clients** (httpx, aiohttp wrappers):
- Response types based on the endpoint

---

## Literal - Specific Literal Values

### Definition

`Literal` restricts values to specific literals, creating more precise types than generic strings or ints.
```python
from typing import Literal

def set_status(status: Literal["pending", "done", "failed"]) -> None:
    print(f"Status: {status}")

set_status("pending")  # OK
set_status("done")     # OK
set_status("invalid")  # Type error
```

### Union of Literals
```python
from typing import Literal

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

def make_request(method: HttpMethod, url: str) -> None:
    ...

def log(level: LogLevel, message: str) -> None:
    ...
```

### Type Narrowing

Type checkers refine types in branches:
```python
from typing import Literal

def process(mode: Literal["sync", "async"]) -> None:
    if mode == "sync":
        # mypy knows mode is Literal["sync"]
        run_sync()
    else:
        # mypy knows mode is Literal["async"]
        run_async()
```

### Real-World Examples

**Typer - Command Arguments:**
```python
# typer/models.py
from typing import Literal

Environment = Literal["dev", "staging", "production"]

@app.command()
def deploy(env: Environment) -> None:
    if env == "production":
        confirm = typer.confirm("Deploy to production?")
        if not confirm:
            raise typer.Abort()
    deploy_to(env)
```

**Pydantic - Discriminated Unions:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class Cat(BaseModel):
    type: Literal["cat"]
    meow: str

class Dog(BaseModel):
    type: Literal["dog"]
    bark: str

Animal = Cat | Dog

def handle_animal(animal: Animal) -> None:
    if animal.type == "cat":
        # Type narrowed to Cat
        print(animal.meow)
    else:
        # Type narrowed to Dog
        print(animal.bark)
```

**FastAPI - Response Status:**
```python
from typing import Literal
from fastapi import HTTPException

def get_user(user_id: str) -> User:
    user = db.get(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

# With Literal for status codes
StatusCode = Literal[200, 201, 400, 404, 500]

class Response(BaseModel):
    status: StatusCode
    data: dict
```

### Established Use Cases

**Enums as strings** (Typer, Click):
- CLI arguments with fixed values

**Discriminated unions** (Pydantic, dataclasses):
- Different types based on discriminator field

**State machines**:
- Valid states as literals

**API status codes, HTTP methods**:
- Type safety for constants

---

## TypedDict - Dicts with Schema

### Definition

`TypedDict` defines a schema for dicts, enabling type checking on dictionaries.
```python
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str
    email: str

user: User = {"id": 1, "name": "Alice", "email": "alice@example.com"}

# Type checking
print(user["name"])    # OK
print(user["age"])     # Type error: 'age' not in User
```

### Required vs Optional
```python
from typing import TypedDict, NotRequired

class User(TypedDict):
    id: int
    name: str
    email: NotRequired[str]  # Optional field

user1: User = {"id": 1, "name": "Alice"}              # OK
user2: User = {"id": 1, "name": "Bob", "email": "b"}  # OK
```

### Total=False
```python
from typing import TypedDict

class PartialUser(TypedDict, total=False):
    id: int
    name: str
    email: str

# All fields are optional
user: PartialUser = {"id": 1}  # OK
```

### Inheritance
```python
from typing import TypedDict

class BaseEntity(TypedDict):
    id: str
    created_at: str

class User(BaseEntity):
    name: str
    email: str

user: User = {
    "id": "123",
    "created_at": "2024-01-01",
    "name": "Alice",
    "email": "alice@example.com"
}
```

### Real-World Examples

**FastAPI - JSON Responses:**
```python
from typing import TypedDict
from fastapi import FastAPI

class UserResponse(TypedDict):
    id: int
    name: str
    email: str

class ErrorResponse(TypedDict):
    error: str
    detail: str

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> UserResponse | ErrorResponse:
    user = db.get(user_id)
    if not user:
        return {"error": "NotFound", "detail": "User not found"}
    return {"id": user.id, "name": user.name, "email": user.email}
```

**Pydantic - Config Dicts:**
```python
from typing import TypedDict
from pydantic import BaseModel

class DatabaseConfig(TypedDict):
    host: str
    port: int
    database: str

class Settings(BaseModel):
    db: DatabaseConfig
    debug: bool = False

config: DatabaseConfig = {
    "host": "localhost",
    "port": 5432,
    "database": "myapp"
}
settings = Settings(db=config)
```

**JSON Schema Validation:**
```python
from typing import TypedDict

class ApiRequest(TypedDict):
    method: str
    url: str
    headers: dict[str, str]
    body: str | None

def validate_request(request: dict) -> ApiRequest:
    # Runtime validation would go here
    return request  # type: ignore
```

### Established Use Cases

**JSON APIs without Pydantic**:
- Type hints for JSON payloads
- Lightweight alternative to BaseModel

**Config files** (YAML, TOML):
- Schema for loaded configurations

**Database rows**:
- Type hints for raw query results

**Structured kwargs**:
- Type checking on `**kwargs` with fixed schema

---

## Modern Union (|) - Python 3.10+

### New Syntax

Python 3.10+ allows `X | Y` instead of `Union[X, Y]`:
```python
# Old (Python < 3.10)
from typing import Union, Optional
def process(value: Union[str, int]) -> Optional[str]:
    ...

# Modern (Python 3.10+)
def process(value: str | int) -> str | None:
    ...
```

### Type Narrowing

Type checkers refine types automatically:
```python
def process(value: str | int) -> str:
    if isinstance(value, str):
        # mypy knows value is str here
        return value.upper()
    else:
        # mypy knows value is int here
        return str(value)
```

### Real-World Examples

**FastAPI - Flexible Parameters:**
```python
from fastapi import FastAPI, Query

@app.get("/items")
async def get_items(
    skip: int = 0,
    limit: int | None = None,  # Optional limit
    filter: str | list[str] | None = Query(None)  # String or list
) -> list[Item]:
    ...
```

**Pydantic - Flexible Fields:**
```python
from pydantic import BaseModel

class Article(BaseModel):
    title: str
    content: str
    tags: str | list[str]  # Accept single tag or list
    metadata: dict | None = None

# Works with both
article1 = Article(title="...", content="...", tags="python")
article2 = Article(title="...", content="...", tags=["python", "fastapi"])
```

### Established Use Cases

**Optional values**: `T | None` more concise than `Optional[T]`

**Multiple return types**: Functions that return different types

**Flexible inputs**: APIs that accept varied formats

---

## NewType - Distinct Types

### Definition

`NewType` creates distinct types based on existing types, preventing accidental mixing.
```python
from typing import NewType

UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)

def get_user(user_id: UserId) -> User:
    ...

def get_order(order_id: OrderId) -> Order:
    ...

user_id = UserId(123)
order_id = OrderId(456)

get_user(user_id)    # OK
get_user(order_id)   # Type error: OrderId is not UserId
get_user(123)        # Type error: int is not UserId
```

### Real-World Examples

**Database IDs:**
```python
from typing import NewType

UserId = NewType("UserId", str)
ProductId = NewType("ProductId", str)
OrderId = NewType("OrderId", str)

def link_order_to_user(user_id: UserId, order_id: OrderId) -> None:
    db.execute(
        "INSERT INTO user_orders VALUES (?, ?)",
        user_id, order_id
    )

# Prevents bugs
user = UserId("user_123")
product = ProductId("prod_456")
link_order_to_user(user, product)  # Type error!
```

### Established Use Cases

**Strongly-typed IDs**: Prevent mixing different types of IDs

**Units**: Differentiate values with the same representation but different meanings

---

## Final - Immutable Values

### Definition

`Final` indicates that a value should not be reassigned:
```python
from typing import Final

MAX_CONNECTIONS: Final = 100
API_VERSION: Final[str] = "v1"

# Type error
MAX_CONNECTIONS = 200
```

### Final Classes and Methods
```python
from typing import final

@final
class SealedClass:
    """Cannot be subclassed."""
    pass

class Base:
    @final
    def process(self) -> None:
        """Cannot be overridden."""
        pass
```

### Established Use Cases

**Constants**: Values that should not change

**Sealed classes**: Prevent unintended inheritance

**Template method pattern**: Methods that should not be overridden

---

## Annotated - Metadata in Types

### Definition

`Annotated` adds metadata to types without affecting type checking:
```python
from typing import Annotated

# Adds metadata
PositiveInt = Annotated[int, "must be positive"]
Username = Annotated[str, "alphanumeric only", "max 20 chars"]

def create_user(age: PositiveInt, name: Username) -> User:
    ...
```

### Real-World Examples

**FastAPI - Parameter Validation:**
```python
from typing import Annotated
from fastapi import FastAPI, Query

@app.get("/items")
async def get_items(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0
) -> list[Item]:
    ...
```

**Pydantic - Field Constraints:**
```python
from typing import Annotated
from pydantic import BaseModel, Field

class User(BaseModel):
    name: Annotated[str, Field(min_length=3, max_length=50)]
    age: Annotated[int, Field(ge=0, le=150)]
    email: Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]
```

### Established Use Cases

**Validation metadata** (FastAPI, Pydantic):
- Constraints on parameters

**Documentation**:
- Metadata for doc generation

**Custom type checking**:
- Additional information for custom linters

---

## ParamSpec - Type-Safe Decorators

### Definition

`ParamSpec` preserves signatures in decorators:
```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec("P")
T = TypeVar("T")

def log_calls(func: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def add(a: int, b: int) -> int:
    return a + b

# Type checker preserves signature
result: int = add(1, 2)  # OK
add("1", "2")  # Type error: expects int
```

### Real-World Examples

**Retry Decorator:**
```python
from typing import ParamSpec, TypeVar, Callable
import functools

P = ParamSpec("P")
T = TypeVar("T")

def retry(times: int) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times - 1:
                        raise
            raise RuntimeError("Unreachable")
        return wrapper
    return decorator

@retry(times=3)
async def fetch_data(url: str, timeout: int) -> dict:
    ...

# Signature preserved
data: dict = await fetch_data("https://...", timeout=30)
```

### Established Use Cases

**Generic decorators**: Preserve complex signatures

**Wrapper functions**: Type-safe wrappers

---

## References

- [PEP 544](https://peps.python.org/pep-0544/) - Protocols
- [PEP 585](https://peps.python.org/pep-0585/) - Built-in Generics
- [PEP 604](https://peps.python.org/pep-0604/) - Union with |
- [PEP 612](https://peps.python.org/pep-0612/) - ParamSpec
- [mypy documentation](https://mypy.readthedocs.io/)
