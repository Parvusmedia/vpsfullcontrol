#!/usr/bin/env python3
"""Backward-compatible wrapper. Prefer migrate_products.py."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.migrate_products import migrate_data


async def main() -> None:
    await migrate_data(dry_run=False)


if __name__ == "__main__":
    asyncio.run(main())
