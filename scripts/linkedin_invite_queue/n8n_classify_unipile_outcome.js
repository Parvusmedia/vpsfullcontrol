const source = $('Random Wait From NocoDB').first().json;
const rule = source.automation_rule || {};
const response = $json || {};
const err = response.error || {};
const httpStatus = Number(err.status || response.statusCode || 0);
const errCode = String(err.code || err.type || '').toLowerCase();
const errMsg = String(err.message || err.description || response.message || '');
const haystack = `${httpStatus} ${errCode} ${errMsg}`.toLowerCase();

let outcome = 'success';
if (response.error || (httpStatus >= 400 && httpStatus !== 0)) {
  if (
    haystack.includes('already_invited_recently') ||
    haystack.includes('already_invited') ||
    haystack.includes('should delay new invitation') ||
    haystack.includes('invitation has already been sent')
  ) {
    outcome = 'already_invited';
  } else if (
    httpStatus === 429 ||
    haystack.includes('rate limit') ||
    haystack.includes('too many') ||
    haystack.includes('throttl')
  ) {
    outcome = 'rate_limit';
  } else if (
    httpStatus === 400 &&
    (haystack.includes('user id does not match') || haystack.includes("does not match provider"))
  ) {
    outcome = 'invalid_provider';
  } else if (
    httpStatus === 422 ||
    haystack.includes('cannot_resend') ||
    haystack.includes('cannot_resend_yet') ||
    (haystack.includes('limit') && haystack.includes('invit'))
  ) {
    outcome = 'provider_limit';
  } else {
    outcome = 'failed';
  }
}

const basePauseHours = Number(source.pause_hours ?? rule.pause_hours ?? 24);
const pauseHours = outcome === 'rate_limit'
  ? Math.max(2, Math.min(6, Math.round(basePauseHours / 6)))
  : basePauseHours;

const needsPause = outcome === 'provider_limit' || outcome === 'rate_limit';
const closeSource = outcome === 'success' || outcome === 'already_invited' || outcome === 'invalid_provider';
const pausedUntilIso = needsPause
  ? new Date(Date.now() + pauseHours * 3600 * 1000).toISOString()
  : null;

const logStatus = outcome === 'success'
  ? 'success'
  : (outcome === 'already_invited' || outcome === 'invalid_provider')
    ? 'skipped'
    : needsPause
      ? 'limit_reached'
      : 'failed';

const inviteSent = closeSource
  ? 'connection_sent'
  : needsPause
    ? 'connection_pending'
    : 'connection_error';

const logPayload = {
  timestamp: new Date().toISOString(),
  action_date: source.action_date,
  client_name: source.client_name,
  workflow_name: source.workflow_name,
  execution_id: $execution.id,
  account_id: source.account_id,
  account_label: source.account_label,
  provider: 'unipile',
  action_type: 'linkedin_connection_invite',
  target_id: source.provider_id,
  target_url: source.linkedin_url || source.profile_url || '',
  source_row_id: String(source.source_row_id || ''),
  status: logStatus,
  http_status: outcome === 'success' ? 201 : httpStatus,
  error_code: outcome === 'success' ? '' : (errCode || String(httpStatus || outcome)),
  error_message: outcome === 'success'
    ? ''
    : (outcome === 'already_invited' || outcome === 'invalid_provider')
      ? `${outcome}: ${errMsg || errCode || httpStatus}`
      : needsPause
        ? `Provider pause (${outcome}) until ${pausedUntilIso}: ${errMsg || errCode || httpStatus}`
        : String(errMsg || errCode || response.error || 'unknown_error'),
  limit_key: source.limit_key,
};

return [{
  json: {
    ...source,
    outcome,
    needs_pause: needsPause,
    skip_sheet_update: needsPause,
    pause_patch: needsPause ? {
      Id: source.limits_record_id || rule.Id,
      paused_until: pausedUntilIso,
      pause_reason: `${outcome}:${errCode || httpStatus || 'provider_limit'}`,
    } : null,
    log_payload: logPayload,
    unipile_response: response,
    invite_sent: inviteSent,
    unipile_connection_id:
      response.invitation_id ||
      response.id ||
      response.object_id ||
      response.data?.id ||
      '',
    unipile_error_message: closeSource ? '' : logPayload.error_message,
  }
}];
