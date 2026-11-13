"""Weather pipeline: providers, fallback, null-safety, API surface.

All external HTTP is faked — the tests never touch the network.
"""

import json

import pytest
import requests

import weather
from weather import get_weather


@pytest.fixture(autouse=True)
def reset_provider_state():
    """get_weather remembers the last working provider module-wide."""
    weather._PREFERRED = None
    yield
    weather._PREFERRED = None


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"HTTP {self.status_code} in test")


def route_mock(open_meteo=None, metno=None, wttr=None):
    """Build a requests.get replacement keyed by the target host."""
    calls = []

    def fake_get(url, timeout=5, **kwargs):
        calls.append(url)
        if "api.open-meteo.com" in url:
            if isinstance(open_meteo, Exception):
                raise open_meteo
            return FakeResponse(open_meteo)
        if "api.met.no" in url:
            if isinstance(metno, Exception):
                raise metno
            return FakeResponse(metno)
        if "wttr.in" in url:
            if isinstance(wttr, Exception):
                raise wttr
            return FakeResponse(wttr)
        raise AssertionError(f"unexpected host in test: {url}")

    return fake_get, calls


OPEN_METEO_PAYLOAD = {
    "current": {
        "temperature_2m": 4.4,
        "apparent_temperature": 1.0,
        "relative_humidity_2m": 85,
        "weather_code": 61,
        "wind_speed_10m": 3.2,
    }
}

METNO_PAYLOAD = {
    "properties": {
        "timeseries": [
            {
                "time": "2026-11-13T19:00:00Z",
                "data": {
                    "instant": {
                        "details": {
                            "air_temperature": 4.3,
                            "wind_speed": 2.8,
                            "relative_humidity": 93.0,
                            "cloud_area_fraction": 100.0,
                        }
                    },
                    "next_1_hours": {"summary": {"symbol_code": "partlycloudy_day"}},
                },
            }
        ]
    }
}

WTTR_PAYLOAD = {
    "current_condition": [
        {
            "temp_C": "4",
            "FeelsLikeC": "-1",
            "temp_F": "39",
            "FeelsLikeF": "30",
            "humidity": "100",
            "windspeedKmph": "11",
            "weatherCode": "116",
            "weatherDesc": [{"value": "Partly cloudy"}],
        }
    ]
}

ALL_DOWN = {
    "open_meteo": requests.ConnectTimeout(),
    "metno": requests.ConnectTimeout(),
    "wttr": requests.ConnectTimeout(),
}


def test_open_meteo_happy_path(monkeypatch):
    fake_get, _ = route_mock(open_meteo=OPEN_METEO_PAYLOAD)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["source"] == "open-meteo"
    assert data["temperature"] == 4
    assert data["feels_like"] == 1
    assert data["humidity"] == 85
    assert data["wind_speed"] == 3
    assert data["weather_code"] == 61
    assert data["icon"] == "🌧️"
    assert data["description_ru"] == "Дождь"
    assert data["description_en"] == "Light rain"
    assert data["unit"] == "°C"


def test_open_meteo_null_fields_do_not_crash(monkeypatch):
    """JSON null is not the same as a missing key — round(None) used to explode."""
    payload = {
        "current": {
            "temperature_2m": 4.4,
            "apparent_temperature": None,
            "relative_humidity_2m": None,
            "weather_code": None,
            "wind_speed_10m": None,
        }
    }
    fake_get, _ = route_mock(open_meteo=payload)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["temperature"] == 4
    assert data["weather_code"] == 0
    assert data["icon"] == "☀️"


def test_empty_forecast_falls_further_down_the_chain(monkeypatch):
    """A null temperature means the provider has no data — try the next one."""
    payload = {
        "current": {
            "temperature_2m": None,
            "apparent_temperature": None,
            "relative_humidity_2m": None,
            "weather_code": None,
            "wind_speed_10m": None,
        }
    }
    fake_get, calls = route_mock(open_meteo=payload, metno=METNO_PAYLOAD)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["source"] == "met.no"
    assert any("api.met.no" in url for url in calls)


