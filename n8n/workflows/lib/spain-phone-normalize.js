/**
 * Prosegur — normalización teléfono España + hash Meta (PHONE).
 * Copiar el cuerpo de normalizeSpainPhone / sha256Phone en nodos Code de n8n.
 */
'use strict';

function normalizeSpainPhone(raw) {
  if (raw == null || String(raw).trim() === '') {
    return { valid: false, reason: 'empty' };
  }
  let d = String(raw).replace(/\D/g, '');
  if (d.startsWith('0034')) {
    d = d.slice(2);
  }
  if (d.length === 9 && /^[6789]/.test(d)) {
    d = '34' + d;
  }
  if (d.length === 11 && d.startsWith('34')) {
    const national = d.slice(2);
    if (/^[6789]\d{8}$/.test(national)) {
      return { valid: true, phone_digits: d };
    }
  }
  return { valid: false, reason: 'invalid_spain' };
}

function sha256Phone(phoneDigits) {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(phoneDigits, 'utf8').digest('hex');
}

module.exports = { normalizeSpainPhone, sha256Phone };
