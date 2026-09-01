# NavExport — Stripe prepaid credits

## Model

| Concept | Rule |
|---------|------|
| **1 credit** | ≈ €0.05 of Basic export (1 credit per lead) |
| **Minimum top-up** | **€20** |
| **Bonus** | From **100 base credits** paid → **+20%** in wallet (e.g. pay €20 → 120 credits) |
| **When to pay** | Before first LinkedIn connect (wallet must be > 0) |
| **When to deduct** | After successful export, tier-based cost |

### Export cost (credits)

| Tier | Retail | Credits |
|------|--------|---------|
| **Basic** | €0.05 / lead | 1.0 / lead |
| **+ Enriched** | + €0.02 / lead | +0.4 / lead |
| **+ Mail** | + €0.09 / email found | +1.8 / work email found |

Enriched tier uses HarvestAPI profile + company enrichment. Mail tier is phase 2.

## User flow

```
Connect LinkedIn
  ├─ billing off → Unipile popup (demo, current behaviour)
  └─ billing on
       ├─ balance = 0 → Stripe Checkout (min pack €20 → 120 credits)
       └─ balance > 0 → Unipile popup (connect-callback.html)

Export CSV
  └─ POST salesnav-export.php
       ├─ tier_enriched / tier_mail in JSON body
       ├─ deduct cde_credits_export_cost(rows, tiers)
       └─ 402 if insufficient → Stripe Checkout
```

## Files

| File | Role |
|------|------|
| `public/api/_credits.php` | Wallet, packs, tier cost, bonus grant |
| `public/api/_stripe.php` | Checkout Session + webhook verify |
| `public/api/salesnav-credits.php` | GET balance + packs + pricing |
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
STRIPE_PRODUCT_ID=prod_VB9BUSTFvzzBRm
STRIPE_PRICE_ID=price_1UAnliL0sc6a4STMwyYdMPF4
SALESNAV_SITE_ORIGIN=https://companydataenrichment.com
# SALESNAV_BILLING_ENABLED=1   # omit or set 1 when ready; set 0 to disable
```

Pack `120` (€20 → 120 credits) uses `STRIPE_PRICE_ID`. Other packs fall back to ad-hoc `price_data` until you add `STRIPE_PRICE_ID_300`, etc.

4. Deploy + test with Stripe test keys first (`sk_test_`, test webhook).

## Credit packs (code)

Defined in `cde_credits_packs()` — `_credits.php`:

| Pack ID | Price | Paid base | Granted (with bonus) |
|---------|-------|-----------|----------------------|
| `120` | €20 | 100 | **120** (+20%) |
| `300` | €50 | 250 | 300 |
| `600` | €100 | 500 | 600 |
| `1200` | €200 | 1,000 | 1,200 |

Edit pack definitions to change retail tiers.

## Promotion codes (Stripe Checkout only)

Codes are entered in Stripe Checkout via **Add promotion code** — not on the website.

| Code | Discount | Pay | Notes |
|------|----------|-----|-------|
| `FREE25` | €19.50 off | **€0.50** | Stripe minimum charge (EUR); still grants full 120 credits via webhook |
| `OX1ENSMN` | same | €0.50 | First-time Stripe customer only |

**Important:** Stripe Checkout `payment` mode cannot total **€0**. A 100% off coupon will show as invalid — use amount-off coupons that leave at least **€0.50** due.

Checkout uses fixed Price `price_1UAnliL0sc6a4STMwyYdMPF4` + `allow_promotion_codes=true`.

## Until Stripe is live

Without `STRIPE_SECRET_KEY`, `billing_enabled: false` — demo limits (25 leads) and free connect unchanged.
