"""
Configuration for the Concert Alert Bot.
Edit this file to change cities, priorities, genres and scoring.
"""

# ---------------------------------------------------------------------------
# CITIES
# ---------------------------------------------------------------------------
# priority: lower number = checked first and shown first in the digest
# km: approximate distance from Vienna
# min_score: an event in this city must score at least this much to be sent.
#            Vienna is 0 so you get everything at home, far cities need to be
#            a big deal before they interrupt you.

CITIES = [
    # Home
    {"name": "Vienna",     "cc": "AT", "km": 0,    "priority": 0, "min_score": 0,  "emoji": "🏠"},

    # Day trip / overnight
    {"name": "Bratislava", "cc": "SK", "km": 65,   "priority": 1, "min_score": 10, "emoji": "🚆"},
    {"name": "Graz",       "cc": "AT", "km": 200,  "priority": 1, "min_score": 15, "emoji": "🚆"},
    {"name": "Budapest",   "cc": "HU", "km": 245,  "priority": 1, "min_score": 15, "emoji": "🚆"},
    {"name": "Salzburg",   "cc": "AT", "km": 300,  "priority": 1, "min_score": 20, "emoji": "🚆"},
    {"name": "Prague",     "cc": "CZ", "km": 335,  "priority": 1, "min_score": 20, "emoji": "🚆"},
    {"name": "Munich",     "cc": "DE", "km": 360,  "priority": 1, "min_score": 20, "emoji": "🚆"},
    {"name": "Ljubljana",  "cc": "SI", "km": 380,  "priority": 1, "min_score": 25, "emoji": "🚆"},
    {"name": "Zagreb",     "cc": "HR", "km": 370,  "priority": 1, "min_score": 25, "emoji": "🚆"},

    # Weekend trip
    {"name": "Krakow",     "cc": "PL", "km": 420,  "priority": 2, "min_score": 30, "emoji": "✈️"},
    {"name": "Berlin",     "cc": "DE", "km": 680,  "priority": 2, "min_score": 30, "emoji": "✈️"},
    {"name": "Warsaw",     "cc": "PL", "km": 680,  "priority": 2, "min_score": 35, "emoji": "✈️"},
    {"name": "Zurich",     "cc": "CH", "km": 750,  "priority": 2, "min_score": 35, "emoji": "✈️"},
    {"name": "Milan",      "cc": "IT", "km": 770,  "priority": 2, "min_score": 35, "emoji": "✈️"},
    {"name": "Hamburg",    "cc": "DE", "km": 930,  "priority": 2, "min_score": 40, "emoji": "✈️"},
    {"name": "Copenhagen", "cc": "DK", "km": 1040, "priority": 2, "min_score": 40, "emoji": "✈️"},
    {"name": "Rome",       "cc": "IT", "km": 1110, "priority": 2, "min_score": 40, "emoji": "✈️"},

    # Plan around it
    {"name": "Brussels",   "cc": "BE", "km": 1120, "priority": 3, "min_score": 50, "emoji": "✈️"},
    {"name": "Amsterdam",  "cc": "NL", "km": 1150, "priority": 3, "min_score": 50, "emoji": "✈️"},
    {"name": "Paris",      "cc": "FR", "km": 1240, "priority": 3, "min_score": 50, "emoji": "✈️"},
    {"name": "London",     "cc": "GB", "km": 1500, "priority": 3, "min_score": 55, "emoji": "✈️"},
    {"name": "Stockholm",  "cc": "SE", "km": 1580, "priority": 3, "min_score": 55, "emoji": "✈️"},
    {"name": "Barcelona",  "cc": "ES", "km": 1870, "priority": 3, "min_score": 55, "emoji": "✈️"},
    {"name": "Dublin",     "cc": "IE", "km": 1890, "priority": 3, "min_score": 60, "emoji": "✈️"},
    {"name": "Madrid",     "cc": "ES", "km": 2310, "priority": 3, "min_score": 60, "emoji": "✈️"},
    {"name": "Lisbon",     "cc": "PT", "km": 2920, "priority": 3, "min_score": 60, "emoji": "✈️"},
]

TIER_LABEL = {
    0: "Home",
    1: "Day trip",
    2: "Weekend",
    3: "Plan it",
}

# ---------------------------------------------------------------------------
# WATCHLIST
# ---------------------------------------------------------------------------
# Any event whose name contains one of these strings is always sent,
# no matter which city or how low it scores. Case insensitive.
# Add your favourite artists here over time.

