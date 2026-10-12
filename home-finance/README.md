# Hogar Finanzas (`home.pmediaplus.com`)

Dashboard personal para analizar gastos del hogar desde Excel/CSV o Google Sheet publicado en CSV.

## Uso

1. Despliega en Parvus con `home-finance/deploy/deploy-home-finance-parvus.sh` (API Python en `:8791` + nginx en `deploy/nginx-home-finance.conf`).
2. Apunta **DNS** `home.pmediaplus.com` al VPS donde corre nginx (hoy el registro A apunta a otro host).
3. Copia el token de `/opt/apps/private/home-finance/app.env` (`HOME_FINANCE_API_TOKEN`) en el servidor.
4. Entra en la web, pega el token como clave.
5. Importa exportaciones bancarias y revisa el resumen mensual.

Alternativa con PHP (Plesk): sube `public/` y usa los endpoints `public/api/*.php` con `deploy/home-finance.env.example`.

## Plantilla de columnas

| fecha | concepto | importe | categoria (opcional) | cuenta (opcional) |

Los importes negativos se tratan como gastos; positivos como ingresos.

## Google Sheet

Publicar en web → CSV, o usar URL `.../export?format=csv` compartida.
