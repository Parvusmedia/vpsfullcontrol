# DEMO — Movistar Para Ti (90 segundos)

## Guion en vivo

### 1. Telegram — explorar (20 s)
Busca `@Movistarparatibot` → `/start`

- **Móviles** → **Todas las marcas** → navega con ◀️ ▶️ (`1/5`, `2/5`…)
- Producto recomendado: **Pixel 11** o **iPhone 16**

### 2. Telegram — crear aviso (15 s)
- Pulsa **🔔 Avísame** → **Si baja la cuota mensual**

### 3. Panel — operador (20 s)
`https://movistarparati.pmediaplus.com/panel` (sesión automática)

- Pestaña **Catálogo** → activa **Solo con avisos**
- O pestaña **🎬 Guion demo** → botones rápidos

### 4. Simular bajada (15 s)
En el producto con aviso → **Bajar a 8 €/mes** (Pixel 11) o el botón contextual

El push llega **al instante** (no hace falta esperar al poll).

### 5. Escenarios extra (opcional, 20 s)
En **🎬 Guion demo**:
- **ACTIVATE BLACK FRIDAY** — destaca 3 productos + bajada de cuota
- **OPEN IPHONE PREORDER** — iPhone 16 Pro en preventa

### 6. Cierre (10 s)
- **Actividad** — eventos en tiempo real
- **CMS NocoDB:** https://mpa.parvusmedia.com/nc/pzyr6ncnc9dk4h0/vwzlxuhc0956ijho/movistar_products-movistar_products

---

## Setup técnico (antes de presentar)

```bash
# Perfil del bot (nombre + descripción)
cd backend && python scripts/setup_telegram_profile.py

# Webhook (respuesta más rápida que polling)
sudo systemctl stop movistar-parati-polling
python scripts/setup_telegram_webhook.py
sudo systemctl restart movistar-parati-api
```

Con `DEMO_MODE=true`, el poll de catálogo corre cada **15 s** (cambios manuales en NocoDB).

| Modo | Cuándo |
|------|--------|
| **Webhook** | Presentación / producción |
| **Polling** | Desarrollo local sin HTTPS |