WATCHLIST = [
    "Sting",
    "Metallica",
    "Snarky Puppy",
    "GoGo Penguin",
    "Tinariwen",
    "Anouar Brahem",
    "Nils Frahm",
    "Bonobo",
    "Ólafur Arnalds",
    "Kamasi Washington",
    "Worakls",
    "Ludovico Einaudi",
    "Buena Vista",
    "Ibrahim Maalouf",
    "Tigran Hamasyan",
]

# ---------------------------------------------------------------------------
# GENRES
# ---------------------------------------------------------------------------
# Ticketmaster genre names that get a scoring bonus. Set BONUS to 0 to disable.
# Leave GENRE_FILTER empty to receive all music genres.

GENRE_BONUS = {
    "jazz": 12,
    "world": 10,
    "latin": 10,
    "classical": 8,
    "electronic": 6,
    "dance": 6,
    "rock": 4,
    "alternative": 4,
    "blues": 6,
    "folk": 6,
    "r&b": 4,
    "reggae": 4,
}

# Only send these genres. Empty list = send everything.
GENRE_FILTER = []

# Never send these, even if they score high.
GENRE_BLOCKLIST = ["children", "comedy", "family"]

# ---------------------------------------------------------------------------
# MAJOR VENUES
# ---------------------------------------------------------------------------
# Events at these venues score higher because they signal a significant show.

MAJOR_VENUES = [
    "stadthalle", "ernst happel", "gasometer", "arena wien", "metastadt",
    "konzerthaus", "musikverein", "staatsoper", "wuk", "porgy",
    "tipos", "ondrej nepela", "tehelne pole", "majestic music",
    "mvm dome", "puskas", "budapest park", "mupa", "akvarium", "barba negra",
    "o2 arena", "forum karlin", "lucerna",
    "olympiahalle", "zenith", "muffathalle",
    "mercedes-benz arena", "columbiahalle", "tempodrom", "velodrom",
    "ziggo dome", "afas live", "paradiso", "melkweg",
    "accor arena", "olympia", "zenith paris", "bataclan",
    "o2 arena london", "royal albert", "brixton", "alexandra palace",
    "palau sant jordi", "wizink", "mediolanum", "unipol",
    "royal arena", "avicii arena",
]

# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------

SCORE = {
    "vienna_bonus": 40,        # anything in Vienna gets a big head start
    "major_venue": 25,         # show is at a landmark venue
    "high_price": 15,          # top ticket price above HIGH_PRICE_EUR
    "mid_price": 8,            # top ticket price above MID_PRICE_EUR
    "watchlist": 500,          # effectively always send
    "distance_penalty_per_500km": 8,
}

HIGH_PRICE_EUR = 90
MID_PRICE_EUR = 50

# ---------------------------------------------------------------------------
# WINDOW
# ---------------------------------------------------------------------------

MONTHS_AHEAD = 12          # look this far into the future
MAX_EVENTS_PER_RUN = 40    # safety cap so one run cannot spam you
MAX_PER_CITY = 6           # at most this many new events per city per run

# ---------------------------------------------------------------------------
# ACCOMMODATION
# ---------------------------------------------------------------------------
# Show hotel/apartment search links only for cities far enough that you would
# actually stay the night. Bratislava at 65km you would just come home.

STAY_THRESHOLD_KM = 150    # show accommodation links from this distance up
STAY_ADULTS = 2            # you and Ana
STAY_NIGHTS = 1            # nights booked, checkout is this many days later

# ---------------------------------------------------------------------------
# SEASON PASS VENUES
# ---------------------------------------------------------------------------
# Venues where you already hold a pass. The bot will not show ticket links for
# these, it links the program page instead. Match is on lowercase substring.

PASS_VENUES = {
    "musikverein": {
        "label": "You have the yearly pass",
        "program_url": "https://www.musikverein.at/programm",
    },
}

# ---------------------------------------------------------------------------
# ON SALE ALERTS
# ---------------------------------------------------------------------------
# When an event is announced but tickets are not on sale yet, the bot holds it
# and pings you again when the sale opens, so you can act rather than forget.

ONSALE_ALERTS = True
ONSALE_REMINDER_DAYS = 1   # remind this many days before the sale opens

# ---------------------------------------------------------------------------
# SECOND SOURCE
# ---------------------------------------------------------------------------
# Songkick fills the gap where Ticketmaster has thin coverage, mainly Slovakia,
# Hungary, Slovenia, Croatia and club-sized venues everywhere.

USE_SONGKICK = True

# ---------------------------------------------------------------------------
# EXTRAS
# ---------------------------------------------------------------------------

SHOW_WEEKEND_FLAG = True     # mark Fri/Sat shows that need no time off
SHOW_CALENDAR_LINK = True    # one tap add to Google Calendar
