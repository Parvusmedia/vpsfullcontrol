import { Actor } from 'apify';
import { flattenLead, normalizeSourceUrl } from './flatten.js';
import { createHarvestConfig, enrichRows } from './harvest.js';
import { createConfig, exportLeads } from './unipile.js';

await Actor.main(async () => {
  const input = await Actor.getInput() ?? {};

  const mode = input.mode === 'search' ? 'search' : 'list';
  const maxLeads = Math.max(1, Math.min(2000, Number(input.maxLeads ?? 100)));
  const pageDelayMs = Math.max(0, Number(input.pageDelayMs ?? 1500));
  const harvestBatchSize = Math.max(3, Math.min(15, Number(input.harvestBatchSize ?? 10)));

  const apiKey = String(input.unipileApiKey ?? process.env.UNIPILE_API_KEY ?? '').trim();
  const accountId = String(input.unipileAccountId ?? process.env.UNIPILE_ACCOUNT_ID ?? '').trim();
  const baseUrl = String(input.unipileBaseUrl ?? process.env.UNIPILE_BASE_URL ?? 'https://api.unipile.com/v2').trim();

  const harvestApiKey = String(
    input.harvestApiKey ?? process.env.HARVEST_API_KEY ?? process.env.HARVESTAPI_KEY ?? '',
  ).trim();
  const harvestBaseUrl = String(
    input.harvestBaseUrl ?? process.env.HARVEST_API_BASE ?? process.env.HARVESTAPI_BASE_URL ?? 'https://api.harvestapi.io',
  ).trim();

  if (!apiKey) {
    throw new Error('Missing Unipile API key. Set unipileApiKey input or UNIPILE_API_KEY env var.');
  }
  if (!accountId) {
    throw new Error('Missing Unipile account ID. Set unipileAccountId input or UNIPILE_ACCOUNT_ID env var.');
  }
  if (!harvestApiKey) {
    throw new Error('Missing Harvest API key. Set harvestApiKey input or HARVEST_API_KEY env var.');
  }

  const rawUrl = mode === 'search'
    ? String(input.searchUrl ?? '').trim()
    : String(input.listUrl ?? '').trim();

  if (!rawUrl) {
    throw new Error(mode === 'search'
      ? 'searchUrl is required when mode is search.'
      : 'listUrl is required when mode is list.');
  }

  const sourceUrl = normalizeSourceUrl(rawUrl, mode);
  const unipile = createConfig(baseUrl, apiKey, accountId);
  const harvest = createHarvestConfig(harvestApiKey, harvestBaseUrl);

  await Actor.setValue('INPUT_META', {
    mode,
    sourceUrl,
    maxLeads,
    accountId,
    apiVersion: unipile.isV1 ? 'v1' : 'v2',
    enrichment: 'harvest-full-profile',
    startedAt: new Date().toISOString(),
  });

  Actor.log.info(
    `Exporting up to ${maxLeads} leads from ${sourceUrl} (${mode}) → Unipile list pull + Harvest full profile (no email).`,
  );

  const rawLeads = await exportLeads(unipile, sourceUrl, mode, maxLeads, pageDelayMs);
  const basicRows = rawLeads.map((row) => flattenLead(row));

  Actor.log.info(`Unipile returned ${basicRows.length} leads. Enriching via Harvest…`);

  const enrichedRows = await enrichRows(basicRows, harvest, {
    batchSize: harvestBatchSize,
    onProgress: (done, total) => {
      if (done === total || done % harvestBatchSize === 0) {
        Actor.log.info(`Harvest profiles: ${done}/${total}`);
      }
    },
  });

  const dataset = await Actor.openDataset();
  for (const row of enrichedRows) {
    await dataset.pushData(row);
  }

  const withProfile = enrichedRows.filter((row) => String(row.profile_summary ?? '').trim() !== '').length;

  await Actor.setValue('OUTPUT', {
    ok: true,
    mode,
    sourceUrl,
    requested: maxLeads,
    exported: enrichedRows.length,
    enrichedProfiles: withProfile,
    finishedAt: new Date().toISOString(),
  });

  Actor.log.info(`Done. Exported ${enrichedRows.length} leads with Harvest full profile (${withProfile} with summary).`);
});
