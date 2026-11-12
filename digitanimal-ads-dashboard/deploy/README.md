# Digitanimal dashboard en Parvus VPS

**URL:** https://digitanimal.pmediaplus.com (requiere DNS)

## DNS (Plesk en nextconvers / 82.223.3.205)

Desde **parvus-vps**:

```bash
bash /opt/apps/digitanimal-ads-dashboard/deploy/plesk-dns-digitanimal.sh
```

(o el script genérico `education-ai-advisor/scripts/plesk-add-a-record.sh` con `DNS_HOST=digitanimal`).

Registro: `digitanimal.pmediaplus.com` **A** → `87.106.194.137`.

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
