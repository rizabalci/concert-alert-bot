# 🎸 Concert Alert Bot

Daily Telegram alerts for important concerts across Europe, with Vienna as the priority. Scans a full year ahead, scores each show by how much it deserves your attention, and only messages you about things you have not already seen.

Runs entirely on GitHub Actions. No server, no hosting cost, no Anthropic API calls.

## What a message looks like

```
🎸 Concert Radar · 3 new

🏠 VIENNA

Wolf Alice
   Rock / Alternative Rock
   British alternative rock band touring their new album.
   📅 Sun 19 Jul 2026 · 19:30
   📍 Arena Wien Open Air, Vienna
   🎫 €55-120 · Buy tickets
   🎧 Spotify · YouTube

🚆 BRATISLAVA (65km · Day trip)

⭐ Sting
   Rock / Pop
   STING 3.0 European Tour, stripped-back three-piece format.
   with Dominic Miller
   📅 Sat 20 Jun 2026 · 20:00
   📍 Tipos Arena, Bratislava
   🎫 €65-150 · Buy tickets
   🎧 Spotify · YouTube
   Getting there (65km from Vienna)
   🚆 ÖBB ~1h
   🚌 FlixBus / RegioJet ~1h15

✈️ BERLIN (680km · Weekend)

⭐ Bonobo
   Electronic / Downtempo
   📅 Sat 12 Sep 2026 · 21:00
   📍 Columbiahalle, Berlin
   🎫 €45-70 · Buy tickets
   🎧 Spotify · YouTube
   Getting there (680km from Vienna)
   🚆 ÖBB Nightjet ~11h
   🚌 FlixBus ~9h
   ✈️ direct only ~1h20 · Austrian · Ryanair · easyJet
   Stay (1 night, 2 adults)
   🏨 Booking · Airbnb · Hostelworld
```

Every element is a tappable link. Vienna shows no travel section because you are already there.

## How it works

1. GitHub Actions wakes up once a day
2. The script queries the Ticketmaster Discovery API for music events in 26 European cities, 12 months ahead
3. Each event gets a score based on venue size, ticket price, genre, watchlist match and distance from Vienna
4. Cities further away need a higher score to qualify, so Vienna sends you everything and Lisbon only sends you something huge
5. New events are grouped by city (Vienna first) and sent to Telegram with program, date, venue, price, ticket link, Spotify sample and travel options
6. Anything not yet on sale goes into a queue and gets a second alert the day tickets open
7. Event IDs are saved to `seen.json` and committed back, so you never get the same show twice

## Asking the bot on demand

The daily digest tells you what is new. But when you want to know what is on right now, message the bot directly.

```
/vienna          what is on in Vienna
/near            Vienna plus day trip cities
/all             everything within your distance settings
/week            next 7 days
/month           next 30 days

/jazz  /rock  /electronic  /classical
/metal /folk  /world  /pop  /latin

/watch Nils Frahm     always alert me, anywhere in Europe
/unwatch Nils Frahm
/list                 show the watchlist

/scan            run the normal new-events scan
/help            command list
```

Search commands ignore the seen list, so asking `/vienna` always gives you an answer rather than silence just because those events were reported last week.

`/watch` writes to `watchlist_extra.json` and gets committed back, so additions survive between runs. You can build the watchlist from your phone as artists occur to you.

### Response time

The listener polls Telegram on a 15 minute cron, and GitHub often delays scheduled jobs by a few minutes under load. So expect an answer within about 20 minutes, not instantly.

If you want instant, fire the workflow directly. Create a fine-grained personal access token with **Actions: read and write** on this repo, then:

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.github.com/repos/rizabalci/concert-alert-bot/dispatches \
  -d '{"event_type":"telegram_command"}'
