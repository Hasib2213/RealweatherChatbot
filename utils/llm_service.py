from groq import AsyncGroq
import json
from Core.config import settings
from utils.prompts import SYSTEM_PROMPT, TOOL_RESPONSE_PROMPT, get_tool_definitions_gemini
from typing import List, Dict, Optional, Tuple

class ToolCall:
    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    async def get_completion(self, messages: List[dict], use_tools: bool = True):
        try:
            tools = get_tool_definitions_gemini() if use_tools else None
            response = await self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto" if use_tools else "none",
                temperature=0.7,
                max_tokens=800
            )
            msg = response.choices[0].message
            if msg.tool_calls:
                calls = []
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    calls.append(ToolCall(tc.function.name, args))
                return None, calls
            return msg.content or "", None
        except Exception as e:
            print("GROQ ERROR:", e)
            return "Sorry, having trouble.", None

    async def format_weather_response(self, data: dict, query: str) -> str:
        prompt = TOOL_RESPONSE_PROMPT.format(weather_data=json.dumps(data, indent=2), user_message=query)
        resp, _ = await self.get_completion([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}], False)
        return resp