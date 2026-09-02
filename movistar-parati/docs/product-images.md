# Imágenes de producto — Telegram

## Tamaño ideal (si creáis nuevas fotos)

| Uso | Dimensiones | Ratio | Notas |
|-----|-------------|-------|-------|
| **Recomendado** | **800 × 400 px** | **2:1** | Ficha compacta en el chat |
| Retina / export | 1200 × 600 px | 2:1 | Misma proporción, más nitidez |
| Alternativa | 640 × 360 px | 16:9 | También válido |

Formato: **JPEG**, fondo uniforme, producto centrado.

## Imágenes actuales (768 × 1024)

Las fotos del ZIP son verticales (3:4). El backend las **recorta al centro** a 2:1 antes de enviarlas a Telegram. No hace falta reexportarlas, pero si queréis control total del encuadre, exportad directamente a **800×400**.

## Límites Telegram (`sendPhoto`)

- Relación ancho/alto ≤ **20:1**
- Suma ancho + alto ≤ **10 000 px**
- Tamaño archivo ≤ **10 MB**

## Regenerar tras cambiar proporción

```bash
# En el VPS, tras cambiar product_image.py:
sudo systemctl restart movistar-parati-api
```

La caché de imágenes se vacía al reiniciar. También: `clear_image_cache()` vía `sync_product_images.py`.
