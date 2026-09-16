"""Acciones de demo contextualizadas por producto (panel operador)."""

from __future__ import annotations

from typing import Any

# new_monthly: simula bajada de cuota mensual
DEMO_PRODUCT_ACTIONS: dict[str, list[dict[str, Any]]] = {
    "pixel-11-256": [
        {"id": "drop-850", "label": "🔥 Bajar a 8 €/mes", "new_monthly": 8},
    ],
    "galaxy-s25": [
        {"id": "drop-1199", "label": "📉 Bajar a 12 €/mes", "new_monthly": 12},
    ],
    "iphone-16-128": [
        {"id": "drop-1199", "label": "📉 Bajar a 12 €/mes", "new_monthly": 12},
    ],
    "galaxy-z-flip": [
        {"id": "drop-1899", "label": "📉 Bajar a 19 €/mes", "new_monthly": 19},
    ],
    "pixel-9a": [
        {"id": "drop-699", "label": "📉 Bajar a 7 €/mes", "new_monthly": 7},
    ],
    "xiaomi-15": [
        {"id": "drop-999", "label": "📉 Bajar a 10 €/mes", "new_monthly": 10},
    ],
    "redmi-note-14": [
        {"id": "drop-549", "label": "📉 Bajar a 5 €/mes", "new_monthly": 5},
    ],
    "iphone-16-pro": [
        {"id": "drop-2499", "label": "📉 Bajar a 25 €/mes", "new_monthly": 25},
    ],
}

DEFAULT_DEMO_ACTION = {"id": "drop-generic", "label": "📉 Simular bajada −2 €/mes", "delta": -2.0}


def demo_actions_for_product(product_id: str, monthly_price: float | None) -> list[dict[str, Any]]:
    if product_id in DEMO_PRODUCT_ACTIONS:
        return DEMO_PRODUCT_ACTIONS[product_id]
    if monthly_price is not None and monthly_price > 2:
        target = round(max(monthly_price + DEFAULT_DEMO_ACTION["delta"], 1.0), 2)
        return [
            {
                "id": DEFAULT_DEMO_ACTION["id"],
                "label": f"📉 Bajar a {target:.2f} €/mes",
                "new_monthly": target,
            }
        ]
    return []
