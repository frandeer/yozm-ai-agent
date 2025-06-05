import json
import httpx
from google.adk.agents import Agent
from geopy.geocoders import Nominatim


def get_coordinates(city_name: str) -> tuple[float, float]:
    """Converts a city name to latitude and longitude."""
    geolocator = Nominatim(user_agent="weather_app")
    location = geolocator.geocode(city_name)
    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"Could not find coordinates for {city_name}")


def get_weather(city_name: str) -> dict:
    """Fetches weather data for a given latitude and longitude or city name."""
    if city_name:
        latitude, longitude = get_coordinates(city_name)
    else:
        raise ValueError("City name must be provided to get weather information.")

    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    response = httpx.get(url)
    response.raise_for_status()  # Raises an exception for HTTP errors
    return response.json()


def get_kbo_rank() -> dict:
    """한국 프로야구 구단의 랭킹을 가져오는 함수입니다."""
    result = httpx.get(
        "https://sports.daum.net/prx/hermes/api/team/rank.json?leagueCode=kbo&seasonKey=2025"
    )
    return json.loads(result.text)


root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash-preview-05-20",
    description="An agent that provides weather information for a given city or coordinates.",
    instruction="Provide the current weather for a specified city or coordinates.",
    tools=[get_weather, get_kbo_rank],
)
