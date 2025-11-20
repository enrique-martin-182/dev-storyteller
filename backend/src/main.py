import os
from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import api_router, schemas
from src.api.v1.connection_manager import manager
from src.core.security import get_current_websocket_user
from src.db.database import init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    init_db()
    yield
    # Any shutdown logic can go here

# Create an instance of the FastAPI class
app = FastAPI(
    title="Dev Storyteller API",
    description="API for analyzing GitHub repositories and generating project narratives.",
    version="0.1.0",
    lifespan=lifespan
)

# Generic exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception for request {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

# Define allowed origins for CORS
# In production, this should be set to the actual frontend URL(s)
frontend_url = os.getenv("FRONTEND_URL")
origins = [
    "http://localhost",
    "http://localhost:5173",  # Default Vite dev server
    "http://localhost:3000",  # Frontend URL from docker-compose
]
if frontend_url:
    origins.append(frontend_url)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Explicitly allow common methods
    allow_headers=["*"], # Allow all headers, as specific headers can vary
)

@app.get("/", tags=["Health Check"])
async def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"status": "ok", "message": "Welcome to Dev Storyteller API!"}


@app.websocket("/api/v1/ws/status")
async def websocket_endpoint(websocket: WebSocket, current_user: "TokenData" = Depends(get_current_websocket_user)):
    await manager.connect(websocket, current_user.id)
    try:
        while True:
            # We are just receiving updates from the server, so we don't need to process incoming messages.
            # This loop keeps the connection alive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(current_user.id)


# In a real application, you would import and include your API routers here
app.include_router(api_router, prefix="/api/v1")

# Rebuild Pydantic models to resolve forward references
schemas.Repository.model_rebuild()
schemas.AnalysisResult.model_rebuild()

# Rebuild Pydantic models to resolve forward references
schemas.Repository.model_rebuild()
schemas.AnalysisResult.model_rebuild()
