import httpx
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from Core.config import settings
from services.chat.chatbot_schema import (
    ChatResponse, WeatherData, ForecastData, ForecastItem
)
from utils.llm_service import LLMService
from utils.prompts import SYSTEM_PROMPT
from vectordb.config import vector_store

class WeatherChatbot:
    def __init__(self):
        self.mcp_url = f"http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}"
        self.llm_service = LLMService()
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.vector_store = vector_store

    def decode_tool_args(self, raw):
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except:
                pass
            fixed = raw.replace("=", ":").replace("'", '"')
            try:
                return json.loads(fixed)
            except:
                print("FAILED TO DECODE TOOL ARGUMENTS:", raw)
                return {}
        return {}

    async def call_mcp_server(self, method: str, params: dict) -> dict:
        """Call the MCP server to execute tools"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mcp_url}/mcp/invoke",
                json={"method": method, "params": params},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

    async def execute_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool call via MCP server"""
        try:
            mcp_response = await self.call_mcp_server(tool_name, arguments)
            if mcp_response.get("error"):
                return {"error": mcp_response["error"]}
            return mcp_response["result"]["data"]
        except Exception as e:
            return {"error": str(e)}

    def get_conversation_history(self, session_id: str = "default") -> List[Dict]:
        """Get conversation history for a session"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        return self.conversation_history[session_id]

    def add_to_history(self, session_id: str, role: str, content: str):
        """Add message to conversation history"""
        history = self.get_conversation_history(session_id)
        history.append({"role": role, "content": content})
        if self.vector_store and role == "user":
            self.vector_store.add_documents(
                [content],
                [{"session_id": session_id, "timestamp": datetime.now().isoformat(), "role": role}]
            )
        if len(history) > 11:
            self.conversation_history[session_id] = [history[0]] + history[-10:]

    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]

    async def get_similar_conversations(self, query: str, k: int = 3) -> List[str]:
        """Get similar past conversations using vector search"""
        if not self.vector_store:
            return []
        try:
            results = self.vector_store.search(query, k=k)
            return [doc for doc, score, meta in results if score < 1.5]
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    async def process_message(
        self,
        message: str,
        session_id: str = "default",
        use_context: bool = True
    ) -> ChatResponse:
        """Process user message using LLM with tool calling"""
        try:
            # Get similar past conversations for context (if enabled)
            context_messages = []
            if use_context and self.vector_store:
                similar_convs = await self.get_similar_conversations(message)
                if similar_convs:
                    context_messages = [
                        {
                            "role": "system",
                            "content": f"Similar past queries: {', '.join(similar_convs[:2])}"
                        }
                    ]

            # Add user message to history
            self.add_to_history(session_id, "user", message)

            # Get conversation history
            messages = self.get_conversation_history(session_id)

            # Add context if available
            if context_messages:
                messages = messages[:1] + context_messages + messages[1:]

            # Get LLM response with potential tool calls
            llm_response, tool_calls = await self.llm_service.get_completion(messages)

            # If LLM wants to use tools
            if tool_calls:
                tool_results = []
                tool_names = []

                for tool_call in tool_calls:
                    tool_names.append(tool_call.name)
                    raw_args = tool_call.arguments
                    args = self.decode_tool_args(raw_args)
                    result = await self.execute_tool_call(
                        tool_call.name,
                        args
                    )
                    tool_results.append({
                        "tool": tool_call.name,
                        "result": result
                    })

                # Format the tool results into a natural response
                if tool_results:
                    # Check if there was an error
                    if "error" in tool_results[0]["result"]:
                        error_message = tool_results[0]["result"]["error"]
                        response_text = (
                            f"I'm sorry, I couldn't fetch the weather data: {error_message}. "
                            "Please check the city name and try again."
                        )
                        self.add_to_history(session_id, "assistant", response_text)
                        return ChatResponse(
                            response=response_text,
                            tool_calls=tool_names,
                            session_id=session_id
                        )

                    # Format successful tool response
                    formatted_response = await self.llm_service.format_weather_response(
                        tool_results[0]["result"],
                        message
                    )
                    self.add_to_history(session_id, "assistant", formatted_response)

                    # Extract weather/forecast data
                    weather_data = None
                    forecast_data = None
                    result_data = tool_results[0]["result"]

                    if tool_results[0]["tool"] == "get_weather":
                        if isinstance(result_data, dict) and "error" not in result_data:
                            try:
                                weather_data = WeatherData(
                                    **result_data,
                                    timestamp=datetime.now()
                                )
                            except Exception as e:
                                print("WeatherData parsing error:", e)
                                weather_data = None

                    elif tool_results[0]["tool"] == "get_forecast":
                        if isinstance(result_data, dict) and "error" not in result_data and "forecasts" in result_data:
                            try:
                                forecasts_list = [
                                    ForecastItem(
                                        date=item["date"],
                                        temp_min=item["temp_min"],
                                        temp_max=item["temp_max"],
                                        description=item["description"]
                                    )
                                    for item in result_data["forecasts"]
                                ]
                                forecast_data = ForecastData(
                                    city=result_data["city"],
                                    country=result_data["country"],
                                    forecasts=forecasts_list
                                )
                            except Exception as e:
                                print("ForecastData parsing error:", e)
                                forecast_data = None
                                formatted_response = "I received the forecast but had trouble displaying it properly."
                        else:
                            formatted_response = "Sorry, I couldn't retrieve the weather forecast right now."

                    return ChatResponse(
                        response=formatted_response,
                        weather_data=weather_data,
                        forecast_data=forecast_data,
                        tool_calls=tool_names,
                        session_id=session_id
                    )

            # No tools called, just conversational response
            self.add_to_history(session_id, "assistant", llm_response)
            return ChatResponse(
                response=llm_response,
                session_id=session_id
            )

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error: {str(e)}. Please try again."
            return ChatResponse(
                response=error_msg,
                session_id=session_id
            )

    async def check_mcp_health(self) -> bool:
        """Check if MCP server is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.mcp_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False

    def get_vector_stats(self) -> dict:
        """Get vector store statistics"""
        if self.vector_store:
            return self.vector_store.get_stats()
        return {"enabled": False}
    