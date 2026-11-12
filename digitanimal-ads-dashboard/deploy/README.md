# Digitanimal dashboard en Parvus VPS

**URL:** https://digitanimal.pmediaplus.com (requiere DNS)

## DNS (IONOS / panel del dominio)

Apunta el subdominio al VPS Parvus:

| Registro | Valor |
|----------|--------|
| `digitanimal` **A** | `87.106.194.137` |

Hoy `digitanimal.pmediaplus.com` resuelve a `82.223.3.205` (landings IONOS), no al VPS. Hasta cambiarlo verás otra web o 404.

Ejemplo correcto: `friendinme.pmediaplus.com` → `87.106.194.137`.

## Despliegue

Desde el repo (con `WINDSOR_API_KEY` en el entorno local o ya en el VPS):

```bash
./digitanimal-ads-dashboard/deploy/deploy-parvus.sh
```

Secretos en el servidor: `/opt/apps/private/digitanimal/windsor.env` (ver `windsor.env.example`).

## TLS

Cuando el DNS apunte al VPS:

```bash
ssh parvus-vps 'sudo certbot --nginx -d digitanimal.pmediaplus.com'
```
