"""Textos conversacionales para recomendaciones «Para mí»."""

from __future__ import annotations

from app.services.product_service import Product

PREFERENCE_META: dict[str, dict] = {
    "camera": {
        "label": "buena cámara",
        "emoji": "📸",
        "field": "camera_score",
        "spec_attr": "spec_camera",
        "ask": "¿Buscas un móvil con <b>buena cámara</b>? Cuéntame tu presupuesto y te propongo opciones.",
        "reasons": {
            5: "tiene una de las mejores cámaras del catálogo, con mucho detalle de día y de noche",
            4: "destaca en fotos con buen equilibrio de color y retratos naturales",
            3: "ofrece una cámara sólida para el día a día sin complicarte",
            2: "cubre lo básico en fotografía; hay modelos con más enfoque fotográfico",
            1: "no es su punto fuerte frente a otros del catálogo",
        },
    },
    "battery": {
        "label": "mucha batería",
        "emoji": "🔋",
        "field": "battery_score",
        "spec_attr": "spec_battery",
        "ask": "¿Quieres un móvil con <b>mucha batería</b>? Te ayudo a encontrar uno que aguante el día.",
        "reasons": {
            5: "está entre los que más autonomía ofrecen: aguanta jornadas largas sin ansiedad",
            4: "tiene muy buena batería para uso intensivo de redes y vídeo",
            3: "equilibra autonomía y tamaño; llega al final del día con uso normal",
            2: "puede requerir carga a mitad de jornada si lo usas mucho",
            1: "la autonomía no es su punto fuerte",
        },
    },
    "work": {
        "label": "trabajo",
        "emoji": "💼",
        "field": "business_score",
        "spec_attr": "spec_work",
        "ask": "¿Necesitas un móvil para <b>trabajo</b>? Busco opciones fiables para correo, reuniones y productividad.",
        "reasons": {
            5: "es muy fiable para trabajo: rendimiento estable, pantalla cómoda y buena conectividad",
            4: "encaja bien en entorno profesional con buen rendimiento multitarea",
            3: "cubre tareas de oficina y videollamadas sin problema",
            2: "vale para uso básico laboral; hay opciones más orientadas a productividad",
            1: "mejor para uso personal que profesional intensivo",
        },
    },
    "premium": {
        "label": "gama alta",
        "emoji": "⭐",
        "field": "premium_score",
        "spec_attr": "spec_premium",
        "ask": "¿Buscas <b>gama alta</b>? Te muestro lo mejor del catálogo en acabados y rendimiento.",
        "reasons": {
            5: "es referencia premium: materiales, pantalla y rendimiento de lo más alto del catálogo",
            4: "apunta a gama alta con muy buena experiencia global",
            3: "gama media-alta con buen conjunto, aunque no es lo más exclusivo",
            2: "más orientado a precio que a prestaciones top",
            1: "no es la opción si priorizas lo más premium",
        },
    },
    "value": {
        "label": "calidad/precio",
        "emoji": "💰",
        "field": "value_score",
        "spec_attr": "spec_value",
        "ask": "¿Priorizas <b>calidad/precio</b>? Busco el mejor equilibrio entre cuota y lo que ofrece.",
        "reasons": {
            5: "es de los que más rentables son: mucho móvil por lo que pagas al mes",
            4: "muy buena relación cuota/prestaciones frente al resto del catálogo",
            3: "precio razonable para lo que incluye",
            2: "hay alternativas con mejor relación calidad-precio en el catálogo",
            1: "no destaca en precio frente a rivales similares",
        },
    },
}

_BRAND_HINTS: dict[str, dict[str, str]] = {
    "camera": {
        "Google": "El procesado de imagen de Google suele sacar partido en contraluz y modo noche.",
        "Apple": "Vídeo estable y colores fieles, ideal si grabas mucho.",
        "Samsung": "Zoom y versatilidad de lentes para casi cualquier escena.",
    },
    "battery": {
        "Samsung": "Suele combinar buena batería con carga rápida.",
        "Xiaomi": "Mucha autonomía por euro invertido.",
    },
    "work": {
        "Apple": "Ecosistema sólido si ya usas Mac o iPad.",
        "Samsung": "DeX y pantalla grande ayudan en productividad móvil.",
    },
    "premium": {
        "Apple": "Acabados premium y soporte software a largo plazo.",
        "Samsung": "Pantallas AMOLED top y funciones flagship.",
    },
    "value": {
        "Xiaomi": "Muchas prestaciones por cuota contenida.",
        "Google": "Experiencia limpia sin pagar extras innecesarios.",
    },
}


def preference_label(preference: str) -> str:
    return PREFERENCE_META.get(preference, PREFERENCE_META["value"])["label"]


def preference_ask_message(preference: str) -> str:
    return PREFERENCE_META.get(preference, PREFERENCE_META["value"])["ask"]


