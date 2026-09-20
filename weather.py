"""Weather via Open-Meteo (no API key needed)."""

import requests
from rich.console import Console

console = Console()

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


def get_weather(lat: float, lon: float, units: str = "celsius") -> dict | None:
    """Fetch current weather from Open-Meteo."""
    try:
        temp_unit = "celsius" if units == "celsius" else "fahrenheit"
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature"
            f"&temperature_unit={temp_unit}"
            f"&wind_speed_unit=kmh"
            f"&timezone=auto"
        )

        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current", {})
        code = current.get("weather_code", 0)
        wmo = WMO_CODES.get(code, WMO_CODES[0])

        return {
            "temperature": round(current.get("temperature_2m", 0)),
            "feels_like": round(current.get("apparent_temperature", 0)),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_speed": round(current.get("wind_speed_10m", 0)),
            "weather_code": code,
            "icon": wmo[1],
            "description_ru": wmo[2],
            "description_en": wmo[3],
            "unit": "°C" if units == "celsius" else "°F",
        }
    except Exception as e:
        console.print(f"[red]Weather error: {e}[/red]")
        return None


def geocode_city(city: str) -> dict | None:
    """Geocode a city name using Open-Meteo geocoding API."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en"
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
        console.print(f"[red]Geocode error: {e}[/red]")
    return None

def reverse_geocode(lat: float, lon: float) -> dict | None:
    """Reverse geocode coordinates → city name using Open-Meteo."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/reverse?latitude={lat}&longitude={lon}&count=1&language=en"
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
        console.print(f"[red]Reverse geocode error: {e}[/red]")
    return None