```

Wrap that in an iOS Shortcut with a home screen icon and the flow becomes: type `/vienna` in Telegram, tap the shortcut, answer arrives in under a minute.

The GitHub mobile app also works. Actions tab, pick the workflow, Run workflow.

### A note on Actions minutes

Polling every 15 minutes is about 96 runs a day. Public repos get unlimited Actions minutes so this is free. On a private repo you would blow through the 2000 minute monthly allowance, so either keep the repo public, or change the cron to `'*/30 * * * *'` and lean on the instant trigger when you actually want something.

## On-sale alerts

Knowing about a show six months early is useless if you forget by the time tickets drop. When the bot finds an event that has not gone on sale yet, it shows the sale date instead of a buy link and quietly parks it in `pending.json`. The day the sale opens you get a second message:

```
🔔 On sale now · 1 shows

🏠 VIENNA

Massive Attack
   🔔 TICKETS ON SALE NOW
   Electronic / Trip Hop
   📅 Fri 20 Nov 2026 · 20:00 🎉 weekend
   📍 Wiener Stadthalle, Vienna
   🎫 €60-110 · Buy tickets
   🎧 Spotify · YouTube · Add to calendar
```

Adjust the lead time in `config.py`:

```python
ONSALE_ALERTS = True
ONSALE_REMINDER_DAYS = 1   # ping this many days before the sale opens
```

## Season pass venues

You hold a Musikverein yearly pass, so the bot never shows ticket links for Musikverein events. It links the program page instead:

```
Wiener Philharmoniker
   Classical
   📅 Sat 14 Nov 2026 · 19:30 🎉 weekend
   📍 Musikverein Grosser Saal, Vienna
   🎟 You have the yearly pass · Program
   🎧 Spotify · YouTube · Add to calendar
```

Add more in `config.py` if you pick up another subscription:

```python
PASS_VENUES = {
    "musikverein": {
        "label": "You have the yearly pass",
        "program_url": "https://www.musikverein.at/programm",
    },
}
```

## Two data sources

Ticketmaster is the primary source and is strong for arenas and Western Europe. Songkick fills the gap, and it is the one that finds club shows at Pink Whale, Majestic Music Club, Metropol, Akvárium and Budapest Park that Ticketmaster never lists.

Songkick is read from the public metro pages via their embedded structured data, so no API key is needed. If a page layout ever changes the scan fails quietly and Ticketmaster results still come through. Turn it off with `USE_SONGKICK = False`.

All 26 cities have a Songkick metro mapped, so every city has at least one working source. This matters most for Lisbon, which Ticketmaster does not cover at all, and for Slovakia, Hungary, Slovenia and Croatia. Near cities are scanned three Songkick pages deep, far cities one page, since only major shows clear the distant score thresholds anyway.

Metro IDs live in `songkick.py`. To add a city, search songkick.com and copy the number from the `/metro-areas/<id>-<slug>` URL.

## Multi-night runs

When an artist plays the same venue on consecutive nights, the alerts collapse them into one card with a date range instead of repeating near-identical entries:

```
⭐ Ólafur Arnalds
   New Age / Neo-Classical
   📅 Mon 12 Oct 2026 – Tue 13 Oct 2026 (2 nights)
   📍 Cirque Royal, Brussels
   🎫 €45-95 · Buy tickets
