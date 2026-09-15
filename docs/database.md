# P Media Plus — Data model

Esquema **mínimo del MVP**. Lo que no está aquí se añade en fase 1.5/2 sin tocar el núcleo `venues` / `review_sessions` / `reviews` / `wallet_transactions`.

Reglas:

- Dinero en `bigint` céntimos (EUR). Nunca `numeric`/`float` para saldo.
- Toda tabla de negocio lleva `venue_id` salvo `profiles` y `wallet_transactions` (esta última sí lo lleva).
- UUIDs `gen_random_uuid()`.
- Timestamps `timestamptz` `now()`.
- Soft-delete no: `active`/`status` en venue y staff.

Motor: Postgres (Supabase). Migraciones SQL. RPCs de wallet con `FOR UPDATE`.

---

## 1. Diagrama de relaciones

```text
auth.users
    │ 1:1
profiles
    │
    └──── venue_users ──── venues ──── staff
                              │           │
                              │           └── review_sessions ── reviews
                              │                      │              │
                              ├── products           └── answers_json
                              │
                              └── wallet_transactions ── reviews (debit)
```

---

## 2. Enums

```sql
create type platform_role as enum ('super_admin', 'venue_admin');

create type venue_status as enum ('active', 'inactive');

create type venue_type as enum (
  'restaurant',
  'bar',
  'shop',
  'salon',
  'hotel',
  'other'
);

create type billing_event as enum (
  'review_generated',
  'user_confirmed_published'
);

create type venue_user_role as enum ('venue_admin', 'staff'); -- staff no se usa en MVP

create type review_status as enum (
  'started',
  'questions_completed',
  'review_generated',
  'google_opened',
  'user_confirmed_published',
  'abandoned',
  'blocked_no_balance',
  'generation_failed'
);

create type sentiment as enum (
  'negative',
  'neutral',
  'positive',
  'very_positive'
);

create type wallet_tx_type as enum (
  'credit',
  'debit',
  'refund',
  'manual_adjustment'
);
```

El piloto solo crea venues `restaurant` y `billing_event = review_generated`. El resto de valores existe para no migrar enums después.

---

## 3. Tablas

### 3.1 `profiles`

Extiende `auth.users`. Trigger `on_auth_user_created` inserta la fila.

```sql
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  display_name text,
  platform_role platform_role not null default 'venue_admin',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index profiles_email_lower on public.profiles (lower(email));
```

### 3.2 `venues`

Ficha + settings + saldo + texto de negocio. Una tabla a propósito (el recorte evita `venue_settings`, `wallets`, `venue_business_info`).

```sql
create table public.venues (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null,
  subdomain text not null,
  type venue_type not null default 'restaurant',
  status venue_status not null default 'active',
  address text,
  website text,
  logo_url text,
  google_review_url text not null,
  locale text not null default 'es',
  price_per_review_cents bigint not null default 100
    check (price_per_review_cents >= 0),
  billing_event billing_event not null default 'review_generated',
  balance_cents bigint not null default 0
    check (balance_cents >= 0),
  low_balance_threshold_cents bigint not null default 500,
  business_info text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint venues_slug_format check (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  constraint venues_subdomain_format check (subdomain ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$')
);

create unique index venues_slug_key on public.venues (slug);
create unique index venues_subdomain_key on public.venues (subdomain);
```

Slugs reservados (check en trigger o en la API, no en SQL check largo):  
`app`, `admin`, `www`, `api`, `mail`, `status`, `assets`, `cdn`, `static`.

`subdomain` y `slug` pueden ser iguales (`restaurante-la-plaza`). Se guardan los dos por si un día el slug de URL interna y el host divergen.

`google_review_url` es obligatorio: sin ella el flujo público no tiene CTA.

### 3.3 `venue_users`

```sql
create table public.venue_users (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete cascade,
  role venue_user_role not null default 'venue_admin',
  created_at timestamptz not null default now(),
  unique (venue_id, user_id)
);

create index venue_users_user_id_idx on public.venue_users (user_id);
```

El piloto: un admin por venue. El unique permite varios más adelante.

### 3.4 `staff`

