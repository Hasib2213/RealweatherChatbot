from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from utils.weather_service import WeatherService
from typing import Dict

app = FastAPI(title="MCP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

weather_service = WeatherService()

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/mcp/invoke")
async def invoke_tool(
    body: Dict = Body(...)
):
    """
    MCP tool invocation endpoint.
    Expects JSON body: {"method": "get_weather", "params": {"city": "Dhaka"}}
    """
    method = body.get("method")
    params = body.get("params", {})

    try:
        if method == "get_weather":
            city = params.get("city")
            country_code = params.get("country_code")
            data = await weather_service.get_weather(city, country_code)
            return {"result": {"data": data}}

        elif method == "get_forecast":
            city = params.get("city")
            country_code = params.get("country_code")
            days = params.get("days", 3)
            data = await weather_service.get_forecast(city, country_code, days=5)
            return {"result": {"data": data}}  
        else:
            return {"error": f"Unknown method: {method}"}

    except Exception as e:
        return {"error": str(e)}
