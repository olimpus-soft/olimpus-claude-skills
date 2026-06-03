# TypeScript Conventions — MercadoLibre Frontend

Standards for TypeScript in Nordic (SSR frontend) and BFF (Express API) projects.

---

## Compiler Settings

```json
// tsconfig.json (recommended baseline)
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "CommonJS",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "./dist",
    "rootDir": "./",
    "baseUrl": ".",
    "jsx": "react"
  }
}
```

`strict: true` is mandatory. Never disable `noImplicitAny` or `strictNullChecks`.

---

## No `any`

```typescript
// ❌ WRONG
function process(data: any): any { ... }
const req: any = request;

// ✅ CORRECT — use unknown + narrowing
function process(data: unknown): ProcessedData {
  if (typeof data === 'string') { ... }
  if (isMyType(data)) { ... }
}

// ✅ CORRECT — use specific types
const req: Request<Params, ResBody, ReqBody, Query> = request;
```

**Exception**: third-party libraries with poor typings. Add a comment explaining why.

---

## Naming Conventions

| Construct | Convention | Example |
|-----------|-----------|---------|
| Variables, functions | camelCase | `adminConfig`, `getConfigById` |
| Classes, interfaces, types | PascalCase | `AdminConfig`, `ConfigRepository` |
| Enums | PascalCase | `OperationType` |
| Files | kebab-case | `admin-config.controller.ts` |
| Test files | same name + `.test.ts` | `admin-config.controller.test.ts` |
| React components | PascalCase file | `SearchBox.tsx` |

---

## Type-Only Imports

```typescript
// ✅ Use import type for type-only dependencies
import type { Request, Response, NextFunction } from 'express';
import type { AdminConfig } from '../domain/entities/admin-config.entity';

// Only use regular import when you need the runtime value
import { DomainError } from '../domain/errors/domain-error';
```

---

## Express Typing

Always use Express generics instead of `req: any`, `res: any`:

```typescript
import type { Request, Response, NextFunction } from 'express';

// Route handler with typed query params
type GetConfigQuery = { admin_id: string; filter?: string };

const getConfig = async (
  req: Request<{}, {}, {}, GetConfigQuery>,
  res: Response,
): Promise<void> => {
  const { admin_id } = req.query; // typed
  // ...
};

// With body
type CreateConfigBody = { key: string; value: unknown };

const createConfig = async (
  req: Request<{}, {}, CreateConfigBody>,
  res: Response,
): Promise<void> => {
  const { key, value } = req.body; // typed
  // ...
};
```

---

## DTOs

Define explicit DTOs for all API request/response contracts:

```typescript
// infra/dto/create-config.dto.ts
export interface CreateAdminConfigDTO {
  adminId: string;
  key: string;
  value: unknown;
  requestedBy: string;
}

export interface AdminConfigResponseDTO {
  id: string;
  adminId: string;
  key: string;
  value: unknown;
  createdAt: string; // ISO string for JSON transport
}
```

Never use `req.body as SomeType` without prior validation middleware. The validation
middleware guarantees the shape — then cast with confidence:

```typescript
// ✅ Safe cast — input-validator middleware already validated the shape
const body = req.body as CreateAdminConfigDTO;
```

---

## Formidable Types

When using formidable for file uploads, use proper types:

```typescript
import formidable, { type Fields, type Files } from 'formidable';

const parseForm = (req: Request): Promise<{ fields: Fields; files: Files }> => {
  return new Promise((resolve, reject) => {
    const form = formidable({ multiples: false, maxFileSize: 10 * 1024 * 1024 });
    form.parse(req, (err, fields, files) => {
      if (err) reject(err);
      else resolve({ fields, files });
    });
  });
};
```

---

## Error Handling — catch (e: unknown)

```typescript
// ❌ WRONG
try {
  await doSomething();
} catch (e: any) {
  console.log(e.message); // unsafe
}

// ✅ CORRECT
try {
  await doSomething();
} catch (e: unknown) {
  if (e instanceof Error) {
    logger.error('Operation failed', { message: e.message, stack: e.stack });
  }
}
```

---

## Logging

Use `@billing-core/logger` for all server-side logging. Never use `console.log` in production code.

```typescript
import { trackError, trackInfo, incrementMetric } from '@billing-core/logger';

// ✅ Structured logging
trackInfo('admin.config.fetched', { adminId, configKey });
trackError('admin.config.fetch_failed', error, { adminId });
incrementMetric('admin.config.requests');

// ❌ WRONG in production code
console.log('fetching config for', adminId);
console.log('error:', error);
```

**Exceptions:** `console.log` is acceptable only in:
- Local development scripts
- `newrelic.js` initialization (before logger is available)
- `config/secrets-client.ts` initialization

---

## ESLint Configuration (v9 flat config)

```javascript
// eslint.config.mjs
import meliConfig from '@meli-lint/eslint-config-base-ts';

export default [
  ...meliConfig,
  {
    rules: {
      complexity: ['error', 20],   // Max complexity 20 (not 60)
      '@typescript-eslint/no-explicit-any': 'error',
    },
  },
];
```

- Complexity limit **20** is the recommended maximum. 60 (seen in some projects) is too permissive.
- Never disable `@typescript-eslint/prefer-promise-reject-errors` at the file level — fix the underlying issue.
