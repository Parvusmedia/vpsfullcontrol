"""NocoDB HTTP client (v2 API)."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings


class NocoDBClient:
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.nocodb_base_url.rstrip("/")
        self.token = s.nocodb_api_token
        self.base_id = s.nocodb_base_id

    @property
    def configured(self) -> bool:
        return bool(self.token and self.base_id)

    def _headers(self) -> dict[str, str]:
        return {"xc-token": self.token, "Content-Type": "application/json"}

    async def request(self, method: str, path: str, json: dict | list | None = None) -> Any:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.request(
                method,
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=json,
            )
            resp.raise_for_status()
            if resp.content:
                return resp.json()
            return {}

    async def list_tables(self) -> list[dict]:
        data = await self.request("GET", f"/api/v2/meta/bases/{self.base_id}/tables")
        return data.get("list", [])

    async def create_table(self, table_def: dict) -> dict:
        return await self.request("POST", f"/api/v2/meta/bases/{self.base_id}/tables", table_def)

    async def list_records(self, table_id: str, *, limit: int = 200, where: str | None = None) -> list[dict]:
        params = f"?limit={limit}"
        if where:
            params += f"&where={where}"
        data = await self.request("GET", f"/api/v2/tables/{table_id}/records{params}")
        return data.get("list", [])

    async def create_record(self, table_id: str, fields: dict) -> dict:
        return await self.request("POST", f"/api/v2/tables/{table_id}/records", fields)

    async def update_record(self, table_id: str, record_id: str | int, fields: dict) -> dict:
        # NocoDB v2: PATCH bulk endpoint; record Id goes in the body, not the URL path.
        payload = {"Id": int(record_id) if str(record_id).isdigit() else record_id, **fields}
        result = await self.request("PATCH", f"/api/v2/tables/{table_id}/records", payload)
        if isinstance(result, list) and result:
            return result[0]
        return result if isinstance(result, dict) else {"Id": record_id}


nocodb = NocoDBClient()
