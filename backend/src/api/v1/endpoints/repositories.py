import time
from collections import defaultdict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketException,
    status,
)
from sqlalchemy.orm import Session

from src.api.v1 import schemas
from src.api.v1.connection_manager import manager
from src.core.security import TokenData, get_current_user, get_current_websocket_user
from src.db import crud
from src.db.database import get_db
from src.services import repository_service  # Import the new service

router = APIRouter()

# WebSocket connection rate limiting
WS_CONNECT_RATE_LIMIT_SECONDS = 60
WS_CONNECT_RATE_LIMIT_COUNT = 5
user_connection_attempts = defaultdict(lambda: {"count": 0, "last_attempt": 0})

async def rate_limit_websocket_connect(current_user: TokenData = Depends(get_current_websocket_user)):
    username = current_user.id
    now = time.time()

    if now - user_connection_attempts[username]["last_attempt"] > WS_CONNECT_RATE_LIMIT_SECONDS:
        user_connection_attempts[username]["count"] = 1
        user_connection_attempts[username]["last_attempt"] = now
    else:
        user_connection_attempts[username]["count"] += 1
        if user_connection_attempts[username]["count"] > WS_CONNECT_RATE_LIMIT_COUNT:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason=f"Too many connection attempts. Please wait {WS_CONNECT_RATE_LIMIT_SECONDS} seconds."
            )
    return current_user

@router.post("/", response_model=schemas.Repository)
async def create_repository_analysis_request(
    repo: "schemas.RepositoryCreate", db: Session = Depends(get_db), response: Response = None, current_user: TokenData = Depends(get_current_user)
):
    """
    Accepts a repository URL for analysis.
    Creates a record in the database and triggers an asynchronous analysis task.
    """
    db_repo = repository_service.get_repository_by_url(db, str(repo.url))
    if db_repo:
        # If repository already exists, return it with 200 OK
        response.status_code = status.HTTP_200_OK
        return db_repo

    # Create a new repository record in the database
    db_repo = repository_service.create_repository(db=db, repo=repo, owner_id=current_user.id)
    response.status_code = status.HTTP_201_CREATED # Explicitly set 201 for new creation
    return db_repo


@router.get("/", response_model=list[schemas.Repository])
async def read_repositories(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)
):
    """
    Retrieve a list of all repositories for the current user.
    """
    repositories = repository_service.get_repositories_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return repositories


@router.get("/{repository_id}")
async def read_repository(repository_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """
    Retrieve a single repository by its ID.
    """
    db_repo = repository_service.get_repository(db, repository_id=repository_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    # Basic authorization: ensure the repository belongs to the current user
    if db_repo.owner_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository")
    return db_repo


@router.get("/{repository_id}/analysis", response_model=schemas.AnalysisResultsList)
async def read_repository_analysis(repository_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """
    Retrieve analysis results for a specific repository.
    """
    db_repo = repository_service.get_repository(db, repository_id=repository_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    # Basic authorization: ensure the repository belongs to the current user
    if db_repo.owner_id!= current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this repository's analysis")
    analysis_results = repository_service.get_analysis_results_for_repository(db, repository_id=repository_id)
    return schemas.AnalysisResultsList(analysis_results=analysis_results)

@router.get("/analysis/{analysis_id}/narrative", response_model=str)
async def get_analysis_narrative(analysis_id: int, db: Session = Depends(get_db), current_user: TokenData = Depends(get_current_user)):
    """
    Retrieve the generated narrative for a specific analysis result.
    """
    # First, get the analysis result to check its repository ID for authorization
    analysis_result_obj = crud.get_analysis_result(db, analysis_id=analysis_id)
    if analysis_result_obj is None:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    # Basic authorization: ensure the analysis result's repository belongs to the current user
    db_repo = repository_service.get_repository(db, repository_id=analysis_result_obj.repository_id)
    if db_repo is None or db_repo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this analysis narrative")

    narrative = analysis_result_obj.narrative
    if narrative is None:
        raise HTTPException(status_code=404, detail="Narrative not available for this analysis result")
    return narrative

from starlette.websockets import WebSocketDisconnect

# ... (other imports)

# ... (router and rate limit code)

@router.websocket("/ws/status")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: TokenData = Depends(rate_limit_websocket_connect)
):
    username = current_user.id
    await manager.connect(websocket, username)
    await websocket.accept()
    try:
        while True:
            # Keep the connection alive, or handle incoming messages if needed
            # For status updates, typically the server sends messages, not the client
            await websocket.receive_text() # Expecting client to send something to keep alive or for specific requests
    except WebSocketDisconnect as e:
        print(f"WebSocket disconnected for {username}: {e.code}")
    finally:
        manager.disconnect(username)