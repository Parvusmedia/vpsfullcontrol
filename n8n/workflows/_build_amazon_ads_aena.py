#!/usr/bin/env python3
"""Generate the n8n Amazon Ads Aena workflow JSON.

Target live canvas: https://pmedia.app.n8n.cloud/workflow/EkaAF0yc5VuRwtVG
The first node already receives the email; this file emits a complete importable
workflow whose trigger can replace that node, or whose later nodes can be
wired after it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SPREADSHEET_ID = "1DzDf3h0LwsQfxgDnU31iLLXGnW9wjgfaRT4uZsrBZa4"
SHEET_GID = "1035524264"
SHEET_NAME = "Amazon"
EXPECTED_RECIPIENT = "aena@pmediaplus.com"
EXISTING_WORKFLOW_URL = "https://pmedia.app.n8n.cloud/workflow/EkaAF0yc5VuRwtVG"
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    f"{SPREADSHEET_ID}/edit?gid={SHEET_GID}#gid={SHEET_GID}"
)

VALIDATE_RECIPIENT_CODE = r"""function collect(value) {
  if (value === null || value === undefined) return '';
  if (Array.isArray(value)) return value.map(collect).join(' ');
  if (typeof value === 'object') {
    const nested = [];
    for (const [key, entry] of Object.entries(value)) {
      nested.push(key, collect(entry));
    }
    return nested.join(' ');
  }
  return String(value);
}

const expected = 'aena@pmediaplus.com';
const headers = $json.headers || $json.header || {};
const haystack = [
  $json.to,
  $json.cc,
  $json.bcc,
  $json.recipients,
  $json.deliveredTo,
  headers['delivered-to'],
  headers['Delivered-To'],
  headers['x-original-to'],
  headers['X-Original-To'],
  headers['envelope-to'],
  headers['Envelope-To'],
  headers,
].map(collect).join(' ').toLowerCase();

const isAenaRecipient = haystack.includes(expected);

return {
  json: {
    ...$json,
    isAenaRecipient,
    recipientCheck: expected,
  },
};
"""

EXTRACT_URL_CODE = r"""const html = String($json.html || $json.textAsHtml || $json.text || '');
const text = String($json.text || '');
const subject = String($json.subject || '');

function decodeEntities(value) {
  return value
    .replace(/&amp;/gi, '&')
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, num) => String.fromCharCode(Number(num)));
}

function unwrap(url) {
  let current = decodeEntities(url).trim();
  for (let i = 0; i < 5; i++) {
    try {
      const parsed = new URL(current);
      const nested =
        parsed.searchParams.get('q') ||
        parsed.searchParams.get('u') ||
        parsed.searchParams.get('U') ||
        parsed.searchParams.get('url') ||
        parsed.searchParams.get('dest') ||
        parsed.searchParams.get('redirect');
      if (nested && /^https?:/i.test(nested) && nested !== current) {
        current = decodeEntities(nested);
        continue;
      }
    } catch (error) {
      break;
    }
    break;
  }
  return current;
}

