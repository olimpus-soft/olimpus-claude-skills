# BFF Clean Architecture

The BFF (Backend-For-Frontend) layer in Nordic apps follows Clean Architecture strictly.
Each domain module is self-contained with `domain/`, `application/`, and `infra/` layers.

---

## Module Structure

```
api/<module>/
  application/
    use-cases/
      get-something.use-case.ts      # One file per use case
      create-something.use-case.ts
  domain/
    entities/
      something.entity.ts            # Plain TypeScript class/interface
    repositories/
      something.repository.ts        # Interface only — no implementation
  infra/
    controller/
      something.controller.ts        # Wires use cases
    repositories/
      something.repository.impl.ts   # Implements domain interface
    schemas/
      something.schema.ts            # @meli/input-validation schemas
    router.ts                        # Express router
```

---

## Use Cases

Use cases are pure business logic. No HTTP, no Express, no framework dependencies.

```typescript
// application/use-cases/get-admin-config.use-case.ts
import type { AdminConfigRepository } from '../../domain/repositories/admin-config.repository';
import type { AdminConfig } from '../../domain/entities/admin-config.entity';

export class GetAdminConfigUseCase {
  constructor(private readonly repository: AdminConfigRepository) {}

  async execute(adminId: string): Promise<AdminConfig> {
    if (!adminId) {
      throw new InvalidParamError('adminId is required');
    }
    return this.repository.findById(adminId);
  }
}
```

**Rules:**
- Constructor receives repository interfaces, not implementations
- Throw `DomainError` subclasses for business rule violations
- Never import from `infra/` — dependency flows inward only

---

## Domain Entities and Repositories

```typescript
// domain/entities/admin-config.entity.ts
export interface AdminConfig {
  id: string;
  adminId: string;
  key: string;
  value: unknown;
  createdAt: Date;
}

// domain/repositories/admin-config.repository.ts
import type { AdminConfig } from '../entities/admin-config.entity';

export interface AdminConfigRepository {
  findById(adminId: string): Promise<AdminConfig>;
  save(config: AdminConfig): Promise<AdminConfig>;
  delete(adminId: string, key: string): Promise<void>;
}
```

---

## Controller — Manual Dependency Injection

```typescript
// infra/controller/admin-config.controller.ts
import type { Request, Response } from 'express';
import { GetAdminConfigUseCase } from '../../application/use-cases/get-admin-config.use-case';
import type { AdminConfigRepository } from '../../domain/repositories/admin-config.repository';

export class AdminConfigController {
  constructor(
    private readonly getAdminConfig: GetAdminConfigUseCase,
  ) {}

  async getConfig(req: Request, res: Response): Promise<void> {
    const { admin_id } = req.query as { admin_id: string };
    const result = await this.getAdminConfig.execute(admin_id);
    res.json(result);
  }
}

// --- Manual DI wiring at bottom of controller file ---
import { AdminConfigRepositoryImpl } from '../repositories/admin-config.repository.impl';

const repository: AdminConfigRepository = AdminConfigRepositoryImpl.getInstance();
const getAdminConfigUseCase = new GetAdminConfigUseCase(repository);
export const adminConfigController = new AdminConfigController(getAdminConfigUseCase);
```

**Rules:**
- Use cases instantiated at the bottom of the controller file
- Repository uses `getInstance()` — singleton per module, not per request
- Controllers have zero business logic

---

## Repository Implementation

