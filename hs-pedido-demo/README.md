# HS Pedido — demo web

Demo estática para enseñar a un cliente un flujo de pedido de productos de peluquería (color, oxigenada, decoloración y cuidado), inspirada en listas tipo nota del móvil.

## Cómo verla

```bash
cd hs-pedido-demo
python3 -m http.server 8765
```

Abre http://localhost:8765 en el navegador.

## Funciones (demo)

- Pestañas por categoría con catálogo de referencias del pedido de ejemplo
- Controles de cantidad (+ / −)
- Resumen del pedido en tiempo real
- **Copiar pedido**: genera texto similar al formato de la nota (`tono/cantidad`, `X uds de …`)
- **Enviar pedido (demo)**: muestra el texto que se enviaría al distribuidor

No hay backend ni persistencia; es solo presentación para el cliente.