```

The price range spans all nights. Shows by the same artist with a gap between dates stay as separate cards, since those are genuinely different decisions.

## Weekend flags and calendar

Friday and Saturday shows get a 🎉 weekend tag so you can see at a glance which ones need no time off. Every event carries an "Add to calendar" link that opens Google Calendar prefilled with the venue, time and ticket link.

```python
SHOW_WEEKEND_FLAG = True
SHOW_CALENDAR_LINK = True
```

## Travel links

For any city outside Vienna the alert includes how to get there, with the concert date already filled in where the site supports it.

| Mode | Source | Notes |
|---|---|---|
| 🚆 Train | ÖBB, ČD, MÁV, DB | Default for everything within about 400km |
| 🚌 Bus | FlixBus, RegioJet | Usually the cheapest option |
| ✈️ Flight | Skyscanner + airline sites | Skyscanner links carry `preferdirects=true` so only non-stop flights show, and the airline names link to their own booking pages so you can book direct rather than through a reseller |
| 🏨 Stay | Booking, Airbnb, Hostelworld | Searches pre-filled with the concert date, checkout the next morning |

Flight durations are shown so you know what you are committing to before clicking.

Accommodation links only appear for cities at least 150km away, since anything closer you would just travel home the same night. Adjust in `config.py`:

```python
STAY_THRESHOLD_KM = 150    # show hotels from this distance up
STAY_ADULTS = 2
STAY_NIGHTS = 1            # bump to 2 to make it a proper weekend
```

## Setup

### 1. Get a Ticketmaster API key (free)

Go to [developer.ticketmaster.com](https://developer.ticketmaster.com/), create an account, and register an app. You get a Consumer Key immediately. The free tier allows 5000 calls per day which is far more than this bot uses (about 30 per run).

### 2. Create a Telegram bot

In Telegram, message [@BotFather](https://t.me/BotFather):

```
/newbot
```

Follow the prompts and copy the token it gives you.

Then get your chat ID. Message [@userinfobot](https://t.me/userinfobot) and it replies with your ID. Also send at least one message to your new bot so it is allowed to message you.

### 3. Create the repo

```bash
cd ~/Desktop/concert-alert-bot
git init
git add .
git commit -m "Concert Alert Bot"
git branch -M main
git remote add origin https://github.com/rizabalci/concert-alert-bot.git
git push -u origin main
```

### 4. Add secrets

Go to your repo, then **Settings → Secrets and variables → Actions → New repository secret**. Add three:

| Name | Value |
|---|---|
| `TICKETMASTER_API_KEY` | your Consumer Key |
| `TELEGRAM_BOT_TOKEN` | the token from BotFather |
| `TELEGRAM_CHAT_ID` | your numeric chat ID |

### 5. Test it

Go to the **Actions** tab, select **Concert Alerts**, and click **Run workflow**. The first run will find a lot, so expect a few messages. After that it only sends new listings.

## Local testing

```bash
pip install -r requirements.txt
export TICKETMASTER_API_KEY=your_key
DRY_RUN=1 python concert_bot.py
```

`DRY_RUN=1` prints the messages to your terminal instead of sending them. Add `RESET_SEEN=1` to ignore the saved state.

## Tuning it

Everything lives in `config.py`.

**Add artists you never want to miss.** Anything on the watchlist is sent regardless of city or score:

```python
WATCHLIST = ["Sting", "Snarky Puppy", "Nils Frahm", ...]
```

**Make a city noisier or quieter.** Lower `min_score` means more alerts from that city:

```python
{"name": "Budapest", "cc": "HU", "km": 245, "priority": 1, "min_score": 15, ...}
```

**Favour certain genres.** Raise the bonus to see more of them:

```python
GENRE_BONUS = {"jazz": 12, "world": 10, "classical": 8, ...}
```

**Only want jazz and classical?** Fill in the filter:

```python
GENRE_FILTER = ["jazz", "classical"]
```

**Too many messages?** Lower `MAX_PER_CITY` or raise the `min_score` values. **Too few?** Do the opposite.

**Change the schedule.** Edit the cron in `.github/workflows/concerts.yml`:

| Frequency | Cron |
|---|---|
| Daily 08:00 Vienna | `0 6 * * *` |
| Mondays only | `0 6 * * 1` |
| Twice a week | `0 6 * * 1,4` |

## Coverage note

Ticketmaster has strong coverage in Austria, Germany, Netherlands, Belgium, Spain, UK, Ireland, Poland, Czechia, Sweden and Denmark. Coverage in Slovakia and Hungary is thinner, so some local Bratislava and Budapest shows will not appear. The big arena tours do show up there, which is what the bot is optimised for anyway.

## Files

```
concert-alert-bot/
├── concert_bot.py                  # daily scan
├── commands.py                     # Telegram command listener
├── config.py                       # cities, watchlist, scoring, genres
├── travel.py                       # train / bus / flight / hotel links per city
├── songkick.py                     # second source for club shows and SK/HU
├── pending.json                    # events waiting for their on-sale date
├── tg_offset.json                  # last handled Telegram message
├── watchlist_extra.json            # artists added with /watch
├── requirements.txt
├── seen.json                       # state, auto committed by the workflow
└── .github/workflows/
    ├── concerts.yml                # daily digest
    └── commands.yml                # command listener
```

## Author

Riza Balci
