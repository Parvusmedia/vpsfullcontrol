# Hogar Finanzas (`home.pmediaplus.com`)

Dashboard personal para analizar gastos del hogar desde Excel/CSV o Google Sheet publicado en CSV.

## Uso

1. **Producción (Plesk):** `home-finance/deploy/deploy-home-finance-plesk.sh` en `nextconvers-vps` → `https://home.pmediaplus.com/`
2. Copia el token de `/var/www/vhosts/parvusmedia.com/private/home-finance/app.env` (`HOME_FINANCE_API_TOKEN`) en el servidor.
4. Entra en la web, pega el token como clave.
5. Importa exportaciones bancarias y revisa el resumen mensual.

Alternativa con PHP (Plesk): sube `public/` y usa los endpoints `public/api/*.php` con `deploy/home-finance.env.example`.

## Plantilla de columnas

| fecha | concepto | importe | categoria (opcional) | cuenta (opcional) |

Los importes negativos se tratan como gastos; positivos como ingresos.

## Google Sheet

Publicar en web → CSV, o usar URL `.../export?format=csv` compartida.
