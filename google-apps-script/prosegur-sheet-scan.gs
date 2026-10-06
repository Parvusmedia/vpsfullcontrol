/**
 * Prosegur — lectura diaria (últimas 500 filas × 2 pestañas) → webhook n8n
 *
 * Spreadsheet: 1Fna1muuArgG_eaehXPAyl9AnRm6VOjcQc6JyO05-y_4
 * Pestañas: Prosegur, leadsconhorario_soportesexternos
 *
 * Script properties (opcional): PROSEGUR_N8N_WEBHOOK_URL (default: prosegur-phone-register)
 *
 * Trigger: time-driven → Day timer → 1am–2am (o la hora que prefieras).
 *
 * Ejecutar debug: prosegurDebugStepByStep()  (o prosegurDryRun, mismo efecto)
 * Ver logs: Apps Script → Ejecuciones → clic en la fila → Registro (Cloud)
 * Probar fechas: prosegurTestParseDates
 */

var DEFAULT_WEBHOOK_URL = 'https://pmedia.app.n8n.cloud/webhook/prosegur-phone-register';
var SHEET_TABS = ['Prosegur', 'leadsconhorario_soportesexternos'];
var TAIL_ROWS = 500;
var LOOKBACK_HOURS = 24;
var DEDUP_PROP = 'prosegur_sent_phone_digits_v1';
/** Máx. ejemplos por motivo de descarte en prosegurDebugStepByStep */
var DEBUG_SAMPLES_PER_REASON = 5;

/**
 * Ejemplos soportados en columna Fecha:
 *   05-10-2026 18:32
 *   06-10-2026 9:20
 *   05-10-2026
 *   2026-10-05T18:34:44.829+02:00
 *   (también Date nativo de Google Sheets)
 */
function parseProsegurFecha(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (value instanceof Date) {
    return isNaN(value.getTime()) ? null : value;
  }

  var s = String(value).trim();
  if (!s) {
    return null;
  }

  // ISO-8601 con zona: 2026-10-05T18:34:44.829+02:00
  if (/^\d{4}-\d{2}-\d{2}T/.test(s)) {
    var iso = new Date(s);
    return isNaN(iso.getTime()) ? null : iso;
  }

  // dd-MM-yyyy [HH:mm] (hora opcional, día/mes con 1-2 dígitos)
  var eu = s.match(/^(\d{1,2})-(\d{1,2})-(\d{4})(?:\s+(\d{1,2}):(\d{2}))?$/);
  if (eu) {
    var day = parseInt(eu[1], 10);
    var mon = parseInt(eu[2], 10);
    var yr = parseInt(eu[3], 10);
    var hr = eu[4] !== undefined ? parseInt(eu[4], 10) : 0;
    var min = eu[5] !== undefined ? parseInt(eu[5], 10) : 0;
    var local = new Date(yr, mon - 1, day, hr, min, 0, 0);
    return isNaN(local.getTime()) ? null : local;
  }

  // yyyy-MM-dd HH:mm:ss (por si aparece)
  var ymd = s.match(/^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?$/);
  if (ymd) {
    var d2 = new Date(
      parseInt(ymd[1], 10),
      parseInt(ymd[2], 10) - 1,
      parseInt(ymd[3], 10),
      ymd[4] !== undefined ? parseInt(ymd[4], 10) : 0,
      ymd[5] !== undefined ? parseInt(ymd[5], 10) : 0,
      ymd[6] !== undefined ? parseInt(ymd[6], 10) : 0,
      0
    );
    return isNaN(d2.getTime()) ? null : d2;
  }

  var fallback = new Date(s);
  return isNaN(fallback.getTime()) ? null : fallback;
}

/** Misma regla que n8n (España). Devuelve phone_digits o null. */
function normalizeSpainPhoneDigits(raw) {
  if (raw === null || raw === undefined || String(raw).trim() === '') {
    return null;
  }
  var d = String(raw).replace(/\D/g, '');
  if (d.indexOf('0034') === 0) {
    d = d.substring(2);
  }
  if (d.length === 9 && /^[6789]/.test(d)) {
    d = '34' + d;
  }
  if (d.length === 11 && d.indexOf('34') === 0) {
    var national = d.substring(2);
    if (/^[6789]\d{8}$/.test(national)) {
      return d;
    }
  }
  return null;
}

