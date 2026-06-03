# 🐍 Análisis Técnico — Python / FastAPI / Django / Flask

Cargar cuando se detecta `requirements.txt`, `pyproject.toml` o `setup.py`. Complementa `03-tecnico-core.md`.

---

## 1. Type Hints

```python
# ❌ Sin type hints
def process_user(data):
    return data['name']

# ✅ Con type hints
def process_user(data: dict[str, Any]) -> str:
    return data['name']
```

- [ ] ¿Funciones públicas tienen type hints en parámetros y retorno?
- [ ] ¿Se usa `mypy` para verificación estática?

---

## 2. FastAPI — patrones clave

### Validación con Pydantic
```python
# ✅ Models tipados para request/response
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=0, le=150)
```

### Async/Await — no bloquear el event loop
```python
# ❌ Llamada síncrona en handler async → bloquea el event loop
@app.get("/users")
async def get_users():
    return requests.get("http://api.com/users")  # SÍNCRONO

# ✅ Non-blocking
@app.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        return await client.get("http://api.com/users")
```

- [ ] ¿Se usa `async def` para operaciones I/O?
- [ ] ¿No hay `requests.get()` dentro de `async def`?
- [ ] ¿Se usa `asyncio.gather()` para operaciones independientes en paralelo?

---

## 3. Django — ORM y migraciones

### N+1 en Django ORM
```python
# ❌ N+1: query por cada iteración
for order in Order.objects.all():
    print(order.customer.name)

# ✅ Optimizado con select_related
for order in Order.objects.select_related('customer'):
    print(order.customer.name)

# ✅ Para M2M o reverse FK
for order in Order.objects.prefetch_related('items'):
    print(order.items.all())
```

### Migraciones seguras
- [ ] ¿Las migraciones son reversibles (`reverse_sql` en RunSQL)?
- [ ] ¿Se evita agregar columna `NOT NULL` sin default en tabla con datos?
- [ ] ¿Índices en tablas grandes se crean con `CREATE INDEX CONCURRENTLY`?

### Seguridad Django
- [ ] ¿`@login_required` en vistas protegidas?
- [ ] ¿CSRF habilitado para formularios?

---

## 4. Context Managers y recursos

```python
# ✅ Siempre usar context managers para recursos
with open('file.txt') as f:
    data = f.read()

# ✅ Custom context manager
@contextmanager
def managed_connection():
    conn = acquire_connection()
    try:
        yield conn
    finally:
        conn.release()
```

---

## 5. Generators para memoria

```python
# ❌ Carga todo en memoria
def get_all_users():
    return [process(u) for u in million_users]

# ✅ Genera bajo demanda
def get_all_users():
    for u in million_users:
        yield process(u)
```

---

## 6. Manejo de excepciones

```python
# ❌ Catch genérico silencia errores
try:
    do_something()
except Exception:
    pass

# ✅ Excepciones específicas con logging
try:
    do_something()
except ValueError as e:
    logger.warning("Invalid value: %s", e)
    raise HTTPException(status_code=400, detail=str(e))
except ConnectionError as e:
    logger.error("Connection error: %s", e)
    raise HTTPException(status_code=503, detail="Service unavailable")
```

---

## 7. Testing con Pytest

```python
# ✅ Tests parametrizados para múltiples casos
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert uppercase(input) == expected

# ✅ Fixtures para setup
@pytest.fixture
def mock_user():
    return User(id=1, name="Test", email="test@example.com")

def test_process_user(mock_user):
    result = process_user(mock_user)
    assert result.name == "Test"
```

---

## 8. Checklist Python

- [ ] Type hints en funciones públicas
- [ ] No llamadas síncronas dentro de `async def`
- [ ] N+1 evitado con `select_related` / `prefetch_related`
- [ ] Migraciones reversibles y seguras para tablas con datos
- [ ] Context managers para recursos (archivos, conexiones, DB)
- [ ] Excepciones específicas (no `except Exception: pass`)
- [ ] Tests con pytest (no unittest), usando fixtures y `parametrize`
- [ ] `black`/`ruff` para formateo, `mypy` para tipos, `bandit` para seguridad
