# event-scraper

Scrapes Bay Area events from [Luma](https://lu.ma), [SF Funcheap](https://sf.funcheap.com), and [Do The Bay](https://dothebay.com), and renders them into a single static HTML page with client-side price and date-range filters.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage

```bash
.venv/bin/python main.py
```

Generates `events.html` in the project root — open it in a browser.

## Known limitations

- Luma's `/sf` discover feed is a randomly-curated sample capped at roughly the next week, not an exhaustive chronological list — events further out (e.g. 2+ weeks away) may not appear even though they exist. Pulling directly from a specific `lu.ma/<calendar-slug>` calendar page avoids this.
- Do The Bay does not expose ticket price in its page data, so those events always show as "price?" (unlisted price) and are included unless the "Include unlisted price" filter is unchecked.
- SF Funcheap's homepage listing only covers the next few days, not multiple weeks.

## Structure

- `scrapers/` — one module per source, each exposing a `fetch()` returning `list[Event]`
- `models.py` — the shared `Event` dataclass
- `render.py` — builds the static HTML page (inline CSS/JS, client-side filtering)
- `main.py` — runs all scrapers, merges + sorts results, writes `events.html`
