"""Sesión del panel admin vía cookie HttpOnly (sin pegar clave manualmente)."""

from __future__ import annotations

import hashlib
import hmac

from fastapi import Cookie, Header, HTTPException

from app.config import get_settings

PANEL_COOKIE = "mp_panel_session"


def panel_session_token() -> str:
    key = get_settings().admin_api_key
    return hmac.new(key.encode(), b"movistar-parati-panel", hashlib.sha256).hexdigest()


def require_admin(
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    mp_panel_session: str | None = Cookie(default=None, alias=PANEL_COOKIE),
) -> None:
    expected = get_settings().admin_api_key
    if x_admin_key and x_admin_key == expected:
        return
    if mp_panel_session and mp_panel_session == panel_session_token():
        return
    raise HTTPException(401, "Invalid admin key")