function loadSentPhones_() {
  var raw = PropertiesService.getScriptProperties().getProperty(DEDUP_PROP);
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw);
  } catch (e) {
    return {};
  }
}

function saveSentPhones_(map) {
  PropertiesService.getScriptProperties().setProperty(DEDUP_PROP, JSON.stringify(map));
}

function collectRowsFromSheet_(sheet, sheetTab, cutoff, debug) {
  var stats = {
    sheet_tab: sheetTab,
    last_row: 0,
    start_row: 0,
    scanned: 0,
    accepted: 0,
    skip_empty_phone: 0,
    skip_no_fecha_column: 0,
    skip_fecha_empty: 0,
    skip_fecha_unparseable: 0,
    skip_fecha_before_cutoff: 0,
    skip_invalid_phone: 0,
    headers: [],
    col_fecha: -1,
    col_telefono: -1,
    col_source: -1,
  };
  var samples = {
    skip_empty_phone: [],
    skip_fecha_empty: [],
    skip_fecha_unparseable: [],
    skip_fecha_before_cutoff: [],
    skip_invalid_phone: [],
    accepted: [],
  };

  function samplePush(bucket, rowNumber, detail) {
    if (samples[bucket].length >= DEBUG_SAMPLES_PER_REASON) {
      return;
    }
    samples[bucket].push('row ' + rowNumber + ': ' + detail);
  }

  var lastRow = sheet.getLastRow();
  stats.last_row = lastRow;
  if (lastRow < 2) {
    return debug ? { rows: [], stats: stats, samples: samples } : [];
  }

  var startRow = Math.max(2, lastRow - TAIL_ROWS + 1);
  stats.start_row = startRow;
  var width = sheet.getLastColumn();
  var headers = sheet.getRange(1, 1, 1, width).getValues()[0];
  stats.headers = headers.map(String);
  var colFecha = headers.indexOf('Fecha');
  var colTel = headers.indexOf('telefono');
  var colSource = headers.indexOf('source');
  stats.col_fecha = colFecha;
  stats.col_telefono = colTel;
  stats.col_source = colSource;

  if (colTel < 0) {
    if (debug) {
      return { rows: [], stats: stats, samples: samples };
    }
    Logger.log('Tab %s: falta columna telefono', sheetTab);
    return [];
  }
  if (colFecha < 0) {
    stats.skip_no_fecha_column = lastRow - startRow + 1;
  }

  var numRows = lastRow - startRow + 1;
  var values = sheet.getRange(startRow, 1, numRows, width).getValues();
  var out = [];

  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    var rowNumber = startRow + i;
    stats.scanned++;

    var rawTel = row[colTel];
    if (rawTel === '' || rawTel === null || rawTel === undefined) {
      stats.skip_empty_phone++;
      samplePush('skip_empty_phone', rowNumber, 'telefono vacío');
      continue;
    }

    if (colFecha < 0) {
      continue;
    }

    var rawFecha = row[colFecha];
    if (rawFecha === '' || rawFecha === null || rawFecha === undefined) {
      stats.skip_fecha_empty++;
      samplePush('skip_fecha_empty', rowNumber, 'Fecha vacía tel=' + rawTel);
      continue;
    }

    var parsedDate = parseProsegurFecha(rawFecha);
    if (!parsedDate) {
      stats.skip_fecha_unparseable++;
      samplePush('skip_fecha_unparseable', rowNumber, 'Fecha="' + rawFecha + '" tel=' + rawTel);
      continue;
    }
    if (parsedDate.getTime() < cutoff.getTime()) {
      stats.skip_fecha_before_cutoff++;
      if (debug && samples.skip_fecha_before_cutoff.length < DEBUG_SAMPLES_PER_REASON) {
        samplePush(
          'skip_fecha_before_cutoff',
          rowNumber,
          'Fecha=' + parsedDate.toISOString() + ' < cutoff tel=' + rawTel
        );
      }
      continue;
    }

    var digits = normalizeSpainPhoneDigits(rawTel);
    if (!digits) {
      stats.skip_invalid_phone++;
      samplePush('skip_invalid_phone', rowNumber, 'tel="' + rawTel + '" no ES válido');
      continue;
    }

    var source =
      colSource >= 0 && row[colSource] !== '' && row[colSource] != null
        ? String(row[colSource])
        : sheetTab;

    var lead = {
      sheet_tab: sheetTab,
      row_number: rowNumber,
      phone_digits: digits,
      telefono: String(rawTel),
      source: String(source).slice(0, 120),
      fecha_ms: parsedDate.getTime(),
      fecha_iso: parsedDate.toISOString(),
    };
    out.push(lead);
    stats.accepted++;
    samplePush(
      'accepted',
      rowNumber,
      digits + ' ' + lead.fecha_iso + ' src=' + lead.source
    );
  }

  if (debug) {
    return { rows: out, stats: stats, samples: samples };
  }
  return out;
}

