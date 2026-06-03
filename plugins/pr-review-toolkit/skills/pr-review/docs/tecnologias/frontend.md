# ⚛️ Análisis Técnico — React / Next.js / Vue / Frontend

Cargar cuando se detectan archivos `.jsx`/`.tsx`, `next.config.*` o `nuxt.config.*`. Complementa `03-tecnico-core.md`.

---

## 1. React Hooks — reglas y dependencias

```jsx
// ❌ Hook condicional — viola las reglas de hooks
if (condition) {
    const [state, setState] = useState(false);
}

// ❌ useEffect con dependencias faltantes
useEffect(() => {
    fetchData(userId);
}, []);  // userId debería estar en deps

// ✅ Dependencias correctas
useEffect(() => {
    fetchData(userId);
}, [userId]);

// ✅ Cleanup siempre que haya subscripciones/listeners
useEffect(() => {
    const sub = subscribe(id);
    return () => sub.unsubscribe();
}, [id]);
```

- [ ] ¿Hooks solo en top level (no dentro de `if`/`for`)?
- [ ] ¿`useEffect` tiene todas sus dependencias declaradas?
- [ ] ¿Hay cleanup en `useEffect` cuando corresponde?

---

## 2. Memorización

```jsx
// ✅ useMemo para cálculos costosos
const sortedItems = useMemo(() =>
    items.sort((a, b) => a.name.localeCompare(b.name)),
[items]);

// ✅ useCallback para funciones pasadas a children
const handleClick = useCallback(() => {
    doSomething(id);
}, [id]);
```

- [ ] ¿Se evita re-crear objetos/arrays en cada render sin memo?
- [ ] ¿`useCallback` para handlers pasados como props a componentes memorizados?

---

## 3. Estructura de componentes

```jsx
// ❌ Componente que hace todo (God Component)
function UserDashboard() {
    // fetch, estado, lógica de negocio, render...
}

// ✅ Separación de responsabilidades
function UserDashboard() {
    return (
        <Layout>
            <UserProfile />
            <OrderList />
            <NotificationPanel />
        </Layout>
    );
}
```

- [ ] ¿Componentes < 200 líneas?
- [ ] ¿Lógica de negocio en custom hooks, no en componentes?
- [ ] ¿Props drilling > 3 niveles → considerar Context o estado global?

---

## 4. Next.js — Server vs Client Components

```jsx
// ✅ Server Component (default App Router): fetch directo
async function UserList() {
    const users = await db.users.findMany();  // en servidor
    return <ul>{users.map(u => <li key={u.id}>{u.name}</li>)}</ul>;
}

// ✅ Client Component: solo cuando hay interactividad
'use client';
function Counter() {
    const [count, setCount] = useState(0);
    return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

- [ ] ¿`'use client'` solo donde hay interactividad (estado, eventos, hooks)?
- [ ] ¿Server Components hacen el fetching cuando es posible?
- [ ] ¿`next/image` para imágenes (no `<img>` plain)?

---

## 5. Performance frontend

```jsx
// ✅ Lazy loading para componentes pesados
const HeavyChart = lazy(() => import('./HeavyChart'));

function Dashboard() {
    return (
        <Suspense fallback={<Spinner />}>
            <HeavyChart />
        </Suspense>
    );
}

// ✅ Virtualización para listas largas (> 100 items)
import { useVirtualizer } from '@tanstack/react-virtual';
```

- [ ] ¿Componentes pesados usan `lazy()` + `Suspense`?
- [ ] ¿Listas largas (>100 items) usan virtualización?
- [ ] ¿Imágenes usan formato moderno (WebP/AVIF)?

---

## 6. TypeScript en React

```typescript
// ✅ Props bien tipadas
interface ButtonProps {
    variant: 'primary' | 'secondary';
    size?: 'sm' | 'md' | 'lg';
    onClick: () => void;
    children: React.ReactNode;
}

function Button({ variant, size = 'md', onClick, children }: ButtonProps) { ... }

// ✅ Event handlers tipados
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
};
```

- [ ] ¿No hay `any` en tipos de componentes?
- [ ] ¿Props de componentes tienen interfaces definidas?

---

## 7. Accesibilidad (a11y)

```jsx
// ✅ Imágenes con alt descriptivo
<Image src="/hero.jpg" alt="Descripción del héroe" />

// ✅ Botones con texto accesible
<button aria-label="Cerrar modal">
    <CloseIcon aria-hidden="true" />
</button>

// ✅ Formularios con labels asociados
<label htmlFor="email">Email</label>
<input id="email" type="email" aria-required="true" />
```

- [ ] ¿Imágenes tienen `alt`?
- [ ] ¿Botones/links tienen texto accesible o `aria-label`?
- [ ] ¿Formularios tienen labels asociados?

---

## 8. Testing frontend

```typescript
// ✅ React Testing Library — testear comportamiento, no implementación
import { render, screen, fireEvent } from '@testing-library/react';

it('should increment on click', () => {
    render(<Counter />);
    fireEvent.click(screen.getByRole('button', { name: /increment/i }));
    expect(screen.getByText('1')).toBeInTheDocument();
});
```

- [ ] ¿Tests usan `getByRole` / `getByText` (no `querySelector`)?
- [ ] ¿No se testea implementación interna (estado, refs)?

---

## 9. Checklist Frontend

- [ ] Hooks en top level (no condicionales)
- [ ] `useEffect` con dependencias completas y cleanup
- [ ] Componentes < 200 líneas, responsabilidad única
- [ ] `'use client'` mínimo en Next.js
- [ ] Lazy loading para componentes pesados
- [ ] TypeScript sin `any`
- [ ] Imágenes con `alt`, botones con texto accesible
- [ ] Tests con React Testing Library
