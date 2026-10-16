#!/usr/bin/env python3
"""Patch Digitanimal Spain Make scenario: router for optional phone parsing."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


def build_sheets_module(module_id: int, phone_expr: str, designer_y: int, source: dict) -> dict:
    mod = copy.deepcopy(source)
    mod["id"] = module_id
    mod["mapper"] = copy.deepcopy(source["mapper"])
    mod["mapper"]["values"] = copy.deepcopy(source["mapper"]["values"])
    mod["mapper"]["values"]["phone"] = phone_expr
    mod["metadata"] = copy.deepcopy(source["metadata"])
    mod["metadata"]["designer"] = {"x": -327, "y": designer_y}
    return mod


def patch_blueprint(blueprint: dict) -> dict:
    bp = copy.deepcopy(blueprint)
    flow = bp["flow"]
    if len(flow) != 3:
        raise SystemExit(f"Unexpected flow length {len(flow)}, expected 3 modules")

    mod1, mod4, mod2 = flow
    if mod1["id"] != 1 or mod4["id"] != 4 or mod2["id"] != 2:
        raise SystemExit("Unexpected module ids in flow")

    mod4 = copy.deepcopy(mod4)
    mod4["metadata"]["designer"] = {"x": -534, "y": -259}

    mod2_phone = copy.deepcopy(mod2)
    mod2_phone["metadata"]["designer"] = {"x": -177, "y": -259}

    mod5_no_phone = build_sheets_module(5, "", -59, mod2)

    phone_filter = {
        "name": "Tiene teléfono",
        "conditions": [
            [
                {"a": "{{1.data.phone_number}}", "o": "exist"},
                {"a": "{{1.data.phone_number}}", "b": "", "o": "text:notequal"},
            ]
        ],
    }
    no_phone_filter = {
        "name": "Sin teléfono",
        "conditions": [
            [{"a": "{{1.data.phone_number}}", "o": "notexist"}],
            [{"a": "{{1.data.phone_number}}", "b": "", "o": "text:equal"}],
        ],
    }

    mod4["filter"] = phone_filter
    mod5_no_phone["filter"] = no_phone_filter

    router = {
        "id": 3,
        "module": "builtin:BasicRouter",
        "version": 1,
        "parameters": {"else": 2},
        "mapper": {},
        "metadata": {"designer": {"x": -784, "y": -159}},
        "routes": [
            {"flow": [mod4, mod2_phone]},
            {"flow": [mod5_no_phone]},
        ],
    }

    bp["flow"] = [mod1, router]
    return bp


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/scenario_7950608.json")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/opt/cursor/artifacts/digitanimal_spain_blueprint.json")
    data = json.loads(src.read_text())
    blueprint = data["blueprint"] if "blueprint" in data else data
    patched = patch_blueprint(blueprint)
    out.write_text(json.dumps(patched, ensure_ascii=False, indent=2))
    print(out)


if __name__ == "__main__":
    main()
