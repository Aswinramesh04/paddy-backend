import requests


class WeatherService:

    @staticmethod
    def get_weather(
        latitude: float,
        longitude: float,
    ):

        weather_url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={latitude}"
            f"&longitude={longitude}"
            "&current=temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        )

        weather_response = requests.get(
            weather_url,
            timeout=10,
        )

        weather_data = weather_response.json()

        reverse_url = (
            "https://nominatim.openstreetmap.org/reverse"
            f"?lat={latitude}"
            f"&lon={longitude}"
            "&format=json"
        )

        location_response = requests.get(
            reverse_url,
            headers={
                "User-Agent": "PaddyCareAI/1.0"
            },
            timeout=10,
        )

        location_data = location_response.json()

        address = location_data.get(
            "address",
            {}
        )

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or ""
        )

        state = address.get(
            "state",
            ""
        )

        location = (
            f"{city}, {state}"
        ).strip(", ")

        current = weather_data["current"]

        weather_code = current.get(
            "weather_code",
            0
        )

        condition = (
            WeatherService.get_condition(
                weather_code
            )
        )

        return {
            "temperature":
                current["temperature_2m"],
            "humidity":
                current[
                    "relative_humidity_2m"
                ],
            "rainfall":
                current["precipitation"],
            "wind_speed":
                current["wind_speed_10m"],
            "condition":
                condition,
            "location":
                location,
        }

    @staticmethod
    def get_condition(
        weather_code: int
    ):

        mapping = {
            0: "Clear Sky",
            1: "Mainly Clear",
            2: "Partly Cloudy",
            3: "Cloudy",
            45: "Fog",
            51: "Light Drizzle",
            61: "Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",
            80: "Rain Showers",
            95: "Thunderstorm",
        }

        return mapping.get(
            weather_code,
            "Unknown",
        )


weather_service = WeatherService()