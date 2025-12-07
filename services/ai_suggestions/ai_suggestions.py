from typing import List, Dict
from datetime import datetime
from services.ai_suggestions.ai_suggestions_schema import (
    SuggestionResponse, WeatherSuggestion
)
from utils.llm_service import LLMService
from utils.weather_service import WeatherService

class AISuggestionsService:
    def __init__(self):
        self.llm_service = LLMService()
        self.weather_service = WeatherService()
    
    async def generate_suggestions(
        self, 
        city: str, 
        context: str = None
    ) -> SuggestionResponse:
        """Generate AI-powered weather-based suggestions"""
        try:
            weather_data = await self.weather_service.get_weather(city)
            
            suggestions = [
                WeatherSuggestion(
                    category="Outdoor Activity",
                    suggestion=f"Great weather for outdoor activities at {weather_data.temperature}°C",
                    priority="medium",
                    icon="🏃"
                ),
                WeatherSuggestion(
                    category="Clothing",
                    suggestion=f"Dress appropriately for {weather_data.description}",
                    priority="high",
                    icon="👕"
                ),
            ]
            
            return SuggestionResponse(
                city=city,
                suggestions=suggestions,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            return SuggestionResponse(
                city=city,
                suggestions=[
                    WeatherSuggestion(
                        category="General",
                        suggestion="Check weather conditions before going out",
                        priority="medium",
                        icon="🌤️"
                    )
                ],
                generated_at=datetime.now()
            )