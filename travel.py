"""
Travel options from Vienna to each city.

Flight rules applied here:
  - direct flights only (Skyscanner links carry preferdirects=true)
  - book directly with the airline, never a reseller
  - durations shown so you know what you are committing to
"""

# Booking homepages for direct airline bookings
AIRLINES = {
    "Austrian":        "https://www.austrian.com",
    "Ryanair":         "https://www.ryanair.com",
    "Wizz Air":        "https://wizzair.com",
    "easyJet":         "https://www.easyjet.com",
    "Eurowings":       "https://www.eurowings.com",
    "Vueling":         "https://www.vueling.com",
    "SAS":             "https://www.flysas.com",
    "KLM":             "https://www.klm.com",
    "Air France":      "https://www.airfrance.com",
    "SWISS":           "https://www.swiss.com",
    "TAP":             "https://www.flytap.com",
    "Aer Lingus":      "https://www.aerlingus.com",
    "LOT":             "https://www.lot.com",
    "ITA Airways":     "https://www.ita-airways.com",
    "Iberia":          "https://www.iberia.com",
    "British Airways": "https://www.britishairways.com",
    "Norwegian":       "https://www.norwegian.com",
    "Brussels Airlines": "https://www.brusselsairlines.com",
    "Transavia":       "https://www.transavia.com",
}

# Ground transport operators
OEBB = "https://www.oebb.at/en/"
REGIOJET = "https://regiojet.com/"
FLIXBUS = "https://global.flixbus.com/"
TRENITALIA = "https://www.trenitalia.com/en.html"
DB = "https://www.bahn.com/en"
MAV = "https://www.mavcsoport.hu/en"
CD = "https://www.cd.cz/en/"

# ---------------------------------------------------------------------------
# Per city travel profile
#   mode      : the sensible default way to get there
#   train     : (label, url) or None
#   bus       : (label, url) or None
#   airport   : IATA code for Skyscanner deep links, or None
#   flight    : (duration label, [airline names]) or None
# ---------------------------------------------------------------------------

TRAVEL = {
    "Vienna": {"mode": "home"},

    "Bratislava": {
        "mode": "train",
        "train": ("ÖBB ~1h", OEBB),
        "bus": ("FlixBus / RegioJet ~1h15", REGIOJET),
        "airport": None,
        "flight": None,
    },
    "Graz": {
        "mode": "train",
        "train": ("ÖBB ~2h35", OEBB),
        "bus": ("FlixBus ~2h45", FLIXBUS),
        "airport": None,
        "flight": None,
    },
    "Budapest": {
        "mode": "train",
        "train": ("ÖBB / MÁV ~2h20", OEBB),
        "bus": ("FlixBus / RegioJet ~3h", REGIOJET),
        "airport": None,
        "flight": None,
    },
    "Salzburg": {
        "mode": "train",
        "train": ("ÖBB ~2h25", OEBB),
        "bus": ("FlixBus ~3h15", FLIXBUS),
        "airport": None,
        "flight": None,
    },
    "Prague": {
        "mode": "train",
        "train": ("ÖBB / ČD ~4h", OEBB),
        "bus": ("RegioJet ~4h15", REGIOJET),
        "airport": "PRG",
        "flight": ("~1h", ["Austrian"]),
    },
    "Munich": {
        "mode": "train",
        "train": ("ÖBB / DB ~4h", OEBB),
        "bus": ("FlixBus ~5h30", FLIXBUS),
        "airport": "MUC",
        "flight": ("~1h10", ["Austrian", "Eurowings"]),
    },
    "Ljubljana": {
        "mode": "train",
        "train": ("ÖBB ~6h", OEBB),
        "bus": ("FlixBus ~4h30", FLIXBUS),
        "airport": None,
        "flight": None,
    },
    "Zagreb": {
        "mode": "train",
        "train": ("ÖBB ~6h30", OEBB),
        "bus": ("FlixBus ~5h", FLIXBUS),
        "airport": "ZAG",
        "flight": ("~1h", ["Austrian"]),
    },

    "Krakow": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~7h", FLIXBUS),
        "airport": "KRK",
        "flight": ("~1h10", ["Ryanair", "Austrian"]),
    },
    "Berlin": {
        "mode": "flight",
        "train": ("ÖBB Nightjet ~11h", OEBB),
        "bus": ("FlixBus ~9h", FLIXBUS),
        "airport": "BER",
        "flight": ("~1h20", ["Austrian", "Ryanair", "easyJet"]),
    },
    "Warsaw": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~10h", FLIXBUS),
        "airport": "WAW",
        "flight": ("~1h20", ["Austrian", "LOT"]),
    },
    "Zurich": {
        "mode": "flight",
        "train": ("ÖBB Railjet ~8h", OEBB),
        "bus": ("FlixBus ~10h", FLIXBUS),
        "airport": "ZRH",
        "flight": ("~1h25", ["Austrian", "SWISS"]),
    },
    "Milan": {
        "mode": "flight",
        "train": ("ÖBB Nightjet ~13h", OEBB),
        "bus": ("FlixBus ~12h", FLIXBUS),
        "airport": "MXP",
        "flight": ("~1h20", ["Austrian", "Ryanair"]),
    },
    "Hamburg": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~12h", FLIXBUS),
        "airport": "HAM",
        "flight": ("~1h35", ["Austrian", "Eurowings"]),
    },
    "Copenhagen": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "CPH",
        "flight": ("~1h50", ["Austrian", "SAS"]),
    },
    "Rome": {
        "mode": "flight",
        "train": ("ÖBB Nightjet ~14h", OEBB),
        "bus": None,
        "airport": "FCO",
        "flight": ("~1h45", ["Austrian", "ITA Airways", "Ryanair"]),
    },

    "Brussels": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~14h", FLIXBUS),
        "airport": "BRU",
        "flight": ("~1h50", ["Austrian", "Brussels Airlines"]),
    },
    "Amsterdam": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~14h", FLIXBUS),
        "airport": "AMS",
        "flight": ("~1h55", ["Austrian", "KLM", "Transavia"]),
    },
    "Paris": {
        "mode": "flight",
        "train": None,
        "bus": ("FlixBus ~16h", FLIXBUS),
        "airport": "CDG",
        "flight": ("~2h05", ["Austrian", "Air France", "Transavia"]),
    },
    "London": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "LON",
        "flight": ("~2h25", ["Austrian", "British Airways", "Ryanair", "easyJet"]),
    },
    "Stockholm": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "ARN",
        "flight": ("~2h20", ["Austrian", "SAS", "Norwegian"]),
    },
    "Barcelona": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "BCN",
        "flight": ("~2h30", ["Austrian", "Vueling", "Ryanair"]),
    },
    "Dublin": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "DUB",
        "flight": ("~2h50", ["Aer Lingus", "Ryanair"]),
    },
    "Madrid": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "MAD",
        "flight": ("~3h", ["Austrian", "Iberia", "Ryanair"]),
    },
    "Lisbon": {
        "mode": "flight",
        "train": None,
        "bus": None,
        "airport": "LIS",
        "flight": ("~3h35", ["Austrian", "TAP", "Ryanair"]),
    },
}


