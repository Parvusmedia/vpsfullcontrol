#!/usr/bin/env python3
"""Coalesce Meta phone slugs (phone_number + número_de_teléfono) in Spain Make blueprint."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

# Make IML: first non-empty wins
PHONE_RAW = "{{ifempty(1.data.phone_number; 1.data.`número_de_teléfono`)}}"

HAS_PHONE_FILTER = {
    "name": "Tiene teléfono",
    "conditions": [
        [
            {"a": PHONE_RAW, "o": "exist"},
            {"a": PHONE_RAW, "b": "", "o": "text:notequal"},
        ]
    ],
}

NO_PHONE_FILTER = {
    "name": "Sin teléfono",
    "conditions": [
        [{"a": PHONE_RAW, "o": "notexist"}],
        [{"a": PHONE_RAW, "b": "", "o": "text:equal"}],
    ],
}


def patch_blueprint(blueprint: dict) -> dict:
    bp = copy.deepcopy(blueprint)
    router = bp["flow"][1]
    if router.get("module") != "builtin:BasicRouter":
        raise SystemExit("Expected router at flow[1]")

    parse_mod = router["routes"][0]["flow"][0]
    if parse_mod.get("module") != "phonenumber:TransformerParseNumber":
        raise SystemExit("Expected phone parser in route 0")
    parse_mod["filter"] = copy.deepcopy(HAS_PHONE_FILTER)
    parse_mod["mapper"]["number"] = PHONE_RAW

    no_phone_sheets = router["routes"][1]["flow"][0]
    no_phone_sheets["filter"] = copy.deepcopy(NO_PHONE_FILTER)

    return bp


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/scenario_7950608.json")
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else Path("/opt/cursor/artifacts/digitanimal_spain_blueprint_coalesce.json")
    )
    payload = json.loads(src.read_text())
    blueprint = payload.get("blueprint", payload)
    patched = patch_blueprint(blueprint)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(patched, ensure_ascii=False, indent="\t"))
    print(out)


if __name__ == "__main__":
    main()
