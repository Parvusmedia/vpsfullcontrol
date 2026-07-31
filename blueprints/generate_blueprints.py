#!/usr/bin/env python3
"""Generate cleaned Make + n8n blueprints for Argentina Prosegur Meta leads."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path

OUT = Path("/workspace/blueprints")
ART = Path("/opt/cursor/artifacts/blueprints")
ART.mkdir(parents=True, exist_ok=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1TTjRCb5YaJ0h7NPNwAdkvdkk564I0-Cj9HjYbCNFk-w"
APIFY_URL = (
    "https://api.apify.com/v2/actor-tasks/"
    "customary_viburnum~prosegur-latam-argentina-comments/"
    "run-sync-get-dataset-items"
    "?token=REPLACE_WITH_APIFY_TOKEN"
)
PARAMS_URL = (
    "https://www.prosegur.com.ar/landings/lead-ads/lead-ads-argentina.html"
    "?utm_source=meta&utm_medium=meta-leadads"
    "&utm_campaign=AR_PERFORMANCE_FB_ALARMAS_HOGAR_LEADS-GEN_CONV_AO"
    "&utm_product=INTERIOR_LAL-INTERESES_FORMS"
    "&utm_offer=PPV_JUL_NINA"
    "&utm_brand=54000926"
    "&utm_target=performance"
)
N8N_WEBHOOK = "https://pmedia.app.n8n.cloud/webhook/argentina-prosegur-meta-leads"
WEBHOOK_PATH = "argentina-prosegur-meta-leads"

GOOGLE_CRED = {
    "googleSheetsOAuth2Api": {
        "id": "IUffqNWvLrjbinjA",
        "name": "Pmedia Dvelopment Google",
    }
}
SMTP_CRED = {
    "smtp": {
        "id": "bI1OPZXssQ2rWLBK",
        "name": "No Reply Pmediaplus",
    }
}

DATE_EXPR = (
    "={{ $now.setZone('America/Argentina/Buenos_Aires')"
    ".toFormat('dd-MM-yyyy HH:mm') }}"
)


def nid() -> str:
    return str(uuid.uuid4())


def conn(src: str, *targets: str, output: int = 0) -> dict:
    return {
        src: {
            "main": [
                *[[] for _ in range(output)],
                [{"node": t, "type": "main", "index": 0} for t in targets],
            ]
        }
    }


def merge_connections(*parts: dict) -> dict:
    out: dict = {}
    for part in parts:
        for src, payload in part.items():
            out.setdefault(src, {"main": []})
            src_main = out[src]["main"]
            for i, branch in enumerate(payload["main"]):
                while len(src_main) <= i:
                    src_main.append([])
                src_main[i].extend(branch)
    return out


INPUTDATA_CODE = r'''/**
 * Argentina Prosegur Meta leads — normalize payload + build Apify comment.
 * Accepts:
 *  1) New Make JSON body: { lead, phone_e164, params_url, aid }
 *  2) Legacy: query.jsonpayload / body.jsonpayload + body.params_url
 */

const crypto = require('crypto');

function generateUuid() {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.floor(Math.random() * 16);
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function normalizeValue(value) {
  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    if (value.length === 1) return normalizeValue(value[0]);
    const parts = value.map(normalizeValue).filter((v) => v !== null && v !== '');
    return parts.length ? parts.join(', ') : null;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed === '' ? null : trimmed;
  }
  return value ?? null;
}

function normalizeKey(key) {
  return String(key)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[¿?¡!:'"]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_+/g, '_');
}

function normalizeObject(object = {}) {
  if (!object || typeof object !== 'object' || Array.isArray(object)) return {};
  return Object.entries(object).reduce((acc, [k, v]) => {
    acc[normalizeKey(k)] = normalizeValue(v);
    return acc;
  }, {});
}

function formatText(value) {
  const normalized = normalizeValue(value);
  if (normalized === null) return null;
  return String(normalized).replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
}

function mapSecuritySituation(value) {
  const normalized = normalizeValue(value);
  if (!normalized) return null;
  const key = normalizeKey(normalized);
  const options = {
    sufri_un_robo_recientemente: 'robo reciente',
    hubo_robos_en_mi_zona: 'robos en zona',
    quiero_prevenir: 'prevención',
    es_una_propiedad_nueva: 'propiedad nueva',
  };
  return options[key] ?? formatText(normalized);
}

function mapPreferredNextStep(value) {
  const normalized = normalizeValue(value);
  if (!normalized) return null;
  const key = normalizeKey(normalized);
  const options = {
    quiero_que_un_asesor_me_contacte_para_cotizar: 'contactar para cotizar',
    quiero_evaluarlo_mas_adelante: 'evaluar más adelante',
  };
  return options[key] ?? formatText(normalized);
}

function buildComment({ currentSecuritySituation, preferredNextStep, preferredContactTime }) {
  const lines = [];
  const securitySituation = mapSecuritySituation(currentSecuritySituation);
  const nextStep = mapPreferredNextStep(preferredNextStep);
  const contactTime = formatText(preferredContactTime);
  if (securitySituation) lines.push(`Situación: ${securitySituation}`);
  if (nextStep) lines.push(`Avance: ${nextStep}`);
  if (contactTime) lines.push(`Horario: ${contactTime}`);
  const comment = lines.join('\n');
  if (!comment) return null;
  return comment.length <= 170 ? comment : `${comment.slice(0, 167).trimEnd()}...`;
}

function capitalize(value) {
  const text = formatText(value);
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function normalizeCityName(input) {
  if (!input || typeof input !== 'string') return '';
  const words = input.trim().split(/\s+/);
  let city = words.slice(0, 2).join(' ');
  if (city.replace(/\s+/g, '').length <= 3) city += '_aaa';
  return city;
}

function normalizePersonName(str) {
  if (str == null) return 'na';
  let s = String(str)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z ]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (!s) return 'na';
  return s.split(' ').filter(Boolean).slice(0, 4).join(' ') || 'na';
}

function normalizePhoneDigits(str) {
  if (str == null) return null;
  const digits = String(str).replace(/\D/g, '');
  return digits || null;
}

function parseLeadPayload(input) {
  const body = input.body || {};

  if (body.lead && typeof body.lead === 'object' && !Array.isArray(body.lead)) {
    return body.lead;
  }

  for (const raw of [body.jsonpayload, input.query?.jsonpayload]) {
    if (!raw) continue;
    if (typeof raw === 'object' && !Array.isArray(raw)) return raw;
    if (typeof raw === 'string') {
      try {
        return JSON.parse(raw);
      } catch (error) {
        throw new Error(`No se pudo parsear jsonpayload: ${error.message}`);
      }
    }
  }

  if (body.leadgenId || body.formId || body.data) {
    return body;
  }

  return {};
}

return items.map((item) => {
  const input = item.json ?? {};
  const body = input.body || {};
  const payload = parseLeadPayload(input);
  const leadData = normalizeObject(payload.data || {});
  const webhookBody = normalizeObject(body);

  const installationPlace =
    leadData.donde_queres_instalar_el_sistema_de_alarmas ?? null;
  const currentSecuritySituation =
    leadData.cual_es_tu_situacion_actual_de_seguridad ?? null;
  const preferredNextStep = leadData.como_te_gustaria_avanzar ?? null;
  const preferredContactTime =
    leadData.selecciona_la_franja_horaria_que_queres_que_te_contacten ?? null;

  const rawPhone =
    body.phone_e164 ||
    leadData.phone ||
    webhookBody.phone ||
    null;

  const fullName = leadData.full_name ?? null;
  const city = leadData.city ?? null;

  const normalized = {
    uuid: generateUuid(),
    aid: normalizeValue(body.aid) || 'ps',
    platform: normalizeValue(payload.platform),
    leadgen_id: normalizeValue(payload.leadgenId),
    form_id: normalizeValue(payload.formId ?? body.formid),
    is_organic: typeof payload.isOrganic === 'boolean' ? payload.isOrganic : null,
    ad_id: normalizeValue(payload.adId),
    ad_name: normalizeValue(payload.adName),
    adset_id: normalizeValue(payload.adsetId),
    adset_name: normalizeValue(payload.adsetName),
    campaign_id: normalizeValue(payload.campaignId),
    campaign_name: normalizeValue(payload.campaignName),
    page_id: normalizeValue(payload.pageId),
    date_created: normalizeValue(payload.dateCreated),
    full_name: fullName,
    name_normalized: normalizePersonName(fullName),
    email: typeof leadData.email === 'string' ? leadData.email.toLowerCase() : null,
    phone: rawPhone,
    phone_digits: normalizePhoneDigits(rawPhone),
    city,
    ciudad: normalizeCityName(city || ''),
    utm_source: leadData.utm_source ?? null,
    utm_medium: leadData.utm_medium ?? null,
    utm_campaign: leadData.utm_campaign ?? null,
    utm_product: leadData.utm_product ?? null,
    utm_offer: leadData.utm_offer ?? null,
    utm_brand: leadData.utm_brand ?? null,
    utm_target: leadData.utm_target ?? null,
    installation_place: installationPlace,
    hogar_negocio: capitalize(installationPlace),
    current_security_situation: currentSecuritySituation,
    preferred_next_step: preferredNextStep,
    preferred_contact_time: preferredContactTime,
    comment: buildComment({
      currentSecuritySituation,
      preferredNextStep,
      preferredContactTime,
    }),
    params_url: webhookBody.params_url ?? body.params_url ?? null,
    source_label: [
      leadData.utm_source || 'meta',
      normalizeValue(payload.platform) || '',
    ].filter(Boolean).join('-'),
    webhook_url: normalizeValue(input.webhookUrl),
    form_data: leadData,
  };

  return { json: normalized };
});
'''

VALIDATE_PHONE_CODE = r'''const settings = $('Settings').first().json;
const lead = $('InputData').first().json;
const countryCode = settings.country_phone_code || '+54';
const phonePattern = settings.phone_pattern || '549\\d{10}';
const phoneNumber = lead.phone;

if (!phoneNumber) {
  return [{ json: { valid: false, error: 'No phone number provided', lead } }];
}

const cleanPhone = String(phoneNumber).replace(/[^0-9+]/g, '');
const fullValidationPattern = new RegExp(`^\\+?${phonePattern}$`);
let formattedPhone = cleanPhone;
let isValid = false;

if (fullValidationPattern.test(cleanPhone.replace(/^\+/, '+') === cleanPhone ? cleanPhone : cleanPhone)) {
  // try with and without leading +
}

if (fullValidationPattern.test(cleanPhone)) {
  formattedPhone = cleanPhone.startsWith('+') ? cleanPhone : `+${cleanPhone.replace(/^\+/, '')}`;
  isValid = true;
} else if (fullValidationPattern.test(cleanPhone.replace(/^\+/, ''))) {
  formattedPhone = `+${cleanPhone.replace(/^\+/, '')}`;
  isValid = true;
} else {
  const digits = cleanPhone.replace(/\D/g, '');
  const withCc = countryCode.replace('+', '') + digits.replace(new RegExp(`^${countryCode.replace('+', '')}`), '');
  if (fullValidationPattern.test(withCc) || fullValidationPattern.test('+' + withCc)) {
    formattedPhone = '+' + withCc.replace(/^\+/, '');
    isValid = true;
  }
}

if (isValid && !String(formattedPhone).startsWith('+')) {
  formattedPhone = '+' + formattedPhone;
}

return [{
  json: {
    valid: isValid,
    phone: cleanPhone,
    e164: formattedPhone,
    original: phoneNumber,
    country_code: countryCode,
  }
}];
'''

# Fix validate phone - the middle block is messy. Rewrite cleaner:
VALIDATE_PHONE_CODE = r'''const settings = $('Settings').first().json;
const lead = $('InputData').first().json;
const countryCode = String(settings.country_phone_code || '+54');
const phonePattern = String(settings.phone_pattern || '549\\d{10}');
const phoneNumber = lead.phone;

if (!phoneNumber) {
  return [{ json: { valid: false, error: 'No phone number provided' } }];
}

const digits = String(phoneNumber).replace(/\D/g, '');
const pattern = new RegExp(`^${phonePattern}$`);
const candidates = [
  digits,
  digits.startsWith('54') ? digits : `54${digits}`,
  digits.startsWith('549') ? digits : `549${digits.replace(/^54/, '')}`,
];

let e164 = null;
for (const candidate of candidates) {
  if (pattern.test(candidate)) {
    e164 = `+${candidate}`;
    break;
  }
}

return [{
  json: {
    valid: Boolean(e164),
    phone: digits,
    e164,
    original: phoneNumber,
    country_code: countryCode,
    error: e164 ? null : 'Invalid Argentine phone number',
  }
}];
'''

BUSINESS_HOURS_CODE = r'''const settings = $('Settings').first().json;
if (!settings || !settings.timezone) {
  throw new Error('Settings must contain timezone configuration');
}

const timezone = settings.timezone;
const startHour = settings.startHour ?? 9;
const startMinute = settings.startMinute ?? 0;
const endHour = settings.endHour ?? 21;
const endMinute = settings.endMinute ?? 59;

const now = new Date();
const localTime = new Date(now.toLocaleString('en-US', { timeZone: timezone }));
const hours = localTime.getHours();
const minutes = localTime.getMinutes();
const totalMinutes = hours * 60 + minutes;
const startTotalMinutes = startHour * 60 + startMinute;
const endTotalMinutes = endHour * 60 + endMinute;
const isBusinessHours = totalMinutes >= startTotalMinutes && totalMinutes <= endTotalMinutes;

return [{
  json: {
    currentTime: localTime.toLocaleString('es-AR', { timeZone: timezone }),
    timezone,
    hours,
    minutes,
    isBusinessHours,
    businessHours: {
      start: `${String(startHour).padStart(2, '0')}:${String(startMinute).padStart(2, '0')}`,
      end: `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`,
    },
  }
}];
'''


def sheet_cols(value: dict, matching: list | None = None) -> dict:
    return {
        "mappingMode": "defineBelow",
        "value": value,
        "matchingColumns": matching or [],
        "schema": [],
        "attemptToConvertTypes": False,
        "convertFieldsToString": False,
    }


def build_n8n() -> dict:
    nodes = []

    def add(node):
        nodes.append(node)
        return node["name"]

    add({
        "parameters": {
            "httpMethod": "POST",
            "path": WEBHOOK_PATH,
            "options": {},
        },
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [-1800, 0],
        "id": nid(),
        "name": "Webhook",
        "webhookId": WEBHOOK_PATH,
    })

    add({
        "parameters": {"jsCode": INPUTDATA_CODE},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-1560, 0],
        "id": nid(),
        "name": "InputData",
    })

    add({
        "parameters": {
            "mode": "raw",
            "jsonOutput": json.dumps(
                {
                    "sheet_id": SHEET_URL,
                    "task_url": APIFY_URL,
                    "timezone": "America/Argentina/Buenos_Aires",
                    "startHour": 9,
                    "startMinute": 0,
                    "endHour": 21,
                    "endMinute": 59,
                    "country_phone_code": "+54",
                    "phone_pattern": r"549\d{10}",
                    "recieve_failuare_emails": (
                        "zezoamer113@gmail.com,"
                        "parvusmedia-development@gmail.com,"
                        "emiliano@parvusmedia.com"
                    ),
                    "recieve_success_emails": "damian.andrei@prosegur.com",
                },
                ensure_ascii=False,
                indent=2,
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [-1320, 0],
        "id": nid(),
        "name": "Settings",
    })

    add({
        "parameters": {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "rawinput",
                "mode": "name",
            },
            "columns": sheet_cols({
                "nombre": "={{ $('InputData').item.json.full_name }}",
                "telefono": "={{ $('InputData').item.json.phone }}",
                "email": "={{ $('InputData').item.json.email }}",
                "params_url": "={{ $('InputData').item.json.params_url }}",
                "campana": "={{ $('InputData').item.json.campaign_name }}",
                "adset": "={{ $('InputData').item.json.utm_product }}",
                "source": "={{ $('InputData').item.json.source_label }}",
                "leadid": "={{ $('InputData').item.json.leadgen_id }}",
                "WS": "pendiente",
                "wsmessage": "pendiente",
                "whatsapp_push": "pendiente",
                "plantillawhatsapp": "pendiente",
                "uuid": "={{ $('InputData').item.json.uuid }}",
                "ciudad": "={{ $('InputData').item.json.city }}",
                "hogar_negocio": "={{ $('InputData').item.json.installation_place }}",
                "estado_actual": "={{ $('InputData').item.json.current_security_situation }}",
                "horario": "={{ $('InputData').item.json.preferred_contact_time }}",
                "proximopaso": "={{ $('InputData').item.json.preferred_next_step }}",
                "comment": "={{ $('InputData').item.json.comment }}",
                "custom1": "={{ $('InputData').item.json.webhook_url }}",
                "fecha": DATE_EXPR,
            }),
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [-1080, 0],
        "id": nid(),
        "name": "LogRawInput",
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "leadsconhorario",
                "mode": "name",
            },
            "columns": sheet_cols({
                "aid": "={{ $('InputData').item.json.aid }}",
                "nombre": "={{ $('InputData').item.json.full_name }}",
                "Fecha": DATE_EXPR,
                "telefono": "={{ $('InputData').item.json.phone }}",
                "email": "={{ $('InputData').item.json.email }}",
                "params_url": "={{ $('InputData').item.json.params_url }}",
                "campana": "={{ $('InputData').item.json.campaign_name }}",
                "adset": "={{ $('InputData').item.json.adset_name }}",
                "adname": "={{ $('InputData').item.json.ad_name }}",
                "formid": "={{ $('InputData').item.json.form_id }}",
                "source": "={{ $('InputData').item.json.source_label }}",
                "leadid": "={{ $('InputData').item.json.leadgen_id }}",
                "WS": "pendiente",
                "horario": "={{ $('InputData').item.json.preferred_contact_time }}",
                "ciudad": "={{ $('InputData').item.json.city }}",
                "dónde_querés_instalar_el_sistema_de_alarmas": "={{ $('InputData').item.json.installation_place }}",
                "¿cuál_es_tu_situación_actual_de_seguridad?": "={{ $('InputData').item.json.current_security_situation }}",
                "¿cómo_te_gustaría_avanzar?": "={{ $('InputData').item.json.preferred_next_step }}",
                "Column 20": "={{ $('InputData').item.json.comment }}",
                "uuid": "={{ $('InputData').item.json.uuid }}",
                "EstadoEnvio": "pendiente",
            }),
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [-840, 0],
        "id": nid(),
        "name": "LogLeadsConHorario",
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {"jsCode": VALIDATE_PHONE_CODE},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-600, 0],
        "id": nid(),
        "name": "ValidatePhone",
    })

    add({
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2,
                },
                "conditions": [{
                    "id": nid(),
                    "leftValue": "={{ $json.valid }}",
                    "rightValue": "",
                    "operator": {
                        "type": "boolean",
                        "operation": "true",
                        "singleValue": True,
                    },
                }],
                "combinator": "and",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [-360, 0],
        "id": nid(),
        "name": "IfPhoneValid",
    })

    add({
        "parameters": {
            "fromEmail": "hola@parvusmedia.com",
            "toEmail": "={{ $('Settings').first().json.recieve_failuare_emails }}",
            "subject": "=Teléfono inválido AR - {{ $('InputData').item.json.leadgen_id }}",
            "emailFormat": "text",
            "text": (
                "=Lead con teléfono inválido\n"
                "Nombre: {{ $('InputData').item.json.full_name }}\n"
                "Tel: {{ $('InputData').item.json.phone }}\n"
                "Lead ID: {{ $('InputData').item.json.leadgen_id }}\n"
                "Error: {{ $json.error }}"
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.emailSend",
        "typeVersion": 2.1,
        "position": [-120, 220],
        "id": nid(),
        "name": "EmailInvalidPhone",
        "credentials": deepcopy(SMTP_CRED),
    })

    add({
        "parameters": {"jsCode": BUSINESS_HOURS_CODE},
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-120, -120],
        "id": nid(),
        "name": "CalculateBusinessHours",
    })

    add({
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "strict",
                    "version": 2,
                },
                "conditions": [{
                    "id": nid(),
                    "leftValue": "={{ $json.isBusinessHours }}",
                    "rightValue": "",
                    "operator": {
                        "type": "boolean",
                        "operation": "true",
                        "singleValue": True,
                    },
                }],
                "combinator": "and",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [120, -120],
        "id": nid(),
        "name": "IfBusinessHours",
    })

    add({
        "parameters": {
            "content": (
                "## Fuera de horario\n"
                "El lead ya quedó en `rawinput` + `leadsconhorario`.\n"
                "No se llama a Apify fuera de 09:00–21:59 ART."
            ),
            "height": 200,
            "width": 320,
        },
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [360, 80],
        "id": nid(),
        "name": "NoteOutsideHours",
    })

    add({
        "parameters": {
            "amount": 20,
            "unit": "seconds",
        },
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "position": [360, -200],
        "id": nid(),
        "name": "Wait20s",
        "webhookId": nid(),
    })

    add({
        "parameters": {
            "url": "={{ $('Settings').first().json.task_url }}",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": (
                "={\n"
                "  \"ciudad\": {{ JSON.stringify($('InputData').item.json.ciudad) }},\n"
                "  \"comuna\": \"\",\n"
                "  \"email\": {{ JSON.stringify($('InputData').item.json.email) }},\n"
                "  \"hogar_negocio\": {{ JSON.stringify($('InputData').item.json.hogar_negocio) }},\n"
                "  \"name\": {{ JSON.stringify($('InputData').item.json.name_normalized) }},\n"
                "  \"comment\": {{ JSON.stringify($('InputData').item.json.comment) }},\n"
                "  \"phone\": {{ JSON.stringify($('ValidatePhone').item.json.e164 || $('InputData').item.json.phone) }},\n"
                "  \"url\": {{ JSON.stringify($('InputData').item.json.params_url) }}\n"
                "}"
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [600, -200],
        "id": nid(),
        "name": "CallApify",
        "onError": "continueErrorOutput",
    })

    add({
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
                        "id": nid(),
                        "leftValue": "={{ $json.status }}",
                        "rightValue": 200,
                        "operator": {"type": "number", "operation": "equals"},
                    },
                    {
                        "id": nid(),
                        "leftValue": "={{ $json.message }}",
                        "rightValue": "The Phone Pushed Successfully",
                        "operator": {
                            "type": "string",
                            "operation": "equals",
                            "name": "filter.operator.equals",
                        },
                    },
                ],
                "combinator": "or",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [840, -200],
        "id": nid(),
        "name": "IfApifySuccess",
    })

    add({
        "parameters": {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "lead2landing",
                "mode": "name",
            },
            "columns": sheet_cols({
                "aid": "={{ $('InputData').item.json.aid }}",
                "telefono": "={{ $('ValidatePhone').item.json.e164 }}",
                "campana": "={{ $('InputData').item.json.campaign_name }}",
                "adset": "={{ $('InputData').item.json.ad_name }}",
                "source": "={{ $('InputData').item.json.platform }}",
                "leadid": "={{ $('InputData').item.json.leadgen_id }}",
                "WS": "={{ $('CallApify').item.json.status }}",
                "wsmessage": "={{ $('CallApify').item.json.message }}",
                "nombre": "={{ $('InputData').item.json.full_name }}",
                "fecha": DATE_EXPR,
                "email": "={{ $('InputData').item.json.email }}",
                "params_url": "={{ $('InputData').item.json.params_url }}",
                "ciudad": "={{ $('InputData').item.json.ciudad }}",
                "hogar_negocio": "={{ $('InputData').item.json.hogar_negocio }}",
                "custom1": "={{ $('InputData').item.json.comment }}",
                "cid": "={{ $('InputData').item.json.form_id }}",
                "estado_actual": "={{ $('InputData').item.json.preferred_contact_time }}",
                "uuid": "={{ $('InputData').item.json.uuid }}",
            }),
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [1080, -320],
        "id": nid(),
        "name": "LogLead2Landing",
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {
            "fromEmail": "hola@parvusmedia.com",
            "toEmail": "={{ $('Settings').first().json.recieve_success_emails }}",
            "subject": (
                "=Ads Facebook - {{ $('ValidatePhone').item.json.e164 }}"
                " - {{ $('InputData').item.json.city }}"
            ),
            "emailFormat": "text",
            "text": (
                "=Nuevo Lead:\n"
                "Fecha: {{ $now }}\n\n"
                "------------------------------------------------------\n"
                "Nombre: {{ $('InputData').item.json.full_name }}\n"
                "Telefono: {{ $('ValidatePhone').item.json.e164 }}\n"
                "Email: {{ $('InputData').item.json.email }}\n"
                "Ciudad: {{ $('InputData').item.json.city }}\n"
                "Tipo de Inmueble: {{ $('InputData').item.json.hogar_negocio }}\n"
                "Situación: {{ $('InputData').item.json.current_security_situation }}\n"
                "Avance: {{ $('InputData').item.json.preferred_next_step }}\n"
                "Horario: {{ $('InputData').item.json.preferred_contact_time }}\n"
                "Comment:\n{{ $('InputData').item.json.comment }}\n\n"
                "Origen: Marketing y Comunicaciones\n"
                "Suborigen: Ads Facebook - Platform {{ $('InputData').item.json.platform }}\n"
                "Campaña: {{ $('InputData').item.json.campaign_name }}\n"
                "Anuncio: {{ $('InputData').item.json.ad_name }}\n"
                "Leadid: {{ $('InputData').item.json.leadgen_id }}\n"
                "Resultado Apify: {{ $('CallApify').item.json.message }}\n"
                "------------------------------------------------------"
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.emailSend",
        "typeVersion": 2.1,
        "position": [1320, -320],
        "id": nid(),
        "name": "EmailSuccess",
        "credentials": deepcopy(SMTP_CRED),
    })

    add({
        "parameters": {
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "reintentos",
                "mode": "name",
            },
            "filtersUI": {
                "values": [{
                    "lookupColumn": "telefono",
                    "lookupValue": "={{ String($('ValidatePhone').item.json.e164 || $('InputData').item.json.phone).trim() }}",
                }]
            },
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [1080, -40],
        "id": nid(),
        "name": "SearchReintentos",
        "alwaysOutputData": True,
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {
            "aggregate": "aggregateAllItemData",
            "options": {},
        },
        "type": "n8n-nodes-base.aggregate",
        "typeVersion": 1,
        "position": [1320, -40],
        "id": nid(),
        "name": "AggregateReintentos",
    })

    add({
        "parameters": {
            "conditions": {
                "options": {
                    "caseSensitive": True,
                    "leftValue": "",
                    "typeValidation": "loose",
                    "version": 2,
                },
                "conditions": [{
                    "id": nid(),
                    "leftValue": "={{ ($json.data || []).length }}",
                    "rightValue": 0,
                    "operator": {"type": "number", "operation": "equals"},
                }],
                "combinator": "and",
            },
            "options": {},
        },
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [1560, -40],
        "id": nid(),
        "name": "IfNewRetry",
    })

    add({
        "parameters": {
            "operation": "append",
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "reintentos",
                "mode": "name",
            },
            "columns": sheet_cols({
                "date": DATE_EXPR,
                "telefono": "={{ $('ValidatePhone').item.json.e164 }}",
                "params_url": "={{ $('InputData').item.json.params_url }}",
                "campana": "={{ $('InputData').item.json.campaign_name }}",
                "estado": "pendiente",
                "source": "={{ $('InputData').item.json.platform }}",
                "reintento": "1",
                "leadid": "={{ $('InputData').item.json.leadgen_id }}",
                "ciudad": "={{ $('InputData').item.json.ciudad }}",
                "hogar_negocio": "={{ $('InputData').item.json.hogar_negocio }}",
                "formid": "={{ $('InputData').item.json.form_id }}",
                "email": "={{ $('InputData').item.json.email }}",
                "nombre": "={{ $('InputData').item.json.full_name }}",
                "webhook": "={{ $('InputData').item.json.webhook_url }}",
                "message": "={{ $('CallApify').item.json.message }}",
                "uuid": "={{ $('InputData').item.json.uuid }}",
            }),
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [1800, -160],
        "id": nid(),
        "name": "AppendReintento",
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {
            "operation": "update",
            "documentId": {
                "__rl": True,
                "value": "={{ $('Settings').first().json.sheet_id }}",
                "mode": "url",
            },
            "sheetName": {
                "__rl": True,
                "value": "reintentos",
                "mode": "name",
            },
            "columns": sheet_cols(
                {
                    "telefono": "={{ String($('ValidatePhone').item.json.e164).trim() }}",
                    "estado": "pendiente",
                    "reintento": "={{ Number(($('AggregateReintentos').first().json.data[0] || {}).reintento || 0) + 1 }}",
                    "message": "={{ $('CallApify').item.json.message }}",
                },
                matching=["telefono"],
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.6,
        "position": [1800, 80],
        "id": nid(),
        "name": "UpdateReintento",
        "credentials": deepcopy(GOOGLE_CRED),
    })

    add({
        "parameters": {
            "fromEmail": "hola@parvusmedia.com",
            "toEmail": "={{ $('Settings').first().json.recieve_failuare_emails }}",
            "subject": "=Error Apify AR - {{ $('InputData').item.json.source_label }}",
            "emailFormat": "text",
            "text": (
                "=Status: {{ $('CallApify').item.json.status }}\n"
                "Tel: {{ $('ValidatePhone').item.json.e164 }}\n"
                "Fuente: {{ $('InputData').item.json.source_label }}\n"
                "Lead: {{ $('InputData').item.json.leadgen_id }}\n"
                "Error:\n{{ $('CallApify').item.json.message }}"
            ),
            "options": {},
        },
        "type": "n8n-nodes-base.emailSend",
        "typeVersion": 2.1,
        "position": [2040, -40],
        "id": nid(),
        "name": "EmailError",
        "credentials": deepcopy(SMTP_CRED),
    })

    add({
        "parameters": {
            "content": (
                "## Argentina Prosegur Meta → Apify Comments\n\n"
                "1. Webhook único desde Make\n"
                "2. Normaliza form + arma `comment`\n"
                "3. Log sheets\n"
                "4. Valida teléfono AR (+549…)\n"
                "5. Solo en horario ART llama Apify comments\n\n"
                f"Webhook path: `{WEBHOOK_PATH}`"
            ),
            "height": 320,
            "width": 420,
            "color": 4,
        },
        "type": "n8n-nodes-base.stickyNote",
        "typeVersion": 1,
        "position": [-1840, -360],
        "id": nid(),
        "name": "Overview",
    })

    connections = merge_connections(
        {"Webhook": {"main": [[{"node": "InputData", "type": "main", "index": 0}]]}},
        {"InputData": {"main": [[{"node": "Settings", "type": "main", "index": 0}]]}},
        {"Settings": {"main": [[{"node": "LogRawInput", "type": "main", "index": 0}]]}},
        {"LogRawInput": {"main": [[{"node": "LogLeadsConHorario", "type": "main", "index": 0}]]}},
        {"LogLeadsConHorario": {"main": [[{"node": "ValidatePhone", "type": "main", "index": 0}]]}},
        {
            "IfPhoneValid": {
                "main": [
                    [{"node": "CalculateBusinessHours", "type": "main", "index": 0}],
                    [{"node": "EmailInvalidPhone", "type": "main", "index": 0}],
                ]
            }
        },
        {"ValidatePhone": {"main": [[{"node": "IfPhoneValid", "type": "main", "index": 0}]]}},
        {"CalculateBusinessHours": {"main": [[{"node": "IfBusinessHours", "type": "main", "index": 0}]]}},
        {
            "IfBusinessHours": {
                "main": [
                    [{"node": "Wait20s", "type": "main", "index": 0}],
                    [],  # outside hours: already logged
                ]
            }
        },
        {"Wait20s": {"main": [[{"node": "CallApify", "type": "main", "index": 0}]]}},
        {
            "CallApify": {
                "main": [
                    [{"node": "IfApifySuccess", "type": "main", "index": 0}],
                    [{"node": "SearchReintentos", "type": "main", "index": 0}],
                ]
            }
        },
        {
            "IfApifySuccess": {
                "main": [
                    [{"node": "LogLead2Landing", "type": "main", "index": 0}],
                    [{"node": "SearchReintentos", "type": "main", "index": 0}],
                ]
            }
        },
        {"LogLead2Landing": {"main": [[{"node": "EmailSuccess", "type": "main", "index": 0}]]}},
        {"SearchReintentos": {"main": [[{"node": "AggregateReintentos", "type": "main", "index": 0}]]}},
        {"AggregateReintentos": {"main": [[{"node": "IfNewRetry", "type": "main", "index": 0}]]}},
        {
            "IfNewRetry": {
                "main": [
                    [{"node": "AppendReintento", "type": "main", "index": 0}],
                    [{"node": "UpdateReintento", "type": "main", "index": 0}],
                ]
            }
        },
        {"AppendReintento": {"main": [[{"node": "EmailError", "type": "main", "index": 0}]]}},
        {"UpdateReintento": {"main": [[{"node": "EmailError", "type": "main", "index": 0}]]}},
    )

    return {
        "name": "Argentina_Prosegur_Meta_Apify_Comments_UNIFIED",
        "nodes": nodes,
        "pinData": {},
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
            "callerPolicy": "workflowsFromSameOwner",
            "availableInMCP": False,
        },
        "versionId": nid(),
        "meta": {"templateCredsSetupCompleted": True},
        "id": "argentina-prosegur-meta-unified",
        "tags": [{"name": "argentina"}, {"name": "prosegur"}, {"name": "meta"}],
    }


def build_make() -> dict:
    """Single-path Make scenario: FB lead → parse phone → POST JSON to n8n."""
    return {
        "name": "arg_prosegurlatam_APIFY_Form_UNIFIED",
        "flow": [
            {
                "id": 10,
                "module": "facebook-lead-ads:NewLeadMultiple",
                "version": 2,
                "parameters": {
                    "v": "2",
                    "fields": [
                        "id",
                        "ad_id",
                        "ad_name",
                        "adset_id",
                        "adset_name",
                        "campaign_id",
                        "campaign_name",
                        "created_time",
                        "custom_disclaimer_responses",
                        "field_data",
                        "form_id",
                        "home_listing",
                        "is_organic",
                        "partner_name",
                        "platform",
                        "retailer_item_id",
                        "vehicle",
                    ],
                    "__IMTHOOK__": 2907206,
                },
                "mapper": {},
                "onerror": [
                    {
                        "id": 13,
                        "module": "builtin:Ignore",
                        "version": 1,
                        "metadata": {"designer": {"x": -400, "y": 200}},
                    }
                ],
                "metadata": {
                    "designer": {"x": -600, "y": 0},
                    "restore": {
                        "parameters": {
                            "__IMTHOOK__": {
                                "data": {"editable": "false"},
                                "label": "arg_prosegurlatam_APIFY_Form - 1589834356082747",
                            }
                        }
                    },
                },
            },
            {
                "id": 4,
                "module": "phonenumber:TransformerParseNumber",
                "version": 1,
                "parameters": {},
                "mapper": {
                    "number": "{{10.data.phone}}",
                    "defaultCountry": "AR",
                },
                "onerror": [
                    {
                        "id": 12,
                        "module": "builtin:Ignore",
                        "version": 1,
                        "metadata": {"designer": {"x": -100, "y": 200}},
                    }
                ],
                "metadata": {
                    "designer": {"x": -250, "y": 0},
                    "restore": {
                        "expect": {
                            "defaultCountry": {
                                "mode": "chose",
                                "label": "Argentina (AR)",
                            }
                        }
                    },
                },
            },
            {
                "id": 29,
                "module": "json:TransformToJSON",
                "version": 1,
                "parameters": {"space": ""},
                "mapper": {"object": "{{`10`}}"},
                "onerror": [
                    {
                        "id": 31,
                        "module": "builtin:Ignore",
                        "version": 1,
                        "metadata": {"designer": {"x": 250, "y": 200}},
                    }
                ],
                "metadata": {
                    "designer": {"x": 100, "y": 0},
                    "restore": {
                        "parameters": {"space": {"label": "Empty"}}
                    },
                },
            },
            {
                "id": 25,
                "module": "http:ActionSendData",
                "version": 3,
                "parameters": {
                    "handleErrors": True,
                    "useNewZLibDeCompress": True,
                },
                "mapper": {
                    "url": N8N_WEBHOOK,
                    "serializeUrl": False,
                    "method": "post",
                    "headers": [
                        {"name": "Content-Type", "value": "application/json"}
                    ],
                    "qs": [],
                    "bodyType": "raw",
                    "parseResponse": False,
                    "authUser": "",
                    "authPass": "",
                    "timeout": "",
                    "shareCookies": False,
                    "ca": "",
                    "rejectUnauthorized": True,
                    "followRedirect": True,
                    "useQuerystring": False,
                    "gzip": True,
                    "useMtls": False,
                    "followAllRedirects": False,
                    "body": (
                        "{\n"
                        '  "lead": {{29.json}},\n'
                        '  "phone_e164": "{{4.phone}}",\n'
                        f'  "params_url": "{PARAMS_URL}",\n'
                        '  "aid": "ps",\n'
                        '  "formid": "{{10.formId}}"\n'
                        "}"
                    ),
                },
                "onerror": [
                    {
                        "id": 26,
                        "module": "builtin:Ignore",
                        "version": 1,
                        "metadata": {"designer": {"x": 650, "y": 200}},
                    }
                ],
                "metadata": {
                    "designer": {"x": 450, "y": 0},
                    "restore": {
                        "expect": {
                            "method": {"mode": "chose", "label": "POST"},
                            "bodyType": {"label": "Raw"},
                            "headers": {"mode": "chose"},
                        }
                    },
                },
            },
        ],
        "metadata": {
            "instant": True,
            "version": 1,
            "scenario": {
                "roundtrips": 1,
                "maxErrors": 3,
                "autoCommit": True,
                "autoCommitTriggerLast": True,
                "sequential": True,
                "slots": None,
                "confidential": False,
                "dataloss": False,
                "dlq": False,
                "freshVariables": False,
            },
            "designer": {"orphans": []},
            "zone": "eu1.make.com",
            "notes": [
                {
                    "content": (
                        "UNIFIED: un solo POST JSON a n8n. "
                        "Desactivar el escenario viejo con doble HTTP "
                        "y el workflow n8n Meta&TikTok."
                    )
                }
            ],
        },
    }


def validate_n8n(wf: dict) -> None:
    names = {n["name"] for n in wf["nodes"]}
    blob = json.dumps(wf)
    import re

    refs = set(re.findall(r"\$\('([^']+)'\)", blob))
    missing = sorted(refs - names)
    if missing:
        raise SystemExit(f"Missing node refs in n8n: {missing}")

    # every connection target exists
    for src, payload in wf["connections"].items():
        if src not in names:
            raise SystemExit(f"Connection source missing: {src}")
        for branch in payload.get("main", []):
            for t in branch:
                if t["node"] not in names:
                    raise SystemExit(f"Connection target missing: {t['node']}")

    # no disabled operational nodes
    for n in wf["nodes"]:
        if n.get("disabled"):
            raise SystemExit(f"Node unexpectedly disabled: {n['name']}")

    print(f"n8n OK: {len(wf['nodes'])} nodes, refs={sorted(refs)}")


def main() -> None:
    n8n = build_n8n()
    make = build_make()
    validate_n8n(n8n)

    files = {
        "Argentina_Prosegur_Meta_Apify_Comments_UNIFIED.n8n.json": n8n,
        "arg_prosegurlatam_APIFY_Form_UNIFIED.make.json": make,
        "README_IMPORT.md": None,
    }

    readme = """# Blueprints unificados — Argentina Prosegur Meta → Apify Comments

