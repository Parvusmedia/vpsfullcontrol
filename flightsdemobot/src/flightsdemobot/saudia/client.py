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
        self._scrape_blocked = False
        self._ctx_adults = 1
        self._ctx_cabin = "economy"
        self._ctx_max_price = 5000

    async def search(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
        max_price_sar: int,
        *,
        adults: int = 1,
        cabin: str = "economy",
        demo_only: bool = False,
    ) -> tuple[list[FareQuote], list[FareQuote]]:
        """Return (exact_matches_under_budget, flex_matches_under_budget)."""
        self._ctx_adults = max(1, int(adults))
        self._ctx_cabin = cabin or "economy"
        self._ctx_max_price = max_price_sar
        origin = origin.upper()
        destination = destination.upper()

        jobs: list[tuple[str, str, date, date | None]] = [
            (origin, destination, departure, return_date),
        ]
        stay = None
        if return_date is not None:
            stay = (return_date - departure).days

        for offset in range(-3, 4):
            if offset == 0:
                continue
            dep = departure + timedelta(days=offset)
            ret = dep + timedelta(days=stay) if stay is not None else None
            jobs.append((origin, destination, dep, ret))

        results = await self.quote_batch(jobs, demo_only=demo_only)
        exact_quote = results[0]
        flex_candidates: list[FareQuote] = []
        for quote in results[1:]:
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
        *,
        demo_only: bool = False,
    ) -> FareQuote:
        if demo_only or self._settings.mock_quotes:
            return self._demo_quote(origin, destination, departure, return_date)

        book = self._book_url(origin, destination, departure, return_date)

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
                    book_url=book,
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
                book_url=book,
                source="saudia_scrape",
            )

        feed_result = await self._feed_month_floor(origin, destination, departure)
        if feed_result is not None:
            price, month_exact = feed_result
            return FareQuote(
                origin=origin,
                destination=destination,
                departure=departure,
                return_date=return_date,
                price_sar=price,
                currency="SAR",
                book_url=book,
                source="network_month_floor",
                is_exact=month_exact,
            )
        return self._demo_quote(origin, destination, departure, return_date)

    def _book_url(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> str:
        return booking_url(
            origin,
            destination,
            departure,
            return_date,
            adults=self._ctx_adults,
            cabin=self._ctx_cabin,
        )

    def _demo_quote(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> FareQuote:
        """Simulated fare when live Saudia data is unavailable (Parvus demo)."""
        seed = abs(
            hash(
                (
                    origin,
                    destination,
                    departure.isoformat(),
                    return_date.isoformat() if return_date else "",
                )
            )
        )
        price = 199 + (seed % 280)
        if return_date:
            price += 40 + (seed % 35)
        if price > self._ctx_max_price:
            price = max(149, int(self._ctx_max_price * 0.82))
        return FareQuote(
            origin=origin,
            destination=destination,
            departure=departure,
            return_date=return_date,
            price_sar=price,
            currency="SAR",
            book_url=self._book_url(origin, destination, departure, return_date),
            source="demo",
            is_exact=False,
        )

    def _mock_quote(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> FareQuote:
        quote = self._demo_quote(origin, destination, departure, return_date)
        quote.source = "mock"
        return quote

    async def _scrape_saudia(
        self,
        origin: str,
        destination: str,
        departure: date,
        return_date: date | None,
    ) -> int | None:
        if self._scrape_blocked:
            return None
        url = self._book_url(origin, destination, departure, return_date)
        timeout = min(self._settings.quote_timeout, 4.0)
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    return None
                text = resp.text[:500000]
                if "Pardon Our Interruption" in text or "reese" in text.lower():
                    self._scrape_blocked = True
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
    ) -> tuple[int, bool] | None:
        """Published month minimum from flights feed when live scrape is blocked."""
        try:
            feed = await self._load_network()
            month = departure.strftime("%Y-%m")
            route_fares = [
                f
                for f in feed.get("fares", [])
                if f.get("origin") == origin and f.get("destination") == destination
            ]
            if not route_fares:
                return None

            for fare in route_fares:
                if fare.get("month") == month:
                    price = fare.get("price")
                    if isinstance(price, (int, float)):
                        return int(round(price)), True

            def month_index(value: str) -> int:
                y, m = map(int, value.split("-"))
                return y * 12 + m

            target = month_index(month)
            nearest: dict | None = None
            nearest_dist: int | None = None
            for fare in route_fares:
                fare_month = fare.get("month")
                price = fare.get("price")
                if not fare_month or not isinstance(price, (int, float)):
                    continue
                dist = abs(month_index(fare_month) - target)
                if nearest_dist is None or dist < nearest_dist:
                    nearest_dist = dist
                    nearest = fare

            if nearest is not None and nearest_dist is not None and nearest_dist <= 3:
                return int(round(nearest["price"])), False
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

    async def quote_batch(
        self,
        jobs: list[tuple[str, str, date, date | None]],
        *,
        demo_only: bool = False,
    ) -> list[FareQuote | None]:
        sem = asyncio.Semaphore(self._settings.quote_max_concurrent)
        results: list[FareQuote | None] = [None] * len(jobs)

        async def run(idx: int, job: tuple[str, str, date, date | None]) -> None:
            async with sem:
                o, d, dep, ret = job
                results[idx] = await self._quote_one(o, d, dep, ret, demo_only=demo_only)

        await asyncio.gather(*(run(i, job) for i, job in enumerate(jobs)))
        return results
