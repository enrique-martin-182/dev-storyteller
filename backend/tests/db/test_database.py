import contextlib
import importlib
import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import sessionmaker

# Import the module under test using a relative import
# to allow mocking of global variables like os.getenv
from src.db import database as db_module


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


@pytest.fixture
def mock_data_dir():
    """Mocks os.makedirs and os.path.exists to prevent actual directory creation."""
    with patch("os.makedirs") as mock_makedirs, patch("os.path.exists", return_value=False) as mock_exists:
        yield mock_makedirs, mock_exists


def test_database_url_sqlite_default(mock_data_dir):
    # Reload the module to apply environment changes
    with patch.dict(os.environ, {}, clear=True): # Ensure DATABASE_URL is not set
        importlib.reload(db_module)

    assert db_module.SQLALCHEMY_DATABASE_URL == "sqlite:///./data/sql_app.db"
    assert db_module.connect_args == {"check_same_thread": False}
    mock_data_dir[0].assert_called_once_with('./data') # os.makedirs should be called
    mock_data_dir[1].assert_called_once_with('./data') # os.path.exists should be called

def test_database_url_postgresql_from_env(mock_data_dir):
    pg_url = "postgresql://user:password@host:5432/dbname"
    with patch.dict(os.environ, {"DATABASE_URL": pg_url}, clear=True):
        importlib.reload(db_module)

    assert pg_url == db_module.SQLALCHEMY_DATABASE_URL
    assert db_module.connect_args == {}
    mock_data_dir[0].assert_called_once_with('./data') # os.makedirs should be called
    mock_data_dir[1].assert_called_once_with('./data') # os.path.exists should be called


def test_engine_creation():
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(db_module)

    # Check if engine is an instance of Engine
    assert isinstance(db_module.engine, type(create_engine("sqlite:///:memory:")))
    assert str(db_module.engine.url) == "sqlite:///./data/sql_app.db"


def test_session_local_creation():
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(db_module)

    assert isinstance(db_module.SessionLocal, type(sessionmaker()))
    assert db_module.SessionLocal.kw["autocommit"] is False
    assert db_module.SessionLocal.kw["autoflush"] is False
    assert db_module.SessionLocal.kw["bind"] == db_module.engine


def test_base_declaration():
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(db_module)

    assert db_module.Base.__class__.__name__ == "DeclarativeMeta"


def test_get_db_dependency():
    with patch.dict(os.environ, {}, clear=True):
        importlib.reload(db_module)

    mock_session = MagicMock(spec=Session)
    mock_session_local = MagicMock(return_value=mock_session)

    with patch("src.db.database.SessionLocal", new=mock_session_local):
        # Call the dependency
        db_generator = db_module.get_db()
        db = next(db_generator)

        # Assert that a session was provided
        assert db == mock_session
        mock_session_local.assert_called_once()

        # Assert that the session is closed after yielding
        with contextlib.suppress(StopIteration):
            next(db_generator)
        mock_session.close.assert_called_once()

