"""Patch VPS unipile-drain copies: already_invited is terminal, no double-log."""

from __future__ import annotations

from pathlib import Path

OLD_HELPER = '''def _is_provider_limit(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    if http_status == 422 and ("cannot_resend" in hay or "limit" in hay and "invit" in hay):
        return True
    if http_status == 429:
        return True
    return "rate limit" in hay or "too many" in hay or "throttl" in hay
'''

NEW_HELPER = '''def _is_already_invited(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    return any(
        needle in hay
        for needle in (
            "already_invited_recently",
            "already_invited",
            "should delay new invitation",
            "invitation has already been sent",
        )
    )


def _is_invalid_provider(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    return http_status == 400 and (
        "user id does not match" in hay or "does not match provider" in hay
    )


def _is_provider_limit(http_status: int, err_text: str) -> bool:
    hay = f"{http_status} {err_text}".lower()
    if _is_already_invited(http_status, err_text):
        return False
    if http_status == 422 and ("cannot_resend" in hay or "limit" in hay and "invit" in hay):
        return True
    if http_status == 429:
        return True
    return "rate limit" in hay or "too many" in hay or "throttl" in hay
'''

OLD_HTTP = '''        if resp.status_code >= 400:
            limits.log_action(
                cfg=cfg,
                rule=rule,
                status="failed",
                target_id=str(provider_id or public_id or ""),
                target_url=url,
                source_row_id=source_row_id or dedupe_key,
                http_status=resp.status_code,
                error_message=text[:800],
                request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
            )
            if _is_provider_limit(resp.status_code, text):
                try:
                    limits.pause_account(cfg=cfg, rule=rule, reason=f"provider_limit http={resp.status_code}")
                except Exception:
                    logger.exception("pause_account failed")
                return {
                    "ok": False,
                    "skipped": True,
                    "reason": "provider_limit",
                    "http_status": resp.status_code,
                    "error": text[:500],
                }
            resp.raise_for_status()
'''

NEW_HTTP = '''        if resp.status_code >= 400:
            target = str(provider_id or public_id or "")
            src = source_row_id or dedupe_key
            if _is_already_invited(resp.status_code, text):
                limits.log_action(
                    cfg=cfg,
                    rule=rule,
                    status="skipped",
                    target_id=target,
                    target_url=url,
                    source_row_id=src,
                    http_status=resp.status_code,
                    error_code="already_invited_recently",
                    error_message=text[:800],
                    request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
                )
                return {
                    "ok": True,
                    "skipped": True,
                    "reason": "already_invited_recently",
                    "http_status": resp.status_code,
                    "status": "already_invited",
                }
            if _is_invalid_provider(resp.status_code, text):
                limits.log_action(
                    cfg=cfg,
                    rule=rule,
                    status="skipped",
                    target_id=target,
                    target_url=url,
                    source_row_id=src,
                    http_status=resp.status_code,
                    error_code="invalid_provider_id",
                    error_message=text[:800],
                    request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
                )
                return {
                    "ok": True,
                    "skipped": True,
                    "reason": "invalid_provider_id",
                    "http_status": resp.status_code,
                    "status": "invalid_provider",
                }
            limits.log_action(
                cfg=cfg,
                rule=rule,
                status="failed",
                target_id=target,
                target_url=url,
                source_row_id=src,
                http_status=resp.status_code,
                error_message=text[:800],
                request_payload=json.dumps(invite_body, ensure_ascii=False)[:1500],
            )
            if _is_provider_limit(resp.status_code, text):
                try:
                    limits.pause_account(cfg=cfg, rule=rule, reason=f"provider_limit http={resp.status_code}")
                except Exception:
                    logger.exception("pause_account failed")
                return {
                    "ok": False,
                    "skipped": True,
                    "reason": "provider_limit",
                    "http_status": resp.status_code,
                    "error": text[:500],
                }
            return {
                "ok": False,
                "error": text[:500],
                "http_status": resp.status_code,
            }
'''

OLD_LOOKUP_TAIL = '''    except Exception:
        logger.exception("unipile user lookup failed")

    invite_body: dict[str, Any] = {
'''