```typescript
// infra/repositories/admin-config.repository.impl.ts
import type { AdminConfigRepository } from '../../domain/repositories/admin-config.repository';
import type { AdminConfig } from '../../domain/entities/admin-config.entity';
import { ExternalApiService } from '../../../shared/infra/services/external-api.service';
import { config } from 'config';

export class AdminConfigRepositoryImpl implements AdminConfigRepository {
  private static instance: AdminConfigRepositoryImpl;
  private readonly client: ExternalApiService;

  private constructor() {
    // ExternalApiService created ONCE in constructor, not per method call
    this.client = new ExternalApiService(
      config.get('apis.downstreamService.host'),
      config.get('apis.downstreamService.path'),
    );
  }

  static getInstance(): AdminConfigRepositoryImpl {
    if (!AdminConfigRepositoryImpl.instance) {
      AdminConfigRepositoryImpl.instance = new AdminConfigRepositoryImpl();
    }
    return AdminConfigRepositoryImpl.instance;
  }

  async findById(adminId: string): Promise<AdminConfig> {
    const response = await this.client.get<AdminConfig>('/config', { params: { adminId } });
    return response.data;
  }
}
```

**Critical rule:** Never create `ExternalApiService` (or any HTTP client) inside a method.
Create it once in the constructor. Creating per-request defeats connection pooling.

---

## Router

```typescript
// infra/router.ts
import { Router } from '@meli/express-server';
import { inputValidator } from '../../shared/infra/middleware/input-validator.middleware';
import { apiAuthorization } from '../../shared/infra/middleware/api-authorization.middleware';
import { adminConfigController } from './controller/admin-config.controller';
import { getAdminConfigSchema } from './schemas/admin-config.schema';
import { handleError } from '../../shared/infra/middleware/error-handler.middleware';

export const adminConfigRouter = Router();

adminConfigRouter.use(apiAuthorization('adminConfig'));

adminConfigRouter.get(
  '/get-config',
  inputValidator(getAdminConfigSchema),
  async (req, res) => {
    try {
      await adminConfigController.getConfig(req, res);
    } catch (err) {
      handleError(err, res);
    }
  },
);
```

---

## Shared — Error Handling

```typescript
// shared/domain/errors/domain-error.ts
export class DomainError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = this.constructor.name;
  }
}

export class InvalidParamError extends DomainError {
  constructor(message: string) {
    super(message, 400);
  }
}

export class NotFoundError extends DomainError {
  constructor(message: string) {
    super(message, 404);
  }
}

export class UnauthorizedError extends DomainError {
  constructor(message: string) {
    super(message, 403);
  }
}
```

```typescript
// shared/infra/middleware/error-handler.middleware.ts
import type { Response } from 'express';
import { AxiosError } from 'axios';
import { DomainError } from '../../domain/errors/domain-error';

export function handleError(err: unknown, res: Response): void {
  if (err instanceof DomainError) {
    res.status(err.statusCode).json({ error: err.message });
    return;
  }
  if (err instanceof AxiosError) {
    const status = err.response?.status ?? 500;
    res.status(status).json({ error: err.message });
    return;
  }
  res.status(500).json({ error: 'Internal server error' });
}
```

---

## Kraken Authorization

```typescript
// Global middleware on API router (api/index.ts)
import kraken from '@kraken/core';

apiRouter.use(krakenSessionResolver());
apiRouter.use(kraken.releaseOnMiddleend());
apiRouter.use(contextMiddleware);

// Per-module authorization
export function apiAuthorization(feature: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const permission = config.get(`adminFeaturesPermissions.${feature}`);
    if (!kraken.hasPermission(req, permission)) {
      throw new UnauthorizedError(`Missing permission: ${permission}`);
    }
    next();
  };
}
```

---

## Context Propagation (AsyncLocalStorage)

```typescript
// shared/utils/context-manager.ts
import { AsyncLocalStorage } from 'async_hooks';

interface RequestContext {
  authToken: string;
  apiScope: string;
  requestId: string;
}

const storage = new AsyncLocalStorage<RequestContext>();

export const ContextManager = {
  run: (context: RequestContext, fn: () => void) => storage.run(context, fn),
  get: (): RequestContext => {
    const ctx = storage.getStore();
    if (!ctx) throw new Error('No context available');
    return ctx;
  },
};

// All downstream HTTP calls use context headers:
const ctx = ContextManager.get();
headers['x-auth'] = ctx.authToken;
headers['x-api-scope'] = ctx.apiScope;
```