/**
 * Dedup en memoria: un lead por phone_digits (el de Fecha más antigua en la ventana).
 */
function dedupeBatchByPhone_(rows) {
  var best = {};
  rows.forEach(function (r) {
    var prev = best[r.phone_digits];
    if (!prev || r.fecha_ms < prev.fecha_ms) {
      best[r.phone_digits] = r;
    }
  });
  return Object.keys(best).map(function (k) {
    return best[k];
  });
}

function prosegurCollectSummary_(dryRun) {
  var props = PropertiesService.getScriptProperties();
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var cutoff = new Date(Date.now() - LOOKBACK_HOURS * 60 * 60 * 1000);
  var allRows = [];
  var tabStats = [];

  SHEET_TABS.forEach(function (tabName) {
    var sheet = ss.getSheetByName(tabName);
    if (!sheet) {
      tabStats.push(tabName + ': NO EXISTE');
      return;
    }
    var chunk = collectRowsFromSheet_(sheet, tabName, cutoff, false);
    tabStats.push(
      tabName + ': lastRow=' + sheet.getLastRow() + ' ventana24h=' + chunk.length + ' (cola ' + TAIL_ROWS + ')'
    );
    allRows = allRows.concat(chunk);
  });

  var uniqueInBatch = dedupeBatchByPhone_(allRows);
  var sentMap = loadSentPhones_();
  var toSend = uniqueInBatch.filter(function (r) {
    return !sentMap[r.phone_digits];
  });

  var lines = [
    '=== prosegur ' + (dryRun ? 'DRY-RUN' : 'PUSH') + ' ===',
    'Spreadsheet: ' + ss.getName(),
    'Cutoff 24h: ' + cutoff.toISOString(),
    'Webhook: ' + (props.getProperty('PROSEGUR_N8N_WEBHOOK_URL') || DEFAULT_WEBHOOK_URL),
  ].concat(tabStats).concat([
    'Filas en ventana (total): ' + allRows.length,
    'Teléfonos únicos en batch: ' + uniqueInBatch.length,
    'Ya enviados (dedup script): ' + (uniqueInBatch.length - toSend.length),
    'A enviar ahora: ' + toSend.length,
  ]);

  if (toSend.length > 0 && toSend.length <= 5) {
    toSend.forEach(function (r) {
      lines.push('  → ' + r.phone_digits + ' row ' + r.row_number + ' ' + r.source);
    });
  }

  return { lines: lines, toSend: toSend, sentMap: sentMap };
}

/** Solo diagnóstico: no llama al webhook. Ver registro (Executions → tu run → Registro). */
function prosegurDryRun() {
  prosegurDebugStepByStep(false);
}

/**
 * Debug paso a paso (ejecutar desde el editor).
 * @param {boolean=} verboseSamples — true: más detalle por fila rechazada
 */
