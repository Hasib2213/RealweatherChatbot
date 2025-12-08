# utils/weather_service.py
import httpx
from typing import Dict, Optional
from Core.config import settings
from datetime import datetime


class WeatherService:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL or "https://api.openweathermap.org/data/2.5"


    # ======================================================
    #   CURRENT WEATHER
    # ======================================================
    async def get_weather(self, city: str, country_code: Optional[str] = None) -> Dict:
        if not city:
            return {"error": "City name is required."}

        location = f"{city},{country_code}" if country_code else city
        url = f"{self.base_url}/weather"
        params = {"q": location, "appid": self.api_key, "units": "metric"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            return {"error": str(e)}

        # TIMEZONE OFFSET (seconds)
        timezone_offset = data.get("timezone", 0)

        # RAW sunrise/sunset timestamps (UTC)
        sunrise_ts = data.get("sys", {}).get("sunrise", 0)
        sunset_ts = data.get("sys", {}).get("sunset", 0)

        # CONVERT TO LOCAL TIME FOR THAT CITY
        sunrise = (
            datetime.utcfromtimestamp(sunrise_ts + timezone_offset).strftime("%I:%M %p")
            if sunrise_ts else "N/A"
        )
        sunset = (
            datetime.utcfromtimestamp(sunset_ts + timezone_offset).strftime("%I:%M %p")
            if sunset_ts else "N/A"
        )

        # Response
        return {
            "city": data.get("name", ""),
            "country": data.get("sys", {}).get("country", ""),

            "temperature": round(data["main"].get("temp", 0), 1),
            "feels_like": round(data["main"].get("feels_like", 0), 1),
            "description": data["weather"][0].get("description", "").title(),

            "humidity": data["main"].get("humidity", 0),
            "wind_speed": data["wind"].get("speed", 0),

            "temp_min": round(data["main"].get("temp_min", 0), 1),
            "temp_max": round(data["main"].get("temp_max", 0), 1),

            "sunrise": sunrise,
            "sunset": sunset,
        }


    # ======================================================
    #   3-DAY FORECAST
    # ======================================================
    async def get_forecast(self, city: str, country_code: Optional[str] = None, days: int = 3) -> Dict:
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
        except Exception as e:
            return {"error": str(e)}

        city_info = data.get("city", {})
        timezone_offset = city_info.get("timezone", 0)

        # Sunrise/Sunset (UTC)
        sunrise_ts = city_info.get("sunrise", 0)
        sunset_ts = city_info.get("sunset", 0)

        # Convert to local time
        sunrise = (
            datetime.utcfromtimestamp(sunrise_ts + timezone_offset).strftime("%I:%M %p")
            if sunrise_ts else "N/A"
        )
        sunset = (
            datetime.utcfromtimestamp(sunset_ts + timezone_offset).strftime("%I:%M %p")
            if sunset_ts else "N/A"
        )

        # Group 3-hour items into days
        from collections import defaultdict
        daily_forecast = defaultdict(list)

        for item in data.get("list", []):
            dt_local = item.get("dt", 0) + timezone_offset
            date = datetime.utcfromtimestamp(dt_local).strftime("%Y-%m-%d")
            daily_forecast[date].append(item)

        # Build daily forecasts
        forecasts = []
        for date, items in list(daily_forecast.items())[:days]:
            temps = [i["main"].get("temp", 0) for i in items]
            descs = [i["weather"][0].get("description", "") for i in items]

            forecast_item = {
                "date": date,
                "temp_min": round(min(temps), 1),
                "temp_max": round(max(temps), 1),
                "description": max(set(descs), key=descs.count).title(),
                "sunrise": sunrise,
                "sunset": sunset
            }
            forecasts.append(forecast_item)

        return {
            "city": city_info.get("name", ""),
            "country": city_info.get("country", ""),
            "forecasts": forecasts
        }
