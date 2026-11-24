# Guardián de potencia 5,8 kW (Deye + Tuya / n8n)

Diseño de viabilidad — **sin cambios en workflows** (nov 2026).

## Objetivo

Evitar saltos de **térmica / diferencial** con **5,8 kW contratados**, comparando la **importación desde red** (vía Deye) con **automatizaciones de calefacción** en Tuya/n8n que están a punto de encender, y avisar al usuario para **saltar un encendido** o **apagar una carga** antes de superar el límite.

---

## 1. ¿Deye da consumo “en tiempo real”?

**Respuesta corta: no en el sentido estricto.** Deye Cloud expone el **último instante disponible** de la planta, pero la cadena suele actualizarse cada **~5 minutos** (logger + caché en nube). Latencia típica **1–10 min** respecto al momento presente.

### API relevante (Deye Cloud OpenAPI, región EU)

| Endpoint | Uso |
|----------|-----|
| `POST /v1.0/station/latest` | Potencias instantáneas de la **estación** (casa completa en el modelo Deye) |
| `POST /v1.0/station/history/power` | Histórico ~5 min (comprobar tendencia) |
| `POST /v1.0/device/latest` | Hasta 10 equipos por lote (si hace falta desglose) |

Autenticación: **Bearer token** (cuenta developer Deye; caducidad ~60 días).

### Campos de potencia (`station/latest`) — útiles para el límite 5,8 kW

Valores observados en documentación/comunidad: **vatios (W)**, no kW. Convertir: `kW = campo / 1000`.

| Campo | Significado habitual | Notas para 5,8 kW |
|-------|----------------------|-------------------|
| `consumptionPower` | Carga de la vivienda (demanda) | No es igual al límite del contador si hay solar/batería |
| `purchasePower` | Importación desde red | **Candidato principal** si el CT de red está bien |
| `wirePower` | Magnitud en acometida / red | A menudo coincide con importación; firmware varía |
| `gridPower` | Exportación/importación | A veces `null`; hay instalaciones que derivan signo del balance |
| `generationPower` | Solar | Reduce importación de red |
| `batteryPower` | Batería (carga/descarga) | Afecta importación |
| `lastUpdateTime` | Marca de frescura | **Imprescindible** rechazar datos viejos |

**Para potencia contratada (5,8 kW)** lo habitual es vigilar **importación en el contador** (`purchasePower` / `wirePower` con CT correcto), no solo `consumptionPower`.

### Limitaciones que hay que asumir en el diseño

- No sustituye un **analizador en el cuadro** subsegundo: decisión con **retraso de minutos**.
- Errores de **pinza CT** en Deye invalidan el número (comprobar con lectura del contador o Shelly/emisor en cuadro si existe).
- Picos **&lt; 5 min** (arranque compresor, resistencia) pueden no verse en la muestra.

---

## 2. Automatizaciones Tuya / n8n relevantes (calefacción)

Estado en n8n Cloud (pmedia) — **solo lectura**:

| Workflow | Qué hace | Cuándo puede encender |
|----------|----------|------------------------|
| **N8-SmartLife Calefa Mateo** (`DYJV0r0Z86pQIHH8`) | AC split Mateo vía IR (Tuya) | Lun–vie `:30` en 00–07 y 18–23; sáb–dom `:00` en 00–10 y 18–23; si T &lt; 21 °C |
| **N8-SmartLife Radiador Buhardilla** (`HPaa9jGQmpDex41t`) | Termostato/radiador Buhardilla | `0,30` en 0–7 y 18–23 todos los días; sáb–dom también 8–9 |
| **Smart Life · Deshumidificación Buhardilla** | (inactivo) | No cuenta por ahora |

**Problema de arquitectura:** cada flujo decide **solo** y no publica “voy a encender en 3 min”. Para el guardián hay que:

1. **Replicar cron + ventana + umbral térmico** (misma lógica que `Decidir temperatura`), o  
2. **Centralizar** en un workflow “coordinador” que llame a sub-flujos con `dry_run`/`force_off`, o  
3. **Interceptar** justo antes de `Enviar orden Tuya` (nodo común de pre-vuelo).

No hay en Tuya un “evento futuro garantizado” sin leer sensores: “a punto de encender” = *próxima pasada del cron* **y** condiciones previstas (p. ej. temperatura &lt; mínimo en la última lectura).

---

## 3. Diseño propuesto: “Pre-vuelo potencia”

### 3.1 Workflow nuevo (recomendado): `N8-Power Guard 5.8kW`

**Disparo:** cada **5 min** (alineado con Deye) **o** 2–3 min antes de cada `:00` / `:30` / `:30` Mateo (más eficiente en tareas n8n).

**Pasos:**

1. **Deye** `station/latest` → `import_kw`, `consumption_kw`, `solar_kw`, `battery_kw`, `age_min`, `lastUpdateTime`.
2. Si `age_min` &gt; 10 → aviso “dato Deye obsoleto”; **no bloquear** o bloquear según política (decisión usuario).
3. **Calendario de cargas** (tabla estática en Code / Google Sheet / n8n Data Store):

   | Lógica | Próximo disparo | kW estimado encendido | kW en marcha (si ya ON) |
   |--------|-----------------|------------------------|-------------------------|
   | Mateo heat-on | cron + ventana + sensor | **TBD usuario** (p. ej. 1,2–2,5) | leer estado AC Tuya |
   | Buhardilla heat-on | cron + ventana + sensor | **TBD** (0,5–2 según nivel) | estado radiador |

