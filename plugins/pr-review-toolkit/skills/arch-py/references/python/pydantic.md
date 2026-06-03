# Pydantic v2 - Python 3.10+

Complete technical reference for Pydantic v2. For decisions on when to use Pydantic vs dataclass vs TypedDict, consult the main skill (`/developer`).

## Fundamentals

Pydantic v2 is a library for data validation and parsing using type hints. It offers:
- Automatic runtime validation
- Serialization/deserialization (JSON, dict)
- Native FastAPI integration
- Performance (~5-50x faster than v1 due to Rust core)

**When to use:**
- Validating external data (APIs, configs, files)
- Application settings (environment variables)
- API schemas (FastAPI, request/response models)
- Parsing JSON with validation

**When NOT to use:**
- Internal domain objects without validation → dataclass
- Simple typed dicts → TypedDict
- Performance-critical paths without validation → dataclass with slots

---

## BaseModel

### Definition

Classes that inherit from `BaseModel` have automatic validation:
```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None

# Automatic validation
user = User(id=1, name="Alice", email="alice@example.com")

# Automatic type coercion
user2 = User(id="1", name="Bob", email="bob@example.com")  # id converted to int

# Validation fails
try:
    User(id="invalid", name="Charlie", email="charlie@example.com")
except ValueError as e:
    # ValidationError with details
    pass
```

### Automatic Validation
```python
from pydantic import BaseModel, ValidationError

class Product(BaseModel):
    name: str
    price: float
    stock: int

# Valid data
product = Product(name="Widget", price=19.99, stock=100)

# Type coercion
product2 = Product(name="Gadget", price="29.99", stock="50")  # Strings converted

# Validation fails
try:
    Product(name="Invalid", price="not-a-number", stock=10)
except ValidationError as e:
    print(e.errors())
    # [
    #     {
    #         'type': 'float_parsing',
    #         'loc': ('price',),
    #         'msg': 'Input should be a valid number',
    #         'input': 'not-a-number'
    #     }
    # ]
```

### Real-World Example

**FastAPI Request Model:**
```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    email: EmailStr  # Automatic email validation
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    age: int | None = Field(None, ge=0, le=150)

class UserResponse(BaseModel):
    """Response model (without password)."""
    id: int
    email: str
    name: str
    age: int | None
    created_at: datetime

# FastAPI endpoint
from fastapi import FastAPI

app = FastAPI()

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreateRequest) -> UserResponse:
    # user is already validated here
    # FastAPI + Pydantic perform automatic validation
    db_user = await db.create_user(user.model_dump())
    return UserResponse(**db_user)
```

---

## Field - Validations and Constraints

### Built-in Constraints
```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, le=1_000_000)  # gt=greater than, le=less equal
    stock: int = Field(ge=0)  # ge=greater equal
    sku: str = Field(pattern=r"^[A-Z]{3}-\d{4}$")  # Regex
    tags: list[str] = Field(default_factory=list, max_length=10)

# Automatic validation
product = Product(
    name="Widget",
    price=19.99,
    stock=100,
    sku="WDG-1234"
)

# Fails: negative price
try:
    Product(name="Invalid", price=-10, stock=0, sku="INV-0001")
except ValidationError:
    # price must be > 0
    pass
```

### Description and Examples
```python
from pydantic import BaseModel, Field

class APIConfig(BaseModel):
    """API configuration."""

    api_key: str = Field(
        description="API key for authentication",
        min_length=32,
        max_length=64,
        examples=["sk_test_abc123def456ghi789jkl012mno345"]
    )

    timeout: int = Field(
        default=30,
        description="Timeout in seconds",
        ge=1,
        le=300,
        examples=[30, 60, 120]
    )

    base_url: str = Field(
        default="https://api.example.com",
        description="Base URL of the API",
        examples=["https://api.example.com", "https://api-staging.example.com"]
    )
```

### Real-World Example

