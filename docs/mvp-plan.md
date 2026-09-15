# P Media Plus — Plan de implementación MVP

Build → test → validate → continue. Un bloque no empieza hasta que el anterior se puede enseñar.

Código en **repo nuevo** `pmediaplus`. Estos docs se copian allí. Este VPS no recibe la app.

---

## Principio

El riesgo está en el móvil del cliente, no en el panel. Por eso el orden es:

1. Hosts + DB
2. Un venue seedeado
3. Flujo público usable
4. IA + cobro
5. Venue admin
6. Super admin
7. Pulido
8. (1.5) Stripe / email cuando el piloto lo pida

No construir Stripe, Resend, tercer host, CMS de preguntas, CSV, SVG ni analytics con gráficos en estos bloques.

---

## Bloque 0 — Repo y cuentas

**Hacer**

- Crear GitHub `pmediaplus`
- Copiar `docs/architecture.md`, `database.md`, `mvp-plan.md`
- Proyecto Supabase vacío (región EU)
- Proyecto Vercel
- Dominio: wildcard `*.pmediaplus.com` → Vercel; `app.pmediaplus.com` como host de preview/prod
- Clave OpenAI del producto (no la de CDE)
- `npx create-next-app` App Router, TypeScript, Tailwind

**Probar**

- Push + deploy que pinta “ok” en Vercel

**Validar**

- Nadie está desplegando esto dentro del repo del VPS

---

## Bloque 1 — Dos hosts

**Hacer**

- `middleware.ts`: si `host === app.` → rutas `(app)`/`(admin)`/`login`; si es `{slug}.` y no está reservado → `(public)`
- Páginas placeholder: público “venue public ok”, app “app ok”
- Lista de slugs reservados

**Probar**

- `app.pmediaplus.com` (o `app.localhost:3000` con `/etc/hosts` / `lvh.me`)
- `restaurante-la-plaza.localhost:3000` → layout público
- `app.` no sirve el flujo cliente y un slug no sirve `/dashboard`

**Validar**

- Un solo deploy, dos skins por `Host`

---

## Bloque 2 — Migraciones + RLS + RPCs

**Hacer**

- SQL de [`database.md`](database.md): enums, tablas, índices, trigger de `profiles`, `credit_wallet`, `debit_wallet`
- RLS venue admin
- `revoke execute` de RPCs a `anon`/`authenticated`
- Cliente server `createServiceClient` vs `createUserClient`

**Probar**

- `supabase db reset` local o branch
- `credit_wallet` 5000 → `balance_cents = 5000` + 1 tx
- segundo `credit` con la misma `idempotency_key` no duplica
- `debit` de 100 → 4900; `debit` del mismo `review_id` no duplica
- `debit` 99999 → `insufficient_balance`
- Un JWT de venue A no `select` staff de venue B

**Validar**

- El dinero no se toca fuera de las RPCs

---

## Bloque 3 — Seed, sin panel

**Hacer**

- `seed.sql`: 1 venue, 2 staff, 4–5 productos, 50 € de saldo, 1 venue admin (o solo el super admin)
- Helper `getVenueBySubdomain(host)`
- Layout público: 404 amable si el slug no existe o `inactive`

**Probar**

- Abrir `{slug}` muestra el nombre del venue
- Subdomain inventado → no leak de datos

**Validar**

- Se puede trabajar el flujo cliente sin haber escrito `/dashboard`

---

## Bloque 4 — Flujo público (IA mock)

**Hacer**

- Pantalla de bienvenida + EMPEZAR → `POST /session`
- `/r/[code]` con Sí / No
- 4 preguntas, una por pantalla, mobile-first:
  1. Quién te ha atendido (staff activos + Otro)
  2. Qué has comido (multi productos activos + Otro)
  3. Qué destacarías (atención, calidad, ambiente, precio, rapidez)
  4. Valoración (neutral / buena / muy buena / excelente)
- `PATCH /session` con `answers_json`
- `POST /generate` **mock**: plantilla con los answers, sin OpenAI, **sin débito aún**
- Textarea + COPIAR + ABRIR GOOGLE (`google_review_url`, `target=_blank`)
- ¿Has publicado? → endpoint

**Probar**

- Completar en el teléfono (o DevTools 390px) en &lt; 1 min
- Copiar pega en un notepad
- ABRIR GOOGLE abre la URL
- Refresco a mitad de formulario: cookie de sesión recupera o se reinicia de forma predecible (documentar: reiniciar es OK en MVP)

**Validar**

- Se siente conversación, no un form de Bootstrap. Si no, no pasar al bloque 5

---

## Bloque 5 — OpenAI + débito

**Hacer**

