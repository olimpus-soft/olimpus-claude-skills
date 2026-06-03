# Testing Patterns — MercadoLibre Frontend

Testing standards for Nordic SSR apps and BFF API layers.
Framework: **Jest + ts-jest + Testing Library**.

---

## Setup

```json
// jest.config.js (typical)
{
  "preset": "ts-jest",
  "testEnvironment": "node",         // BFF tests
  "testEnvironment": "jsdom",        // Frontend component tests
  "testMatch": ["**/__tests__/**/*.test.ts", "**/*.test.tsx"],
  "coverageThreshold": {
    "global": { "lines": 80 }
  }
}
```

---

## Test Co-location

```
api/<module>/
  application/use-cases/
    get-config.use-case.ts
    __tests__/
      get-config.use-case.test.ts    ← use case tests

  infra/controller/
    config.controller.ts
    __tests__/
      config.controller.test.ts     ← controller tests

  infra/repositories/
    config.repository.impl.ts
    __tests__/
      config.repository.impl.test.ts

app/nordic-pages/<feature>/
  index.tsx
  __tests__/
    index.test.tsx                  ← page component tests

  components/
    SearchBox.tsx
    SearchBox.test.tsx              ← co-located component test
```

---

## Use Case Tests

Use cases receive mocked repositories via constructor injection — no HTTP, no DB.

```typescript
// __tests__/get-admin-config.use-case.test.ts
import { GetAdminConfigUseCase } from '../get-admin-config.use-case';
import type { AdminConfigRepository } from '../../../domain/repositories/admin-config.repository';
import { InvalidParamError } from '../../../../shared/domain/errors/domain-error';

const mockRepository: jest.Mocked<AdminConfigRepository> = {
  findById: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};

describe('GetAdminConfigUseCase', () => {
  let useCase: GetAdminConfigUseCase;

  beforeEach(() => {
    jest.clearAllMocks();
    useCase = new GetAdminConfigUseCase(mockRepository);
  });

  it('should return config when adminId is valid', async () => {
    const expected = { id: '1', adminId: 'admin-123', key: 'feature', value: true };
    mockRepository.findById.mockResolvedValue(expected);

    const result = await useCase.execute('admin-123');

    expect(result).toEqual(expected);
    expect(mockRepository.findById).toHaveBeenCalledWith('admin-123');
  });

  it('should throw InvalidParamError when adminId is empty', async () => {
    await expect(useCase.execute('')).rejects.toThrow(InvalidParamError);
    expect(mockRepository.findById).not.toHaveBeenCalled();
  });
});
```

---

## Controller Tests

Test controllers by calling methods directly with mocked request/response objects.

```typescript
// __tests__/admin-config.controller.test.ts
import { AdminConfigController } from '../admin-config.controller';
import { GetAdminConfigUseCase } from '../../application/use-cases/get-admin-config.use-case';
import type { Request, Response } from 'express';

const mockGetAdminConfig = { execute: jest.fn() } as jest.Mocked<GetAdminConfigUseCase>;
const controller = new AdminConfigController(mockGetAdminConfig);

const mockRes = () => {
  const res = {} as Response;
  res.json = jest.fn().mockReturnValue(res);
  res.status = jest.fn().mockReturnValue(res);
  return res;
};

describe('AdminConfigController.getConfig', () => {
  it('should respond with config data', async () => {
    const req = { query: { admin_id: 'admin-123' } } as unknown as Request;
    const res = mockRes();
    const config = { id: '1', adminId: 'admin-123', key: 'feature', value: true };

    mockGetAdminConfig.execute.mockResolvedValue(config);

    await controller.getConfig(req, res);

    expect(res.json).toHaveBeenCalledWith(config);
  });
});
```

---

## Kraken Auth Testing Patterns

Authorization is security-critical — always test session resolution, permission enforcement, and the full middleware chain. The three Kraken middlewares form a pipeline: **session → release → authorization**.

### Session Resolution (`krakenSessionResolver`)

Test that session is correctly resolved from the `session_id` cookie, and that missing/invalid sessions are handled:

