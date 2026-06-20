from pydantic import BaseModel


class WeatherResponse(BaseModel):
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    condition: str
    location: str