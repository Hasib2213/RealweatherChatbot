# services/chat/chatbot_schema.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    message: str
    # ← ONLY THIS FIELD! No session_id here!

class WeatherData(BaseModel):
    city: str
    country: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    icon: Optional[str] = None

class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ChatResponse(BaseModel):
    response: str
    weather_data: Optional[WeatherData] = None
    forecast_data: Optional[Dict] = None
    tool_calls: Optional[List[str]] = None
    session_id: str

class ConversationHistory(BaseModel):
    session_id: str
    history: List[Dict[str, str]]
    created_at: str
    updated_at: str

class HealthCheck(BaseModel):
    status: str
    fastapi: str
    mcp_server: str
    llm_configured: bool
    redis_connected: bool