```typescript
// __tests__/kraken-session.middleware.test.ts
import kraken from '@kraken/core';
import { krakenSessionResolver } from '../kraken-session.middleware';

jest.mock('@kraken/core');

const mockReq = (cookies: Record<string, string> = {}) => ({
  cookies,
  session: undefined as unknown,
} as unknown as Request);

const mockRes = () => {
  const res = {} as Response;
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

describe('krakenSessionResolver', () => {
  beforeEach(() => jest.clearAllMocks());

  it('should resolve session and attach to request', async () => {
    const session = { userId: 'user-123', siteId: 'MLA' };
    (kraken.resolveSession as jest.Mock).mockResolvedValue(session);
    const req = mockReq({ session_id: 'valid-token' });
    const next = jest.fn();

    await krakenSessionResolver()(req, mockRes(), next);

    expect(kraken.resolveSession).toHaveBeenCalledWith('valid-token');
    expect(req.session).toEqual(session);
    expect(next).toHaveBeenCalled();
  });

  it('should return 401 when session_id cookie is missing', async () => {
    const req = mockReq({});
    const res = mockRes();
    const next = jest.fn();

    await krakenSessionResolver()(req, res, next);

    expect(res.status).toHaveBeenCalledWith(401);
    expect(next).not.toHaveBeenCalled();
  });

  it('should return 401 when session is expired or invalid', async () => {
    (kraken.resolveSession as jest.Mock).mockRejectedValue(
      new Error('Session expired'),
    );
    const req = mockReq({ session_id: 'expired-token' });
    const res = mockRes();
    const next = jest.fn();

    await krakenSessionResolver()(req, res, next);

    expect(res.status).toHaveBeenCalledWith(401);
    expect(next).not.toHaveBeenCalled();
  });
});
```

### Permission Enforcement (`apiAuthorization`)

Test both authorized and unauthorized cases, including edge cases like missing config keys:

```typescript
// __tests__/api-authorization.middleware.test.ts
import { apiAuthorization } from '../api-authorization.middleware';
import kraken from '@kraken/core';
import config from 'config';

jest.mock('@kraken/core');
jest.mock('config');

const mockReq = { session: { userId: 'user-123' } } as unknown as Request;
const mockRes = () => {
  const res = {} as Response;
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res;
};

describe('apiAuthorization', () => {
  beforeEach(() => jest.clearAllMocks());

  it('should call next when user has the required permission', () => {
    (config.get as jest.Mock).mockReturnValue('admin:myFeature:write');
    (kraken.hasPermission as jest.Mock).mockReturnValue(true);
    const next = jest.fn();

    apiAuthorization('myFeature')(mockReq, mockRes(), next);

    expect(kraken.hasPermission).toHaveBeenCalledWith(mockReq, 'admin:myFeature:write');
    expect(next).toHaveBeenCalled();
  });

  it('should throw UnauthorizedError when user lacks permission', () => {
    (config.get as jest.Mock).mockReturnValue('admin:myFeature:write');
    (kraken.hasPermission as jest.Mock).mockReturnValue(false);
    const next = jest.fn();

    expect(() => apiAuthorization('myFeature')(mockReq, mockRes(), next))
      .toThrow(UnauthorizedError);
    expect(next).not.toHaveBeenCalled();
  });

  it('should throw when permission key is not configured', () => {
    (config.get as jest.Mock).mockReturnValue(undefined);
    const next = jest.fn();

    expect(() => apiAuthorization('unknownFeature')(mockReq, mockRes(), next))
      .toThrow();
    expect(next).not.toHaveBeenCalled();
  });
});
```

### Full Middleware Chain (Session → Release → Authorization)

Test the complete auth pipeline as it runs in production — session resolution feeds into permission enforcement:

