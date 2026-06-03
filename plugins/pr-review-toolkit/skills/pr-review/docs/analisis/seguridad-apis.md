# 🔐 Análisis de Seguridad — APIs REST/GraphQL

Complementa `01-seguridad-core.md`. Cargar cuando el PR toca endpoints.

---

## 1. Autenticación y autorización

- [ ] ¿Todos los endpoints sensibles requieren autenticación?
- [ ] ¿Se validan permisos por recurso (no solo por usuario)?
- [ ] ¿Los tokens tienen expiración razonable?
- [ ] ¿Se valida el signature de JWTs?
- [ ] ¿Hay rate limiting por usuario/IP?

---

## 2. CORS

```javascript
// ❌ PELIGROSO
app.use(cors({ origin: '*' }));
app.use(cors({ origin: req.headers.origin })); // refleja sin validar

// ✅ SEGURO
const allowedOrigins = ['https://app.company.com'];
app.use(cors({
    origin: (origin, callback) => {
        if (!origin || allowedOrigins.includes(origin)) callback(null, true);
        else callback(new Error('CORS no permitido'));
    },
    credentials: true
}));
```

- [ ] ¿CORS tiene whitelist de orígenes específicos?
- [ ] ¿Se evita `Access-Control-Allow-Origin: *` con credentials?
- [ ] ¿Se limitan los métodos y headers permitidos?

---

## 3. Rate Limiting

- [ ] ¿Hay rate limiting global?
- [ ] ¿Endpoints sensibles (login, registro) tienen límites más estrictos?
- [ ] ¿Se limitan operaciones costosas (búsquedas, exports)?
- [ ] ¿El rate limit considera IP y usuario?

---

## 4. Exposición de información

- [ ] ¿Los errores 500 ocultan detalles técnicos (no exponen stack trace)?
- [ ] ¿Se eliminan headers como `X-Powered-By`?
- [ ] ¿Los endpoints de health/debug están protegidos?
- [ ] ¿Se usan UUIDs en lugar de IDs secuenciales?

---

## 5. Inyecciones SQL / NoSQL

```javascript
// ❌ SQL injection
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ Query parametrizada
const query = 'SELECT * FROM users WHERE id = ?';
db.execute(query, [userId]);

// ❌ NoSQL injection
db.users.find({ username: req.body.username });

// ✅ Validación de tipo primero
if (typeof req.body.username !== 'string') throw new Error('Invalid input');
```

---

## 6. Logging de APIs — qué NO loggear

- ❌ Passwords, tokens, API keys
- ❌ Datos de tarjetas de crédito
- ❌ PII sensible (documentos de identidad, etc.)

- [ ] ¿Se filtran datos sensibles de los logs?
- [ ] ¿Los logs incluyen correlation ID?
- [ ] ¿Se loggean intentos de acceso fallidos?
