# 🔒 Análisis de Seguridad — Core

Aplica a **todas las tecnologías**. Siempre cargar este módulo.

---

## 1. SSRF (Server-Side Request Forgery)

### Patrones peligrosos
```python
# ❌ URL dinámica sin validación
url = f"http://{user_input}/api/data"
requests.get(url)

# ❌ Redirección abierta
redirect_url = request.params.get('url')
return redirect(redirect_url)
```

### Patrones seguros
```python
# ✅ Whitelist de dominios
ALLOWED_HOSTS = ['api.trusted.com', 'internal.company.com']
if urlparse(url).netloc not in ALLOWED_HOSTS:
    raise SecurityError("Host no permitido")
```

### Checklist SSRF
- [ ] ¿URLs dinámicas tienen whitelist de dominios?
- [ ] ¿Se valida el esquema (http/https únicamente)?
- [ ] ¿Hay timeout en requests externos?
- [ ] ¿Se bloquean IPs privadas/localhost?

---

## 2. Validación de input

- [ ] ¿Todos los inputs tienen validación de tipo?
- [ ] ¿Hay límites de tamaño para strings/arrays?
- [ ] ¿Se escapan caracteres especiales?
- [ ] ¿Se validan formatos (email, URL, etc.)?

---

## 3. Credenciales y secrets

### Patrones a detectar
```regex
(api[_-]?key|apikey|secret|password|token|credential)[\s]*[=:][\s]*['"](.[^'"]+)['"]
AWS[A-Z0-9]{20}
ghp_[a-zA-Z0-9]{36}
```

### Checklist
- [ ] ¿Hay secrets hardcodeados?
- [ ] ¿Se usan variables de entorno para config sensible?
- [ ] ¿Están los archivos `.env` en `.gitignore`?
- [ ] ¿Se loggean datos sensibles?

---

## 4. Dependencias

```bash
npm audit              # Node.js
pip-audit              # Python
mvn dependency-check:check  # Java
govulncheck ./...      # Go
```

- [ ] ¿Hay CVEs conocidos en dependencias nuevas?
- [ ] ¿Las versiones actualizadas son compatibles?

---

## Formato de reporte por hallazgo

```markdown
### 🔴 [CRÍTICO/ALTO/MEDIO/BAJO] — {Tipo de Vulnerabilidad}

**Archivo:** `path/to/file.ext:línea`

**Código problemático:**
\`\`\`
{código vulnerable}
\`\`\`

**Riesgo:** {descripción}
**Remediación:** {código corregido}
```
