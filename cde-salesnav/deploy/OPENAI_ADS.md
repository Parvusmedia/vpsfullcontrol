# OpenAI Ads — Sales Navigator (`/salesnav/`)

## Landing pixel

`public/salesnav/openai-ads.js` loads `oaiq.min.js` and calls `init` with Pixel ID `NQH4BHyBvLncEkDLpUrQpJ`.

Included on:

- `https://companydataenrichment.com/salesnav/` (`index.html`)
- `https://companydataenrichment.com/salesnav/panel/` (`panel/index.html`)
- `stripe-callback.html` (after checkout)

Debug: add `?oaiq_debug=1` to the URL or `localStorage.oaiq_debug = "1"`.

## Top-up conversion (`order_created`)

When Stripe checkout credits the wallet (first time per `cs_…` session):

1. **Browser:** `oaiq("measure", "order_created", …)` with `event_id` = Stripe session id (deduped in `sessionStorage`).
2. **Server:** `cde_openai_ads_track_checkout_session()` POSTs to `https://bzr.openai.com/v1/events?pid=…` if `OPENAI_CONVERSIONS_API_KEY` is set in `private/cde/stripe.env`.

`source_url` for server events: `https://companydataenrichment.com/salesnav/panel/#topup`

## Production setup

On `nextconvers-vps`, add to `/var/www/vhosts/companydataenrichment.com/private/cde/stripe.env`:

```bash
OPENAI_ADS_PIXEL_ID=NQH4BHyBvLncEkDLpUrQpJ
OPENAI_CONVERSIONS_API_KEY=<from OpenAI Ads Conversions API>
```

Never commit the API key. Test with `validate_only: true` via curl (see OpenAI docs) before live traffic.

Deploy: `cde-salesnav/deploy-salesnav-prod.sh` (include `_openai_ads.php` in api sync if you extend the script).
