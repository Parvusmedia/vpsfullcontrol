# Smart Life — Calefa Mateo (n8n)

Workflow: **N8-SmartLife Calefa Mateo** (`DYJV0r0Z86pQIHH8`).

## Notificación message center (app Smart Life)

Tras encender y verificar el AC, el flujo puede enviar un **push al centro de mensajes** de Smart Life.

### Requisitos en Tuya IoT Platform (proyecto cloud vinculado a la cuenta)

1. Suscribir **App Push Notification Service** (y autorizar el proyecto).
2. Crear plantilla en *Notification center* (tipo **system message** recomendado), por ejemplo:
   - **Título:** `Calefacción Mateo`
   - **Contenido:** `Aire Mateo encendido: ${temp}°C (objetivo ${target}°C).`
3. Esperar aprobación de Tuya y copiar el `template_id` (`PUSH_...`).

### Configuración n8n (nodo Configuracion)

| Campo | Valor |
| --- | --- |
| `smartlife_uid` | UID de la app (p. ej. del dispositivo sensor: campo `uid`) |
| `push_biz_type` | `18` (Smart Life en este hogar) |
| `push_template_id` | ID aprobado (`PUSH_...`) |
| `notify_on_heat` | `true` |

Si `push_template_id` está vacío, el encendido sigue funcionando y el push se omite (`push_skipped` en el resumen).

### Scripts

```bash
# Parvus VPS (con deployment.local.env)
python3 scripts/n8n_mateo_patch_push_workflow.py
python3 scripts/n8n_apply_mateo_workflow.py
python3 scripts/n8n_mateo_ensure_push_template.py   # intenta crear/listar plantilla (requiere API push activa)
```