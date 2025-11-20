import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.database import Base
from src.db.models import AnalysisResult, Repository, User
from src.db import crud
from src.core.enums import AnalysisStatus
from src.api.v1 import schemas

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="session")
def session_fixture():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(session):
    user = crud.create_user(session, username="testuser", hashed_password="hashedpassword")
    return user

@pytest.fixture
def test_repository(session, test_user):
    repo = crud.create_repository(session, url="https://github.com/test/repo", name="test/repo", owner_id=test_user.id)
    return repo

@pytest.fixture
def test_analysis_result(session, test_repository):
    analysis_data = schemas.AnalysisResultCreate(
        repository_id=test_repository.id,
        summary="Initial summary",
        narrative="Initial narrative",
        file_count=10,
        commit_count=5,
        languages={"Python": 100},
        tech_stack=["Python"],
        open_issues_count=2,
        open_pull_requests_count=1,
        contributors=[{"login": "contributor1"}],
        report_url="http://example.com/report",
        status=AnalysisStatus.PENDING
    )
    result = crud.create_analysis_result(session, analysis=analysis_data)
    return result


# Helper function for create_user since it's not in crud.py, but used by test_user fixture
def create_user(db: Session, username: str, hashed_password: str):
    db_user = User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
crud.create_user = create_user # Monkey patch crud to include create_user for testing fixtures


def test_create_repository(session, test_user):
    repo = crud.create_repository(session, url="https://github.com/new/repo", name="new/repo", owner_id=test_user.id)
    assert repo.id is not None
    assert repo.url == "https://github.com/new/repo"
    assert repo.name == "new/repo"
    assert repo.owner_id == test_user.id
    assert repo.status == AnalysisStatus.PENDING

def test_get_repository_by_url(session, test_repository):
    repo = crud.get_repository_by_url(session, url="https://github.com/test/repo")
    assert repo.id == test_repository.id

def test_get_repositories(session, test_repository):
    repos = crud.get_repositories(session)
    assert len(repos) == 1
    assert repos[0].id == test_repository.id

def test_get_repository(session, test_repository):
    repo = crud.get_repository(session, repository_id=test_repository.id)
    assert repo.id == test_repository.id

def test_create_analysis_result(session, test_repository):
    analysis_data = schemas.AnalysisResultCreate(
        repository_id=test_repository.id,
        summary="Another summary",
        narrative="Another narrative",
        file_count=20,
        commit_count=10,
        languages={"Java": 50},
        tech_stack=["Java"],
        open_issues_count=3,
        open_pull_requests_count=0,
        contributors=[{"login": "contributor2"}],
        report_url="http://example.com/another_report",
        status=AnalysisStatus.COMPLETED
    )
    result = crud.create_analysis_result(session, analysis=analysis_data)
    assert result.id is not None
    assert result.repository_id == test_repository.id
    assert result.summary == "Another summary"

def test_get_analysis_results_for_repository(session, test_analysis_result):
    results = crud.get_analysis_results_for_repository(session, repository_id=test_analysis_result.repository_id)
    assert len(results) == 1
    assert results[0].id == test_analysis_result.id

def test_get_analysis_result(session, test_analysis_result):
    result = crud.get_analysis_result(session, analysis_id=test_analysis_result.id)
    assert result.id == test_analysis_result.id

def test_update_repository_status(session, test_repository):
    updated_repo = crud.update_repository_status(session, repository_id=test_repository.id, new_status=AnalysisStatus.COMPLETED)
    assert updated_repo.status == AnalysisStatus.COMPLETED

def test_update_analysis_result_summary(session, test_analysis_result):
    updated_result = crud.update_analysis_result_summary(session, analysis_id=test_analysis_result.id, new_summary="Updated summary")
    assert updated_result.summary == "Updated summary"

def test_delete_repository(session, test_repository):
    crud.delete_repository(session, repository_id=test_repository.id)
    repo = crud.get_repository(session, repository_id=test_repository.id)
    assert repo is None

def test_delete_analysis_result(session, test_analysis_result):
    crud.delete_analysis_result(session, analysis_id=test_analysis_result.id)
    result = crud.get_analysis_result(session, analysis_id=test_analysis_result.id)
    assert result is None