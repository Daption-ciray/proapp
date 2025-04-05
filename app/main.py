from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
from app.database.database import engine, Base
from dotenv import load_dotenv
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
from app.agent.shopping_assistant import ShoppingAssistant
from typing import Dict

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

# Alışveriş asistanı instance'ı
shopping_assistant = ShoppingAssistant()

@app.post("/chat")
async def chat_with_assistant(request: Dict[str, str]):
    """
    Alışveriş asistanı ile sohbet endpoint'i
    
    Request body:
    {
        "message": "Spor ayakkabı arıyorum, bütçem 1000 TL"
    }
    """
    if "message" not in request:
        raise HTTPException(status_code=400, detail="Message field is required")
    
    response = await shopping_assistant.process_message(request["message"])
    return {"response": response}

@app.post("/reset-chat")
async def reset_chat():
    """Sohbet geçmişini sıfırla"""
    shopping_assistant.reset_conversation()
    return {"status": "success", "message": "Chat history has been reset"} 