```sql
create table public.staff (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete cascade,
  first_name text not null,
  last_name text,
  position text,
  photo_url text,
  employee_code text not null,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint staff_code_format check (employee_code ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
  unique (venue_id, employee_code)
);

create index staff_venue_id_idx on public.staff (venue_id);
```

No se denormalizan counters (`reviews_count`, `score`). Se calculan en el overview con `GROUP BY`. Menos sitios que desincronizar.

QR público: `https://{subdomain}.pmediaplus.com/r/{employee_code}`

### 3.5 `products`

Lista plana. `category` es texto libre controlado en UI (Entrantes, Principales, …).

```sql
create table public.products (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete cascade,
  name text not null,
  description text,
  category text not null default 'Principales',
  active boolean not null default true,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index products_venue_id_idx on public.products (venue_id);
```

### 3.6 `review_sessions`

Una visita al flujo. Cookie apunta aquí.

```sql
create table public.review_sessions (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete cascade,
  staff_id uuid references public.staff (id) on delete set null,
  staff_preselected_id uuid references public.staff (id) on delete set null,
  status review_status not null default 'started',
  answers_json jsonb not null default '{}'::jsonb,
  ip_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index review_sessions_venue_id_idx on public.review_sessions (venue_id);
create index review_sessions_venue_created_idx on public.review_sessions (venue_id, created_at desc);
```

`staff_preselected_id`: el del QR. `staff_id`: el confirmado en la pregunta 1 (puede cambiar).

`answers_json` ejemplo:

```json
{
  "staff_id": "…",
  "staff_other": null,
  "products": [{ "id": "…", "name": "Arroz Negro" }],
  "products_other": "Croquetas",
  "highlights": ["atencion", "calidad"],
  "rating": "muy_buena"
}
```

No hay tabla `review_answers`. Si más adelante se analizan atributos, se leen de este JSON o se extraen a una tabla nueva.

### 3.7 `reviews`

Una por sesión, cuando la IA responde. Relación 1:1 con sesión cobrada.

```sql
create table public.reviews (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete cascade,
  session_id uuid not null references public.review_sessions (id) on delete restrict,
  staff_id uuid references public.staff (id) on delete set null,
  answers_json jsonb not null default '{}'::jsonb,
  generated_review text not null,
  sentiment sentiment,
  experience_score smallint
    check (experience_score is null or experience_score between 1 and 5),
  status review_status not null default 'review_generated',
  cost_cents bigint not null default 0,
  google_opened boolean not null default false,
  user_confirmed_published boolean,
  prompt_version int not null default 1,
  model text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id)
);

create index reviews_venue_id_idx on public.reviews (venue_id);
create index reviews_venue_created_idx on public.reviews (venue_id, created_at desc);
create index reviews_staff_id_idx on public.reviews (staff_id);
```

`user_confirmed_published`: `null` = no contestó, `true`/`false` = Sí / Todavía no.

Copiar `answers_json` aquí (además de la sesión) para que el listado de reviews no dependa de joinear la sesión.

### 3.8 `wallet_transactions`

Libro mayor. El saldo vivo está en `venues.balance_cents`; esta tabla es la verdad de movimientos.

```sql
create table public.wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  venue_id uuid not null references public.venues (id) on delete restrict,
  amount_cents bigint not null
    check (amount_cents <> 0),
  type wallet_tx_type not null,
  description text,
  review_id uuid references public.reviews (id) on delete restrict,
  idempotency_key text,
  created_at timestamptz not null default now(),
  created_by uuid references public.profiles (id) on delete set null
);

create index wallet_tx_venue_id_idx on public.wallet_transactions (venue_id, created_at desc);
create unique index wallet_tx_idempotency_key on public.wallet_transactions (idempotency_key)
  where idempotency_key is not null;
create unique index wallet_tx_debit_review on public.wallet_transactions (review_id)
  where type = 'debit' and review_id is not null;
```

Signo:

- `credit` / `manual_adjustment` positivo: `amount_cents > 0`
- `debit` negativo: `amount_cents < 0` (p.ej. `-100`)
- `refund` positivo

Forzar el signo en el RPC, no en un check complicado.

