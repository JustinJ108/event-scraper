import re
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from models import Event

HEADERS = {"User-Agent": "Mozilla/5.0 (event-scraper)"}
PACIFIC = ZoneInfo("America/Los_Angeles")
PRICE_RE = re.compile(r"\$([\d,]+(?:\.\d+)?)")


def _parse_price(text: str | None) -> tuple[float | None, str | None]:
    if not text:
        return None, None
    if text.upper().startswith("FREE"):
        return 0.0, text
    match = PRICE_RE.search(text)
    if match:
        return float(match.group(1).replace(",", "")), text
    return None, text


def fetch(subdomain: str = "sf", days: int = 14) -> list[Event]:
    """Fetch one page per day, since the homepage only covers a few days."""
    events = []
    for i in range(days):
        day = date.today() + timedelta(days=i)
        url = f"https://{subdomain}.funcheap.com/{day:%Y/%m/%d}/"
        try:
            events.extend(_fetch_page(url))
        except requests.RequestException as e:
            print(f"  [SF Funcheap] {day} failed: {e}")
        time.sleep(1)  # be polite to the site
    return events


def _fetch_page(url: str) -> list[Event]:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for span in soup.select("span[data-event-date]"):
        link = span.find("a")
        if not link:
            continue

        date_str = span["data-event-date"]
        try:
            start = datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=PACIFIC)
        except ValueError:
            continue

        row = span.find_parent("tr")
        price_text = None
        if row:
            cells = row.find_all("td")
            if cells:
                price_text = cells[-1].get_text(strip=True) or None
        price_min, price_label = _parse_price(price_text)

        events.append(
            Event(
                title=link.get_text(strip=True),
                start=start,
                venue=None,
                url=link["href"],
                source="SF Funcheap",
                price=price_label,
                price_min=price_min,
            )
        )
    return events
