from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.database.database import engine, Base, SessionLocal
from dotenv import load_dotenv
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
from app.agent.shopping_assistant import ShoppingAssistant
from app.models.user_preferences import UserPreferencesManager
from typing import Dict, Optional, Any
from fastapi.security import OAuth2PasswordBearer

# Load environment variables
load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Product Search API",
    description="A FastAPI application with GraphQL, Elasticsearch, and PostgreSQL",
    version="1.0.0",
    debug=os.getenv("DEBUG", "False").lower() == "true"
)

# Add rate limiter
app.state.limiter = limiter

# Configure CORS
allowed_origins = json.loads(os.getenv("ALLOWED_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]'))
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure GraphQL route
graphql_app = GraphQLRouter(schema)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Alışveriş asistanı instance'ı
shopping_assistant = ShoppingAssistant()

@app.post("/chat")
async def chat_with_assistant(
    request: Dict[str, str],
    user_id: Optional[str] = None,
    db: SessionLocal = Depends(get_db)
):
    """
    Alışveriş asistanı ile sohbet endpoint'i
    
    Request body:
    {
        "message": "Spor ayakkabı arıyorum, bütçem 1000 TL"
    }
    """
    if "message" not in request:
        raise HTTPException(status_code=400, detail="Message field is required")
    
    response = await shopping_assistant.process_message(request["message"], user_id)
    return {"response": response}

@app.post("/reset-chat")
async def reset_chat(user_id: Optional[str] = None):
    """Sohbet geçmişini sıfırla"""
    shopping_assistant.reset_conversation(user_id)
    return {"status": "success", "message": "Chat history has been reset"}

@app.get("/user/preferences")
async def get_user_preferences(
    user_id: str,
    db: SessionLocal = Depends(get_db)
):
    """Kullanıcı tercihlerini getir"""
    prefs_manager = UserPreferencesManager(db)
    preferences = prefs_manager.get_user_preferences(user_id)
    return preferences

@app.post("/user/preferences")
async def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any],
    db: SessionLocal = Depends(get_db)
):
    """Kullanıcı tercihlerini güncelle"""
    prefs_manager = UserPreferencesManager(db)
    success = prefs_manager.update_preferences(user_id, preferences)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update preferences")
    return {"status": "success", "message": "Preferences updated successfully"}

@app.get("/user/search-history")
async def get_search_history(
    user_id: str,
    limit: int = 10,
    db: SessionLocal = Depends(get_db)
):
    """Kullanıcının arama geçmişini getir"""
    prefs_manager = UserPreferencesManager(db)
    history = prefs_manager.get_recent_searches(user_id, limit)
    return {"history": history}

@app.get("/user/preferences/analysis")
async def get_preferences_analysis(
    user_id: str,
    db: SessionLocal = Depends(get_db)
):
    """Kullanıcı tercihlerinin analizini getir"""
    prefs_manager = UserPreferencesManager(db)
    analysis = prefs_manager.analyze_user_preferences(user_id)
    return analysis

# Health check endpoint
@app.get("/health")
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "healthy"}

# Error handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too many requests",
            "detail": "Rate limit exceeded. Please try again later."
        }
    )

# Statik dosyaları serve et
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Ana sayfa
@app.get("/")
async def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found") 