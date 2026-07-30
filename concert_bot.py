#!/usr/bin/env python3
"""
Concert Alert Bot
=================
Scans European concert listings via the Ticketmaster Discovery API,
scores each show by importance and distance from Vienna, and sends
rich alerts to Telegram with travel options, Spotify links and tickets.

Runs on GitHub Actions. No server needed.

Environment variables required:
    TICKETMASTER_API_KEY
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID

Optional:
    DRY_RUN=1        print to stdout instead of sending to Telegram
    RESET_SEEN=1     ignore seen.json for this run (useful for testing)
"""

import os
import sys
import json
import time
import html
from urllib.parse import quote
from datetime import datetime, timedelta, timezone

import requests

from config import (
    CITIES, TIER_LABEL, WATCHLIST, GENRE_BONUS, GENRE_FILTER, GENRE_BLOCKLIST,
    MAJOR_VENUES, SCORE, HIGH_PRICE_EUR, MID_PRICE_EUR,
    MONTHS_AHEAD, MAX_EVENTS_PER_RUN, MAX_PER_CITY,
    STAY_THRESHOLD_KM, STAY_ADULTS, STAY_NIGHTS,
    PASS_VENUES, ONSALE_ALERTS, ONSALE_REMINDER_DAYS, USE_SONGKICK,
    SHOW_WEEKEND_FLAG, SHOW_CALENDAR_LINK,
)
from travel import TRAVEL, AIRLINES, skyscanner_url, stay_links
import songkick

TM_API = "https://app.ticketmaster.com/discovery/v2/events.json"
SEEN_FILE = "seen.json"
PENDING_FILE = "pending.json"
TELEGRAM_LIMIT = 3800

DRY_RUN = os.getenv("DRY_RUN") == "1"
RESET_SEEN = os.getenv("RESET_SEEN") == "1"

TM_KEY = os.getenv("TICKETMASTER_API_KEY", "").strip()
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "").strip()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def load_seen():
    if RESET_SEEN:
        return set()
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f).get("ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen(seen_ids):
    trimmed = list(seen_ids)[-5000:]
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"updated": datetime.now(timezone.utc).isoformat(), "ids": trimmed},
            f, indent=1,
        )


def load_pending():
    """Events announced but not yet on sale, waiting for their sale date."""
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("events", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_pending(events):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"updated": datetime.now(timezone.utc).isoformat(), "events": events},
            f, indent=1, ensure_ascii=False,
        )


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_city_events(city, start_iso, end_iso):
    events = []
    page = 0
    while page < 3:
        params = {
            "apikey": TM_KEY,
            "city": city["name"],
            "countryCode": city["cc"],
            "classificationName": "music",
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "size": 100,
            "page": page,
            "sort": "date,asc",
        }
        try:
            r = requests.get(TM_API, params=params, timeout=25)
        except requests.RequestException as e:
            print(f"  ! network error for {city['name']}: {e}")
            break

        if r.status_code == 429:
            print("  ! rate limited, sleeping 5s")
            time.sleep(5)
            continue
        if r.status_code != 200:
            print(f"  ! HTTP {r.status_code} for {city['name']}")
            break

        data = r.json()
        events.extend(data.get("_embedded", {}).get("events", []))

        info = data.get("page", {})
        if page + 1 >= info.get("totalPages", 1):
            break
        page += 1
        time.sleep(0.25)

    return events


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def spotify_for(attraction, artist_name):
    """Real Spotify link from Ticketmaster if present, otherwise a search link."""
    if attraction:
        links = attraction.get("externalLinks", {}) or {}
        sp = links.get("spotify") or []
        if sp and sp[0].get("url"):
            return sp[0]["url"]
    return f"https://open.spotify.com/search/{quote(artist_name)}"