function prosegurDebugStepByStep(verboseSamples) {
  verboseSamples = verboseSamples !== false;
  var props = PropertiesService.getScriptProperties();
  var webhook = props.getProperty('PROSEGUR_N8N_WEBHOOK_URL') || DEFAULT_WEBHOOK_URL;
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var cutoff = new Date(Date.now() - LOOKBACK_HOURS * 60 * 60 * 1000);
  var now = new Date();

  Logger.log('========== PASO 0: entorno ==========');
  Logger.log('Hora script: %s (tz %s)', now.toISOString(), Session.getScriptTimeZone());
  Logger.log('Spreadsheet: %s', ss.getName());
  Logger.log('Spreadsheet ID: %s', ss.getId());
  Logger.log('TAIL_ROWS=%s LOOKBACK_HOURS=%s', TAIL_ROWS, LOOKBACK_HOURS);
  Logger.log('Cutoff >= %s', cutoff.toISOString());
  Logger.log('Webhook: %s', webhook);

  var allRows = [];
  var sentMap = loadSentPhones_();
  Logger.log('========== PASO 1: dedup persistente ==========');
  Logger.log('Teléfonos ya marcados enviados: %s', Object.keys(sentMap).length);

  SHEET_TABS.forEach(function (tabName, tabIndex) {
    Logger.log('========== PASO 2.%s: pestaña "%s" ==========', tabIndex + 1, tabName);
    var sheet = ss.getSheetByName(tabName);
    if (!sheet) {
      Logger.log('ERROR: no existe la pestaña "%s"', tabName);
      return;
    }

    var result = collectRowsFromSheet_(sheet, tabName, cutoff, true);
    var st = result.stats;
    Logger.log('Headers (%s cols): %s', st.headers.length, st.headers.join(' | '));
    Logger.log('Column indices: Fecha=%s telefono=%s source=%s', st.col_fecha, st.col_telefono, st.col_source);
    Logger.log('Rango leído: filas %s → %s (lastRow=%s)', st.start_row, st.last_row, st.last_row);
    Logger.log('--- contadores ---');
    Logger.log('  escaneadas: %s', st.scanned);
    Logger.log('  aceptadas (24h + tel OK): %s', st.accepted);
    Logger.log('  skip telefono vacío: %s', st.skip_empty_phone);
    Logger.log('  skip sin columna Fecha: %s', st.skip_no_fecha_column);
    Logger.log('  skip Fecha vacía: %s', st.skip_fecha_empty);
    Logger.log('  skip Fecha no parseable: %s', st.skip_fecha_unparseable);
    Logger.log('  skip Fecha anterior a cutoff: %s', st.skip_fecha_before_cutoff);
    Logger.log('  skip teléfono no España: %s', st.skip_invalid_phone);

    if (verboseSamples) {
      logSampleBlock_('Ejemplos ACEPTADOS', result.samples.accepted);
      logSampleBlock_('Ejemplos Fecha antigua', result.samples.skip_fecha_before_cutoff);
      logSampleBlock_('Ejemplos Fecha ilegible', result.samples.skip_fecha_unparseable);
      logSampleBlock_('Ejemplos tel inválido', result.samples.skip_invalid_phone);
      logSampleBlock_('Ejemplos tel vacío', result.samples.skip_empty_phone);
    }

    allRows = allRows.concat(result.rows);
  });

  Logger.log('========== PASO 3: dedup en batch ==========');
  var uniqueInBatch = dedupeBatchByPhone_(allRows);
  Logger.log('Filas aceptadas total: %s', allRows.length);
  Logger.log('Teléfonos únicos (1 por número): %s', uniqueInBatch.length);

  var skippedSent = [];
  var toSend = [];
  uniqueInBatch.forEach(function (r) {
    if (sentMap[r.phone_digits]) {
      skippedSent.push(r);
    } else {
      toSend.push(r);
    }
  });

  Logger.log('========== PASO 4: envío webhook ==========');
  Logger.log('Omitidos (ya enviados antes): %s', skippedSent.length);
  skippedSent.slice(0, DEBUG_SAMPLES_PER_REASON).forEach(function (r) {
    Logger.log('  ya enviado: %s row %s (guardado %s)', r.phone_digits, r.row_number, sentMap[r.phone_digits]);
  });
  Logger.log('Listos para POST n8n: %s', toSend.length);
  toSend.slice(0, 15).forEach(function (r) {
    Logger.log('  → POST phone=%s source=%s row=%s tab=%s', r.telefono, r.source, r.row_number, r.sheet_tab);
  });
  if (toSend.length > 15) {
    Logger.log('  … y %s más', toSend.length - 15);
  }

  Logger.log('========== PASO 5: conclusión ==========');
  if (toSend.length === 0) {
    Logger.log('Nada que enviar. Revisa contadores PASO 2 (¿cutoff? ¿Fecha? ¿dedup?)');
    Logger.log('Prueba prosegurResetSentPhones() si el dedup script bloquea todo.');
  } else {
    Logger.log('OK: ejecuta prosegurDailySheetPush para enviar %s teléfonos', toSend.length);
  }
  Logger.log('========== FIN debug ==========');
}

