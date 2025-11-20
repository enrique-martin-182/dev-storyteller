from fastapi import APIRouter

from .endpoints import login, repositories

api_router = APIRouter()
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["repositories"]
)
api_router.include_router(login.router, tags=["authentication"])
