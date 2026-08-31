# NavExport — Stripe prepaid credits

## Model

| Concept | Rule |
|---------|------|
| **1 credit** | 1 lead row exported (Basic tier) |
| **When to pay** | Before first LinkedIn connect (wallet must be > 0) |
| **When to deduct** | After successful export, `count(rows)` credits |
| **Enriched / Mail** | Phase 2 — add multipliers or separate meters |

Retail anchor: **€0.05 / lead** → packs at €5 / 100 credits.

## User flow

```
Connect LinkedIn
  ├─ billing off → Unipile popup (demo, current behaviour)
  └─ billing on
       ├─ balance = 0 → Stripe Checkout popup (100 credits = €5)
       └─ balance > 0 → Unipile popup (connect-callback.html)

Export CSV
  └─ POST salesnav-export.php → deduct credits server-side
       └─ 402 if insufficient → Stripe Checkout
```

## Files

| File | Role |
|------|------|
| `public/api/_credits.php` | Wallet + ledger (`private/cde/salesnav_wallets.json`) |
| `public/api/_stripe.php` | Checkout Session + webhook verify |
| `public/api/salesnav-credits.php` | GET balance + packs |
| `public/api/salesnav-stripe-checkout.php` | POST → Stripe Checkout URL |
| `public/api/salesnav-stripe-webhook.php` | `checkout.session.completed` → add credits |
| `public/salesnav/connect-callback.html` | Unipile popup callback → `postMessage` + close |

## Stripe setup (production)

1. [Stripe Dashboard](https://dashboard.stripe.com) → **Developers → API keys**
   - `STRIPE_SECRET_KEY=sk_live_...`

2. **Developers → Webhooks** → Add endpoint:
   - URL: `https://companydataenrichment.com/api/salesnav-stripe-webhook.php`
   - Event: `checkout.session.completed`
   - Copy signing secret → `STRIPE_WEBHOOK_SECRET=whsec_...`

3. On VPS (`private/cde/stripe.env`, mode 640):

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
SALESNAV_SITE_ORIGIN=https://companydataenrichment.com
# SALESNAV_BILLING_ENABLED=1   # omit or set 1 when ready; set 0 to disable
```

4. Deploy + test with Stripe test keys first (`sk_test_`, test webhook).

## Credit packs (code)

| Pack ID | Credits | Price |
|---------|---------|-------|
| `100` | 100 | €5.00 |
| `500` | 500 | €25.00 |
| `1000` | 1000 | €50.00 |

Edit `cde_credits_packs()` in `_credits.php` to change.

## Phase 2 ideas

- **Hold + settle**: reserve `limit` credits before export, refund delta if fewer rows returned
- **Tier multipliers**: Enriched +0.4 cr/lead, Mail +1.8 cr/email found
- **Stripe Customer Portal** for top-ups and invoices
- **Email login** instead of session-only wallet (tie credits to account)

## Until Stripe is live

Without `STRIPE_SECRET_KEY`, `billing_enabled: false` — demo limits (25 leads) and free connect unchanged.
