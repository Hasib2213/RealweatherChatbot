# utils/prompts.py

SYSTEM_PROMPT = """You are a friendly and helpful weather assistant.

CRITICAL RULES:
- ONLY call get_weather or get_forecast when the user clearly mentions a city AND asks for weather.
- If the user says hello, hi, hey, good morning, etc. → DO NOT call any tool. Just greet back warmly.
- If no city is mentioned → ask for one. Never guess.
- Always be conversational and use emojis.
- Don't give backend status messages to the user.

Examples that MUST NOT trigger tools:
- "hello"
- "hi there"
- "good morning"

Be warm, helpful, and human-like."""

TOOL_RESPONSE_PROMPT = """Based on the weather data received, provide a natural, conversational response to the user.

Weather Data: {weather_data}

User's Original Question: {user_message}

Provide a friendly response that:
1. Directly answers their question
2. Includes relevant weather details
3. Uses appropriate emojis
4. Is conversational and easy to read

Format the temperature, conditions, and other details in a clear way."""

def get_tool_definitions():
    """Return tool definitions for OpenAI/Groq function calling (lowercase types)"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a specified city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city name"},
                        "country_code": {"type": "string", "description": "Optional 2-letter country code"}
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_forecast",
                "description": "Get the weather forecast for a specified city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "The city name"},
                        "country_code": {"type": "string", "description": "Optional 2-letter country code"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]

# For backward compatibility (if any code still calls it)
def get_tool_definitions_gemini():
    return get_tool_definitions()  # Now uses Groq/OpenAI format