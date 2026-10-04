import json
import re
from datetime import datetime

import requests

from models import Event

HEADERS = {"User-Agent": "Mozilla/5.0 (event-scraper)"}


def _parse_ticket_info(ticket_info: dict | None) -> tuple[float | None, str | None]:
    if not ticket_info:
        return None, None
    if ticket_info.get("is_free"):
        return 0.0, "Free"

    price = ticket_info.get("price")
    if not price or price.get("cents") is None:
        return None, None

    cents = price.get("min_cents") or price.get("cents")
    amount = cents / 100
    label = f"${amount:,.0f}" if amount == int(amount) else f"${amount:,.2f}"
    if price.get("is_flexible") or (price.get("min_cents") and price["min_cents"] != price.get("cents")):
        label += "+"
    return amount, label


def fetch(city_slug: str = "sf") -> list[Event]:
    resp = requests.get(f"https://luma.com/{city_slug}", headers=HEADERS, timeout=15)
    resp.raise_for_status()

    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL
    )
    if not match:
        return []

    data = json.loads(match.group(1))
    entries = data["props"]["pageProps"]["initialData"]["data"].get("events", [])

    events = []
    for entry in entries:
        ev = entry.get("event", {})
        name = ev.get("name")
        start_at = ev.get("start_at")
        slug = ev.get("url")
        if not (name and start_at and slug):
            continue

        address_info = ev.get("geo_address_info") or {}
        venue = address_info.get("short_address") or address_info.get("city_state")
        price_min, price_label = _parse_ticket_info(entry.get("ticket_info"))

        events.append(
            Event(
                title=name,
                start=datetime.fromisoformat(start_at.replace("Z", "+00:00")),
                venue=venue,
                url=f"https://lu.ma/{slug}",
                source="Luma",
                price=price_label,
                price_min=price_min,
            )
        )
    return events
