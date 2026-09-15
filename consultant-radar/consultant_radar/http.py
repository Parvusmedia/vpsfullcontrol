from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; ConsultantRadar/0.1; "
    "+https://github.com/Parvusmedia/vpsfullcontrol)"
)
DEFAULT_TIMEOUT = 25


class HttpError(RuntimeError):
    def __init__(self, url: str, status: int, body: bytes = b""):
        super().__init__(f"HTTP {status} for {url}")
        self.url = url
        self.status = status
        self.body = body


def request(
    url: str,
    *,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    opener: urllib.request.OpenerDirector | None = None,
) -> tuple[int, str, bytes]:
    hdrs = {
        "User-Agent": DEFAULT_UA,
        "Accept": "application/json, text/html, application/xml, text/xml, */*;q=0.8",
    }
    if headers:
        hdrs.update(headers)
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    open_fn = opener.open if opener else urllib.request.urlopen
    try:
        with open_fn(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("content-type", ""), resp.read()
    except urllib.error.HTTPError as exc:
        raise HttpError(url, exc.code, exc.read()) from exc


def get_text(url: str, **kwargs: Any) -> str:
    _status, _ct, body = request(url, **kwargs)
    return body.decode("utf-8", "replace")


def get_json(url: str, **kwargs: Any) -> Any:
    _status, _ct, body = request(url, **kwargs)
    return json.loads(body.decode("utf-8"))
