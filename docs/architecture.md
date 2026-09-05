# P Media Plus — Product Requirements & Architecture

Documento de diseño del SaaS multi-tenant de reseñas para venues.
Producto nuevo, **repositorio propio** (no mezclar con este VPS ni con CDE).
Este archivo es la fuente de verdad de producto y arquitectura. El esquema SQL está en [`database.md`](database.md). El orden de implementación está en [`mvp-plan.md`](mvp-plan.md).

**Estado:** diseño aprobado. No hay código de la app en este repo.

---

## 0. Decisiones cerradas

| Decisión | Valor |
|---|---|
| Stack | Next.js 15 App Router, Route Handlers, Supabase (Postgres + Auth + RLS), OpenAI, Vercel |
| Hosts MVP | 2: `{slug}.pmediaplus.com` (público) y `app.pmediaplus.com` (venue + super admin) |
| `admin.pmediaplus.com` | Reservado, no se implementa aún |
| Stripe | Fuera del MVP. Crédito de wallet **manual**. Checkout = fase 1.5 |
| Resend / emails | Fuera del MVP. Alerta de saldo = banner in-app |
| Vertical piloto | Solo restaurante |
| Idioma | `es` |
| Moneda | EUR, importes en céntimos enteros |
| Cobro | Al pasar a `review_generated`. Campo `billing_event` deja cambiarlo luego |
| Staff | Entidad con QR. Sin login |
| Preguntas | 4, hardcoded de restaurante. Sin CMS / sin IA de preguntas |
| Regenerar review | No en MVP |
| Impersonación | No en MVP |
| Código | Repo GitHub nuevo `pmediaplus`. Este workspace solo guarda el diseño |

No se cambia el stack. Un backend separado (Nest, Fastify) no aporta nada al piloto. Prisma se evita: convive mal con RLS y con débitos atómicos de wallet.

---

## 1. Product Requirements Document

### 1.1 Problema

El cliente de un restaurante quiere dejar una reseña en Google y no sabe qué escribir. El negocio quiere más reseñas y saber **quién atendió**.

Hoy el QR genérico de Google abre un recuadro vacío. La fricción mata la conversión. Además la reseña no se atribuye al camarero.

### 1.2 Promesa del piloto

Escanear un QR → 30–60 segundos de preguntas en el móvil → un texto natural listo para copiar → abrir la URL de reseña de Google.

El restaurante paga por review **generada**, desde un saldo prepago.

### 1.3 Qué hay que validar (y qué no)

Validar:

1. Un cliente real completa el flujo en el móvil.
2. El texto se siente humano y se puede publicar.
3. El venue entiende saldo, empleados y reseñas atribuidas.

No validar aún: pagos self-serve, emails, otros verticales, rankings, si la reseña acaba en Google (no hay forma fiable).

### 1.4 Actores

| Actor | Login | Dónde |
|---|---|---|
| Super admin | Sí | `app.pmediaplus.com/admin` |
| Venue admin | Sí | `app.pmediaplus.com/dashboard` |
| Cliente final | No | `{slug}.pmediaplus.com` |
| Staff | No | Solo aparece en QR y en el formulario |

### 1.5 Alcance MVP

**Dentro**

- Multi-tenant real (`venue_id` + RLS), aunque el piloto tenga 1–2 venues
- Super admin mínimo: crear venue, on/off, precio por review, cargar saldo a mano, listar reviews
- Venue admin: overview, empleados, menú manual, QR (URL + PNG), reviews, settings, banner de saldo bajo
- Flujo público mobile-first, 4 preguntas, conversacional
- Generación OpenAI (`gpt-4o-mini`)
- Copiar al clipboard + abrir Google Review URL
- Tracking de estados (incluido “¿has publicado?”)
- Wallet: débito atómico al generar; bloqueo si no hay saldo

**Fuera (fase 1.5 / 2 / 3)**

- Stripe, paquetes 25/50/100/250, webhooks
- Resend (invites, low-balance email)
- Host `admin.`, impersonación, audit log
- Preguntas por tipo de venue, motor `question_sets`, condicional postre, “¿primera visita?”
- CSV / texto / URL / PDF de menú
- Fotos de staff y logo en Storage (una URL opcional basta)
- QR SVG, imprimir, diseñador
- Página Analytics con gráficos
- Regenerar versión
- Landing en el apex
- i18n, login de staff, rewards, POS, cadenas, white-label, Turnstile

