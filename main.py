from datetime import datetime, timezone
from pathlib import Path

from render import render_html
from scrapers import dothebay, funcheap, luma

OUTPUT_FILE = Path(__file__).parent / "events.html"


def collect() -> list:
    events = []
    for fetcher, label in [(luma.fetch, "Luma"), (funcheap.fetch, "SF Funcheap"), (dothebay.fetch, "Do The Bay")]:
        try:
            found = fetcher()
            print(f"[{label}] fetched {len(found)} events")
            events.extend(found)
        except Exception as e:
            print(f"[{label}] failed: {e}")
    return events


def main():
    events = collect()
    now = datetime.now(timezone.utc)
    events = [e for e in events if e.start >= now]
    events.sort(key=lambda e: e.start)

    print(f"\n{len(events)} upcoming events")

    now_local = datetime.now().astimezone()
    generated_at_label = now_local.strftime("%a %b %d, %I:%M %p")
    generated_at_epoch = int(now_local.timestamp() * 1000)
    html = render_html(events, generated_at_label, generated_at_epoch)
    OUTPUT_FILE.write_text(html)
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