def test_metno_happy_path(monkeypatch):
    fake_get, _ = route_mock(
        open_meteo=requests.ConnectTimeout(),
        metno=METNO_PAYLOAD,
    )
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["source"] == "met.no"
    assert data["temperature"] == 4
    assert data["weather_code"] == 2  # partlycloudy_day → WMO partly cloudy
    assert data["icon"] == "⛅"
    assert data["description_ru"] == "Переменная облачность"
    assert data["description_en"] == "Partly cloudy"
    assert data["unit"] == "°C"
    assert data["wind_speed"] == 10  # 2.8 m/s → 10 km/h
    assert data["humidity"] == 93


def test_metno_fahrenheit(monkeypatch):
    fake_get, _ = route_mock(open_meteo=requests.ConnectTimeout(), metno=METNO_PAYLOAD)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55, units="fahrenheit")
    assert data["unit"] == "°F"
    assert data["temperature"] == 40  # 4.3 °C → 39.7 °F


def test_metno_no_symbol_uses_cloud_cover(monkeypatch):
    payload = json.loads(json.dumps(METNO_PAYLOAD))
    del payload["properties"]["timeseries"][0]["data"]["next_1_hours"]

    fake_get, _ = route_mock(open_meteo=requests.ConnectTimeout(), metno=payload)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["weather_code"] == 3  # 100% cloud cover → overcast


def test_falls_back_to_wttr_when_others_dead(monkeypatch):
    fake_get, calls = route_mock(
        open_meteo=ALL_DOWN["open_meteo"],
        metno=ALL_DOWN["metno"],
        wttr=WTTR_PAYLOAD,
    )
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55)
    assert data["source"] == "wttr.in"
    assert data["temperature"] == 4
    assert data["feels_like"] == -1
    assert data["humidity"] == 100
    assert data["wind_speed"] == 11
    assert data["weather_code"] == 2  # wttr 116 → WMO partly cloudy
    assert data["icon"] == "⛅"
    assert data["description_ru"] == "Переменная облачность"
    assert data["description_en"] == "Partly cloudy"
    assert any("wttr.in" in url for url in calls)


def test_wttr_fahrenheit(monkeypatch):
    fake_get, _ = route_mock(open_meteo=ALL_DOWN["open_meteo"], metno=ALL_DOWN["metno"], wttr=WTTR_PAYLOAD)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    data = get_weather(55.42, 37.55, units="fahrenheit")
    assert data["unit"] == "°F"
    assert data["temperature"] == 39
    assert data["feels_like"] == 30


def test_preferred_provider_tried_first(monkeypatch):
    fake_get, calls = route_mock(
        open_meteo=requests.ConnectTimeout(),
        metno=METNO_PAYLOAD,
    )
    monkeypatch.setattr(weather.requests, "get", fake_get)

    get_weather(55.42, 37.55)
    assert weather._PREFERRED is weather._from_metno

    # Second call must hit met.no first — no repeat of the dead host's timeout
    get_weather(55.42, 37.55)
    assert "api.met.no" in calls[-1]


def test_all_providers_down(monkeypatch):
    fake_get, _ = route_mock(**ALL_DOWN)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    assert get_weather(55.42, 37.55) is None


def test_invalid_coords_never_hit_the_network(monkeypatch):
    def boom(url, timeout=5, **kwargs):
        raise AssertionError("network must not be touched")

    monkeypatch.setattr(weather.requests, "get", boom)
    assert get_weather(999, 37.55) is None
    assert get_weather(55.42, -9999) is None


def test_api_weather_ok(client, monkeypatch):
    fake_get, _ = route_mock(open_meteo=OPEN_METEO_PAYLOAD)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    resp = client.get("/api/weather?lat=55.42&lon=37.55")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["temperature"] == 4
    assert data["unit"] == "°C"


def test_api_weather_providers_unavailable(client, monkeypatch):
    fake_get, _ = route_mock(**ALL_DOWN)
    monkeypatch.setattr(weather.requests, "get", fake_get)

    resp = client.get("/api/weather?lat=55.42&lon=37.55")
    assert resp.status_code == 502
    assert resp.get_json()["error"]


def test_wttr_payload_is_real_json():
    """Sanity: the mocked wttr shape is valid JSON round-trip."""
    assert json.loads(json.dumps(WTTR_PAYLOAD)) == WTTR_PAYLOAD
