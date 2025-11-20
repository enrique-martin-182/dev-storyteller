import os

import pytest
from sqlalchemy.exc import OperationalError

from src.core.enums import AnalysisStatus
from src.db import models
from src.db.database import Base, SessionLocal, engine


@pytest.fixture(scope="module")
def postgres_db_url():
    """
    Fixture to provide a PostgreSQL database URL from an environment variable.
    If not set, skips PostgreSQL tests.
    """
    url = os.getenv("TEST_DATABASE_URL_POSTGRES")
    if not url:
        pytest.skip("TEST_DATABASE_URL_POSTGRES environment variable not set. Skipping PostgreSQL tests.")
    return url

@pytest.fixture(scope="module")
def setup_postgres_test_db(postgres_db_url):
    """
    Sets up a temporary PostgreSQL database for testing.
    Requires a running PostgreSQL instance at the provided URL.
    """
    # Temporarily set the DATABASE_URL for the database.py logic
    original_database_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = postgres_db_url

    # Import get_db after setting the environment variable to ensure it picks up the new URL

    try:
        # Attempt to connect and create tables
        Base.metadata.create_all(bind=engine)
        yield SessionLocal()
    except OperationalError as e:
        pytest.fail(f"Could not connect to PostgreSQL database at {postgres_db_url}. "
                    f"Ensure a PostgreSQL instance is running and accessible. Error: {e}")
    finally:
        # Clean up: drop tables and reset environment variable
        Base.metadata.drop_all(bind=engine)
        if original_database_url is not None:
            os.environ["DATABASE_URL"] = original_database_url
        else:
            del os.environ["DATABASE_URL"]

def test_postgres_connection_and_crud(setup_postgres_test_db):
    """
    Tests if the application can connect to PostgreSQL and perform basic CRUD operations.
    """
    db = setup_postgres_test_db
    # Perform a simple CRUD operation to verify connection and table creation
    new_repo = models.Repository(url="https://github.com/test/postgres", name="postgres_test_repo", status=AnalysisStatus.PENDING)
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    retrieved_repo = db.query(models.Repository).filter(models.Repository.url == "https://github.com/test/postgres").first()
    assert retrieved_repo is not None
    assert retrieved_repo.name == "postgres_test_repo"

    db.delete(retrieved_repo)
    db.commit()

    deleted_repo = db.query(models.Repository).filter(models.Repository.url == "https://github.com/test/postgres").first()
    assert deleted_repo is None