def skyscanner_url(airport_code, depart_date, return_date):
    """
    Direct-flights-only Skyscanner search.
    depart_date / return_date are datetime.date objects.
    """
    if not airport_code:
        return None
    d = depart_date.strftime("%y%m%d")
    r = return_date.strftime("%y%m%d")
    return (
        f"https://www.skyscanner.net/transport/flights/vie/"
        f"{airport_code.lower()}/{d}/{r}/?preferdirects=true"
    )


# ---------------------------------------------------------------------------
# Accommodation
# ---------------------------------------------------------------------------
# Search links pre-filled with the concert date. City names below are what the
# booking sites expect in their search field.

STAY_CITY_QUERY = {
    "Bratislava": "Bratislava, Slovakia",
    "Graz": "Graz, Austria",
    "Budapest": "Budapest, Hungary",
    "Salzburg": "Salzburg, Austria",
    "Prague": "Prague, Czech Republic",
    "Munich": "Munich, Germany",
    "Ljubljana": "Ljubljana, Slovenia",
    "Zagreb": "Zagreb, Croatia",
    "Krakow": "Krakow, Poland",
    "Berlin": "Berlin, Germany",
    "Warsaw": "Warsaw, Poland",
    "Zurich": "Zurich, Switzerland",
    "Milan": "Milan, Italy",
    "Hamburg": "Hamburg, Germany",
    "Copenhagen": "Copenhagen, Denmark",
    "Rome": "Rome, Italy",
    "Brussels": "Brussels, Belgium",
    "Amsterdam": "Amsterdam, Netherlands",
    "Paris": "Paris, France",
    "London": "London, United Kingdom",
    "Stockholm": "Stockholm, Sweden",
    "Barcelona": "Barcelona, Spain",
    "Dublin": "Dublin, Ireland",
    "Madrid": "Madrid, Spain",
    "Lisbon": "Lisbon, Portugal",
}


def stay_links(city_name, checkin, checkout, adults=2):
    """
    Return [(label, url), ...] for accommodation searches on the concert date.
    checkin / checkout are datetime.date objects.
    """
    from urllib.parse import quote

    q = STAY_CITY_QUERY.get(city_name, city_name)
    ci = checkin.strftime("%Y-%m-%d")
    co = checkout.strftime("%Y-%m-%d")

    booking = (
        "https://www.booking.com/searchresults.html"
        f"?ss={quote(q)}&checkin={ci}&checkout={co}"
        f"&group_adults={adults}&no_rooms=1&group_children=0"
    )

    airbnb = (
        f"https://www.airbnb.com/s/{quote(q)}/homes"
        f"?checkin={ci}&checkout={co}&adults={adults}"
    )

    hostelworld = (
        "https://www.hostelworld.com/search"
        f"?search_keywords={quote(q)}&date_from={ci}&date_to={co}"
        f"&number_of_guests={adults}"
    )

    return [
        ("Booking", booking),
        ("Airbnb", airbnb),
        ("Hostelworld", hostelworld),
    ]
