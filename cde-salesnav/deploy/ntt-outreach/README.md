# NTT DATA outreach (Sales Nav export)

Copy alineado con InMail (ES/EN) y campañas Smartlead dedicadas con recordatorio a 7 días.

## En VPS (`parvus-vps`)

```bash
cd /opt/apps/prospeccion-consultoras
python3 -m venv .venv   # una vez
.venv/bin/pip install httpx

# CSV en data/ntt_salesnav_deduped.csv
.venv/bin/python ntt-outreach/run_ntt_outreach.py create-campaigns
.venv/bin/python ntt-outreach/run_ntt_outreach.py enroll --csv data/ntt_salesnav_deduped.csv --live --start
.venv/bin/python ntt-outreach/run_ntt_outreach.py inmail --csv data/ntt_salesnav_deduped.csv --live --limit 20
.venv/bin/python ntt-outreach/run_ntt_outreach.py fix-smartlead-locale --csv data/ntt_salesnav_deduped.csv --live
```

Los InMail omiten URLs ya enviadas (`ntt_inmail_sent_urls.json` + resultados previos).

IDs de campaña: `SMARTLEAD_NTT_ES_CAMPAIGN_ID`, `SMARTLEAD_NTT_EN_CAMPAIGN_ID` en `.env`.

Resultados: `data/ntt_smartlead_enroll.json`, `data/ntt_inmail_results.json`.
