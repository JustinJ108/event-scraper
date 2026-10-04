from html import escape
from itertools import groupby

from models import Event

SOURCE_COLORS = {
    "Luma": "#6c5ce7",
    "SF Funcheap": "#00b894",
    "Do The Bay": "#e17055",
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bay Area Events</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #f5f5f7;
    color: #1d1d1f;
    margin: 0;
    padding: 24px;
  }}
  h1 {{
    font-size: 22px;
    margin: 0 0 4px;
  }}
  .subtitle {{
    color: #6e6e73;
    font-size: 13px;
    margin-bottom: 20px;
  }}
  .controls {{
    background: white;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    align-items: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
  }}
  .control-group {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }}
  .control-group label {{
    color: #6e6e73;
  }}
  .btn-group button {{
    border: 1px solid #d2d2d7;
    background: white;
    color: #1d1d1f;
    padding: 5px 10px;
    font-size: 12px;
    cursor: pointer;
    border-radius: 6px;
    margin-right: 4px;
  }}
  .btn-group button.active {{
    background: #1d1d1f;
    color: white;
    border-color: #1d1d1f;
  }}
  #maxPrice {{
    width: 70px;
    padding: 4px 6px;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    font-size: 13px;
  }}
  .day-heading {{
    font-size: 15px;
    font-weight: 600;
    margin: 28px 0 10px;
    color: #1d1d1f;
  }}
  .card {{
    background: white;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    display: flex;
    align-items: baseline;
    gap: 14px;
  }}
  .card a {{
    color: #1d1d1f;
    text-decoration: none;
    font-weight: 500;
  }}
  .card a:hover {{
    text-decoration: underline;
  }}
  .time {{
    width: 70px;
    flex-shrink: 0;
    color: #6e6e73;
    font-size: 13px;
  }}
  .details {{
    flex: 1;
  }}
  .venue {{
    color: #6e6e73;
    font-size: 13px;
  }}
  .tag {{
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
    color: white;
    flex-shrink: 0;
  }}
  .price {{
    font-size: 12px;
    color: #6e6e73;
    flex-shrink: 0;
    width: 50px;
    text-align: right;
  }}
  #emptyState {{
    color: #6e6e73;
    font-size: 14px;
    padding: 40px 0;
    text-align: center;
  }}
  [hidden] {{
    display: none !important;
  }}
</style>
</head>
<body data-generated-at="{generated_at_epoch}">
<h1>Bay Area Events</h1>
<div class="subtitle">Showing <strong id="resultCount">{count}</strong> of {count} upcoming events &middot; generated {generated_at_label}</div>

<div class="controls">
  <div class="control-group">
    <label>Max price</label>
    <div class="btn-group" id="priceButtons">
      <button data-price="0">Free</button>
      <button data-price="20" class="active">$20</button>
      <button data-price="50">$50</button>
      <button data-price="">Any</button>
    </div>
    <input type="number" id="maxPrice" placeholder="custom $" min="0" value="20">
  </div>
  <div class="control-group">
    <label><input type="checkbox" id="includeUnknown" checked> Include unlisted price</label>
  </div>
  <div class="control-group">
    <label>When</label>
    <div class="btn-group" id="dateButtons">
      <button data-days="7">7 days</button>
      <button data-days="14" class="active">14 days</button>
      <button data-days="30">30 days</button>
      <button data-days="">All</button>
    </div>
  </div>
  <button id="applyBtn" style="padding:6px 14px;border-radius:6px;border:1px solid #1d1d1f;background:#1d1d1f;color:white;font-size:13px;cursor:pointer;">Apply Filters</button>
</div>

{body}
<div id="emptyState" hidden>No events match your filters.</div>

