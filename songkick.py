"""
Songkick as a second source.

Ticketmaster has thin coverage in Slovakia, Hungary, Slovenia and Croatia, and
misses most club-sized shows. Songkick's public metro pages embed JSON-LD
structured data for every listing, which is far more stable to read than HTML.

This module returns events in the same shape the main script expects.
"""

import re
import json
import time
from datetime import datetime
from urllib.parse import quote

import requests

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Metro area IDs. Add more by searching songkick.com and copying the number
# out of the /metro-areas/<id>-<slug> URL.
SONGKICK_METROS = {
    "Vienna":     "26771-austria-vienna",
    "Bratislava": "32262-slovakia-bratislava",
    "Budapest":   "29047-hungary-budapest",
    "Graz":       "26766-austria-graz",
    "Salzburg":   "26770-austria-salzburg",
    "Prague":     "28425-czech-republic-prague",
    "Ljubljana":  "32259-slovenia-ljubljana",
    "Zagreb":     "29037-croatia-zagreb",
}

JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S
)


def _iter_music_events(html_text):
    for block in JSONLD_RE.findall(html_text):
        try:
            data = json.loads(block)
        except (json.JSONDecodeError, ValueError):
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and "MusicEvent" in str(it.get("@type", "")):
                yield it


def _performer_name(ev):
    perf = ev.get("performer")
    if isinstance(perf, list) and perf:
        return perf[0].get("name", "") or ""
    if isinstance(perf, dict):
        return perf.get("name", "") or ""
    return ""


def fetch_city_events(city_name, months_ahead=12, max_pages=3):
    """
    Return a list of raw dicts for one city, or [] if the city is not mapped
    or the fetch fails. Never raises.
    """
    slug = SONGKICK_METROS.get(city_name)
    if not slug:
        return []

    out = []
    seen_urls = set()

    for page in range(1, max_pages + 1):
        url = f"https://www.songkick.com/metro-areas/{slug}"
        params = {"page": page} if page > 1 else {}
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=25)
        except requests.RequestException:
            break

        if r.status_code != 200:
            break

        found_this_page = 0
        for ev in _iter_music_events(r.text):
            ev_url = ev.get("url", "")
            if ev_url in seen_urls:
                continue
            seen_urls.add(ev_url)
            out.append(ev)
            found_this_page += 1

        if found_this_page == 0:
            break
        time.sleep(0.4)

    return out


def normalise(ev, city):
    """
    Convert a Songkick JSON-LD event into the flat dict the main script uses.
    Returns None if the record is unusable.
    """
    start = ev.get("startDate", "") or ""
    if not start:
        return None

    date_str = start[:10]
    time_str = ""
    if "T" in start and len(start) >= 16:
        time_str = start[11:16]

    loc = ev.get("location") or {}
    venue = loc.get("name", "") or ""
    addr = loc.get("address") or {}
    venue_city = addr.get("addressLocality", "") or city["name"]

    artist = _performer_name(ev) or ev.get("name", "") or "Unknown"
    name = ev.get("name") or artist

    ev_url = ev.get("url", "") or ""
    # Songkick event URLs are stable, use them as the dedupe id
    ev_id = "sk_" + (ev_url.rsplit("/", 1)[-1] if ev_url else f"{artist}_{date_str}")

    offers = ev.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price")
    try:
        price = float(price) if price not in (None, "") else None
    except (TypeError, ValueError):
        price = None

    return {
        "id": ev_id,
        "name": name,
        "artist": artist,
        "support": [],
        "date": date_str,
        "time": time_str,
        "venue": venue,
        "venue_city": venue_city,
        "genre": "",
        "subgenre": "",
        "program": "",
        "min_price": price,
        "max_price": price,
        "currency": offers.get("priceCurrency", "") or "",
        "url": ev_url,
        "onsale": None,
        "source": "songkick",
        "spotify": f"https://open.spotify.com/search/{quote(artist)}",
        "youtube": f"https://www.youtube.com/results?search_query={quote(artist)}",
        "city": city["name"],
        "city_emoji": city["emoji"],
        "km": city["km"],
        "priority": city["priority"],
    }


def within_window(e, months_ahead):
    try:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False
    today = datetime.now().date()
    horizon = today.replace(year=today.year + (months_ahead // 12)) if months_ahead >= 12 else today
    if months_ahead >= 12:
        return today <= d <= horizon
    return d >= today