`idempotency_key`: en MVP `manual:{uuid}` o `seed:{venue_id}:initial`. En fase 1.5 `stripe:{event_id}`.

---

## 4. Tablas que NO se crean en MVP

| Tabla | Por qué se espera | Cómo se añade |
|---|---|---|
| `wallets` | 1:1 innecesario | el saldo ya está en `venues` |
| `payments` | Stripe | `venue_id`, `provider`, `stripe_session_id`, `amount_cents`, `status`, `stripe_event_id` unique |
| `notifications` | Resend | `venue_id`, `type`, `sent_at` |
| `audit_logs` | impersonar / compliance | después |
| `platform_settings` | pricing global | env o fila única luego |
| `question_sets` / `questions` / `question_options` | preguntas dinámicas | el cliente ya persiste `answers_json` |
| `review_answers` | analytics normalizado | extraer de JSON |
| `product_categories` | menú rico | `products.category` es el puente |
| `venue_business_info` | campos separados | `venues.business_info` texto |
| `venue_settings` | split de ficha | columnas en `venues` |

---

## 5. RPCs de wallet

Única vía para tocar `balance_cents`.

```sql
create or replace function public.credit_wallet(
  p_venue_id uuid,
  p_amount_cents bigint,
  p_type wallet_tx_type,
  p_description text,
  p_idempotency_key text default null,
  p_created_by uuid default null
) returns public.wallet_transactions
language plpgsql
security definer
set search_path = public
as $$
declare
  tx public.wallet_transactions;
begin
  if p_amount_cents <= 0 then
    raise exception 'amount must be positive';
  end if;
  if p_type not in ('credit', 'manual_adjustment', 'refund') then
    raise exception 'invalid credit type';
  end if;

  if p_idempotency_key is not null then
    select * into tx from public.wallet_transactions
      where idempotency_key = p_idempotency_key;
    if found then
      return tx;
    end if;
  end if;

  update public.venues
    set balance_cents = balance_cents + p_amount_cents,
        updated_at = now()
    where id = p_venue_id;

  if not found then
    raise exception 'venue not found';
  end if;

  insert into public.wallet_transactions (
    venue_id, amount_cents, type, description, idempotency_key, created_by
  ) values (
    p_venue_id, p_amount_cents, p_type, p_description, p_idempotency_key, p_created_by
  ) returning * into tx;

  return tx;
end;
$$;

create or replace function public.debit_wallet(
  p_venue_id uuid,
  p_amount_cents bigint,
  p_review_id uuid,
  p_description text default 'review_generated'
) returns public.wallet_transactions
language plpgsql
security definer
set search_path = public
as $$
declare
  tx public.wallet_transactions;
  v_balance bigint;
begin
  if p_amount_cents <= 0 then
    raise exception 'amount must be positive';
  end if;

  select * into tx from public.wallet_transactions
    where review_id = p_review_id and type = 'debit';
  if found then
    return tx;
  end if;

  select balance_cents into v_balance
    from public.venues
    where id = p_venue_id
    for update;

  if v_balance is null then
    raise exception 'venue not found';
  end if;
  if v_balance < p_amount_cents then
    raise exception 'insufficient_balance';
  end if;

  update public.venues
    set balance_cents = balance_cents - p_amount_cents,
        updated_at = now()
    where id = p_venue_id;

  insert into public.wallet_transactions (
    venue_id, amount_cents, type, description, review_id
  ) values (
    p_venue_id, -p_amount_cents, 'debit', p_description, p_review_id
  ) returning * into tx;

  return tx;
end;
$$;
```

Orden en `generate` (transacción única, o débito **después** de insertar `reviews` para tener `review_id`):

1. Lock venue / comprobar saldo *antes* de llamar a OpenAI (lectura). Si no hay saldo → `blocked_no_balance`, no gastar tokens.
2. OpenAI.
3. `INSERT reviews`.
4. `debit_wallet`. Si fallara (carrera), marcar `generation_failed` y no dejar review cobrada a medias — o borrar/ocultar la review. La carrera es rara; el `FOR UPDATE` en el débito + unique de `review_id` cubre el doble cobro.

`credit_wallet` / `debit_wallet` **no** se exponen a `anon` ni a `authenticated`. Solo las Route Handlers con service role. `revoke execute from public, anon, authenticated`.