### 1.6 Requisitos funcionales (piloto)

**Super admin**

- Crear venue: nombre, slug, subdominio, tipo (`restaurant` en piloto), dirección, web, Google Review URL, email del admin, precio por review, saldo inicial, idioma `es`, activo/inactivo
- Editar esos campos, activar/desactivar
- Ver venues, saldo, reviews, usuarios vinculados
- Ajuste manual de saldo (`manual_adjustment`)
- Precio por review a nivel de venue (no hace falta panel global de pricing)

**Venue admin**

- Overview: saldo, reviews del mes, histórico, coste acumulado del mes, nº empleados, reviews por empleado, recientes, alerta si saldo &lt; 5 €
- CRUD empleados: nombre, apellido opcional, posición, activo, `employee_code`
- QR general y por empleado: ver, copiar URL, descargar PNG
- Productos: nombre, descripción, categoría (texto), activo
- Información del negocio: un textarea (descripción / especialidades / ambiente). Alimenta el prompt
- Settings: Google Review URL, nombre público
- Recarga: no hay botón Stripe. Copy: “Contacta para recargar” o el super admin carga

**Cliente**

- Bienvenida → EMPEZAR → 4 preguntas (una a una) → generar → textarea editable → COPIAR → ABRIR GOOGLE → “¿Has publicado?” Sí / Todavía no
- Si entra por `/r/{code}`: preselección “¿Te ha atendido {nombre}?” Sí / No, otra persona
- Sin cuenta
- Si el venue está inactivo o sin saldo: mensaje claro, no generar

### 1.7 Requisitos no funcionales

- Mobile-first en público. Desktop en paneles
- &lt; 60 s el cuestionario
- Aislamiento estricto entre venues
- Dinero consistente (nada de float, nada de read-modify-write en Node)
- El esquema debe aguantar Stripe, más verticales y preguntas dinámicas **sin rehacer tablas de reviews/wallet**

### 1.8 Criterio de éxito del piloto

Un restaurante real genera ≥ 10 reviews en una semana de uso, con texto publicable, y el admin entiende saldo y atribución. Si eso no ocurre, no se construye Stripe ni más verticales.

---

## 2. User journeys

### 2.1 Cliente (camino feliz)

```text
Escanea QR general o de María
  → {slug}.pmediaplus.com  o  /r/maria
  → “Hola, vamos a ayudarte a crear tu reseña de Restaurante La Plaza”
  → EMPEZAR
  → (si /r/maria) ¿Te ha atendido María?  [Sí] [No, otra persona]
  → ¿Quién te ha atendido? (si No, o si QR general)
  → ¿Qué has comido? (multi + Otro)
  → ¿Qué destacarías? (multi)
  → ¿Cómo valorarías?  Neutral / Buena / Muy buena / Excelente
  → POST /generate  (débito + OpenAI)
  → “Tu reseña está lista”
  → COPIAR / ABRIR GOOGLE
  → ¿Has publicado?  Sí / Todavía no
```

Textos de error:

- Venue inactivo: “Este negocio no está disponible.”
- Sin saldo: “Este venue no tiene saldo disponible.”
- Fallo IA: “No hemos podido generar la reseña. Inténtalo de nuevo.” (no se cobra)

### 2.2 Venue admin

```text
app.pmediaplus.com/login  (magic link)
  → /dashboard
  → ve saldo 23 €, 17 reviews este mes, alerta si < 5 €
  → Empleados: alta María, descarga QR PNG
  → Productos: alta “Arroz Negro”
  → Reviews: lee textos y sentimiento
```

### 2.3 Super admin

```text
app.pmediaplus.com/login  (mismo Auth, platform_role = super_admin)
  → /admin
  → Crear venue (slug, subdominio, admin email, 1 €/review, saldo 50 €)
  → El venue admin puede entrar
  → Más tarde: ajuste de saldo +10 €
```

### 2.4 QR de empleado

Si el code no existe o el staff está inactivo: caer al QR general (preguntar quién atendió, sin preselección). No 404 agresivo.

---

## 3. Technical architecture