**Order Validation:**
```python
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

class OrderItem(BaseModel):
    product_id: str = Field(pattern=r"^prod-[a-z0-9]{8}$")
    quantity: int = Field(ge=1, le=1000)
    unit_price: Decimal = Field(gt=0, decimal_places=2)

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.quantity

class Order(BaseModel):
    order_id: str = Field(pattern=r"^ord-[a-z0-9]{12}$")
    customer_id: str = Field(pattern=r"^cust-[a-z0-9]{10}$")
    items: list[OrderItem] = Field(min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def total_amount(self) -> Decimal:
        return sum(item.total for item in self.items)

# Usage
order = Order(
    order_id="ord-abc123def456",
    customer_id="cust-xyz9876543",
    items=[
        OrderItem(product_id="prod-abc12345", quantity=2, unit_price=Decimal("19.99")),
        OrderItem(product_id="prod-def67890", quantity=1, unit_price=Decimal("49.99"))
    ]
)

print(order.total_amount)  # Decimal('89.97')
```

---

## @field_validator - Custom Validation

### Definition

Validates individual fields with custom logic:
```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    name: str
    email: str
    age: int

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Custom email validation."""
        if "@" not in v:
            raise ValueError("Email must contain @")
        if not v.endswith((".com", ".org", ".net")):
            raise ValueError("Email must end with .com, .org, or .net")
        return v.lower()  # Normalize to lowercase

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        """Age validation."""
        if v < 18:
            raise ValueError("User must be 18 or older")
        if v > 120:
            raise ValueError("Age must be realistic")
        return v

# Usage
user = User(name="Alice", email="ALICE@EXAMPLE.COM", age=25)
print(user.email)  # "alice@example.com" (normalized)

# Validation fails
try:
    User(name="Bob", email="bob@invalid.xyz", age=30)
except ValidationError:
    # Email must end with .com/.org/.net
    pass
```

### Mode: before vs after
```python
from pydantic import BaseModel, field_validator

class Product(BaseModel):
    name: str
    price: float

    @field_validator("price", mode="before")
    @classmethod
    def parse_price(cls, v):
        """Runs BEFORE type validation."""
        # Remove currency symbols
        if isinstance(v, str):
            v = v.replace("$", "").replace(",", "")
        return float(v)

    @field_validator("price", mode="after")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Runs AFTER type validation."""
        if v <= 0:
            raise ValueError("Price must be positive")
        return round(v, 2)  # Rounds to 2 decimal places

# Usage
product = Product(name="Widget", price="$1,234.567")
print(product.price)  # 1234.57 (parsed and rounded)
```

### Real-World Example

**Password Validation:**
```python
from pydantic import BaseModel, field_validator
import re

class UserRegistration(BaseModel):
    email: str
    password: str
    password_confirm: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normalize and validate email."""
        v = v.lower().strip()

        # Basic email regex
        pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validates password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain special character")

        return v
```

---

## @model_validator - Cross-Field Validation

### Definition

Validates multiple fields together:
```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode="after")
    def validate_date_range(self):
        """Validates that end_date >= start_date."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be >= start_date")
        return self

# Usage
valid = DateRange(start_date="2026-01-01", end_date="2026-12-31")

# Fails: end_date before start_date
try:
    DateRange(start_date="2026-12-31", end_date="2026-01-01")
except ValidationError:
    pass
```

### Real-World Example

**Password Confirmation:**
```python
from pydantic import BaseModel, model_validator, Field

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
    new_password_confirm: str = Field(min_length=8)

    @model_validator(mode="after")
    def validate_passwords(self):
        """Validates passwords."""
        # New password must differ from current
        if self.new_password == self.current_password:
            raise ValueError("New password must differ from current password")

        # Confirmation matches
        if self.new_password != self.new_password_confirm:
            raise ValueError("Password confirmation does not match")

        return self

# Usage
change = PasswordChange(
    current_password="OldPass123!",
    new_password="NewPass456!",
    new_password_confirm="NewPass456!"
)
```

**Business Rules Validation:**
```python
from pydantic import BaseModel, model_validator
from decimal import Decimal

class Invoice(BaseModel):
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal

    @model_validator(mode="after")
    def validate_calculations(self):
        """Validates invoice calculations."""
        # Tax amount correct
        expected_tax = self.subtotal * self.tax_rate
        if abs(self.tax_amount - expected_tax) > Decimal("0.01"):
            raise ValueError(
                f"Tax amount {self.tax_amount} does not match "
                f"expected {expected_tax}"
            )

        # Total correct
        expected_total = self.subtotal + self.tax_amount
        if abs(self.total - expected_total) > Decimal("0.01"):
            raise ValueError(
                f"Total {self.total} does not match "
                f"expected {expected_total}"
            )

        return self

# Usage
invoice = Invoice(
    subtotal=Decimal("100.00"),
    tax_rate=Decimal("0.10"),
    tax_amount=Decimal("10.00"),
    total=Decimal("110.00")
)
```

