"""Live Saudia fare quotes for specific dates."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from flightsdemobot.config import Settings
from flightsdemobot.saudia.booking_url import booking_url
from flightsdemobot.saudia.amadeus import AmadeusClient

logger = logging.getLogger(__name__)

PRICE_PATTERNS = [
    re.compile(r'"totalPrice"\s*:\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)', re.I),
    re.compile(r'"amount"\s*:\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)', re.I),
    re.compile(r'SAR\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)', re.I),
    re.compile(r'(?:from|starting at)\s*SAR\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)', re.I),
]

USER_AGENT = (
    "Mozilla/5.0 (compatible; ParvusFlightsDemo/1.0; +https://flights.pmediaplus.com/demo)"
)


@dataclass
class FareQuote:
    origin: str
    destination: str
    departure: date
    return_date: date | None
    price_sar: int
    currency: str
    book_url: str
    source: str
    is_exact: bool = True
    over_budget: bool = False


class QuoteService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._amadeus = (
            AmadeusClient(
                settings.amadeus_client_id,
                settings.amadeus_client_secret,
                settings.amadeus_host,
            )
            if settings.amadeus_client_id and settings.amadeus_client_secret
            else None
        )
        self._network_cache: dict | None = None

    async def search(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
        max_price_sar: int,
    ) -> tuple[list[FareQuote], list[FareQuote]]:
        """Return (exact_matches_under_budget, flex_matches_under_budget)."""
        origin = origin.upper()
        destination = destination.upper()
        exact_quote = await self._quote_one(origin, destination, departure, return_date)
        flex_candidates: list[FareQuote] = []
        stay = None
        if return_date is not None:
            stay = (return_date - departure).days

        for offset in range(-3, 4):
            if offset == 0:
                continue
            dep = departure + timedelta(days=offset)
            ret = None
            if stay is not None:
                ret = dep + timedelta(days=stay)
            quote = await self._quote_one(origin, destination, dep, ret)
            if quote:
                quote.is_exact = False
                flex_candidates.append(quote)

        exact_under: list[FareQuote] = []
        flex_under: list[FareQuote] = []
        if exact_quote:
            if exact_quote.price_sar <= max_price_sar:
                exact_under.append(exact_quote)
            else:
                exact_quote.over_budget = True

        for q in flex_candidates:
            if q.price_sar <= max_price_sar:
                flex_under.append(q)

        flex_under.sort(key=lambda x: x.price_sar)
        cheapest_exact = exact_quote.price_sar if exact_quote else None
        if cheapest_exact is not None:
            flex_under = [q for q in flex_under if q.price_sar < cheapest_exact]
        flex_under = flex_under[:3]

        if not exact_under and exact_quote and exact_quote.over_budget:
            flex_under = sorted(flex_candidates, key=lambda x: x.price_sar)[:1]
            for q in flex_under:
                q.over_budget = q.price_sar > max_price_sar

        return exact_under[:3], flex_under[:3]

    async def _quote_one(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> FareQuote | None:
        if self._settings.mock_quotes:
            return self._mock_quote(origin, destination, departure, return_date)

        if self._amadeus:
            price = await self._amadeus.quote_sar(origin, destination, departure, return_date)
            if price is not None:
                return FareQuote(
                    origin=origin,
                    destination=destination,
                    departure=departure,
                    return_date=return_date,
                    price_sar=price,
                    currency="SAR",
                    book_url=booking_url(origin, destination, departure, return_date),
                    source="amadeus",
                )

        scraped = await self._scrape_saudia(origin, destination, departure, return_date)
        if scraped is not None:
            return FareQuote(
                origin=origin,
                destination=destination,
                departure=departure,
                return_date=return_date,
                price_sar=scraped,
                currency="SAR",
                book_url=booking_url(origin, destination, departure, return_date),
                source="saudia_scrape",
            )

        feed_price = await self._feed_month_floor(origin, destination, departure)
        if feed_price is not None:
            return FareQuote(
                origin=origin,
                destination=destination,
                departure=departure,
                return_date=return_date,
                price_sar=feed_price,
                currency="SAR",
                book_url=booking_url(origin, destination, departure, return_date),
                source="network_month_floor",
            )
        return None

    def _mock_quote(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> FareQuote:
        base = 300 + abs(hash((origin, destination, departure.isoformat())) % 400)
        if return_date:
            base += 80
        return FareQuote(
            origin=origin,
            destination=destination,
            departure=departure,
            return_date=return_date,
            price_sar=base,
            currency="SAR",
            book_url=booking_url(origin, destination, departure, return_date),
            source="mock",
        )

    async def _scrape_saudia(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> int | None:
        url = booking_url(origin, destination, departure, return_date)
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.quote_timeout,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    return None
                text = resp.text[:500000]
                if "Pardon Our Interruption" in text or "reese" in text.lower():
                    return None
                for pattern in PRICE_PATTERNS:
                    match = pattern.search(text)
                    if match:
                        value = float(match.group(1))
                        if 50 <= value <= 50000:
                            return int(round(value))
        except Exception as exc:
            logger.warning("saudia scrape failed %s-%s: %s", origin, destination, exc)
        return None

    async def _feed_month_floor(
        self,
        origin: str,
        destination: str,
        departure: date,
    ) -> int | None:
        """Use published month minimum from flights feed when live scrape is blocked."""
        try:
            feed = await self._load_network()
            month = departure.strftime("%Y-%m")
            for fare in feed.get("fares", []):
                if (
                    fare.get("origin") == origin
                    and fare.get("destination") == destination
                    and fare.get("month") == month
                ):
                    price = fare.get("price")
                    if isinstance(price, (int, float)):
                        return int(round(price))
        except Exception as exc:
            logger.warning("network feed lookup failed: %s", exc)
        return None

    async def _load_network(self) -> dict:
        if self._network_cache is not None:
            return self._network_cache
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(self._settings.network_feed_url)
            resp.raise_for_status()
            self._network_cache = resp.json()
            return self._network_cache

    async def quote_batch(self, jobs: list[tuple[str, str, date, date | None]]) -> list[FareQuote | None]:
        sem = asyncio.Semaphore(self._settings.quote_max_concurrent)
        results: list[FareQuote | None] = [None] * len(jobs)

        async def run(idx: int, job: tuple[str, str, date, date | None]) -> None:
            async with sem:
                o, d, dep, ret = job
                results[idx] = await self._quote_one(o, d, dep, ret)

        await asyncio.gather(*(run(i, job) for i, job in enumerate(jobs)))
        return results
