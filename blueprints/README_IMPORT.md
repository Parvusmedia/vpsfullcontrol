# Blueprints unificados — Argentina Prosegur Meta → Apify Comments

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

## Nota seguridad
El token de Apify viene del blueprint original. Conviene rotarlo en Apify y actualizar `Settings.task_url`.