function logSampleBlock_(title, lines) {
  if (!lines || lines.length === 0) {
    return;
  }
  Logger.log('--- %s ---', title);
  lines.forEach(function (line) {
    Logger.log('  %s', line);
  });
}

function prosegurDryRunLegacy() {
  var s = prosegurCollectSummary_(true);
  s.lines.forEach(function (line) {
    Logger.log(line);
  });
  Logger.log('=== FIN dry-run ===');
}

function prosegurDailySheetPush() {
  var props = PropertiesService.getScriptProperties();
  var webhook = props.getProperty('PROSEGUR_N8N_WEBHOOK_URL') || DEFAULT_WEBHOOK_URL;
  var summary = prosegurCollectSummary_(false);
  summary.lines.forEach(function (line) {
    Logger.log(line);
  });

  var toSend = summary.toSend;
  var sentMap = summary.sentMap;

  if (toSend.length === 0) {
    Logger.log('=== FIN: nada que enviar ===');
    return;
  }

  var ok = 0;
  var fail = 0;

  toSend.forEach(function (lead) {
    var payload = JSON.stringify({
      phone: lead.telefono,
      source: lead.source,
    });
    var res = UrlFetchApp.fetch(webhook, {
      method: 'post',
      contentType: 'application/json',
      payload: payload,
      muteHttpExceptions: true,
    });
    var code = res.getResponseCode();
    if (code >= 200 && code < 300) {
      sentMap[lead.phone_digits] = new Date().toISOString();
      ok++;
    } else {
      fail++;
      Logger.log(
        'FAIL %s row %s HTTP %s %s',
        lead.phone_digits,
        lead.row_number,
        code,
        res.getContentText().slice(0, 200)
      );
    }
    Utilities.sleep(150);
  });

  saveSentPhones_(sentMap);
  Logger.log('=== FIN push: ok=%s fail=%s ===', ok, fail);
}

/** Ejecutar desde el editor para validar parseProsegurFecha. */
function prosegurTestParseDates() {
  var samples = [
    '05-10-2026 18:32',
    '2026-10-05T18:34:44.829+02:00',
    '2026-10-05T19:04:06.350+02:00',
    '05-10-2026 19:07',
    '05-10-2026',
    '2026-10-05T19:53:49.253+02:00',
    '06-10-2026 9:20',
    '2026-10-06T09:31:43.822+02:00',
    '06-10-2026',
  ];
  samples.forEach(function (s) {
    var d = parseProsegurFecha(s);
    Logger.log('%s → %s', s, d ? d.toISOString() : 'NULL');
  });
}

/** Borrar dedup persistente (solo mantenimiento). */
function prosegurResetSentPhones() {
  PropertiesService.getScriptProperties().deleteProperty(DEDUP_PROP);
  Logger.log('Cleared %s', DEDUP_PROP);
}
