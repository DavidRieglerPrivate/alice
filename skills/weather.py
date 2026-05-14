import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from skills._base import SkillResult

load_dotenv()

_API_KEY      = os.getenv("OPENWEATHERMAP_API_KEY", "")
_DEFAULT_CITY = os.getenv("WEATHER_DEFAULT_CITY", "London")
_UNITS        = os.getenv("WEATHER_UNITS", "metric").lower()
_BASE_URL     = "https://api.openweathermap.org/data/2.5"
_UNIT_WORD    = "Celsius" if _UNITS == "metric" else "Fahrenheit"


def _wind_dir(deg: float) -> str:
    dirs = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
    return dirs[round(deg / 45) % 8]


def _wind_desc(speed: float, deg: float) -> str:
    direction = _wind_dir(deg)
    kmh = speed * 3.6 if _UNITS == "metric" else speed * 1.609
    if kmh < 2:
        return "calm conditions"
    if kmh < 20:
        return f"a light breeze from the {direction}"
    if kmh < 40:
        return f"moderate winds from the {direction}"
    return f"strong winds from the {direction}"


def _fetch(endpoint: str, city: str, extra: dict | None = None) -> dict:
    params: dict = {"q": city, "appid": _API_KEY, "units": _UNITS}
    if extra:
        params.update(extra)
    resp = requests.get(f"{_BASE_URL}/{endpoint}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _error(city: str, exc: Exception) -> SkillResult:
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response.status_code == 404:
        return SkillResult(
            response=f"I couldn't find a place called {city}. Try a different city name.",
            success=False,
        )
    if isinstance(exc, requests.exceptions.RequestException):
        return SkillResult(
            response="I couldn't reach the weather service. Check your internet connection.",
            success=False,
        )
    return SkillResult(response="Something went wrong fetching the weather.", success=False)


def _entries_by_date(entries: list, tz_offset: int) -> dict:
    by_date: dict = defaultdict(list)
    for e in entries:
        local_dt = datetime.fromtimestamp(e["dt"], tz=timezone.utc) + timedelta(seconds=tz_offset)
        by_date[local_dt.date()].append(e)
    return by_date


def _day_summary(day_entries: list) -> tuple[int, int, str, bool]:
    lo       = min(round(e["main"]["temp_min"]) for e in day_entries)
    hi       = max(round(e["main"]["temp_max"]) for e in day_entries)
    conds    = [e["weather"][0]["description"] for e in day_entries]
    dominant = max(set(conds), key=conds.count)
    has_rain = any("rain" in e["weather"][0]["main"].lower() for e in day_entries)
    return lo, hi, dominant, has_rain


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _no_key() -> SkillResult:
    return SkillResult(
        response="I need an OpenWeatherMap API key to check the weather.",
        success=False,
    )


# ── current conditions ────────────────────────────────────────────────────────

def handle_current_weather(city: str = "") -> SkillResult:
    city = (city or _DEFAULT_CITY).strip()
    if not _API_KEY:
        return _no_key()
    try:
        d        = _fetch("weather", city)
        temp     = round(d["main"]["temp"])
        feels    = round(d["main"]["feels_like"])
        humidity = d["main"]["humidity"]
        desc     = d["weather"][0]["description"]
        wind     = _wind_desc(d["wind"]["speed"], d["wind"].get("deg", 0))
        name     = d["name"]
        country  = d["sys"]["country"]
        return SkillResult(
            response=(
                f"Currently in {name}, {country}: {temp} degrees {_UNIT_WORD}, {desc}. "
                f"Feels like {feels} degrees, humidity {humidity} percent, and {wind}."
            ),
            success=True,
        )
    except Exception as e:
        return _error(city, e)


# ── single-day forecast (tomorrow / day after tomorrow) ───────────────────────

def _handle_day_forecast(city: str, day_offset: int, label: str) -> SkillResult:
    city = (city or _DEFAULT_CITY).strip()
    if not _API_KEY:
        return _no_key()
    try:
        d         = _fetch("forecast", city, {"cnt": 8 * (day_offset + 2)})
        name      = d["city"]["name"]
        country   = d["city"]["country"]
        tz_off    = d["city"]["timezone"]
        now_local = datetime.now(timezone.utc) + timedelta(seconds=tz_off)
        target    = (now_local + timedelta(days=day_offset)).date()
        entries   = _entries_by_date(d["list"], tz_off).get(target, [])

        if not entries:
            return SkillResult(
                response=f"I don't have forecast data for {label} in {name}, {country}.",
                success=False,
            )

        lo, hi, dominant, has_rain = _day_summary(entries)
        rain_note = " Rain is expected." if has_rain else ""
        return SkillResult(
            response=(
                f"{label.capitalize()} in {name}, {country}: "
                f"expect {dominant} with lows of {lo} and highs of {hi} degrees {_UNIT_WORD}.{rain_note}"
            ),
            success=True,
        )
    except Exception as e:
        return _error(city, e)


def handle_tomorrow_weather(city: str = "") -> SkillResult:
    return _handle_day_forecast(city, 1, "tomorrow")


def handle_day_after_tomorrow(city: str = "") -> SkillResult:
    return _handle_day_forecast(city, 2, "the day after tomorrow")


# ── umbrella advice ───────────────────────────────────────────────────────────

def handle_umbrella(city: str = "", timeframe: str = "today") -> SkillResult:
    city = (city or _DEFAULT_CITY).strip()
    if not _API_KEY:
        return _no_key()
    try:
        is_week     = "week" in timeframe
        is_tomorrow = timeframe == "tomorrow"
        cnt         = 40 if is_week else 16 if is_tomorrow else 8

        d         = _fetch("forecast", city, {"cnt": cnt})
        name      = d["city"]["name"]
        country   = d["city"]["country"]
        tz_off    = d["city"]["timezone"]
        entries   = d["list"]

        if not is_week:
            now_local = datetime.now(timezone.utc) + timedelta(seconds=tz_off)
            offset    = 1 if is_tomorrow else 0
            target    = (now_local + timedelta(days=offset)).date()
            entries   = _entries_by_date(entries, tz_off).get(target, entries)

        has_rain = any("rain" in e["weather"][0]["main"].lower() for e in entries)
        period   = {"today": "today", "tomorrow": "tomorrow", "this week": "this week"}.get(
            timeframe, "then"
        )

        if has_rain:
            return SkillResult(
                response=f"Yes, bring an umbrella {period} in {name}, {country}. Rain is in the forecast.",
                success=True,
            )
        return SkillResult(
            response=f"No umbrella needed {period} in {name}, {country}. No rain is expected.",
            success=True,
        )
    except Exception as e:
        return _error(city, e)


# ── weekly outlook ────────────────────────────────────────────────────────────

def handle_week_outlook(city: str = "") -> SkillResult:
    city = (city or _DEFAULT_CITY).strip()
    if not _API_KEY:
        return _no_key()
    try:
        d         = _fetch("forecast", city, {"cnt": 40})
        name      = d["city"]["name"]
        country   = d["city"]["country"]
        tz_off    = d["city"]["timezone"]
        entries   = d["list"]
        by_date   = _entries_by_date(entries, tz_off)

        overall_lo = min(round(e["main"]["temp_min"]) for e in entries)
        overall_hi = max(round(e["main"]["temp_max"]) for e in entries)

        rainy_days = [
            date.strftime("%A")
            for date, day_entries in sorted(by_date.items())
            if _day_summary(day_entries)[3]
        ]

        rain_part = (
            f" Rain is expected on {_join(rainy_days)}." if rainy_days
            else " No rain is expected."
        )

        return SkillResult(
            response=(
                f"This week in {name}, {country}: temperatures ranging from {overall_lo} to "
                f"{overall_hi} degrees {_UNIT_WORD}.{rain_part}"
            ),
            success=True,
        )
    except Exception as e:
        return _error(city, e)


# ── next-24h forecast ─────────────────────────────────────────────────────────

def handle_weather_forecast(city: str = "") -> SkillResult:
    city = (city or _DEFAULT_CITY).strip()
    if not _API_KEY:
        return _no_key()
    try:
        d       = _fetch("forecast", city, {"cnt": 8})
        name    = d["city"]["name"]
        country = d["city"]["country"]
        entries = d["list"]

        lo       = min(round(e["main"]["temp_min"]) for e in entries)
        hi       = max(round(e["main"]["temp_max"]) for e in entries)
        conds    = [e["weather"][0]["description"] for e in entries]
        dominant = max(set(conds), key=conds.count)
        has_rain = any("rain" in e["weather"][0]["main"].lower() for e in entries)
        rain_note = " Rain is expected at some point." if has_rain else ""

        return SkillResult(
            response=(
                f"Over the next 24 hours in {name}, {country}: "
                f"expect {dominant} with lows of {lo} and highs of {hi} degrees {_UNIT_WORD}.{rain_note}"
            ),
            success=True,
        )
    except Exception as e:
        return _error(city, e)
