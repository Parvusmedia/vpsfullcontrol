"""Optional Amadeus API quotes (SAR)."""

from __future__ import annotations

import logging
from datetime import date

import httpx

logger = logging.getLogger(__name__)


class AmadeusClient:
    def __init__(self, client_id: str, client_secret: str, host: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host.rstrip("/")
        self._token_value: str | None = None

    async def _fetch_token(self) -> str | None:
        if self._token_value:
            return self._token_value
        url = f"{self._host}/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(url, data=data)
                if resp.status_code != 200:
                    return None
                payload = resp.json()
                self._token_value = payload.get("access_token")
                return self._token_value
        except Exception as exc:
            logger.warning("amadeus token failed: %s", exc)
            return None

    async def quote_sar(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> int | None:
        token = await self._fetch_token()
        if not token:
            return None
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure.isoformat(),
            "adults": 1,
            "currencyCode": "SAR",
            "max": 1,
            "nonStop": "false",
        }
        if return_date:
            params["returnDate"] = return_date.isoformat()
        url = f"{self._host}/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                offers = data.get("data") or []
                if not offers:
                    return None
                price = offers[0].get("price", {}).get("total")
                if price is None:
                    return None
                return int(round(float(price)))
        except Exception as exc:
            logger.warning("amadeus quote failed: %s", exc)
            return None
