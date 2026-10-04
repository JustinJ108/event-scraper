import time
from datetime import date, datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import Event

HEADERS = {"User-Agent": "Mozilla/5.0 (event-scraper)"}
BASE_URL = "https://dothebay.com"


def fetch(days: int = 14) -> list[Event]:
    """Fetch one page per day, since the homepage only covers today."""
    events = []
    for i in range(days):
        day = date.today() + timedelta(days=i)
        url = f"{BASE_URL}/events/{day:%Y/%m/%d}"
        try:
            events.extend(_fetch_page(url))
        except requests.RequestException as e:
            print(f"  [Do The Bay] {day} failed: {e}")
        time.sleep(1)  # be polite to the site
    return events


def _fetch_page(url: str) -> list[Event]:
    resp = requests.get(url, headers=HEADERS, timeout=15)
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
            start = datetime.fromisoformat(date_str)
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
