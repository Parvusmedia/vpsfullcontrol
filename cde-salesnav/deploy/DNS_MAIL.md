# DNS de correo — companydataenrichment.com

Gmail y otros proveedores marcan como spam los correos transaccionales si **DKIM** y **DMARC** no están publicados en el DNS **público** (Piensa).

Plesk en el VPS ya tiene estos registros, pero el dominio usa nameservers de **Piensa** (`ns97` / `ns98.piensasolutions.com`), así que hay que añadirlos en el panel DNS de Piensa.

## Verificar estado actual

```bash
bash cde-salesnav/scripts/verify-mail-dns.sh
```

Debe mostrar DKIM y DMARC como `OK`. Si salen `MISSING`, añadir los registros siguientes.

## Registros a añadir en Piensa

### 1. DKIM (obligatorio)

| Campo | Valor |
|-------|-------|
| Tipo  | `TXT` |
| Host  | `default._domainkey` |
| Valor | `v=DKIM1; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsFqOzb5szXO2wQDafAaU31HAMDgeuM/EDTmnslz8M0OQxADrHmX91HxI88fPisbMnBlgndOiIMCCsHMKgk4XQ6ljaQ3bm2N/yKpC74FImNk0vfGcfIu4XN6p251FnAhGOw3yZ1zMyMMYQ8LoknW55JzkPiAgPyyz0sEHDn/xPE3X0UwnnRLUU0d6QFiVFN2d7i7MKtwy85Z0IgdP1TqoCLGBJVZH3oqSWRpNroWh/qQlfyegv60ZeE+5uyMBaSUeIZXocXw7lAh9cQCDxoNaCkkt0Ukf6v8ZefkX07oPFRSjMQY1qVd0avwZc9gXt0JER7B6ese16H60SLC52y3CowIDAQAB;` |

### 2. DMARC (obligatorio)

| Campo | Valor |
|-------|-------|
| Tipo  | `TXT` |
| Host  | `_dmarc` |
| Valor | `v=DMARC1; p=none; adkim=s; aspf=s; rua=mailto:hello@companydataenrichment.com` |

Usar `p=none` al principio (solo monitorización). Pasar a `p=quarantine` cuando la entrega sea estable.

### 3. SPF (revisar)

El registro actual en DNS público suele ser:

```txt
v=spf1 ip4:82.223.3.205 a mx -all
```

Mantener **un solo** TXT SPF en el apex. No duplicar con el de Plesk (`+a:mail.dataformedia.com`) salvo que también envíes desde ese host.

## Propagación

Tras guardar en Piensa, esperar 15–60 minutos y volver a ejecutar `verify-mail-dns.sh`.

## Mientras tanto (usuarios)

- Revisar carpeta **Spam** / **Promociones**
- Pulsar **No es spam** en Gmail (mejora la reputación del remitente)
- El enlace de confirmación funciona igual desde spam