## Archivos

1. `arg_prosegurlatam_APIFY_Form_UNIFIED.make.json` — Make (importar como scenario)
2. `Argentina_Prosegur_Meta_Apify_Comments_UNIFIED.n8n.json` — n8n (import workflow)

## Flujo final

```
Meta Lead Ads
  → Make (parse phone AR)
  → POST JSON único a n8n `/webhook/argentina-prosegur-meta-leads`
  → n8n:
       InputData (normaliza + comment)
       → Log rawinput + leadsconhorario
       → Valida teléfono AR (+549XXXXXXXXXX)
       → Si horario ART 09–21:59 → Wait 20s → Apify comments
       → Success: lead2landing + email
       → Fail: reintentos + email error
```

## Qué se eliminó

- Segundo HTTP de Make al workflow viejo (`main_facebook_lead_from_argentina_prosegur`)
- Workflow viejo Meta&TikTok (no usar)
- Nodos huérfanos: Unicode converter, email de test, InputData_old, waits muertos
- Settings duplicados (Phone/BusinessHours/Apify/Emails/Sheets → un solo `Settings`)
- jsonpayload en query string (pasa en body JSON)

## Cómo importar

### n8n
1. Import workflow → activar
2. Copiar Production Webhook URL
3. Reconectar credenciales Google Sheets + SMTP si hace falta
4. **Desactivar** `Argentina_Prosegur_Apify_Meta&TikTok` y el viejo `+Comments`

### Make
1. Import scenario
2. Reconectar el webhook de Facebook Lead Ads (mismo form)
3. Pegar la URL real del webhook n8n nuevo en el módulo HTTP
4. Desactivar el escenario viejo con doble envío

## Body que envía Make

```json
{
  "lead": { ...objeto Meta completo... },
  "phone_e164": "+549...",
  "params_url": "https://www.prosegur.com.ar/landings/...",
  "aid": "ps",
  "formid": "1589834356082747"
}
```

## Setup obligatorio en n8n Settings

En el nodo `Settings`, reemplazar `REPLACE_WITH_APIFY_TOKEN` en `task_url`
por el token real del actor `customary_viburnum~prosegur-latam-argentina-comments`.

Rotar el token anterior si estuvo expuesto en blueprints viejos.
"""

    for name, data in files.items():
        if data is None:
            continue
        for folder in (OUT, ART):
            path = folder / name
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print("wrote", path, path.stat().st_size, "bytes")

    for folder in (OUT, ART):
        (folder / "README_IMPORT.md").write_text(readme, encoding="utf-8")
        print("wrote", folder / "README_IMPORT.md")


if __name__ == "__main__":
    main()