<script>
console.log('[events page] script tag reached');
(function () {{
  console.log('[events page] script running, found', document.querySelectorAll('.card').length, 'cards');
  const generatedAt = parseInt(document.body.dataset.generatedAt, 10);
  const maxPriceInput = document.getElementById('maxPrice');
  const includeUnknown = document.getElementById('includeUnknown');
  const priceButtons = document.querySelectorAll('#priceButtons button');
  const dateButtons = document.querySelectorAll('#dateButtons button');
  const emptyState = document.getElementById('emptyState');
  const applyBtn = document.getElementById('applyBtn');
  const resultCount = document.getElementById('resultCount');

  let activeDays = 14;

  function setActive(buttons, target) {{
    buttons.forEach(b => b.classList.toggle('active', b === target));
  }}

  priceButtons.forEach(btn => btn.addEventListener('click', () => {{
    maxPriceInput.value = btn.dataset.price;
    setActive(priceButtons, btn);
    applyFilters();
  }}));

  maxPriceInput.addEventListener('input', () => {{
    setActive(priceButtons, null);
    applyFilters();
  }});

  dateButtons.forEach(btn => btn.addEventListener('click', () => {{
    activeDays = btn.dataset.days ? parseInt(btn.dataset.days, 10) : null;
    setActive(dateButtons, btn);
    applyFilters();
  }}));

  includeUnknown.addEventListener('change', applyFilters);
  applyBtn.addEventListener('click', applyFilters);

  function applyFilters() {{
   try {{
    const rawMax = maxPriceInput.value;
    const maxPrice = rawMax === '' ? null : parseFloat(rawMax);
    const cutoff = activeDays === null ? null : generatedAt + activeDays * 86400000;
    let anyVisible = false;
    let shownCount = 0;
    let totalCount = 0;

    console.log('[applyFilters] running. maxPrice=', maxPrice, 'activeDays=', activeDays, 'includeUnknown=', includeUnknown.checked);

    document.querySelectorAll('.day').forEach(day => {{
      let dayHasVisible = false;
      day.querySelectorAll('.card').forEach(card => {{
        totalCount++;
        const start = parseInt(card.dataset.start, 10);
        const priceAttr = card.dataset.price;
        const price = priceAttr === '' ? null : parseFloat(priceAttr);

        let visible = true;
        if (cutoff !== null && start > cutoff) visible = false;
        if (visible && maxPrice !== null) {{
          visible = price === null ? includeUnknown.checked : price <= maxPrice;
        }}

        card.hidden = !visible;
        if (visible) {{
          dayHasVisible = true;
          shownCount++;
        }}
      }});
      day.hidden = !dayHasVisible;
      if (dayHasVisible) anyVisible = true;
    }});

    emptyState.hidden = anyVisible;
    resultCount.textContent = shownCount;
    console.log('[applyFilters] done. showing', shownCount, 'of', totalCount, 'events');
   }} catch (err) {{
    console.error('[applyFilters] ERROR', err);
   }}
  }}

  applyFilters();
}})();
</script>
</body>
</html>
"""


def render_html(events: list[Event], generated_at_label: str, generated_at_epoch: int) -> str:
    body_parts = []
    for day, day_events in groupby(events, key=lambda e: e.start.astimezone().strftime("%A, %B %d")):
        day_events = list(day_events)
        cards = []
        for e in day_events:
            local_time = e.start.astimezone().strftime("%I:%M %p").lstrip("0")
            venue = f'<div class="venue">{escape(e.venue)}</div>' if e.venue else ""
            price_display = (
                f'<div class="price">{escape(e.price)}</div>' if e.price
                else '<div class="price" style="opacity:0.5">price?</div>'
            )
            color = SOURCE_COLORS.get(e.source, "#636e72")
            price_attr = "" if e.price_min is None else e.price_min
            start_epoch = int(e.start.timestamp() * 1000)

            cards.append(
                f'''<div class="card" data-price="{price_attr}" data-start="{start_epoch}">
  <div class="time">{local_time}</div>
  <div class="details">
    <a href="{escape(e.url)}" target="_blank" rel="noopener">{escape(e.title)}</a>
    {venue}
  </div>
  {price_display}
  <span class="tag" style="background:{color}">{escape(e.source)}</span>
</div>'''
            )

        body_parts.append(
            f'<section class="day"><div class="day-heading">{escape(day)}</div>{"".join(cards)}</section>'
        )

    return PAGE_TEMPLATE.format(
        count=len(events),
        generated_at_label=generated_at_label,
        generated_at_epoch=generated_at_epoch,
        body="\n".join(body_parts),
    )