---

## @computed_field - Derived Fields

### Definition

Calculated fields included in serialization:
```python
from pydantic import BaseModel, computed_field
from datetime import date

class Person(BaseModel):
    first_name: str
    last_name: str
    birth_date: date

    @computed_field
    @property
    def full_name(self) -> str:
        """Derived full name."""
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def age(self) -> int:
        """Calculated age."""
        today = date.today()
        return today.year - self.birth_date.year

# Usage
person = Person(
    first_name="Alice",
    last_name="Smith",
    birth_date=date(1990, 5, 15)
)

print(person.full_name)  # "Alice Smith"
print(person.age)        # 36 (in 2026)

# Included in serialization
print(person.model_dump())
# {
#     'first_name': 'Alice',
#     'last_name': 'Smith',
#     'birth_date': date(1990, 5, 15),
#     'full_name': 'Alice Smith',
#     'age': 36
# }
```

### Real-World Example

**Order with Calculations:**
```python
from pydantic import BaseModel, computed_field
from decimal import Decimal

class OrderItem(BaseModel):
    product_name: str
    quantity: int
    unit_price: Decimal

    @computed_field
    @property
    def line_total(self) -> Decimal:
        return self.quantity * self.unit_price

class Order(BaseModel):
    order_id: str
    items: list[OrderItem]
    discount_percent: Decimal = Decimal("0")

    @computed_field
    @property
    def subtotal(self) -> Decimal:
        return sum(item.line_total for item in self.items)

    @computed_field
    @property
    def discount_amount(self) -> Decimal:
        return self.subtotal * (self.discount_percent / 100)

    @computed_field
    @property
    def total(self) -> Decimal:
        return self.subtotal - self.discount_amount

# Usage
order = Order(
    order_id="ord-123",
    items=[
        OrderItem(product_name="Widget", quantity=2, unit_price=Decimal("10.00")),
        OrderItem(product_name="Gadget", quantity=1, unit_price=Decimal("30.00"))
    ],
    discount_percent=Decimal("10")
)

print(order.model_dump())
# {
#     'order_id': 'ord-123',
#     'items': [...],
#     'discount_percent': Decimal('10'),
#     'subtotal': Decimal('50.00'),
#     'discount_amount': Decimal('5.00'),
#     'total': Decimal('45.00')
# }
```

---

## ConfigDict - Model Configuration

### Common Options
```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        # Strict validation (no type coercion)
        strict=False,

        # Extra fields are forbidden
        extra="forbid",  # "allow", "ignore", "forbid"

        # Validate on assignment
        validate_assignment=True,

        # Allow mutations (default True)
        frozen=False,

        # Populate by field name (not alias)
        populate_by_name=True,

        # JSON schema
        json_schema_extra={
            "examples": [
                {"id": 1, "name": "Alice", "email": "alice@example.com"}
            ]
        }
    )

    id: int
    name: str
    email: str

# extra="forbid" — extra fields raise an error
try:
    User(id=1, name="Alice", email="alice@example.com", unknown="field")
except ValidationError:
    # Extra inputs not allowed
    pass

# validate_assignment=True — validates on assignment
user = User(id=1, name="Alice", email="alice@example.com")
try:
    user.email = "invalid-email"  # Validation fails
except ValidationError:
    pass
```

### Real-World Example

**Strict API Models:**
```python
from pydantic import BaseModel, ConfigDict, Field

class StrictAPIRequest(BaseModel):
    """Request model with strict validation."""

    model_config = ConfigDict(
        extra="forbid",  # Reject unknown fields
        strict=True,     # No type coercion
        validate_assignment=True  # Validates on assignment
    )

    user_id: int
    action: str = Field(pattern=r"^(create|update|delete)$")

# Strict usage
request = StrictAPIRequest(user_id=123, action="create")

# Fails: extra field
try:
    StrictAPIRequest(user_id=123, action="create", extra_field="invalid")
except ValidationError:
    # extra="forbid" rejects
    pass

# Fails: type coercion disabled
try:
    StrictAPIRequest(user_id="123", action="create")  # String not accepted
except ValidationError:
    # strict=True: "123" is not converted to int
    pass
```