def _budget_phrase(max_monthly: float | None) -> str:
    if max_monthly is None:
        return "sin límite de cuota concreto"
    if max_monthly <= 10:
        return f"hasta <b>{max_monthly:.0f} €/mes</b>"
    return f"con presupuesto de hasta <b>{max_monthly:.0f} €/mes</b>"


def _price_range_phrase(price_min: float | None, price_max: float | None) -> str:
    if price_min is None and price_max is None:
        return "sin límite de precio del terminal"
    if price_min is None and price_max is not None:
        return f"con terminal de hasta <b>{price_max:.0f} €</b>"
    if price_min is not None and price_max is None:
        return f"con terminal desde <b>{price_min:.0f} €</b>"
    if price_min == price_max:
        return f"con terminal de unos <b>{price_min:.0f} €</b>"
    return f"con terminal entre <b>{price_min:.0f} €</b> y <b>{price_max:.0f} €</b>"


def _client_phrase(is_client: bool | None) -> str:
    if is_client is True:
        return "como <b>cliente Movistar</b>"
    if is_client is False:
        return "sin ser cliente (precio de terminal libre)"
    return ""


def forme_price_question(preference: str) -> str:
    meta = PREFERENCE_META.get(preference, PREFERENCE_META["value"])
    return (
        f"{meta['ask']}\n\n"
        "¿Cuánto quieres gastar en el <b>terminal</b>?\n"
        "<i>Si eres cliente Movistar, sueles tener mejor precio, descuentos "
        "y la opción de pagarlo en cuotas.</i>"
    )


def forme_client_question() -> str:
    return (
        "¿Eres <b>cliente Movistar</b>?\n\n"
        "Como cliente puedes acceder a <b>descuentos</b>, promociones y "
        "<b>financiación en cuotas</b>. Si no lo eres, te mostramos el precio "
        "del terminal y cuánto podrías ahorrar haciéndote cliente."
    )


def _brand_phrase(brand: str | None) -> str:
    if not brand or brand.lower() in {"any", "me da igual", "cualquiera"}:
        return "de cualquier marca"
    return f"de marca <b>{brand}</b>"


def forme_results_intro(
    preference: str,
    *,
    max_monthly: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    is_client: bool | None = None,
    brand: str | None = None,
    count: int = 3,
) -> str:
    meta = PREFERENCE_META.get(preference, PREFERENCE_META["value"])
    emoji = meta["emoji"]
    label = meta["label"]
    n = max(count, 1)
    if price_min is not None or price_max is not None or is_client is not None:
        budget = _price_range_phrase(price_min, price_max)
        client = _client_phrase(is_client)
        profile = " ".join(part for part in (budget, client) if part)
    else:
        profile = _budget_phrase(max_monthly)
    return (
        f"{emoji} <b>Para ti — {label}</b>\n\n"
        f"He buscado {n} móvil{'es' if n != 1 else ''} {_brand_phrase(brand)} "
        f"{profile}.\n\n"
        f"En cada ficha te explico <b>por qué encaja</b> con lo que pediste. "
        f"Navega con ◀️ ▶️."
    )


def _format_mah(value: int) -> str:
    raw = str(value)
    if len(raw) <= 3:
        return raw
    parts: list[str] = []
    while raw:
        parts.append(raw[-3:])
        raw = raw[:-3]
    return ".".join(reversed(parts))


def _battery_rank(product: Product, catalog: list[Product] | None) -> tuple[int, int, int]:
    values = sorted((p.battery_mah for p in (catalog or []) if p.battery_mah), reverse=True)
    if not values or not product.battery_mah:
        return 0, 0, 0
    rank = values.index(product.battery_mah) + 1
    return len(values), values[0], rank


def _camera_rank(product: Product, catalog: list[Product] | None) -> tuple[int, int, int]:
    values = sorted((p.camera_main_mp for p in (catalog or []) if p.camera_main_mp), reverse=True)
    if not values or not product.camera_main_mp:
        return 0, 0, 0
    rank = values.index(product.camera_main_mp) + 1
    return len(values), values[0], rank


def _technical_battery_line(product: Product, catalog: list[Product] | None) -> str | None:
    if product.spec_battery:
        return product.spec_battery.strip()

    mah = product.battery_mah
    if not mah:
        return None

    total, max_mah, rank = _battery_rank(product, catalog)
    parts = [f"lleva <b>{_format_mah(mah)} mAh</b>"]

    if product.fast_charge_w:
        parts.append(f"con carga rápida de <b>{product.fast_charge_w} W</b>")

    if total >= 3 and rank == 1:
        parts.append("la <b>mayor batería del catálogo</b> ahora mismo")
    elif total >= 3 and rank <= 3:
        parts.append(f"está entre las <b>{min(3, total)} con más autonomía</b> del catálogo ({rank}º de {total})")
    elif total >= 3 and max_mah and mah >= max_mah * 0.9:
        parts.append("muy cerca del tope de autonomía del catálogo")
    elif total >= 3:
        parts.append(f"en el catálogo hay modelos hasta <b>{_format_mah(max_mah)} mAh</b>")

    return ", ".join(parts) + "."


