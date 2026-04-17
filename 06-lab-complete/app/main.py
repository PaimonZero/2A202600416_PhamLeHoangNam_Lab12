"""
Production AI Agent — Tích hợp LangGraph Agent + Security Layer

Checklist:
  ✅ LangGraph Agent (search_flights, search_hotels, calculate_budget)
  ✅ Config từ environment (12-factor)
  ✅ API Key + JWT authentication
  ✅ Sliding window rate limiting (20 req/min)
  ✅ Cost guard + daily budget ($5 USD)
  ✅ Session management (conversation history)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers + CORS
  ✅ Error handling
"""
import os
import time
import signal
import logging
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import get_rate_limiter
from app.cost_guard import get_cost_guard
from app.agent import create_agent

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# ─────────────────────────────────────────────────────────
# Initialize Agent & Security Modules
# ─────────────────────────────────────────────────────────
_agent_graph = None
_rate_limiter = None
_cost_guard = None

def init_agent():
    """Initialize LangGraph agent once at startup."""
    global _agent_graph
    try:
        _agent_graph, _ = create_agent()
        logger.info("LangGraph agent initialized successfully")
    except Exception as error:
        logger.error(f"Failed to initialize agent: {error}")
        _agent_graph = None

def get_agent():
    """Get initialized agent or raise error."""
    if _agent_graph is None:
        raise HTTPException(503, "Agent not initialized. Check LLM API keys.")
    return _agent_graph

# Initialize security modules at module level
_rate_limiter = get_rate_limiter(settings.rate_limit_per_minute)
_cost_guard = get_cost_guard(settings.daily_budget_usd)

# ─────────────────────────────────────────────────────────
# Session Management (In-Memory Storage)
# ─────────────────────────────────────────────────────────
class ChatSession:
    """In-memory session for conversation history."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict] = []
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.last_activity = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Export session as dict."""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": len(self.messages)
        }

# Global session storage
_sessions: Dict[str, ChatSession] = {}

def get_or_create_session(session_id: Optional[str] = None) -> ChatSession:
    """Get existing session or create new one."""
    if not session_id:
        session_id = str(uuid.uuid4())
    
    if session_id not in _sessions:
        _sessions[session_id] = ChatSession(session_id)
        logger.info(f"Created new session: {session_id}")
    
    return _sessions[session_id]

def delete_session(session_id: str) -> bool:
    """Delete session."""
    if session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
        return True
    return False

# ─────────────────────────────────────────────────────────
# Lifespan - Startup/Shutdown
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    
    # Initialize agent
    init_agent()
    
    time.sleep(0.1)  # simulate init
    _is_ready = True
    logger.info(json.dumps({
        "event": "ready",
        "sessions": len(_sessions),
        "agent_available": _agent_graph is not None
    }))

    yield

    _is_ready = False
    logger.info(json.dumps({
        "event": "shutdown",
        "active_sessions": len(_sessions)
    }))

# ─────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers.pop("server", None)
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        _error_count += 1
        raise

# ─────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    """User question for the agent."""
    question: str = Field(..., min_length=1, max_length=2000,
                          description="Your question for the travel agent")
    session_id: Optional[str] = Field(None, description="Conversation session ID (auto-generated if not provided)")

class AskResponse(BaseModel):
    """Agent response."""
    session_id: str
    question: str
    answer: str
    model: str
    cost_usd: float
    budget_remaining_usd: float
    timestamp: str

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    """Chat session history."""
    session_id: str
    messages: List[ChatMessage]
    created_at: str
    last_activity: str
    message_count: int

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    """Root endpoint with service info."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "sessions_active": len(_sessions),
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "chat_history": "GET /chat/{session_id}/history (requires X-API-Key)",
            "delete_session": "DELETE /chat/{session_id} (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Send a question to the travel agent.
    
    Returns conversation history with cost tracking.
    
    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    try:
        # Get or create session
        session = get_or_create_session(body.session_id)
        
        # Check rate limit (using API key as limiter key)
        _rate_limiter.check(api_key[:16])
        
        # Get agent
        agent = get_agent()
        
        logger.info(json.dumps({
            "event": "agent_call",
            "session_id": session.session_id,
            "q_len": len(body.question),
            "client": str(request.client.host) if request.client else "unknown",
        }))
        
        # Add user message to session
        session.add_message("user", body.question)
        
        # Build conversation history for agent (LangChain HumanMessage format)
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session.messages
        ]
        
        # Invoke agent with messages
        from langchain_core.messages import HumanMessage
        agent_messages = [
            HumanMessage(content=msg["content"]) if msg["role"] == "user"
            else {"role": msg["role"], "content": msg["content"]}
            for msg in session.messages
        ]
        
        result = agent.invoke({"messages": agent_messages})
        
        # Extract final response
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        # Estimate tokens (rough: ~0.25 tokens per character)
        input_tokens = int(len(body.question) * 0.25)
        output_tokens = int(len(answer) * 0.25)
        
        # Check and record cost
        cost_info = _cost_guard.check_and_record(api_key[:16], input_tokens, output_tokens)
        
        # Add assistant response to session
        session.add_message("assistant", answer)
        
        logger.info(json.dumps({
            "event": "agent_response",
            "session_id": session.session_id,
            "a_len": len(answer),
            "cost_usd": cost_info["cost_usd"],
            "budget_remaining_usd": cost_info["remaining_usd"],
        }))
        
        return AskResponse(
            session_id=session.session_id,
            question=body.question,
            answer=answer,
            model=settings.llm_model,
            cost_usd=cost_info["cost_usd"],
            budget_remaining_usd=cost_info["remaining_usd"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Agent error: {error}", exc_info=True)
        raise HTTPException(500, f"Agent error: {str(error)}")


@app.get("/chat/{session_id}/history", response_model=ChatHistoryResponse, tags=["Chat"])
async def get_chat_history(
    session_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Get conversation history for a session.
    
    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    session = get_or_create_session(session_id)
    
    return ChatHistoryResponse(
        session_id=session.session_id,
        messages=[ChatMessage(**msg) for msg in session.messages],
        created_at=session.created_at.isoformat(),
        last_activity=session.last_activity.isoformat(),
        message_count=len(session.messages)
    )


@app.delete("/chat/{session_id}", tags=["Chat"])
async def delete_chat_session(
    session_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Delete a chat session.
    
    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    success = delete_session(session_id)
    
    if not success:
        raise HTTPException(404, f"Session {session_id} not found")
    
    return {
        "message": f"Session {session_id} deleted",
        "deleted": True
    }


@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe. Platform restarts container if this fails."""
    checks = {
        "llm": "ready" if _agent_graph else "unavailable",
        "agent": "ready" if _agent_graph else "unavailable"
    }
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "active_sessions": len(_sessions),
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe. Load balancer stops routing here if not ready."""
    if not _is_ready or _agent_graph is None:
        raise HTTPException(503, "Not ready. Agent initialization pending.")
    return {"ready": True}


@app.get("/metrics", tags=["Operations"])
def metrics(api_key: str = Depends(verify_api_key)):
    """
    Basic metrics (protected).
    
    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    usage = _cost_guard.get_usage(api_key[:16])
    current_cost = usage.total_cost_usd if usage else 0.0
    
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "active_sessions": len(_sessions),
        "daily_cost_usd": round(current_cost, 6),
        "daily_budget_usd": settings.daily_budget_usd,
        "budget_used_pct": round((current_cost / settings.daily_budget_usd * 100) if settings.daily_budget_usd > 0 else 0, 2),
    }


# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
