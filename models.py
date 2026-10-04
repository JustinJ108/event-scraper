from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    title: str
    start: datetime
    venue: Optional[str]
    url: str
    source: str
    price: Optional[str] = None
    price_min: Optional[float] = None