def youtube_for(attraction, artist_name):
    if attraction:
        links = attraction.get("externalLinks", {}) or {}
        yt = links.get("youtube") or []
        if yt and yt[0].get("url"):
            return yt[0]["url"]
    return f"https://www.youtube.com/results?search_query={quote(artist_name)}"


def parse_event(ev, city):
    name = ev.get("name", "Unknown")

    dates = ev.get("dates", {}).get("start", {})
    date_str = dates.get("localDate", "")
    time_str = dates.get("localTime", "")

    embedded = ev.get("_embedded", {}) or {}

    venues = embedded.get("venues", []) or []
    venue = venues[0].get("name", "") if venues else ""
    venue_city = ""
    if venues:
        venue_city = (venues[0].get("city") or {}).get("name", "") or ""

    attractions = embedded.get("attractions", []) or []
    attraction = attractions[0] if attractions else None
    artist_name = attraction.get("name") if attraction else name

    support = [a.get("name", "") for a in attractions[1:4] if a.get("name")]

    genre = subgenre = ""
    classifications = ev.get("classifications", []) or []
    if classifications:
        c = classifications[0]
        genre = (c.get("genre") or {}).get("name", "") or ""
        subgenre = (c.get("subGenre") or {}).get("name", "") or ""

    program = (ev.get("info") or "").strip()
    if not program:
        program = (ev.get("pleaseNote") or "").strip()
    program = " ".join(program.split())
    if len(program) > 180:
        program = program[:177].rsplit(" ", 1)[0] + "..."

    min_price = max_price = None
    currency = ""
    for pr in ev.get("priceRanges", []) or []:
        if pr.get("min") is not None:
            if min_price is None or pr["min"] < min_price:
                min_price = pr["min"]
                currency = pr.get("currency", "") or currency
        if pr.get("max") is not None:
            if max_price is None or pr["max"] > max_price:
                max_price = pr["max"]
                currency = pr.get("currency", "") or currency

    # Ticket sale window
    sales = (ev.get("sales") or {}).get("public") or {}
    onsale = sales.get("startDateTime") or None

    return {
        "id": ev.get("id", ""),
        "onsale": onsale,
        "source": "ticketmaster",
        "name": name,
        "artist": artist_name,
        "support": support,
        "date": date_str,
        "time": time_str,
        "venue": venue,
        "venue_city": venue_city or city["name"],
        "genre": genre,
        "subgenre": subgenre,
        "program": program,
        "min_price": min_price,
        "max_price": max_price,
        "currency": currency,
        "url": ev.get("url", ""),
        "spotify": spotify_for(attraction, artist_name),
        "youtube": youtube_for(attraction, artist_name),
        "city": city["name"],
        "city_emoji": city["emoji"],
        "km": city["km"],
        "priority": city["priority"],
    }


# ---------------------------------------------------------------------------
# Filtering and scoring
# ---------------------------------------------------------------------------

def is_blocked(e):
    blob = f"{e['genre']} {e['subgenre']}".lower()
    return any(b in blob for b in GENRE_BLOCKLIST)


def passes_genre_filter(e):
    if not GENRE_FILTER:
        return True
    blob = f"{e['genre']} {e['subgenre']}".lower()
    return any(g.lower() in blob for g in GENRE_FILTER)


