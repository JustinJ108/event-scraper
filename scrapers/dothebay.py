from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Event

HEADERS = {"User-Agent": "Mozilla/5.0 (event-scraper)"}
BASE_URL = "https://dothebay.com"


def fetch() -> list[Event]:
    resp = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for card in soup.select('[itemtype="http://schema.org/Event"]'):
        title_el = card.select_one('[itemprop="name"]')
        date_el = card.select_one('[itemprop="startDate"]')
        link_el = card.select_one('a[itemprop="url"]')
        venue_el = card.select_one(".ds-venue-name [itemprop='name']")

        if not (title_el and date_el and link_el):
            continue

        date_str = date_el.get("content") or date_el.get("datetime")
        try:
            start = datetime.strptime(date_str, "%Y-%m-%dT%H:%M%z")
        except (ValueError, TypeError):
            continue

        events.append(
            Event(
                title=title_el.get_text(strip=True),
                start=start,
                venue=venue_el.get_text(strip=True) if venue_el else None,
                url=urljoin(BASE_URL, link_el["href"]),
                source="Do The Bay",
            )
        )
    return events
