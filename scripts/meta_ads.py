#!/usr/bin/env python3
"""CLI mínima para Meta Marketing API (campañas/ad sets pausados + lead forms en DRAFT).

Pensado para acceso partner (Parvus) a activos del cliente vía system user + token largo.

  scripts/meta status
  scripts/meta list-pages
  scripts/meta create-campaign --name "..."
  scripts/meta create-adset --campaign-id ... --name "..." --page-id ...
  scripts/meta create-form --page-id ... --name "..."
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DRAFT_NAME_PREFIX = "[CURSOR-DRAFT]"


class MetaGraphClient:
    def __init__(self, access_token: str, graph_version: str) -> None:
        self.access_token = access_token
        self.base = f"https://graph.facebook.com/{graph_version}"

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        params = dict(params or {})
        if body is None:
            params["access_token"] = self.access_token
        else:
            body = dict(body)
            body["access_token"] = self.access_token

        url = f"{self.base}{path}"
        if params and body is None:
            url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"

        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = urllib.parse.urlencode(body, doseq=True).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return response.status, {}
                try:
                    return response.status, json.loads(raw)
                except json.JSONDecodeError:
                    return response.status, {"raw": raw}
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
            except Exception:
                payload = {"error": "http_error", "status": exc.code}
            return exc.code, payload
        except urllib.error.URLError as exc:
            return 0, {"error": "url_error", "detail": str(exc)}


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _load_env_file(path: str | None) -> None:
    if not path:
        return
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _ad_account_path(ad_account_id: str) -> str:
    raw = ad_account_id.strip()
    if raw.startswith("act_"):
        return f"/{raw}"
    return f"/act_{raw}"


def _draft_name(name: str) -> str:
    name = name.strip()
    if name.startswith(DRAFT_NAME_PREFIX):
        return name
    return f"{DRAFT_NAME_PREFIX} {name}"


def _config_from_env() -> dict[str, str]:
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    ad_account = os.getenv("META_AD_ACCOUNT_ID", "").strip()
    graph_version = os.getenv("META_GRAPH_VERSION", "v22.0").strip() or "v22.0"
    privacy = os.getenv("META_PRIVACY_POLICY_URL", "").strip()
    return {
        "token": token,
        "ad_account_id": ad_account,
        "graph_version": graph_version,
        "privacy_policy_url": privacy,
        "client_business_id": os.getenv("META_CLIENT_BUSINESS_ID", "").strip(),
        "partner_business_id": os.getenv("META_PARTNER_BUSINESS_ID", "").strip(),
    }


def _require_client(cfg: dict[str, str]) -> MetaGraphClient | None:
    if not cfg["token"]:
        _print_json(
            {
                "error": "Falta META_ACCESS_TOKEN.",
                "hint": "System user en Parvus BM → generar token con ads_management y pages_manage_ads.",
                "env_example": "deploy/meta.env.example",
            }
        )
        return None
    return MetaGraphClient(cfg["token"], cfg["graph_version"])


def cmd_status(client: MetaGraphClient, cfg: dict[str, str]) -> int:
    status, debug = client.request("GET", "/debug_token", params={"input_token": cfg["token"]})
    me_status, me = client.request("GET", "/me", params={"fields": "id,name"})
    ad_status, ad_info = (0, {})
    if cfg["ad_account_id"]:
        ad_status, ad_info = client.request(
            "GET",
            f"{_ad_account_path(cfg['ad_account_id'])}",
            params={"fields": "id,name,account_status,currency,business"},
        )

    _print_json(
        {
            "graph_version": cfg["graph_version"],
            "env": {
                "META_ACCESS_TOKEN": "set",
                "META_AD_ACCOUNT_ID": cfg["ad_account_id"] or "missing",
                "META_CLIENT_BUSINESS_ID": cfg["client_business_id"] or "unset",
                "META_PARTNER_BUSINESS_ID": cfg["partner_business_id"] or "unset",
                "META_PRIVACY_POLICY_URL": "set" if cfg["privacy_policy_url"] else "missing",
            },
            "debug_token": {"http_status": status, "data": debug},
            "me": {"http_status": me_status, "data": me},
            "ad_account": {"http_status": ad_status, "data": ad_info},
        }
    )
    if status != 200 or me_status != 200:
        return 1
    if cfg["ad_account_id"] and ad_status != 200:
        return 1
    return 0


def cmd_list_pages(client: MetaGraphClient) -> int:
    status, payload = client.request(
        "GET",
        "/me/accounts",
        params={"fields": "id,name,access_token", "limit": 100},
    )
    if status != 200:
        _print_json({"error": "No se pudieron listar páginas", "status": status, "payload": payload})
        return 1
    pages = payload.get("data", []) if isinstance(payload, dict) else []
    safe = [{"id": p.get("id"), "name": p.get("name")} for p in pages if isinstance(p, dict)]
    _print_json({"count": len(safe), "pages": safe})
    return 0


def cmd_create_campaign(
    client: MetaGraphClient,
    cfg: dict[str, str],
    name: str,
    objective: str,
    dry_run: bool,
) -> int:
    if not cfg["ad_account_id"]:
        _print_json({"error": "Falta META_AD_ACCOUNT_ID."})
        return 1

    body = {
        "name": _draft_name(name),
        "objective": objective,
        "status": "PAUSED",
        "special_ad_categories": json.dumps([]),
        "buying_type": "AUCTION",
    }
    path = f"{_ad_account_path(cfg['ad_account_id'])}/campaigns"
    if dry_run:
        _print_json({"dry_run": True, "path": path, "body": body})
        return 0

    status, payload = client.request("POST", path, body=body)
    _print_json({"http_status": status, "result": payload})
    return 0 if status == 200 and isinstance(payload, dict) and payload.get("id") else 1


def cmd_create_adset(
    client: MetaGraphClient,
    cfg: dict[str, str],
    campaign_id: str,
    name: str,
    page_id: str,
    daily_budget_eur: float,
    country: str,
    dry_run: bool,
) -> int:
    if not cfg["ad_account_id"]:
        _print_json({"error": "Falta META_AD_ACCOUNT_ID."})
        return 1
    if not page_id:
        _print_json({"error": "Falta --page-id (requerido para promoted_object en leads)."})
        return 1

    daily_budget = max(100, int(daily_budget_eur * 100))
    targeting = {"geo_locations": {"countries": [country.upper()]}}
    body = {
        "name": _draft_name(name),
        "campaign_id": campaign_id,
        "status": "PAUSED",
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "LEAD_GENERATION",
        "daily_budget": str(daily_budget),
        "targeting": json.dumps(targeting),
        "promoted_object": json.dumps({"page_id": page_id}),
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
    }
    path = f"{_ad_account_path(cfg['ad_account_id'])}/adsets"
    if dry_run:
        _print_json({"dry_run": True, "path": path, "body": body})
        return 0

    status, payload = client.request("POST", path, body=body)
    _print_json({"http_status": status, "result": payload})
    return 0 if status == 200 and isinstance(payload, dict) and payload.get("id") else 1


def _default_form_questions() -> list[dict[str, str]]:
    return [
        {"type": "FULL_NAME"},
        {"type": "EMAIL"},
        {"type": "PHONE"},
    ]


def _page_access_token(client: MetaGraphClient, page_id: str) -> str | None:
    status, payload = client.request(
        "GET",
        "/me/accounts",
        params={"fields": "id,access_token", "limit": 100},
    )
    if status != 200 or not isinstance(payload, dict):
        return None
    for page in payload.get("data", []):
        if isinstance(page, dict) and page.get("id") == page_id and page.get("access_token"):
            return str(page["access_token"])
    return None


def _questions_for_create(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for q in questions:
        qtype = q.get("type")
        if qtype == "CUSTOM":
            out.append(
                {
                    "type": "CUSTOM",
                    "key": q["key"],
                    "label": q["label"],
                    "options": [{"key": o["key"], "value": o["value"]} for o in q.get("options", [])],
                }
            )
        elif qtype:
            out.append({"type": qtype})
    return out


def _privacy_policy_block(url: str) -> dict[str, str]:
    return {
        "url": url,
        "link_text": "Consulta la Política de privacidad de digitanimal.",
    }


def _load_form_questions(template_path: str | None) -> list[dict[str, Any]]:
    if not template_path:
        return _default_form_questions()
    data = json.loads(Path(template_path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("questions"), list):
        return data["questions"]
    if isinstance(data, list):
        return data
    raise ValueError("Plantilla de formulario inválida: esperaba lista o {questions: [...]}")


def _post_leadgen_form(
    client: MetaGraphClient,
    page_id: str,
    body: dict[str, Any],
    page_token: str,
) -> tuple[int, Any]:
    path = f"/{page_id}/leadgen_forms"
    full = dict(body)
    full["access_token"] = page_token
    data = urllib.parse.urlencode(full, doseq=True).encode("utf-8")
    req = urllib.request.Request(
        f"{client.base}{path}",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return exc.code, {"error": "http_error"}


def cmd_get_form(client: MetaGraphClient, page_id: str, form_id: str) -> int:
    page_token = _page_access_token(client, page_id)
    if not page_token:
        _print_json({"error": f"No hay page access token para page_id={page_id}."})
        return 1
    fields = (
        "id,name,status,locale,created_time,questions,privacy_policy_url,"
        "thank_you_page,legal_content,follow_up_action_url"
    )
    status, payload = client.request("GET", f"/{form_id}", params={"fields": fields})
    # GET form works with system token sometimes; retry with page token via urlopen
    if status != 200:
        params = {"fields": fields, "access_token": page_token}
        url = f"{client.base}/{form_id}?{urllib.parse.urlencode(params)}"
        with urllib.request.urlopen(url, timeout=60) as response:
            payload = json.loads(response.read())
            status = response.status
    _print_json({"http_status": status, "form": payload})
    return 0 if status == 200 else 1


def cmd_duplicate_form(
    client: MetaGraphClient,
    cfg: dict[str, str],
    page_id: str,
    source_form_id: str,
    name: str,
    follow_up_url: str | None,
    exact_name: bool,
    prepare_only: bool,
    dry_run: bool,
) -> int:
    page_token = _page_access_token(client, page_id)
    if not page_token:
        _print_json({"error": f"No hay page access token para page_id={page_id}."})
        return 1

    fields = "questions,thank_you_page,locale,privacy_policy_url,legal_content,follow_up_action_url"
    params = {"fields": fields, "access_token": page_token}
    url = f"{client.base}/{source_form_id}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        source = json.loads(response.read())

    privacy = (
        (cfg["privacy_policy_url"] or "").strip()
        or (source.get("privacy_policy_url") or "").strip()
        or (source.get("legal_content", {}) or {}).get("privacy_policy", {}).get("url", "")
    )
    if not privacy:
        _print_json({"error": "Falta URL de privacidad (META_PRIVACY_POLICY_URL)."})
        return 1

    follow_up = (follow_up_url or source.get("follow_up_action_url") or "").strip()
    if not follow_up:
        _print_json({"error": "Falta --follow-up-url o follow_up en el formulario origen."})
        return 1

    questions_out = _questions_for_create(source.get("questions", []))
    ty = source.get("thank_you_page") or {}
    thank_you = {
        "title": ty.get("title", "Muchas Gracias."),
        "body": ty.get("body", ""),
        "button_text": ty.get("button_text", "Ver sitio web"),
        "button_type": ty.get("button_type", "VIEW_WEBSITE"),
        "website_url": follow_up,
        "enable_messenger": ty.get("enable_messenger", False),
    }
    form_name = name.strip() if exact_name else _draft_name(name)
    body = {
        "name": form_name,
        "locale": source.get("locale", "es_ES"),
        "status": "DRAFT",
        "questions": json.dumps(questions_out, ensure_ascii=False),
        "thank_you_page": json.dumps(thank_you, ensure_ascii=False),
        "follow_up_action_url": follow_up,
        "privacy_policy": json.dumps(_privacy_policy_block(privacy), ensure_ascii=False),
    }

    spec = {
        "page_id": page_id,
        "source_form_id": source_form_id,
        "requested_status": "DRAFT",
        "body": body,
        "meta_api_note": (
            "La Graph API suele publicar el formulario como ACTIVE (Sharing: Restricted) "
            "aunque status=DRAFT. Para borrador editable usa la pestaña Draft forms en Ads Manager: "
            "duplicar el form origen y aplicar estos cambios."
        ),
    }

    if prepare_only or dry_run:
        _print_json({"prepare_only": prepare_only or dry_run, **spec})
        return 0

    status, payload = _post_leadgen_form(client, page_id, body, page_token)
    actual_status: str | None = None
    if status == 200 and isinstance(payload, dict) and payload.get("id"):
        verify_params = {"fields": "id,name,status", "access_token": page_token}
        verify_url = f"{client.base}/{payload['id']}?{urllib.parse.urlencode(verify_params)}"
        with urllib.request.urlopen(verify_url, timeout=60) as response:
            verified = json.loads(response.read())
            actual_status = verified.get("status")

    _print_json(
        {
            "http_status": status,
            "result": payload,
            "actual_status": actual_status,
            "warning": spec["meta_api_note"] if actual_status and actual_status != "DRAFT" else None,
        }
    )
    return 0 if status == 200 and isinstance(payload, dict) and payload.get("id") else 1


def cmd_create_form(
    client: MetaGraphClient,
    cfg: dict[str, str],
    page_id: str,
    name: str,
    template_path: str | None,
    privacy_url: str | None,
    follow_up_url: str | None,
    exact_name: bool,
    prepare_only: bool,
    dry_run: bool,
) -> int:
    privacy = (privacy_url or cfg["privacy_policy_url"] or "").strip()
    if not privacy:
        _print_json(
            {
                "error": "Falta URL de privacidad.",
                "hint": "META_PRIVACY_POLICY_URL o --privacy-url",
            }
        )
        return 1

    follow_up = (follow_up_url or os.getenv("META_DEFAULT_FOLLOW_UP_URL", "")).strip()
    if not follow_up and not prepare_only:
        _print_json(
            {
                "error": "Falta follow-up URL.",
                "hint": "META_DEFAULT_FOLLOW_UP_URL o --follow-up-url",
            }
        )
        return 1

    try:
        questions = _load_form_questions(template_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        _print_json({"error": str(exc)})
        return 1

    questions_out = _questions_for_create(questions)
    form_name = name.strip() if exact_name else _draft_name(name)
    body = {
        "name": form_name,
        "status": "DRAFT",
        "locale": "es_ES",
        "questions": json.dumps(questions_out, ensure_ascii=False),
        "privacy_policy": json.dumps(_privacy_policy_block(privacy), ensure_ascii=False),
    }
    if follow_up:
        body["follow_up_action_url"] = follow_up
        body["thank_you_page"] = json.dumps(
            {
                "title": "Muchas Gracias.",
                "body": "",
                "button_text": "Ver sitio web",
                "button_type": "VIEW_WEBSITE",
                "website_url": follow_up,
            },
            ensure_ascii=False,
        )

    if prepare_only or dry_run:
        _print_json({"prepare_only": prepare_only or dry_run, "page_id": page_id, "body": body})
        return 0

    page_token = _page_access_token(client, page_id)
    if not page_token:
        _print_json({"error": f"No hay page access token para page_id={page_id}."})
        return 1

    status, payload = _post_leadgen_form(client, page_id, body, page_token)
    _print_json({"http_status": status, "result": payload})
    return 0 if status == 200 and isinstance(payload, dict) and payload.get("id") else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meta Ads helper (borradores pausados / forms DRAFT).")
    parser.add_argument(
        "--env-file",
        default=os.getenv("META_ENV_FILE"),
        help="Ruta a fichero .env (también META_ENV_FILE).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Validar token y acceso a la ad account.")
    sub.add_parser("list-pages", help="Páginas accesibles con el token (elegir page_id).")

    camp = sub.add_parser("create-campaign", help="Crear campaña PAUSED.")
    camp.add_argument("--name", required=True)
    camp.add_argument("--objective", default="OUTCOME_LEADS")
    camp.add_argument("--dry-run", action="store_true")

    adset = sub.add_parser("create-adset", help="Crear ad set PAUSED (leads).")
    adset.add_argument("--campaign-id", required=True)
    adset.add_argument("--name", required=True)
    adset.add_argument("--page-id", required=True)
    adset.add_argument("--daily-budget-eur", type=float, default=5.0)
    adset.add_argument("--country", default="ES")
    adset.add_argument("--dry-run", action="store_true")

    form = sub.add_parser("create-form", help="Crear lead form (preferir --prepare-only; ver META_ADS_SETUP.md).")
    form.add_argument("--page-id", required=True)
    form.add_argument("--name", required=True)
    form.add_argument("--template", help="JSON con questions (ver deploy/meta_lead_form.example.json).")
    form.add_argument("--privacy-url")
    form.add_argument("--follow-up-url")
    form.add_argument("--exact-name", action="store_true", help="No añadir prefijo [CURSOR-DRAFT].")
    form.add_argument(
        "--prepare-only",
        action="store_true",
        help="Solo devolver spec JSON (recomendado: duplicar en pestaña Draft forms).",
    )
    form.add_argument("--dry-run", action="store_true")

    get_form = sub.add_parser("get-form", help="Leer un lead form por ID.")
    get_form.add_argument("--page-id", required=True)
    get_form.add_argument("--form-id", required=True)

    dup = sub.add_parser("duplicate-form", help="Duplicar lead form desde un ID origen.")
    dup.add_argument("--page-id", required=True)
    dup.add_argument("--source-form-id", required=True)
    dup.add_argument("--name", required=True)
    dup.add_argument("--follow-up-url")
    dup.add_argument("--exact-name", action="store_true")
    dup.add_argument("--prepare-only", action="store_true")
    dup.add_argument("--dry-run", action="store_true")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _load_env_file(args.env_file)
    cfg = _config_from_env()
    client = _require_client(cfg)
    if client is None:
        return 1

    if args.command == "status":
        return cmd_status(client, cfg)
    if args.command == "list-pages":
        return cmd_list_pages(client)
    if args.command == "create-campaign":
        return cmd_create_campaign(client, cfg, args.name, args.objective, args.dry_run)
    if args.command == "create-adset":
        return cmd_create_adset(
            client,
            cfg,
            args.campaign_id,
            args.name,
            args.page_id,
            args.daily_budget_eur,
            args.country,
            args.dry_run,
        )
    if args.command == "get-form":
        return cmd_get_form(client, args.page_id, args.form_id)
    if args.command == "duplicate-form":
        return cmd_duplicate_form(
            client,
            cfg,
            args.page_id,
            args.source_form_id,
            args.name,
            args.follow_up_url,
            args.exact_name,
            args.prepare_only,
            args.dry_run,
        )
    if args.command == "create-form":
        return cmd_create_form(
            client,
            cfg,
            args.page_id,
            args.name,
            args.template,
            args.privacy_url,
            args.follow_up_url,
            args.exact_name,
            args.prepare_only,
            args.dry_run,
        )

    _print_json({"error": "Comando no soportado."})
    return 1


if __name__ == "__main__":
    sys.exit(main())
