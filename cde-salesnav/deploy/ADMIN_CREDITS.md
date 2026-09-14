# Admin credit grants (Sales Navigator)

Panel wallets live in `private/cde/salesnav_wallets.json` (not Django). Use these tools to top up any account.

## CLI (SSH on prod)

```bash
/opt/plesk/php/8.3/bin/php /path/to/grant-credits.php emiliano@parvusmedia.com 200 "Support top-up"
```

## HTTP API (for Django or internal ops)

**Endpoint:** `POST https://companydataenrichment.com/api/salesnav-admin-credits.php`

**Header:** `X-Salesnav-Admin-Token: <SALESNAV_ADMIN_SECRET>`

**Body:**

```json
{
  "email": "user@company.com",
  "credits": 200,
  "note": "Manual grant",
  "ref": "optional-idempotency-key"
}
```

**Response:**

```json
{
  "ok": true,
  "email": "user@company.com",
  "user_id": "em_…",
  "granted": 200,
  "balance_before": 0,
  "balance": 200,
  "ref": "admin:grant:…"
}
```

Set `SALESNAV_ADMIN_SECRET` in `private/cde/unipile.env` on production (never commit the value).

### Django example

```python
import requests

def grant_salesnav_credits(email: str, credits: int, note: str = "") -> dict:
    resp = requests.post(
        "https://companydataenrichment.com/api/salesnav-admin-credits.php",
        headers={"X-Salesnav-Admin-Token": settings.SALESNAV_ADMIN_SECRET},
        json={"email": email, "credits": credits, "note": note},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
```

Wire this into Django Admin as a custom action or a small form view; store `SALESNAV_ADMIN_SECRET` in Django settings/env.
