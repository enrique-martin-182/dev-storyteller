import os
import tempfile
from datetime import datetime # <-- Añadido
from dotenv import load_dotenv # Importar load_dotenv
import types # Importar el módulo types
from unittest.mock import MagicMock, AsyncMock # <-- Movida esta línea

# Cargar variables de entorno y configurar para testing al principio
load_dotenv()
os.environ["ENVIRONMENT"] = "testing"

import pytest
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from pydantic import HttpUrl # <-- Añadido

from src.api.v1 import schemas
from src.celery_app import celery_app
from src.core.security import get_current_user, TokenData
from src.db import crud, models # Añadido 'crud'
from src.db.database import Base, get_db, init_db
from src.main import app
from src.services import repository_service # Import the real service

@pytest.fixture(autouse=True)
def mock_celery_send_task(mocker):
    """Mocks celery_app.send_task to prevent actual Celery task dispatch during tests."""
    mocker.patch("src.celery_app.celery_app.send_task", return_value=MagicMock(id="mock_task_id", status="SUCCESS"))

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


@pytest.fixture(name="client")
def client_fixture(db_session: Session):
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
def mock_session_local(mocker, db_session):
    """
    Mocks SessionLocal in analysis_service to return the test db_session.
    This prevents Celery tasks from trying to connect to a real database.
    """
    mocker.patch("src.services.analysis_service.SessionLocal", return_value=db_session)