```text
                    *.pmediaplus.com  →  Vercel
                              |
                    Next.js middleware (host)
                     /                    \
        slug.pmediaplus.com          app.pmediaplus.com
        (público, sin login)         (cookie de Auth)
                |                         |
        Route Handlers             Route Handlers
        + service role             + user JWT + RLS
                |                         |
                +-------- Supabase -------+
                     Postgres / Auth
                |
            OpenAI (solo generate)
```

Un solo proyecto Next.js. Un deploy. El middleware **no** consulta la DB en Edge: extrae el host y reescribe a route groups `(public)` / `(app)` / `(admin)`. El layout público resuelve el venue por `subdomain`.

Datos de tenant en público: APIs de servidor con service role, filtrando siempre por el venue resuelto. El cliente anónimo **nunca** recibe la anon key con RLS laxo ni lista de otros venues.

---

## 4. Authentication and permissions

### 4.1 Roles

| Rol | Dónde vive | Permiso |
|---|---|---|
| `super_admin` | `profiles.platform_role` | Todo, solo UI `/admin` |
| `venue_admin` | `venue_users.role` | Solo sus `venue_id` |
| `staff` | No es usuario en MVP | — |

Un `super_admin` no usa el dashboard de venue salvo que también esté en `venue_users` (no hace falta para el piloto).

### 4.2 Auth

Supabase Auth, **magic link**. Sin passwords en MVP.

Alta del primer venue admin: el super admin guarda el email en el alta del venue; se crea/vincula el usuario y `venue_users`. La primera semana es aceptable crear el usuario a mano en el dashboard de Supabase si el invite automático no está.

Sesión pública del cliente: cookie httpOnly **opaca** (`review_session_id` firmado o UUID random en cookie + fila `review_sessions`). Distinto dominio, no se mezcla con la cookie de `app.`.

### 4.3 Regla de oro RLS

- Venue admin: `venue_id IN (SELECT venue_id FROM venue_users WHERE user_id = auth.uid())`
- Super admin y flujo público: **solo servidor** (service role). No abrir políticas `true` para anon.

Detalle SQL en [`database.md`](database.md).

---

## 5. URL / subdomain architecture

| Host | App | Auth |
|---|---|---|
| `{slug}.pmediaplus.com` | Flujo cliente | No |
| `app.pmediaplus.com` | Venue + `/admin` | Sí |
| `pmediaplus.com` | No en MVP (opcional: redirect a `app.`) | — |
| `admin.pmediaplus.com` | Reservado | — |

Público:

- `/` — QR general
- `/r/{employee_code}` — QR de empleado

App:

- `/login`
- `/dashboard` — overview
- `/reviews`
- `/employees`
- `/products`
- `/qr`
- `/settings`

Super admin:

- `/admin`
- `/admin/venues`
- `/admin/venues/[id]`
- `/admin/reviews`
- `/admin/wallets`

Slugs de subdominio **reservados** (no se pueden asignar a un venue):

`app`, `admin`, `www`, `api`, `mail`, `status`, `assets`, `cdn`, `static`

DNS: `A/CNAME` wildcard `*.pmediaplus.com` → Vercel. Añadir el dominio wildcard en el proyecto.

Cookies: `Domain=app.pmediaplus.com` para Auth. Público: host del slug, `Secure`, `HttpOnly`, `SameSite=Lax`, path `/`.

---

## 6. API architecture

Prefijo `/api`. JSON. Errores `{ error: { code, message } }`.

