// n8n Code node — retry monthly quota failures that never ran nodes (no duplicates).
const apiKey = $vars.PARVUS_N8N_REST_API_KEY;
if (!apiKey) {
  throw new Error('Falta la variable PARVUS_N8N_REST_API_KEY.');
}

const baseUrl = 'https://pmedia.app.n8n.cloud';
const lookbackHours = 24;
const maxRetries = 300;
const delayBetweenRetriesSeconds = 5;
const limitPatterns = ['execution limit reached', 'consider upgrading your plan'];

const staticData = $getWorkflowStaticData('global');
if (!staticData.retriedExecutionIds) staticData.retriedExecutionIds = {};
const retried = staticData.retriedExecutionIds;

const cutoff = Date.now() - lookbackHours * 60 * 60 * 1000;
const results = {
  scanned: 0,
  candidates: 0,
  retried: 0,
  skipped: {},
  errors: [],
};

function skip(reason) {
  results.skipped[reason] = (results.skipped[reason] || 0) + 1;
}

function isLimitFailure(payload) {
  const text = JSON.stringify(payload || {}).toLowerCase();
  if (limitPatterns.some((p) => text.includes(p))) return true;
  return text.includes('execution limit') && text.includes('upgrade');
}

function neverRanWorkflowNodes(detail) {
  const root = detail?.data ?? detail;
  const inner = root?.data ?? root;
  const result = inner?.resultData;
  if (!result) return true;
  const runData = result.runData;
  if (!runData || Object.keys(runData).length === 0) return true;
  for (const nodeRuns of Object.values(runData)) {
    if (!Array.isArray(nodeRuns)) continue;
    for (const run of nodeRuns) {
      if (run?.executionStatus === 'success') return false;
    }
  }
  const msg = String(result.error?.message || '').toLowerCase();
  return msg.includes('execution limit') || msg.includes('upgrading your plan');
}

function inLookback(ex) {
  const ts = ex.stoppedAt || ex.startedAt;
  if (!ts) return true;
  return Date.parse(ts) >= cutoff;
}

async function apiListExecutions(status, cursor) {
  const qs = { status, limit: 100 };
  if (cursor) qs.cursor = cursor;
  return await this.helpers.httpRequest({
    method: 'GET',
    url: `${baseUrl}/api/v1/executions`,
    headers: { 'X-N8N-API-KEY': apiKey, Accept: 'application/json' },
    qs,
    json: true,
  });
}

async function apiGetExecution(id) {
  return await this.helpers.httpRequest({
    method: 'GET',
    url: `${baseUrl}/api/v1/executions/${id}`,
    headers: { 'X-N8N-API-KEY': apiKey, Accept: 'application/json' },
    qs: { includeData: true },
    json: true,
  });
}

async function apiRetryExecution(id) {
  return await this.helpers.httpRequest({
    method: 'POST',
    url: `${baseUrl}/api/v1/executions/${id}/retry`,
    headers: { 'X-N8N-API-KEY': apiKey, Accept: 'application/json' },
    json: true,
  });
}

const successfulRetryParents = new Set();
let successCursor;
for (let page = 0; page < 40; page += 1) {
  let pageData;
  try {
    pageData = await apiListExecutions.call(this, 'success', successCursor);
  } catch (error) {
    results.errors.push(`list-success: ${error.message || error}`);
    break;
  }
  const items = pageData.data || [];
  if (!items.length) break;
  let stop = false;
  for (const ex of items) {
    const ts = ex.startedAt || ex.stoppedAt;
    if (ts && Date.parse(ts) < cutoff) {
      stop = true;
      break;
    }
    if (ex.retryOf && ex.status === 'success') {
      successfulRetryParents.add(String(ex.retryOf));
    }
  }
  successCursor = pageData.nextCursor;
  if (stop || !successCursor) break;
}

const toRetry = [];
let errorCursor;
while (toRetry.length < maxRetries) {
  let pageData;
  try {
    pageData = await apiListExecutions.call(this, 'error', errorCursor);
  } catch (error) {
    results.errors.push(`list-error: ${error.message || error}`);
    break;
  }
  const items = pageData.data || [];
  if (!items.length) break;

  for (const ex of items) {
    results.scanned += 1;
    const id = String(ex.id);
    if (!inLookback(ex)) continue;
    if (ex.retryOf) {
      skip('retry_child');
      continue;
    }
    if (ex.retrySuccessId) {
      skip('already_succeeded_via_retry');
      continue;
    }
    if (successfulRetryParents.has(id)) {
      skip('has_successful_retry_child');
      continue;
    }
    if (retried[id]) {
      skip('already_retried_by_ops');
      continue;
    }
    if (ex.mode === 'error') {
      skip('error_workflow');
      continue;
    }
    if (ex.mode === 'retry') {
      skip('retry_mode');
      continue;
    }

    let detail;
    try {
      detail = await apiGetExecution.call(this, id);
    } catch (error) {
      results.errors.push(`get ${id}: ${error.message || error}`);
      skip('detail_unavailable');
      continue;
    }
    if (!isLimitFailure(detail)) {
      skip('not_limit_failure');
      continue;
    }
    if (!neverRanWorkflowNodes(detail)) {
      skip('nodes_already_ran');
      continue;
    }

    results.candidates += 1;
    toRetry.push(id);
    if (toRetry.length >= maxRetries) break;
  }

  errorCursor = pageData.nextCursor;
  if (!errorCursor || toRetry.length >= maxRetries) break;
}

for (let i = 0; i < toRetry.length; i += 1) {
  const id = toRetry[i];
  try {
    await apiRetryExecution.call(this, id);
    retried[id] = new Date().toISOString();
    results.retried += 1;
  } catch (error) {
    results.errors.push(`retry ${id}: ${error.message || error}`);
  }
  if (i < toRetry.length - 1 && delayBetweenRetriesSeconds > 0) {
    await new Promise((resolve) => setTimeout(resolve, delayBetweenRetriesSeconds * 1000));
  }
}

return [{ json: results }];
