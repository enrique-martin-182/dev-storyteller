import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set environment variables at the very top
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "super-secret-test-key"

# Patch load_dotenv to prevent actual .env file loading during tests
with patch("src.main.load_dotenv", lambda: None):
    # These imports are now safe as environment variables are set
    from src.api.v1 import schemas
    from src.celery_app import celery_app
    from src.core.security import TokenData, get_current_user, get_current_websocket_user
    from src.db.database import get_db, init_db
    from src.main import app
    from src.services import repository_service  # Import the real service


@pytest.fixture(autouse=True)
def mock_celery_send_task(mocker):
    """
    Mocks clone_and_analyze_repository.delay to prevent actual Celery task dispatch during tests
    and returns the mock object for assertions.
    """
    mock_send_task = mocker.patch(
        "src.services.analysis_service.clone_and_analyze_repository.delay",
        return_value=MagicMock(id="mock_task_id", status="SUCCESS"),
    )
    return mock_send_task


# Explicitly rebuild Pydantic models to resolve forward references in tests
schemas.Repository.model_rebuild()
schemas.AnalysisResult.model_rebuild()

# Set Celery to always run tasks eagerly (synchronously) during tests
celery_app.conf.task_always_eager = True


# Explicitly rebuild Pydantic models to resolve forward references in tests


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


@pytest.fixture(autouse=True)
def mock_repository_service(mocker):
    """
    Fixture to mock the entire RepositoryService module, returning a MagicMock instance
    that can be configured in individual tests. This effectively replaces the imported
    `repository_service` object in `src.api.v1.endpoints.repositories`.
    """
    mock_service_instance = MagicMock(spec=repository_service.RepositoryService)
    # Patch the imported repository_service object in the repositories endpoint module
    mocker.patch(
        "src.api.v1.endpoints.repositories.repository_service", new=mock_service_instance
    )
    return mock_service_instance


@pytest.fixture(name="client")
def client_fixture(db_session: Session, mocker, mock_manager):
    """
    Fixture that provides a TestClient instance for each test,
    with dependencies overridden for testing, including authentication.
    """
    mocker.patch("src.api.v1.endpoints.repositories.manager", new=mock_manager)

    def override_get_db():
        yield db_session

    def override_get_current_user():
        # Bypasses the actual token validation and returns a dummy user
        return TokenData(username="testuser", id=1)  # INTEGER ID

    def override_get_current_websocket_user_dep():
        # Directly return a dummy user object for websocket authentication
        return TokenData(username="testuser_ws", id=2)  # INTEGER ID

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[
        get_current_websocket_user
    ] = override_get_current_websocket_user_dep

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
def mock_manager():
    manager_mock = MagicMock()
    manager_mock.connect = AsyncMock(return_value=True)
    manager_mock.disconnect = MagicMock()
    return manager_mock


@pytest.fixture
def _mock_redis_client(mocker):
    """Fixture to mock the Redis client."""
    return mocker.patch("redis.Redis", autospec=True)


@pytest.fixture(autouse=True)
def mock_session_local(mocker, db_session):
    """
    Mocks SessionLocal in analysis_service to return the test db_session.
    This prevents Celery tasks from trying to connect to a real database.
    """
    mocker.patch("src.services.analysis_service.SessionLocal", return_value=db_session)