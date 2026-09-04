# Sales Nav Admin

Internal panel: **https://companydataenrichment.com/salesnav/admin/**

## Setup (production)

1. Allow specific panel accounts in `private/cde/unipile.env`:

   ```bash
   SALESNAV_ADMIN_EMAILS=you@company.com,other@company.com
   ```

   Those users sign in with the **same email + password** as `/salesnav/panel/`.

   Optional legacy shared password: `SALESNAV_ADMIN_PASSWORD` (API scripts only).

2. Open `/salesnav/admin/` and sign in with your panel credentials (session ~12h).

## Features

- **Overview** — users, credits in circulation, tasks, 30-day top-ups / grants / spend
- **Users** — email, balance, Stripe purchases, admin grants, spend, tasks, LinkedIn status
- **Ledger** — filter by top-up, grant, spend, refund
- **Tasks** — all export jobs across users
- **Grant credits** — free credit top-ups (same wallet + ledger as Stripe)

## API

Base: `/api/salesnav-admin-api.php?action=…`

| Action | Method | Auth |
|--------|--------|------|
| `status` | GET | no |
| `login` | POST `{email,password}` | no |
| `logout` | POST | session |
| `overview` | GET | yes |
| `users` | GET `?q=` | yes |
| `user` | GET `?email=` or `?user_id=` | yes |
| `ledger` | GET `?kind=&limit=` | yes |
| `tasks` | GET `?status=&limit=` | yes |
| `grant` | POST `{email,credits,note?}` | yes |

Header auth (scripts): `X-Salesnav-Admin-Token: <password>`

Legacy grant-only endpoint: `POST /api/salesnav-admin-credits.php`

## CLI (SSH)

```bash
/opt/plesk/php/8.3/bin/php /var/www/vhosts/companydataenrichment.com/private/cde/grant-credits.php user@co.com 200 "Support"
```

Or copy from repo `deploy/grant-credits.php`.