### 6.1 Público (resuelve venue por `Host`)

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/api/public/session` | Crea `review_sessions` (`started`). 403 si venue inactivo. Cookie de sesión |
| `PATCH` | `/api/public/session` | Guarda `answers_json`, avanza a `questions_completed` cuando las 4 están |
| `POST` | `/api/public/generate` | Comprueba saldo, llama OpenAI, débito RPC, inserta `reviews`, status `review_generated`. 402 si no hay saldo |
| `POST` | `/api/public/google-opened` | Flag + status `google_opened` |
| `POST` | `/api/public/published` | `{ confirmed: boolean }` → `user_confirmed_published` si true |

`generate` es **idempotente por session_id**: si ya hay review cobrada, devuelve la existente. No se cobra un retry de red.

### 6.2 Venue app (JWT)

CRUD mínimo REST o Server Actions, da igual mientras pasen por RLS:

- Staff, products, venue settings (nombre público, google URL, business_info)
- `GET /api/app/overview`
- `GET /api/app/reviews`

### 6.3 Super admin (JWT + `platform_role`)

- CRUD venues
- `POST /api/admin/wallets/credit` `{ venue_id, amount_cents, description }`
- Listados reviews / venues

Toda mutación de dinero: RPC SQL. Nunca `balance = balance - x` en Node.

---

## 7. AI architecture

### 7.1 Cuándo se llama

Solo en `POST /generate`, una vez por sesión (MVP). El cliente no habla con OpenAI.

### 7.2 Input

- Venue: nombre, tipo, `business_info`
- Staff: nombre (si hay)
- `answers_json`
- Locale `es`
- `PROMPT_VERSION` (constante en código, p.ej. `1`)

### 7.3 Output

Texto plano, 40–100 palabras. **No** se pide JSON al modelo en MVP.

`sentiment` y `experience_score` se derivan de la pregunta de valoración:

| Valoración | sentiment | score |
|---|---|---|
| Neutral | `neutral` | 3 |
| Buena | `positive` | 4 |
| Muy buena | `very_positive` | 5 |
| Excelente | `very_positive` | 5 |

(Negativo se deja en el enum para más adelante; el piloto no ofrece “mala” a propósito: el producto empuja reseñas publicables. Si más adelante se captura negativo, no se genera texto o se avisa al venue.)

### 7.4 Prompt (contrato)

Sistema: escribir una reseña en primera persona del cliente, natural, como un WhatsApp cuidado, no como un anuncio. Variar arranque y longitud. Prohibido: “encantados de haber tenido el placer”, “sin duda alguna”, “una experiencia gastronómica inolvidable”, emojis, inventar platos o nombres que no vengan en el input, mencionar Google.

Usuario: bloques `Venue`, `Empleado`, `Platos`, `Destacado`, `Valoración`, `Notas`.

Parámetros: `gpt-4o-mini`, `temperature` 0.9, `max_tokens` ~250.

Si el modelo falla o el texto sale vacío: `generation_failed`, **no débito**.

Guardar en `reviews`: `generated_review`, `prompt_version`, `model`, `raw_response` opcional (útil al tunear; se puede omitir si preocupa volumen).

---

## 8. Wallet architecture (sin Stripe)

```text
venues.balance_cents
        ^
        |  RPC credit_wallet / debit_wallet  (row lock)
        v
wallet_transactions
  type: credit | debit | refund | manual_adjustment
  review_id nullable, unique cuando type = debit
```

Alta de venue: `credit_wallet` con `manual_adjustment` o `credit` por el saldo inicial.

`generate`: `debit_wallet(venue_id, price_per_review_cents, review_id)`. Si `balance < price` → excepción SQL → 402.

Umbral 5,00 € (`500` cents): el overview pinta el aviso. No email.

Fase 1.5: Stripe Checkout `mode=payment`, metadata `venue_id`, webhook `checkout.session.completed` llama el **mismo** `credit_wallet` con `idempotency_key = stripe_event_id`. Por eso el RPC se diseña ya con clave de idempotencia.

Paquetes previstos (no UI): 25 / 50 / 100 / 250 EUR.

`billing_event` en `venues`: valor MVP `review_generated`. Si un día se cobra al confirmar publicación, el RPC se llama en esa transición en vez de en generate. Las filas antiguas no se reescriben.

---

## 9. Review state machine

```text
started
  → questions_completed     (4 respuestas)
  → review_generated        (OpenAI OK + débito)     ← cobro MVP
  → google_opened
  → user_confirmed_published

laterales:
  started → abandoned       (no se implementa job; el estado queda started)
  questions_completed → blocked_no_balance
  questions_completed → generation_failed → (retry generate) → review_generated
```

`copy` no es un estado: es un gesto del navegador. No hace falta endpoint.

---

## 10. Folder / project structure (repo nuevo)

Un solo proyecto Next.js, **sin monorepo**.

```text
pmediaplus/
  app/
    (public)/                 # host = slug
      page.tsx
      r/[code]/page.tsx
    (app)/                    # host = app, venue admin
      login/page.tsx
      dashboard/page.tsx
      reviews/page.tsx
      employees/page.tsx
      products/page.tsx
      qr/page.tsx
      settings/page.tsx
    (admin)/                  # host = app + role
      admin/page.tsx
      admin/venues/...
    api/
      public/...
      app/...
      admin/...
    layout.tsx
  middleware.ts               # host → rewrite
  lib/
    tenant.ts
    supabase/{server,admin,rls}.ts
    money.ts
    openai.ts
    qr.ts
  supabase/
    migrations/
    seed.sql                  # 1 venue piloto
  docs/                       # copiar estos markdowns