```typescript
// __tests__/auth-chain.integration.test.ts
import express from 'express';
import request from 'supertest';
import kraken from '@kraken/core';
import { krakenSessionResolver } from '../kraken-session.middleware';
import { apiAuthorization } from '../api-authorization.middleware';

jest.mock('@kraken/core');

function buildApp(feature: string) {
  const app = express();
  app.use(krakenSessionResolver());
  app.use(kraken.releaseOnMiddleend());
  app.get('/protected', apiAuthorization(feature), (_req, res) => {
    res.json({ ok: true });
  });
  return app;
}

describe('Auth middleware chain', () => {
  beforeEach(() => jest.clearAllMocks());

  it('should allow request with valid session and permission', async () => {
    (kraken.resolveSession as jest.Mock).mockResolvedValue({ userId: 'u1' });
    (kraken.releaseOnMiddleend as jest.Mock).mockImplementation(() =>
      (_req: Request, _res: Response, next: NextFunction) => next(),
    );
    (kraken.hasPermission as jest.Mock).mockReturnValue(true);

    const res = await request(buildApp('myFeature'))
      .get('/protected')
      .set('Cookie', 'session_id=valid-token');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ ok: true });
  });

  it('should reject at session layer when no cookie', async () => {
    const res = await request(buildApp('myFeature'))
      .get('/protected');

    expect(res.status).toBe(401);
  });

  it('should reject at authorization layer when no permission', async () => {
    (kraken.resolveSession as jest.Mock).mockResolvedValue({ userId: 'u1' });
    (kraken.releaseOnMiddleend as jest.Mock).mockImplementation(() =>
      (_req: Request, _res: Response, next: NextFunction) => next(),
    );
    (kraken.hasPermission as jest.Mock).mockReturnValue(false);

    const res = await request(buildApp('myFeature'))
      .get('/protected')
      .set('Cookie', 'session_id=valid-token');

    expect(res.status).toBe(403);
  });
});
```

### Kraken Auth Test Checklist

| Scenario | Must Test | Why |
|----------|-----------|-----|
| Valid session + valid permission | Yes | Happy path |
| Missing `session_id` cookie | Yes | Unauthenticated user |
| Expired / invalid session token | Yes | Token rotation, session timeout |
| Valid session + missing permission | Yes | Least-privilege enforcement |
| Permission key not in config | Yes | Misconfiguration detection |
| Multiple features with different permissions | Yes | Cross-module authorization isolation |
| `releaseOnMiddleend` propagation | Yes | Ensures Kraken context flows to downstream middleware |

---

## React Component Tests (Testing Library)

```typescript
// app/nordic-pages/my-feature/__tests__/index.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MyFeaturePage from '../index';

const defaultProps = {
  data: { items: [{ id: '1', name: 'Item One' }] },
};

describe('MyFeaturePage', () => {
  it('renders the page title', () => {
    render(<MyFeaturePage {...defaultProps} />);
    expect(screen.getByText('My Feature')).toBeInTheDocument();
  });

  it('renders all items', () => {
    render(<MyFeaturePage {...defaultProps} />);
    expect(screen.getByText('Item One')).toBeInTheDocument();
  });

  it('shows empty state when no items', () => {
    render(<MyFeaturePage data={{ items: [] }} />);
    expect(screen.getByText('No items found')).toBeInTheDocument();
  });
});
```

**Rules:**
- Test **behavior**, not implementation (do not test internal state)
- Query elements by role, label, or text — not by CSS class or data-testid (last resort)
- Never test Andes component internals — only test how your component uses them

---

## Mocking Downstream HTTP (Repository Tests)

```typescript
import nock from 'nock';
import { AdminConfigRepositoryImpl } from '../admin-config.repository.impl';

describe('AdminConfigRepositoryImpl', () => {
  afterEach(() => nock.cleanAll());

  it('should return config from downstream API', async () => {
    nock('https://downstream-service.mercadolibre.com')
      .get('/api/v1/config')
      .query({ adminId: 'admin-123' })
      .reply(200, { id: '1', adminId: 'admin-123', key: 'feature', value: true });

    const repo = AdminConfigRepositoryImpl.getInstance();
    const result = await repo.findById('admin-123');

    expect(result.adminId).toBe('admin-123');
  });
});
```

---

## Coverage Priorities

| Priority | What to cover |
|----------|--------------|
| **Critical** | Use cases, authorization middleware, error handler middleware |
| **High** | Controllers, repository implementations |
| **Medium** | Page components (happy path + empty state) |
| **Low** | Utility functions, mappers |

Modules with **zero tests** in order of risk:
1. Authorization middleware
2. Use cases in massive/bulk operation modules
3. File upload/download routes

---

## Running Tests

```bash
npm test                     # Run all tests
npm run test:watch           # Watch mode
npm test -- --coverage       # With coverage report
npm test -- path/to/file     # Single file
npm test -- --testNamePattern="pattern"  # Filter by test name
```