- Sustituir mock por `gpt-4o-mini` + `PROMPT_VERSION = 1`
- Antes de llamar: si `balance < price` → status `blocked_no_balance`, UI “Este venue no tiene saldo disponible.”
- Insert `reviews` + `debit_wallet` + status `review_generated`
- Idempotencia: segundo `generate` de la misma sesión devuelve la review ya cobrada
- `sentiment` / `experience_score` desde la pregunta 4, no desde el LLM
- Timeout y `generation_failed` sin cobro

**Probar**

- Generar 3 reseñas del mismo input: textos distintos, 40–100 palabras, platos reales
- Saldo 50 €, precio 1 € → 49 € y 1 débito
- Forzar saldo 0 → 402, cero llamadas netas cobradas (si OpenAI se llama por error, no débito)
- Retry del botón no cobra dos veces

**Validar**

- El loop de producto ya existe. Aquí se puede enseñar el piloto a un restaurante amigo **aunque el panel sea el SQL editor**

---

## Bloque 6 — Venue admin

**Hacer**

- Magic link en `/login`
- Guard: solo `venue_users`
- `/dashboard`: saldo, reviews mes/histórico, coste, empleados, reviews por empleado, últimas 10, banner si saldo &lt; 5 €
- CRUD staff + `employee_code`
- `/qr`: QR general y por empleado, copiar URL, PNG (`qrcode` o similar). Sin SVG
- CRUD products
- `/settings`: nombre, google URL, `business_info`
- `/reviews`: lista texto + empleado + fecha + sentiment

**Probar**

- Login del admin del seed
- Alta “Lucía”, descargar PNG, escanear (o abrir URL) → preselección Lucía
- Añadir un plato y que salga en la pregunta 2
- Un segundo usuario sin `venue_users` no entra

**Validar**

- El dueño del restaurante puede operar sin ti ni SQL

---

## Bloque 7 — Super admin

**Hacer**

- `platform_role = super_admin` → `/admin`
- Crear venue (campos del PRD, sin logo obligatorio)
- Al crear: `venue_users` + `credit_wallet` saldo inicial
- Editar, activar/desactivar
- Listado venues con saldo
- `POST credit` ajuste manual
- Listado global de reviews (filtro por venue)

**Probar**

- Crear “Bar Prueba” con 10 €, entrar como su admin, generar 1 review, ver 9 €
- Desactivar → público muestra no disponible
- Venue admin **no** abre `/admin`

**Validar**

- Puedes dar de alta el segundo local sin tocar la base a mano

---

## Bloque 8 — Pulido del piloto

**Hacer**

- Rate limit IP en `generate` (10/h/venue)
- Estados `google_opened` / published bien guardados
- Empty states (0 empleados, 0 productos: el form sigue funcionando con “Otro”)
- Copy de error único y en español
- Favicon / nombre en la pestaña pública = nombre del venue

**Probar**

- Flujo entero en un iPhone real o al menos 390px + un Android UA
- 0 productos: se puede terminar con “Otro”
- Venue sin saldo: mensaje, no spinner eterno

**Validar**

- Checklist de lanzamiento piloto (abajo) en verde

---

## Bloque 9 — Fase 1.5 (solo si el piloto convierte)

No planificar sprint hasta ver las 10 reviews reales.

- Stripe Checkout paquetes 25/50/100/250 + webhook → `credit_wallet` con `idempotency_key = stripe:{event_id}` + tabla `payments`
- Resend: aviso saldo &lt; 5 € (máx. 1/24h)
- PNG+SVG, imprimir
- Segunda plantilla de preguntas (bar) si hace falta
- Turnstile si hay abuso
- Top productos / atributos en overview

---

## Orden exacto (una línea)

```text
0 repo/cuentas
→ 1 middleware 2 hosts
→ 2 SQL+RLS+RPC
→ 3 seed
→ 4 público mock
→ 5 OpenAI+débito
→ 6 venue admin
→ 7 super admin
→ 8 pulido
→ (1.5 Stripe/email)
```

---

## Checklist de lanzamiento piloto

- [ ] `{slug}.pmediaplus.com` abre el restaurante correcto
- [ ] QR de María preselecciona a María
- [ ] 4 preguntas en móvil, sin teclado innecesario (taps)
- [ ] La review se puede copiar y suena natural
- [ ] ABRIR GOOGLE va al review URL real
- [ ] Cada generate resta el precio y deja transacción
- [ ] Saldo 0 bloquea con el mensaje acordado
- [ ] El admin ve sus reviews y no las de otro venue
- [ ] Super admin crea un segundo venue aislado
- [ ] Venue `inactive` no genera

---

## Qué no hacer “de paso”

- No añadir Prisma
- No extraer `wallets` / `question_sets` “por si acaso”
- No landing marketing
- No i18n
- No regenerar
- No impersonate
- No meter este código en el repo del VPS