```

UI pública: una pregunta por pantalla, botones grandes, sin look de “formulario admin”.

---

## 11. Analytics (MVP = overview, no un módulo)

El dashboard muestra:

- Saldo
- Reviews este mes / histórico
- Coste del mes (`SUM(cost_cents)`)
- Nº empleados activos
- Reviews por empleado (count + % positive aproximado: sentiment in positive/very_positive)
- Últimas 10 reviews

No hay gráficos, ni “top products”, ni “top attributes” en el piloto. Esos campos ya están en `answers_json` para calcularlos después con una query.

---

## 12. Security

Piloto, poca fricción:

- Aislamiento: host público ≠ cookie de `app.` + `venue_id` + RLS + service role en público
- Rate limit: ~10 `generate` / hora / IP / venue. Mensaje amable. Sin Turnstile hasta que haya abuso
- No se guarda PII del cliente (no email, no teléfono). IP se hashea si se guarda
- QR público: el coste lo paga el venue (saldo). Ese es el freno principal
- No bloquear “misma mesa, dos reseñas”: familias reales
- Service role **solo** en servidor, nunca `NEXT_PUBLIC_`
- Validar `employee_code` y `slug` como `[a-z0-9-]+`

Riesgos y mitigaciones en la sección 14.

---

## 13. Evolución (para no rehacer)

El esquema MVP deja ganchos, no tablas vacías de más:

| Luego | Cómo entra sin migrar reviews |
|---|---|
| Stripe | tabla `payments` + mismo `credit_wallet` |
| Email | tabla `notifications` + Resend |
| Preguntas dinámicas | `question_sets`; el cliente ya manda `answers_json` |
| Categorías de menú | extraer `products.category` a tabla |
| Business info rica | extraer columna texto a tabla/JSON |
| Staff login | `venue_users.role = staff` |
| Rewards | tablas nuevas colgadas de `staff_id` |
| Multi-local / cadenas | `organization_id` en venues |
| `admin.` host | el route group `(admin)` ya existe; solo DNS + middleware |
| Cobrar al publicar | cambiar `billing_event` y el punto de llamada al RPC |

---

## 14. Riesgos

### Técnicos

- Wildcard DNS/SSL en Vercel mal configurado → el slug no resuelve
- Resolver el tenant mal (www, `app`, mayúsculas) → 404 o leak
- OpenAI lento/caído en el móvil → timeout y doble tap; mitigar con idempotencia de sesión
- Texto “demasiado IA” → iterar `PROMPT_VERSION`, no arquitectura
- Drift de saldo si alguien actualiza `balance_cents` a mano; solo RPCs

### Seguridad

- IDOR: un GET de reviews sin filtrar `venue_id`
- Anon key en el bundle con políticas abiertas
- Subdomain takeover de slugs vacíos (Vercel + slugs reservados)
- Magic link al email equivocado al crear el venue

### Producto

- Cobrar aunque no publiquen en Google (aceptado; `billing_event` es la válvula)
- 4 preguntas pueden ser pocas para un hotel; el piloto es restaurante a propósito
- Sin Stripe, recargar a 20 venues a mano no escala — se hace Stripe en 1.5, no se diseña otro wallet

---

## 15. Decisiones pendientes (no bloquean docs ni el piloto)

- Nombre comercial público si no es “P Media Plus”
- Org/cuenta GitHub del repo nuevo
- Cuentas **separadas** de Supabase, Vercel, OpenAI (y Stripe luego) — no reutilizar CDE
- Dominio `pmediaplus.com` ya en el DNS del proyecto Vercel
- Precio por defecto 1,00 € (ajustable por venue)

Cuando se empiece a programar: crear el repo `pmediaplus`, copiar estos tres docs, y seguir [`mvp-plan.md`](mvp-plan.md) bloque a bloque.
