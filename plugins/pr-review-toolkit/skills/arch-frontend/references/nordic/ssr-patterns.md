# Nordic SSR Patterns

Nordic is MercadoLibre's internal SSR framework (v9.7.x) built on React, Express, Webpack, and Node.js.
It provides SSR, CSR, Fast Refresh, SASS preprocessing, code splitting, and automatic CDN asset upload.

---

## Server Bootstrap

### Ragnar Server

The entry point wires the BFF API router and the SSR app router through the Ragnar server:

```typescript
// init.ts
import { createRagnarServer } from 'nordic/server';
import { apiRouter } from './api';
import { appRouter } from './app/server';

const server = createRagnarServer({
  apiRouter,
  appRouter,
});

server.start();
```

- `apiRouter` — Express Router with all BFF endpoints (under `/api` prefix)
- `appRouter` — Nordic SSR router with Kraken auth wiring
- `index.ts` loads dotenv, New Relic, Babel register, then calls `init.ts`

### App Router with Kraken

```typescript
// app/server/index.ts
import kraken from '@kraken/core';
import { Router } from '@meli/express-server';

const router = Router();

router.use(kraken.initialize());
router.use(kraken.session());

// Mount Nordic page routes
router.get('/path', krakenAuth, pageHandler);

export const appRouter = router;
```

---

## Nordic Pages

Each route corresponds to a folder in `app/nordic-pages/`. The folder contains:

```
app/nordic-pages/<feature>/
  index.tsx          # Page root component (SSR entry)
  components/        # Sub-components for this page
  __tests__/         # Jest + Testing Library tests
```

### Page Component Pattern

```tsx
// app/nordic-pages/my-feature/index.tsx
import React from 'react';

interface Props {
  data: MyFeatureData;
}

const MyFeaturePage: React.FC<Props> = ({ data }) => {
  return (
    <div>
      {/* page content */}
    </div>
  );
};

export default MyFeaturePage;
```

### Server-Side Data Fetching

In Nordic, server-side data is passed as props to page components. The pattern uses the
app service layer to call BFF endpoints before render:

```typescript
// app/services/my-feature.service.ts
import { restclient } from 'nordic/restclient';

export const getMyFeatureData = async (params: Params): Promise<MyFeatureData> => {
  const response = await restclient.get('/api/my-feature', { params });
  return response.data;
};
```

---

## Configuration — `config/default.js`

All Nordic configuration lives in `config/default.js`. Environment-specific overrides
come from Fury JSON configs loaded at runtime.

```javascript
// config/default.js
module.exports = {
  // API connections (injected by Fury platform per scope)
  apis: {
    downstreamService: {
      host: 'https://service.mercadolibre.com',
      path: '/api/v1',
      scope: 'service-scope',
      timeout: 5000,
    },
  },

  // Permission keys for Kraken authorization
  adminFeaturesPermissions: {
    myFeature: 'my-feature-permission-key',
  },

  // Object storage buckets
  objectStorageOwned: {
    storageName: process.env.STORAGE_SERVICE || 'my-storage-test',
  },
};
```

**Rules:**
- Never duplicate config keys — silent overwrites cause hard-to-debug issues
- Fury injects `apis.*.host` and `apis.*.path` per environment scope
- Permissions must match the keys configured in Kraken

---

## i18n (Translations)

Translation files live in `app/translations/` as JSON files:

```
app/translations/
  pt-BR.json
  es.json
  en.json
```

Usage in components:

```tsx
import { useTranslation } from 'nordic/i18n';

const MyComponent = () => {
  const { t } = useTranslation();
  return <span>{t('my_key')}</span>;
};
```

Always add translation keys to **all** locale files, not just pt-BR.

---

## SCSS / Styles

- Global styles in `app/styles/`
- Component-scoped styles via CSS Modules (`.module.scss`) co-located with components
- Never override Andes component styles with custom CSS — use component props/classNames API
- Stylelint enforces style conventions

---

## Docker / Runtime

- **Dev**: `hub.furycloud.io/mercadolibre/distroless-node-dev:24-mini` — ports 8080, 8443
- **Prod**: `hub.furycloud.io/mercadolibre/distroless-node:24-mini`
- Node.js 24 (distroless means no shell — avoid shell-dependent scripts in runtime)
- Environment variable `SCOPE` selects the Fury config file (`prod`, `test`, `stage`)

---

## Fury Environment Configs

```
configs/
  latest/
    prod.json      # Production values (API hosts, storage names, etc.)
    test.json      # Test environment values
```

These files are loaded by Nordic config system based on `SCOPE` env var.
They are **not secrets** — secrets come from `node-melitk-secrets`.

---

## New Relic APM

- Agent enabled only when `NODE_ENV=production`
- Configured in `newrelic.js` at project root
- App name from `APPLICATION` env var or `package.json` name
- License key injected by Fury platform as `NEW_RELIC_LICENSE_KEY`
- Ignores `/ping` endpoint
