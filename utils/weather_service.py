# utils/weather_service.py
import httpx
from typing import Dict, Optional
from Core.config import settings


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        # Use base URL from settings or fallback to correct OpenWeather URL
        self.base_url = settings.OPENWEATHER_BASE_URL or "https://api.openweathermap.org/data/2.5"

    async def get_weather(self, city: str, country_code: Optional[str] = None) -> Dict:
        if not city:
            return {"error": "City name is required."}

        location = f"{city},{country_code}" if country_code else city
        url = f"{self.base_url}/weather"
        params = {"q": location, "appid": self.api_key, "units": "metric"}

        # DEBUG
        print(f"[WeatherService] Requesting: {url}")
        print(f"[WeatherService] Params: {params}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

        # Build a clean structured response
        return {
            "city": data.get("name", ""),
            "country": data.get("sys", {}).get("country", ""),
            "temperature": round(data.get("main", {}).get("temp", 0), 1),
            "feels_like": round(data.get("main", {}).get("feels_like", 0), 1),
            "description": data.get("weather", [{}])[0].get("description", "").title(),
            "humidity": data.get("main", {}).get("humidity", 0),
            "wind_speed": data.get("wind", {}).get("speed", 0)
        }
    async def get_forecast(self, city: str, country_code: Optional[str] = None, days: int = 3) -> Dict:
        """
        Fetch weather forecast for the next `days` days.
        Note: OpenWeatherMap free API supports 3-hour forecast, 
        so this example aggregates daily forecast for simplicity.
        """
        if not city:
            return {"error": "City name is required."}

        location = f"{city},{country_code}" if country_code else city
        url = f"{self.base_url}/forecast"
        params = {"q": location, "appid": self.api_key, "units": "metric"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

        # Aggregate forecasts per day
        from collections import defaultdict
        daily_forecast = defaultdict(list)

        for item in data.get("list", []):
            dt_txt = item.get("dt_txt", "")
            date_str = dt_txt.split(" ")[0] if dt_txt else ""
            daily_forecast[date_str].append(item)

        # Build summary per day
        forecasts = []
        for date, items in list(daily_forecast.items())[:days]:
            temps = [x.get("main", {}).get("temp", 0) for x in items]
            descriptions = [x.get("weather", [{}])[0].get("description", "") for x in items]
            forecasts.append({
                "date": date,
                "temp_min": round(min(temps), 1),
                "temp_max": round(max(temps), 1),
                "description": max(set(descriptions), key=descriptions.count).title()
            })

        if not forecasts:
            return {"message": "Forecast not available yet."}

        return {
            "city": data.get("city", {}).get("name", ""),
            "country": data.get("city", {}).get("country", ""),
            "forecasts": forecasts
        }
