# Live fare demo (DV360 HTML5 POC)

Banner HTML5 300×600 con tarifas aéreas dinámicas. Google Studio no interviene.
Feed estático servido por Nginx. Un updater regenera el JSON cada 60 segundos.

**Dominio:** `https://flights.pmediaplus.com`

| Recurso | URL |
|---------|-----|
| Demo | https://flights.pmediaplus.com/demo |
| Feed | https://flights.pmediaplus.com/fares/network.json |
| Por origen | https://flights.pmediaplus.com/fares/JED.json |
| Creative | https://flights.pmediaplus.com/creative/ |
| Health | https://flights.pmediaplus.com/health |

DNS: `flights.pmediaplus.com A 87.106.194.137` (Plesk). HTTPS con Let's Encrypt.

## Architecture

```text
source/routes.json
    → updater (systemd timer, 60s)
    → network.json + JED.json + RUH.json + …
    → Nginx (CORS *, Cache-Control max-age=30)
    → HTML5 fetch() una vez (network.json)
    → dropdowns origen/destino/mes en memoria
```

Las impresiones no ejecutan Python ni FastAPI. Solo `GET` de un JSON estático, listo para poner delante Cloudflare / R2 / S3 más adelante.

El creative nunca contiene secretos. La interfaz estable es el JSON público; el updater mock se puede sustituir por API, GDS, CSV, n8n, etc. sin tocar el HTML5.

## Deployment

Código en este repo: `live-fare-demo/`. En el VPS: `/opt/apps/live-fare-demo`.

Patrón igual que el resto de productos: **nginx nativo + systemd**. No se publica ningún puerto nuevo. Docker Compose es solo para desarrollo local (`127.0.0.1:8088`).

```bash
# En el VPS (o via GitHub Action deploy-live-fare-demo)
live-fare-demo/scripts/inspect-vps.sh
live-fare-demo/scripts/deploy.sh
```

El deploy hace `nginx -t` y **reload**. No reinicia friendinme, prosegur ni otros servicios.

```bash
# Reiniciar solo el updater
sudo systemctl restart live-fare-updater.timer
sudo systemctl start live-fare-updater.service

# Logs del updater (no de cada impresión)
journalctl -u live-fare-updater.service -n 50 --no-pager
```

`/fares/` tiene `access_log off` para no generar un log por impresión.

## Feed

El banner descarga **un** JSON combinado: `/fares/network.json` (~222 tarifas).

Cada origen también se publica aparte para CDN/escala:

- `/fares/JED.json` `/fares/RUH.json` `/fares/MED.json` `/fares/DMM.json`
- `/fares/DXB.json` `/fares/AUH.json`
- `/fares/JFK.json` `/fares/IAD.json` `/fares/LAX.json`

Fuente (OD reales, no producto cartesiano): `feed/source/routes.json`

Orígenes: Arabia Saudí (JED, RUH, MED, DMM), EAU (DXB, AUH), EE. UU. (JFK, IAD, LAX).
74 rutas × 3 meses = **222 combinaciones**. Destinos solo si Saudia opera ese OD.

Headers:

```http
Access-Control-Allow-Origin: *
Content-Type: application/json
Cache-Control: public, max-age=30
```

## Update frequency

Por defecto 60 segundos: `deploy/live-fare-updater.timer` → `OnUnitActiveSec=60s`.

Para cambiarlo:

1. Editar `OnUnitActiveSec` en ese timer.
2. `sudo systemctl daemon-reload && sudo systemctl restart live-fare-updater.timer`

En Docker local: `UPDATE_INTERVAL_SECONDS` / `docker-compose.yml`.

## Manual fare update

```bash
cd /opt/apps/live-fare-demo
./scripts/set-fare.sh JED RUH 2026-10 299
```

Publica al momento (escritura atómica). El jitter posterior se mantiene cerca de ese precio.

Simular feed caducado (creative fallback):

```bash
./scripts/set-stale.sh 45
```

Volver a datos frescos:

```bash
python3 feed/updater/update.py --once
```

## Creative

Vanilla HTML/CSS/JS. Un `fetch` al cargar (`network.json`). Cambios de origen, destino o mes no disparan red: el destino se filtra en memoria según el origen.

Configuración en `creative/app.js`:

```javascript
const CONFIG = {
    feedUrl: "https://flights.pmediaplus.com/fares/network.json",
    defaultOrigin: "JED",
    maxDataAgeMinutes: 30
};
```

- Demo: https://flights.pmediaplus.com/demo
- Debug: https://flights.pmediaplus.com/creative/index.html?debug=1
- Si `now - updated_at` > 30 min, o el feed falla: texto fallback + CTA operativo. Nunca `€undefined` / `NaN`.

Click: `resolveExitUrl()` usa el deeplink de la tarifa. Si existe `window.clickTag` (DV360), se usa como tracking URL.

## DV360

```bash
./scripts/build-dv360.sh
# → dist/dv360-creative.zip
```

El ZIP contiene solo `index.html`, `styles.css`, `app.js` (y `assets/` si hay ficheros). Peso actual: **5.4 KB**. El creative llama al feed remoto por HTTPS. Sin Studio, sin API keys.

## Production migration

El HTML5 no cambia. Solo cambia dónde vive el JSON:

1. El updater (o n8n / API) escribe `MAD.json` con el mismo schema.
2. Sube el JSON a Cloudflare R2 / S3.
3. CDN delante con CORS `*` y el TTL que quieras.
4. Cambia `CONFIG.feedUrl` en el creative (o republica el ZIP).

Nginx del VPS puede quedar como origen de R2 o retirarse.

## TTL del feed

Busca el comentario `TTL FEED` en `deploy/nginx-live-fare-demo.conf` (`max-age=30`). Después:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## Local

```bash
python3 feed/updater/update.py --once
python3 feed/updater/test_update.py
docker compose up
# http://127.0.0.1:8088/demo
```
