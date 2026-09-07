# Catálogo de accesos (NocoDB)

Tabla privada para que cualquier agente Cursor pueda localizar tokens, APIs y SSH de los entornos Parvus **sin copiar secretos a git ni al chat**.

## Dónde está

| Campo | Valor |
|-------|--------|
| UI | https://mpa.parvusmedia.com/w1yr9d7k/pluyg9y6o3thd5o/m6956l2gfi8d96c/vwb7btk1zh9yc601/accesos-accesos |
| Base ID | `pluyg9y6o3thd5o` |
| Table ID | `m6956l2gfi8d96c` |
| View ID | `vwb7btk1zh9yc601` |
| Auth | header `xc-token` = `NOCODB_API_TOKEN` |

Columnas: `Title`, `Entorno`, `Servicio`, `Clave`, `Valor`, `URL`, `Fuente`, `Notas`.

`Title` es `{entorno} · {servicio} · {clave}`.

## Cómo leerla (agentes)

```bash
scripts/accesos status
scripts/accesos list --query unipile
scripts/accesos get --clave UNIPILE_API_KEY --entorno nextconvers-vps --servicio cde --out /tmp/unipile.key
```

`list` **nunca** devuelve `Valor`. `get` escribe el secreto a un archivo `0600` y solo imprime metadatos + ruta.

Si el Cloud Agent no tiene `NOCODB_API_TOKEN`, el helper lo arranca por SSH desde `.env` conocidos en `parvus-vps` (mismo token que los pipelines de prospección).

Recomendado: añadir `NOCODB_API_TOKEN` y `NOCODB_BASE_URL=https://mpa.parvusmedia.com` como secrets del entorno Cursor.

## Entornos cubiertos

- `parvus-vps` — `/opt/apps/*`, `/etc/*/app.env`, `/opt/apps/private/cde`
- `nextconvers-vps` — hop `ssh parvus-vps 'ssh nextconvers-vps'`; CDE prod en `/var/www/vhosts/companydataenrichment.com/private/cde/`
- `cursor-cloud` — secrets inyectados en este entorno (`N8N_*`)
- `noco` / `make-eu1` — coordenadas del catálogo y MCP Make (nombres de conexión, no OAuth)

## Guardrails

- No imprimir `Valor` en chat, commits, PRs ni logs.
- No copiar el catálogo a git.
- Zapier / Slack MCP pueden estar `needsAuth` en un run concreto; el catálogo no sustituye OAuth de MCP.
- Para refrescar filas hay que re-escanear los `.env` en ambos VPS (no lo hace `scripts/accesos` en cada listado).