---

## 6. Row Level Security

Activar RLS en todas las tablas públicas.

### 6.1 Helpers

```sql
create or replace function public.is_super_admin()
returns boolean
language sql
stable
as $$
  select exists (
    select 1 from public.profiles
    where id = auth.uid() and platform_role = 'super_admin'
  );
$$;

create or replace function public.user_venue_ids()
returns setof uuid
language sql
stable
as $$
  select venue_id from public.venue_users where user_id = auth.uid();
$$;
```

### 6.2 Políticas (venue admin)

`profiles`: el usuario lee/edita su fila. Super admin lee todas.

`venues`: `id in (select public.user_venue_ids())` para `select` y `update` de campos no financieros. **`balance_cents` y `price_per_review_cents` no se actualizan por UPDATE de cliente** — solo RPCs / service role. Opción simple: venue admin tiene `select`; `update` limitado por trigger que rechaza cambios a columnas de dinero.

`venue_users`: `select` donde `venue_id in user_venue_ids()`. Writes: service role (alta en el create-venue del super admin).

`staff`, `products`, `review_sessions`, `reviews`: `select/insert/update` si `venue_id in user_venue_ids()`. Venue admin **no borra** reviews (opcional `delete` deshabilitado).

`wallet_transactions`: `select` si `venue_id in user_venue_ids()`. Sin insert/update/delete para `authenticated`.

### 6.3 Anon / público

**Ninguna** política `for anon`. El flujo público usa service role en servidor y filtra por el `venue_id` resuelto del `Host`.

### 6.4 Super admin

Las rutas `/api/admin/*` usan service role **después** de comprobar `profiles.platform_role` con el JWT del usuario. No hace falta `using (is_super_admin())` en cada tabla (reduce superficie si alguien usa el anon client). El panel no instancia el cliente con service role en el browser.

---

## 7. Auth trigger

```sql
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

El primer `super_admin` se marca a mano (`update profiles set platform_role = 'super_admin'`).

---

## 8. Queries del overview

Reviews este mes:

```sql
select count(*) from reviews
where venue_id = $1
  and created_at >= date_trunc('month', now() at time zone 'Europe/Madrid');
```

Por empleado:

```sql
select s.id, s.first_name,
       count(r.id) as reviews_count,
       count(*) filter (where r.sentiment in ('positive', 'very_positive'))::float
         / nullif(count(r.id), 0) as positive_pct
from staff s
left join reviews r on r.staff_id = s.id
  and r.created_at >= date_trunc('month', now() at time zone 'Europe/Madrid')
where s.venue_id = $1 and s.active
group by s.id;
```

Coste del mes: `sum(cost_cents)` sobre `reviews` del mes. Debe coincidir con débitos del mes (salvo ajustes).

---

## 9. Seed piloto (`seed.sql`)

1. Usuario super admin (dashboard Supabase o SQL sobre `auth.users`).
2. Venue `restaurante-la-plaza`, subdomain igual, `google_review_url` real de prueba, `price_per_review_cents = 100`, `balance_cents = 0`.
3. `credit_wallet(..., 5000, 'manual_adjustment', 'saldo inicial', 'seed:la-plaza:initial')`.
4. Staff: `maria`, `juan`.
5. Products: Paella Valenciana, Arroz Negro, Solomillo, Flan casero (categorías Principales / Postres).
6. `venue_users` con un admin de prueba.

Con eso el bloque 4 del plan MVP (flujo público) se puede probar sin panel.

---

## 10. Storage (opcional)

Bucket público `venue-assets` si más adelante hay logo/foto. En MVP `logo_url` / `photo_url` pueden quedar `null` o ser una URL pegada. No es bloqueante.

---

## 11. Integridad extra

- Trigger `updated_at = now()` en tablas con esa columna.
- FK `reviews.venue_id` debe coincidir con `review_sessions.venue_id` (check en la API o trigger).
- `employee_code` único por venue, no global (María puede existir en dos restaurantes).
- No borrar un venue con transacciones: `on delete restrict` en `wallet_transactions`. Desactivar con `status = inactive`.
