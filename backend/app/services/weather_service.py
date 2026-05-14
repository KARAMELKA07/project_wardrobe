import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


WEATHER_CODE_TO_CONDITION = {
    0: "clear",
    1: "clear",
    2: "sunny",
    3: "cloudy",
    45: "cloudy",
    48: "cloudy",
    51: "rain",
    53: "rain",
    55: "rain",
    56: "rain",
    57: "rain",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "rain",
    96: "rain",
    99: "rain",
}


@dataclass
class ResolvedLocation:
    latitude: float
    longitude: float
    city: Optional[str]
    source: str


class WeatherServiceError(Exception):
    pass


class FallbackWeatherService:
    @staticmethod
    def get_current_weather(city=None, latitude=None, longitude=None):
        month = datetime.utcnow().month
        season = WeatherService.month_to_season(month)

        sample_weather = {
            "winter": {"temperature": -3, "weather_condition": "snow"},
            "spring": {"temperature": 12, "weather_condition": "clear"},
            "summer": {"temperature": 24, "weather_condition": "clear"},
            "autumn": {"temperature": 9, "weather_condition": "rain"},
        }

        weather = sample_weather[season]
        return {
            "city": city or "Текущее местоположение",
            "latitude": latitude,
            "longitude": longitude,
            "temperature": weather["temperature"],
            "temperature_min": weather["temperature"],
            "temperature_max": weather["temperature"],
            "weather_condition": weather["weather_condition"],
            "season": season,
            "source": "fallback",
        }


class WeatherService:
    GEOCODING_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_ENDPOINT = "https://api.open-meteo.com/v1/forecast"

    @classmethod
    def get_current_weather(cls, city=None, latitude=None, longitude=None):
        try:
            resolved_location = cls.resolve_location(
                city=city,
                latitude=latitude,
                longitude=longitude,
            )
            if resolved_location is None:
                return FallbackWeatherService.get_current_weather(city, latitude, longitude)

            forecast_payload = cls.fetch_forecast(
                resolved_location.latitude,
                resolved_location.longitude,
            )
            return cls.normalize_weather_payload(forecast_payload, resolved_location)
        except WeatherServiceError:
            return FallbackWeatherService.get_current_weather(city, latitude, longitude)

    @classmethod
    def resolve_location(cls, city=None, latitude=None, longitude=None):
        if latitude is not None and longitude is not None:
            return ResolvedLocation(
                latitude=float(latitude),
                longitude=float(longitude),
                city=city or "Текущее местоположение",
                source="coordinates",
            )

        normalized_city = (city or "").strip()
        if not normalized_city:
            return None

        geocoding_payload = cls.request_json(
            cls.GEOCODING_ENDPOINT,
            {
                "name": normalized_city,
                "count": 1,
                "language": "ru",
                "format": "json",
            },
        )
        results = geocoding_payload.get("results") or []
        if not results:
            raise WeatherServiceError("Не удалось определить координаты города.")

        first_result = results[0]
        resolved_city = first_result.get("name") or normalized_city
        admin1 = first_result.get("admin1")
        country = first_result.get("country")
        city_label = resolved_city
        if admin1 and admin1 != resolved_city:
            city_label = f"{resolved_city}, {admin1}"
        elif country and country != resolved_city:
            city_label = f"{resolved_city}, {country}"

        return ResolvedLocation(
            latitude=float(first_result["latitude"]),
            longitude=float(first_result["longitude"]),
            city=city_label,
            source="city",
        )

    @classmethod
    def fetch_forecast(cls, latitude, longitude):
        return cls.request_json(
            cls.FORECAST_ENDPOINT,
            {
                "latitude": round(float(latitude), 6),
                "longitude": round(float(longitude), 6),
                "current": "temperature_2m,weather_code,is_day,wind_speed_10m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
                "forecast_days": 1,
                "timezone": "auto",
            },
        )

    @classmethod
    def normalize_weather_payload(cls, payload, resolved_location):
        current = payload.get("current") or {}
        daily = payload.get("daily") or {}

        temperature = cls.pick_number(
            current.get("temperature_2m"),
            cls.mean_temperature(
                cls.get_first_value(daily.get("temperature_2m_min")),
                cls.get_first_value(daily.get("temperature_2m_max")),
            ),
        )
        temperature_min = cls.pick_number(cls.get_first_value(daily.get("temperature_2m_min")))
        temperature_max = cls.pick_number(cls.get_first_value(daily.get("temperature_2m_max")))
        weather_code = cls.pick_number(
            current.get("weather_code"),
            cls.get_first_value(daily.get("weather_code")),
        )
        wind_speed = cls.pick_number(
            current.get("wind_speed_10m"),
            cls.get_first_value(daily.get("wind_speed_10m_max")),
        )
        is_day = bool(current.get("is_day", 1))
        season = cls.month_to_season(datetime.utcnow().month)

        return {
            "city": resolved_location.city or "Текущее местоположение",
            "latitude": round(resolved_location.latitude, 4),
            "longitude": round(resolved_location.longitude, 4),
            "temperature": temperature,
            "temperature_min": temperature_min,
            "temperature_max": temperature_max,
            "weather_condition": cls.map_weather_condition(weather_code, wind_speed, is_day),
            "season": season,
            "source": "open-meteo",
            "timezone": payload.get("timezone"),
            "resolved_from": resolved_location.source,
        }

    @classmethod
    def map_weather_condition(cls, weather_code, wind_speed, is_day):
        if wind_speed is not None and wind_speed >= 35 and weather_code in {0, 1, 2, 3}:
            return "wind"

        normalized_code = int(weather_code) if weather_code is not None else None
        if normalized_code in {1, 2} and is_day:
            return "sunny"

        return WEATHER_CODE_TO_CONDITION.get(normalized_code, "cloudy")

    @classmethod
    def request_json(cls, endpoint, params):
        query_string = urlencode(params)
        url = f"{endpoint}?{query_string}"

        try:
            with urlopen(url, timeout=8) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise WeatherServiceError("Не удалось получить данные о погоде.") from error

    @staticmethod
    def pick_number(*values):
        for value in values:
            if value is None:
                continue
            try:
                return round(float(value))
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def get_first_value(value):
        if isinstance(value, list) and value:
            return value[0]
        return value

    @staticmethod
    def mean_temperature(min_temperature, max_temperature):
        if min_temperature is None and max_temperature is None:
            return None
        if min_temperature is None:
            return max_temperature
        if max_temperature is None:
            return min_temperature
        return (float(min_temperature) + float(max_temperature)) / 2

    @staticmethod
    def month_to_season(month):
        if month in {12, 1, 2}:
            return "winter"
        if month in {3, 4, 5}:
            return "spring"
        if month in {6, 7, 8}:
            return "summer"
        return "autumn"

    @classmethod
    def infer_season_from_temperature(cls, temperature):
        if temperature is None:
            return cls.month_to_season(datetime.utcnow().month)
        if temperature <= 2:
            return "winter"
        if temperature <= 15:
            return "spring"
        if temperature <= 22:
            return "summer" if datetime.utcnow().month in {6, 7, 8} else "autumn"
        return "summer"
