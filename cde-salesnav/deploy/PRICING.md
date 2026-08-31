# NavExport tier pricing analysis

Last updated: 2026-08-31. Benchmark: [Evaboot credit model](https://evaboot.com/pricing). Costs in USD; retail in EUR (~€1 ≈ $1.08).

## Competitor benchmark — Evaboot

| Monthly credits | Price/mo | $/credit | Export (1 cr) | Email found (1 cr) | Lead + email (2 cr) |
|-----------------|----------|----------|---------------|--------------------|---------------------|
| 100             | $9       | $0.090   | $0.09         | $0.09              | $0.18               |
| 500             | $29      | $0.058   | $0.058        | $0.058             | $0.116              |
| 1,500           | $49      | $0.033   | $0.033        | $0.033             | $0.066              |
| 4,000           | $99      | $0.025   | $0.025        | $0.025             | $0.050              |
| 8,000           | $149     | $0.019   | $0.019        | $0.019             | $0.038              |
| 20,000          | $299     | $0.015   | $0.015        | $0.015             | $0.030              |

Rules: 1 credit per exported lead; 1 credit per email **found** (no charge when not found). Unlimited Sales Navigator seats on all plans.

## Our supplier costs

| Supplier | When charged | Unit cost (USD) | Source |
|----------|--------------|-----------------|--------|
| **Unipile** | Per connected LinkedIn/SN account | **$5/mo** fixed | User-provided |
| **Harvest** (Apify actor) | Enriched tier — full profile scrape | **$0.004/lead** ($4/1k) | [harvestapi/linkedin-profile-scraper](https://apify.com/harvestapi/linkedin-profile-scraper) |
| **Icypeas** | Mail tier — email found only | **$0.019** (Basic 1k) → **$0.005** (Hypergrowth 100k) per found email | [Icypeas credit cost](https://api-doc.icypeas.com/how-works/credit-cost/) |

Unipile is amortised per lead: `$5 ÷ monthly_leads`. Example at **1,000 leads/mo**: **$0.005/lead**.

## Cost stack @ 1,000 leads/month (reference volume)

| Tier component | Variable cost/lead | Fixed (Unipile) amortised | Total cost (USD) |
|----------------|-------------------|---------------------------|------------------|
| Basic export   | ~$0.001 API       | $0.005                    | **~$0.006**      |
| + Enriched     | $0.004 Harvest    | —                         | **+$0.004**      |
| + Mail (per email found) | $0.009–0.019 Icypeas | —                  | **+$0.009–0.019** per hit |

Assumptions: 1 SN seat; Icypeas Premium tier ($39/4k credits ≈ $0.009/email) at moderate volume.

## Proposed retail (site tiers)

Modular add-ons vs Evaboot’s bundled credits. Prices chosen to **match or undercut Evaboot entry tier** on Basic and Mail while keeping **≥75% gross margin** at 1k leads/mo.

| Tier | Retail price | Est. cost @ 1k/mo | Gross margin | Evaboot equivalent |
|------|--------------|-------------------|--------------|-------------------|
| **Basic** | **€0.05 / lead** | ~$0.006 | ~89% | $0.09 export (100-cr tier) |
| **Enriched** add-on | **+ €0.02 / lead** | +$0.004 | ~82% | Included in Evaboot export |
| **Mail** add-on | **+ €0.09 / email found** | +$0.009–0.019 | ~79–90% | $0.09 email (100-cr tier) |

**Example totals (email found):**

| Package | Our price | Evaboot @ 100 cr | Evaboot @ 4k cr |
|---------|-----------|------------------|-----------------|
| Basic only | €0.05 | $0.09 | $0.025 |
| Basic + Enriched | €0.07 | $0.09 | $0.025 |
| Basic + Enriched + Mail | €0.16 / found email | $0.18 | $0.050 |

## Volume sensitivity — Unipile seat

| Leads/mo | Unipile amortised | Basic cost | Margin @ €0.05 |
|----------|-------------------|------------|----------------|
| 100      | $0.050/lead       | ~$0.051    | ~4% (break-even) |
| 500      | $0.010/lead       | ~$0.011    | ~78% |
| 1,000    | $0.005/lead       | ~$0.006    | ~89% |
| 3,000    | $0.0017/lead      | ~$0.003    | ~94% |

**Note:** Customers below ~200 leads/mo should be quoted higher per-lead rates or a minimum monthly fee; the public tier card uses €0.05 as the volume anchor (500+ leads/mo).

## Implementation

- Site copy: `cde-salesnav/public/salesnav/salesnav.js` (EN + ES i18n) and `index.html` fallbacks.
- Billing logic (future): charge Basic + Enriched per exported row; Mail only on `work_email` populated.
