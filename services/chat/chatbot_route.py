# services/chat/chatbot_route.py
from fastapi import APIRouter, HTTPException, Query
from services.chat.chatbot_schema import ChatMessage, ChatResponse, ConversationHistory, HealthCheck
from services.chat.chatbot import WeatherChatbot
from Core.config import settings
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["Chat"])
chatbot = WeatherChatbot()


@router.post("/", response_model=ChatResponse)
async def chat(
    message: ChatMessage,  # ← Only { "message": "..." } in body
    session_id: str = Query(default="default", description="Session ID"),
    use_context: bool = Query(default=True, description="Use vector context")
):
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # ← THIS IS THE CORRECT CALL — YOUR METHOD USES "message", NOT "user_message"
    response = await chatbot.process_message(
        message=message.message,      # ← FIXED: was user_message
        session_id=session_id,
        use_context=use_context
    )
    return response


# Rest of your routes (keep exactly as they are — they are perfect)
@router.get("/history", response_model=ConversationHistory)
async def get_history(session_id: str = Query(default="default")):
    history = chatbot.get_conversation_history(session_id)
    user_history = history[1:] if len(history) > 1 else []
    return ConversationHistory(
        session_id=session_id,
        history=user_history,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )

@router.post("/clear")
async def clear_history(session_id: str = Query(default="default")):
    chatbot.clear_history(session_id)
    return {"message": f"History cleared for session: {session_id}"}

@router.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        status="healthy",
        fastapi="healthy",
        mcp_server="healthy",
        llm_configured=bool(settings.GEMINI_API_KEY),
        redis_connected=True
    )