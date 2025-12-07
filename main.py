from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Core.config import settings
from services.chat.chatbot_route import router as chat_router
from services.ai_suggestions.ai_suggestions_route import router as suggestions_router
import uvicorn

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Weather Chatbot API with LLM Integration and MCP Server"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(suggestions_router)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "endpoints": {
            "/chat": "Chat with weather bot",
            "/suggestions": "Get AI suggestions",
            "/docs": "API documentation"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=settings.FASTAPI_PORT,
        reload=settings.DEBUG
    )