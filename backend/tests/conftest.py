from unittest.mock import MagicMock, AsyncMock
import os
import tempfile
from datetime import timedelta
from dotenv import load_dotenv
import types # Importar el módulo types

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Define the path to the .env file relative to this conftest.py
# conftest.py is in tests/, .env is in backend/
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)


from src.api.v1 import schemas
from src.celery_app import celery_app
from src.core.security import get_current_user, TokenData
from src.db.database import Base, get_db, init_db
from src.main import app
from src.services import repository_service # Import the real service


# Explicitly rebuild Pydantic models to resolve forward references in tests
schemas.Repository.model_rebuild()
schemas.AnalysisResult.model_rebuild()

# Set Celery to always run tasks eagerly (synchronously) during tests
celery_app.conf.task_always_eager = True


@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    Fixture that provides a fresh, isolated database session for each test.
    Uses a temporary file-based SQLite database.
    """
    fd, db_path = tempfile.mkstemp()
    os.close(fd)

    sqlalchemy_database_url = f"sqlite:///{db_path}"
    engine = create_engine(
        sqlalchemy_database_url, connect_args={"check_same_thread": False}
    )
    init_db(engine)

    db = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield db
    finally:
        db.close()
        os.unlink(db_path)


@pytest.fixture
def mock_repository_service():
    """Fixture to mock the entire repository_service module."""
    mock = MagicMock()
    # Mock individual functions that are accessed directly by the API endpoints
    mock.get_repository_by_url = MagicMock()
    mock.create_repository = MagicMock()
    mock.get_repositories_by_owner = MagicMock()
    mock.get_repository = MagicMock()
    mock.get_analysis_results_for_repository = MagicMock()
    mock.get_analysis_narrative = MagicMock()
    # Note: get_analysis_result is a crud function, not in repository_service
    return mock


@pytest.fixture(name="client")
def client_fixture(db_session: Session, mock_repository_service: MagicMock):
    """
    Fixture that provides a TestClient instance for each test,
    with dependencies overridden for testing, including authentication.
    """
    # Re-import app here to ensure it picks up all routers and configurations
    from src.main import app

    def override_get_db():
        yield db_session

    def override_get_current_user():
        # Bypasses the actual token validation and returns a dummy user
        # Ensure id is an integer to match owner_id expectations
        return TokenData(username="testuser", id=1)
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Override specific functions from repository_service
    app.dependency_overrides[repository_service.get_repository_by_url] = mock_repository_service.get_repository_by_url
    app.dependency_overrides[repository_service.create_repository] = mock_repository_service.create_repository
    app.dependency_overrides[repository_service.get_repositories_by_owner] = mock_repository_service.get_repositories_by_owner
    app.dependency_overrides[repository_service.get_repository] = mock_repository_service.get_repository
    app.dependency_overrides[repository_service.get_analysis_results_for_repository] = mock_repository_service.get_analysis_results_for_repository
    app.dependency_overrides[repository_service.get_analysis_narrative] = mock_repository_service.get_analysis_narrative


    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=TokenData)
    user.id = 1
    user.username = "testuser"
    return user

@pytest.fixture
def mock_current_websocket_user():
    user = MagicMock(spec=TokenData)
    user.id = "testuser_ws"
    user.username = "testuser_ws"
    return user

@pytest.fixture
def mock_connection_manager():
    return MagicMock()

@pytest.fixture
def _mock_redis_client(mocker):
    """Fixture to mock the Redis client."""
    return mocker.patch("redis.Redis", autospec=True)


@pytest.fixture(autouse=True)
def mock_asyncio_run_global(mocker):
    """Globally mocks asyncio.run to return a simple MagicMock,
    allowing synchronous tests to proceed without actual async execution."""
    def side_effect_for_asyncio_run(coro):
        # We don't try to "resolve" the awaitable here.
        # We just return a MagicMock, simulating that asyncio.run completed successfully.
        return MagicMock() 

    mocker.patch("asyncio.run", side_effect=side_effect_for_asyncio_run)


