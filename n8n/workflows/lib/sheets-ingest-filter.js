/**
 * Lógica compartida (referencia) para filtro 24h + filas ya procesadas.
 * Copiada en el nodo Code "Filter 24h rows" del workflow n8n.
 */
'use strict';

const LOOKBACK_MS = 24 * 60 * 60 * 1000;

function parseSheetDate(value) {
  if (value == null || value === '') return null;
  if (typeof value === 'number' && Number.isFinite(value)) {
    return new Date((value - 25569) * 86400000);
  }
  const s = String(value).trim();
  if (!s) return null;
  let d = new Date(s);
  if (!Number.isNaN(d.getTime())) return d;
  const m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})(?:[ T](\d{1,2}):(\d{2})(?::(\d{2}))?)?/);
  if (m) {
    const day = +m[1];
    const mon = +m[2];
    let yr = +m[3];
    if (yr < 100) yr += 2000;
    d = new Date(yr, mon - 1, day, +(m[4] || 0), +(m[5] || 0), +(m[6] || 0));
    if (!Number.isNaN(d.getTime())) return d;
  }
  return null;
}

module.exports = { LOOKBACK_MS, parseSheetDate };
