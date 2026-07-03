import requests
from fastapi import HTTPException, status

from app.core.config import get_settings


class WeatherService:

    @staticmethod
    def get_weather(
        latitude: float,
        longitude: float,
    ):
        api_key = get_settings().OPENWEATHER_API_KEY
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Weather service is temporarily unavailable."
            )

        weather_url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={latitude}"
            f"&lon={longitude}"
            "&units=metric"
            f"&appid={api_key}"
        )

        try:
            weather_response = requests.get(
                weather_url,
                timeout=10,
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch weather data at the moment.",
            ) from exc

        reverse_url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={latitude}"
            f"&lon={longitude}"
            "&format=json"
        )

        try:
            location_response = requests.get(
                reverse_url,
                headers={
                    "User-Agent": "PaddyCareAI/1.0"
                },
                timeout=10,
            )
            location_response.raise_for_status()
            location_data = location_response.json()
        except requests.RequestException:
            location_data = {}

        address = location_data.get("address", {})

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or ""
        )

        state = address.get("state", "")

        location = f"{city}, {state}".strip(", ")

        return {
            "temperature": weather_data["main"]["temp"],
            "humidity": weather_data["main"]["humidity"],
            "rainfall": weather_data.get("rain", {}).get("1h", 0),
            "wind_speed": weather_data["wind"]["speed"],
            "condition": weather_data["weather"][0]["description"].title(),
            "location": location,
        }


weather_service = WeatherService()