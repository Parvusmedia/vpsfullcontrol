/**
 * Prosegur — escaneo incremental de leads (Prosegur + leadsconhorario_soportesexternos)
 *
 * Instalar: Extensiones → Apps Script en el spreadsheet
 * 1Fna1muuArgG_eaehXPAyl9AnRm6VOjcQc6JyO05-y_4
 *
 * Script properties (Project settings → Script properties):
 *   PROSEGUR_N8N_WEBHOOK_URL  = https://pmedia.app.n8n.cloud/webhook/prosegur-sheet-ingest
 *   PROSEGUR_N8N_SECRET        = (mismo valor que n8n Variables / header)
 *
 * Trigger: time-driven, cada hora (o cada 15 min).
 */

var SHEETS = [
  { name: 'Prosegur', propKey: 'lastRow_Prosegur' },
  { name: 'leadsconhorario_soportesexternos', propKey: 'lastRow_leadsconhorario' },
];

var LOOKBACK_MS = 24 * 60 * 60 * 1000;
/** Si el cursor falla, no leer más de esta cola de filas. */
var MAX_TAIL_ROWS = 2000;

function prosegurHourlyScan() {
  var props = PropertiesService.getScriptProperties();
  var webhook = props.getProperty('PROSEGUR_N8N_WEBHOOK_URL');
  var secret = props.getProperty('PROSEGUR_N8N_SECRET');
  if (!webhook || !secret) {
    throw new Error('Faltan PROSEGUR_N8N_WEBHOOK_URL o PROSEGUR_N8N_SECRET en Script properties');
  }

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var batch = [];
  var cutoff = new Date(Date.now() - LOOKBACK_MS);

  SHEETS.forEach(function (cfg) {
    var sheet = ss.getSheetByName(cfg.name);
    if (!sheet) return;

    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return;

    var stored = parseInt(props.getProperty(cfg.propKey) || '1', 10);
    var startRow = Math.max(2, Math.min(stored + 1, lastRow - MAX_TAIL_ROWS));
    if (startRow > lastRow) return;

    var width = sheet.getLastColumn();
    var headers = sheet.getRange(1, 1, 1, width).getValues()[0];
    var colFecha = headers.indexOf('Fecha');
    var colTel = headers.indexOf('telefono');
    var colSource = headers.indexOf('source');
    if (colTel < 0) return;

    var numRows = lastRow - startRow + 1;
    var values = sheet.getRange(startRow, 1, numRows, width).getValues();

    for (var i = 0; i < values.length; i++) {
      var row = values[i];
      var rowNumber = startRow + i;
      var fecha = colFecha >= 0 ? row[colFecha] : null;
      if (fecha instanceof Date && fecha < cutoff) continue;
      if (!(fecha instanceof Date) && fecha) {
        var parsed = new Date(fecha);
        if (!isNaN(parsed.getTime()) && parsed < cutoff) continue;
      }

      var telefono = row[colTel];
      if (telefono === '' || telefono == null) continue;

      batch.push({
        sheet_tab: cfg.name,
        row_number: rowNumber,
        telefono: String(telefono),
        source: colSource >= 0 ? String(row[colSource] || cfg.name) : cfg.name,
        fecha: fecha instanceof Date ? fecha.toISOString() : String(fecha || ''),
      });
    }

    props.setProperty(cfg.propKey, String(lastRow));
  });

  if (batch.length === 0) {
    Logger.log('prosegurHourlyScan: nothing to send');
    return;
  }

  var payload = JSON.stringify({ leads: batch, sent_at: new Date().toISOString() });
  var res = UrlFetchApp.fetch(webhook, {
    method: 'post',
    contentType: 'application/json',
    headers: { 'X-Prosegur-Register-Secret': secret },
    payload: payload,
    muteHttpExceptions: true,
  });

  Logger.log(
    'prosegurHourlyScan: sent %s rows, HTTP %s %s',
    batch.length,
    res.getResponseCode(),
    res.getContentText().slice(0, 500)
  );
}
