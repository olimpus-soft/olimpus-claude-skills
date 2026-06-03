# 🔴 Detección de Breaking Changes

Cargar siempre. Es la primera pregunta antes de aprobar cualquier PR.

---

## ¿Qué es un breaking change?

Cualquier modificación que haga que código existente (consumidores internos o externos) deje de funcionar sin cambios de su parte.

---

## 1. Contratos de API (endpoints públicos)

### Señales en el diff
```diff
# ❌ Remoción de endpoint
- router.get('/api/v1/users/:id', getUserById)

# ❌ Cambio de método HTTP
- router.get('/api/v1/orders', getOrders)
+ router.post('/api/v1/orders', getOrders)

# ❌ Cambio de path
- router.get('/api/v1/users', getUsers)
+ router.get('/api/v2/users', getUsers)
```

### Cambios en payload de respuesta
```diff
# ❌ Campo removido de la respuesta (consumidores que lo usan se rompen)
- user_id: userId,
- site_id: siteId,

# ❌ Renombrado de campo (equivale a remover + agregar)
- userId: user.id,
+ user_identifier: user.id,

# ✅ Campo nuevo (backward compatible si es opcional)
+ full_name: `${user.firstName} ${user.lastName}`,
```

### Checklist API
- [ ] ¿Se removió algún endpoint?
- [ ] ¿Cambió el método HTTP de algún endpoint?
- [ ] ¿Cambió el path de algún endpoint?
- [ ] ¿Se removieron campos de la respuesta?
- [ ] ¿Se renombraron campos en request o response?
- [ ] ¿Cambió el tipo de algún campo (ej: string → number)?
- [ ] ¿Se hicieron obligatorios campos antes opcionales?

---

## 2. Esquema de base de datos

```diff
# 🔴 CRÍTICO: columna NOT NULL sin default en tabla con datos
+ status VARCHAR(20) NOT NULL,   # ← rompe si hay filas existentes

# 🔴 CRÍTICO: remoción de columna
- user_token VARCHAR(255),

# 🔴 CRÍTICO: cambio de tipo incompatible
- amount DECIMAL(10,2),
+ amount VARCHAR(50),

# ⚠️ Revisar: índice nuevo en tabla grande (bloqueo)
+ CREATE INDEX idx_user_site ON orders(user_id, site_id);

# ✅ Backward compatible: columna nullable nueva
+ full_name VARCHAR(255) DEFAULT NULL,
```

### Checklist DB
- [ ] ¿Se eliminan columnas o tablas?
- [ ] ¿Se agrega columna NOT NULL sin default (con datos existentes)?
- [ ] ¿Cambia el tipo de alguna columna de forma incompatible?
- [ ] ¿Se crean índices en tablas grandes (puede causar lock)?
- [ ] ¿La migración tiene rollback definido?
- [ ] ¿Es un cambio de esquema multi-step (add nullable → populate → add constraint)?

---

## 3. Interfaces y contratos internos

```diff
# ❌ Agregar parámetro requerido a función pública
- function auditPending(userId, siteId, operation)
+ function auditPending(userId, siteId, operation, sourceApp)  # ← rompe todos los callers

# ❌ Cambiar tipo de retorno
- async function getUser(id): Promise<User>
+ async function getUser(id): Promise<User | null>  # callers que no manejan null se rompen

# ✅ Parámetro opcional (backward compatible)
+ function auditPending(userId, siteId, operation, sourceApp = '')
```

### Checklist funciones/módulos
- [ ] ¿Cambió la firma de funciones exportadas?
- [ ] ¿Se removieron exports de módulos?
- [ ] ¿Cambió el tipo de retorno de funciones públicas?
- [ ] ¿Se renombraron constantes o enums exportados?

---

## 4. Configuración y variables de entorno

```diff
# ❌ Variable de entorno renombrada sin backwards compat
- DB_HOST=
+ DATABASE_HOST=   # todos los ambientes deben actualizar config

# ❌ Nueva variable requerida sin default
+ JWT_SECRET=      # el deploy falla si no está definida
```

### Checklist config
- [ ] ¿Se renombraron variables de entorno?
- [ ] ¿Se agregaron variables requeridas sin valor por defecto?
- [ ] ¿Cambió el formato de algún archivo de configuración?

---

## 5. Dependencias

```diff
# ⚠️ Major version upgrade → puede tener breaking changes del proveedor
- "frontend-i18n": "5.8.1"
+ "frontend-i18n": "6.0.2"   # ← verificar changelog de la librería

# ⚠️ Remoción de dependencia usada por otros módulos
- "some-shared-lib": "1.2.0"
```

---

## 6. Formato del reporte de breaking changes

```markdown
### 🔴 BREAKING CHANGE: {descripción breve}

**Tipo:** API / DB Schema / Interfaz interna / Configuración / Dependencia
**Archivo:** `path/to/file.ext:línea`
**Impacto:** {quién se ve afectado — consumidores externos, otros servicios, etc.}

**Cambio:**
\`\`\`diff
- código anterior
+ código nuevo
\`\`\`

**Mitigación:**
- [ ] {paso 1}
- [ ] {paso 2}
```

---

## Regla de oro

> Un campo/endpoint/función **nuevo** raramente es un breaking change.
> Un campo/endpoint/función **removido o renombrado** casi siempre lo es.
