"""Build Saudia booking deeplinks (same pattern as the HTML5 demo)."""

from __future__ import annotations

from datetime import date
from urllib.parse import quote


BOOKING_BASE = "https://www.saudia.com/booking"


def booking_url(
    origin: str,
    destination: str,
    departure: date,
    return_date: date | None,
) -> str:
    origin = origin.upper()
    destination = destination.upper()
    trip = "OW" if return_date is None else "RT"
    dep_ts = f"{departure.isoformat()}T00:00:00"
    url = (
        f"{BOOKING_BASE}?B_LOCATION={quote(origin)}"
        f"&E_LOCATION={quote(destination)}"
        f"&trip_type={trip}"
        f"&DATE_1={quote(dep_ts)}"
    )
    if return_date is not None:
        ret_ts = f"{return_date.isoformat()}T00:00:00"
        url += f"&DATE_2={quote(ret_ts)}"
    return url
