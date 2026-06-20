from fastapi import APIRouter

from app.schemas.weather import (
    WeatherResponse
)
from app.services.weather_service import (
    weather_service
)

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "",
    response_model=WeatherResponse,
)
def get_weather(
    latitude: float,
    longitude: float,
):

    return weather_service.get_weather(
        latitude,
        longitude,
    )