---

## Serialization

### model_dump()

Converts to dict:
```python
from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    name: str
    timestamp: datetime
    metadata: dict

event = Event(
    name="user.created",
    timestamp=datetime.now(),
    metadata={"user_id": 123}
)

# Default dict
data = event.model_dump()

# Exclude fields
data = event.model_dump(exclude={"metadata"})

# Include only certain fields
data = event.model_dump(include={"name", "timestamp"})

# Serialization mode
data = event.model_dump(mode="json")  # JSON-serializable types
```

### model_dump_json()

Converts directly to JSON string:
```python
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: int
    name: str
    created_at: datetime

user = User(id=1, name="Alice", created_at=datetime.now())

# JSON string
json_str = user.model_dump_json()
# '{"id":1,"name":"Alice","created_at":"2026-02-11T10:30:00.123456"}'

# Pretty print
json_str = user.model_dump_json(indent=2)

# Exclude fields
json_str = user.model_dump_json(exclude={"created_at"})
```

### Real-World Example

**API Response Serialization:**
```python
from pydantic import BaseModel, computed_field
from datetime import datetime
from decimal import Decimal

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime
    password_hash: str  # Should not be exposed

    @computed_field
    @property
    def is_new(self) -> bool:
        days_since_creation = (datetime.now() - self.created_at).days
        return days_since_creation < 7

# FastAPI endpoint
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> dict:
    db_user = await db.get_user(user_id)

    user = UserResponse(**db_user)

    # Serialize without sensitive fields
    return user.model_dump(
        exclude={"password_hash"},
        mode="json"
    )
    # {
    #     'id': 1,
    #     'name': 'Alice',
    #     'email': 'alice@example.com',
    #     'created_at': '2026-02-05T10:00:00',
    #     'is_new': True
    # }
```

---

## pydantic-settings

### BaseSettings

Manages application settings:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",  # APP_DATABASE_URL
        case_sensitive=False
    )

    # Database
    database_url: str
    database_pool_size: int = 10

    # API
    api_key: str
    api_timeout: int = 30

    # Features
    debug: bool = False
    log_level: str = "INFO"

# Loads from environment variables
settings = Settings()

# Or from .env file:
# APP_DATABASE_URL=postgresql://localhost/mydb
# APP_API_KEY=secret123
# APP_DEBUG=true
```

### Real-World Example

**Production Settings:**
```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class DatabaseSettings(BaseSettings):
    """Database configuration."""
    url: str
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = False

class RedisSettings(BaseSettings):
    """Redis configuration."""
    url: str = "redis://localhost:6379/0"
    max_connections: int = Field(default=50, ge=1, le=1000)

class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # DB__URL = database.url
        case_sensitive=False
    )

    # Application
    app_name: str = "MyApp"
    debug: bool = False
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR)$")

    # Nested settings
    database: DatabaseSettings
    redis: RedisSettings

    # Secrets
    secret_key: str = Field(min_length=32)

    # Paths
    data_dir: Path = Field(default=Path("/data"))

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, v: Path) -> Path:
        """Ensure data directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

# Usage
settings = Settings()

# .env file:
# DEBUG=true
# LOG_LEVEL=DEBUG
# SECRET_KEY=your-secret-key-here-at-least-32-chars
# DATABASE__URL=postgresql://localhost/mydb
# DATABASE__POOL_SIZE=20
# REDIS__URL=redis://localhost:6379/0
```

---

## FastAPI Integration

### Request/Response Models
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

app = FastAPI()

class UserCreate(BaseModel):
    """Request for creating a user."""
    email: EmailStr
    password: str = Field(min_length=8)
    name: str

class UserResponse(BaseModel):
    """Response with public data."""
    id: int
    email: str
    name: str
    created_at: datetime

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate) -> UserResponse:
    """
    Creates a new user.

    - Automatic request body validation
    - Automatic response with UserResponse schema
    """
    # user is already validated
    db_user = await db.create_user(
        email=user.email,
        password=hash_password(user.password),
        name=user.name
    )

    return UserResponse(**db_user)
```

### Dependency Injection with Validation
```python
from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel, Field

app = FastAPI()

class PaginationParams(BaseModel):
    """Validated pagination parameters."""
    page: int = Field(default=1, ge=1, le=1000)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

def get_pagination(
    page: int = Query(1, ge=1, le=1000),
    page_size: int = Query(20, ge=1, le=100)
) -> PaginationParams:
    """Dependency with validation."""
    return PaginationParams(page=page, page_size=page_size)

@app.get("/items")
async def list_items(
    pagination: PaginationParams = Depends(get_pagination)
) -> dict:
    items = await db.get_items(
        limit=pagination.page_size,
        offset=pagination.offset
    )
    return {"items": items, "page": pagination.page}
```

---

## Custom Types

### Creating Custom Types
```python
from pydantic import BaseModel, field_validator
from typing import Annotated
import re

class CPF(str):
    """Validated Brazilian CPF."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema

        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v: str) -> str:
        """Validates CPF."""
        # Remove formatting
        cpf = re.sub(r"[^\d]", "", v)

        if len(cpf) != 11:
            raise ValueError("CPF must have 11 digits")

        # Check digit validation (simplified)
        if cpf == cpf[0] * 11:
            raise ValueError("Invalid CPF")

        # Format: 000.000.000-00
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

