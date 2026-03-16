from datetime import datetime


class MockWeatherService:
    @staticmethod
    def get_current_weather(city=None):
        month = datetime.utcnow().month
        season = MockWeatherService._month_to_season(month)

        sample_weather = {
            "winter": {"temperature": -3, "weather_condition": "snow"},
            "spring": {"temperature": 12, "weather_condition": "clear"},
            "summer": {"temperature": 24, "weather_condition": "clear"},
            "autumn": {"temperature": 9, "weather_condition": "rain"},
        }

        weather = sample_weather[season]
        return {
            "city": city or "Тестовый город",
            "temperature": weather["temperature"],
            "weather_condition": weather["weather_condition"],
            "season": season,
            "source": "mock",
        }

    @staticmethod
    def _month_to_season(month):
        if month in {12, 1, 2}:
            return "winter"
        if month in {3, 4, 5}:
            return "spring"
        if month in {6, 7, 8}:
            return "summer"
        return "autumn"
