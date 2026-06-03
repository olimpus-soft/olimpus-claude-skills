# 🟢 Análisis Técnico — Node.js / Express / NestJS

Cargar cuando se detecta `package.json`. Complementa `03-tecnico-core.md`.

---

## 1. TypeScript

- [ ] ¿Se evita `any`?
- [ ] ¿Interfaces/Types bien definidos?
- [ ] ¿Se usa `strict: true` en tsconfig?

```typescript
// ❌ Evitar
function process(data: any): any { return data.something; }

// ✅ Tipar correctamente
interface UserData { id: string; name: string; }
function process(data: UserData): string { return data.name; }
```

---

## 2. Express — patrones clave

### Async errors (punto crítico frecuente)
```javascript
// ❌ Si falla, el error no se captura → servidor cuelga
app.get('/users', async (req, res) => {
    const users = await User.findAll();
    res.json(users);
});

// ✅ Wrapper para capturar errores async
const asyncHandler = (fn) => (req, res, next) =>
    Promise.resolve(fn(req, res, next)).catch(next);

app.get('/users', asyncHandler(async (req, res) => {
    const users = await User.findAll();
    res.json(users);
}));
```

### Error handler centralizado
```javascript
// ✅ Un solo lugar para manejar errores
app.use((err, req, res, next) => {
    if (err instanceof ValidationError) return res.status(400).json({ error: err.message });
    res.status(500).json({ error: 'Internal server error' }); // no exponer stack trace
});
```

---

## 3. NestJS — estructura

- [ ] ¿Cada feature tiene su módulo?
- [ ] ¿Controllers solo manejan HTTP (no lógica de negocio)?
- [ ] ¿Services contienen la lógica?
- [ ] ¿DTOs con validación (`class-validator`)?
- [ ] ¿Guards para autenticación/autorización?

---

## 4. Async/Await

```javascript
// ❌ Operaciones secuenciales innecesarias
const user = await userService.findById(id);
const orders = await orderService.findByUser(id); // espera innecesariamente

// ✅ Operaciones paralelas
const [user, orders] = await Promise.all([
    userService.findById(id),
    orderService.findByUser(id),
]);
```

---

## 5. Variables de entorno

```javascript
// ✅ Validar al inicio (no descubrir errores en runtime)
const required = ['DATABASE_URL', 'JWT_SECRET', 'PORT'];
required.forEach(key => {
    if (!process.env[key]) throw new Error(`Missing env var: ${key}`);
});
```

---

## 6. Drizzle ORM — puntos de atención

- [ ] ¿Los campos del objeto pasado a `.values()` coinciden con las columnas del modelo? (Drizzle ignora campos extra silenciosamente → data loss)
- [ ] ¿Las migraciones de esquema están incluidas en el PR?
- [ ] ¿Queries de lista tienen límite/paginación?
- [ ] ¿Los tipos decimales para valores monetarios usan `decimal(15,2)`?

---

## 7. Checklist Node.js

- [ ] TypeScript con `strict: true`
- [ ] Error handling centralizado
- [ ] Async errors capturados con wrapper o try-catch
- [ ] Variables de entorno validadas al inicio
- [ ] Tests con Jest / Mocha (AAA pattern)
- [ ] Logging estructurado (no `console.log` en producción)
- [ ] No `any` en TypeScript
- [ ] Pools de conexiones configurados