class Person(BaseModel):
    name: str
    cpf: CPF

# Usage
person = Person(name="João", cpf="12345678901")
print(person.cpf)  # "123.456.789-01" (formatted)

# Automatic validation
try:
    Person(name="Maria", cpf="invalid")
except ValidationError:
    pass
```

---

## Performance Considerations

### Comparison: Pydantic v1 vs v2

Pydantic v2 is **5-50x faster** than v1 due to its Rust core:
```python
# Simple benchmark (indicative)
from pydantic import BaseModel
import time

class User(BaseModel):
    id: int
    name: str
    email: str

# Create 100k instances
start = time.perf_counter()
for i in range(100_000):
    User(id=i, name=f"User{i}", email=f"user{i}@example.com")
elapsed = time.perf_counter() - start

# Pydantic v1: ~2.5 seconds
# Pydantic v2: ~0.3 seconds (~8x faster)
```

### When Validation is Expensive

For trusted data, use `model_construct`:
```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

# Normal validation (slower)
user1 = User(id=1, name="Alice", email="alice@example.com")

# Bypass validation (faster)
user2 = User.model_construct(id=1, name="Alice", email="alice@example.com")

# Use model_construct when:
# - Data comes from a trusted source (database)
# - Performance critical
# - Data has already been validated
```

---

## Established Use Cases

### API Development (FastAPI)
```python
@app.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    ...
```

### Configuration Management
```python
class Settings(BaseSettings):
    database_url: str
    redis_url: str
```

### Data Parsing
```python
# Parse JSON with validation
user = User.model_validate_json(json_string)
```

### ETL Pipelines
```python
# Validate data from external source
for row in csv_reader:
    record = DataRecord(**row)  # Automatic validation
```

---

## Best Practices

✅ **Use validators for business rules**
```python
@field_validator("email")
@classmethod
def normalize_email(cls, v: str) -> str:
    return v.lower().strip()
```

✅ **Separate request/response models**
```python
class UserCreate(BaseModel):
    email: str
    password: str  # Input

class UserResponse(BaseModel):
    id: int
    email: str  # Output (without password)
```

✅ **Use computed_field for derived fields**
```python
@computed_field
@property
def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}"
```

✅ **Validate early, fail fast**
```python
# Validate at the entry point (API request)
@app.post("/users")
async def create_user(user: UserCreate):
    # user already validated here
```

❌ **Do not use Pydantic for complex domain models**
```python
# AVOID — too much business logic
class Order(BaseModel):
    def calculate_discount(self): ...
    def apply_coupon(self): ...
    def finalize(self): ...

# PREFER — dataclass or plain class
@dataclass
class Order:
    # Complex business logic
```

❌ **Do not validate trusted internal data**
```python
# AVOID — unnecessary overhead
for db_row in db.query():
    user = User(**db_row)  # Unnecessary validation

# USE — bypass validation
for db_row in db.query():
    user = User.model_construct(**db_row)
```

---

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI + Pydantic](https://fastapi.tiangolo.com/tutorial/body/)
