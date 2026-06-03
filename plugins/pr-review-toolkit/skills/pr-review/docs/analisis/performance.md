# ⚡ Análisis de Performance

Cargar siempre. Complementa `03-tecnico-core.md`.

---

## 1. N+1 Queries

El problema más frecuente y costoso en PRs con acceso a BD.

### Cómo detectarlo en el diff
Buscar loops que llamen a funciones que hacen queries:

```javascript
// ❌ N+1: 1 query para la lista + 1 por cada item
const orders = await ordersRepo.findAll();
for (const order of orders) {
    order.customer = await customersRepo.findById(order.customerId); // N queries
}

// ✅ Una sola query con JOIN
const orders = await ordersRepo.findAllWithCustomers();
```

```python
# ❌ Django N+1
for order in Order.objects.all():
    print(order.customer.name)  # query por cada iteración

# ✅ select_related / prefetch_related
for order in Order.objects.select_related('customer'):
    print(order.customer.name)
```

```java
// ❌ JPA N+1
orders.forEach(o -> System.out.println(o.getCustomer().getName()));

// ✅ JOIN FETCH
@Query("SELECT o FROM Order o JOIN FETCH o.customer")
List<Order> findAllWithCustomer();
```

### Checklist N+1
- [ ] ¿Hay loops que contengan llamadas a BD/servicios externos?
- [ ] ¿Se usan JOINs / eager loading donde corresponde?
- [ ] ¿Las queries de lista tienen límite o paginación?

---

## 2. Operaciones bloqueantes / síncronas en contextos async

```javascript
// ❌ Bloquea el event loop de Node.js
app.get('/data', async (req, res) => {
    const data = fs.readFileSync('./data.json');  // SÍNCRONO
    res.json(data);
});

// ✅ No bloquea
app.get('/data', async (req, res) => {
    const data = await fs.promises.readFile('./data.json');
    res.json(data);
});
```

```python
# ❌ FastAPI: llamada sync en handler async bloquea el event loop
@app.get("/users")
async def get_users():
    return requests.get("http://api.com/users")  # SYNC!

# ✅ Non-blocking
@app.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        return await client.get("http://api.com/users")
```

---

## 3. Operaciones paralelas vs secuenciales innecesarias

```javascript
// ❌ Secuencial innecesario (doble tiempo)
const user = await userService.findById(id);
const orders = await orderService.findByUser(id);

// ✅ Paralelo
const [user, orders] = await Promise.all([
    userService.findById(id),
    orderService.findByUser(id),
]);
```

```go
// ✅ Go: goroutines para operaciones independientes
var wg sync.WaitGroup
results := make(chan Result, 2)

wg.Add(2)
go func() { defer wg.Done(); results <- fetchUser(ctx, id) }()
go func() { defer wg.Done(); results <- fetchOrders(ctx, id) }()
wg.Wait()
```

---

## 4. Memory leaks

### JavaScript / Node.js
```javascript
// ❌ Event listener sin cleanup → memory leak
useEffect(() => {
    window.addEventListener('resize', handler);
    // Falta cleanup
}, []);

// ✅ Con cleanup
useEffect(() => {
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
}, []);

// ❌ Interval sin cleanup
const interval = setInterval(tick, 1000);
// Si el componente se desmonta, el interval sigue corriendo

// ✅ Con cleanup
useEffect(() => {
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
}, []);
```

### Go: goroutine leaks
```go
// ❌ Goroutine queda colgada si nadie lee el channel
go func() {
    ch <- expensiveOp()  // bloqueado para siempre si caller retornó
}()

// ✅ Context con cancelación
go func() {
    select {
    case ch <- expensiveOp():
    case <-ctx.Done():
        return
    }
}()
```

---

## 5. Tamaño de payload y bundle

### APIs
- [ ] ¿Las respuestas incluyen solo los campos necesarios?
- [ ] ¿Hay paginación en endpoints que devuelven listas?
- [ ] ¿Queries de búsqueda tienen límite máximo de resultados?

### Frontend
- [ ] ¿Se usa lazy loading para componentes pesados?
- [ ] ¿Las imágenes están optimizadas (formato, tamaño)?
- [ ] ¿Las dependencias nuevas aumentan significativamente el bundle?

---

## 6. Caché y re-fetching innecesario

```javascript
// ❌ Refetch en cada render
function Component({ userId }) {
    const [user, setUser] = useState(null);
    useEffect(() => {
        fetchUser(userId).then(setUser);
    }); // Sin array de dependencias → corre en cada render

// ✅ Solo cuando cambia userId
    useEffect(() => {
        fetchUser(userId).then(setUser);
    }, [userId]);
}
```

---

## 7. Checklist de performance

- [ ] ¿Hay N+1 queries en loops?
- [ ] ¿Operaciones independientes se ejecutan en paralelo?
- [ ] ¿No hay llamadas síncronas en contextos async?
- [ ] ¿Event listeners / intervals tienen cleanup?
- [ ] ¿Queries tienen límite/paginación?
- [ ] ¿No hay goroutine leaks (Go)?
- [ ] ¿Bundle size no aumenta sin justificación?
