from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    

class WeatherData(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    country: str
    timestamp: Optional[datetime] = None
    #new add fields
    temp_min: float
    temp_max: float
    sunrise: None
    sunset: None

class ForecastItem(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    
    description: str
    #new add fields
    sunrise:str="N/A"
    sunset:str="N/A"
    
    

class ForecastData(BaseModel):
    city: str
    country: str
    forecasts: List[ForecastItem]

class ChatResponse(BaseModel):
    response: str
    weather_data: Optional[WeatherData] = None
    forecast_data: Optional[ForecastData] = None
    tool_calls: Optional[List[str]] = None
    session_id: str

class ConversationHistory(BaseModel):
    session_id: str
    history: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime

class HealthCheck(BaseModel):
    status: str
    fastapi: str
    mcp_server: str
    llm_configured: bool
    redis_connected: bool