function score(url) {
  const lower = url.toLowerCase();
  if (!/^https?:\/\//i.test(url)) return -100;
  if (lower.startsWith('mailto:')) return -100;
  if (/(unsubscribe|privacy|help|support|preferences|pixel|tracking|fls-na\.amazon)/i.test(lower)) return -50;
  if (/\.(png|gif|jpg|jpeg|svg|css|woff2?)(\?|$)/i.test(lower)) return -50;

  let points = 0;
  if (/(advertising\.amazon|amazonaws\.com|offline-report-storage)/i.test(lower)) points += 40;
  if (/amazon\.com/i.test(lower)) points += 10;
  if (/(download|report|csv|gzip)/i.test(lower)) points += 25;
  if (/(\.csv|\.gz)(\?|$)/i.test(lower)) points += 30;
  if (/(s3\.|signed|X-Amz-Signature)/i.test(url)) points += 20;
  return points;
}

const hrefs = [];
const hrefRe = /href\s*=\s*["']([^"']+)["']/gi;
let match;
while ((match = hrefRe.exec(html))) {
  hrefs.push(unwrap(match[1]));
}
const rawUrlRe = /https?:\/\/[^\s"'<>]+/gi;
for (const found of (html + ' ' + text).match(rawUrlRe) || []) {
  hrefs.push(unwrap(found.replace(/[),.;]+$/, '')));
}

const unique = [...new Set(hrefs.filter(Boolean))];
const ranked = unique
  .map((url) => ({ url, score: score(url) }))
  .filter((row) => row.score > 0)
  .sort((a, b) => b.score - a.score);

return {
  json: {
    emailId: $json.id,
    threadId: $json.threadId,
    subject,
    from: $json.from,
    to: $json.to,
    date: $json.date,
    isAenaRecipient: $json.isAenaRecipient,
    downloadUrl: ranked[0]?.url || '',
    candidateUrls: ranked.slice(0, 8),
  },
};
"""

PREPARE_CSV_CODE = r"""const email = $('Extraer enlace de descarga').item.json;
const binary = $input.item.binary?.data;
if (!binary) {
  throw new Error('La descarga no devolvió un fichero binario.');
}

const zlib = require('zlib');
let buffer = await this.helpers.getBinaryDataBuffer(0, 'data');
const headers = $json.headers || {};
const contentType = String(headers['content-type'] || headers['Content-Type'] || binary.mimeType || '').toLowerCase();
const contentDisposition = String(headers['content-disposition'] || headers['Content-Disposition'] || '');

function filenameFromDisposition(value) {
  const star = /filename\*\s*=\s*UTF-8''([^;]+)/i.exec(value);
  if (star) return decodeURIComponent(star[1].replace(/["']/g, ''));
  const basic = /filename\s*=\s*"?([^";]+)"?/i.exec(value);
  return basic ? basic[1] : '';
}

function sniff(buf) {
  if (buf.length >= 2 && buf[0] === 0x1f && buf[1] === 0x8b) return 'gzip';
  const text = buf.slice(0, 400).toString('utf8').toLowerCase();
  if (text.includes('<html') || text.includes('<!doctype html')) return 'html';
  return 'csv';
}

let fileName = filenameFromDisposition(contentDisposition) || binary.fileName || 'amazon-aena-report.csv';
let kind = sniff(buffer);

if (kind === 'gzip') {
  buffer = zlib.gunzipSync(buffer);
  fileName = fileName.replace(/\.gz$/i, '');
  kind = sniff(buffer);
}

if (kind === 'html') {
  const preview = buffer.slice(0, 280).toString('utf8').replace(/\s+/g, ' ');
  throw new Error(
    'El enlace no entregó el CSV (HTML de login o link caducado). Preview: ' + preview
  );
}

if (!/\.(csv|txt|tsv)$/i.test(fileName)) fileName += '.csv';

const stamp = new Date().toISOString().slice(0, 10);
const storedName = `Aena_AmazonAds_${stamp}_${fileName.replace(/[^\w.\-]+/g, '_')}`;
const prepared = await this.helpers.prepareBinaryData(buffer, storedName, 'text/csv');

return {
  json: {
    emailId: email.emailId,
    threadId: email.threadId,
    subject: email.subject,
    from: email.from,
    date: email.date,
    downloadUrl: email.downloadUrl,
    fileName: storedName,
    byteSize: buffer.length,
    contentType,
  },
  binary: { data: prepared },
};
"""

NORMALIZE_ROWS_CODE = r"""const meta = $('Preparar CSV').first().json;
const items = $input.all();

function flatten(value) {
  if (value && typeof value === 'object' && value.row && typeof value.row === 'object') {
    return value.row;
  }
  return value;
}

const rows = [];
for (const item of items) {
  const payload = flatten(item.json);
  if (payload && typeof payload === 'object' && Object.keys(payload).length) {
    rows.push(payload);
  }
}

const usable = rows.filter((row) =>
  row && typeof row === 'object' && Object.values(row).some((v) => v !== '' && v !== null && v !== undefined)
);

if (!usable.length) {
  return [{ json: { _skip_sheets: true, emailId: meta.emailId, fileName: meta.fileName } }];
}

return usable.map((row) => {
  const mapped = {};
  for (const [key, value] of Object.entries(row)) {
    if (key.startsWith('_')) continue;
    mapped[key] = value;
  }
  mapped.Plataforma = 'Amazon';
  mapped.ImportadoAt = new Date().toISOString();
  mapped._skip_sheets = false;
  mapped._emailId = meta.emailId;
  mapped._fileName = meta.fileName;
  return { json: mapped };
});
"""

TRIGGER_CLEAR_CODE = r"""const items = $input.all();
return [{ json: { ok: true, rowCount: items.length, emailId: items[0].json._emailId } }];
"""

RESTORE_ROWS_CODE = r"""return $('Normalizar filas').all().filter((item) => item.json._skip_sheets !== true);
"""


def sticky(node_id: str, name: str, content: str, x: int, y: int, w: int, h: int, color: int = 7) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [x, y],
        "parameters": {
            "content": content,
            "height": h,
            "width": w,
            "color": color,
        },
    }


def rlc_id(value: str, mode: str = "id", cached: str | None = None) -> dict:
    data = {"__rl": True, "value": value, "mode": mode}
    if cached:
        data["cachedResultName"] = cached
    return data


def gmail_creds() -> dict:
    return {"gmailOAuth2": {"id": "", "name": "Gmail emiliano@parvusmedia.com"}}


def sheets_creds() -> dict:
    return {"googleSheetsOAuth2Api": {"id": "", "name": "Google Sheets emiliano@parvusmedia.com"}}


def if_not_empty(left: str, condition_id: str) -> dict:
    return {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "strict",
                "version": 2,
            },
            "conditions": [
                {
                    "id": condition_id,
                    "leftValue": left,
                    "rightValue": "",
                    "operator": {
                        "type": "string",
                        "operation": "notEmpty",
                        "singleValue": True,
                    },
                }
            ],
            "combinator": "and",
        },
        "options": {},
    }


def if_boolean_true(left: str, condition_id: str) -> dict:
    return {
        "conditions": {
            "options": {
                "caseSensitive": True,
                "leftValue": "",
                "typeValidation": "loose",
                "version": 2,
            },
            "conditions": [
                {
                    "id": condition_id,
                    "leftValue": left,
                    "rightValue": True,
                    "operator": {
                        "type": "boolean",
                        "operation": "true",
                        "singleValue": True,
                    },
                }
            ],
            "combinator": "and",
        },
        "options": {},
    }


nodes = [
    sticky(
        "note-setup",
        "Nota setup",
        "\n".join(
            [
                "## Amazon Ads Aena — pegar en el escenario existente",
                "",
                f"Canvas vivo: {EXISTING_WORKFLOW_URL}",
                "El **primer nodo de ese workflow ya recibe el correo**. No dupliques el Gmail Trigger:",
                "1. Importa este JSON (`Workflows → Import from File`) o copia los nodos desde `Validar destinatario`.",
                "2. Conecta la salida del trigger actual → `Validar destinatario`.",
                "3. Credenciales OAuth de **emiliano@parvusmedia.com**: Gmail + Google Sheets.",
                "4. Destinatario obligatorio: `aena@pmediaplus.com` (To/Cc/Delivered-To).",
                "5. Cada día se **vacía** la pestaña Amazon y se pega el CSV nuevo.",
                "",
                f"Sheet: `{SHEET_NAME}` — {SPREADSHEET_URL}",
            ]
        ),
        x=-720,
        y=-480,
        w=620,
        h=380,
        color=5,
    ),
    sticky(
        "note-flow",
        "Nota flujo",
        "\n".join(
            [
                "## Flujo",
                "",
                "Trigger (existente) → validar `aena@pmediaplus.com` → extraer `href` del HTML → GET del CSV → (gunzip si viene `.gz`) → Clear pestaña Amazon → Append filas → marcar leído.",
                "",
                "Si el enlace de Amazon exige login o está caducado, `Preparar CSV` falla a propósito.",
            ]
        ),
        x=-40,
        y=-480,
        w=460,
        h=260,
        color=6,
    ),
    {
        "id": "gmail-trigger",
        "name": "Gmail Trigger Aena",
        "type": "n8n-nodes-base.gmailTrigger",
        "typeVersion": 1.3,
        "position": [-560, 40],
        "notes": (
            "En EkaAF0yc5VuRwtVG el trigger ya existe. Usa este nodo solo si "
            "importas el workflow completo; si no, conéctalo al trigger actual y bórralo."
        ),
        "notesInFlow": True,
        "credentials": gmail_creds(),
        "parameters": {
            "authentication": "oAuth2",
            "event": "messageReceived",
            "simple": False,
            "filters": {
                "q": 'from:("Amazon Display Advertising Analytics") subject:"Report available: Aena"',
                "readStatus": "unread",
                "sender": "Amazon Display Advertising Analytics",
            },
            "options": {"downloadAttachments": False},
            "pollTimes": {
                "item": [{"mode": "everyX", "value": 15, "unit": "minutes"}]
            },
        },
    },
    {
        "id": "validate-recipient",
        "name": "Validar destinatario",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-280, 40],
        "parameters": {
            "mode": "runOnceForEachItem",
            "language": "javaScript",
            "jsCode": VALIDATE_RECIPIENT_CODE,
        },
    },
    {
        "id": "if-recipient",
        "name": "Destinatario Aena?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [0, 40],
        "parameters": if_boolean_true("={{ $json.isAenaRecipient }}", "is-aena"),
    },
    {
        "id": "ignore-other",
        "name": "Ignorar otro destinatario",
        "type": "n8n-nodes-base.noOp",
        "typeVersion": 1,
        "position": [280, 260],
        "parameters": {},
        "notes": f"El correo no va a {EXPECTED_RECIPIENT}; no se toca la Sheet.",
        "notesInFlow": True,
    },
    {
        "id": "extract-url",
        "name": "Extraer enlace de descarga",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [280, 40],
        "parameters": {
            "mode": "runOnceForEachItem",
            "language": "javaScript",
            "jsCode": EXTRACT_URL_CODE,
        },
    },
    {
        "id": "if-url",
        "name": "Hay enlace?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [520, 40],
        "parameters": if_not_empty("={{ $json.downloadUrl }}", "has-download-url"),
    },
    {
        "id": "no-url",
        "name": "Sin enlace de descarga",
        "type": "n8n-nodes-base.stopAndError",
        "typeVersion": 1,
        "position": [760, 260],
        "parameters": {
            "errorType": "errorMessage",
            "errorMessage": "={{ 'No se encontró un enlace de descarga en: ' + ($json.subject || 'sin asunto') }}",
        },
    },
    {
        "id": "download-report",
        "name": "Descargar CSV",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [760, 40],
        "parameters": {
            "method": "GET",
            "url": "={{ $json.downloadUrl }}",
            "authentication": "none",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "User-Agent",
                        "value": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                    },
                    {
                        "name": "Accept",
                        "value": "text/csv,application/gzip,text/plain,*/*",
                    },
                ]
            },
            "options": {
                "redirect": {
                    "redirect": {
                        "followRedirects": True,
                        "maxRedirects": 10,
                    }
                },
                "response": {
                    "response": {
                        "fullResponse": True,
                        "responseFormat": "file",
                        "outputPropertyName": "data",
                    }
                },
                "timeout": 120000,
            },
        },
    },
    {
        "id": "prepare-csv",
        "name": "Preparar CSV",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1000, 40],
        "parameters": {
            "mode": "runOnceForEachItem",
            "language": "javaScript",
            "jsCode": PREPARE_CSV_CODE,
        },
    },
    {
        "id": "extract-csv",
        "name": "Parsear CSV",
        "type": "n8n-nodes-base.extractFromFile",
        "typeVersion": 1,
        "position": [1240, 40],
        "alwaysOutputData": True,
        "parameters": {
            "operation": "csv",
            "binaryPropertyName": "data",
            "options": {
                "headerRow": True,
                "relaxQuotes": True,
            },
        },
    },
    {
        "id": "normalize",
        "name": "Normalizar filas",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1480, 40],
        "parameters": {
            "mode": "runOnceForAllItems",
            "language": "javaScript",
            "jsCode": NORMALIZE_ROWS_CODE,
        },
    },
    {
        "id": "if-rows",
        "name": "Hay filas?",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [1720, 40],
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "loose",
                    "version": 2,
                },
                "conditions": [
                    {
                        "id": "not-skip",
                        "leftValue": "={{ $json._skip_sheets }}",
                        "rightValue": True,
                        "operator": {
                            "type": "boolean",
                            "operation": "false",
                            "singleValue": True,
                        },
                    }
                ],
                "combinator": "and",
            },
            "options": {},
        },
    },
    {
        "id": "trigger-clear",
        "name": "Una vez para vaciar",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1960, -80],
        "parameters": {
            "mode": "runOnceForAllItems",
            "language": "javaScript",
            "jsCode": TRIGGER_CLEAR_CODE,
        },
    },
    {
        "id": "clear-sheet",
        "name": "Vaciar pestaña Amazon",
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": [2200, -80],
        "credentials": sheets_creds(),
        "parameters": {
            "resource": "sheet",
            "operation": "clear",
            "documentId": rlc_id(SPREADSHEET_ID, "id", "Copia de Aena V3"),
            "sheetName": rlc_id(SHEET_GID, "id", SHEET_NAME),
            "clear": "wholeSheet",
            "keepFirstRow": False,
        },
    },
    {
        "id": "restore-rows",
        "name": "Restaurar filas CSV",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2440, -80],
        "parameters": {
            "mode": "runOnceForAllItems",
            "language": "javaScript",
            "jsCode": RESTORE_ROWS_CODE,
        },
    },
    {
        "id": "append-sheets",
        "name": "Pegar CSV en Amazon",
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "position": [2680, -80],
        "credentials": sheets_creds(),
        "parameters": {
            "resource": "sheet",
            "operation": "append",
            "documentId": rlc_id(SPREADSHEET_ID, "id", "Copia de Aena V3"),
            "sheetName": rlc_id(SHEET_GID, "id", SHEET_NAME),
            "columns": {
                "mappingMode": "autoMapInputData",
                "value": {},
                "matchingColumns": [],
                "schema": [],
                "attemptToConvertTypes": False,
                "convertFieldsToString": False,
            },
            "options": {
                "useAppend": True,
                "cellFormat": "USER_ENTERED",
                "handlingExtraData": "insertInNewColumn",
            },
        },
    },
    {
        "id": "mark-read",
        "name": "Marcar correo leido",
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "position": [2920, 40],
        "executeOnce": True,
        "credentials": gmail_creds(),
        "parameters": {
            "authentication": "oAuth2",
            "resource": "message",
            "operation": "markAsRead",
            "messageId": "={{ $('Gmail Trigger Aena').item.json.id }}",
        },
        "notes": (
            "Si enganchas el trigger existente de EkaAF0yc5VuRwtVG, cambia esta "
            "expresión al nombre real de ese nodo."
        ),
        "notesInFlow": True,
    },
]


def conn(target: str, index: int = 0) -> dict:
    return {"node": target, "type": "main", "index": index}


connections = {
    "Gmail Trigger Aena": {"main": [[conn("Validar destinatario")]]},
    "Validar destinatario": {"main": [[conn("Destinatario Aena?")]]},
    "Destinatario Aena?": {
        "main": [
            [conn("Extraer enlace de descarga")],
            [conn("Ignorar otro destinatario")],
        ]
    },
    "Extraer enlace de descarga": {"main": [[conn("Hay enlace?")]]},
    "Hay enlace?": {
        "main": [
            [conn("Descargar CSV")],
            [conn("Sin enlace de descarga")],
        ]
    },
    "Descargar CSV": {"main": [[conn("Preparar CSV")]]},
    "Preparar CSV": {"main": [[conn("Parsear CSV")]]},
    "Parsear CSV": {"main": [[conn("Normalizar filas")]]},
    "Normalizar filas": {"main": [[conn("Hay filas?")]]},
    "Hay filas?": {
        "main": [
            [conn("Una vez para vaciar")],
            [conn("Marcar correo leido")],
        ]
    },
    "Una vez para vaciar": {"main": [[conn("Vaciar pestaña Amazon")]]},
    "Vaciar pestaña Amazon": {"main": [[conn("Restaurar filas CSV")]]},
    "Restaurar filas CSV": {"main": [[conn("Pegar CSV en Amazon")]]},
    "Pegar CSV en Amazon": {"main": [[conn("Marcar correo leido")]]},
}

workflow = {
    "name": "Amazon Ads Aena → Google Sheets",
    "active": False,
    "nodes": nodes,
    "connections": connections,
    "pinData": {},
    "settings": {
        "executionOrder": "v1",
        "timezone": "Europe/Madrid",
        "callerPolicy": "workflowsFromSameOwner",
        "saveManualExecutions": True,
        "saveDataErrorExecution": "all",
        "saveDataSuccessExecution": "all",
        "executionTimeout": 3600,
    },
    "meta": {
        "templateCredsSetupCompleted": False,
        "description": (
            "Extiende el escenario EkaAF0yc5VuRwtVG: valida destinatario "
            "aena@pmediaplus.com, descarga el CSV del enlace del correo Amazon "
            "Display Advertising Analytics y reemplaza la pestaña Amazon del "
            "spreadsheet Copia de Aena V3."
        ),
    },
    "tags": [
        {"name": "amazon-ads"},
        {"name": "aena"},
        {"name": "gmail"},
    ],
}


def validate(data: dict) -> list[str]:
    errors: list[str] = []
    names = [n["name"] for n in data["nodes"] if n["type"] != "n8n-nodes-base.stickyNote"]
    if len(names) != len(set(names)):
        errors.append("duplicate node names")

    known = {n["name"] for n in data["nodes"]}
    for source, outputs in data["connections"].items():
        if source not in known:
            errors.append(f"connection source missing: {source}")
        for branch in outputs.get("main", []):
            for target in branch:
                if target["node"] not in known:
                    errors.append(f"connection target missing: {target['node']}")

    required = [
        "Gmail Trigger Aena",
        "Validar destinatario",
        "Destinatario Aena?",
        "Extraer enlace de descarga",
        "Descargar CSV",
        "Parsear CSV",
        "Vaciar pestaña Amazon",
        "Pegar CSV en Amazon",
        "Marcar correo leido",
    ]
    for name in required:
        if name not in known:
            errors.append(f"required node missing: {name}")

    trigger = next(n for n in data["nodes"] if n["name"] == "Gmail Trigger Aena")
    if trigger["parameters"].get("simple") is not False:
        errors.append("Gmail trigger must not simplify (HTML body required)")

    append = next(n for n in data["nodes"] if n["name"] == "Pegar CSV en Amazon")
    if append["parameters"]["operation"] != "append":
        errors.append("Amazon write must append after clear")
    clear = next(n for n in data["nodes"] if n["name"] == "Vaciar pestaña Amazon")
    if clear["parameters"].get("keepFirstRow") is not False:
        errors.append("Clear must drop old headers so the CSV owns the schema")

    return errors


def main() -> int:
    errors = validate(workflow)
    out = Path(__file__).with_name("amazon-ads-aena-to-google-sheets.json")
    out.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size} bytes, {len(nodes)} nodes)")
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("Validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
