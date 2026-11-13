"""Weather via Open-Meteo (no API key needed) with wttr.in fallback."""

from urllib.parse import quote, quote_plus

import requests
from console_ui import console

WMO_CODES = {
    0: ("clear", "☀️", "Ясно", "Clear"),
    1: ("mainly_clear", "🌤️", "Малооблачно", "Mostly clear"),
    2: ("partly_cloudy", "⛅", "Переменная облачность", "Partly cloudy"),
    3: ("overcast", "☁️", "Пасмурно", "Overcast"),
    45: ("fog", "🌫️", "Туман", "Fog"),
    48: ("fog", "🌫️", "Изморозь", "Rime fog"),
    51: ("drizzle", "🌦️", "Морось", "Light drizzle"),
    53: ("drizzle", "🌦️", "Морось", "Moderate drizzle"),
    55: ("drizzle", "🌧️", "Сильная морось", "Dense drizzle"),
    61: ("rain", "🌧️", "Дождь", "Light rain"),
    63: ("rain", "🌧️", "Дождь", "Moderate rain"),
    65: ("rain", "🌧️", "Сильный дождь", "Heavy rain"),
    71: ("snow", "🌨️", "Снег", "Light snow"),
    73: ("snow", "🌨️", "Снег", "Moderate snow"),
    75: ("snow", "❄️", "Сильный снег", "Heavy snow"),
    77: ("snow", "❄️", "Снежная крупа", "Snow grains"),
    80: ("rain", "🌧️", "Ливень", "Rain showers"),
    81: ("rain", "🌧️", "Ливень", "Moderate showers"),
    82: ("rain", "🌧️", "Сильный ливень", "Violent showers"),
    85: ("snow", "🌨️", "Снегопад", "Snow showers"),
    86: ("snow", "❄️", "Сильный снегопад", "Heavy snow showers"),
    95: ("thunderstorm", "⛈️", "Гроза", "Thunderstorm"),
    96: ("thunderstorm", "⛈️", "Гроза с градом", "Thunderstorm with hail"),
    99: ("thunderstorm", "⛈️", "Сильная гроза", "Heavy thunderstorm"),
}

# wttr.in weather codes (met.no style) → our WMO categories
WTTR_TO_WMO = {
    113: 0, 116: 2, 119: 3, 122: 3, 143: 45, 176: 61, 179: 71, 182: 61,
    185: 61, 200: 95, 227: 71, 230: 75, 248: 45, 260: 45, 281: 51, 284: 53,
    293: 61, 296: 61, 299: 63, 302: 63, 305: 65, 308: 65, 311: 51, 314: 53,
    317: 71, 320: 73, 323: 71, 326: 71, 329: 73, 332: 73, 335: 75, 338: 75,
    350: 61, 353: 80, 356: 81, 359: 82, 362: 61, 365: 61, 368: 71, 371: 75,
    374: 61, 377: 61, 386: 95, 389: 95, 392: 95, 395: 85,
}

# met.no symbol_code (day/night suffix stripped) → our WMO categories
METNO_TO_WMO = {
    "clearsky": 0,
    "fair": 1,
    "partlycloudy": 2,
    "cloudy": 3,
    "fog": 45,
    "drizzle": 51,
    "lightrain": 61,
    "rain": 63,
    "heavyrain": 65,
    "lightrainshowers": 80,
    "rainshowers": 80,
    "heavyrainshowers": 82,
    "lightsleet": 71,
    "lightsleetshowers": 85,
    "sleet": 71,
    "sleetshowers": 85,
    "heavysleet": 73,
    "heavysleetshowers": 85,
    "lightsnow": 71,
    "lightsnowshowers": 85,
    "snow": 73,
    "snowshowers": 85,
    "heavysnow": 75,
    "heavysnowshowers": 86,
    "lightsnowshowersandthunder": 95,
    "lightssleetshowersandthunder": 95,
    "snowshowersandthunder": 95,
    "sleetandthunder": 95,
    "heavysleetandthunder": 95,
    "snowandthunder": 95,
    "heavysnowandthunder": 99,
    "rainshowersandthunder": 95,
    "heavyrainshowersandthunder": 95,
    "heavyrainandthunder": 96,
}

METNO_USER_AGENT = "botyaranewtab/0.2.1 (github.com/dimasbotyara/botyaranewtab)"

# Provider that worked last (avoid paying the timeout of a dead one
# on every refresh). Benign races under the threaded dev server.
_PREFERRED = None


def _valid_coords(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def _num(value, default: float = 0.0) -> float:
    """Coerce a JSON value to float; JSON nulls and junk → default.

    wttr.in returns numbers as strings ("temp_C": "4"), so numeric
    strings must survive the coercion.
    """
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _get_json(url: str, timeout: int = 5) -> dict:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _from_open_meteo(lat: float, lon: float, units: str) -> dict:
    """Fetch current weather from api.open-meteo.com."""
    temp_unit = "celsius" if units == "celsius" else "fahrenheit"
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={quote(str(lat))}&longitude={quote(str(lon))}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature"
        f"&temperature_unit={temp_unit}"
        f"&wind_speed_unit=kmh"
        f"&timezone=auto"
    )

    data = _get_json(url)
    current = data.get("current") or {}
    if current.get("temperature_2m") is None:
        raise ValueError("empty forecast payload")

    code = int(_num(current.get("weather_code")))
    wmo = WMO_CODES.get(code, WMO_CODES[0])

    return {
        "temperature": round(_num(current.get("temperature_2m"))),
        "feels_like": round(_num(current.get("apparent_temperature"))),
        "humidity": int(_num(current.get("relative_humidity_2m"))),
        "wind_speed": round(_num(current.get("wind_speed_10m"))),
        "weather_code": code,
        "icon": wmo[1],
        "description_ru": wmo[2],
        "description_en": wmo[3],
        "unit": "°C" if units == "celsius" else "°F",
        "source": "open-meteo",
    }