NEW_LOOKUP_TAIL = '''    except Exception:
        logger.exception("unipile user lookup failed")

    try:
        if hasattr(limits, "has_resolved_invite") and limits.has_resolved_invite(
            cfg=cfg,
            target_ids=[str(provider_id or ""), str(public_id or "")],
            source_row_id=source_row_id or dedupe_key,
        ):
            return {
                "ok": True,
                "skipped": True,
                "reason": "already_invited_recently",
                "status": "already_resolved",
            }
    except Exception:
        logger.exception("resolved invite lookup failed")

    invite_body: dict[str, Any] = {
'''

HAS_RESOLVED = '''
def has_resolved_invite(
    *,
    cfg,
    target_ids: list[str] | None = None,
    source_row_id: str = "",
) -> bool:
    """True if this person/row already succeeded or was skipped (do not resend)."""
    for tid in [str(t).strip() for t in (target_ids or []) if str(t).strip()]:
        where = f"(target_id,eq,{tid})~and(status,in,success,skipped)"
        if _count_logs(cfg=cfg, where=where) > 0:
            return True
    src = str(source_row_id or "").strip()
    if src:
        where = f"(source_row_id,eq,{src})~and(status,in,success,skipped)"
        if _count_logs(cfg=cfg, where=where) > 0:
            return True
    return False


'''

UNIPILE_FILES = [
    Path("/opt/apps/prospeccion-alarmas/alarmas/unipile.py"),
    Path("/opt/apps/prospeccion-alarmas-us/alarmas/unipile.py"),
    Path("/opt/apps/prospeccion-parvus-agencias-en/agencies/unipile.py"),
    Path("/opt/apps/prospeccion-usj-universidades/usj/unipile.py"),
]

LIMITS_FILES = [
    Path("/opt/apps/prospeccion-alarmas/alarmas/automation_limits.py"),
    Path("/opt/apps/prospeccion-alarmas-us/alarmas/automation_limits.py"),
    Path("/opt/apps/prospeccion-parvus-agencias-en/agencies/automation_limits.py"),
    Path("/opt/apps/prospeccion-usj-universidades/usj/automation_limits.py"),
]


def _replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new.strip() in text and old not in text:
        print(f"SKIP already patched {label} {path}")
        return
    if old not in text:
        raise SystemExit(f"MISSING block {label} in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"OK {label} {path}")


def patch_unipile(path: Path) -> None:
    _replace_once(path, OLD_HELPER, NEW_HELPER, "helpers")
    _replace_once(path, OLD_HTTP, NEW_HTTP, "http")
    _replace_once(path, OLD_LOOKUP_TAIL, NEW_LOOKUP_TAIL, "resolved-check")


def patch_limits(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "def has_resolved_invite(" in text:
        print(f"SKIP has_resolved_invite {path}")
        return
    needle = "def _count_logs("
    idx = text.find(needle)
    if idx < 0:
        raise SystemExit(f"MISSING _count_logs in {path}")
    # insert before _count_logs
    path.write_text(text[:idx] + HAS_RESOLVED + text[idx:], encoding="utf-8")
    print(f"OK has_resolved_invite {path}")


N8N_JSON_FILES = [
    Path("/opt/apps/linkedinreport/docs/n8n/NextConvers_Step2_Process_Pending_LinkedIn_Invites_Throttled.json"),
    Path("/opt/apps/linkedinreport/docs/n8n/Incremental_Step2_Process_Pending_LinkedIn_Invites_Throttled.json"),
]


def patch_n8n_classify() -> None:
    js_path = Path(__file__).resolve().parent / "n8n_classify_unipile_outcome.js"
    js = js_path.read_text(encoding="utf-8")
    import json

    for path in N8N_JSON_FILES:
        if not path.is_file():
            print(f"SKIP missing n8n json {path}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for node in data.get("nodes") or []:
            if node.get("name") == "Classify Unipile Outcome":
                node.setdefault("parameters", {})["jsCode"] = js
                changed += 1
        if not changed:
            print(f"SKIP no Classify Unipile Outcome in {path}")
            continue
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"OK n8n classify {path}")


def main() -> None:
    for path in UNIPILE_FILES:
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        patch_unipile(path)
    for path in LIMITS_FILES:
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        patch_limits(path)
    patch_n8n_classify()


if __name__ == "__main__":
    main()