def _technical_camera_line(product: Product, catalog: list[Product] | None) -> str | None:
    if product.spec_camera:
        return product.spec_camera.strip()

    mp = product.camera_main_mp
    if not mp:
        return None

    total, _max_mp, rank = _camera_rank(product, catalog)
    parts = [f"cámara principal de <b>{mp} MP</b>"]

    if total >= 3 and rank == 1:
        parts.append("la <b>más resolutiva del catálogo</b>")
    elif total >= 3 and rank <= 3:
        parts.append(f"entre las <b>mejores del catálogo</b> en resolución ({rank}º de {total})")

    return ", ".join(parts) + "."


def _technical_work_line(product: Product, _catalog: list[Product] | None) -> str | None:
    if product.spec_work:
        return product.spec_work.strip()
    if product.processor:
        return f"monta <b>{product.processor}</b>, pensado para multitarea y apps del día a día."
    return None


def _technical_premium_line(product: Product, _catalog: list[Product] | None) -> str | None:
    if product.spec_premium:
        return product.spec_premium.strip()
    bits: list[str] = []
    if product.processor:
        bits.append(f"<b>{product.processor}</b>")
    if product.camera_main_mp and product.camera_main_mp >= 48:
        bits.append(f"cámara de <b>{product.camera_main_mp} MP</b>")
    if product.battery_mah and product.battery_mah >= 5000:
        bits.append(f"batería de <b>{_format_mah(product.battery_mah)} mAh</b>")
    if bits:
        return "Apuesta por " + ", ".join(bits) + "."
    return None


def _technical_value_line(product: Product, _catalog: list[Product] | None) -> str | None:
    if product.spec_value:
        return product.spec_value.strip()
    if product.monthly_price and product.price:
        months = product.months or 48
        return (
            f"<b>{product.monthly_price:.2f} €/mes</b> durante {months} meses "
            f"({product.price:.0f} € en total)."
        )
    return None


_TECHNICAL_BUILDERS = {
    "battery": _technical_battery_line,
    "camera": _technical_camera_line,
    "work": _technical_work_line,
    "premium": _technical_premium_line,
    "value": _technical_value_line,
}


def _technical_line(product: Product, preference: str, catalog: list[Product] | None) -> str | None:
    builder = _TECHNICAL_BUILDERS.get(preference)
    if not builder:
        return None
    return builder(product, catalog)


def product_pitch(
    product: Product,
    preference: str,
    *,
    rank: int = 1,
    max_monthly: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    is_client: bool | None = None,
    catalog: list[Product] | None = None,
) -> str:
    meta = PREFERENCE_META.get(preference, PREFERENCE_META["value"])
    field = meta["field"]
    score = int(getattr(product, field, 0) or 0)
    score = max(1, min(5, score))
    reason = meta["reasons"].get(score, meta["reasons"][3])

    lines: list[str] = []
    if rank == 1:
        lines.append(f"🥇 <b>Mi mejor recomendación</b> para «{meta['label']}»:")
    elif rank == 2:
        lines.append("🥈 <b>Otra muy buena opción</b>:")
    else:
        lines.append("🥉 <b>También te encaja</b>:")

    technical = _technical_line(product, preference, catalog)
    if technical:
        lines.append(technical)
        lines.append(f"Además, {reason}.")
    else:
        lines.append(f"Te lo propongo porque <b>{reason}</b>.")

    brand_hint = _BRAND_HINTS.get(preference, {}).get(product.brand)
    if brand_hint:
        lines.append(brand_hint)

    if product.promotion and (is_client is not False):
        lines.append(f"Además: {product.promotion}.")

    if is_client is False:
        client_price = product.client_terminal_price()
        terminal = product.terminal_price(is_client=False)
        if client_price and terminal and client_price < terminal:
            saving = terminal - client_price
            lines.append(
                f"Si te haces cliente, el terminal podría quedarte en <b>{client_price:.0f} €</b> "
                f"(ahorro de {saving:.0f} €)."
            )
            if product.monthly_price and product.months:
                lines.append(
                    f"Y podrías financiarlo desde <b>{product.monthly_price:.0f} €/mes</b> en {product.months} meses."
                )
    elif max_monthly and product.monthly_price and product.monthly_price <= max_monthly:
        lines.append(f"Y entra en tu presupuesto de {max_monthly:.0f} €/mes.")
    elif (price_min is not None or price_max is not None) and is_client is not False:
        terminal = product.terminal_price(is_client=True)
        if terminal is not None:
            if price_max is not None and terminal <= price_max:
                lines.append(f"Y el terminal queda en <b>{terminal:.0f} €</b> dentro de tu rango.")

    return " ".join(lines)