def _from_metno(lat: float, lon: float, units: str) -> dict:
    """Fetch current weather from api.met.no (Yr, keyless, User-Agent required)."""
    url = (
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact"
        f"?lat={quote(str(lat))}&lon={quote(str(lon))}"
    )
    resp = requests.get(url, timeout=8, headers={"User-Agent": METNO_USER_AGENT})
    resp.raise_for_status()
    series = resp.json().get("properties", {}).get("timeseries") or []
    if not series:
        raise ValueError("empty met.no payload")

    details = (((series[0].get("data") or {}).get("instant") or {}).get("details")) or {}
    if details.get("air_temperature") is None:
        raise ValueError("empty met.no details")

    temp_c = _num(details.get("air_temperature"))
    hours = (series[0].get("data") or {}).get("next_1_hours") or {}
    symbol = ((hours.get("summary") or {}).get("symbol_code")) or ""
    if symbol:
        code = METNO_TO_WMO.get(symbol.rsplit("_", 1)[0], 3)
    else:
        # No forecast symbol — approximate from cloud cover
        cloud = _num(details.get("cloud_area_fraction"))
        code = 0 if cloud < 25 else (2 if cloud < 75 else 3)
    wmo = WMO_CODES.get(code, WMO_CODES[0])

    if units == "celsius":
        temperature, feels_like, unit = round(temp_c), round(temp_c), "°C"
    else:
        temperature, feels_like, unit = round(temp_c * 9 / 5 + 32), round(temp_c * 9 / 5 + 32), "°F"

    return {
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": int(_num(details.get("relative_humidity"))),
        "wind_speed": round(_num(details.get("wind_speed")) * 3.6),  # m/s → km/h
        "weather_code": code,
        "icon": wmo[1],
        "description_ru": wmo[2],
        "description_en": wmo[3],
        "unit": unit,
        "source": "met.no",
    }


def _from_wttr(lat: float, lon: float, units: str) -> dict:
    """Fetch current weather from wttr.in (fallback provider)."""
    data = _get_json(f"https://wttr.in/{quote(str(lat))},{quote(str(lon))}?format=j1", timeout=8)
    conditions = data.get("current_condition") or []
    current = conditions[0] if conditions else None
    if not current or current.get("temp_C") is None:
        raise ValueError("empty wttr payload")

    wttr_code = int(_num(current.get("weatherCode"), 113))
    code = WTTR_TO_WMO.get(wttr_code, 3)
    wmo = WMO_CODES.get(code, WMO_CODES[0])
    desc_en = ((current.get("weatherDesc") or [{}])[0]).get("value") or wmo[3]

    if units == "celsius":
        temperature, feels_like, unit = (
            round(_num(current.get("temp_C"))),
            round(_num(current.get("FeelsLikeC"))),
            "°C",
        )
    else:
        temperature, feels_like, unit = (
            round(_num(current.get("temp_F"))),
            round(_num(current.get("FeelsLikeF"))),
            "°F",
        )

    return {
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": int(_num(current.get("humidity"))),
        "wind_speed": round(_num(current.get("windspeedKmph"))),
        "weather_code": code,
        "icon": wmo[1],
        "description_ru": wmo[2],
        "description_en": desc_en,
        "unit": unit,
        "source": "wttr.in",
    }


_PROVIDERS = (_from_open_meteo, _from_metno, _from_wttr)


def get_weather(lat: float, lon: float, units: str = "celsius") -> dict | None:
    """Fetch current weather, trying providers (last working one first)."""
    if not _valid_coords(lat, lon):
        return None

    order = sorted(_PROVIDERS, key=lambda p: p is not _PREFERRED)
    for fetcher in order:
        try:
            result = fetcher(lat, lon, units)
            if result:
                globals()["_PREFERRED"] = fetcher
                return result
        except Exception as e:
            console.print(f"[err]weather error ({fetcher.__name__}): {e}[/err]")
    return None


def geocode_city(city: str) -> dict | None:
    """Geocode a city name using Open-Meteo geocoding API."""
    try:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search"
            f"?name={quote_plus(city)}&count=1&language=en"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if results:
            r = results[0]
            return {
                "name": r.get("name", city),
                "lat": r["latitude"],
                "lon": r["longitude"],
                "country": r.get("country", ""),
                "timezone": r.get("timezone", ""),
            }
    except Exception as e:
        console.print(f"[err]geocode error: {e}[/err]")
    return None

def reverse_geocode(lat: float, lon: float) -> dict | None:
    """Reverse geocode coordinates → city name using Open-Meteo."""
    if not _valid_coords(lat, lon):
        return None
    try:
        url = (
            "https://geocoding-api.open-meteo.com/v1/reverse"
            f"?latitude={quote(str(lat))}&longitude={quote(str(lon))}&count=1&language=en"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            r = results[0]
            return {
                "name": r.get("name", ""),
                "country": r.get("country", ""),
                "timezone": r.get("timezone", ""),
            }
    except Exception as e:
        console.print(f"[err]reverse geocode error: {e}[/err]")
    return None