def _all_watchlist():
    """Config watchlist plus anything added from Telegram with /watch."""
    extra = []
    try:
        with open("watchlist_extra.json", "r", encoding="utf-8") as f:
            extra = json.load(f).get("artists", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return list(WATCHLIST) + extra


def on_watchlist(e):
    blob = f"{e.get('name','')} {e.get('artist','')}".lower()
    return any(w.lower() in blob for w in _all_watchlist())


def score_event(e):
    s = 0
    reasons = []

    if on_watchlist(e):
        s += SCORE["watchlist"]
        reasons.append("watchlist")

    if e["city"] == "Vienna":
        s += SCORE["vienna_bonus"]

    if any(v in e["venue"].lower() for v in MAJOR_VENUES):
        s += SCORE["major_venue"]
        reasons.append("major venue")

    if e["max_price"] is not None:
        if e["max_price"] >= HIGH_PRICE_EUR:
            s += SCORE["high_price"]
            reasons.append("big show")
        elif e["max_price"] >= MID_PRICE_EUR:
            s += SCORE["mid_price"]

    blob = f"{e['genre']} {e['subgenre']}".lower()
    for g, bonus in GENRE_BONUS.items():
        if g in blob:
            s += bonus
            break

    s -= int(e["km"] / 500) * SCORE["distance_penalty_per_500km"]

    e["score"] = s
    e["reasons"] = reasons
    return s


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def pass_venue_for(e):
    """Return the pass config if this event is at a venue you hold a pass for."""
    blob = f"{e.get('venue','')} {e.get('name','')}".lower()
    for key, cfg in PASS_VENUES.items():
        if key in blob:
            return cfg
    return None


def is_weekend(e):
    try:
        d = datetime.strptime(e["date"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False
    return d.weekday() in (4, 5)   # Friday, Saturday


def onsale_state(e):
    """
    Returns (state, human_text).
    state is one of: 'open', 'soon', 'unknown'
    """
    raw = e.get("onsale")
    if not raw:
        return "unknown", ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return "unknown", ""
    now = datetime.now(timezone.utc)
    if dt <= now:
        return "open", ""
    return "soon", dt.strftime("%a %d %b %Y, %H:%M UTC")


def calendar_link(e):
    """Google Calendar template link, one tap to save the show."""
    try:
        d = datetime.strptime(e["date"], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

    hh, mm = 20, 0
    if e.get("time"):
        try:
            hh, mm = int(e["time"][:2]), int(e["time"][3:5])
        except (ValueError, IndexError):
            pass

    start = d.replace(hour=hh, minute=mm)
    end = start + timedelta(hours=3)
    fmt = "%Y%m%dT%H%M%S"

    where = e.get("venue", "")
    if e.get("venue_city") and e["venue_city"] not in where:
        where = f"{where}, {e['venue_city']}" if where else e["venue_city"]

    details = []
    if e.get("url"):
        details.append(f"Tickets: {e['url']}")
    if e.get("spotify"):
        details.append(f"Listen: {e['spotify']}")

    return (
        "https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote(e['name'])}"
        f"&dates={start.strftime(fmt)}/{end.strftime(fmt)}"
        f"&location={quote(where)}"
        f"&details={quote(chr(10).join(details))}"
    )


def esc(t):
    return html.escape(t or "")


def link(label, url):
    return f'<a href="{html.escape(url, quote=True)}">{esc(label)}</a>'


def fmt_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%a %d %b %Y")
    except ValueError:
        return d


def fmt_price(e):
    if e["min_price"] is None and e["max_price"] is None:
        return ""
    cur = e["currency"] or "EUR"
    lo, hi = e["min_price"], e["max_price"]
    if cur == "EUR":
        if lo is not None and hi is not None and abs(hi - lo) > 1:
            return f"€{int(lo)}-{int(hi)}"
        v = hi if hi is not None else lo
        return f"from €{int(v)}"
    if lo is not None and hi is not None and abs(hi - lo) > 1:
        return f"{int(lo)}-{int(hi)} {cur}"
    v = hi if hi is not None else lo
    return f"from {int(v)} {cur}"


def travel_block(e):
    """Getting-there options for cities outside Vienna."""
    if e["city"] == "Vienna":
        return ""

    t = TRAVEL.get(e["city"])
    if not t or t.get("mode") == "home":
        return ""

    try:
        dep = datetime.strptime(e["date"], "%Y-%m-%d").date()
    except ValueError:
        dep = (datetime.now() + timedelta(days=30)).date()
    ret = dep + timedelta(days=1)

    parts = []

    if t.get("train"):
        label, url = t["train"]
        parts.append(f"🚆 {link(label, url)}")

    if t.get("bus"):
        label, url = t["bus"]
        parts.append(f"🚌 {link(label, url)}")

    if t.get("flight") and t.get("airport"):
        duration, carriers = t["flight"]
        sky = skyscanner_url(t["airport"], dep, ret)
        bits = []
        if sky:
            bits.append(link(f"direct only {duration}", sky))
        for c in carriers[:3]:
            if c in AIRLINES:
                bits.append(link(c, AIRLINES[c]))
        if bits:
            parts.append("✈️ " + " · ".join(bits))

    out = ""
    if parts:
        out += f"   <i>Getting there ({e['km']}km from Vienna)</i>\n"
        for p in parts:
            out += f"   {p}\n"

    # Where to stay, only for cities worth an overnight
    if e["km"] >= STAY_THRESHOLD_KM:
        checkout = dep + timedelta(days=STAY_NIGHTS)
        stays = stay_links(e["city"], dep, checkout, STAY_ADULTS)
        if stays:
            night_word = "night" if STAY_NIGHTS == 1 else "nights"
            out += (
                f"   <i>Stay ({STAY_NIGHTS} {night_word}, {STAY_ADULTS} adults)</i>\n"
            )
            out += "   🏨 " + " · ".join(link(l, u) for l, u in stays) + "\n"

    return out


def format_event(e, onsale_banner=False):
    star = "⭐ " if on_watchlist(e) else ""
    out = f"{star}<b>{esc(e['name'])}</b>\n"

    if onsale_banner:
        out += "   🔔 <b>TICKETS ON SALE NOW</b>\n"

    g = " / ".join([x for x in [e.get("genre"), e.get("subgenre")]
                    if x and x.lower() != "undefined"])
    if g:
        out += f"   <i>{esc(g)}</i>\n"

    if e.get("program"):
        out += f"   {esc(e['program'])}\n"

    if e.get("support"):
        out += f"   with {esc(', '.join(e['support']))}\n"

    if e.get("date_end"):
        d1, d2 = fmt_date(e["date"]), fmt_date(e["date_end"])
        when = [f"{d1} – {d2} ({e.get('nights', 2)} nights)"]
    else:
        when = [fmt_date(e["date"])]
        if e.get("time"):
            when.append(e["time"][:5])
    weekend = " 🎉 <i>weekend</i>" if (SHOW_WEEKEND_FLAG and is_weekend(e)) else ""
    out += f"   📅 {' · '.join(when)}{weekend}\n"

    where = e.get("venue") or ""
    if e.get("venue_city") and e["venue_city"] not in where:
        where = f"{where}, {e['venue_city']}" if where else e["venue_city"]
    if where:
        out += f"   📍 {esc(where)}\n"

    # Tickets, or pass note if you already hold a season pass here
    pv = pass_venue_for(e)
    if pv:
        out += f"   🎟 <i>{esc(pv['label'])}</i> · {link('Program', pv['program_url'])}\n"
    else:
        ticket_line = []
        price = fmt_price(e)
        if price:
            ticket_line.append(f"🎫 {esc(price)}")

        state, when_txt = onsale_state(e)
        if state == "soon" and not onsale_banner:
            ticket_line.append(f"🔔 on sale {esc(when_txt)}")
        elif e.get("url"):
            ticket_line.append(link("Buy tickets", e["url"]))

        if ticket_line:
            out += "   " + " · ".join(ticket_line) + "\n"

    extras = [link("Spotify", e["spotify"])]
    if e.get("youtube"):
        extras.append(link("YouTube", e["youtube"]))
    if SHOW_CALENDAR_LINK:
        cal = calendar_link(e)
        if cal:
            extras.append(link("Add to calendar", cal))
    out += "   🎧 " + " · ".join(extras) + "\n"

    out += travel_block(e)

    return out


def collapse_runs(events):
    """
    Merge multi-night runs: same artist, same venue, same city, on consecutive
    dates become one card with a date range. Keeps the earliest event as the
    base and records the last night in date_end.
    """
    def key(e):
        return (
            (e.get("artist") or e.get("name") or "").lower().strip(),
            (e.get("venue") or "").lower().strip(),
            e.get("city", ""),
        )

    groups = {}
    for e in events:
        groups.setdefault(key(e), []).append(e)

    out = []
    for _, evs in groups.items():
        evs.sort(key=lambda x: x.get("date", ""))
        run = [evs[0]]
        for e in evs[1:]:
            try:
                prev = datetime.strptime(run[-1]["date"], "%Y-%m-%d").date()
                cur = datetime.strptime(e["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                out.extend(_finish_run(run))
                run = [e]
                continue
            if (cur - prev).days == 1:
                run.append(e)
            else:
                out.extend(_finish_run(run))
                run = [e]
        out.extend(_finish_run(run))
    return out


def _finish_run(run):
    if len(run) == 1:
        return run
    base = dict(run[0])
    base["date_end"] = run[-1]["date"]
    base["nights"] = len(run)
    # widest price range across the nights
    lows = [e["min_price"] for e in run if e.get("min_price") is not None]
    highs = [e["max_price"] for e in run if e.get("max_price") is not None]
    if lows:
        base["min_price"] = min(lows)
    if highs:
        base["max_price"] = max(highs)
    return [base]


def build_messages(events, header_text=None, onsale_banner=False):
    events = collapse_runs(events)
    by_city = {}
    for e in events:
        by_city.setdefault(e["city"], []).append(e)

    order = sorted(
        by_city.keys(),
        key=lambda c: next(
            (ci["priority"] * 10000 + ci["km"] for ci in CITIES if ci["name"] == c), 99999
        ),
    )

    header = header_text or f"🎸 <b>Concert Radar</b> · {len(events)} new\n\n"
    chunks = []
    current = header

    for city_name in order:
        city = next((c for c in CITIES if c["name"] == city_name), None)
        emoji = city["emoji"] if city else "•"
        tier = TIER_LABEL.get(city["priority"], "") if city else ""
        km = city["km"] if city else 0

        head = f"{emoji} <b>{esc(city_name.upper())}</b>"
        if km > 0:
            head += f" <i>({km}km · {tier})</i>"
        head += "\n\n"

        if len(current) + len(head) > TELEGRAM_LIMIT:
            chunks.append(current.rstrip())
            current = ""
        current += head

        for e in sorted(by_city[city_name], key=lambda x: x["date"]):
            block = format_event(e, onsale_banner=onsale_banner) + "\n"
            if len(current) + len(block) > TELEGRAM_LIMIT:
                chunks.append(current.rstrip())
                current = f"{emoji} <b>{esc(city_name.upper())}</b> <i>(cont.)</i>\n\n"
            current += block

    if current.strip() and current != header:
        chunks.append(current.rstrip())

    return chunks


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(text):
    if DRY_RUN:
        print("\n" + "=" * 64)
        print(text)
        print("=" * 64 + "\n")
        return True

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=20)
        if r.status_code != 200:
            print(f"  ! telegram error {r.status_code}: {r.text[:300]}")
            return False
        return True
    except requests.RequestException as e:
        print(f"  ! telegram network error: {e}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not TM_KEY:
        print("Missing TICKETMASTER_API_KEY")
        sys.exit(1)
    if not DRY_RUN and (not TG_TOKEN or not TG_CHAT):
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        sys.exit(1)

    now = datetime.now(timezone.utc)
    start_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = (now + timedelta(days=MONTHS_AHEAD * 31)).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Scanning {len(CITIES)} cities from {start_iso[:10]} to {end_iso[:10]}")

    seen = load_seen()
    pending = load_pending() if ONSALE_ALERTS else []
    print(f"Already seen: {len(seen)} events | pending on-sale: {len(pending)}")

    # ---------------------------------------------------------------
    # Step 1: anything in the pending queue whose sale opens now
    # ---------------------------------------------------------------
    going_on_sale, still_pending = [], []
    if ONSALE_ALERTS:
        now_utc = datetime.now(timezone.utc)
        threshold = now_utc + timedelta(days=ONSALE_REMINDER_DAYS)
        for e in pending:
            state, _ = onsale_state(e)
            try:
                dt = datetime.fromisoformat(
                    (e.get("onsale") or "").replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue
            # drop anything whose concert date has passed
            if e.get("date", "") < now_utc.strftime("%Y-%m-%d"):
                continue
            if dt <= threshold:
                going_on_sale.append(e)
            else:
                still_pending.append(e)

    if going_on_sale:
        print(f"{len(going_on_sale)} events going on sale")
        going_on_sale.sort(key=lambda e: (e["priority"], e["km"], e["date"]))
        header = f"🔔 <b>On sale now</b> · {len(going_on_sale)} shows\n\n"
        for chunk in build_messages(going_on_sale, header_text=header,
                                    onsale_banner=True):
            if not send_telegram(chunk):
                print("  ! on-sale send failed, keeping queue for retry")
                return
            time.sleep(0.5)

    # ---------------------------------------------------------------
    # Step 2: scan for new events
    # ---------------------------------------------------------------
    fresh = []
    new_pending = []

    for city in sorted(CITIES, key=lambda c: (c["priority"], c["km"])):
        raw = fetch_city_events(city, start_iso, end_iso)
        parsed = [parse_event(ev, city) for ev in raw]
        tm_count = len(parsed)

        if USE_SONGKICK:
            try:
                # Vienna deepest, near cities deep, far cities one page since
                # only major shows clear their score threshold anyway.
                if city["name"] == "Vienna":
                    pages = 6
                elif city["priority"] <= 1:
                    pages = 3
                else:
                    pages = 1
                sk_raw = songkick.fetch_city_events(city["name"], max_pages=pages)
                for r in sk_raw:
                    n = songkick.normalise(r, city)
                    if n:
                        parsed.append(n)
                if sk_raw:
                    print(f"  {city['name']}: {tm_count} TM + {len(sk_raw)} Songkick")
                else:
                    print(f"  {city['name']}: {tm_count} TM")
            except Exception as ex:
                print(f"  {city['name']}: {tm_count} TM (songkick failed: {ex})")
        else:
            print(f"  {city['name']}: {tm_count} TM")

        city_new = []
        for e in parsed:
            if not e["id"] or e["id"] in seen:
                continue
            if is_blocked(e) or not passes_genre_filter(e):
                continue
            score_event(e)
            if e["score"] < city["min_score"]:
                continue
            city_new.append(e)

        city_new.sort(key=lambda x: -x["score"])
        keep = city_new[:MAX_PER_CITY]

        for e in keep:
            seen.add(e["id"])
            state, _ = onsale_state(e)
            if ONSALE_ALERTS and state == "soon":
                # hold it, we will ping again when the sale opens
                new_pending.append(e)
            fresh.append(e)

        if keep:
            print(f"    -> {len(keep)} worth sending")

    if ONSALE_ALERTS:
        save_pending(still_pending + new_pending)

    if not fresh:
        print("No new events worth sending.")
        save_seen(seen)
        return

    fresh.sort(key=lambda e: (e["priority"], e["km"], e["date"]))
    fresh = fresh[:MAX_EVENTS_PER_RUN]

    print(f"\nSending {len(fresh)} events")
    for chunk in build_messages(fresh):
        if not send_telegram(chunk):
            print("  ! send failed, state not saved so it retries next run")
            return
        time.sleep(0.5)

    save_seen(seen)
    print("Done.")


if __name__ == "__main__":
    main()