4. **Proyección:**

   ```
   projected_import_kw = current_import_kw + sum(kw_estimated_new_loads) - kw_sheddable_if_user_picks
   ```

   Margen:

   ```
   headroom_kw = 5.8 - projected_import_kw   (o 5.8 * factor_seguridad - projected)
   ```

5. Si `headroom_kw < umbral` (p. ej. **0,3–0,5 kW**) y hay encendido previsto en los próximos **N min** (p. ej. 15):

   → **Alerta + pregunta** (no actuar sin respuesta configurada).

### 3.2 Aviso al usuario

**Contenido del mensaje (plantilla):**

- Hora (Madrid).
- **Importación red ahora:** X kW (Deye, edad Y min).
- **Límite:** 5,8 kW · **Cabeza de margen:** Z kW.
- **Próximos actos:** “Mateo AC (~2 kW) a las 18:30 si sigue &lt; 21 °C”; “Buhardilla (~1 kW) a las 18:30”.
- **Riesgo:** posible salto si se cumplen condiciones.

**Canales (ya usáis parte):**

| Canal | Pros | Contras |
|-------|------|---------|
| **Telegram** (`SmartLife Buhardilla — alertas error`) | Botones inline, respuesta rápida | Un chat por persona |
| **Email** | Registro escrito | Lento, sin botones nativos |
| **Push Smart Life** | Mismo ecosistema Tuya | Plantilla + aprobación; no ideal para diálogo |

**Recomendación:** **Telegram** para la pregunta; email como copia opcional.

### 3.3 Pregunta y acciones (Telegram inline keyboard)

```
⚡ Red ~4,9 kW (Deye, hace 4 min). Límite 5,8 kW.
En ≤15 min puede encenderse:
 • Mateo AC (~2,0 kW estim.)
 • Buhardilla (~1,0 kW estim.)
¿Qué hacemos?

[ Omitir Mateo esta hora ]
[ Omitir Buhardilla esta hora ]
[ Apagar: <lista Tuya ON> ▼ ]
[ Continuar igual ]
```

**Persistencia (n8n static data / Redis / KV):**

- `skip_mateo_until`: ISO timestamp (hasta próxima hora cron).
- `skip_buhardilla_until`: idem.
- `user_override_expires`: TTL 1 h.

**En los workflows de calefacción (futuro cambio):** al inicio de `Decidir temperatura`, si `now < skip_*_until` → `should_send: false`, motivo `skipped_by_power_guard`.

**Apagar dispositivo Tuya:** solo dispositivos en **lista blanca** (usuario): identificar `device_id`, comando `power: 0` (o API equivalente). **Nunca** automático sin confirmación explícita.

### 3.4 Si no responde

Decisión solo del usuario (ejemplos):

| Política | Comportamiento |
|----------|----------------|
| **Conservadora** | Omitir todos los encendidos previstos en esa ventana |
| **Permisiva** | Continuar (solo aviso) |
| **Mixta** | Omitir solo la carga de mayor kW estimado |

Timeout sugerido: **10 min** antes del cron de encendido; si no hay respuesta → aplicar política por defecto.

---

## 4. Viabilidad de los 4 puntos del encargo

| # | ¿Factible? | Comentario |
|---|------------|------------|
| 1 | **Sí, con matices** | “Tiempo real” = último dato Deye, ~5 min |
| 2 | **Sí, con desarrollo** | Hay que modelar cron + sensores de cada workflow |
| 3 | **Sí** | Telegram/email/push; push peor para interacción |
| 4 | **Sí** | Requiere botones + flags `skip_*` y comandos Tuya solo sobre lista blanca |

**No hemos encontrado integración Deye en este repo** (`vpsfullcontrol`); asumir credenciales en otro sitio o por configurar.

---

## 5. Huecos que solo el usuario puede cerrar

1. **`stationId` Deye** y dónde guardar **client_id / secret / refresh token** (sin pegarlos en chat).
2. Confirmar métrica legal: ¿límite sobre **importación red** medida por Deye? ¿Contador oficial coincide con `purchasePower`?
3. **kW estimados** (y pico arranque) por: Mateo AC, Buhardilla, otras resistencias Tuya, termo, vitro, etc.
4. Lista de cargas **apagables** (device_id + nombre + kW liberados).
5. Umbral de alerta (p. ej. avisar si &gt; **5,0 kW** o margen &lt; **0,5 kW**).
6. Política **sin respuesta** y horario en que no molestar.
7. ¿Incluir **solo calefacción** o también otros flujos n8n/Tuya futuros?
8. Si tiene **Shelly / emisor en cuadro** además de Deye, ¿cuál manda?

---

## 6. Próximo paso técnico (cuando apruebe)

1. Script de **sonda Deye** (`station/latest` + imprimir solo campos y edad).
2. Tabla de **próximos eventos** desde cron Mateo/Buhardilla.
3. Prototipo **solo aviso** Telegram (sin skip/apagar).
4. Añadir interacción y flags en workflows de calefacción.

*Ningún paso de esta lista se ha ejecutado en producción en el encargo actual.*