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
| Segunda clave | `ACCESOS_MASTER_KEY` (AES-256-GCM). **No está en NocoDB.** Vive en `parvus-vps:/opt/apps/private/accesos.master.key` y/o secret Cursor `ACCESOS_MASTER_KEY`. |

Columnas: `Title`, `Entorno`, `Servicio`, `Clave`, `Valor`, `URL`, `Fuente`, `Notas`.

`Title` es `{entorno} · {servicio} · {clave}`.

`Valor` se guarda como `enc:v1:<base64>`. Con el token de Noco solo se ve ciphertext. Hace falta la clave maestra para `scripts/accesos get`. Una passphrase *dentro* de Noco no cubre un token filtrado: el mismo token leería esa passphrase.

## Cómo leerla (agentes)

```bash
scripts/accesos status
scripts/accesos list --query unipile
scripts/accesos get --clave UNIPILE_API_KEY --entorno nextconvers-vps --servicio cde --out /tmp/unipile.key
```

`list` **nunca** devuelve `Valor`. `get` descifra a un archivo `0600` y solo imprime metadatos + ruta.

```bash
scripts/accesos seal --dry-run   # cuántas filas siguen en claro
scripts/accesos seal             # cifra Valor con la clave maestra
```

Si el Cloud Agent no tiene `NOCODB_API_TOKEN` / `ACCESOS_MASTER_KEY`, el helper los arranca por SSH desde Parvus.

Recomendado en el entorno Cursor: `NOCODB_API_TOKEN`, `NOCODB_BASE_URL=https://mpa.parvusmedia.com`, `ACCESOS_MASTER_KEY`. El token y la clave maestra deben ser secrets distintos: filtrar uno no basta para leer el catálogo. El helper necesita el paquete `cryptography`.

## Entornos cubiertos

- `parvus-vps` — `/opt/apps/*`, `/etc/*/app.env`, `/opt/apps/private/cde`
- `nextconvers-vps` — hop `ssh parvus-vps 'ssh nextconvers-vps'`; CDE prod en `/var/www/vhosts/companydataenrichment.com/private/cde/`
- `cursor-cloud` — secrets inyectados en este entorno (`N8N_*`)
- `noco` / `make-eu1` — coordenadas del catálogo y MCP Make (nombres de conexión, no OAuth)

## Guardrails

- No imprimir `Valor` ni `ACCESOS_MASTER_KEY` en chat, commits, PRs ni logs.
- No guardar la clave maestra en NocoDB ni en git.
- No copiar el catálogo a git.
- Si se filtra `NOCODB_API_TOKEN`, rota ese token en Noco; el ciphertext sigue siendo inútil sin la clave maestra. Si se filtra la clave maestra, rota `/opt/apps/private/accesos.master.key` y vuelve a `scripts/accesos seal` (hace falta re-cifrar desde las fuentes `.env`, no desde ciphertext viejo).
- Zapier / Slack MCP pueden estar `needsAuth` en un run concreto; el catálogo no sustituye OAuth de MCP.
- Para refrescar filas hay que re-escanear los `.env` en ambos VPS (no lo hace `scripts/accesos` en cada listado).
